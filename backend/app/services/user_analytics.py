from datetime import datetime, timezone
from recombee_api_client.api_requests import SetUserValues
from ..recombee_client import client as recombee

AUDIO_COLS = [
    "energy",
    "danceability",
    "acousticness",
    "instrumentalness",
    "valence",
    "speechiness",
    "liveness",
    "tempo",
]


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def update_user_stats_and_taste(con, user_id: str):
    """
    Updates:
      - user_stats: avg_listen_seconds, avg_listen_ratio (from last 200 views)
      - user_taste: taste_* (from last 100 likes, weighted by listen_ratio of latest view on that track)
    """
    # ---- stats from views ----
    rows = con.execute(
        """
        SELECT i.duration_ms, t.duration_ms
        FROM interactions i
        JOIN tracks t ON t.track_id=i.track_id
        WHERE i.user_id=? AND i.event_type='view'
          AND i.duration_ms IS NOT NULL
          AND t.duration_ms IS NOT NULL
        ORDER BY i.created_at DESC
        LIMIT 200
        """,
        (user_id,),
    ).fetchall()

    total_views = len(rows)
    if total_views:
        listen_seconds = [max(0.0, r[0] / 1000.0) for r in rows]
        ratios = []
        for dv_ms, track_ms in rows:
            if track_ms and track_ms > 0:
                ratios.append(min(1.0, (dv_ms / 1000.0) / (track_ms / 1000.0)))

        avg_listen_seconds = sum(listen_seconds) / total_views
        avg_listen_ratio = (sum(ratios) / len(ratios)) if ratios else 0.0
    else:
        avg_listen_seconds = 0.0
        avg_listen_ratio = 0.5  # neutral default

    con.execute(
        """
        INSERT INTO user_stats(user_id,total_views,total_listen_seconds,avg_listen_seconds,avg_listen_ratio,updated_at)
        VALUES(?,?,?,?,?,?)
        ON CONFLICT(user_id) DO UPDATE SET
          total_views=excluded.total_views,
          total_listen_seconds=excluded.total_listen_seconds,
          avg_listen_seconds=excluded.avg_listen_seconds,
          avg_listen_ratio=excluded.avg_listen_ratio,
          updated_at=excluded.updated_at
        """,
        (
            user_id,
            total_views,
            avg_listen_seconds * total_views,
            avg_listen_seconds,
            avg_listen_ratio,
            utcnow_iso(),
        ),
    )

    # ---- taste from likes (weighted by listen ratio) ----
    liked = con.execute(
        """
        SELECT
          t.energy,t.danceability,t.acousticness,t.instrumentalness,
          t.valence,t.speechiness,t.liveness,t.tempo,
          t.duration_ms,
          (
            SELECT i2.duration_ms
            FROM interactions i2
            WHERE i2.user_id=i.user_id AND i2.track_id=i.track_id AND i2.event_type='view'
            ORDER BY i2.created_at DESC
            LIMIT 1
          ) as last_view_ms
        FROM interactions i
        JOIN tracks t ON t.track_id=i.track_id
        WHERE i.user_id=? AND i.event_type='rating' AND i.rating=1
        ORDER BY i.created_at DESC
        LIMIT 100
        """,
        (user_id,),
    ).fetchall()

    if not liked:
        con.execute(
            """
            INSERT INTO user_taste(user_id, updated_at)
            VALUES(?,?)
            ON CONFLICT(user_id) DO UPDATE SET updated_at=excluded.updated_at
            """,
            (user_id, utcnow_iso()),
        )
        return

    sums = {c: 0.0 for c in AUDIO_COLS}
    wsum = 0.0

    for row in liked:
        (
            energy,
            danceability,
            acousticness,
            instrumentalness,
            valence,
            speechiness,
            liveness,
            tempo,
            track_ms,
            last_view_ms,
        ) = row

        if track_ms and last_view_ms:
            w = min(1.0, (last_view_ms / 1000.0) / (track_ms / 1000.0))
        else:
            w = 0.5  # fallback weight

        wsum += w
        vals = {
            "energy": energy,
            "danceability": danceability,
            "acousticness": acousticness,
            "instrumentalness": instrumentalness,
            "valence": valence,
            "speechiness": speechiness,
            "liveness": liveness,
            "tempo": tempo,
        }
        for k, v in vals.items():
            if v is not None:
                sums[k] += float(v) * w

    if wsum <= 0:
        return

    taste = {f"taste_{k}": (sums[k] / wsum) for k in AUDIO_COLS}

    con.execute(
        """
        INSERT INTO user_taste(
          user_id,
          taste_energy, taste_danceability, taste_acousticness, taste_instrumentalness,
          taste_valence, taste_speechiness, taste_liveness, taste_tempo,
          updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(user_id) DO UPDATE SET
          taste_energy=excluded.taste_energy,
          taste_danceability=excluded.taste_danceability,
          taste_acousticness=excluded.taste_acousticness,
          taste_instrumentalness=excluded.taste_instrumentalness,
          taste_valence=excluded.taste_valence,
          taste_speechiness=excluded.taste_speechiness,
          taste_liveness=excluded.taste_liveness,
          taste_tempo=excluded.taste_tempo,
          updated_at=excluded.updated_at
        """,
        (
            user_id,
            taste["taste_energy"],
            taste["taste_danceability"],
            taste["taste_acousticness"],
            taste["taste_instrumentalness"],
            taste["taste_valence"],
            taste["taste_speechiness"],
            taste["taste_liveness"],
            taste["taste_tempo"],
            utcnow_iso(),
        ),
    )


def sync_user_derived_to_recombee(con, user_id: str):
    """
    Push avg_listen_* and taste_* to Recombee so booster can use context_user values.
    """
    stats = con.execute(
        "SELECT avg_listen_seconds, avg_listen_ratio FROM user_stats WHERE user_id=?",
        (user_id,),
    ).fetchone()
    taste = con.execute(
        """
        SELECT taste_energy, taste_danceability, taste_acousticness, taste_instrumentalness,
               taste_valence, taste_speechiness, taste_liveness, taste_tempo
        FROM user_taste WHERE user_id=?
        """,
        (user_id,),
    ).fetchone()

    values = {}

    if stats:
        values["avg_listen_seconds"] = float(stats[0] or 0.0)
        values["avg_listen_ratio"] = float(stats[1] if stats[1] is not None else 0.5)
    else:
        values["avg_listen_seconds"] = 0.0
        values["avg_listen_ratio"] = 0.5

    if taste:
        keys = [
            "taste_energy",
            "taste_danceability",
            "taste_acousticness",
            "taste_instrumentalness",
            "taste_valence",
            "taste_speechiness",
            "taste_liveness",
            "taste_tempo",
        ]
        for k, v in zip(keys, taste):
            if v is not None:
                values[k] = float(v)

    recombee.send(SetUserValues(user_id, values, cascade_create=True))
