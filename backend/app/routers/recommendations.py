import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from recombee_api_client.api_requests import (
    RecommendItemsToUser,
    RecommendItemsToItem,
    SetUserValues,
)

from ..db import get_db
from ..recombee_client import client as recombee
from ..schemas import RecommendForYouIn
from ..services.recommender import (
    load_user_prefs,
    get_track_or_none,
    build_reql_filter,
    build_reql_booster,
)
from ..deps import get_current_user_id

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _enrich_tracks(con, recomms):
    tracks = []
    for r in recomms:
        tid = r["id"] if isinstance(r, dict) and "id" in r else r
        t = get_track_or_none(con, tid)
        if t:
            tracks.append(t)
    return tracks


def _maybe_log_recs(
    con,
    user_id: str,
    rec_type: str,
    item_ids: list[str],
    recomm_id: str | None,
    source_track_id: str | None = None,
):
    exists = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='recommendation_logs'"
    ).fetchone()
    if not exists:
        return

    con.execute(
        """
        INSERT INTO recommendation_logs(user_id, rec_type, source_track_id, recomm_id, item_ids, created_at)
        VALUES(?,?,?,?,?,?)
        """,
        (
            user_id,
            rec_type,
            source_track_id,
            recomm_id,
            json.dumps(item_ids),
            utcnow_iso(),
        ),
    )
    con.commit()


def get_rated_track_ids(con, user_id: str, limit: int = 500) -> list[str]:
    """
    Returns track_ids the user has rated (likes OR dislikes).
    We exclude these from recommendations so we don't recommend items the user already judged.
    """
    rows = con.execute(
        """
        SELECT track_id
        FROM interactions
        WHERE user_id=? AND event_type='rating'
        ORDER BY created_at DESC
        LIMIT ?;
        """,
        (user_id, limit),
    ).fetchall()
    return [r["track_id"] for r in rows]


@router.post("/knowledge-only")
def recommend_knowledge_only(
    payload: RecommendForYouIn, current_user_id: str = Depends(get_current_user_id)
):
    """
    Knowledge-only (cold-start):
    Uses a special Recombee user id: cold::<real_user_id>
    Copies explicit prefs + safe defaults for avg_listen_* so booster won't hit nulls.
    ALSO excludes rated tracks (likes/dislikes) from the *real* user.
    """
    if payload.user_id != current_user_id:
        raise HTTPException(403, "Forbidden")

    with get_db() as con:
        try:
            prefs = load_user_prefs(con, payload.user_id)
        except KeyError:
            raise HTTPException(404, "User not found")

        # Exclude items user already rated (like/dislike)
        exclude_ids = get_rated_track_ids(con, payload.user_id, limit=500)

        cold_user_id = f"cold::{payload.user_id}"

        recombee.send(
            SetUserValues(
                cold_user_id,
                {
                    "preferred_genres": prefs.get("preferred_genres") or [],
                    "mood": prefs.get("mood"),
                    "preferred_energy": prefs.get("preferred_energy"),
                    "preferred_danceability": prefs.get("preferred_danceability"),
                    "preferred_acousticness": prefs.get("preferred_acousticness"),
                    "preferred_instrumentalness": prefs.get(
                        "preferred_instrumentalness"
                    ),
                    "preferred_valence": prefs.get("preferred_valence"),
                    "preferred_speechiness": prefs.get("preferred_speechiness"),
                    "preferred_liveness": prefs.get("preferred_liveness"),
                    "preferred_tempo": prefs.get("preferred_tempo"),
                    "avg_listen_seconds": 0.0,
                    "avg_listen_ratio": 0.5,
                },
                cascade_create=True,
            )
        )

        reql_filter = build_reql_filter(prefs, exclude_item_ids=exclude_ids)
        booster = build_reql_booster(prefs)

        resp = recombee.send(
            RecommendItemsToUser(
                cold_user_id,
                payload.count,
                filter=reql_filter,
                booster=booster,
            )
        )

        recomms = resp.get("recomms", [])
        recomm_id = resp.get("recommId")

        item_ids = [r["id"] if isinstance(r, dict) else r for r in recomms]
        _maybe_log_recs(con, payload.user_id, "knowledge_only", item_ids, recomm_id)

        return {"recomm_id": recomm_id, "tracks": _enrich_tracks(con, recomms)}


@router.post("/for-you")
def recommend_for_you(
    payload: RecommendForYouIn, current_user_id: str = Depends(get_current_user_id)
):
    """
    Hybrid:
    - Knowledge-based filter/booster (explicit prefs + derived stats/taste)
    - + Recombee uses logged interactions for personalization
    ALSO excludes rated tracks (likes/dislikes).
    """
    if payload.user_id != current_user_id:
        raise HTTPException(403, "Forbidden")

    with get_db() as con:
        try:
            prefs = load_user_prefs(con, payload.user_id)
        except KeyError:
            raise HTTPException(404, "User not found")

        exclude_ids = get_rated_track_ids(con, payload.user_id, limit=500)

        reql_filter = build_reql_filter(prefs, exclude_item_ids=exclude_ids)
        booster = build_reql_booster(prefs)

        resp = recombee.send(
            RecommendItemsToUser(
                payload.user_id,
                payload.count,
                filter=reql_filter,
                booster=booster,
            )
        )

        recomms = resp.get("recomms", [])
        recomm_id = resp.get("recommId")

        item_ids = [r["id"] if isinstance(r, dict) else r for r in recomms]
        _maybe_log_recs(con, payload.user_id, "hybrid", item_ids, recomm_id)

        return {"recomm_id": recomm_id, "tracks": _enrich_tracks(con, recomms)}


@router.get("/similar/{track_id}")
def recommend_similar(
    track_id: str,
    user_id: str,
    count: int = 5,
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Content-based (item-to-item) recommendation for a selected track.

    NOTE:
    RecommendItemsToItem does not use our knowledge filter here.
    We still exclude already-rated items after we get the list,
    so disliked/liked items won’t show up.
    """
    if user_id != current_user_id:
        raise HTTPException(403, "Forbidden")

    with get_db() as con:
        try:
            _ = load_user_prefs(con, user_id)
        except KeyError:
            raise HTTPException(404, "User not found")

        base = get_track_or_none(con, track_id)
        if not base:
            raise HTTPException(404, "Track not found")

        exclude_ids = set(get_rated_track_ids(con, user_id, limit=1000))
        exclude_ids.add(track_id)  # don't recommend the same track back

        resp = recombee.send(RecommendItemsToItem(track_id, user_id, count))
        recomms = resp.get("recomms", [])
        recomm_id = resp.get("recommId")

        # Filter out rated items (and the source track)
        filtered = []
        for r in recomms:
            tid = r["id"] if isinstance(r, dict) else r
            if tid in exclude_ids:
                continue
            filtered.append(r)

        item_ids = [r["id"] if isinstance(r, dict) else r for r in filtered]
        _maybe_log_recs(
            con, user_id, "similar", item_ids, recomm_id, source_track_id=track_id
        )

        return {"recomm_id": recomm_id, "tracks": _enrich_tracks(con, filtered)}
