import uuid
import os
import random
from pathlib import Path
from typing import Dict, Any, List
# Removed unused imports from main


def clean_name(filename: str) -> str:
    """Rimuove estensioni e caratteri strani dal nome del file per farne un nome prodotto leggibile."""
    name = Path(filename).stem
    # Sostituisci _ con spazio e rimuovi numeri/uuid eccessivi se necessario
    # Esempio: blazer_cerbruti_1888_size_m_1684926636 -> Blazer Cerbruti 1888 Size M
    parts = name.split('_')
    # Filtra parti numeriche lunghe (timestamp/uuid)
    clean_parts = [p for p in parts if not (p.isdigit() and len(p) > 6) and len(p) < 30] 
    return " ".join(clean_parts).title()

def get_random_attribute(attr_name: str, profile_attributes: Dict[str, Any]) -> Any:
    """Recupera un valore random valido per un attributo dal profilo."""
    if attr_name not in profile_attributes:
        return None
    
    attr_config = profile_attributes[attr_name]
    if attr_config.enum:
        return random.choice(attr_config.enum)
    return "Default" # Fallback per stringhe libere

def seed_data():
    print("Data seeding from local 'archive' folder is disabled. Data is managed via Mother Duck.")
    # The original local seeding logic has been removed to avoid dependency on the 'archive' folder.