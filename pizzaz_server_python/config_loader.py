import json
from pathlib import Path
from pydantic import BaseModel, ValidationError
from typing import List, Optional, Any, Dict
from pydantic import Field

# Ridefinizione dei modelli necessari per la configurazione (copiati/adattati da main.py o definiti qui per chiarezza)
class FilterDefinition(BaseModel):
    id: str
    label: str
    type: str # enum, range, boolean
    attribute_name: Optional[str] = None

class SortOptionDefinition(BaseModel):
    id: str
    label: str
    default: Optional[bool] = False

class AttributeDefinition(BaseModel):
    # La struttura nel JSON sembra essere un dizionario di definizioni di attributi, 
    # ma pydantic si aspetta campi specifici. 
    # Adattiamo il modello per accettare un dict arbitrario di definizioni di attributi
    pass
    # In alternativa, se la struttura è fissa (size, color, material...), la definiamo esplicitamente.
    # Ma il JSON ha "product_attributes": { "size": {...}, ... }
    # Quindi usiamo Dict[str, Any] per flessibilità o definiamo un modello per il singolo attributo.

class SingleAttributeConfig(BaseModel):
    type: str
    enum: Optional[List[str]] = None
    display_name: str
    filterable: Optional[bool] = False

class AssistantPolicy(BaseModel):
    tone_of_voice: str
    do_and_donts: List[str]

class VerticalProfileConfig(BaseModel):
    name: str
    description: str
    product_attributes: Dict[str, SingleAttributeConfig]
    variant_attributes: Dict[str, SingleAttributeConfig]
    default_filters: Dict[str, Any]
    default_sorts: List[Dict[str, str]] # Semplicificato rispetto al main per matchare il JSON
    product_description_template: str
    assistant_policy: AssistantPolicy

def load_vertical_profile(file_path: str = "vertical_profile.json") -> VerticalProfileConfig:
    path = Path(__file__).parent / file_path
    if not path.exists():
        raise FileNotFoundError(f"Vertical profile configuration file not found at {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            # Validazione Pydantic
            profile = VerticalProfileConfig(**data)
            return profile
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON from {path}: {e}")
        except ValidationError as e:
             raise ValueError(f"Error validating vertical profile configuration: {e}")
