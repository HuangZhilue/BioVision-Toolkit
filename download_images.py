import json
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_image(sci_name, image_url, output_dir):
    if not image_url:
        return
    
    # Safe filename
    filename = sci_name.replace(" ", "_").replace("/", "_") + ".jpg"
    filepath = os.path.join(output_dir, filename)
    
    # Skip if already downloaded
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        return

    for attempt in range(3):
        try:
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return  # Success
            elif response.status_code == 404:
                print(f"Image not found (404) for {sci_name}")
                return # No point in retrying a 404
        except Exception as e:
            if attempt == 2:
                print(f"Failed to download {sci_name} after 3 attempts: {e}")

def main():
    json_path = "database/china_birds.json"
    output_dir = os.path.join("offline_images", "birds")
    
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return
        
    os.makedirs(output_dir, exist_ok=True)
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"Starting download for {len(data)} images...")
    
    # Use 10 threads to download concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for sci_name, info in data.items():
            image_url = info.get("image_url")
            if image_url:
                futures.append(executor.submit(download_image, sci_name, image_url, output_dir))
                
        # Wait for all to complete
        for i, future in enumerate(as_completed(futures), 1):
            if i % 100 == 0:
                print(f"Downloaded {i}/{len(futures)} images...")
                
    print(f"All images downloaded to {output_dir}/")

if __name__ == "__main__":
    main()
