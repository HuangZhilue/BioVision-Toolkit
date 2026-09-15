import requests
import json
import time
import os

provinces_map = {
    "北京": "Beijing",
    "天津": "Tianjin",
    "河北": "Hebei",
    "山西": "Shanxi",
    "内蒙古": "Inner Mongolia",
    "辽宁": "Liaoning",
    "吉林": "Jilin",
    "黑龙江": "Heilongjiang",
    "上海": "Shanghai",
    "江苏": "Jiangsu",
    "浙江": "Zhejiang",
    "安徽": "Anhui",
    "福建": "Fujian",
    "江西": "Jiangxi",
    "山东": "Shandong",
    "河南": "Henan",
    "湖北": "Hubei",
    "湖南": "Hunan",
    "广东": "Guangdong",
    "广西": "Guangxi",
    "海南": "Hainan",
    "重庆": "Chongqing",
    "四川": "Sichuan",
    "贵州": "Guizhou",
    "云南": "Yunnan",
    "西藏": "Tibet",
    "陕西": "Shaanxi",
    "甘肃": "Gansu",
    "青海": "Qinghai",
    "宁夏": "Ningxia",
    "新疆": "Xinjiang",
    "台湾": "Taiwan",
    "香港": "Hong Kong",
    "澳门": "Macau"
}

def get_place_id(query_name):
    url = f"https://api.inaturalist.org/v1/places/autocomplete?q={query_name}"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        for place in data.get("results", []):
            # Try to ensure it's in China (ancestor 6903) or Taiwan (ancestor 97394)
            ancestors = place.get("ancestor_place_ids", [])
            if 6903 in ancestors or 97394 in ancestors or place.get("name") == "Taiwan":
                return place["id"]
        # Fallback to first result
        if data.get("results"):
            return data["results"][0]["id"]
    except Exception as e:
        print(f"Error fetching place_id for {query_name}: {e}")
    return None

def main():
    db_path = "china_birds.json"
    if not os.path.exists(db_path):
        print(f"{db_path} not found.")
        return
        
    with open(db_path, "r", encoding="utf-8") as f:
        birds_db = json.load(f)
        
    # Initialize empty provinces list for all birds
    for sci_name in birds_db:
        birds_db[sci_name]["provinces"] = []
        
    for ch_name, eng_name in provinces_map.items():
        print(f"Processing {ch_name} ({eng_name})...")
        place_id = get_place_id(eng_name)
        if not place_id:
            print(f"  -> Could not find place_id for {eng_name}")
            continue
            
        print(f"  -> Place ID: {place_id}")
        
        # Fetch top 1000 birds in this province
        url = f"https://api.inaturalist.org/v1/observations/species_counts?place_id={place_id}&taxon_id=3&per_page=1000"
        try:
            res = requests.get(url, timeout=15)
            data = res.json()
            results = data.get("results", [])
            
            matched_count = 0
            for item in results:
                sci_name = item.get("taxon", {}).get("name")
                if sci_name in birds_db:
                    if ch_name not in birds_db[sci_name]["provinces"]:
                        birds_db[sci_name]["provinces"].append(ch_name)
                    matched_count += 1
            print(f"  -> Found {len(results)} birds, matched {matched_count} in local DB.")
        except Exception as e:
            print(f"  -> Error fetching birds for {ch_name}: {e}")
            
        time.sleep(1) # Be nice to the API
        
    # Save back to JSON
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(birds_db, f, ensure_ascii=False, indent=2)
        
    print("Database updated with provincial regions!")

if __name__ == "__main__":
    main()
