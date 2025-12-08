# Ghid Setup Recombee - Pas cu Pas

## Pasul 1: Creare Cont Recombee

1. **Accesează**: https://www.recombee.com/
2. **Click pe "Sign Up"** sau "Get Started"
3. **Completează formularul**:
   - Email
   - Parolă
   - Nume (opțional)
4. **Confirmă email-ul** (dacă este necesar)

## Pasul 2: Creare Bază de Date

1. **După login**, vei fi redirecționat la **Admin UI** (Dashboard)
2. **Click pe "Create Database"** sau "New Database"
3. **Numează baza de date**: ex. `spotify-recommendations`
4. **Selectează regiunea** (cea mai apropiată de tine)
5. **Click "Create"**

## Pasul 3: Obținere API Keys

### 3.1 Private Token (Server-Side)

1. **În Admin UI**, mergi la **"Settings"** sau **"API"**
2. **Găsește secțiunea "Tokens"** sau **"API Keys"**
3. **Private Token** este folosit pentru:
   - Adăugare items (piese)
   - Adăugare users (utilizatori)
   - Setare valori pentru items/users
   - Obținere recomandări server-side
4. **Copiază Private Token** - **PĂSTREAZĂ-L SECRET!**

### 3.2 Public Token (Client-Side - Opțional)

1. **În aceeași secțiune "Tokens"**
2. **Public Token** este folosit pentru:
   - Recomandări client-side
   - Tracking interacțiuni (views, purchases)
3. **Copiază Public Token** (dacă ai nevoie)

### 3.3 Database ID

1. **Database ID** este numele bazei de date create
2. **Exemplu**: Dacă ai creat `spotify-recommendations`, acesta este Database ID-ul

## Pasul 4: Configurare în Proiect

### 4.1 Creează fișier de configurare

Creează un fișier `.env` (sau `config.py`) cu:

```python
# config.py
RECOMBEE_DATABASE_ID = "spotify-recommendations"  # Numele bazei de date
RECOMBEE_PRIVATE_TOKEN = "your-private-token-here"  # Private token
RECOMBEE_PUBLIC_TOKEN = "your-public-token-here"  # Public token (opțional)
```

**IMPORTANT**: Nu comite acest fișier în Git! Adaugă în `.gitignore`:
```
.env
config.py
```

### 4.2 Instalează biblioteca Recombee

```bash
pip install recombee-api-client
```

## Pasul 5: Încărcare Date în Recombee

Folosește scriptul `setup_recombee.py` pentru a încărca:
- Toate piesele (items) din dataset
- Caracteristicile acustice
- Genurile

## Pasul 6: Testare Conexiune

Rulează scriptul de test pentru a verifica că totul funcționează:

```bash
python test_recombee.py
```

## Structura în Recombee

### Items (Piese)
- **item_id**: track_id din CSV
- **Properties**:
  - `artists` (string)
  - `track_name` (string)
  - `genre` (string)
  - `energy` (double)
  - `danceability` (double)
  - `tempo` (double)
  - `valence` (double)
  - `popularity` (int)
  - etc.

### Users (Utilizatori)
- **user_id**: ID-ul utilizatorului
- **Properties**:
  - `preferred_genres` (set of strings)
  - `mood` (string)
  - `listening_time` (string)
  - `energy_level` (double)
  - `danceability` (double)

### Interactions (Interacțiuni)
- **view**: Utilizatorul a văzut/ascultat piesa
- **bookmark**: Utilizatorul a salvat piesa
- **rating**: Utilizatorul a dat rating (1-5)

## Exemple de Utilizare

### Adăugare Item
```python
from recombee_api_client.api_requests import AddItem, SetItemValues

client.send(AddItem("track_123"))
client.send(SetItemValues("track_123", {
    "track_name": "Song Name",
    "artists": "Artist Name",
    "genre": "pop",
    "energy": 0.8,
    "danceability": 0.7
}))
```

### Adăugare User
```python
from recombee_api_client.api_requests import AddUser, SetUserValues

client.send(AddUser("user_001"))
client.send(SetUserValues("user_001", {
    "preferred_genres": ["pop", "rock"],
    "mood": "energetic"
}))
```

### Obținere Recomandări
```python
from recombee_api_client.api_requests import RecommendItemsToUser

recommendations = client.send(RecommendItemsToUser("user_001", 10))
```

## Troubleshooting

### Eroare: "Invalid database ID"
- Verifică că Database ID-ul este corect
- Asigură-te că baza de date există în contul tău

### Eroare: "Invalid token"
- Verifică că ai copiat corect token-ul
- Asigură-te că folosești Private Token pentru operațiuni server-side

### Eroare: "Rate limit exceeded"
- Recombee are limite de rate pentru planul gratuit
- Așteaptă câteva secunde și încearcă din nou

### Datele nu se încarcă
- Verifică conexiunea la internet
- Verifică că token-ul are permisiuni de scriere
- Verifică formatul datelor (tipuri corecte)

## Resurse Utile

- **Documentație oficială**: https://docs.recombee.com/
- **API Reference**: https://docs.recombee.com/api-reference
- **Python SDK**: https://github.com/Recombee/python-api-client
- **Examples**: https://docs.recombee.com/getting_started

## Planuri și Limite

### Plan Gratuit (Free Tier)
- **10,000 items** (piese)
- **10,000 users** (utilizatori)
- **100,000 requests/lună**
- **Perfect pentru demo și testare**

### Planuri Plătite
- Mai multe items/users
- Mai multe requests
- Suport prioritar
- Funcții avansate

Pentru proiectul tău (1000 piese), planul gratuit este suficient!

