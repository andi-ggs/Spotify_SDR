from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class CreateUserIn(BaseModel):
    user_id: str = Field(..., min_length=1)


class UserPreferencesIn(BaseModel):
    preferred_genres: List[str] = Field(default_factory=list)
    mood: Optional[str] = None
    preferred_energy: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    preferred_danceability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    preferred_acousticness: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    preferred_instrumentalness: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    preferred_valence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    preferred_speechiness: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    preferred_liveness: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    preferred_tempo: Optional[float] = (
        None  # tempo isn’t 0..1; leave unbounded or set ge=0
    )


class ViewEventIn(BaseModel):
    user_id: str
    track_id: str
    duration_ms: Optional[int] = None
    recomm_id: Optional[str] = None


class RatingEventIn(BaseModel):
    user_id: str
    track_id: str
    rating: Literal[-1, 1]  # dislike=-1, like=+1
    recomm_id: Optional[str] = None


class RecommendForYouIn(BaseModel):
    user_id: str
    count: int = Field(default=5, ge=1, le=50)
