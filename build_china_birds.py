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
    
    # 获取前 1500 种中国最常见的鸟类 (3页)
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
            if sci_name:
                chinese_name = taxon.get("preferred_common_name")
                # 如果没有中文名，尽量保留一个英文俗名或保持为空
                if not chinese_name:
                    chinese_name = taxon.get("english_common_name")
                
                photo_url = None
                default_photo = taxon.get("default_photo")
                if default_photo and default_photo.get("medium_url"):
                    photo_url = default_photo.get("medium_url")
                
                birds_dict[sci_name] = {
                    "chinese_name": chinese_name,
                    "image_url": photo_url
                }
                
        # 遵守 iNaturalist 礼仪，防止请求过快
        time.sleep(1)
        
    # 保存到 JSON 文件
    with open("china_birds.json", "w", encoding="utf-8") as f:
        json.dump(birds_dict, f, ensure_ascii=False, indent=2)
        
    print(f"成功构建离线数据库！共收集了 {len(birds_dict)} 种鸟类数据。")
    print("文件已保存为 china_birds.json")

if __name__ == "__main__":
    build_database()
