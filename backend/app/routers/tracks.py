from fastapi import APIRouter, HTTPException, Query
from ..db import get_db

router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.get("")
def list_tracks(
    q: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    with get_db() as con:
        if q:
            rows = con.execute(
                """
                SELECT * FROM tracks
                WHERE track_name LIKE ? OR artists LIKE ? OR album_name LIKE ?
                ORDER BY popularity DESC
                LIMIT ? OFFSET ?;
                """,
                (f"%{q}%", f"%{q}%", f"%{q}%", limit, offset),
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT * FROM tracks
                ORDER BY popularity DESC
                LIMIT ? OFFSET ?;
                """,
                (limit, offset),
            ).fetchall()

        return {
            "items": [dict(r) for r in rows],
            "limit": limit,
            "offset": offset,
            "q": q,
        }


@router.get("/{track_id}")
def get_track(track_id: str):
    with get_db() as con:
        row = con.execute(
            "SELECT * FROM tracks WHERE track_id=?", (track_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Track not found")
        return dict(row)
