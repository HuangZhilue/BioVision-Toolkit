import os
import json
import shutil

# Map of groups
GROUPS = ['birds', 'mammals', 'insects', 'fishes', 'arachnids', 'plants', 'fungi', 'others']

def main():
    if not os.path.exists('offline_images'):
        os.makedirs('offline_images')
        
    for g in GROUPS:
        os.makedirs(os.path.join('offline_images', g), exist_ok=True)
        
    if os.path.exists('cached_species.json'):
        with open('cached_species.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"Loaded {len(data)} items from cached_species.json")
        
        with open('cached_others.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        # Move images
        for sci_name in data:
            filename = sci_name.replace(" ", "_").replace("/", "_") + ".jpg"
            old_path = os.path.join('offline_images', filename)
            new_path = os.path.join('offline_images', 'others', filename)
            if os.path.exists(old_path):
                shutil.move(old_path, new_path)
        
        # Rename original to avoid re-running issues
        os.rename('cached_species.json', 'cached_species.json.bak')
                
    # Also move any stray images for china_birds.json to 'birds'
    if os.path.exists('china_birds.json'):
        with open('china_birds.json', 'r', encoding='utf-8') as f:
            china_birds = json.load(f)
            
        for sci_name in china_birds:
            filename = sci_name.replace(" ", "_").replace("/", "_") + ".jpg"
            old_path = os.path.join('offline_images', filename)
            new_path = os.path.join('offline_images', 'birds', filename)
            if os.path.exists(old_path):
                shutil.move(old_path, new_path)
                
    print("Migration completed.")

if __name__ == '__main__':
    main()
