from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from recombee_api_client.api_requests import AddUser, SetUserValues
from ..db import get_db
from ..recombee_client import client as recombee
from ..security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RegisterIn(BaseModel):
    user_id: str = Field(..., min_length=1)
    password: str = Field(..., min_length=4)


class LoginIn(BaseModel):
    user_id: str = Field(..., min_length=1)
    password: str = Field(..., min_length=4)


@router.post("/register")
def register(payload: RegisterIn):
    with get_db() as con:
        exists = con.execute(
            "SELECT 1 FROM users WHERE user_id=?", (payload.user_id,)
        ).fetchone()
        if exists:
            raise HTTPException(400, "User already exists")

        now = utcnow_iso()
        pw_hash = hash_password(payload.password)

        # requires users table with the extra columns you already added in v2 + password_hash migration
        con.execute(
            """
            INSERT INTO users(
              user_id, created_at,
              preferred_genres, mood,
              preferred_energy, preferred_danceability,
              preferred_acousticness, preferred_instrumentalness,
              preferred_valence, preferred_speechiness,
              preferred_liveness, preferred_tempo,
              password_hash
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
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
                pw_hash,
            ),
        )

        # init derived tables (if you created them)
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

    # Create user in Recombee
    recombee.send(AddUser(payload.user_id))
    # Safe defaults for ReQL
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

    token = create_access_token(payload.user_id)
    return {"user_id": payload.user_id, "access_token": token, "token_type": "bearer"}


@router.post("/login")
def login(payload: LoginIn):
    with get_db() as con:
        row = con.execute(
            "SELECT user_id, password_hash FROM users WHERE user_id=?",
            (payload.user_id,),
        ).fetchone()
        if not row:
            raise HTTPException(401, "Invalid credentials")

        password_hash = row["password_hash"]
        if not password_hash or not verify_password(payload.password, password_hash):
            raise HTTPException(401, "Invalid credentials")

    token = create_access_token(payload.user_id)
    return {"user_id": payload.user_id, "access_token": token, "token_type": "bearer"}
