from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from recombee_api_client.api_requests import AddDetailView, AddRating
from ..db import get_db
from ..recombee_client import client as recombee
from ..schemas import ViewEventIn, RatingEventIn
from ..services.user_analytics import (
    update_user_stats_and_taste,
    sync_user_derived_to_recombee,
)
from fastapi import Depends
from ..deps import get_current_user_id

router = APIRouter(prefix="/events", tags=["events"])


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_user_and_track(con, user_id: str, track_id: str):
    u = con.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone()
    if not u:
        raise HTTPException(404, "User not found")
    t = con.execute("SELECT 1 FROM tracks WHERE track_id=?", (track_id,)).fetchone()
    if not t:
        raise HTTPException(404, "Track not found")


@router.post("/view")
def view_event(
    payload: ViewEventIn, current_user_id: str = Depends(get_current_user_id)
):
    if payload.user_id != current_user_id:
        raise HTTPException(403, "Forbidden")

    duration_ms = payload.duration_ms if payload.duration_ms is not None else 0

    with get_db() as con:
        ensure_user_and_track(con, payload.user_id, payload.track_id)

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
                duration_ms,
                payload.recomm_id,
                utcnow_iso(),
            ),
        )

        # update stats/taste AFTER storing the interaction
        update_user_stats_and_taste(con, payload.user_id)
        con.commit()

        # sync derived values to recombee (avg_listen_* and taste_*)
        sync_user_derived_to_recombee(con, payload.user_id)

    # send to Recombee: duration is in SECONDS for DetailView :contentReference[oaicite:1]{index=1}
    recombee.send(
        AddDetailView(
            payload.user_id,
            payload.track_id,
            duration=int(duration_ms / 1000),
            recomm_id=payload.recomm_id,
            cascade_create=True,
        )
    )

    return {"ok": True}


@router.post("/rating")
def rating_event(
    payload: RatingEventIn, current_user_id: str = Depends(get_current_user_id)
):
    if payload.user_id != current_user_id:
        raise HTTPException(403, "Forbidden")

    with get_db() as con:
        ensure_user_and_track(con, payload.user_id, payload.track_id)

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

        # rating can change taste too (because taste is based on likes)
        update_user_stats_and_taste(con, payload.user_id)
        con.commit()
        sync_user_derived_to_recombee(con, payload.user_id)

    recombee.send(
        AddRating(
            payload.user_id,
            payload.track_id,
            float(payload.rating),
            recomm_id=payload.recomm_id,
            cascade_create=True,
        )
    )
    return {"ok": True}
