import io
import os

# 将模型缓存目录设置为项目当前目录下的 "models" 文件夹
os.environ["HF_HOME"] = os.path.join(os.getcwd(), "models")
os.environ["TORCH_HOME"] = os.path.join(os.getcwd(), "models")

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import torch

import os
import json
import requests
import asyncio
import random
import time
import gc
from apscheduler.schedulers.background import BackgroundScheduler
import build_china_birds
import update_regions
import download_images


# Monkey-patch torch.compile on Windows, as it's not supported and pybioclip tries to use it unconditionally
if os.name == 'nt':
    torch.compile = lambda x, **kwargs: x

from bioclip import TreeOfLifeClassifier, Rank
from PIL import Image

app = FastAPI(title="BioCLIP Local Server")

# Mount local images directory
os.makedirs("offline_images", exist_ok=True)
app.mount("/images", StaticFiles(directory="offline_images"), name="images")

PROVINCE_COORDS = {
    "北京": ("39.9042", "116.4074"), "天津": ("39.3434", "117.3616"), "河北": ("38.0428", "114.5149"),
    "山西": ("37.8706", "112.5624"), "内蒙古": ("40.8420", "111.7492"), "辽宁": ("41.8057", "123.4315"),
    "吉林": ("43.8171", "125.3235"), "黑龙江": ("45.7569", "126.6577"), "上海": ("31.2304", "121.4737"),
    "江苏": ("32.0603", "118.7969"), "浙江": ("30.2741", "120.1551"), "安徽": ("31.8612", "117.2830"),
    "福建": ("26.0745", "119.2965"), "江西": ("28.6820", "115.8579"), "山东": ("36.6512", "117.1201"),
    "河南": ("34.7466", "113.6253"), "湖北": ("30.5928", "114.3055"), "湖南": ("28.2282", "112.9388"),
    "广东": ("23.1291", "113.2644"), "广西": ("22.8140", "108.3200"), "海南": ("20.0174", "110.3492"),
    "重庆": ("29.5630", "106.5516"), "四川": ("30.5728", "104.0668"), "贵州": ("26.6470", "106.6302"),
    "云南": ("25.0406", "102.7123"), "西藏": ("29.6500", "91.1000"), "陕西": ("34.3416", "108.9398"),
    "甘肃": ("36.0611", "103.8343"), "青海": ("36.6171", "101.7782"), "宁夏": ("38.4872", "106.2309"),
    "新疆": ("43.8256", "87.6168"), "台湾": ("25.0330", "121.5654"), "香港": ("22.3193", "114.1694"),
    "澳门": ("22.1987", "113.5439")
}


# Load offline database
china_birds_db = {}
def load_china_birds_db():
    global china_birds_db
    if os.path.exists("china_birds.json"):
        print("Loading offline China birds database...")
        try:
            with open("china_birds.json", "r", encoding="utf-8") as f:
                china_birds_db = json.load(f)
            print(f"Loaded {len(china_birds_db)} birds into memory.")
        except Exception as e:
            print(f"Failed to load offline database: {e}")

load_china_birds_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run_maintenance_task():
    print("Starting automated maintenance task...")
    try:
        build_china_birds.build_database()
        update_regions.main()
        download_images.main()
        load_china_birds_db()
        print("Automated maintenance task completed successfully.")
    except Exception as e:
        print(f"Error during automated maintenance: {e}")

# --- 按需加载模型逻辑 ---
classifier = None
model_lock = asyncio.Lock()
last_model_use_time = 0

def _init_classifier():
    global classifier
    if classifier is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Loading BioCLIP model into memory using device: {device}...")
        classifier = TreeOfLifeClassifier(device=device)
        print("Model loaded successfully!")

async def get_classifier():
    global last_model_use_time, classifier
    async with model_lock:
        if classifier is None:
            await asyncio.to_thread(_init_classifier)
        last_model_use_time = time.time()
        return classifier

def unload_model_if_idle():
    global classifier, last_model_use_time
    if classifier is not None and time.time() - last_model_use_time > 600:
        print("Model idle for 10 minutes. Unloading to free memory...")
        classifier = None
        gc.collect()
# ------------------------

@app.on_event("startup")
def start_scheduler():
    scheduler = BackgroundScheduler()
    # 每周日凌晨 3 点执行
    scheduler.add_job(run_maintenance_task, 'cron', day_of_week='sun', hour=3, minute=0)
    # 每分钟检查一次模型是否空闲
    scheduler.add_job(unload_model_if_idle, 'interval', minutes=1)
    scheduler.start()
    print("Background scheduler started.")

@app.post("/api/maintenance/run")
async def trigger_maintenance(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_maintenance_task)
    return {"status": "Maintenance task started in the background. Check server logs for progress."}

online_request_lock = asyncio.Lock()


@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("bioclip.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/identify")
async def identify_image(image: UploadFile = File(...), province: Optional[str] = Form(None), lat: Optional[str] = Form(None), lng: Optional[str] = Form(None)):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File uploaded is not an image.")

    try:
        # Read image
        contents = await image.read()
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Save temporarily for pybioclip since it prefers a file path in some versions, 
        # but predict() also accepts PIL Image in newer versions. Let's try file path to be safe.
        temp_path = "temp_image.jpg"
        pil_image.save(temp_path)
        
        # Predict using BioCLIP (Rank.SPECIES) (按需加载模型)
        model = await get_classifier()
        predictions = await asyncio.to_thread(model.predict, temp_path, rank=Rank.SPECIES)
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        # Format the response to match what the frontend expects
        
        # Reverse geocode if lat/lng are provided but no province
        detected_province = province
        if not detected_province and lat and lng:
            try:
                headers = {"User-Agent": "iNatBioClip/1.0", "Accept-Language": "zh"}
                res = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json", headers=headers, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    addr = data.get("address", {})
                    state = addr.get("state") or addr.get("province") or ""
                    for suffix in ["省", "市", "自治区", "维吾尔自治区", "回族自治区", "壮族自治区", "特别行政区"]:
                        if state.endswith(suffix):
                            state = state.replace(suffix, "")
                    detected_province = state
                    print(f"Detected province from GPS: {detected_province}")
            except Exception as e:
                print(f"Reverse geocode failed: {e}")
                pass

        results = []
        for pred in predictions: # Process all to allow re-sorting

            # Extract names safely depending on pybioclip version
            
            sci_name = pred.get("scientific_name") or pred.get("species") or pred.get("classification") or "Unknown"
            
            # Lookup in offline database
            offline_info = china_birds_db.get(sci_name)
            is_rare_in_region = False
            
            if offline_info:
                if detected_province:
                    provinces = offline_info.get("provinces", [])
                    # Match province name (allow substring match just in case)
                    matched = any(detected_province in p or p in detected_province for p in provinces)
                    if not matched and provinces: # If provinces list is empty, we don't penalize to be safe
                        is_rare_in_region = True
                        pred["score"] = pred.get("score", 0.0) * 0.01

                common_name = offline_info.get("chinese_name") or pred.get("common_name") or sci_name

                # Use local image path
                image_filename = sci_name.replace(" ", "_").replace("/", "_") + ".jpg"
                default_photo = f"/images/{image_filename}" if offline_info.get("image_url") else None
                is_chinese_bird = True
            else:
                # Online API Fallback
                common_name = pred.get("common_name") or sci_name
                default_photo = None
                is_chinese_bird = False
                
                try:
                    res = requests.get(f"https://api.inaturalist.org/v1/taxa?q={sci_name}&is_active=true&per_page=1&locale=zh-CN", timeout=5)
                    if res.status_code == 200:
                        data = res.json()
                        if data.get("results"):
                            match = data["results"][0]
                            if match.get("preferred_common_name"):
                                common_name = match["preferred_common_name"]
                            if match.get("default_photo") and match["default_photo"].get("medium_url"):
                                default_photo = match["default_photo"]["medium_url"]
                except Exception as e:
                    print(f"API fallback failed for {sci_name}: {e}")

            results.append({
                "score": pred["score"] * 100, # Convert to percentage
                "is_chinese_bird": is_chinese_bird,
                "is_rare_in_region": is_rare_in_region,
                "taxon": {
                    "name": sci_name,
                    "preferred_common_name": common_name,
                    "default_photo": {"medium_url": default_photo} if default_photo else None
                }
            })
            
        # Re-sort results by score descending since we might have penalized some scores
        results.sort(key=lambda x: x["score"], reverse=True)
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/identify/online")
async def identify_image_online(
    image: UploadFile = File(...), 
    token: str = Form(...),
    province: Optional[str] = Form(None),
    lat: Optional[str] = Form(None), 
    lng: Optional[str] = Form(None)
):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File uploaded is not an image.")

    async with online_request_lock:
        # 保守串行模式: 等待上一个请求处理完毕后，再强制随机等待 1.0~2.0 秒
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        try:
            contents = await image.read()
            
            # 使用 requests.post 上传文件
            files = {'image': (image.filename, contents, image.content_type)}
            data = {}
            
            # If province is provided but lat/lng are missing, use province default coordinates
            if province and (not lat or not lng):
                if province in PROVINCE_COORDS:
                    lat, lng = PROVINCE_COORDS[province]

            if lat and lng:
                data['lat'] = lat
                data['lng'] = lng
            
            headers = {
                'Authorization': token
            }
            
            url = 'https://api.inaturalist.org/v2/taxa/suggest?source=visual&taxon_id=3&fields=all'
            
            # 发起同步请求 (使用 to_thread 避免阻塞事件循环)
            res = await asyncio.to_thread(
                requests.post,
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=15
            )
            
            if res.status_code != 200:
                error_msg = f"API Error: {res.status_code}"
                try:
                    err_data = res.json()
                    if err_data.get("errors"):
                        error_msg = ", ".join([e.get("message", str(e)) for e in err_data["errors"]])
                    elif err_data.get("error"):
                        error_msg = err_data["error"]
                except:
                    pass
                raise HTTPException(status_code=res.status_code, detail=error_msg)
                
            return res.json()
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # 修改为 0.0.0.0，以便在 Docker 容器外部可以访问
    uvicorn.run(app, host="0.0.0.0", port=8000)
