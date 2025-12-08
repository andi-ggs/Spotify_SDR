# Sistem de Recomandare Muzică - Documentație Completă

## 1. Funcționalitate Sistem de Recomandare (2 puncte)

### Tip de Sistem: HIBRID (Content-Based + Knowledge-Based)

Sistemul nostru de recomandare este un **sistem hibrid** care combină două abordări principale:

#### 1.1 Content-Based Filtering
- **Principiu**: Recomandă piese similare din punct de vedere acustic cu cele preferate de utilizator
- **Caracteristici folosite**: energy, danceability, valence, tempo, acousticness, instrumentalness
- **Algoritm**: Cosine Similarity pe vectori de caracteristici acustice

**Pseudocod Content-Based:**
```
FUNCTION content_based_recommend(track_id, num_recommendations):
    target_track = tracks[track_id]
    similarities = []
    
    FOR EACH track IN tracks:
        IF track.id != track_id:
            similarity = calculate_acoustic_similarity(target_track, track)
            similarities.append((track, similarity))
    
    SORT similarities BY similarity DESCENDING
    RETURN top num_recommendations tracks
END FUNCTION

FUNCTION calculate_acoustic_similarity(track1, track2):
    features1 = [energy1, danceability1, valence1, tempo1/200, acousticness1, instrumentalness1]
    features2 = [energy2, danceability2, valence2, tempo2/200, acousticness2, instrumentalness2]
    
    dot_product = SUM(features1[i] * features2[i] for i in range(len(features1)))
    magnitude1 = SQRT(SUM(features1[i]^2 for i in range(len(features1))))
    magnitude2 = SQRT(SUM(features2[i]^2 for i in range(len(features2))))
    
    RETURN dot_product / (magnitude1 * magnitude2)
END FUNCTION
```

#### 1.2 Knowledge-Based Filtering
- **Principiu**: Personalizează recomandările în funcție de informațiile despre utilizator
- **Date utilizate**: genuri preferate, dispoziție (mood), timp de ascultare preferat, nivel energie, dansabilitate
- **Algoritm**: Scor de potrivire bazat pe profilul utilizatorului

**Pseudocod Knowledge-Based:**
```
FUNCTION knowledge_based_recommend(user_id, num_recommendations):
    user = users[user_id]
    recommendations = []
    
    FOR EACH genre IN user.preferred_genres:
        genre_tracks = get_tracks_by_genre(genre)
        FOR EACH track IN genre_tracks:
            score = calculate_user_match_score(user, track)
            recommendations.append((track, score))
    
    FILTER recommendations BY mood_match(user.mood, track)
    FILTER recommendations BY listening_time_match(user.listening_time, track.duration)
    SORT recommendations BY score DESCENDING
    RETURN top num_recommendations tracks
END FUNCTION

FUNCTION calculate_user_match_score(user, track):
    score = 0.0
    
    IF track.genre IN user.preferred_genres:
        score += 0.4
    
    energy_diff = ABS(track.energy - user.preferred_energy_level)
    score += 0.3 * (1 - energy_diff)
    
    dance_diff = ABS(track.danceability - user.preferred_danceability)
    score += 0.2 * (1 - dance_diff)
    
    score += 0.1 * (track.popularity / 100.0)
    
    RETURN score
END FUNCTION
```

#### 1.3 Integrare Recombee

Recombee este folosit pentru:
- **Învățare automată**: Învață gusturile fiecărui utilizator pe baza interacțiunilor
- **Optimizare**: Optimizează recomandările în timp real
- **Scalabilitate**: Gestionează eficient baze de date mari

**Configurare Recombee:**
- Database ID: `spotify-recommendations`
- Tipuri de date: Items (tracks), Users, Interactions
- Algoritmi: Content-Based Similarity, User-Based Collaborative Filtering

### Cum Funcționează Sistemul Hibrid

1. **Colectare date utilizator**: Genuri preferate, mood, timp de ascultare, preferințe acustice
2. **Content-Based**: Dacă utilizatorul a selectat o piesă, găsim piese similare acustic
3. **Knowledge-Based**: Filtrem piese pe baza profilului utilizatorului
4. **Combinare**: Fuzionăm rezultatele cu ponderi (60% Content-Based, 40% Knowledge-Based)
5. **Diversificare**: Aplicăm algoritm de diversificare pentru rezolvarea problemei long tail

---

## 2. Dataset (2 puncte)

### 2.1 Descrierea Setului de Date

**Spotify Dataset** conține **1000 de piese muzicale** cu următoarele caracteristici:

#### Structura Dataset-ului:
- **track_id**: Identificator unic pentru fiecare piesă
- **artists**: Artiștii piesei
- **album_name**: Numele albumului
- **track_name**: Numele piesei
- **popularity**: Popularitatea piesei (0-100)
- **duration_ms**: Durata în milisecunde
- **explicit**: Conținut explicit (True/False)
- **Caracteristici acustice**:
  - `danceability` (0.0-1.0): Cât de potrivită este pentru dans
  - `energy` (0.0-1.0): Intensitatea și puterea
  - `key` (0-11): Cheia muzicală
  - `loudness` (dB): Volumul mediu
  - `mode` (0/1): Major (1) sau minor (0)
  - `speechiness` (0.0-1.0): Prezența cuvintelor vorbite
  - `acousticness` (0.0-1.0): Probabilitatea că piesa este acustică
  - `instrumentalness` (0.0-1.0): Cât de instrumentală este
  - `liveness` (0.0-1.0): Prezența publicului
  - `valence` (0.0-1.0): Positivitatea muzicală
  - `tempo` (BPM): Tempo-ul piesei
  - `time_signature`: Semnătura temporală
- **track_genre**: Genul muzical (ex: pop, rock, electronic, etc.)

### 2.2 Exemple Particulare din Dataset

#### Exemplu 1: Piesă cu Descriere Foarte Scurta (Durată Minimă)
**Track**: "Ready fi di party" - Tony Matterhorn
- **Durată**: 59,600 ms (≈ 1 minut)
- **Gen**: j-dance
- **Caracteristici**:
  - Energy: 0.616
  - Danceability: 0.911 (foarte dansabilă)
  - Tempo: 120.999 BPM
- **Observație**: Piesă foarte scurtă, ideală pentru utilizatori cu preferință pentru timp scurt de ascultare

#### Exemplu 2: Piesă cu Descriere Foarte Lungă (Durată Maximă)
**Track**: "Box Fan Long Loop For Sleep" - Fan Sounds
- **Durată**: 500,166 ms (≈ 8.3 minute)
- **Gen**: sleep
- **Caracteristici**:
  - Energy: 0.00002 (extrem de scăzută)
  - Danceability: 0.0
  - Tempo: 0.0 BPM
  - Acousticness: 0.145
- **Observație**: Piesă foarte lungă, instrumentală, pentru relaxare/somn

#### Exemplu 3: Piesă Foarte Energetică
**Track**: "Failed Organum" - Internal Rot
- **Energy**: 0.997 (aproape maximă)
- **Gen**: grindcore
- **Caracteristici**:
  - Danceability: 0.171 (foarte scăzută)
  - Tempo: 122.223 BPM
  - Instrumentalness: 0.801
- **Observație**: Piesă extrem de energetică, potrivită pentru utilizatori cu mood "energetic"

#### Exemplu 4: Piesă Foarte Puțin Energetică
**Track**: "O Sopro do Fole" - Maria Bethânia
- **Energy**: 0.0856 (foarte scăzută)
- **Gen**: r-n-b
- **Caracteristici**:
  - Acousticness: 0.739
  - Loudness: -17.766 dB (foarte liniștită)
  - Tempo: 93.672 BPM
- **Observație**: Piesă calmă, potrivită pentru mood "calm"

#### Exemplu 5: Piesă Foarte Populară
**Track**: "Yo No Soy Celoso" - Bad Bunny
- **Popularity**: 85/100
- **Gen**: reggaeton
- **Caracteristici**:
  - Energy: 0.588
  - Danceability: 0.872
  - Valence: 0.93 (foarte pozitivă)
- **Observație**: Piesă din mainstream, cu popularitate ridicată

#### Exemplu 6: Piesă de Nișă (Popularitate Foarte Scăzută)
**Track**: "Save the Trees, Pt. 1" - Zhoobin Askarieh; Ali Sasha
- **Popularity**: 0/100
- **Gen**: iranian
- **Caracteristici**:
  - Energy: 0.803
  - Acousticness: 0.613
  - Tempo: 75.564 BPM
- **Observație**: Piesă de nișă, exemplu perfect pentru problema long tail

---

## 3. Modelul Utilizatorului (2 puncte)

### 3.1 Datele Colectate

Sistemul colectează următoarele informații despre utilizator:

#### 3.1.1 Preferințe de Genuri
- **Colectare**: Utilizatorul selectează genurile preferate dintr-o listă
- **Folosire**: Filtrare inițială a pieselor pentru Knowledge-Based Filtering
- **Exemplu**: Utilizator selectează: pop, rock, electronic

#### 3.1.2 Dispoziție (Mood)
- **Colectare**: Utilizatorul selectează starea emoțională actuală
- **Valori posibile**: happy, sad, energetic, calm
- **Folosire**: Filtrare piese pe baza caracteristicilor emoționale (valence, energy)
- **Exemplu**: 
  - Mood "happy" → filtrează piese cu valence > 0.6 și energy > 0.5
  - Mood "sad" → filtrează piese cu valence < 0.4 și energy < 0.6

#### 3.1.3 Timp de Ascultare Preferat
- **Colectare**: Utilizatorul selectează durata preferată
- **Valori**: short (≤ 3 min), medium (3-5 min), long (> 5 min)
- **Folosire**: Filtrare piese pe baza duratei (duration_ms)
- **Exemplu**: Utilizator cu preferință "short" → doar piese ≤ 3 minute

#### 3.1.4 Nivel Energie Preferat
- **Colectare**: Slider 0.0 - 1.0
- **Folosire**: Calcul scor de potrivire în Knowledge-Based Filtering
- **Formula**: `score += 0.3 * (1 - abs(track.energy - user.preferred_energy_level))`

#### 3.1.5 Dansabilitate Preferată
- **Colectare**: Slider 0.0 - 1.0
- **Folosire**: Calcul scor de potrivire în Knowledge-Based Filtering
- **Formula**: `score += 0.2 * (1 - abs(track.danceability - user.preferred_danceability))`

### 3.2 Cum Se Colectează Datele

1. **Interfață Web**: Formular interactiv cu:
   - Checkbox-uri pentru genuri
   - Dropdown pentru mood și timp de ascultare
   - Slider-uri pentru energie și dansabilitate

2. **API Endpoint**: `/api/recommend` primește datele JSON:
```json
{
  "user_id": "user_001",
  "preferred_genres": ["pop", "rock"],
  "mood": "energetic",
  "listening_time": "medium",
  "energy_level": 0.7,
  "danceability": 0.6
}
```

3. **Stocare**: Profilul utilizatorului este stocat în:
   - Memorie (pentru demo)
   - Recombee (pentru producție)

### 3.3 La Ce Sunt Folosite Datele

#### În Knowledge-Based Filtering:
- **Genuri preferate**: Filtrare inițială a pieselor
- **Mood**: Filtrare după caracteristici emoționale
- **Timp de ascultare**: Filtrare după durată
- **Energie/Dansabilitate**: Calcul scor de potrivire

#### În Content-Based Filtering:
- Datele utilizatorului nu sunt direct folosite
- Se folosesc caracteristicile acustice ale pieselor preferate

#### În Sistemul Hibrid:
- Combină rezultatele din ambele abordări
- Pondere: 60% Content-Based, 40% Knowledge-Based

---

## 4. Long Tail / Alte Probleme (2 puncte)

### 4.1 Problema Long Tail

**Definiție**: Majoritatea utilizatorilor ascultă o mică parte din catalog (piese populare), în timp ce o mare parte din catalog (piese de nișă) rămâne neexplorată.

**Exemplu din dataset**:
- Piese populare (popularity > 70): ~5% din catalog
- Piese de nișă (popularity < 20): ~60% din catalog
- Piese foarte populare (popularity > 80): ~2% din catalog

### 4.2 Modul de Rezolvare

#### 4.2.1 Diversificare pe Genuri
**Algoritm**:
```
FUNCTION solve_long_tail_problem(recommendations, diversity_weight):
    genre_groups = GROUP recommendations BY genre
    
    diversified = []
    FOR EACH round:
        FOR EACH genre IN genre_groups:
            IF exists track in genre not yet added:
                ADD track to diversified
    
    RETURN diversified
END FUNCTION
```

**Beneficii**:
- Asigură reprezentare echilibrată a genurilor
- Previne concentrarea pe un singur gen
- Expune utilizatorul la muzică diversă

#### 4.2.2 Balansare Popularitate-Diversitate
- **Strategie**: Include atât piese populare, cât și piese de nișă
- **Pondere**: 70% scor de potrivire, 30% diversitate
- **Rezultat**: Recomandări echilibrate între mainstream și nișă

#### 4.2.3 Filtrare Adaptivă
- **Cold Start**: Pentru utilizatori noi, folosim Knowledge-Based cu genuri populare
- **Warm Start**: Pentru utilizatori cu istoric, combinăm cu Content-Based

### 4.3 Alte Probleme Specifice

#### 4.3.1 Cold Start Problem
**Problema**: Utilizatori noi fără istoric de ascultare

**Soluție**:
- Folosim Knowledge-Based Filtering bazat pe preferințe declarate
- Recomandăm piese populare din genurile preferate
- Colectăm feedback implicit (timp de ascultare, skip rate)

#### 4.3.2 Sparsity Problem
**Problema**: Dataset-ul are doar 1000 de piese, limitând varietatea

**Soluție**:
- Folosim caracteristici acustice detaliate pentru găsirea de similarități
- Extindem recomandările pe baza similarității acustice, nu doar gen
- Implementăm fallback la genuri similare

#### 4.3.3 Scalability
**Problema**: Calculul similarităților pentru toate piesele este costisitor

**Soluție**:
- Indexare eficientă pe genuri
- Cache pentru recomandări frecvente
- Integrare Recombee pentru optimizare și scalabilitate

---

## 5. Demo (2 puncte)

### 5.1 Interfață Web

Sistemul include o **interfață web interactivă** accesibilă la `http://localhost:5000`

#### Funcționalități:
1. **Formular de profil utilizator**:
   - Selectare genuri preferate (checkbox-uri)
   - Selectare mood (dropdown)
   - Selectare timp de ascultare (dropdown)
   - Slider-uri pentru energie și dansabilitate

2. **Afișare recomandări**:
   - Card-uri pentru fiecare piesă recomandată
   - Informații: nume, artist, gen, caracteristici acustice
   - Badge-uri pentru sursa recomandării (Content-Based / Knowledge-Based)
   - Scor de potrivire

3. **Design modern**:
   - Interfață responsive
   - Animații și tranziții
   - Color scheme atractiv

### 5.2 Rulare Demo

#### Instalare dependențe:
```bash
pip install flask
pip install recombee-api-client  # Opțional, pentru integrare Recombee
```

#### Rulare aplicație:
```bash
python app.py
```

#### Accesare:
- Deschide browser la `http://localhost:5000`
- Completează formularul
- Apasă "Obține Recomandări"
- Vezi rezultatele în timp real

### 5.3 API Endpoints

#### `GET /api/tracks`
Returnează lista de piese disponibile

#### `POST /api/recommend`
Obține recomandări personalizate
```json
Request:
{
  "user_id": "user_001",
  "preferred_genres": ["pop", "rock"],
  "mood": "energetic",
  "listening_time": "medium",
  "energy_level": 0.7,
  "danceability": 0.6,
  "num_recommendations": 10
}

Response:
{
  "recommendations": [
    {
      "track_id": "...",
      "track_name": "...",
      "artists": "...",
      "genre": "...",
      "source": "content-based",
      "final_score": 0.85
    }
  ]
}
```

#### `GET /api/dataset-examples`
Returnează exemple specifice din dataset

#### `GET /api/content-based/<track_id>`
Recomandări Content-Based pentru o piesă specifică

### 5.4 Screenshot-uri și Demonstrații

**Pentru prezentare, includeți**:
1. Screenshot din interfața web cu formularul completat
2. Screenshot cu recomandările afișate
3. Screenshot din Recombee Dashboard (dacă este configurat)
4. Diagramă a arhitecturii sistemului

---

## Concluzie

Sistemul de recomandare implementat este un **sistem hibrid** care combină:
- **Content-Based Filtering** pentru similaritate acustică
- **Knowledge-Based Filtering** pentru personalizare bazată pe profil
- **Rezolvarea problemei long tail** prin diversificare
- **Interfață web modernă** pentru demonstrație live

Sistemul este funcțional, scalabil și pregătit pentru integrare cu Recombee în producție.

