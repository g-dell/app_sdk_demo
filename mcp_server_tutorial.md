# Guida Completa: Creare un Server MCP (Model Context Protocol) da Zero

Questa guida ti accompagnerà passo dopo passo nella creazione di un server MCP in Python, simile a quello che abbiamo costruito insieme ("Pizzaz"). Imparerai a esporre dati e funzionalità (Tools) agli assistenti AI come ChatGPT.

---

## Prerequisiti

*   **Python 3.10+** installato.
*   Un editor di codice (VS Code consigliato).
*   (Opzionale) Un account **MotherDuck** per il database cloud (altrimenti useremo DuckDB locale).

---

## Step 1: Setup del Progetto

Crea una cartella per il tuo progetto e prepara l'ambiente virtuale.

```bash
# 1. Crea la cartella
mkdir my_mcp_shop
cd my_mcp_shop

# 2. Crea ambiente virtuale
python -m venv .venv

# 3. Attiva ambiente (Windows)
.venv\Scripts\activate
# (Mac/Linux: source .venv/bin/activate)

# 4. Installa le dipendenze
pip install "mcp[fastapi]" uvicorn duckdb python-dotenv pydantic
```

*   `mcp[fastapi]`: Il framework ufficiale MCP.
*   `uvicorn`: Server web per eseguire l'applicazione.
*   `duckdb`: Database SQL veloce e leggero.
*   `pydantic`: Per definire la struttura dei dati.

---

## Step 2: La Struttura dei File

Crea questa struttura di base:

```text
my_mcp_shop/
├── .env                 # File per le password/token (segreto!)
├── main.py              # Il cuore del server
├── database.py          # Gestione dati
└── seed_data.json       # Dati di esempio
```

---

## Step 3: Il Database (`database.py`)

Creiamo un modulo per gestire i dati. Useremo **DuckDB**, che può funzionare sia in memoria (volatile) che collegato al cloud (persistente).

Crea `database.py`:

```python
import duckdb
import os
from dotenv import load_dotenv

load_dotenv() # Carica variabili da .env

def get_connection():
    # Se abbiamo un token MotherDuck, ci connettiamo al cloud
    token = os.getenv("MOTHERDUCK_TOKEN")
    if token:
        return duckdb.connect(f"md:my_shop?motherduck_token={token}")
    
    # Altrimenti usiamo un DB in memoria per test
    return duckdb.connect(":memory:")

CONN = get_connection()

# Inizializza le tabelle
def init_db():
    CONN.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id VARCHAR PRIMARY KEY,
            name VARCHAR,
            price DOUBLE,
            description VARCHAR
        )
    """)
    # Aggiungiamo un prodotto di prova se vuoto
    if CONN.execute("SELECT count(*) FROM products").fetchone()[0] == 0:
        CONN.execute("INSERT INTO products VALUES ('1', 'T-Shirt MCP', 19.99, 'Maglietta fantastica')")

init_db()

def get_all_products():
    # Restituisce una lista di dizionari
    results = CONN.execute("SELECT * FROM products").fetchall()
    # Mappiamo i risultati (id, name, price, desc) in dizionari
    return [
        {"id": r[0], "name": r[1], "price": r[2], "description": r[3]} 
        for r in results
    ]
```

---

## Step 4: Il Server MCP (`main.py`)

Ora creiamo il server vero e proprio usando `FastMCP`. Definiremo un **Tool** che l'AI potrà chiamare.

Crea `main.py`:

```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
import database # Importiamo il nostro modulo database

# Inizializza il server MCP
mcp = FastMCP("My Shop Server")

# --- DEFINIZIONE INPUT ---
# Definiamo cosa l'AI deve passarci per cercare prodotti
class SearchInput(BaseModel):
    query: str = Field(description="Cosa stai cercando? es. 'maglietta'")

# --- DEFINIZIONE TOOLS ---

@mcp.tool()
def search_products(args: SearchInput) -> str:
    """Cerca prodotti nel catalogo del negozio."""
    
    products = database.get_all_products()
    
    # Filtriamo in Python (per semplicità)
    found = [
        p for p in products 
        if args.query.lower() in p['name'].lower() 
        or args.query.lower() in p['description'].lower()
    ]
    
    if not found:
        return "Nessun prodotto trovato."
    
    # Formattiamo la risposta per l'AI
    result_text = "Ecco i prodotti trovati:\n"
    for p in found:
        result_text += f"- {p['name']} (€ {p['price']}): {p['description']}\n"
        
    return result_text

# --- AVVIO ---
if __name__ == "__main__":
    import uvicorn
    # Avvia il server sulla porta 8000
    uvicorn.run("main:mcp", host="0.0.0.0", port=8000, reload=True)
```

> **Nota**: `main:mcp` dice a uvicorn di cercare l'oggetto `mcp` dentro il file `main.py`. FastMCP crea automaticamente un'app compatibile.

---

## Step 5: Avviare e Testare

1.  Apri il terminale nella cartella del progetto.
2.  Esegui:
    ```bash
    python main.py
    ```
3.  Vedrai: `Uvicorn running on http://0.0.0.0:8000`.

### Come si usa?
Questo è un server **SSE (Server-Sent Events)** con endpoint MCP.
Per usarlo con ChatGPT (o Claude Desktop):
1.  Serve un client MCP o il "Connector" di OpenAI.
2.  L'URL di configurazione sarà solitamente quello dove gira il server (es. via tunnel `ngrok` se sei in cloud, o localhost per app desktop).

## Step Extra: Collegamento con MotherDuck

Se vuoi rendere i dati persistenti:
1.  Vai su [MotherDuck.com](https://motherduck.com) e prendi il tuo token.
2.  Crea un file `.env`:
    ```env
    MOTHERDUCK_TOKEN=tuo_token_lunghissimo
    ```
3.  Il codice in `database.py` rileverà automaticamente il token e si connetterà al cloud invece che alla memoria locale!

---

## Concetti Chiave Imparati

1.  **FastMCP**: Libreria che semplifica tantissimo la creazione di server. Basta usare `@mcp.tool()` sopra una funzione Python.
2.  **Pydantic**: Fondamentale per dire all'AI *esattamente* che dati ci aspettiamo (schema rigoroso).
3.  **Separazione**: Tenere il DB separato dalla logica server (`database.py` vs `main.py`) evita confusione e problemi tecnici (import circulari).
