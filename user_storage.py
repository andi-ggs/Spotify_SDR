"""
Sistem de stocare pentru utilizatori și preferințe
Salvează datele utilizatorilor și interacțiunile lor
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

class UserStorage:
    """Gestionează stocarea datelor utilizatorilor"""
    
    def __init__(self, storage_file: str = 'users_data.json', recommendation_system=None):
        self.storage_file = storage_file
        self.users = self._load_users()
        self.auth_data = self._load_auth_data()  # Stochează datele de autentificare
        self.recommendation_system = recommendation_system  # Pentru sincronizare cu Recombee
    
    def _load_users(self) -> Dict:
        """Încarcă datele utilizatorilor din fișier"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def load_users_data(self) -> Dict:
        """Returnează toate datele utilizatorilor pentru sincronizare"""
        return self._load_users()
    
    def _save_users(self):
        """Salvează datele utilizatorilor în fișier"""
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, indent=2, ensure_ascii=False)
    
    def get_user_data_for_sync(self, user_id: str) -> Optional[Dict]:
        """Returnează datele unui utilizator pentru sincronizare cu Recombee"""
        return self.users.get(user_id)
    
    def _load_auth_data(self) -> Dict:
        """Încarcă datele de autentificare"""
        auth_file = 'auth_data.json'
        if os.path.exists(auth_file):
            try:
                with open(auth_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_auth_data(self):
        """Salvează datele de autentificare"""
        auth_file = 'auth_data.json'
        with open(auth_file, 'w', encoding='utf-8') as f:
            json.dump(self.auth_data, f, indent=2, ensure_ascii=False)
    
    def _hash_password(self, password: str) -> str:
        """Hash-uiește parola"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, user_id: str, email: str = None, name: str = None) -> bool:
        """Înregistrează un utilizator nou"""
        if user_id not in self.users:
            self.users[user_id] = {
                'user_id': user_id,
                'email': email,
                'name': name,
                'registered_at': datetime.now().isoformat(),
                'preferred_genres': [],
                'preferred_artists': [],
                'mood_preferences': [],
                'listening_history': [],
                'liked_tracks': [],
                'interactions': [],
                'stats': {
                    'total_listens': 0,
                    'total_likes': 0,
                    'favorite_genres': {},
                    'favorite_artists': {}
                }
            }
            self._save_users()
            return True
        return False
    
    def register_user_with_auth(self, username: str, email: str, password: str, 
                                name: str, preferred_genres: List[str] = None,
                                preferred_artists: List[str] = None) -> Dict:
        """
        Înregistrează un utilizator nou cu autentificare
        Returnează {'success': bool, 'user_id': str, 'error': str}
        """
        # Verifică dacă username-ul sau email-ul există deja
        for user_id, auth_info in self.auth_data.items():
            if auth_info.get('username') == username:
                return {'success': False, 'error': 'Username-ul este deja folosit'}
            if auth_info.get('email') == email:
                return {'success': False, 'error': 'Email-ul este deja înregistrat'}
        
        # Generează user_id
        user_id = 'user_' + str(int(datetime.now().timestamp() * 1000))
        
        # Hash-uiește parola
        hashed_password = self._hash_password(password)
        
        # Salvează datele de autentificare
        self.auth_data[user_id] = {
            'username': username,
            'email': email,
            'password_hash': hashed_password,
            'created_at': datetime.now().isoformat()
        }
        self._save_auth_data()
        
        # Creează profilul utilizatorului
        self.register_user(user_id, email, name)
        
        # Actualizează preferințele
        if preferred_genres:
            self.update_user_preferences(
                user_id=user_id,
                preferred_genres=preferred_genres,
                preferred_artists=preferred_artists
            )
        
        # Sincronizează cu Recombee dacă este disponibil
        if self.recommendation_system:
            try:
                user_data = self.get_user_data_for_sync(user_id)
                if user_data:
                    self.recommendation_system.sync_user_to_recombee(user_data)
            except Exception as e:
                print(f"Eroare la sincronizarea utilizatorului nou cu Recombee: {e}")
        
        return {'success': True, 'user_id': user_id}
    
    def authenticate_user(self, username: str, password: str) -> Dict:
        """
        Autentifică un utilizator
        Returnează {'success': bool, 'user_id': str, 'username': str, 'error': str}
        """
        hashed_password = self._hash_password(password)
        
        # Caută utilizatorul după username sau email
        for user_id, auth_info in self.auth_data.items():
            if auth_info.get('username') == username or auth_info.get('email') == username:
                if auth_info.get('password_hash') == hashed_password:
                    return {
                        'success': True,
                        'user_id': user_id,
                        'username': auth_info.get('username')
                    }
                else:
                    return {'success': False, 'error': 'Parolă incorectă'}
        
        return {'success': False, 'error': 'Utilizator nu există'}
    
    def get_user_by_username(self, username: str) -> Optional[str]:
        """Obține user_id după username"""
        for user_id, auth_info in self.auth_data.items():
            if auth_info.get('username') == username:
                return user_id
        return None
    
    def update_user_preferences(self, user_id: str, preferred_genres: List[str] = None,
                               preferred_artists: List[str] = None,
                               mood: str = None, listening_time: str = None,
                               energy_level: float = None, danceability: float = None):
        """Actualizează preferințele utilizatorului"""
        if user_id not in self.users:
            self.register_user(user_id)
        
        if preferred_genres:
            # Adaugă genuri noi, fără duplicate
            existing_genres = set(self.users[user_id].get('preferred_genres', []))
            new_genres = [g for g in preferred_genres if g not in existing_genres]
            self.users[user_id]['preferred_genres'].extend(new_genres)
            
            # Actualizează statistici
            for genre in preferred_genres:
                self.users[user_id]['stats']['favorite_genres'][genre] = \
                    self.users[user_id]['stats']['favorite_genres'].get(genre, 0) + 1
        
        if preferred_artists:
            existing_artists = set(self.users[user_id].get('preferred_artists', []))
            new_artists = [a for a in preferred_artists if a not in existing_artists]
            self.users[user_id]['preferred_artists'].extend(new_artists)
            
            for artist in preferred_artists:
                self.users[user_id]['stats']['favorite_artists'][artist] = \
                    self.users[user_id]['stats']['favorite_artists'].get(artist, 0) + 1
        
        if mood:
            if mood not in self.users[user_id].get('mood_preferences', []):
                self.users[user_id].setdefault('mood_preferences', []).append({
                    'mood': mood,
                    'timestamp': datetime.now().isoformat()
                })
        
        if listening_time:
            self.users[user_id]['listening_time_preference'] = listening_time
        
        if energy_level is not None:
            self.users[user_id]['energy_level'] = energy_level
        
        if danceability is not None:
            self.users[user_id]['danceability'] = danceability
        
        self._save_users()
        
        # Sincronizează cu Recombee dacă este disponibil
        if self.recommendation_system:
            try:
                user_data = self.get_user_data_for_sync(user_id)
                if user_data:
                    self.recommendation_system.sync_user_to_recombee(user_data)
            except Exception as e:
                print(f"Eroare la sincronizarea preferințelor cu Recombee: {e}")
    
    def add_interaction(self, user_id: str, track_id: str, interaction_type: str,
                       metadata: Dict = None, recomm_id: str = None):
        """
        Adaugă o interacțiune (ascultare, like, skip, etc.)
        
        interaction_type: 'listen', 'like', 'skip', 'playlist_add', etc.
        recomm_id: ID-ul recomandării (dacă interacțiunea provine dintr-o recomandare)
        """
        if user_id not in self.users:
            self.register_user(user_id)
        
        interaction = {
            'track_id': track_id,
            'type': interaction_type,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {},
            'recomm_id': recomm_id  # Pentru tracking-ul succesului recomandărilor
        }
        
        self.users[user_id]['interactions'].append(interaction)
        
        # Trimite interacțiunea către Recombee
        if self.recommendation_system:
            try:
                if interaction_type == 'like':
                    self.recommendation_system.send_track_like(user_id, track_id, recomm_id)
                elif interaction_type == 'dislike':
                    self.recommendation_system.send_track_dislike(user_id, track_id, recomm_id)
                elif interaction_type == 'listen':
                    duration = metadata.get('duration', 30) if metadata else 30
                    self.recommendation_system.send_track_view(user_id, track_id, duration, recomm_id)
                elif interaction_type == 'bookmark':
                    self.recommendation_system.send_track_bookmark(user_id, track_id, recomm_id)
            except Exception as e:
                print(f"Eroare la trimiterea interacțiunii către Recombee: {e}")
        
        # Actualizează istoricul
        if interaction_type == 'listen':
            self.users[user_id]['listening_history'].append({
                'track_id': track_id,
                'timestamp': datetime.now().isoformat()
            })
            self.users[user_id]['stats']['total_listens'] += 1
        
        if interaction_type == 'like':
            if track_id not in self.users[user_id]['liked_tracks']:
                self.users[user_id]['liked_tracks'].append(track_id)
            self.users[user_id]['stats']['total_likes'] += 1
        
        self._save_users()
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Obține profilul complet al utilizatorului"""
        return self.users.get(user_id)
    
    def get_user_liked_tracks(self, user_id: str) -> List[str]:
        """Obține lista de piese apreciate de utilizator"""
        return self.users.get(user_id, {}).get('liked_tracks', [])
    
    def get_user_listening_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Obține istoricul de ascultare"""
        history = self.users.get(user_id, {}).get('listening_history', [])
        return history[-limit:]  # Ultimele N piese
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Obține statisticile utilizatorului"""
        user_data = self.users.get(user_id, {})
        stats = user_data.get('stats', {})
        
        # Add liked tracks count to stats
        stats['liked_tracks_count'] = len(user_data.get('liked_tracks', []))
        stats['disliked_tracks_count'] = len(user_data.get('disliked_tracks', []))
        
        return stats
    
    def add_liked_track(self, user_id: str, track_id: str):
        """Adaugă o piesă la lista de favorite"""
        if user_id not in self.users:
            self.register_user(user_id)
        
        if track_id not in self.users[user_id]['liked_tracks']:
            self.users[user_id]['liked_tracks'].append(track_id)
            self._save_users()
    
    def add_disliked_track(self, user_id: str, track_id: str):
        """Adaugă o piesă la lista de piese neapreciate"""
        if user_id not in self.users:
            self.register_user(user_id)
        
        if 'disliked_tracks' not in self.users[user_id]:
            self.users[user_id]['disliked_tracks'] = []
        
        if track_id not in self.users[user_id]['disliked_tracks']:
            self.users[user_id]['disliked_tracks'].append(track_id)
            self._save_users()
    
    def get_user_disliked_tracks(self, user_id: str) -> List[str]:
        """Returnează lista de piese neapreciate de utilizator"""
        return self.users.get(user_id, {}).get('disliked_tracks', [])

