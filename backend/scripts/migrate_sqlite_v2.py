import os
import sqlite3
from dotenv import load_dotenv

NEW_USER_COLS = [
    ("preferred_acousticness", "REAL"),
    ("preferred_instrumentalness", "REAL"),
    ("preferred_valence", "REAL"),
    ("preferred_speechiness", "REAL"),
    ("preferred_liveness", "REAL"),
    ("preferred_tempo", "REAL"),
]


def col_exists(con, table, col):
    rows = con.execute(f"PRAGMA table_info({table});").fetchall()
    return any(r[1] == col for r in rows)


def main():
    load_dotenv()
    db_path = os.getenv("SQLITE_PATH", "./spotify_sr.db")
    con = sqlite3.connect(db_path)
    try:
        # add new columns to users (if missing)
        for col, typ in NEW_USER_COLS:
            if not col_exists(con, "users", col):
                con.execute(f"ALTER TABLE users ADD COLUMN {col} {typ};")
                print(f"Added users.{col}")

        # stats table
        con.execute(
            """
        CREATE TABLE IF NOT EXISTS user_stats (
          user_id TEXT PRIMARY KEY,
          total_views INTEGER NOT NULL DEFAULT 0,
          total_listen_seconds REAL NOT NULL DEFAULT 0,
          avg_listen_seconds REAL NOT NULL DEFAULT 0,
          avg_listen_ratio REAL NOT NULL DEFAULT 0,
          updated_at TEXT NOT NULL,
          FOREIGN KEY(user_id) REFERENCES users(user_id)
        );
        """
        )

        # taste profile table (learned from likes)
        con.execute(
            """
        CREATE TABLE IF NOT EXISTS user_taste (
          user_id TEXT PRIMARY KEY,
          taste_energy REAL,
          taste_danceability REAL,
          taste_acousticness REAL,
          taste_instrumentalness REAL,
          taste_valence REAL,
          taste_speechiness REAL,
          taste_liveness REAL,
          taste_tempo REAL,
          updated_at TEXT NOT NULL,
          FOREIGN KEY(user_id) REFERENCES users(user_id)
        );
        """
        )

        # recommendation logs (optional but excellent for grading/demo)
        con.execute(
            """
        CREATE TABLE IF NOT EXISTS recommendation_logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id TEXT NOT NULL,
          rec_type TEXT NOT NULL,         -- knowledge_only | hybrid | similar
          source_track_id TEXT,           -- for similar
          recomm_id TEXT,
          item_ids TEXT NOT NULL,         -- JSON list of track_ids
          created_at TEXT NOT NULL,
          FOREIGN KEY(user_id) REFERENCES users(user_id)
        );
        """
        )
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_reclogs_user ON recommendation_logs(user_id);"
        )

        con.commit()
        print("Migration v2 complete:", db_path)
    finally:
        con.close()


if __name__ == "__main__":
    main()
