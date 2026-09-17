import requests
import json
import time

def build_database():
    print("开始构建中国鸟类离线数据库...")
    place_id = 6903 # China
    taxon_id = 3    # Aves (Birds)
    locale = 'zh-CN'
    per_page = 500
    
    birds_dict = {}
    
    for page in range(1, 4):
        url = f"https://api.inaturalist.org/v1/observations/species_counts?place_id={place_id}&taxon_id={taxon_id}&locale={locale}&per_page={per_page}&page={page}"
        print(f"正在抓取第 {page} 页...")
        
        response = requests.get(url)
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            break
            
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            break
            
        for item in results:
            taxon = item.get("taxon", {})
            sci_name = taxon.get("name")
            taxon_id = taxon.get("id")
            
            if sci_name and taxon_id:
                chinese_name = taxon.get("preferred_common_name")
                if not chinese_name:
                    chinese_name = taxon.get("english_common_name")
                
                photo_url = None
                default_photo = taxon.get("default_photo")
                if default_photo and default_photo.get("medium_url"):
                    photo_url = default_photo.get("medium_url")
                
                birds_dict[sci_name] = {
                    "taxon_id": taxon_id,
                    "chinese_name": chinese_name,
                    "image_url": photo_url,
                    "family": "Unknown"
                }
                
        time.sleep(1)
        
    print("开始获取科(family)分类信息...")
    taxon_items = list(birds_dict.items())
    chunk_size = 30
    for i in range(0, len(taxon_items), chunk_size):
        chunk = taxon_items[i:i+chunk_size]
        ids = [str(item[1]["taxon_id"]) for item in chunk]
        
        taxa_url = f"https://api.inaturalist.org/v1/taxa/{','.join(ids)}?locale={locale}"
        print(f"正在抓取分类详情... ({i}/{len(taxon_items)})")
        try:
            res = requests.get(taxa_url)
            if res.status_code == 200:
                for t in res.json().get("results", []):
                    sci_name = t.get("name")
                    family_name = "Unknown"
                    if t.get("ancestors"):
                        for anc in t["ancestors"]:
                            if anc.get("rank") == "family":
                                family_name = anc.get("name") or "Unknown"
                                break
                    if sci_name in birds_dict:
                        birds_dict[sci_name]["family"] = family_name
        except Exception as e:
            print("获取分类失败:", e)
            
        time.sleep(1)
        
    # 保存到 JSON 文件
    with open("china_birds.json", "w", encoding="utf-8") as f:
        json.dump(birds_dict, f, ensure_ascii=False, indent=2)
        
    print(f"成功构建离线数据库！共收集了 {len(birds_dict)} 种鸟类数据。")
    print("文件已保存为 china_birds.json")

if __name__ == "__main__":
    build_database()
