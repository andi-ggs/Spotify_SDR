"""
Script pentru încărcarea datelor în Recombee
Rulează acest script după ce ai configurat API keys
Șterge toate items-urile existente și le reîncarcă cu toate proprietățile din CSV
"""

import csv
import os
from recombee_api_client.api_client import RecombeeClient
from recombee_api_client.api_requests import (
    AddItem, SetItemValues, Batch, DeleteItem, ListItems,
    AddItemProperty, ListItemProperties
)
from recombee_api_client.exceptions import APIException

def load_recombee_config():
    """Încarcă configurația Recombee din config.py, variabile de mediu sau input"""
    # Încearcă să încarce din config.py
    try:
        from config import RECOMBEE_DATABASE_ID, RECOMBEE_PRIVATE_TOKEN
        return RECOMBEE_DATABASE_ID, RECOMBEE_PRIVATE_TOKEN
    except ImportError:
        pass
    
    # Fallback la variabile de mediu
    database_id = os.getenv('RECOMBEE_DATABASE_ID')
    private_token = os.getenv('RECOMBEE_PRIVATE_TOKEN')
    
    if not database_id or not private_token:
        print("=" * 60)
        print("CONFIGURARE RECOMBEE")
        print("=" * 60)
        print("\nIntrodu datele tale Recombee:")
        print("(Sau creează un fișier config.py cu RECOMBEE_DATABASE_ID și RECOMBEE_PRIVATE_TOKEN)")
        
        if not database_id:
            database_id = input("\nDatabase ID (numele bazei de date): ").strip()
        
        if not private_token:
            private_token = input("Private Token: ").strip()
    
    return database_id, private_token

def setup_recombee():
    """Configurează și încarcă datele în Recombee"""
    
    # Încarcă configurația
    database_id, private_token = load_recombee_config()
    
    if not database_id or not private_token:
        print("\n❌ Eroare: Database ID și Private Token sunt obligatorii!")
        print("\nCum să obții acestea:")
        print("1. Creează cont la https://www.recombee.com/")
        print("2. Creează o bază de date")
        print("3. Copiază Database ID și Private Token din Settings")
        return
    
    # Inițializează client Recombee
    print("\n" + "=" * 60)
    print("CONECTARE LA RECOMBEE")
    print("=" * 60)
    print(f"Database ID: {database_id}")
    
    try:
        from recombee_api_client.api_client import Region
        
        # Pentru operațiuni server-side (scriere), folosim PRIVATE token
        # Public token este doar pentru citire și client-side
        try:
            from config import RECOMBEE_REGION
            region_str = RECOMBEE_REGION
        except ImportError:
            region_str = None
        
        # Folosim private token pentru scriere
        token = private_token
        
        # Convertim regiunea
        region_enum = None
        if region_str:
            region_upper = region_str.upper().replace('-', '_')
            if hasattr(Region, region_upper):
                region_enum = getattr(Region, region_upper)
            else:
                for attr in dir(Region):
                    if not attr.startswith('_') and region_upper in attr.upper():
                        region_enum = getattr(Region, attr)
                        break
        
        if region_enum:
            client = RecombeeClient(
                database_id=database_id,
                token=token,
                region=region_enum
            )
        else:
            client = RecombeeClient(
                database_id=database_id,
                token=token
            )
        print("✓ Conectat la Recombee cu succes!")
    except Exception as e:
        print(f"❌ Eroare la conectare: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Încarcă dataset-ul
    print("\n" + "=" * 60)
    print("ÎNCĂRCARE DATASET")
    print("=" * 60)
    
    csv_file = 'spotify_dataset.csv'
    if not os.path.exists(csv_file):
        print(f"❌ Fișierul {csv_file} nu există!")
        return
    
    tracks = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tracks.append(row)
    
    print(f"✓ Dataset încărcat: {len(tracks)} piese")
    
    # Definește proprietățile items-urilor
    print("\n" + "=" * 60)
    print("DEFINIRE PROPRIETĂȚI ITEMS")
    print("=" * 60)
    
    # Proprietățile care trebuie definite (tipuri Recombee)
    item_properties = {
        # String properties
        'track_id': 'string',
        'track_name': 'string',
        'artists': 'string',
        'album_name': 'string',
        'track_genre': 'string',
        
        # Integer properties
        'popularity': 'int',
        'duration_ms': 'int',
        'key': 'int',
        'mode': 'int',
        'time_signature': 'int',
        
        # Double properties
        'danceability': 'double',
        'energy': 'double',
        'loudness': 'double',
        'speechiness': 'double',
        'acousticness': 'double',
        'instrumentalness': 'double',
        'liveness': 'double',
        'valence': 'double',
        'tempo': 'double',
        
        # Boolean properties
        'explicit': 'boolean'
    }
    
    try:
        # Obține lista proprietăților existente
        existing_properties = client.send(ListItemProperties())
        existing_prop_names = set()
        
        if isinstance(existing_properties, list):
            for prop in existing_properties:
                if isinstance(prop, dict):
                    existing_prop_names.add(prop.get('name', ''))
                else:
                    existing_prop_names.add(str(prop))
        elif isinstance(existing_properties, dict):
            props = existing_properties.get('properties', [])
            for prop in props:
                if isinstance(prop, dict):
                    existing_prop_names.add(prop.get('name', ''))
        
        # Adaugă proprietățile care nu există
        added_count = 0
        for prop_name, prop_type in item_properties.items():
            if prop_name not in existing_prop_names:
                try:
                    client.send(AddItemProperty(prop_name, prop_type))
                    added_count += 1
                    print(f"✓ Proprietate adăugată: {prop_name} ({prop_type})")
                except Exception as e:
                    print(f"⚠ Eroare la adăugarea proprietății {prop_name}: {e}")
        
        if added_count == 0:
            print("✓ Toate proprietățile există deja")
        else:
            print(f"✓ Total proprietăți adăugate: {added_count}")
            
    except Exception as e:
        print(f"⚠ Eroare la verificarea/definirea proprietăților: {e}")
        print("Continuăm cu adăugarea items-urilor...")
    
    # Șterge toate items-urile existente
    print("\n" + "=" * 60)
    print("ȘTERGERE ITEMS EXISTENTE")
    print("=" * 60)
    
    try:
        # Obține lista cu toate items-urile
        items_response = client.send(ListItems(count=10000))  # Obține până la 10000 items
        
        # ListItems returnează o listă de dicționare sau o listă directă
        if isinstance(items_response, list):
            existing_items = items_response
        elif isinstance(items_response, dict):
            existing_items = items_response.get('items', [])
        else:
            existing_items = []
        
        if existing_items:
            print(f"Găsite {len(existing_items)} items existente. Se șterg...")
            
            # Șterge în batch-uri
            delete_batch_size = 100
            total_delete_batches = (len(existing_items) + delete_batch_size - 1) // delete_batch_size
            
            deleted_count = 0
            for batch_num in range(total_delete_batches):
                start_idx = batch_num * delete_batch_size
                end_idx = min(start_idx + delete_batch_size, len(existing_items))
                batch_items = existing_items[start_idx:end_idx]
                
                # Extrage ID-urile items-urilor
                item_ids = []
                for item in batch_items:
                    if isinstance(item, dict):
                        item_ids.append(item.get('id', item))
                    else:
                        item_ids.append(item)
                
                delete_requests = [DeleteItem(item_id) for item_id in item_ids]
                
                try:
                    client.send(Batch(delete_requests))
                    deleted_count += len(batch_items)
                    print(f"✓ Batch {batch_num + 1}/{total_delete_batches}: {len(batch_items)} items șterse")
                except Exception as e:
                    print(f"⚠ Eroare la ștergerea batch {batch_num + 1}: {e}")
            
            print(f"✓ Total items șterse: {deleted_count}")
        else:
            print("✓ Nu există items de șters")
    except Exception as e:
        print(f"⚠ Eroare la ștergerea items existente: {e}")
        import traceback
        traceback.print_exc()
        print("Continuăm cu adăugarea items-urilor...")
    
    # Încarcă items în Recombee (batch processing pentru eficiență)
    print("\n" + "=" * 60)
    print("ÎNCĂRCARE PIESE ÎN RECOMBEE")
    print("=" * 60)
    
    batch_size = 100  # Recombee recomandă batch-uri de 100
    total_batches = (len(tracks) + batch_size - 1) // batch_size
    
    success_count = 0
    error_count = 0
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(tracks))
        batch_tracks = tracks[start_idx:end_idx]
        
        requests = []
        
        for track in batch_tracks:
            track_id = track['track_id']
            
            # Adaugă item
            requests.append(AddItem(track_id))
            
            # Setează toate proprietățile din dataset
            # Toate câmpurile din CSV sunt incluse ca proprietăți în Recombee
            # Ordinea câmpurilor este aceeași ca în dataset
            properties = {
                # Câmpuri din dataset (în ordinea din CSV header)
                'track_id': track['track_id'],
                'artists': track['artists'],
                'album_name': track['album_name'],
                'track_name': track['track_name'],
                'popularity': int(track['popularity']),
                'duration_ms': int(track['duration_ms']),
                'explicit': track['explicit'].lower() == 'true',
                'danceability': float(track['danceability']),
                'energy': float(track['energy']),
                'key': int(track['key']),
                'loudness': float(track['loudness']),
                'mode': int(track['mode']),
                'speechiness': float(track['speechiness']),
                'acousticness': float(track['acousticness']),
                'instrumentalness': float(track['instrumentalness']),
                'liveness': float(track['liveness']),
                'valence': float(track['valence']),
                'tempo': float(track['tempo']),
                'time_signature': int(track['time_signature']),
                'track_genre': track['track_genre']
            }
            
            requests.append(SetItemValues(track_id, properties))
        
        # Trimite batch-ul
        try:
            client.send(Batch(requests))
            success_count += len(batch_tracks)
            print(f"✓ Batch {batch_num + 1}/{total_batches}: {len(batch_tracks)} piese încărcate")
        except APIException as e:
            error_count += len(batch_tracks)
            print(f"❌ Eroare la batch {batch_num + 1}: {e}")
        except Exception as e:
            error_count += len(batch_tracks)
            print(f"❌ Eroare neașteptată la batch {batch_num + 1}: {e}")
    
    print("\n" + "=" * 60)
    print("REZUMAT")
    print("=" * 60)
    print(f"✓ Piese încărcate cu succes: {success_count}")
    if error_count > 0:
        print(f"❌ Erori: {error_count}")
    print(f"\nTotal: {len(tracks)} piese")
    
    print("\n" + "=" * 60)
    print("SETUP COMPLET!")
    print("=" * 60)
    print("\nAcum poți folosi Recombee pentru recomandări!")
    print("\nPentru a testa, rulează:")
    print("  python test_recombee.py")

if __name__ == "__main__":
    setup_recombee()

