import os
from dotenv import load_dotenv

load_dotenv()

SQLITE_PATH = os.getenv("SQLITE_PATH", "./spotify_sr.db")

DATABASE_ID = os.getenv("DATABASE_ID")
PRIVATE_TOKEN = os.getenv("PRIVATE_TOKEN")
REGION = os.getenv("REGION", "eu-west").strip()

if not DATABASE_ID:
    raise RuntimeError("Missing DATABASE_ID in .env")

if not PRIVATE_TOKEN:
    raise RuntimeError("Missing PRIVATE_TOKEN in .env")
