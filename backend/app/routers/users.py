import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query

from recombee_api_client.api_requests import AddUser, SetUserValues
from ..db import get_db
from ..recombee_client import client as recombee
from ..schemas import CreateUserIn, UserPreferencesIn

from fastapi import Depends
from ..deps import get_current_user_id


router = APIRouter(prefix="/users", tags=["users"])


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("")
def create_user(payload: CreateUserIn):
    with get_db() as con:
        now = utcnow_iso()
        try:
            # NOTE: requires migration that added the new columns
            con.execute(
                """
                INSERT INTO users(
                  user_id, created_at,
                  preferred_genres, mood,
                  preferred_energy, preferred_danceability,
                  preferred_acousticness, preferred_instrumentalness,
                  preferred_valence, preferred_speechiness,
                  preferred_liveness, preferred_tempo
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    payload.user_id,
                    now,
                    "[]",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            )

            # init derived tables too (requires migration)
            con.execute(
                """
                INSERT OR IGNORE INTO user_stats(
                  user_id,total_views,total_listen_seconds,avg_listen_seconds,avg_listen_ratio,updated_at
                ) VALUES (?,?,?,?,?,?)
                """,
                (payload.user_id, 0, 0.0, 0.0, 0.5, now),
            )
            con.execute(
                "INSERT OR IGNORE INTO user_taste(user_id, updated_at) VALUES(?,?)",
                (payload.user_id, now),
            )

            con.commit()
        except Exception as e:
            raise HTTPException(400, f"Could not create user: {e}")

    # create in Recombee
    recombee.send(AddUser(payload.user_id))

    # also set safe defaults so ReQL doesn't see null avg_listen_ratio
    recombee.send(
        SetUserValues(
            payload.user_id,
            {
                "preferred_genres": [],
                "mood": None,
                "avg_listen_seconds": 0.0,
                "avg_listen_ratio": 0.5,
            },
            cascade_create=True,
        )
    )

    return {"user_id": payload.user_id, "created_at": now}


@router.get("/{user_id}")
def get_user(user_id: str, current_user_id: str = Depends(get_current_user_id)):
    if user_id != current_user_id:
        raise HTTPException(403, "Forbidden")

    with get_db() as con:
        row = con.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(404, "User not found")

        d = dict(row)
        d["preferred_genres"] = json.loads(d.get("preferred_genres") or "[]")

        # attach derived info if present
        stats = con.execute(
            "SELECT avg_listen_seconds, avg_listen_ratio FROM user_stats WHERE user_id=?",
            (user_id,),
        ).fetchone()
        if stats:
            sd = dict(stats)
            d["avg_listen_seconds"] = sd.get("avg_listen_seconds")
            d["avg_listen_ratio"] = sd.get("avg_listen_ratio")

        taste = con.execute(
            """
            SELECT taste_energy, taste_danceability, taste_acousticness, taste_instrumentalness,
                   taste_valence, taste_speechiness, taste_liveness, taste_tempo
            FROM user_taste WHERE user_id=?
            """,
            (user_id,),
        ).fetchone()
        if taste:
            d.update(dict(taste))

        return d


@router.put("/{user_id}/preferences")
def set_preferences(
    user_id: str,
    payload: UserPreferencesIn,
    current_user_id: str = Depends(get_current_user_id),
):
    if user_id != current_user_id:
        raise HTTPException(403, "Forbidden")

    with get_db() as con:
        row = con.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(404, "User not found")

        con.execute(
            """
            UPDATE users
            SET preferred_genres=?,
                mood=?,
                preferred_energy=?,
                preferred_danceability=?,
                preferred_acousticness=?,
                preferred_instrumentalness=?,
                preferred_valence=?,
                preferred_speechiness=?,
                preferred_liveness=?,
                preferred_tempo=?
            WHERE user_id=?
            """,
            (
                json.dumps(payload.preferred_genres),
                payload.mood,
                payload.preferred_energy,
                payload.preferred_danceability,
                payload.preferred_acousticness,
                payload.preferred_instrumentalness,
                payload.preferred_valence,
                payload.preferred_speechiness,
                payload.preferred_liveness,
                payload.preferred_tempo,
                user_id,
            ),
        )
        con.commit()

    # push to Recombee user properties (explicit prefs)
    recombee.send(
        SetUserValues(
            user_id,
            {
                "preferred_genres": payload.preferred_genres,
                "mood": payload.mood,
                "preferred_energy": payload.preferred_energy,
                "preferred_danceability": payload.preferred_danceability,
                "preferred_acousticness": payload.preferred_acousticness,
                "preferred_instrumentalness": payload.preferred_instrumentalness,
                "preferred_valence": payload.preferred_valence,
                "preferred_speechiness": payload.preferred_speechiness,
                "preferred_liveness": payload.preferred_liveness,
                "preferred_tempo": payload.preferred_tempo,
            },
            cascade_create=True,
        )
    )
    return {"ok": True}


@router.get("/{user_id}/interactions")
def get_user_interactions(
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Returns the user's implicit feedback stored in SQLite:
    - views (with duration_ms)
    - ratings (like/dislike)
    """
    if user_id != current_user_id:
        raise HTTPException(403, "Forbidden")
    with get_db() as con:
        row = con.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(404, "User not found")

        rows = con.execute(
            """
            SELECT
              i.id, i.event_type, i.rating, i.duration_ms, i.recomm_id, i.created_at,
              t.track_id, t.track_name, t.artists, t.album_name, t.track_genre
            FROM interactions i
            JOIN tracks t ON t.track_id = i.track_id
            WHERE i.user_id = ?
            ORDER BY i.created_at DESC
            LIMIT ? OFFSET ?;
            """,
            (user_id, limit, offset),
        ).fetchall()

        out = []
        for r in rows:
            d = dict(r)
            out.append(
                {
                    "id": d["id"],
                    "event_type": d["event_type"],
                    "rating": d["rating"],
                    "duration_ms": d["duration_ms"],
                    "recomm_id": d["recomm_id"],
                    "created_at": d["created_at"],
                    "track": {
                        "track_id": d["track_id"],
                        "track_name": d["track_name"],
                        "artists": d["artists"],
                        "album_name": d["album_name"],
                        "track_genre": d["track_genre"],
                    },
                }
            )

        return {"user_id": user_id, "count": len(out), "interactions": out}
