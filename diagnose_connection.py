import duckdb
import os
from dotenv import load_dotenv

load_dotenv()

def diagnose():
    print("🔍 Diagnostic start.")
    token = os.environ.get("motherduck_token")
    if not token:
        print("❌ No token found.")
        return

    print(f"Token present (len={len(token)}).")
    
    try:
        # Create a local in-memory conn first without MD
        con = duckdb.connect()
        print("local conn created.")
        
        print("Installing motherduck extension...")
        con.sql("INSTALL motherduck;")
        print("Loading motherduck extension...")
        con.sql("LOAD motherduck;")
        print("MotherDuck extension loaded.")
        
        print("Connecting to service...")
        # Now try to attach or connect
        # We use strict mode to fail fast?
        print("Setting token...")
        con.sql(f"SET motherduck_token='{token}'")
        print("Token set.")
        
        print("Attaching to MotherDuck generic (md:)...")
        con.sql("ATTACH 'md:' AS md_root")
        print("✅ Attached successfully to root!")
        
        print("Databases:")
        print(con.sql("SHOW DATABASES").fetchall())
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    diagnose()
