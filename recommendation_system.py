"""
Sistem de Recomandare Muzică - Spotify Dataset
Integrare cu Recombee pentru Content-Based și Knowledge-Based Filtering
"""

import csv
import json
import math
from typing import List, Dict, Optional
from dataclasses import dataclass
from collections import defaultdict

# Pentru integrarea cu Recombee (necesită instalarea: pip install recombee)
try:
    from recombee_api_client.api_client import RecombeeClient
    from recombee_api_client.api_requests import AddItem, SetItemValues, AddUser, SetUserValues, RecommendItemsToUser
    RECOMBEE_AVAILABLE = True
except ImportError:
    RECOMBEE_AVAILABLE = False
    print("Recombee nu este instalat. Folosim implementare locală.")


@dataclass
class Track:
    """Reprezentare a unei piese muzicale"""
    track_id: str
    artists: str
    album_name: str
    track_name: str
    popularity: int
    duration_ms: int
    explicit: bool
    danceability: float
    energy: float
    key: int
    loudness: float
    mode: int
    speechiness: float
    acousticness: float
    instrumentalness: float
    liveness: float
    valence: float
    tempo: float
    time_signature: int
    track_genre: str


@dataclass
class UserProfile:
    """Profilul utilizatorului cu preferințe"""
    user_id: str
    preferred_genres: List[str]
    mood: str  # 'happy', 'sad', 'energetic', 'calm', etc.
    listening_time_preference: str  # 'short', 'medium', 'long'
    preferred_energy_level: float  # 0.0 - 1.0
    preferred_danceability: float  # 0.0 - 1.0


class SpotifyRecommendationSystem:
    """Sistem de recomandare hibrid: Content-Based + Knowledge-Based"""
    
    def __init__(self, csv_file: str, recombee_db: Optional[str] = None, 
                 recombee_private_token: Optional[str] = None,
                 recombee_public_token: Optional[str] = None,
                 recombee_region: Optional[str] = None):
        """
        Inițializează sistemul de recomandare
        
        Args:
            csv_file: Path către fișierul CSV cu datele Spotify
            recombee_db: Numele bazei de date Recombee (opțional)
            recombee_private_token: Token privat Recombee (opțional, pentru server-side)
            recombee_public_token: Token public Recombee (opțional, pentru client-side)
            recombee_region: Regiunea Recombee (opțional, ex: 'eu-west')
        """
        self.tracks: Dict[str, Track] = {}
        self.users: Dict[str, UserProfile] = {}
        self.genre_tracks: defaultdict = defaultdict(list)
        self.csv_file = csv_file
        
        # Inițializare Recombee (dacă este disponibil)
        self.recombee_client = None
        if RECOMBEE_AVAILABLE and recombee_db:
            try:
                from recombee_api_client.api_client import Region
                
                # Pentru operațiuni server-side, folosim private token
                # Public token este doar pentru citire/recomandări client-side
                # Private token poate face toate operațiunile
                token = recombee_private_token or recombee_public_token
                
                if token:
                    # Convertim regiunea string în enum Region dacă este necesar
                    region_enum = None
                    if recombee_region:
                        region_upper = recombee_region.upper().replace('-', '_')
                        if hasattr(Region, region_upper):
                            region_enum = getattr(Region, region_upper)
                        else:
                            # Încearcă să găsească regiunea similară
                            for attr in dir(Region):
                                if not attr.startswith('_') and region_upper in attr.upper():
                                    region_enum = getattr(Region, attr)
                                    break
                    
                    # Inițializează clientul
                    if region_enum:
                        self.recombee_client = RecombeeClient(
                            database_id=recombee_db,
                            token=token,
                            region=region_enum
                        )
                    else:
                        self.recombee_client = RecombeeClient(
                            database_id=recombee_db,
                            token=token
                        )
                    print(f"✓ Conectat la Recombee: {recombee_db} (region: {recombee_region or 'default'})")
            except Exception as e:
                print(f"Eroare la conectarea la Recombee: {e}")
                import traceback
                traceback.print_exc()
        
        self._load_dataset()
    
    def _load_dataset(self):
        """Încarcă dataset-ul din CSV"""
        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                track = Track(
                    track_id=row['track_id'],
                    artists=row['artists'],
                    album_name=row['album_name'],
                    track_name=row['track_name'],
                    popularity=int(row['popularity']),
                    duration_ms=int(row['duration_ms']),
                    explicit=row['explicit'].lower() == 'true',
                    danceability=float(row['danceability']),
                    energy=float(row['energy']),
                    key=int(row['key']),
                    loudness=float(row['loudness']),
                    mode=int(row['mode']),
                    speechiness=float(row['speechiness']),
                    acousticness=float(row['acousticness']),
                    instrumentalness=float(row['instrumentalness']),
                    liveness=float(row['liveness']),
                    valence=float(row['valence']),
                    tempo=float(row['tempo']),
                    time_signature=int(row['time_signature']),
                    track_genre=row['track_genre']
                )
                self.tracks[track.track_id] = track
                self.genre_tracks[track.track_genre].append(track.track_id)
    
    def create_user_profile(self, user_id: str, preferred_genres: List[str],
                          mood: str, listening_time: str,
                          energy_level: float = 0.5, danceability: float = 0.5):
        """
        Creează un profil de utilizator
        
        Args:
            user_id: ID-ul utilizatorului
            preferred_genres: Lista de genuri preferate
            mood: Dispoziția utilizatorului
            listening_time: Preferința pentru durata pieselor
            energy_level: Nivelul de energie preferat (0.0-1.0)
            danceability: Nivelul de dansabilitate preferat (0.0-1.0)
        """
        user = UserProfile(
            user_id=user_id,
            preferred_genres=preferred_genres,
            mood=mood,
            listening_time_preference=listening_time,
            preferred_energy_level=energy_level,
            preferred_danceability=danceability
        )
        self.users[user_id] = user
        
        # Adaugă utilizatorul în Recombee (dacă este disponibil)
        if self.recombee_client:
            try:
                self.recombee_client.send(AddUser(user_id))
                self.recombee_client.send(SetUserValues(
                    user_id,
                    {
                        'preferred_genres': json.dumps(preferred_genres),
                        'mood': mood,
                        'listening_time': listening_time,
                        'energy_level': energy_level,
                        'danceability': danceability
                    }
                ))
            except Exception as e:
                print(f"Eroare la adăugarea utilizatorului în Recombee: {e}")
    
    def _calculate_acoustic_similarity(self, track1: Track, track2: Track) -> float:
        """
        Calculează similaritatea acustică între două piese folosind Cosine Similarity
        Folosește TOATE caracteristicile acustice disponibile pentru o potrivire mai precisă
        
        Formula Cosine Similarity:
        cosine_similarity = (A · B) / (||A|| * ||B||)
        unde A și B sunt vectorii de caracteristici ale celor două piese
        """
        # Extragem toate caracteristicile acustice și le normalizăm
        # Normalizăm tempo și loudness pentru a fi în intervalul [0, 1]
        features1 = [
            track1.energy,                    # [0, 1]
            track1.danceability,              # [0, 1]
            track1.valence,                   # [0, 1]
            track1.speechiness,               # [0, 1]
            track1.acousticness,              # [0, 1]
            track1.instrumentalness,          # [0, 1]
            track1.liveness,                  # [0, 1]
            (track1.tempo / 200.0),          # Normalizare tempo [0, 1] (max ~200 BPM)
            ((track1.loudness + 60) / 60.0), # Normalizare loudness [-60, 0] -> [0, 1]
            (track1.key / 11.0),             # Normalizare key [0, 11] -> [0, 1]
            (track1.mode / 1.0),             # Mode [0, 1]
            (track1.time_signature / 5.0),   # Normalizare time_signature [3, 5] -> [0, 1]
            (track1.popularity / 100.0)       # Normalizare popularity [0, 100] -> [0, 1]
        ]
        
        features2 = [
            track2.energy,
            track2.danceability,
            track2.valence,
            track2.speechiness,
            track2.acousticness,
            track2.instrumentalness,
            track2.liveness,
            (track2.tempo / 200.0),
            ((track2.loudness + 60) / 60.0),
            (track2.key / 11.0),
            (track2.mode / 1.0),
            (track2.time_signature / 5.0),
            (track2.popularity / 100.0)
        ]
        
        # Cosine Similarity: cos(θ) = (A · B) / (||A|| * ||B||)
        # A · B = dot product (suma produselor elementelor corespunzătoare)
        dot_product = sum(a * b for a, b in zip(features1, features2))
        
        # ||A|| = magnitudinea vectorului A (norma euclidiană)
        magnitude1 = math.sqrt(sum(a * a for a in features1))
        magnitude2 = math.sqrt(sum(b * b for b in features2))
        
        # Evită împărțirea la zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        # Cosine similarity returnează o valoare între -1 și 1
        # Pentru caracteristici muzicale, rezultatul este de obicei între 0 și 1
        cosine_similarity = dot_product / (magnitude1 * magnitude2)
        
        # Asigurăm că rezultatul este în intervalul [0, 1]
        # (în practică, pentru caracteristici muzicale pozitive, va fi întotdeauna pozitiv)
        return max(0.0, cosine_similarity)
    
    def content_based_recommend(self, track_id: str, num_recommendations: int = 10) -> List[Dict]:
        """
        Recomandări bazate pe conținut (Content-Based Filtering)
        Găsește piese similare din punct de vedere acustic
        
        Pseudocod:
        FUNCTION content_based_recommend(track_id, num_recommendations):
            target_track = tracks[track_id]
            similarities = []
            
            FOR EACH track IN tracks:
                IF track.id != track_id:
                    similarity = calculate_acoustic_similarity(target_track, track)
                    similarities.append((track, similarity))
            
            SORT similarities BY similarity DESCENDING
            RETURN top num_recommendations tracks
        """
        if track_id not in self.tracks:
            return []
        
        target_track = self.tracks[track_id]
        similarities = []
        
        for other_id, other_track in self.tracks.items():
            if other_id != track_id:
                similarity = self._calculate_acoustic_similarity(target_track, other_track)
                similarities.append({
                    'track': other_track,
                    'similarity': similarity
                })
        
        # Sortează după similaritate
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        recommendations = []
        for item in similarities[:num_recommendations]:
            track = item['track']
            recommendations.append({
                'track_id': track.track_id,
                'track_name': track.track_name,
                'artists': track.artists,
                'album_name': track.album_name,
                'track_genre': track.track_genre,
                'popularity': track.popularity,
                'duration_ms': track.duration_ms,
                'explicit': track.explicit,
                'danceability': track.danceability,
                'energy': track.energy,
                'key': track.key,
                'loudness': track.loudness,
                'mode': track.mode,
                'speechiness': track.speechiness,
                'acousticness': track.acousticness,
                'instrumentalness': track.instrumentalness,
                'liveness': track.liveness,
                'valence': track.valence,
                'tempo': track.tempo,
                'time_signature': track.time_signature,
                'similarity_score': item['similarity']
            })
        
        return recommendations
    
    def knowledge_based_recommend(self, user_id: str, num_recommendations: int = 10) -> List[Dict]:
        """
        Recomandări bazate pe cunoștințe (Knowledge-Based Filtering)
        Personalizează recomandările în funcție de profilul utilizatorului
        
        Pseudocod:
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
        """
        if user_id not in self.users:
            return []
        
        user = self.users[user_id]
        recommendations = []
        
        # Caută piese din genurile preferate
        # Dacă nu există genuri preferate, returnează lista goală
        if not user.preferred_genres:
            return []
        
        for genre in user.preferred_genres:
            if genre in self.genre_tracks:
                for track_id in self.genre_tracks[genre]:
                    track = self.tracks[track_id]
                    score = self._calculate_user_match_score(user, track)
                    recommendations.append({
                        'track': track,
                        'score': score,
                        'genre': genre  # Păstrează genul pentru sortare
                    })
        
        # Filtrare după mood și durată
        filtered_recommendations = []
        for item in recommendations:
            track = item['track']
            if self._matches_mood(user.mood, track) and \
               self._matches_listening_time(user.listening_time_preference, track.duration_ms):
                filtered_recommendations.append(item)
        
        # Dacă nu există recomandări după filtrare, relaxează condițiile
        if not filtered_recommendations:
            # Relaxează doar filtrarea mood (păstrează durata)
            for item in recommendations:
                track = item['track']
                if self._matches_listening_time(user.listening_time_preference, track.duration_ms):
                    filtered_recommendations.append(item)
        
        # Dacă încă nu există, folosește toate recomandările
        if not filtered_recommendations:
            filtered_recommendations = recommendations
        
        # Sortează: mai întâi după genuri preferate (prioritate), apoi după scor
        # Genurile preferate primele în listă au prioritate mai mare
        genre_priority = {genre: idx for idx, genre in enumerate(user.preferred_genres)}
        filtered_recommendations.sort(key=lambda x: (
            genre_priority.get(x.get('genre', ''), 999),  # Genuri preferate primele
            -x['score']  # Apoi după scor descrescător
        ))
        
        result = []
        for item in filtered_recommendations[:num_recommendations]:
            track = item['track']
            result.append({
                'track_id': track.track_id,
                'track_name': track.track_name,
                'artists': track.artists,
                'album_name': track.album_name,
                'track_genre': track.track_genre,
                'popularity': track.popularity,
                'duration_ms': track.duration_ms,
                'explicit': track.explicit,
                'danceability': track.danceability,
                'energy': track.energy,
                'key': track.key,
                'loudness': track.loudness,
                'mode': track.mode,
                'speechiness': track.speechiness,
                'acousticness': track.acousticness,
                'instrumentalness': track.instrumentalness,
                'liveness': track.liveness,
                'valence': track.valence,
                'tempo': track.tempo,
                'time_signature': track.time_signature,
                'match_score': item['score']
            })
        
        return result
    
    def _calculate_user_match_score(self, user: UserProfile, track: Track) -> float:
        """
        Calculează scorul de potrivire între utilizator și piesă
        Folosește Cosine Similarity pentru a calcula potrivirea bazată pe preferințe
        """
        # Vector de preferințe utilizator (normalizat)
        user_vector = [
            user.preferred_energy_level,      # [0, 1]
            user.preferred_danceability,      # [0, 1]
            0.5,                              # Valence (nu avem preferință explicită, folosim medie)
            0.5,                              # Speechiness (nu avem preferință)
            0.5,                              # Acousticness (nu avem preferință)
            0.0,                              # Instrumentalness (nu avem preferință)
            0.5,                              # Liveness (nu avem preferință)
            0.5,                              # Tempo (nu avem preferință explicită)
            0.5,                              # Loudness (nu avem preferință)
            0.5,                              # Key (nu avem preferință)
            0.5,                              # Mode (nu avem preferință)
            0.5,                              # Time signature (nu avem preferință)
            0.5                              # Popularity (nu avem preferință explicită)
        ]
        
        # Vector de caracteristici piesă (normalizat, la fel ca în _calculate_acoustic_similarity)
        track_vector = [
            track.energy,
            track.danceability,
            track.valence,
            track.speechiness,
            track.acousticness,
            track.instrumentalness,
            track.liveness,
            (track.tempo / 200.0),
            ((track.loudness + 60) / 60.0),
            (track.key / 11.0),
            (track.mode / 1.0),
            (track.time_signature / 5.0),
            (track.popularity / 100.0)
        ]
        
        # Cosine Similarity între preferințele utilizatorului și caracteristicile piesei
        dot_product = sum(a * b for a, b in zip(user_vector, track_vector))
        magnitude_user = math.sqrt(sum(a * a for a in user_vector))
        magnitude_track = math.sqrt(sum(b * b for b in track_vector))
        
        if magnitude_user == 0 or magnitude_track == 0:
            cosine_score = 0.0
        else:
            cosine_score = dot_product / (magnitude_user * magnitude_track)
        
        # Bonus pentru potrivire gen (nu poate fi exprimat în cosine similarity)
        genre_bonus = 0.0
        if track.track_genre in user.preferred_genres:
            genre_bonus = 0.3
        
        # Scor final: combină cosine similarity cu bonus-ul pentru gen
        final_score = max(0.0, cosine_score) * 0.7 + genre_bonus
        
        return min(1.0, final_score)  # Asigură că scorul este în [0, 1]
    
    def _matches_mood(self, mood: str, track: Track) -> bool:
        """Verifică dacă piesa se potrivește cu dispoziția utilizatorului"""
        mood_mapping = {
            'happy': {'min_valence': 0.6, 'min_energy': 0.5},
            'sad': {'max_valence': 0.4, 'max_energy': 0.6},
            'energetic': {'min_energy': 0.7, 'min_tempo': 120},
            'calm': {'max_energy': 0.4, 'min_acousticness': 0.5}
        }
        
        if mood not in mood_mapping:
            return True
        
        conditions = mood_mapping[mood]
        
        if 'min_valence' in conditions and track.valence < conditions['min_valence']:
            return False
        if 'max_valence' in conditions and track.valence > conditions['max_valence']:
            return False
        if 'min_energy' in conditions and track.energy < conditions['min_energy']:
            return False
        if 'max_energy' in conditions and track.energy > conditions['max_energy']:
            return False
        if 'min_tempo' in conditions and track.tempo < conditions['min_tempo']:
            return False
        if 'min_acousticness' in conditions and track.acousticness < conditions['min_acousticness']:
            return False
        
        return True
    
    def _matches_listening_time(self, preference: str, duration_ms: int) -> bool:
        """Verifică dacă durata piesei se potrivește cu preferința utilizatorului"""
        duration_minutes = duration_ms / 60000.0
        
        if preference == 'short':
            return duration_minutes <= 3.0
        elif preference == 'medium':
            return 3.0 < duration_minutes <= 5.0
        elif preference == 'long':
            return duration_minutes > 5.0
        
        return True
    
    def recombee_recommend(self, user_id: str, num_recommendations: int = 10,
                          scenario: str = 'spotify-recommendations') -> List[Dict]:
        """
        Obține recomandări folosind Recombee API
        Aceasta este metoda principală când Recombee este configurat
        
        Args:
            user_id: ID-ul utilizatorului
            num_recommendations: Numărul de recomandări
            scenario: Numele scenariului Recombee
        """
        if not self.recombee_client:
            return []
        
        try:
            from recombee_api_client.api_requests import RecommendItemsToUser, GetItemValues
            
            # Obține recomandări de la Recombee
            response = self.recombee_client.send(RecommendItemsToUser(
                user_id=user_id,
                count=num_recommendations,
                scenario=scenario,
                return_properties=True
            ))
            
            recommendations = []
            for rec in response.get('recomms', []):
                track_id = rec['id']
                
                # Obține detalii despre piesă
                if track_id in self.tracks:
                    track = self.tracks[track_id]
                    recommendations.append({
                        'track_id': track.track_id,
                        'track_name': track.track_name,
                        'artists': track.artists,
                        'album_name': track.album_name,
                        'track_genre': track.track_genre,
                        'popularity': track.popularity,
                        'duration_ms': track.duration_ms,
                        'explicit': track.explicit,
                        'danceability': track.danceability,
                        'energy': track.energy,
                        'key': track.key,
                        'loudness': track.loudness,
                        'mode': track.mode,
                        'speechiness': track.speechiness,
                        'acousticness': track.acousticness,
                        'instrumentalness': track.instrumentalness,
                        'liveness': track.liveness,
                        'valence': track.valence,
                        'tempo': track.tempo,
                        'time_signature': track.time_signature,
                        'source': 'recombee',
                        'final_score': rec.get('values', {}).get('rating', 0.5)
                    })
                else:
                    # Dacă nu există în cache local, încarcă din Recombee
                    try:
                        item_values = self.recombee_client.send(GetItemValues(track_id))
                        recommendations.append({
                            'track_id': track_id,
                            'track_name': item_values.get('track_name', 'Unknown'),
                            'artists': item_values.get('artists', 'Unknown'),
                            'album_name': item_values.get('album_name', 'Unknown'),
                            'track_genre': item_values.get('genre', 'unknown'),
                            'popularity': item_values.get('popularity', 0),
                            'duration_ms': item_values.get('duration_ms', 0),
                            'explicit': item_values.get('explicit', False),
                            'danceability': item_values.get('danceability', 0.5),
                            'energy': item_values.get('energy', 0.5),
                            'key': item_values.get('key', 0),
                            'loudness': item_values.get('loudness', 0.0),
                            'mode': item_values.get('mode', 0),
                            'speechiness': item_values.get('speechiness', 0.0),
                            'acousticness': item_values.get('acousticness', 0.0),
                            'instrumentalness': item_values.get('instrumentalness', 0.0),
                            'liveness': item_values.get('liveness', 0.0),
                            'valence': item_values.get('valence', 0.0),
                            'tempo': item_values.get('tempo', 120.0),
                            'time_signature': item_values.get('time_signature', 4),
                            'source': 'recombee',
                            'final_score': rec.get('values', {}).get('rating', 0.5)
                        })
                    except:
                        continue
            
            return recommendations
            
        except Exception as e:
            print(f"Eroare la obținerea recomandărilor din Recombee: {e}")
            return []
    
    def hybrid_recommend(self, user_id: str, seed_track_id: Optional[str] = None,
                        num_recommendations: int = 10, use_recombee: bool = True) -> List[Dict]:
        """
        Recomandări hibrid: combină Content-Based și Knowledge-Based
        Dacă Recombee este disponibil, îl folosește pentru recomandări
        
        Pseudocod:
        FUNCTION hybrid_recommend(user_id, seed_track_id, num_recommendations):
            IF recombee_available:
                RETURN recombee_recommend(user_id, num_recommendations)
            ELSE:
                content_recs = content_based_recommend(seed_track_id, num_recommendations * 2)
                knowledge_recs = knowledge_based_recommend(user_id, num_recommendations * 2)
                combined = merge_and_rank(content_recs, knowledge_recs)
                RETURN top num_recommendations from combined
        """
        # Dacă Recombee este disponibil și este activat, folosește-l
        if use_recombee and self.recombee_client:
            recombee_recs = self.recombee_recommend(user_id, num_recommendations)
            if recombee_recs:
                return recombee_recs
            # Fallback la metoda locală dacă Recombee nu returnează rezultate
        
        recommendations = []
        
        # Recomandări Content-Based (dacă există track seed)
        if seed_track_id and seed_track_id in self.tracks:
            content_recs = self.content_based_recommend(seed_track_id, num_recommendations * 2)
            for rec in content_recs:
                recommendations.append({
                    **rec,
                    'source': 'content-based',
                    'final_score': rec['similarity_score'] * 0.6
                })
        
        # Recomandări Knowledge-Based
        knowledge_recs = self.knowledge_based_recommend(user_id, num_recommendations * 2)
        for rec in knowledge_recs:
            recommendations.append({
                **rec,
                'source': 'knowledge-based',
                'final_score': rec['match_score'] * 0.4
            })
        
        # Elimină duplicatele și sortează
        seen_tracks = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec['track_id'] not in seen_tracks:
                seen_tracks.add(rec['track_id'])
                unique_recommendations.append(rec)
        
        unique_recommendations.sort(key=lambda x: x['final_score'], reverse=True)
        
        return unique_recommendations[:num_recommendations]
    
    def get_dataset_examples(self) -> Dict:
        """Returnează exemple specifice din dataset pentru prezentare"""
        examples = {
            'short_description_track': None,
            'long_description_track': None,
            'high_energy_track': None,
            'low_energy_track': None,
            'popular_track': None,
            'niche_track': None
        }
        
        min_duration = float('inf')
        max_duration = 0
        max_energy = 0
        min_energy = float('inf')
        max_popularity = 0
        min_popularity = float('inf')
        
        for track in self.tracks.values():
            # Cea mai scurtă piesă
            if track.duration_ms < min_duration:
                min_duration = track.duration_ms
                examples['short_description_track'] = track
            
            # Cea mai lungă piesă
            if track.duration_ms > max_duration:
                max_duration = track.duration_ms
                examples['long_description_track'] = track
            
            # Cea mai energetică piesă
            if track.energy > max_energy:
                max_energy = track.energy
                examples['high_energy_track'] = track
            
            # Cea mai puțin energetică piesă
            if track.energy < min_energy:
                min_energy = track.energy
                examples['low_energy_track'] = track
            
            # Cea mai populară piesă
            if track.popularity > max_popularity:
                max_popularity = track.popularity
                examples['popular_track'] = track
            
            # Piesă de nișă (popularitate mică)
            if track.popularity < min_popularity:
                min_popularity = track.popularity
                examples['niche_track'] = track
        
        return examples
    
    def solve_long_tail_problem(self, recommendations: List[Dict], 
                               diversity_weight: float = 0.3) -> List[Dict]:
        """
        Rezolvă problema long tail prin diversificare
        
        Strategie:
        1. Include piese din genuri diverse
        2. Include piese cu popularitate variabilă
        3. Balansează între popularitate și diversitate
        """
        if not recommendations:
            return []
        
        # Grupează după gen
        genre_groups = defaultdict(list)
        for rec in recommendations:
            genre = rec.get('track_genre') or rec.get('genre', 'unknown')
            genre_groups[genre].append(rec)
        
        # Diversifică: ia câte o piesă din fiecare gen
        diversified = []
        used_tracks = set()
        
        # Runde de diversificare
        max_rounds = max(len(group) for group in genre_groups.values())
        for round_num in range(max_rounds):
            for genre, tracks in genre_groups.items():
                if round_num < len(tracks):
                    track = tracks[round_num]
                    if track['track_id'] not in used_tracks:
                        diversified.append(track)
                        used_tracks.add(track['track_id'])
        
        # Completează cu restul dacă nu sunt suficiente
        for rec in recommendations:
            if rec['track_id'] not in used_tracks and len(diversified) < len(recommendations):
                diversified.append(rec)
                used_tracks.add(rec['track_id'])
        
        return diversified[:len(recommendations)]


# Exemplu de utilizare
if __name__ == "__main__":
    # Inițializare sistem
    system = SpotifyRecommendationSystem('spotify_dataset.csv')
    
    # Creează profil utilizator
    system.create_user_profile(
        user_id='user_001',
        preferred_genres=['pop', 'rock', 'electronic'],
        mood='energetic',
        listening_time='medium',
        energy_level=0.7,
        danceability=0.6
    )
    
    # Obține recomandări
    recommendations = system.hybrid_recommend('user_001', num_recommendations=10)
    
    print("Recomandări pentru utilizator:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['track_name']} - {rec['artists']} ({rec['genre']})")
        print(f"   Scor: {rec['final_score']:.3f}, Sursă: {rec['source']}")

