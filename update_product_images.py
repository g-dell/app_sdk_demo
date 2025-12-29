import duckdb
import os
import json
import random
from dotenv import load_dotenv

load_dotenv()

# Configuration
DB_NAME = "mcp_app_ChatGPT"
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
STATIC_PATH = "/static/images"
DATASET_PATH = os.path.join(os.getcwd(), "archive", "Clothes_Dataset")

def get_db_connection():
    token = os.environ.get("motherduck_token")
    if token:
        print("Connecting to MotherDuck...")
        return duckdb.connect(f"md:{DB_NAME}?motherduck_token={token}")
    else:
        print("Connecting to local DuckDB...")
        return duckdb.connect("local.db") # O :memory: se non vogliamo persistere

def get_image_map():
    """Scans dataset folder and returns a map {folder_name: [list of files]}."""
    image_map = {}
    if not os.path.exists(DATASET_PATH):
        print(f"Dataset path not found: {DATASET_PATH}")
        return {}

    for folder in os.listdir(DATASET_PATH):
        folder_path = os.path.join(DATASET_PATH, folder)
        if os.path.isdir(folder_path):
            files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            if files:
                image_map[folder] = files
    return image_map

def map_product_to_folder(product_name):
    """Simple heuristic to map product name to folder."""
    name = product_name.lower()
    if "t-shirt" in name or "kaos" in name: return "Kaos"
    if "shirt" in name: return "Kemeja" # Generic shirt but not t-shirt
    if "jacket" in name: return "Jaket"
    if "hoodie" in name: return "Hoodie"
    if "jeans" in name: return "Jeans"
    if "shorts" in name: return "Celana_Pendek"
    if "dress" in name: return "Gaun"
    if "sweater" in name: return "Sweter"
    if "blazer" in name: return "Blazer"
    if "coat" in name or "mantel" in name: return "Mantel"
    if "skirt" in name or "rok" in name: return "Rok"
    return None

def update_images():
    conn = get_db_connection()
    image_map = get_image_map()
    
    products = conn.execute("SELECT product_id, name FROM products").fetchall()
    print(f"Found {len(products)} products.")

    for pid, name in products:
        folder = map_product_to_folder(name)
        if folder and folder in image_map:
            # Pick a random image
            bg_image = random.choice(image_map[folder])
            image_url = f"{BASE_URL}{STATIC_PATH}/{folder}/{bg_image}"
            
            # Create Media JSON
            media_json = json.dumps([{
                "url": image_url,
                "alt_text": name,
                "type": "image"
            }])
            
            # Update DB - Update products table 'media' column
            # Note: The schema might not have 'media' column in 'products' table if it was created strictly from init_schema.py 
            # Check init_schema.py: 'media VARCHAR' is in the create statement in my memory? 
            # Re-checking init_schema.py content from logs... yes 'media VARCHAR' might be missing if I used the simpler schema.
            # Let's check schema first.
            try:
                conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS media VARCHAR")
                conn.execute("UPDATE products SET media = ? WHERE product_id = ?", [media_json, pid])
                print(f"Updated {name} with {image_url}")
            except Exception as e:
                print(f"Error updating {name}: {e}")
        else:
            print(f"No folder match for {name}")

if __name__ == "__main__":
    update_images()
