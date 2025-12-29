import duckdb, json, os, uuid
from dotenv import load_dotenv

load_dotenv()

DB_NAME = "mcp_app_ChatGPT"

token = os.getenv("motherduck_token") or os.getenv("MOTHERDUCK_TOKEN")
if not token:
    raise SystemExit('Setta $env:motherduck_token="TOKEN" prima.')

os.environ["motherduck_token"] = token
con = duckdb.connect(f"md:{DB_NAME}")
con.sql(f"USE {DB_NAME};")

with open("data/products_seed.json", "r", encoding="utf-8") as f:
    products = json.load(f)

for p in products:
    product_id = str(uuid.uuid4())
    con.execute(
        "INSERT INTO products VALUES (?, ?, ?, ?)",
        [product_id, p["name"], p.get("description",""), float(p["base_price"])]
    )

    for k, v in (p.get("attributes") or {}).items():
        con.execute("INSERT INTO product_attributes VALUES (?, ?, ?)", [product_id, k, str(v)])

    for v in (p.get("variants") or []):
        sku = v["sku"]
        con.execute("INSERT INTO variants VALUES (?, ?, ?)", [sku, product_id, int(v.get("inventory_quantity",0))])
        for ak, av in (v.get("attributes") or {}).items():
            con.execute("INSERT INTO variant_attributes VALUES (?, ?, ?)", [sku, ak, str(av)])

print("✅ Seed completato.")
print("Products:", con.sql("SELECT COUNT(*) FROM products;").fetchone()[0])
print("Variants:", con.sql("SELECT COUNT(*) FROM variants;").fetchone()[0])

con.close()
