import os
import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional, List, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from recombee_api_client.api_client import RecombeeClient, Region
from recombee_api_client.api_requests import (
    AddUser,
    SetUserValues,
    AddDetailView,
    AddRating,
    RecommendItemsToUser,
    RecommendItemsToItem,
)

load_dotenv()

# ---------- config ----------
DB_PATH = os.getenv("SQLITE_PATH", "./spotify_sr.db")
DATABASE_ID = os.getenv("DATABASE_ID") or os.getenv("DATABSE_ID")
PRIVATE_TOKEN = os.getenv("PRIVATE_TOKEN")
REGION_STR = os.getenv("REGION", "eu-west").strip()

REGION_MAP = {
    "eu-west": Region.EU_WEST,
    "eu_west": Region.EU_WEST,
    "us-west": Region.US_WEST,
    "us-east": Region.US_EAST,
    "ap-se": Region.AP_SE,
}

if not DATABASE_ID or not PRIVATE_TOKEN:
    raise RuntimeError("Missing DATABASE_ID and/or PRIVATE_TOKEN in .env")

recombee = RecombeeClient(
    DATABASE_ID, PRIVATE_TOKEN, region=REGION_MAP.get(REGION_STR, Region.EU_WEST)
)


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")
    return con


# ---------- models ----------
class CreateUserIn(BaseModel):
    user_id: str = Field(..., min_length=1)


class UserPreferencesIn(BaseModel):
    preferred_genres: List[str] = Field(default_factory=list)
    mood: Optional[str] = None
    preferred_energy: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    preferred_danceability: Optional[float] = Field(default=None, ge=0.0, le=1.0)


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
    count: int = Field(default=10, ge=1, le=50)


app = FastAPI(title="Spotify SR Backend (SQLite + Recombee)")


# ---------- helpers ----------
def get_track_or_404(con: sqlite3.Connection, track_id: str) -> dict:
    row = con.execute("SELECT * FROM tracks WHERE track_id=?", (track_id,)).fetchone()
    if not row:
        raise HTTPException(404, f"Track not found: {track_id}")
    return dict(row)


def build_reql_filter_from_userprefs(prefs: dict) -> Optional[str]:
    """
    Knowledge-based part:
    - if user has preferred genres, require at least one overlap with item's track_genre (set)
      using set intersection: size(A & B) > 0
    This matches Recombee ReQL examples of filtering with set intersection. :contentReference[oaicite:2]{index=2}
    """
    genres = prefs.get("preferred_genres") or []
    if genres:
        # we stored item property track_genre as a set with one element
        # and user property preferred_genres as a set
        return "size(context_user[\"preferred_genres\"] & 'track_genre') > 0"
    return None


def build_reql_booster_from_userprefs(prefs: dict) -> Optional[str]:
    """
    Soft preference boosting (still “knowledge-based”):
    - if user has preferred_energy, boost items closer in energy
    - if user has preferred_danceability, boost items closer in danceability
    Keep it simple + robust.
    """
    parts = []
    if prefs.get("preferred_energy") is not None:
        parts.append("1 / (1 + abs('energy' - context_user[\"preferred_energy\"]))")
    if prefs.get("preferred_danceability") is not None:
        parts.append(
            "1 / (1 + abs('danceability' - context_user[\"preferred_danceability\"]))"
        )
    if not parts:
        return None
    # multiply boosters
    return " * ".join(parts)


def load_user_prefs(con: sqlite3.Connection, user_id: str) -> dict:
    row = con.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    if not row:
        raise HTTPException(404, f"User not found: {user_id}")
    d = dict(row)
    d["preferred_genres"] = json.loads(d["preferred_genres"] or "[]")
    return d


# ---------- endpoints ----------
@app.post("/users")
def create_user(payload: CreateUserIn):
    con = db()
    try:
        now = utcnow_iso()
        con.execute(
            "INSERT INTO users(user_id, created_at, preferred_genres, mood, preferred_energy, preferred_danceability) VALUES(?,?,?,?,?,?)",
            (payload.user_id, now, "[]", None, None, None),
        )
        con.commit()

        # Create user in Recombee too (or you can rely on cascade_create from events)
        recombee.send(AddUser(payload.user_id))

        return {"user_id": payload.user_id, "created_at": now}
    finally:
        con.close()


@app.get("/users/{user_id}")
def get_user(user_id: str):
    con = db()
    try:
        prefs = load_user_prefs(con, user_id)
        # Return User Info directly from SQLite
        return {
            "user_id": prefs["user_id"],
            "created_at": prefs["created_at"],
            "preferred_genres": prefs["preferred_genres"],
            "mood": prefs["mood"],
            "preferred_energy": prefs["preferred_energy"],
            "preferred_danceability": prefs["preferred_danceability"],
        }
    finally:
        con.close()


@app.put("/users/{user_id}/preferences")
def set_preferences(user_id: str, payload: UserPreferencesIn):
    con = db()
    try:
        # ensure user exists
        _ = load_user_prefs(con, user_id)

        con.execute(
            """
            UPDATE users
            SET preferred_genres=?, mood=?, preferred_energy=?, preferred_danceability=?
            WHERE user_id=?
            """,
            (
                json.dumps(payload.preferred_genres),
                payload.mood,
                payload.preferred_energy,
                payload.preferred_danceability,
                user_id,
            ),
        )
        con.commit()

        # push to Recombee user properties
        recombee.send(
            SetUserValues(
                user_id,
                {
                    "preferred_genres": payload.preferred_genres,
                    "mood": payload.mood,
                    "preferred_energy": payload.preferred_energy,
                    "preferred_danceability": payload.preferred_danceability,
                },
                cascade_create=True,
            )
        )

        return {"ok": True}
    finally:
        con.close()


@app.get("/tracks/{track_id}")
def get_track(track_id: str):
    con = db()
    try:
        return get_track_or_404(con, track_id)
    finally:
        con.close()


@app.post("/events/view")
def event_view(payload: ViewEventIn):
    con = db()
    try:
        # validate
        _ = load_user_prefs(con, payload.user_id)
        _ = get_track_or_404(con, payload.track_id)

        con.execute(
            """
            INSERT INTO interactions(user_id, track_id, event_type, rating, duration_ms, recomm_id, created_at)
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                payload.user_id,
                payload.track_id,
                "view",
                None,
                payload.duration_ms,
                payload.recomm_id,
                utcnow_iso(),
            ),
        )
        con.commit()

        # Recombee interaction
        recombee.send(
            AddDetailView(payload.user_id, payload.track_id, cascade_create=True)
        )

        return {"ok": True}
    finally:
        con.close()


@app.post("/events/rating")
def event_rating(payload: RatingEventIn):
    con = db()
    try:
        _ = load_user_prefs(con, payload.user_id)
        _ = get_track_or_404(con, payload.track_id)

        con.execute(
            """
            INSERT INTO interactions(user_id, track_id, event_type, rating, duration_ms, recomm_id, created_at)
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                payload.user_id,
                payload.track_id,
                "rating",
                float(payload.rating),
                None,
                payload.recomm_id,
                utcnow_iso(),
            ),
        )
        con.commit()

        # Recombee rating: like=+1, dislike=-1
        recombee.send(
            AddRating(
                payload.user_id,
                payload.track_id,
                float(payload.rating),
                cascade_create=True,
            )
        )

        return {"ok": True}
    finally:
        con.close()


@app.post("/recommendations/for-you")
def recommend_for_you(payload: RecommendForYouIn):
    con = db()
    try:
        prefs = load_user_prefs(con, payload.user_id)

        reql_filter = build_reql_filter_from_userprefs(prefs)
        booster = build_reql_booster_from_userprefs(prefs)

        # Knowledge-based + learning-from-interactions happens in Recombee
        # ReQL filter/booster are standard mechanism in Recombee. :contentReference[oaicite:3]{index=3}
        resp = recombee.send(
            RecommendItemsToUser(
                payload.user_id, payload.count, filter=reql_filter, booster=booster
            )
        )

        item_ids = resp.get("recomms", [])
        recomm_id = resp.get("recommId")

        # enrich from SQLite for frontend
        tracks = []
        for r in item_ids:
            # recomms can be list of dicts: {"id": "..."} depending on SDK;
            # handle both
            tid = r["id"] if isinstance(r, dict) and "id" in r else r
            tracks.append(get_track_or_404(con, tid))

        return {"recomm_id": recomm_id, "tracks": tracks}
    finally:
        con.close()


@app.get("/recommendations/similar/{track_id}")
def recommend_similar(track_id: str, user_id: str, count: int = 10):
    con = db()
    try:
        _ = load_user_prefs(con, user_id)
        _ = get_track_or_404(con, track_id)

        resp = recombee.send(RecommendItemsToItem(track_id, user_id, count))

        item_ids = resp.get("recomms", [])
        recomm_id = resp.get("recommId")

        tracks = []
        for r in item_ids:
            tid = r["id"] if isinstance(r, dict) and "id" in r else r
            tracks.append(get_track_or_404(con, tid))

        return {"recomm_id": recomm_id, "tracks": tracks}
    finally:
        con.close()
