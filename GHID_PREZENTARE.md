# Ghid de Prezentare - Sistem de Recomandare Muzică

## Pregătire Prezentare

### 1. Verificare Sistem
```bash
# Testează sistemul
python test_system.py

# Extrage exemple
python extract_examples.py

# Rulează interfața web
python app.py
```

### 2. Screenshot-uri Necesare

1. **Interfața Web**:
   - Deschide `http://localhost:5000`
   - Completează formularul cu date de test
   - Fă screenshot cu formularul completat
   - Fă screenshot cu recomandările afișate

2. **Cod Pseudocod**:
   - Deschide `recommendation_system.py`
   - Fă screenshot cu funcțiile principale
   - Highlight pseudocod-ul din documentație

3. **Exemple Dataset**:
   - Rulează `extract_examples.py`
   - Fă screenshot cu output-ul
   - Include în slide-ul despre dataset

### 3. Structura Prezentării

#### Slide 1: Titlu și Introducere
- Titlu proiect
- Nume echipă
- Data prezentării

#### Slide 2: Funcționalitate SR (2 puncte)
- Tip sistem: HIBRID
- Diagramă arhitectură
- Pseudocod principal
- Screenshot Recombee (dacă disponibil)

#### Slide 3: Dataset (2 puncte)
- Statistici generale
- 2+ exemple particulare (scurt/lung, energetic/calm, popular/nișă)
- Tabel cu caracteristici

#### Slide 4: Model Utilizator (2 puncte)
- Datele colectate (listă)
- Cum se colectează (flux)
- La ce se folosesc (diagramă)

#### Slide 5: Long Tail (2 puncte)
- Problema (statistici)
- Soluția (algoritm)
- Rezultate (comparativ)

#### Slide 6: Demo (2 puncte)
- Screenshot interfață web
- Demonstrație live (dacă posibil)
- Rezultate obținute

#### Slide 7: Concluzii
- Realizări
- Tehnologii
- Rezultate

#### Slide 8: Întrebări
- Q&A

### 4. Puncte Cheie pentru Fiecare Slide

#### Funcționalitate SR
- **Subliniază**: Sistem HIBRID (nu doar unul sau altul)
- **Menționează**: Ponderile (60% Content-Based, 40% Knowledge-Based)
- **Arată**: Pseudocod clar și concis
- **Dacă ai Recombee**: Screenshot din dashboard

#### Dataset
- **Subliniază**: Varietatea (114 genuri, 997 piese)
- **Arată**: Contrastul între exemple (scurt vs lung, energetic vs calm)
- **Menționează**: Problema long tail (307 piese cu popularity < 20)

#### Model Utilizator
- **Subliniază**: 5 tipuri de date colectate
- **Arată**: Fluxul de colectare (interfață → API → algoritm)
- **Explică**: Cum fiecare tip de date influențează recomandările

#### Long Tail
- **Subliniază**: Problema reală (4.4% piese populare vs 30.8% de nișă)
- **Arată**: Algoritmul de diversificare
- **Demonstrează**: Îmbunătățirea diversității

#### Demo
- **Rulează live**: Dacă este posibil
- **Arată**: Interfața completă
- **Demonstrează**: Recomandări diferite pentru profiluri diferite

### 5. Răspunsuri la Întrebări Frecvente

**Q: De ce sistem hibrid?**
A: Content-Based găsește similarități acustice, dar poate fi limitat. Knowledge-Based personalizează pe baza profilului, dar poate ignora similarități acustice. Hibridul combină avantajele ambelor.

**Q: Cum funcționează integrarea cu Recombee?**
A: Recombee oferă infrastructură pentru stocare utilizatori, items și interacțiuni. Învață automat din comportamentul utilizatorilor și optimizează recomandările în timp real.

**Q: Ce face algoritmul de diversificare?**
A: Asigură că recomandările provin din genuri diverse, prevenind concentrarea pe un singur gen și expunând utilizatorul la muzică variată (rezolvând long tail).

**Q: Cum rezolvați cold start?**
A: Pentru utilizatori noi, folosim Knowledge-Based cu preferințe declarate. Recomandăm piese populare din genurile preferate până când colectăm suficiente date despre comportament.

**Q: De ce 60% Content-Based și 40% Knowledge-Based?**
A: Ponderile pot fi ajustate. Am ales 60/40 pentru că similaritatea acustică este mai obiectivă, dar preferințele utilizatorului sunt importante pentru personalizare.

### 6. Checklist Pre-Prezentare

- [ ] Sistemul rulează fără erori
- [ ] Interfața web este accesibilă
- [ ] Exemplele sunt extrase și documentate
- [ ] Screenshot-urile sunt pregătite
- [ ] Pseudocod-ul este clar și corect
- [ ] Statisticile sunt actualizate
- [ ] Demo-ul este testat
- [ ] Documentația este completă

### 7. Timp Recomandat per Slide

- Slide 1 (Titlu): 1 minut
- Slide 2 (Funcționalitate): 3-4 minute
- Slide 3 (Dataset): 2-3 minute
- Slide 4 (Model Utilizator): 2-3 minute
- Slide 5 (Long Tail): 2-3 minute
- Slide 6 (Demo): 3-4 minute (cu demonstrație live)
- Slide 7 (Concluzii): 1-2 minute
- Slide 8 (Q&A): restul timpului

**Total**: ~15-20 minute prezentare + 5-10 minute Q&A

### 8. Tips pentru Prezentare

1. **Demonstrație Live**: Dacă este posibil, rulează interfața web în timpul prezentării
2. **Comparații Vizuale**: Arată diferențe între recomandări pentru profiluri diferite
3. **Statistici**: Folosește grafice pentru a arăta distribuția popularității (long tail)
4. **Cod**: Nu arăta prea mult cod, doar pseudocod-ul și funcțiile cheie
5. **Interactivitate**: Dacă este posibil, lasă publicul să testeze interfața

### 9. Fișiere de Referință

- `documentatie.md` - Documentație completă
- `prezentare_sumar.md` - Sumar pentru slide-uri
- `recommendation_system.py` - Cod sursă principal
- `app.py` - Aplicația web
- `test_system.py` - Teste funcționalitate
- `extract_examples.py` - Extragere exemple

### 10. Backup Plan

Dacă interfața web nu funcționează în timpul prezentării:
- Arată screenshot-urile pregătite
- Demonstrează prin CLI: `python test_system.py`
- Explică fluxul fără demo live

