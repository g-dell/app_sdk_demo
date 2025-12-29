import duckdb
import os
from dotenv import load_dotenv

load_dotenv()


DB_NAME = "mcp_app_ChatGPT"

token = os.getenv("motherduck_token") or os.getenv("MOTHERDUCK_TOKEN")
if not token:
    raise SystemExit('Setta $env:motherduck_token="TOKEN" prima.')

# usa env var (pulito) oppure query param, va bene entrambi
# usa env var (pulito) oppure query param, va bene entrambi
print(f"Connecting to MotherDuck with token: {token[:5]}...")
try:
    con = duckdb.connect("md:", config={"motherduck_token": token})
    print("✅ Connected to MD root.")
    con.sql(f"USE {DB_NAME};")
    print(f"✅ Switched to {DB_NAME}.")
except Exception as e:
    print(f"❌ Initial connection failed: {e}")
    # Retry logic or exit
    raise e

con.sql("""
CREATE TABLE IF NOT EXISTS products (
  product_id VARCHAR PRIMARY KEY,
  name VARCHAR,
  description VARCHAR,
  base_price DOUBLE
);
""")

con.sql("""
CREATE TABLE IF NOT EXISTS product_attributes (
  product_id VARCHAR,
  key VARCHAR,
  value VARCHAR
);
""")

con.sql("""
CREATE TABLE IF NOT EXISTS variants (
  sku VARCHAR PRIMARY KEY,
  product_id VARCHAR,
  inventory_quantity BIGINT
);
""")

con.sql("""
CREATE TABLE IF NOT EXISTS variant_attributes (
  sku VARCHAR,
  key VARCHAR,
  value VARCHAR
);
""")

con.sql("""
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id VARCHAR PRIMARY KEY,
    cart_id VARCHAR,
    created_at VARCHAR
);
""")

con.sql("""
CREATE TABLE IF NOT EXISTS carts (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR,
    subtotal DOUBLE,
    discount DOUBLE,
    total DOUBLE,
    currency VARCHAR,
    last_updated_at VARCHAR
);
""")

con.sql("""
CREATE TABLE IF NOT EXISTS cart_items (
    product_id VARCHAR,
    variant_id VARCHAR,
    quantity INTEGER,
    unit_price DOUBLE,
    cart_id VARCHAR
);
""")

print("✅ Schema creato/aggiornato.")
print("Tables:", con.sql("SHOW TABLES;").fetchall())

con.close()
