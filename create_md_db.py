import duckdb
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = "mcp_app_ChatGPT"

token = os.getenv("motherduck_token") or os.getenv("MOTHERDUCK_TOKEN")
if not token:
    raise SystemExit(
        "Manca il token MotherDuck. In PowerShell:\n"
        '$env:motherduck_token="IL_TUO_TOKEN"\n'
        "poi rilancia python create_md_db.py"
    )

con = duckdb.connect(f"md:{DB_NAME}?motherduck_token={token}")
con.sql(f"CREATE DATABASE IF NOT EXISTS {DB_NAME};")
con.sql(f"USE {DB_NAME};")

print("OK. Current database:", con.sql("SELECT current_database();").fetchone()[0])
print("Databases visible:", con.sql("SHOW DATABASES;").fetchall())

con.close()
