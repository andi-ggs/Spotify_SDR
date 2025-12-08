# Sumar Prezentare - Sistem de Recomandare Muzică

## Slide 1: Titlu
**Sistem de Recomandare Muzică - Spotify Dataset**
- Content-Based + Knowledge-Based Filtering
- Integrare Recombee
- Rezolvare Long Tail Problem

---

## Slide 2: Funcționalitate Sistem de Recomandare (2 puncte)

### Tip de Sistem: **HIBRID**

**Componente:**
1. **Content-Based Filtering** (60%)
   - Similaritate acustică
   - Caracteristici: energy, danceability, valence, tempo, acousticness, instrumentalness
   - Algoritm: Cosine Similarity

2. **Knowledge-Based Filtering** (40%)
   - Personalizare bazată pe profil utilizator
   - Filtrare: genuri, mood, timp ascultare, preferințe acustice
   - Scor de potrivire ponderat

**Pseudocod Principal:**
```
FUNCTION hybrid_recommend(user_id, seed_track_id):
    content_recs = content_based_recommend(seed_track_id)
    knowledge_recs = knowledge_based_recommend(user_id)
    combined = merge_and_rank(content_recs, knowledge_recs)
    RETURN diversified_recommendations
END FUNCTION
```

**Integrare Recombee:**
- Învățare automată a gusturilor utilizatorilor
- Optimizare în timp real
- Scalabilitate pentru baze de date mari

---

## Slide 3: Dataset (2 puncte)

### Statistici Dataset
- **Total piese**: 997
- **Total genuri**: 114
- **Popularitate medie**: 32.62/100
- **Piese populare (>70)**: 44 (4.4%)
- **Piese de nișă (<20)**: 307 (30.8%)

### Exemple Particulare

#### Exemplu 1: Piesă Foarte Scurtă
- **"Kill a Politician"** - Insult
- **Durată**: 31.2 secunde (0.52 minute)
- **Gen**: grindcore
- **Energy**: 0.995 (foarte ridicată)
- **Observație**: Ideală pentru utilizatori cu preferință "short"

#### Exemplu 2: Piesă Foarte Lungă
- **"Kali Kali Zulfon Ke Phande Na"** - Nusrat Fateh Ali Khan
- **Durată**: 859.3 secunde (14.32 minute)
- **Gen**: indian
- **Energy**: 0.694
- **Observație**: Ideală pentru utilizatori cu preferință "long"

#### Exemplu 3: Piesă Foarte Energetică
- **"Affront Final"** - Akitsa
- **Energy**: 1.000 (maxim)
- **Tempo**: 171.81 BPM
- **Gen**: black-metal
- **Observație**: Potrivită pentru mood "energetic"

#### Exemplu 4: Piesă Foarte Puțin Energetică
- **"Box Fan Long Loop For Sleep"** - Fan Sounds
- **Energy**: 0.000 (minim)
- **Tempo**: 0.00 BPM
- **Gen**: sleep
- **Observație**: Potrivită pentru mood "calm" sau relaxare

#### Exemplu 5: Piesă Foarte Populară
- **"Only Love Can Hurt Like This"** - Paloma Faith
- **Popularity**: 87/100
- **Gen**: dance
- **Energy**: 0.885
- **Observație**: Exemplu de piesă mainstream

#### Exemplu 6: Piesă de Nișă
- **"Save the Trees, Pt. 1"** - Zhoobin Askarieh; Ali Sasha
- **Popularity**: 0/100
- **Gen**: iranian
- **Energy**: 0.803
- **Observație**: Exemplu perfect pentru problema long tail

---

## Slide 4: Modelul Utilizatorului (2 puncte)

### Datele Colectate

1. **Genuri Preferate**
   - Colectare: Selectare multiplă din listă
   - Folosire: Filtrare inițială în Knowledge-Based
   - Exemplu: pop, rock, electronic

2. **Dispoziție (Mood)**
   - Colectare: Dropdown (happy, sad, energetic, calm)
   - Folosire: Filtrare după caracteristici emoționale
   - Mapping:
     - happy → valence > 0.6, energy > 0.5
     - sad → valence < 0.4, energy < 0.6
     - energetic → energy > 0.7, tempo > 120
     - calm → energy < 0.4, acousticness > 0.5

3. **Timp de Ascultare Preferat**
   - Colectare: Dropdown (short, medium, long)
   - Folosire: Filtrare după durată
   - Mapping:
     - short → ≤ 3 minute
     - medium → 3-5 minute
     - long → > 5 minute

4. **Nivel Energie Preferat**
   - Colectare: Slider 0.0 - 1.0
   - Folosire: Calcul scor potrivire (pondere 30%)
   - Formula: `score += 0.3 * (1 - abs(track.energy - user.energy))`

5. **Dansabilitate Preferată**
   - Colectare: Slider 0.0 - 1.0
   - Folosire: Calcul scor potrivire (pondere 20%)
   - Formula: `score += 0.2 * (1 - abs(track.danceability - user.danceability))`

### Flux de Colectare
```
Interfață Web → API /api/recommend → Stocare Profil → Utilizare în Algoritm
```

### Utilizare Date
- **Knowledge-Based**: Toate datele pentru filtrare și scoring
- **Content-Based**: Nu folosește direct, doar caracteristicile pieselor
- **Hibrid**: Combină rezultatele cu ponderi

---

## Slide 5: Long Tail / Alte Probleme (2 puncte)

### Problema Long Tail

**Definiție**: Majoritatea utilizatorilor ascultă o mică parte din catalog (piese populare), în timp ce o mare parte (piese de nișă) rămâne neexplorată.

**Statistici din Dataset:**
- Piese populare (>70): 44 (4.4%)
- Piese de nișă (<20): 307 (30.8%)
- **Problema**: Sistemul ar putea recomanda doar piese populare

### Rezolvare: Diversificare

**Algoritm de Diversificare:**
```
FUNCTION solve_long_tail_problem(recommendations):
    genre_groups = GROUP recommendations BY genre
    
    diversified = []
    FOR EACH round:
        FOR EACH genre:
            IF exists track not yet added:
                ADD track to diversified
    
    RETURN diversified
END FUNCTION
```

**Strategii:**
1. **Diversificare pe Genuri**: Asigură reprezentare echilibrată
2. **Balansare Popularitate-Diversitate**: 70% potrivire, 30% diversitate
3. **Filtrare Adaptivă**: Cold start → Knowledge-Based, Warm start → Hibrid

**Rezultate:**
- Expunere la muzică variată
- Descoperire de piese noi
- Prevenirea concentrării pe un singur gen

### Alte Probleme Rezolvate

1. **Cold Start Problem**
   - Soluție: Knowledge-Based cu preferințe declarate
   - Fallback: Piese populare din genurile preferate

2. **Sparsity Problem**
   - Soluție: Caracteristici acustice detaliate
   - Extindere pe baza similarității, nu doar gen

3. **Scalability**
   - Soluție: Indexare pe genuri
   - Cache pentru recomandări frecvente
   - Integrare Recombee

---

## Slide 6: Demo (2 puncte)

### Interfață Web Live

**URL**: `http://localhost:5000`

**Funcționalități:**
1. Formular interactiv pentru profil utilizator
2. Selectare genuri, mood, timp ascultare
3. Slider-uri pentru energie și dansabilitate
4. Afișare recomandări în timp real
5. Badge-uri pentru sursa recomandării (Content-Based / Knowledge-Based)

### Rulare Demo

```bash
# Instalare
pip install -r requirements.txt

# Rulare
python app.py

# Accesare
http://localhost:5000
```

### API Endpoints

1. **POST /api/recommend**: Obține recomandări personalizate
2. **GET /api/tracks**: Listă piese disponibile
3. **GET /api/dataset-examples**: Exemple specifice din dataset
4. **GET /api/content-based/<track_id>**: Recomandări Content-Based

### Screenshot-uri Recomandate

1. Interfața web cu formularul completat
2. Recomandările afișate cu badge-uri
3. Diagramă arhitectură sistem
4. Recombee Dashboard (dacă configurat)

### Rezultate Demo

- Sistem funcțional și responsive
- Recomandări personalizate în timp real
- Diversificare pentru long tail
- Interfață modernă și intuitivă

---

## Slide 7: Concluzii

### Realizări
✅ Sistem hibrid funcțional (Content-Based + Knowledge-Based)
✅ Integrare Recombee pentru scalabilitate
✅ Rezolvare problema long tail prin diversificare
✅ Interfață web modernă pentru demo
✅ Documentație completă

### Tehnologii
- Python 3
- Flask (Web Framework)
- Recombee API (Recomandări)
- HTML/CSS/JavaScript (Frontend)

### Rezultate
- 997 piese în dataset
- 114 genuri diferite
- Recomandări personalizate în < 1 secundă
- Diversificare eficientă pentru long tail

---

## Slide 8: Întrebări?

**Contact:**
- Documentație completă: `documentatie.md`
- Cod sursă: `recommendation_system.py`, `app.py`
- Teste: `test_system.py`
- Exemple: `extract_examples.py`

