# Sistem de Recomandare Muzică - Spotify Dataset

Sistem hibrid de recomandare muzicală care combină **Content-Based Filtering** și **Knowledge-Based Filtering**, cu integrare **Recombee**.

## 🎯 Funcționalități Principale

- **Content-Based Filtering**: "Show me more of the same what I've liked"
  - Folosește Cosine Similarity pentru a găsi piese similare acustic
  - Analizează 13 caracteristici acustice (energy, danceability, tempo, etc.)
  
- **Knowledge-Based Filtering**: "Tell me what fits based on my needs"
  - Personalizează recomandările pe baza profilului utilizatorului
  - Folosește genuri preferate, mood, timp de ascultare, preferințe acustice
  
- **Sistem Hibrid**: Combină ambele abordări pentru recomandări optimale
- **Rezolvare Long Tail**: Diversificare pentru expunere la muzică variată
- **Autentificare Utilizatori**: Login/Register cu selecție genuri muzicale
- **Tracking Interacțiuni**: Colectează date despre preferințele utilizatorilor

## 📋 Cerințe

- Python 3.7+
- Flask
- recombee-api-client (pentru integrare Recombee)

## 🚀 Instalare

```bash
# Clonează repository-ul
git clone https://github.com/andi-ggs/Spotify_SDR.git
cd Spotify_SDR

# Instalează dependențele
pip install -r requirements.txt
```

## ⚙️ Configurare

### 1. Configurare Recombee (Opțional)

Creează un fișier `config.py` (nu este inclus în Git):

```python
RECOMBEE_DATABASE_ID = "your-database-id"
RECOMBEE_PUBLIC_TOKEN = "your-public-token"
RECOMBEE_PRIVATE_TOKEN = "your-private-token"
RECOMBEE_REGION = "eu-west"
```

### 2. Setup Recombee

```bash
# Încarcă datele în Recombee
python setup_recombee.py
```

## 🎮 Rulare

```bash
python app.py
```

Apoi deschide browser-ul:
- **Login/Register**: `http://localhost:5001/login` sau `/register`
- **Profil Utilizator**: `http://localhost:5001/profile`
- **Demo Original**: `http://localhost:5001`

## 📁 Structură Proiect

```
Spotify_SDR/
├── spotify_dataset.csv          # Dataset cu 1000 de piese
├── recommendation_system.py    # Logica sistemului de recomandare
├── app.py                       # Aplicația Flask
├── user_storage.py              # Sistem de stocare utilizatori
├── setup_recombee.py            # Script setup Recombee
├── templates/
│   ├── index.html              # Interfața demo originală
│   ├── login.html              # Pagină login
│   ├── register.html           # Pagină înregistrare
│   └── user_profile.html       # Pagină profil utilizator
├── documentatie.md             # Documentație completă
├── prezentare_sumar.md         # Sumar pentru prezentare
├── GHID_PREZENTARE.md          # Ghid prezentare
├── SETUP_RECOMBEE.md           # Ghid setup Recombee
└── requirements.txt            # Dependențe Python
```

## 📚 Documentație

- **documentatie.md** - Documentație completă cu toate cerințele
- **prezentare_sumar.md** - Sumar pentru slide-uri PPT/PDF
- **GHID_PREZENTARE.md** - Ghid de prezentare
- **SETUP_RECOMBEE.md** - Ghid setup Recombee

## 🔐 Securitate

Fișierele sensibile (`config.py`, `auth_data.json`, `users_data.json`) sunt excluse din Git prin `.gitignore`.

## 📊 Dataset

Dataset-ul conține **1000 de piese** cu următoarele caracteristici:
- Informații de bază: track_id, artists, album_name, track_name
- Metadate: popularity, duration_ms, explicit
- Caracteristici acustice: energy, danceability, valence, tempo, etc.
- Genuri: 114 genuri diferite

## 🎓 Pentru Prezentare

Vezi `prezentare_sumar.md` pentru structura prezentării și `GHID_PREZENTARE.md` pentru tips.

