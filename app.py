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

# Disable template caching for development
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

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

# Inițializează stocarea utilizatorilor cu referință la sistemul de recomandări
user_storage = UserStorage(recommendation_system=system)

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

@app.route('/onboarding')
def onboarding():
    """Pagina de onboarding pentru utilizatori noi"""
    # Verifică dacă utilizatorul este autentificat
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')
    return render_template('onboarding.html')

@app.route('/admin')
def admin():
    """Pagina de administrare"""
    return render_template('admin.html')

@app.route('/recommendations')
def recommendations():
    """Pagina de recomandări personalizate"""
    # Verifică dacă utilizatorul este autentificat
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')
    return render_template('recommendations.html')


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

@app.route('/api/sync-users-to-recombee', methods=['POST'])
def sync_users_to_recombee():
    """Sincronizează toți utilizatorii cu Recombee"""
    try:
        # Load all users data
        users_data = user_storage.load_users_data()
        
        # Sync to Recombee
        system.sync_all_users_to_recombee(users_data)
        
        return jsonify({
            'success': True,
            'message': f'Sincronizare completă: {len(users_data)} utilizatori',
            'users_synced': len(users_data)
        })
    except Exception as e:
        print(f"Eroare la sincronizarea utilizatorilor: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/users', methods=['GET'])
def get_admin_users():
    """Returnează lista utilizatorilor pentru administrare"""
    try:
        users_data = user_storage.load_users_data()
        
        # Format users for admin display
        formatted_users = []
        for user_id, user_data in users_data.items():
            formatted_users.append({
                'user_id': user_id,
                'email': user_data.get('email', 'N/A'),
                'name': user_data.get('name', 'N/A'),
                'registered_at': user_data.get('registered_at', 'N/A'),
                'preferred_genres': user_data.get('preferred_genres', []),
                'liked_tracks_count': len(user_data.get('liked_tracks', [])),
                'interactions_count': len(user_data.get('interactions', [])),
                'total_likes': user_data.get('stats', {}).get('total_likes', 0),
                'recommendation_type': 'knowledge-based' if len(user_data.get('liked_tracks', [])) < 10 else 'mixed' if len(user_data.get('liked_tracks', [])) < 25 else 'content-based'
            })
        
        return jsonify({
            'success': True,
            'users': formatted_users,
            'total_users': len(formatted_users)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/interactions', methods=['GET'])
def get_admin_interactions():
    """Returnează statistici despre interacțiunile trimise către Recombee"""
    try:
        users_data = user_storage.load_users_data()
        
        total_interactions = 0
        interaction_types = {}
        recent_interactions = []
        
        for user_id, user_data in users_data.items():
            interactions = user_data.get('interactions', [])
            total_interactions += len(interactions)
            
            for interaction in interactions:
                interaction_type = interaction.get('type', 'unknown')
                interaction_types[interaction_type] = interaction_types.get(interaction_type, 0) + 1
                
                # Adaugă la interacțiunile recente (ultimele 10)
                if len(recent_interactions) < 10:
                    recent_interactions.append({
                        'user_id': user_id,
                        'track_id': interaction.get('track_id'),
                        'type': interaction_type,
                        'timestamp': interaction.get('timestamp'),
                        'recomm_id': interaction.get('recomm_id'),
                        'has_recomm_id': bool(interaction.get('recomm_id'))
                    })
        
        # Sortează interacțiunile recente după timestamp
        recent_interactions.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'total_interactions': total_interactions,
            'interaction_types': interaction_types,
            'recent_interactions': recent_interactions[:10],
            'recombee_tracking_enabled': system.recombee_client is not None
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test-recommendations', methods=['GET'])
def get_test_recommendations():
    """Test endpoint for recommendations using ONLY Recombee"""
    try:
        # Folosește DOAR Recombee pentru recomandări test
        if not system.recombee_client:
            return jsonify({'error': 'Recombee nu este disponibil'}), 503
        
        test_user_id = "test_user_anonymous"
        
        print(f"🧪 Test recomandări Recombee pentru utilizator anonim: {test_user_id}")
        
        # Obține recomandări de la Recombee pentru utilizator test
        recommendations = system.recombee_recommend(
            user_id=test_user_id,
            num_recommendations=10,
            scenario='homepage',
            return_properties=True
        )
        
        if not recommendations:
            return jsonify({'error': 'Nu s-au putut obține recomandări de la Recombee'}), 503
        
        # Adaugă label-ul pentru sursa recomandării
        for rec in recommendations:
            rec['source_label'] = 'Recombee test recommendations'
            rec['source'] = 'recombee_test'
        
        return jsonify({
            'recommendations': recommendations,
            'source': 'recombee_test',
            'message': 'Test recommendations from Recombee only'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint-ul pentru content-based local a fost eliminat - folosim doar Recombee

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
            'message': 'Cont creat cu succes',
            'redirect': '/onboarding'  # Redirect to onboarding
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
            'message': 'Conectare reușită',
            'redirect': '/recommendations'  # Redirect to recommendations
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
    """Get recommendations using ONLY Recombee"""
    # Verifică autentificarea
    session_user_id = session.get('user_id')
    print(f"DEBUG CONTENT: Session user_id: {session_user_id}, URL user_id: {user_id}")
    if not session_user_id:
        return jsonify({'error': 'Nu ești autentificat'}), 401
    if session_user_id != user_id:
        return jsonify({'error': f'Neautorizat - session: {session_user_id}, requested: {user_id}'}), 401
    
    # Folosește DOAR Recombee pentru recomandări
    if not system.recombee_client:
        return jsonify({'error': 'Recombee nu este disponibil'}), 503
    
    try:
        recommendations = system.recombee_recommend(
            user_id=user_id,
            num_recommendations=10,
            scenario='homepage',
            return_properties=True
        )
        
        if not recommendations:
            return jsonify({'error': 'Nu s-au putut obține recomandări de la Recombee'}), 503
        
        # Add source labels
        for rec in recommendations:
            rec['source_label'] = 'Recombee recommendations'
            rec['source'] = 'recombee'
        
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    # Obține parametri din query string (preferințe curente)
    preferred_genres = request.args.get('genres', '').split(',')
    preferred_genres = [g.strip() for g in preferred_genres if g.strip()]
    energy_level = float(request.args.get('energy', 0.5))
    danceability = float(request.args.get('danceability', 0.5))

@app.route('/api/user/<user_id>/recommendations/knowledge-based', methods=['GET'])
def get_knowledge_based_recommendations(user_id):
    """Get recommendations using ONLY Recombee"""
    # Verifică autentificarea
    session_user_id = session.get('user_id')
    print(f"DEBUG: Session user_id: {session_user_id}, URL user_id: {user_id}")
    if not session_user_id:
        return jsonify({'error': 'Nu ești autentificat'}), 401
    if session_user_id != user_id:
        return jsonify({'error': f'Neautorizat - session: {session_user_id}, requested: {user_id}'}), 401
    
    # Folosește DOAR Recombee pentru recomandări
    if not system.recombee_client:
        return jsonify({'error': 'Recombee nu este disponibil'}), 503
    
    try:
        recommendations = system.recombee_recommend(
            user_id=user_id,
            num_recommendations=10,
            scenario='homepage',
            return_properties=True
        )
        
        if not recommendations:
            return jsonify({'error': 'Nu s-au putut obține recomandări de la Recombee'}), 503
        
        # Add source labels
        for rec in recommendations:
            rec['source_label'] = 'Recombee recommendations'
            rec['source'] = 'recombee'
        
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

# ==================== NEW API ENDPOINTS FOR IMPROVED FLOW ====================

@app.route('/api/user/onboarding', methods=['POST'])
def user_onboarding():
    """Handle onboarding preferences for new users"""
    data = request.json
    user_id = data.get('user_id')
    preferred_genres = data.get('preferred_genres', [])
    
    if not user_id or not preferred_genres:
        return jsonify({'success': False, 'error': 'user_id și preferred_genres sunt necesare'}), 400
    
    # Update user preferences
    user_storage.update_user_preferences(
        user_id=user_id,
        preferred_genres=preferred_genres,
        mood='happy',  # Default
        listening_time='medium',  # Default
        energy_level=0.5,
        danceability=0.5
    )
    
    # Create profile in recommendation system
    system.create_user_profile(
        user_id=user_id,
        preferred_genres=preferred_genres,
        mood='happy',
        listening_time='medium',
        energy_level=0.5,
        danceability=0.5
    )
    
    return jsonify({
        'success': True,
        'message': 'Preferințe salvate cu succes'
    })

@app.route('/api/user/<user_id>/recommendations/mixed', methods=['GET'])
def get_mixed_recommendations(user_id):
    """Get recommendations using ONLY Recombee"""
    # Verifică autentificarea
    session_user_id = session.get('user_id')
    print(f"DEBUG MIXED: Session user_id: {session_user_id}, URL user_id: {user_id}")
    if not session_user_id:
        return jsonify({'error': 'Nu ești autentificat'}), 401
    if session_user_id != user_id:
        return jsonify({'error': f'Neautorizat - session: {session_user_id}, requested: {user_id}'}), 401
    
    user_profile = user_storage.get_user_profile(user_id)
    if not user_profile:
        return jsonify({'error': 'Utilizator nu există'}), 404
    
    # Get user stats
    liked_tracks_count = len(user_profile.get('liked_tracks', []))
    
    # Folosește DOAR Recombee pentru recomandări
    if not system.recombee_client:
        return jsonify({'error': 'Recombee nu este disponibil'}), 503
    
    print(f"🎯 Folosind DOAR Recombee pentru recomandări către {user_id}")
    
    # Determină scenariul bazat pe numărul de piese apreciate
    if liked_tracks_count < 5:
        scenario = 'homepage'  # Pentru utilizatori noi
        recommendation_type = "Recombee recommendations (new user)"
    elif liked_tracks_count < 25:
        scenario = 'homepage'  # Utilizatori cu puține interacțiuni
        recommendation_type = "Recombee recommendations (learning)"
    else:
        scenario = 'homepage'  # Utilizatori cu multe interacțiuni
        recommendation_type = "Recombee recommendations (personalized)"
    
    # Obține recomandări de la Recombee
    recommendations = system.recombee_recommend(
        user_id=user_id,
        num_recommendations=10,
        scenario=scenario,
        return_properties=True
    )
    
    if not recommendations:
        return jsonify({'error': 'Nu s-au putut obține recomandări de la Recombee'}), 503
    
    # Adaugă label-ul pentru sursa recomandării
    for rec in recommendations:
        rec['source_label'] = recommendation_type
        rec['source'] = 'recombee'
    
    return jsonify({
        'recommendations': recommendations,
        'source': 'recombee',
        'scenario': scenario,
        'liked_tracks_count': liked_tracks_count
    })

@app.route('/api/user/<user_id>/interaction', methods=['POST'])
def add_user_interaction(user_id):
    """Add user interaction (like/dislike) with enhanced tracking"""
    # Verifică autentificarea
    if session.get('user_id') != user_id:
        return jsonify({'error': 'Neautorizat'}), 401
    
    data = request.json
    track_id = data.get('track_id')
    interaction_type = data.get('interaction_type', 'listen')
    recomm_id = data.get('recomm_id')  # ID-ul recomandării pentru tracking
    
    if not track_id:
        return jsonify({'success': False, 'error': 'track_id este necesar'}), 400
    
    # Add interaction to user storage (care va trimite automat către Recombee)
    user_storage.add_interaction(
        user_id=user_id,
        track_id=track_id,
        interaction_type=interaction_type,
        metadata=data.get('metadata', {}),
        recomm_id=recomm_id
    )
    
    # If it's a like, add to liked tracks (pentru compatibilitate)
    if interaction_type == 'like':
        user_storage.add_liked_track(user_id, track_id)
    elif interaction_type == 'dislike':
        user_storage.add_disliked_track(user_id, track_id)
    
    # Interacțiunea este deja trimisă către Recombee prin user_storage.add_interaction()
    
    return jsonify({
        'success': True, 
        'message': 'Interacțiune adăugată și trimisă către Recombee',
        'recomm_id': recomm_id
    })

@app.route('/api/user/<user_id>/recommendations/similar/<track_id>', methods=['GET'])
def get_similar_track_recommendations(user_id, track_id):
    """Get recommendations similar to a specific track using Recombee"""
    # Verifică autentificarea
    session_user_id = session.get('user_id')
    if not session_user_id:
        return jsonify({'error': 'Nu ești autentificat'}), 401
    if session_user_id != user_id:
        return jsonify({'error': f'Neautorizat - session: {session_user_id}, requested: {user_id}'}), 401
    
    try:
        num_recommendations = int(request.args.get('count', 5))
        
        print(f"🎵 Cerere recomandări similare cu {track_id} pentru {user_id}")
        
        # Obține recomandări similare folosind Recombee
        recommendations = system.recombee_recommend_similar_tracks(
            track_id=track_id,
            user_id=user_id,
            num_recommendations=num_recommendations,
            scenario='similar-tracks'
        )
        
        return jsonify({
            'recommendations': recommendations,
            'based_on_track': track_id,
            'source': 'recombee_similar',
            'count': len(recommendations)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-recombee-direct', methods=['GET'])
def test_recombee_direct():
    """Test direct Recombee recommendations"""
    try:
        if not system.recombee_client:
            return jsonify({
                'error': 'Recombee client nu este disponibil',
                'recombee_available': False
            }), 400
        
        test_user_id = "test_user_direct"
        
        print(f"🧪 Test direct Recombee pentru {test_user_id}")
        
        # Test direct cu Recombee
        recommendations = system.recombee_recommend(
            user_id=test_user_id,
            num_recommendations=5,
            scenario='homepage'
        )
        
        return jsonify({
            'success': True,
            'recombee_available': True,
            'recommendations_count': len(recommendations),
            'recommendations': recommendations[:3],  # Doar primele 3 pentru test
            'message': f'Recombee test successful: {len(recommendations)} recommendations'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'recombee_available': system.recombee_client is not None
        }), 500

@app.route('/api/test-similar-tracks/<track_id>', methods=['GET'])
def test_similar_tracks(track_id):
    """Test similar tracks recommendations without authentication"""
    try:
        num_recommendations = int(request.args.get('count', 5))
        
        print(f"🧪 Test recomandări similare cu {track_id}")
        
        # Test similar tracks cu Recombee
        recommendations = system.recombee_recommend_similar_tracks(
            track_id=track_id,
            user_id="test_user_similar",
            num_recommendations=num_recommendations,
            scenario='similar-tracks'
        )
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'based_on_track': track_id,
            'source': 'recombee_similar_test',
            'count': len(recommendations),
            'message': f'Similar tracks test successful: {len(recommendations)} recommendations'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'recombee_available': system.recombee_client is not None
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)

