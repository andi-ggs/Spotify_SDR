# 🎵 Sistem de Recomandare Muzică - Recombee Integration

Sistem de recomandare muzicală care folosește **EXCLUSIV Recombee** pentru toate tipurile de recomandări, incluzând recomandări item-to-item (piese similare) și modal interactiv pentru explorarea pieselor.

## 🎯 Funcționalități Principale

- **🤖 Recomandări Recombee**: Folosește integral API-ul Recombee pentru recomandări personalizate
- **🔗 Item-to-Item Recommendations**: Piese similare bazate pe piesele apreciate
- **📊 Tracking Complet**: Toate interacțiunile sunt trimise către Recombee cu `recomm_id`
- **🔔 Notificări Interactive**: Afișează piese similare după aprecierea unei piese
- **🎭 Modal Dialog**: Click pe piese similare pentru detalii complete cu like/dislike
- **✨ Interfață Modernă**: UI/UX plăcut cu animații și feedback vizual
- **📈 Progresiv Learning**: Sistemul învață din fiecare interacțiune

---

## 🚀 Quick Start - Instalare Rapidă

### 1. Instalează Dependențele
```bash
pip install -r requirements.txt
```

### 2. Configurează Recombee
Creează fișierul `config.py`:
```python
RECOMBEE_DATABASE_ID = "your-database-id"
RECOMBEE_PRIVATE_TOKEN = "your-private-token"  
RECOMBEE_REGION = "eu-west"  # sau regiunea ta
```

### 3. Rulează Aplicația
```bash
python app.py
```

### 4. Accesează Aplicația
Deschide browser la: `http://127.0.0.1:5001`

---

## 🎵 Cum Funcționează - Flux Complet

### 1. **Înregistrare și Onboarding**
1. Accesează aplicația → Apasă "Înregistrare" 
2. Completează formularul → Selectează genurile preferate
3. Vei fi redirecționat automat la recomandări

### 2. **Recomandări Principale**
- Sistemul cere recomandări de la Recombee folosind `RecommendItemsToUser`
- Afișează 10 piese personalizate bazate pe interacțiunile anterioare
- Fiecare recomandare include un `recomm_id` unic pentru tracking

### 3. **Interacțiuni și Piese Similare**
1. **Like pe piesă** → Trimite `AddPurchase` către Recombee
2. **Notificare automată** → Afișează 3 piese similare
3. **Click pe piesă similară** → Se deschide modal cu detalii complete
4. **Like/Dislike în modal** → Interacțiunea se trimite către Recombee
5. **Cascadă de recomandări** → După like, caută piese similare noi

### 4. **Modal Dialog pentru Piese Similare**
- **Layout identic** cu cardurile principale
- **Detalii complete**: nume, artist, gen, energie, dansabilitate, album, durată
- **Butoane interactive**: "❤️ Îmi place" și "👎 Nu îmi place"
- **Animații smooth**: Deschidere/închidere cu feedback vizual
- **Auto-închidere**: După interacțiune, modalul se închide elegant

---

## 📁 Structura Proiectului

```
Spotify_SDR/
├── 🐍 Backend Core
│   ├── app.py                              # Aplicația Flask principală
│   ├── recommendation_system.py            # Sistem Recombee (DOAR Recombee)
│   ├── user_storage.py                    # Gestionarea utilizatorilor
│   └── config.py                          # Configurație Recombee
│
├── 🎨 Frontend Templates
│   ├── templates/
│   │   ├── index.html                     # Pagina principală/demo
│   │   ├── login.html                     # Autentificare
│   │   ├── register.html                  # Înregistrare
│   │   ├── onboarding.html               # Selectare genuri
│   │   ├── recommendations.html           # Recomandări + modal piese similare
│   │   ├── user_profile.html             # Profilul utilizatorului
│   │   └── admin.html                     # Administrare și statistici
│
├── 💾 Date și Configurare
│   ├── users_data.json                   # Date utilizatori (sincronizat cu Recombee)
│   ├── auth_data.json                    # Date autentificare
│   ├── spotify_dataset.csv              # Dataset muzical (32k+ piese)
│   └── requirements.txt                  # Dependențe Python
│
└── 📚 Documentație
    └── README.md                         # Acest fișier (documentație completă)
```

---

## 🔧 API Endpoints

### 🎵 Recomandări
- `GET /api/user/{user_id}/recommendations/mixed` - Recomandări generale Recombee
- `GET /api/user/{user_id}/recommendations/similar/{track_id}` - Piese similare
- `GET /api/test-recombee-direct` - Test recomandări (fără autentificare)
- `GET /api/test-similar-tracks/{track_id}` - Test piese similare

### 🔄 Interacțiuni
- `POST /api/user/{user_id}/interaction` - Trimite interacțiune (like/dislike/view)

### 👤 Autentificare
- `POST /api/auth/login` - Autentificare
- `POST /api/auth/register` - Înregistrare
- `GET /api/auth/check` - Verificare status autentificare

### 🛠️ Administrare
- `GET /admin` - Pagina de administrare
- `GET /api/admin/interactions` - Statistici interacțiuni
- `GET /api/admin/users` - Date utilizatori
- `POST /api/sync-users-to-recombee` - Sincronizare utilizatori

---

## 🧪 Testare Rapidă

### Test Recomandări Generale
```bash
curl "http://127.0.0.1:5001/api/test-recombee-direct"
```

### Test Recomandări Similare
```bash
curl "http://127.0.0.1:5001/api/test-similar-tracks/test_track_123?count=3"
```

### Test Interacțiuni
```bash
curl -X POST "http://127.0.0.1:5001/api/user/USER_ID/interaction" \
  -H "Content-Type: application/json" \
  -d '{
    "track_id": "TRACK_ID",
    "interaction_type": "like",
    "recomm_id": "RECOMM_ID"
  }'
```

---

## 🔒 Configurare Recombee

### 1. Creează Cont Recombee
- Mergi la [recombee.com](https://recombee.com)
- Creează un cont gratuit
- Creează o nouă bază de date

### 2. Obține Credențialele
- **Database ID**: ID-ul bazei de date (ex: "my-music-db")
- **Private Token**: Token-ul privat pentru API
- **Region**: Regiunea serverului (ex: "eu-west", "us-west")

### 3. Configurează Aplicația
Creează `config.py`:
```python
RECOMBEE_DATABASE_ID = "your-database-id"
RECOMBEE_PRIVATE_TOKEN = "your-private-token"
RECOMBEE_REGION = "eu-west"
```

---

## 📊 Implementare Tehnică - 100% Recombee

### ✅ **Eliminarea Completă a Algoritmilor Locali**
- ❌ **Eliminat**: `knowledge_based_recommend()` local
- ❌ **Eliminat**: `content_based_recommend()` local  
- ❌ **Eliminat**: `hybrid_recommend()` local
- ❌ **Eliminat**: Toate fallback-urile la algoritmi locali

### ✅ **Recomandări 100% Recombee**
- ✅ **`RecommendItemsToUser`**: Pentru recomandări generale
- ✅ **`RecommendItemsToItem`**: Pentru piese similare
- ✅ **Parsing complet**: Toate proprietățile item-urilor din Recombee
- ✅ **`recomm_id` tracking**: Pentru fiecare recomandare

### ✅ **Interacțiuni Complete**
- ✅ **`AddDetailView`**: Când utilizatorul vede o piesă
- ✅ **`AddPurchase`**: Când utilizatorul dă like
- ✅ **`AddRating`**: Când utilizatorul dă dislike (rating: -1.0)
- ✅ **`AddBookmark`**: Pentru piese salvate

### ✅ **Sincronizare Utilizatori**
- ✅ **User Properties**: Gen, vârstă, genuri preferate
- ✅ **Auto-sync**: La înregistrare și actualizare profil
- ✅ **Admin Interface**: Pentru sincronizare manuală

---

## 📈 Monitorizare și Administrare

### Pagina de Administrare (`/admin`)
- ✅ **Status conexiune Recombee**
- ✅ **Statistici interacțiuni în timp real**
- ✅ **Lista utilizatori sincronizați**
- ✅ **Buton pentru sincronizare manuală**

### Loguri Detaliate
Aplicația afișează loguri pentru:
- ✅ **Conexiunea la Recombee**
- ✅ **Trimiterea interacțiunilor**
- ✅ **Cererile de recomandări**
- ✅ **Erorile și debug-ul**

---

## ⚡ Troubleshooting

### Eroare "Recombee nu este disponibil"
- Verifică `config.py` există și are credențialele corecte
- Verifică conexiunea la internet
- Verifică că Database ID și Token sunt valide

### Nu apar recomandări
- Verifică că utilizatorul există în Recombee
- Adaugă câteva interacțiuni (like/dislike)
- Verifică logurile pentru erori Recombee

### Modalul nu se deschide
- Verifică că JavaScript-ul nu are erori în consolă
- Asigură-te că utilizatorul este autentificat
- Verifică că API-ul pentru piese similare funcționează

### Sesiune expirată
- Reautentifică-te la `/login`
- Sesiunile Flask expiră la restart server

---

## 🎉 Rezultate și Beneficii

### 🚀 **Performanță**
- **Recomandări personalizate** bazate pe machine learning avansat (Recombee)
- **Scalabilitate** pentru milioane de utilizatori
- **Răspuns rapid** prin API optimizat Recombee

### 🎨 **Experiența Utilizatorului**
- **Interfață modernă** cu glassmorphism și gradiente
- **Animații smooth** pentru toate interacțiunile
- **Modal interactiv** pentru explorarea pieselor similare
- **Feedback vizual** pentru fiecare acțiune

### 📊 **Învățare Continuă**
- **Tracking complet** al tuturor interacțiunilor
- **Îmbunătățire automată** a recomandărilor
- **Personalizare progresivă** bazată pe comportament

---

## 🚀 Tehnologii Folosite

- **Backend**: Python 3.x, Flask
- **Recomandări**: Recombee API (Machine Learning)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Styling**: CSS modern cu gradiente și glassmorphism
- **Date**: JSON (local storage) + Recombee Cloud
- **Tracking**: Recombee Interactions API

---

## 🎯 Flux Complet de Utilizare

1. **📝 Înregistrare** → Selectare genuri → Redirect la recomandări
2. **🎵 Recomandări** → Recombee returnează piese personalizate  
3. **❤️ Like pe piesă** → Trimite către Recombee + caută piese similare
4. **🔔 Notificare** → Afișează 3 piese similare interactive
5. **🖱️ Click pe piesă similară** → Modal cu detalii complete
6. **👍👎 Like/Dislike în modal** → Interacțiune către Recombee
7. **🔄 Repeat** → Sistemul învață și îmbunătățește recomandările

---

## 📞 Support și Dezvoltare

Pentru întrebări sau probleme:
1. **Verifică logurile** aplicației pentru debugging
2. **Testează API-urile** cu comenzile curl de mai sus
3. **Consultă pagina `/admin`** pentru statistici sistem
4. **Verifică conexiunea Recombee** în loguri

**🎵 Enjoy your personalized music recommendations powered by Recombee! ✨**