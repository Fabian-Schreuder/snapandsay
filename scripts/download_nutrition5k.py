import os
import httpx
import random
import csv
from pathlib import Path
import argparse
import time

BASE_URL = "https://storage.googleapis.com/nutrition5k_dataset/nutrition5k_dataset"
METADATA_FILES = [
    "metadata/ingredients_metadata.csv",
    "metadata/dish_metadata_cafe1.csv",
    "metadata/dish_metadata_cafe2.csv",
]
# Resolve data dir relative to project root (assuming script is in scripts/)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "nutrition5k"

def download_file(client, url, dest_path):
    if dest_path.exists():
        # print(f"Skipping {dest_path.name}, already exists.")
        return True
    
    # print(f"Downloading {url} to {dest_path}...")
    try:
        resp = client.get(url, timeout=30.0, follow_redirects=True)
        if resp.status_code == 404:
            print(f"Warning: 404 for {url}")
            return False
            
        resp.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(resp.content)
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=500, help="Number of images to sample")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    print(f"Starting Nutrition5k downloader with seed={args.seed}, limit={args.limit}")
    
    random.seed(args.seed)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    with httpx.Client() as client:
        # 1. Download Metadata
        print("Downloading metadata files...")
        for rel_path in METADATA_FILES:
            url = f"{BASE_URL}/{rel_path}"
            dest = DATA_DIR / rel_path
            success = download_file(client, url, dest)
            if not success:
                print(f"CRITICAL: Failed to download metadata {rel_path}")
                return
            
        # 2. Parse Dish IDs
        dish_ids = []
        for meta_file in ["metadata/dish_metadata_cafe1.csv", "metadata/dish_metadata_cafe2.csv"]:
            p = DATA_DIR / meta_file
            if not p.exists(): continue
            
            with open(p, "r") as f:
                reader = csv.reader(f)
                count = 0
                for row in reader:
                    if row:
                        dish_ids.append(row[0])
                        count += 1
                print(f"Loaded {count} dishes from {meta_file}")
                        
        print(f"Found {len(dish_ids)} total dishes.")
        
        # 3. Stratify/Sample
        selected_ids = random.sample(dish_ids, min(args.limit, len(dish_ids)))
        print(f"Selected {len(selected_ids)} dishes for image download.")
        
        # 4. Download Images
        img_dir_base = DATA_DIR / "imagery/realsense_overhead"
        img_dir_base.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        for i, dish_id in enumerate(selected_ids):
            url = f"{BASE_URL}/imagery/realsense_overhead/{dish_id}/rgb.png"
            dest = img_dir_base / dish_id / "rgb.png"
            
            if i % 10 == 0:
                print(f"[{i+1}/{len(selected_ids)}] Processed {success_count} successful downloads...")
                
            if download_file(client, url, dest):
                success_count += 1
            
            # Rate limiting
            # time.sleep(0.05)
            
    print(f"Download complete. {success_count}/{len(selected_ids)} images downloaded.")

if __name__ == "__main__":
    main()
