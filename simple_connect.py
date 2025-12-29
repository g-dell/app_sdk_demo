import duckdb
import os
from dotenv import load_dotenv

load_dotenv()

def simple_test():
    token = os.environ.get("motherduck_token")
    if not token:
        print("❌ No token.")
        return

    print("🚀 Connecting to 'md:' directly...")
    try:
        # Pass token via config dict which is safer/cleaner in newer versions
        # or just in the string if config param invalid
        con = duckdb.connect("md:", config={"motherduck_token": token})
        print("✅ Connected to MotherDuck root!")
        
        print("Existing Databases:")
        dbs = con.sql("SHOW DATABASES").fetchall()
        print(dbs)
        
        target_db = "mcp_app_ChatGPT"
        print(f"Switching to {target_db}...")
        con.sql(f"USE {target_db}")
        print(f"✅ Switched to {target_db}!")
        
        print("Tables:")
        print(con.sql("SHOW TABLES").fetchall())
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    simple_test()
