## 8. Checklist TODO Completa (per Sviluppo Reale)

Questa sezione aggrega tutte le attività TODO identificate nelle sezioni precedenti, fornendo una checklist completa per lo sviluppo del progetto.

### 8.1 Contesto e Principi

*   [x] Verificare la coerenza dei principi con l'implementazione effettiva.
*   [ ] Documentare eventuali deviazioni dai principi per giustificarle.

### 8.2 Architettura Modulare

*   [x] Definire la struttura dettagliata dei moduli UI (`src/`).
    *   `src/nome-app/index.jsx|tsx` (entry point)
    *   `src/nome-app/components/` (componenti specifici dell'app)
    *   `src/nome-app/hooks/` (custom hooks specifici dell'app)
    *   `src/nome-app/types/` (tipi specifici dell'app, per TS)
    *   `src/nome-app/utils/` (utility specifiche dell'app)
    *   Utilizzo di hooks e utility globali da `src/` root.

*   [x] Implementare il processo di build e verifica degli asset in `assets/`.
*   [x] Sviluppare il server MCP (`pizzaz_server_python` esteso) con endpoint e gestione dei tool (CRUD per tutte le entità implementato).
*   [x] Creare il primo prototipo del "Vertical Profile" e un meccanismo per la sua lettura (`config_loader.py`).
*   [x] Preparare l'ambiente di sviluppo per lo storage in-memory (fallback in `main.py`).
*   [x] Individuare e documentare il database per la produzione (MotherDuck).
*   [ ] Aggiornare `README.md` con le istruzioni per l'avvio e la configurazione del nuovo progetto.

### 8.3 Schema Dati Minimo

*   [x] Finalizzare lo schema dati per le entità principali, includendo tutti i campi necessari (`init_schema.py` per MotherDuck).
*   [x] Definire un esempio di "Vertical Profile" per il vertical "Vestiti" che specifichi gli attributi dinamici per Product e Variant (`vertical_profile.json`).
*   [x] Implementare i modelli dati nel backend (`pizzaz_server_python`) in modo da supportare lo schema definito e gli attributi dinamici.
*   [x] Preparare script di popolamento dati di esempio (in-memory per dev e `seed_md.py` per MotherDuck).

### 8.4 Design del Layer MCP

*   [x] Definire gli schemi JSON per l'input e l'output di ogni tool elencato.
*   [x] Implementare i stub per i tool nel server MCP (`pizzaz_server_python`).
*   [x] Sviluppare la logica per generare il campo `_meta["openai/outputTemplate"]` dinamicamente, in base al tool chiamato e al "Vertical Profile".
*   [x] Integrare la gestione di `widgetSessionId` e `widgetState` per i tool che richiedono la persistenza dello stato (es. carrello).
*   [ ] Creare o adattare i componenti UI (`src/`) per rispondere ai diversi `outputTemplate` e `widgetState`.

### 8.5 Strategia di Deploy su Render

*   [x] Configurare il server `pizzaz_server_python` per servire i file statici dalla directory `assets/` (o `archive/Clothes_Dataset` mappato).
*   [ ] Assicurarsi che il server utilizzi `0.0.0.0` e `os.environ.get("PORT")`.
*   [x] Implementare la logica nel server per utilizzare la variabile d'ambiente `BASE_URL` per la generazione degli URL degli asset.
*   [ ] Aggiornare le istruzioni di deploy nel `README.md` con i dettagli specifici per Render (o servizio equivalente).

### 8.6 Procedura di Collegamento in ChatGPT

*   [ ] Documentare la procedura esatta per configurare il connettore in ChatGPT (Settings > Connectors).
*   [ ] Testare il collegamento con un server MCP locale esposto tramite `ngrok`.
*   [ ] Testare il collegamento con il server MCP deployato su Render.

### 8.7 Roadmap in Milestone

*   [ ] Definire metriche di successo per ogni milestone.
*   [ ] Assegnare priorità e stimare tempi per i task di ogni milestone.
*   [ ] Allineare la roadmap con le esigenze di business e gli stakeholder.

### 8.8 Documentazione e Testing

*   [ ] **Documentazione**: Assicurarsi che `README.md` sia sempre aggiornato con le istruzioni più recenti per installazione, configurazione, avvio e deploy.
*   [ ] **Testing Minimale**: Implementare test unitari e di integrazione per le funzionalità critiche dei tool MCP e dei componenti UI.
*   [x] **Refactoring e Pulizia**: Rivedere il codice per garantire pulizia, leggibilità e conformità agli standard di codice (Separazione `main.py` e `database.py` completata).
