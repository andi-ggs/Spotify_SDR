"""
Interfață Web Demo pentru Sistemul de Recomandare
Flask Application
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from recommendation_system import SpotifyRecommendationSystem
from user_storage import UserStorage
import os
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Pentru sesiuni

# Inițializează stocarea utilizatorilor
user_storage = UserStorage()

# Încarcă configurația Recombee
try:
    from config import RECOMBEE_DATABASE_ID, RECOMBEE_PRIVATE_TOKEN, RECOMBEE_PUBLIC_TOKEN, RECOMBEE_REGION
    recombee_db = RECOMBEE_DATABASE_ID
    recombee_private_token = RECOMBEE_PRIVATE_TOKEN
    recombee_public_token = getattr(__import__('config', fromlist=['RECOMBEE_PUBLIC_TOKEN']), 'RECOMBEE_PUBLIC_TOKEN', None)
    recombee_region = getattr(__import__('config', fromlist=['RECOMBEE_REGION']), 'RECOMBEE_REGION', None)
    print(f"✓ Configurație Recombee încărcată: Database ID = {recombee_db}, Region = {recombee_region}")
except ImportError:
    # Fallback la variabile de mediu dacă config.py nu există
    recombee_db = os.getenv('RECOMBEE_DATABASE_ID')
    recombee_private_token = os.getenv('RECOMBEE_PRIVATE_TOKEN')
    recombee_public_token = os.getenv('RECOMBEE_PUBLIC_TOKEN')
    recombee_region = os.getenv('RECOMBEE_REGION')
    if recombee_db:
        print(f"✓ Configurație Recombee din variabile de mediu: Database ID = {recombee_db}")

# Inițializează sistemul de recomandare
# Dacă Recombee este configurat, îl folosește; altfel folosește implementarea locală
system = SpotifyRecommendationSystem(
    'spotify_dataset.csv',
    recombee_db=recombee_db,
    recombee_private_token=recombee_private_token,
    recombee_public_token=recombee_public_token,
    recombee_region=recombee_region
)

@app.route('/')
def index():
    """Pagina principală"""
    return render_template('index.html')

@app.route('/login')
def login():
    """Pagina de login"""
    return render_template('login.html')

@app.route('/register')
def register():
    """Pagina de înregistrare"""
    return render_template('register.html')

@app.route('/profile')
def user_profile():
    """Pagina de profil utilizator"""
    # Verifică dacă utilizatorul este autentificat
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')
    return render_template('user_profile.html')

@app.route('/api/tracks', methods=['GET'])
def get_tracks():
    """Returnează lista de piese pentru selectare"""
    tracks = []
    for track_id, track in list(system.tracks.items())[:100]:  # Limitează pentru performanță
        tracks.append({
            'id': track_id,
            'name': track.track_name,
            'artist': track.artists,
            'genre': track.track_genre
        })
    return jsonify(tracks)

@app.route('/api/recommend', methods=['POST'])
def recommend():
    """Endpoint pentru obținerea recomandărilor"""
    data = request.json
    
    user_id = data.get('user_id', 'demo_user')
    preferred_genres = data.get('preferred_genres', [])
    mood = data.get('mood', 'happy')
    listening_time = data.get('listening_time', 'medium')
    energy_level = float(data.get('energy_level', 0.5))
    danceability = float(data.get('danceability', 0.5))
    seed_track_id = data.get('seed_track_id')
    num_recommendations = int(data.get('num_recommendations', 10))
    
    # Creează sau actualizează profilul utilizatorului
    system.create_user_profile(
        user_id=user_id,
        preferred_genres=preferred_genres,
        mood=mood,
        listening_time=listening_time,
        energy_level=energy_level,
        danceability=danceability
    )
    
    # Obține recomandări (folosește Recombee dacă este disponibil)
    use_recombee = data.get('use_recombee', True)  # Default: folosește Recombee dacă este disponibil
    recommendations = system.hybrid_recommend(
        user_id=user_id,
        seed_track_id=seed_track_id,
        num_recommendations=num_recommendations,
        use_recombee=use_recombee
    )
    
    # Aplică diversificare pentru long tail
    diversified_recommendations = system.solve_long_tail_problem(recommendations)
    
    return jsonify({
        'recommendations': diversified_recommendations,
        'user_profile': {
            'preferred_genres': preferred_genres,
            'mood': mood,
            'listening_time': listening_time
        }
    })

@app.route('/api/dataset-examples', methods=['GET'])
def get_dataset_examples():
    """Returnează exemple specifice din dataset"""
    examples = system.get_dataset_examples()
    
    result = {}
    for key, track in examples.items():
        if track:
            result[key] = {
                'track_name': track.track_name,
                'artists': track.artists,
                'genre': track.track_genre,
                'duration_ms': track.duration_ms,
                'energy': track.energy,
                'popularity': track.popularity,
                'danceability': track.danceability
            }
    
    return jsonify(result)

@app.route('/api/content-based/<track_id>', methods=['GET'])
def content_based_recommend(track_id):
    """Recomandări Content-Based pentru o piesă specifică"""
    recommendations = system.content_based_recommend(track_id, num_recommendations=10)
    return jsonify({'recommendations': recommendations})

# ==================== API ENDPOINTS PENTRU AUTENTIFICARE ====================

@app.route('/api/auth/register', methods=['POST'])
def auth_register():
    """Înregistrează un utilizator nou cu autentificare"""
    data = request.json
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    preferred_genres = data.get('preferred_genres', [])
    preferred_artists = data.get('preferred_artists', [])
    
    if not username or not email or not password:
        return jsonify({'success': False, 'error': 'Username, email și parolă sunt obligatorii'}), 400
    
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Parola trebuie să aibă minim 6 caractere'}), 400
    
    if not preferred_genres:
        return jsonify({'success': False, 'error': 'Selectează cel puțin un gen muzical'}), 400
    
    # Înregistrează utilizatorul
    result = user_storage.register_user_with_auth(
        username=username,
        email=email,
        password=password,
        name=name,
        preferred_genres=preferred_genres,
        preferred_artists=preferred_artists
    )
    
    if result['success']:
        user_id = result['user_id']
        
        # Creează profil în sistemul de recomandare
        system.create_user_profile(
            user_id=user_id,
            preferred_genres=preferred_genres,
            mood='happy',  # Default
            listening_time='medium',  # Default
            energy_level=0.5,
            danceability=0.5
        )
        
        # Setează sesiunea
        session['user_id'] = user_id
        session['username'] = username
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'username': username,
            'message': 'Cont creat cu succes'
        })
    else:
        return jsonify(result), 400

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    """Autentifică un utilizator"""
    data = request.json
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username și parolă sunt obligatorii'}), 400
    
    result = user_storage.authenticate_user(username, password)
    
    if result['success']:
        # Setează sesiunea
        session['user_id'] = result['user_id']
        session['username'] = result['username']
        
        return jsonify({
            'success': True,
            'user_id': result['user_id'],
            'username': result['username'],
            'message': 'Conectare reușită'
        })
    else:
        return jsonify(result), 401

@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    """Deconectează utilizatorul"""
    session.clear()
    return jsonify({'success': True, 'message': 'Deconectare reușită'})

@app.route('/api/auth/check', methods=['GET'])
def auth_check():
    """Verifică dacă utilizatorul este autentificat"""
    user_id = session.get('user_id')
    if user_id:
        return jsonify({
            'authenticated': True,
            'user_id': user_id,
            'username': session.get('username')
        })
    return jsonify({'authenticated': False}), 401

# ==================== API ENDPOINTS PENTRU UTILIZATORI ====================

@app.route('/api/user/register', methods=['POST'])
def register_user():
    """Înregistrează un utilizator nou sau actualizează profilul"""
    data = request.json
    
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'user_id este necesar'}), 400
    
    # Înregistrează utilizatorul
    user_storage.register_user(
        user_id=user_id,
        email=data.get('email'),
        name=data.get('name')
    )
    
    # Actualizează preferințele
    user_storage.update_user_preferences(
        user_id=user_id,
        preferred_genres=data.get('preferred_genres', []),
        preferred_artists=data.get('preferred_artists', []),
        mood=data.get('mood'),
        listening_time=data.get('listening_time'),
        energy_level=data.get('energy_level'),
        danceability=data.get('danceability')
    )
    
    # Creează profil în sistemul de recomandare
    system.create_user_profile(
        user_id=user_id,
        preferred_genres=data.get('preferred_genres', []),
        mood=data.get('mood', 'happy'),
        listening_time=data.get('listening_time', 'medium'),
        energy_level=float(data.get('energy_level', 0.5)),
        danceability=float(data.get('danceability', 0.5))
    )
    
    return jsonify({
        'success': True,
        'user_id': user_id,
        'message': 'Utilizator înregistrat cu succes'
    })

@app.route('/api/user/<user_id>/recommendations/content-based', methods=['GET'])
def get_content_based_recommendations(user_id):
    """Obține recomandări Content-Based bazate pe piese apreciate și preferințe curente"""
    # Verifică autentificarea
    if session.get('user_id') != user_id:
        return jsonify({'error': 'Neautorizat'}), 401
    """Obține recomandări Content-Based bazate pe piese apreciate și preferințe curente"""
    user_profile = user_storage.get_user_profile(user_id)
    
    # Obține parametri din query string (preferințe curente)
    preferred_genres = request.args.get('genres', '').split(',')
    preferred_genres = [g.strip() for g in preferred_genres if g.strip()]
    energy_level = float(request.args.get('energy', 0.5))
    danceability = float(request.args.get('danceability', 0.5))
    
    # Dacă nu sunt genuri în query, folosește din profil
    if not preferred_genres and user_profile:
        preferred_genres = user_profile.get('preferred_genres', [])
    
    # Obține piese apreciate
    liked_tracks = user_storage.get_user_liked_tracks(user_id)
    listening_history = user_storage.get_user_listening_history(user_id, limit=10)
    
    recommendations = []
    
    # Strategie 1: Dacă are piese apreciate, folosește-le ca seed
    if liked_tracks:
        seed_tracks = liked_tracks[:5]
        for seed_track_id in seed_tracks:
            if seed_track_id in system.tracks:
                recs = system.content_based_recommend(seed_track_id, num_recommendations=5)
                recommendations.extend(recs)
    
    # Strategie 2: Dacă are istoric de ascultare, folosește ultimele piese
    elif listening_history:
        seed_tracks = [h['track_id'] for h in listening_history[-5:]]
        for seed_track_id in seed_tracks:
            if seed_track_id in system.tracks:
                recs = system.content_based_recommend(seed_track_id, num_recommendations=5)
                recommendations.extend(recs)
    
    # Strategie 3: Dacă nu are istoric, folosește piese din genurile preferate ca seed
    elif preferred_genres:
        # Găsește piese populare din genurile preferate
        seed_tracks = []
        for genre in preferred_genres:
            if genre in system.genre_tracks:
                # Sortează piese din gen după popularitate
                genre_tracks = [(tid, system.tracks[tid]) for tid in system.genre_tracks[genre] if tid in system.tracks]
                genre_tracks.sort(key=lambda x: x[1].popularity, reverse=True)
                # Ia primele 2 piese populare din fiecare gen
                for tid, track in genre_tracks[:2]:
                    if tid not in seed_tracks:
                        seed_tracks.append(tid)
                        if len(seed_tracks) >= 5:
                            break
                if len(seed_tracks) >= 5:
                    break
        
        # Folosește piese din genurile preferate ca seed pentru Content-Based
        for seed_track_id in seed_tracks[:5]:
            if seed_track_id in system.tracks:
                recs = system.content_based_recommend(seed_track_id, num_recommendations=3)
                recommendations.extend(recs)
    
    # Filtrare și sortare
    if recommendations:
        # Filtrare după genuri preferate (dacă sunt specificate)
        if preferred_genres:
            filtered_recs = []
            for rec in recommendations:
                track_genre = rec.get('track_genre') or rec.get('genre', '')
                # Prioritate pentru genurile preferate, dar include și altele
                if track_genre in preferred_genres:
                    rec['genre_match'] = True
                filtered_recs.append(rec)
            recommendations = filtered_recs
        
        # Elimină duplicatele
        seen = set()
        unique_recs = []
        for rec in recommendations:
            if rec['track_id'] not in seen:
                seen.add(rec['track_id'])
                rec['source'] = 'content-based'
                unique_recs.append(rec)
        
        # Sortează: mai întâi genuri preferate, apoi după similaritate
        unique_recs.sort(key=lambda x: (
            not x.get('genre_match', False),  # Genuri preferate primele
            -x.get('similarity_score', 0)      # Apoi după similaritate
        ))
        recommendations = unique_recs[:10]
    else:
        # Fallback: Knowledge-Based
        recommendations = system.knowledge_based_recommend(user_id, num_recommendations=10)
        for rec in recommendations:
            rec['source'] = 'content-based-fallback'
    
    return jsonify({'recommendations': recommendations})

@app.route('/api/user/<user_id>/recommendations/knowledge-based', methods=['GET'])
def get_knowledge_based_recommendations(user_id):
    """Obține recomandări Knowledge-Based bazate pe profilul utilizatorului și preferințe curente"""
    # Verifică autentificarea
    if session.get('user_id') != user_id:
        return jsonify({'error': 'Neautorizat'}), 401
    """Obține recomandări Knowledge-Based bazate pe profilul utilizatorului și preferințe curente"""
    user_profile = user_storage.get_user_profile(user_id)
    
    # Obține parametri din query string (preferințe curente din formular)
    preferred_genres = request.args.get('genres', '').split(',')
    preferred_genres = [g.strip() for g in preferred_genres if g.strip()]
    mood = request.args.get('mood', 'happy')
    listening_time = request.args.get('listening_time', 'medium')
    energy_level = float(request.args.get('energy', 0.5))
    danceability = float(request.args.get('danceability', 0.5))
    
    # Dacă nu sunt genuri în query, folosește din profil
    if not preferred_genres and user_profile:
        preferred_genres = user_profile.get('preferred_genres', [])
        mood = user_profile.get('mood_preferences', [{}])[-1].get('mood', 'happy') if user_profile.get('mood_preferences') else 'happy'
        listening_time = user_profile.get('listening_time_preference', 'medium')
        energy_level = user_profile.get('energy_level', 0.5)
        danceability = user_profile.get('danceability', 0.5)
    
    if not preferred_genres:
        return jsonify({'recommendations': [], 'message': 'Nu sunt genuri preferate'}), 400
    
    # Actualizează profilul în sistem cu preferințele curente
    system.create_user_profile(
        user_id=user_id,
        preferred_genres=preferred_genres,
        mood=mood,
        listening_time=listening_time,
        energy_level=energy_level,
        danceability=danceability
    )
    
    # Obține recomandări Knowledge-Based
    recommendations = system.knowledge_based_recommend(user_id, num_recommendations=15)
    
    # Filtrare suplimentară după artiști preferați (dacă există)
    if user_profile:
        preferred_artists = user_profile.get('preferred_artists', [])
        if preferred_artists:
            # Bonus pentru piese de artiști preferați
            for rec in recommendations:
                track_artists = rec.get('artists', '').lower()
                for artist in preferred_artists:
                    if artist.lower() in track_artists:
                        rec['match_score'] = min(1.0, rec.get('match_score', 0) + 0.2)
                        break
    
    # Sortează după scor
    recommendations.sort(key=lambda x: x.get('match_score', 0), reverse=True)
    
    # Adaugă sursa
    for rec in recommendations[:10]:  # Limitează la 10
        rec['source'] = 'knowledge-based'
    
    return jsonify({'recommendations': recommendations[:10]})

@app.route('/api/user/<user_id>/interaction', methods=['POST'])
def add_interaction(user_id):
    """Adaugă o interacțiune (like, listen, etc.)"""
    data = request.json
    
    track_id = data.get('track_id')
    interaction_type = data.get('interaction_type', 'listen')
    
    if not track_id:
        return jsonify({'success': False, 'error': 'track_id este necesar'}), 400
    
    # Adaugă interacțiunea
    user_storage.add_interaction(
        user_id=user_id,
        track_id=track_id,
        interaction_type=interaction_type,
        metadata=data.get('metadata', {})
    )
    
    # Dacă este Recombee, adaugă interacțiunea acolo
    if system.recombee_client:
        try:
            from recombee_api_client.api_requests import AddDetailView, AddBookmark
            
            if interaction_type == 'listen':
                system.recombee_client.send(AddDetailView(user_id, track_id))
            elif interaction_type == 'like':
                system.recombee_client.send(AddBookmark(user_id, track_id))
        except Exception as e:
            print(f"Eroare la adăugarea interacțiunii în Recombee: {e}")
    
    return jsonify({'success': True, 'message': 'Interacțiune adăugată'})

@app.route('/api/user/<user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    """Obține statisticile utilizatorului"""
    user_profile = user_storage.get_user_profile(user_id)
    
    if not user_profile:
        return jsonify({'error': 'Utilizator nu există'}), 404
    
    return jsonify({
        'stats': user_storage.get_user_stats(user_id),
        'preferred_genres': user_profile.get('preferred_genres', []),
        'preferred_artists': user_profile.get('preferred_artists', []),
        'total_interactions': len(user_profile.get('interactions', [])),
        'liked_tracks_count': len(user_profile.get('liked_tracks', []))
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)

