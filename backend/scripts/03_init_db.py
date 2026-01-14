import os
import sqlite3
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tracks (
  track_id TEXT PRIMARY KEY,
  track_name TEXT,
  artists TEXT,
  album_name TEXT,
  track_genre TEXT,
  popularity INTEGER,
  duration_ms INTEGER,
  explicit INTEGER,
  danceability REAL,
  energy REAL,
  key INTEGER,
  loudness REAL,
  mode INTEGER,
  speechiness REAL,
  acousticness REAL,
  instrumentalness REAL,
  liveness REAL,
  valence REAL,
  tempo REAL,
  time_signature INTEGER
);

CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  preferred_genres TEXT,          -- JSON string, e.g. ["rock","pop"]
  mood TEXT,                      -- e.g. "happy", "sad", "energetic"
  preferred_energy REAL,          -- 0..1
  preferred_danceability REAL     -- 0..1
);

CREATE TABLE IF NOT EXISTS interactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  track_id TEXT NOT NULL,
  event_type TEXT NOT NULL,       -- "view" | "rating" | "bookmark"
  rating REAL,                    -- for likes/dislikes
  duration_ms INTEGER,            -- optional for view
  recomm_id TEXT,                 -- optional Recombee recommId
  created_at TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(user_id),
  FOREIGN KEY(track_id) REFERENCES tracks(track_id)
);

CREATE INDEX IF NOT EXISTS idx_interactions_user ON interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_track ON interactions(track_id);
"""

TRACK_COLS = [
    "track_id",
    "track_name",
    "artists",
    "album_name",
    "track_genre",
    "popularity",
    "duration_ms",
    "explicit",
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "time_signature",
]


def utcnow_iso():
    return datetime.now(timezone.utc).isoformat()


def main():
    load_dotenv()
    db_path = os.getenv("SQLITE_PATH", "./spotify_sr.db")
    csv_path = os.getenv("SPOTIFY_CSV_PATH", "spotify_dataset.csv")

    con = sqlite3.connect(db_path)
    try:
        con.executescript(SCHEMA_SQL)

        df = pd.read_csv(csv_path)

        missing = [c for c in TRACK_COLS if c not in df.columns]
        if missing:
            raise ValueError(f"CSV missing columns: {missing}")

        # normalize artists delimiter (keep as stored text; we’ll split in code when needed)
        df["artists"] = df["artists"].fillna("").astype(str)

        # SQLite upsert
        placeholders = ",".join(["?"] * len(TRACK_COLS))
        cols_sql = ",".join(TRACK_COLS)
        update_sql = ",".join(
            [f"{c}=excluded.{c}" for c in TRACK_COLS if c != "track_id"]
        )

        sql = f"""
        INSERT INTO tracks ({cols_sql})
        VALUES ({placeholders})
        ON CONFLICT(track_id) DO UPDATE SET {update_sql};
        """

        rows = []
        for _, r in df[TRACK_COLS].iterrows():
            rows.append(tuple(None if pd.isna(v) else v for v in r.values))

        con.executemany(sql, rows)
        con.commit()

        count = con.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        print(f"SQLite ready: {db_path}")
        print(f"Tracks loaded: {count}")

    finally:
        con.close()


if __name__ == "__main__":
    main()
