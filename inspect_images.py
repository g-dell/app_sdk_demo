import duckdb
import os
from dotenv import load_dotenv

load_dotenv()
token = os.environ.get("motherduck_token")
try:
    conn = duckdb.connect(f"md:mcp_app_ChatGPT?motherduck_token={token}")
    print(conn.execute("DESCRIBE images").fetchall())
except Exception as e:
    print(f"Error: {e}")
