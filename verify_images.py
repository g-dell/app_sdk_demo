from pizzaz_server_python.database import get_all_products
import os
from dotenv import load_dotenv

load_dotenv()

try:
    products = get_all_products()
    print(f"Found {len(products)} products.")
    for p in products[:3]: # Show first 3
        print(f"Product: {p.name}")
        print(f"  Media count: {len(p.media) if p.media else 0}")
        if p.media:
            print(f"  First image: {p.media[0].url}")
            
except Exception as e:
    print(f"Error fetching products: {e}")
