import sys
from dotenv import load_dotenv
load_dotenv()

from pizzaz_server_python.seed_data import seed_data

if __name__ == "__main__":
    print("🚀 Starting data seeding...")
    try:
        seed_data()
        print("✅ Seeding completed successfully.")
    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        sys.exit(1)
