import duckdb
import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()

def test_connection():
    token = os.environ.get("motherduck_token")
    if not token:
        print("❌ Nessun token 'motherduck_token' trovato nelle variabili d'ambiente.")
        print("   -> Il sistema userà DuckDB in-memory (locale).")
        return

    print(f"miniconda found token: {token[:5]}...{token[-5:]} (mascherato)")
    
    try:
        print("🔄 Tentativo di connessione a MotherDuck...")
        # Usa la stessa stringa di connessione del server
        conn = duckdb.connect(f"md:mcp_app_ChatGPT?motherduck_token={token}")
        print("✅ Connessione riuscita!")
        
        # Test query
        print("   Esecuzione query di test (SELECT 1)...")
        res = conn.execute("SELECT 1").fetchall()
        print(f"   Risultato: {res}")
        
    except Exception as e:
        print("\n❌ ERRORE DI CONNESSIONE:")
        print(e)
        print("\nSUGGERIMENTI:")
        print("1. Controlla che il token in .env sia corretto e non scaduto.")
        print("2. Verifica che il database 'mcp_app_ChatGPT' esista su MotherDuck.")
        print("3. Se vuoi usare il DB locale, rimuovi o commenta 'motherduck_token' nel file .env")

if __name__ == "__main__":
    test_connection()
