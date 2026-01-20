import os, sqlite3
from dotenv import load_dotenv


def col_exists(con, table, col):
    rows = con.execute(f"PRAGMA table_info({table});").fetchall()
    return any(r[1] == col for r in rows)


def main():
    load_dotenv()
    db_path = os.getenv("SQLITE_PATH", "./spotify_sr.db")
    con = sqlite3.connect(db_path)
    try:
        if not col_exists(con, "users", "password_hash"):
            con.execute("ALTER TABLE users ADD COLUMN password_hash TEXT;")
            print("Added users.password_hash")

        con.commit()
        print("Auth migration complete.")
    finally:
        con.close()


if __name__ == "__main__":
    main()
