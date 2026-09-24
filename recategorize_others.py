import json
import os
import requests
import shutil
import time

GROUPS = ['birds', 'mammals', 'insects', 'fishes', 'arachnids', 'plants', 'fungi', 'amphibians', 'reptiles', 'mollusks', 'others']

def get_group_from_ancestors(ancestor_ids):
    group_name = "others"
    if not ancestor_ids: return group_name
    
    for aid in ancestor_ids:
        if aid == 3: group_name = "birds"
        elif aid == 40151: group_name = "mammals"
        elif aid == 47158: group_name = "insects"
        elif aid in [47178, 11865]: group_name = "fishes"
        elif aid == 47119: group_name = "arachnids"
        elif aid == 47126: group_name = "plants"
        elif aid == 47170: group_name = "fungi"
        elif aid == 20978: group_name = "amphibians"
        elif aid == 26036: group_name = "reptiles"
        elif aid == 47115: group_name = "mollusks"
        
    if group_name == "others":
        if 1 in ancestor_ids: group_name = "animalia"
        
    return group_name

def main():
    if not os.path.exists("database/cached_others.json"):
        return
        
    with open("database/cached_others.json", "r", encoding="utf-8") as f:
        others_data = json.load(f)
        
    dbs = {g: {} for g in GROUPS}
    
    # Load existing to not overwrite
    for g in GROUPS:
        p = f"database/cached_{g}.json"
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                dbs[g] = json.load(f)
                
    remaining_others = {}
    
    for sci_name, info in list(others_data.items()):
        print(f"Processing {sci_name}...")
        try:
            res = requests.get(f"https://api.inaturalist.org/v1/taxa?q={sci_name}&is_active=true&per_page=1", timeout=5)
            if res.status_code == 200:
                data = res.json()
                if data.get("results"):
                    match = data["results"][0]
                    target_group = get_group_from_ancestors(match.get("ancestor_ids", []))
                    
                    if target_group != "others":
                        # Move to target group
                        dbs[target_group][sci_name] = info
                        # Move image
                        filename = sci_name.replace(" ", "_").replace("/", "_") + ".jpg"
                        old_path = os.path.join("offline_images", "others", filename)
                        new_path = os.path.join("offline_images", target_group, filename)
                        os.makedirs(os.path.join("offline_images", target_group), exist_ok=True)
                        if os.path.exists(old_path):
                            shutil.move(old_path, new_path)
                        continue
            
            # If we reach here, it failed to categorize, keep in others
            remaining_others[sci_name] = info
            
        except Exception as e:
            print(f"Error for {sci_name}: {e}")
            remaining_others[sci_name] = info
        time.sleep(0.5) # rate limit
        
    # Save back
    for g in GROUPS:
        if g == "others":
            with open(f"database/cached_{g}.json", "w", encoding="utf-8") as f:
                json.dump(remaining_others, f, ensure_ascii=False, indent=2)
        else:
            if dbs[g]:
                with open(f"database/cached_{g}.json", "w", encoding="utf-8") as f:
                    json.dump(dbs[g], f, ensure_ascii=False, indent=2)
                    
    print("Recategorization complete.")

if __name__ == "__main__":
    main()
