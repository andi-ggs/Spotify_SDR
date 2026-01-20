import json
import sqlite3
from typing import Optional


def load_user_prefs(con: sqlite3.Connection, user_id: str) -> dict:
    """
    Loads:
      - explicit prefs from users
      - derived stats from user_stats
      - derived taste from user_taste
    Returns a single dict used for building filters/boosters.
    """
    row = con.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    if not row:
        raise KeyError(f"User not found: {user_id}")

    d = dict(row)
    d["preferred_genres"] = json.loads(d.get("preferred_genres") or "[]")

    # derived stats (optional)
    stats = con.execute(
        """
        SELECT avg_listen_seconds, avg_listen_ratio
        FROM user_stats
        WHERE user_id=?
        """,
        (user_id,),
    ).fetchone()
    if stats:
        sd = dict(stats)
        d["avg_listen_seconds"] = sd.get("avg_listen_seconds")
        d["avg_listen_ratio"] = sd.get("avg_listen_ratio")
    else:
        # safe defaults so ReQL doesn't hit nulls
        d["avg_listen_seconds"] = 0.0
        d["avg_listen_ratio"] = 0.5

    # learned taste (optional)
    taste = con.execute(
        """
        SELECT taste_energy, taste_danceability, taste_acousticness, taste_instrumentalness,
               taste_valence, taste_speechiness, taste_liveness, taste_tempo
        FROM user_taste
        WHERE user_id=?
        """,
        (user_id,),
    ).fetchone()
    if taste:
        td = dict(taste)
        d.update(td)
    else:
        for k in [
            "taste_energy",
            "taste_danceability",
            "taste_acousticness",
            "taste_instrumentalness",
            "taste_valence",
            "taste_speechiness",
            "taste_liveness",
            "taste_tempo",
        ]:
            d[k] = None

    return d


def get_track_or_none(con: sqlite3.Connection, track_id: str) -> Optional[dict]:
    row = con.execute("SELECT * FROM tracks WHERE track_id=?", (track_id,)).fetchone()
    return dict(row) if row else None


def build_reql_filter(
    prefs: dict, exclude_item_ids: Optional[list[str]] = None
) -> Optional[str]:
    """
    ReQL FILTER (hard constraints):

    1) Knowledge-based: if preferred genres exist -> require overlap with item track_genre.
       size(context_user["preferred_genres"] & 'track_genre') > 0

    2) Optional exclusion: if exclude_item_ids is provided -> do not recommend those exact items.
       Uses special ReQL field 'itemId'.
       Example: 'itemId' not in {"id1","id2"}
    """
    parts = []

    if prefs.get("preferred_genres"):
        parts.append("size(context_user[\"preferred_genres\"] & 'track_genre') > 0")

    if exclude_item_ids:
        # Safely quote IDs for ReQL using JSON encoding
        ids = [json.dumps(str(x)) for x in exclude_item_ids if x]
        if ids:
            parts.append(f"'itemId' not in {{{', '.join(ids)}}}")

    if not parts:
        return None

    return " and ".join(f"({p})" for p in parts)


def _closeness_01(item_prop: str, user_prop: str, weight: float) -> str:
    """
    For properties in [0..1]:
      weight * max(0, 1 - abs(item - user))
    """
    return f"{weight} * max(0, 1 - abs('{item_prop}' - context_user[\"{user_prop}\"]))"


def _closeness_tempo(item_prop: str, user_prop: str, weight: float) -> str:
    """
    Tempo is not [0..1]. Normalize by /200 so the penalty isn't huge.
    """
    return (
        f"{weight} * max(0, 1 - abs('{item_prop}' - context_user[\"{user_prop}\"])/200)"
    )


def build_reql_booster(prefs: dict) -> Optional[str]:
    """
    Hybrid booster:
      - explicit prefs (knowledge-based)
      - learned taste profile (from likes weighted by listen ratio)
      - listening behavior: more skippers -> slight popularity bias

    IMPORTANT: ReQL functions return null if any argument is null.
    Therefore, we only include terms if we have a concrete value for that user prop.
    We also ensure avg_listen_ratio exists via defaults (0.5) and syncing to Recombee.
    """
    parts = []

    # --- explicit prefs (knowledge-based) ---
    if prefs.get("preferred_energy") is not None:
        parts.append(_closeness_01("energy", "preferred_energy", 0.30))
    if prefs.get("preferred_danceability") is not None:
        parts.append(_closeness_01("danceability", "preferred_danceability", 0.30))
    if prefs.get("preferred_acousticness") is not None:
        parts.append(_closeness_01("acousticness", "preferred_acousticness", 0.18))
    if prefs.get("preferred_instrumentalness") is not None:
        parts.append(
            _closeness_01("instrumentalness", "preferred_instrumentalness", 0.14)
        )
    if prefs.get("preferred_valence") is not None:
        parts.append(_closeness_01("valence", "preferred_valence", 0.14))
    if prefs.get("preferred_speechiness") is not None:
        parts.append(_closeness_01("speechiness", "preferred_speechiness", 0.10))
    if prefs.get("preferred_liveness") is not None:
        parts.append(_closeness_01("liveness", "preferred_liveness", 0.10))
    if prefs.get("preferred_tempo") is not None:
        parts.append(_closeness_tempo("tempo", "preferred_tempo", 0.10))

    # --- learned taste (derived from behavior) ---
    # We only add a taste-term if we have a non-null taste_* value in SQLite.
    # (We also sync it to Recombee, so context_user has it.)
    if prefs.get("taste_energy") is not None:
        parts.append(_closeness_01("energy", "taste_energy", 0.18))
    if prefs.get("taste_danceability") is not None:
        parts.append(_closeness_01("danceability", "taste_danceability", 0.18))
    if prefs.get("taste_acousticness") is not None:
        parts.append(_closeness_01("acousticness", "taste_acousticness", 0.10))
    if prefs.get("taste_instrumentalness") is not None:
        parts.append(_closeness_01("instrumentalness", "taste_instrumentalness", 0.08))
    if prefs.get("taste_valence") is not None:
        parts.append(_closeness_01("valence", "taste_valence", 0.08))
    if prefs.get("taste_speechiness") is not None:
        parts.append(_closeness_01("speechiness", "taste_speechiness", 0.06))
    if prefs.get("taste_liveness") is not None:
        parts.append(_closeness_01("liveness", "taste_liveness", 0.06))
    if prefs.get("taste_tempo") is not None:
        parts.append(_closeness_tempo("tempo", "taste_tempo", 0.06))

    # --- listening behavior: skippers get a tiny popularity bias ---
    # popularity is 0..100
    # avg_listen_ratio is 0..1, default 0.5
    parts.append(
        "(1 - context_user[\"avg_listen_ratio\"]) * ('popularity' / 100.0) * 0.20"
    )

    return " + ".join(parts) if parts else None
