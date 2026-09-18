import requests
import json
import time
import os

provinces_map = {
    "北京": "Beijing", "天津": "Tianjin", "河北": "Hebei", "山西": "Shanxi", "内蒙古": "Inner Mongolia",
    "辽宁": "Liaoning", "吉林": "Jilin", "黑龙江": "Heilongjiang", "上海": "Shanghai", "江苏": "Jiangsu",
    "浙江": "Zhejiang", "安徽": "Anhui", "福建": "Fujian", "江西": "Jiangxi", "山东": "Shandong",
    "河南": "Henan", "湖北": "Hubei", "湖南": "Hunan", "广东": "Guangdong", "广西": "Guangxi",
    "海南": "Hainan", "重庆": "Chongqing", "四川": "Sichuan", "贵州": "Guizhou", "云南": "Yunnan",
    "西藏": "Tibet", "陕西": "Shaanxi", "甘肃": "Gansu", "青海": "Qinghai", "宁夏": "Ningxia",
    "新疆": "Xinjiang", "台湾": "Taiwan", "香港": "Hong Kong", "澳门": "Macau"
}

def fetch_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            pass
        time.sleep(2)
    return None

def get_place_id(query_name):
    url = f"https://api.inaturalist.org/v1/places/autocomplete?q={query_name}"
    data = fetch_with_retry(url)
    if data:
        for place in data.get("results", []):
            ancestors = place.get("ancestor_place_ids") or []
            if 6903 in ancestors or 97394 in ancestors or place.get("name") == "Taiwan":
                return place["id"]
        if data.get("results"):
            return data["results"][0]["id"]
    return None

def main():
    print("开始完美构建中国鸟类全量数据库 (包含所有鸟种、科属、分布省份)...")
    place_id = 6903
    taxon_id = 3
    locale = 'zh-CN'
    birds_dict = {}

    # 1. Fetch ALL birds in China using pagination
    print("\n[1/3] 正在抓取全量鸟种名单...")
    page = 1
    while True:
        url = f"https://api.inaturalist.org/v1/observations/species_counts?place_id={place_id}&taxon_id={taxon_id}&locale={locale}&per_page=500&page={page}"
        print(f"  -> 正在抓取第 {page} 页...")
        data = fetch_with_retry(url)
        if not data or not data.get("results"):
            break
            
        results = data.get("results", [])
        for item in results:
            taxon = item.get("taxon", {})
            sci_name = taxon.get("name")
            tid = taxon.get("id")
            if sci_name and tid:
                ch_name = taxon.get("preferred_common_name") or taxon.get("english_common_name")
                photo_url = None
                default_photo = taxon.get("default_photo")
                if default_photo and default_photo.get("medium_url"):
                    photo_url = default_photo.get("medium_url")
                
                birds_dict[sci_name] = {
                    "taxon_id": tid,
                    "chinese_name": ch_name,
                    "image_url": photo_url,
                    "family": "Unknown",
                    "provinces": []
                }
        if len(results) < 500:
            break
        page += 1
        time.sleep(1)

    print(f"成功获取 {len(birds_dict)} 种鸟类！")

    # 2. Fetch Family information in chunks
    print("\n[2/3] 正在获取科(family)分类信息...")
    taxon_items = list(birds_dict.items())
    chunk_size = 30
    for i in range(0, len(taxon_items), chunk_size):
        chunk = taxon_items[i:i+chunk_size]
        ids = [str(item[1]["taxon_id"]) for item in chunk]
        taxa_url = f"https://api.inaturalist.org/v1/taxa/{','.join(ids)}?locale={locale}"
        print(f"  -> 正在抓取分类详情... ({min(i+chunk_size, len(taxon_items))}/{len(taxon_items)})")
        
        data = fetch_with_retry(taxa_url)
        if data:
            for t in data.get("results", []):
                sci_name = t.get("name")
                family_name = "Unknown"
                for anc in t.get("ancestors", []):
                    if anc.get("rank") == "family":
                        family_name = anc.get("name") or "Unknown"
                        break
                if sci_name in birds_dict:
                    birds_dict[sci_name]["family"] = family_name
        time.sleep(1)

    # 3. Fetch Provinces for all birds
    print("\n[3/3] 正在匹配全国各省份分布记录 (由于使用多页遍历，这可能需要几分钟)...")
    for ch_name, eng_name in provinces_map.items():
        pid = get_place_id(eng_name)
        if not pid:
            print(f"  -> 找不到 {ch_name} 的地区ID，跳过。")
            continue
            
        print(f"  -> 正在扫描 {ch_name}...")
        p_page = 1
        while True:
            url = f"https://api.inaturalist.org/v1/observations/species_counts?place_id={pid}&taxon_id=3&per_page=500&page={p_page}"
            data = fetch_with_retry(url)
            if not data or not data.get("results"):
                break
                
            results = data.get("results", [])
            for item in results:
                sci_name = item.get("taxon", {}).get("name")
                if sci_name in birds_dict:
                    if ch_name not in birds_dict[sci_name]["provinces"]:
                        birds_dict[sci_name]["provinces"].append(ch_name)
                        
            if len(results) < 500:
                break
            p_page += 1
            time.sleep(1)
            
    # Save to file
    with open("china_birds.json", "w", encoding="utf-8") as f:
        json.dump(birds_dict, f, ensure_ascii=False, indent=2)
        
    print(f"\n==============================================")
    print(f"太棒了！离线数据库 china_birds.json 重建完成！")
    print(f"最终共收录了 {len(birds_dict)} 种鸟类，均已包含图片URL、科属和分布省份！")
    print(f"==============================================")

if __name__ == "__main__":
    main()
