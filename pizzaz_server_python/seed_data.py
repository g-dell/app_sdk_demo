import uuid
import os
import random
from pathlib import Path
from typing import Dict, Any, List
# Importa le funzioni CRUD e i modelli dal modulo principale (assicurati che main.py esponga questi simboli)
from .main import (
    create_product,
    create_category,
    create_collection,
    create_variant,
    Product,
    Variant,
    Category,
    Collection,
    Media,
    VERTICAL_PROFILE,
)

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
    print("Populating database with sample data from 'archive/Clothes_Dataset'...")
    
    base_path = Path(__file__).parent.parent / "archive" / "Clothes_Dataset"
    
    if not base_path.exists():
        print(f"Warning: Dataset path {base_path} not found. Using minimal fallback data.")
        # Fallback manuale limitato se non trova le immagini
        return

    # Mappa le sottocartelle come Categorie
    categories: Dict[str, Category] = {}
    
    # Crea una collezione generica
    collection_all = create_collection(Collection(
        id=uuid.uuid4(),
        name="All Products",
        slug="all-products",
        description="Full catalog"
    ))

    # Scansione directory
    for category_dir in base_path.iterdir():
        if category_dir.is_dir():
            cat_name = category_dir.name
            print(f"Processing category: {cat_name}")
            
            # Crea Categoria
            category = create_category(Category(
                id=uuid.uuid4(),
                name=cat_name,
                slug=cat_name.lower().replace(" ", "-"),
                description=f"Category for {cat_name}"
            ))
            categories[cat_name] = category

            # Processa e limita a max 20 prodotti per categoria per non intasare il DB
            count = 0
            for image_file in category_dir.glob("*.jpg"):
                if count >= 20: break
                
                prod_name = clean_name(image_file.name)
                
                # Genera Attributi Prodotto Random (es. Materiale, Stile)
                prod_attributes = {}
                for attr_key, attr_def in VERTICAL_PROFILE.product_attributes.items():
                    val = get_random_attribute(attr_key, VERTICAL_PROFILE.product_attributes)
                    if val: prod_attributes[attr_key] = val

                # Genera Prodotto Base
                product_id = uuid.uuid4()
                # URL immagine: assumiamo che il server serva i file statici. 
                # In una vera app, caricheremmo le immagini su S3/Blob storage.
                # Qui usiamo un path relativo o un placeholder locale se servito staticamente.
                # Per ora usiamo un path fittizio che punta al file locale (il server dovrà essere configurato per servirli)
                # Il server main.py serve "assets", ma le immagini sono in "archive". 
                # Idealmente dovremmo copiare le immagini in assets o configurare un mount extra.
                # Per la demo, usiamo un URL fittizio.
                image_url = f"/static_images/{cat_name}/{image_file.name}" 

                product = create_product(Product(
                    id=product_id,
                    name=prod_name,
                    description=f"Un ottimo {prod_name} della categoria {cat_name}.",
                    slug=f"{cat_name.lower()}-{count}-{uuid.uuid4().hex[:4]}",
                    category_id=category.id,
                    collection_ids=[collection_all.id],
                    brand="GenericBrand",
                    media=[Media(url=image_url, alt_text=prod_name)],
                    base_price=random.uniform(20.0, 150.0), # Prezzo random
                    currency="EUR",
                    attributes=prod_attributes,
                    variants=[]
                ))
                
                # Genera 1-3 Varianti (Taglia/Colore)
                # Usiamo gli attributi di variante del profilo
                num_variants = random.randint(1, 3)
                seen_variants = set()
                
                for _ in range(num_variants):
                    variant_attrs = {}
                    # Costruisci combinazione unica di attributi
                    for attr_key, attr_def in VERTICAL_PROFILE.variant_attributes.items():
                         variant_attrs[attr_key] = get_random_attribute(attr_key, VERTICAL_PROFILE.variant_attributes)
                    
                    # Genera SKU semplice
                    variant_signature = "-".join([str(v) for v in variant_attrs.values()])
                    if variant_signature in seen_variants:
                        continue # Evita duplicati
                    seen_variants.add(variant_signature)

                    create_variant(Variant(
                        id=uuid.uuid4(),
                        product_id=product.id,
                        sku=f"{product.slug}-{variant_signature}".upper(),
                        price_adjustment=0.0,
                        inventory_quantity=random.randint(0, 50),
                        media=[Media(url=image_url, alt_text=f"{prod_name} {variant_signature}")],
                        attributes=variant_attrs
                    ))
                
                count += 1

    print("Database population from image dataset complete.")