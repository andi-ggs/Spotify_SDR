# Quick Start Guide

## Instalare Rapidă

```bash
# 1. Instalează dependențele
pip install flask

# 2. Rulează interfața web
python app.py

# 3. Deschide browser la
# http://localhost:5000
```

## Testare Rapidă

```bash
# Testează sistemul
python test_system.py

# Extrage exemple din dataset
python extract_examples.py
```

## Structura Fișierelor

```
SDR/
├── spotify_dataset.csv          # Dataset-ul principal
├── recommendation_system.py      # Logica sistemului de recomandare
├── app.py                        # Aplicația Flask (web)
├── templates/
│   └── index.html               # Interfața web
├── documentatie.md               # Documentație completă
├── prezentare_sumar.md          # Sumar pentru prezentare
├── GHID_PREZENTARE.md           # Ghid prezentare
├── extract_examples.py          # Script extragere exemple
├── test_system.py               # Script testare
└── requirements.txt             # Dependențe Python
```

## Utilizare Rapidă

### 1. Testare CLI
```python
from recommendation_system import SpotifyRecommendationSystem

# Inițializează sistem
system = SpotifyRecommendationSystem('spotify_dataset.csv')

# Creează profil utilizator
system.create_user_profile(
    user_id='user_001',
    preferred_genres=['pop', 'rock'],
    mood='energetic',
    listening_time='medium',
    energy_level=0.7,
    danceability=0.6
)

# Obține recomandări
recommendations = system.hybrid_recommend('user_001', num_recommendations=10)

# Afișează rezultate
for rec in recommendations:
    print(f"{rec['track_name']} - {rec['artists']}")
```

### 2. Utilizare Web
1. Rulează `python app.py`
2. Deschide `http://localhost:5000`
3. Completează formularul
4. Apasă "Obține Recomandări"
5. Vezi rezultatele

## Configurare Recombee (Opțional)

Pentru integrare completă cu Recombee:

1. Creează cont la https://www.recombee.com
2. Creează o bază de date
3. Obține token-ul privat
4. Modifică `recommendation_system.py`:
```python
system = SpotifyRecommendationSystem(
    'spotify_dataset.csv',
    recombee_db='your-db-name',
    recombee_private_token='your-private-token'
)
```

## Probleme Comune

### Eroare: "ModuleNotFoundError: No module named 'flask'"
**Soluție**: `pip install flask`

### Eroare: "FileNotFoundError: spotify_dataset.csv"
**Soluție**: Asigură-te că fișierul CSV este în același director

### Port 5000 deja folosit
**Soluție**: Modifică port-ul în `app.py`:
```python
app.run(debug=True, port=5001)  # sau alt port
```

## Next Steps

1. Citește `documentatie.md` pentru detalii complete
2. Consultă `GHID_PREZENTARE.md` pentru prezentare
3. Folosește `prezentare_sumar.md` pentru slide-uri
4. Testează cu `test_system.py`
5. Extrage exemple cu `extract_examples.py`

