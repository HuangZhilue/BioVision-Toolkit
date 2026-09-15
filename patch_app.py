import re

# 1. Update app.py
with open("app.py", "r", encoding="utf-8") as f:
    app_content = f.read()

imports = """
import os
import json
import requests
import asyncio
import random
"""
app_content = app_content.replace("import os\nimport json\nimport requests", imports)

lock_decl = """
print("Model loaded successfully!")

online_request_lock = asyncio.Lock()
"""
app_content = app_content.replace('print("Model loaded successfully!")', lock_decl)

api_logic = """
@app.post("/api/identify/online")
async def identify_image_online(
    image: UploadFile = File(...), 
    token: str = Form(...),
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
"""
app_content = app_content.replace('if __name__ == "__main__":', api_logic)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(app_content)


# 2. Update bioclip.html
with open("bioclip.html", "r", encoding="utf-8") as f:
    html_content = f.read()

# Replace frontend logic
old_fetch_logic = """
            const formData = new FormData();
            formData.append('image', selectedFile);

            let url = 'https://api.inaturalist.org/v2/taxa/suggest?source=visual&taxon_id=3&fields=all';
            if (selectedLat !== null && selectedLng !== null) {
                formData.append('lat', selectedLat.toString());
                formData.append('lng', selectedLng.toString());
            }

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Authorization': token },
                    body: formData
                });
"""

new_fetch_logic = """
            const formData = new FormData();
            formData.append('image', selectedFile);
            formData.append('token', token);

            let url = 'http://127.0.0.1:8000/api/identify/online';
            if (selectedLat !== null && selectedLng !== null) {
                formData.append('lat', selectedLat.toString());
                formData.append('lng', selectedLng.toString());
            }

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    body: formData
                });
"""

html_content = html_content.replace(old_fetch_logic, new_fetch_logic)

with open("bioclip.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Patch applied successfully.")
