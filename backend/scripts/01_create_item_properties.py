import os
from dotenv import load_dotenv

from recombee_api_client.api_client import RecombeeClient, Region
from recombee_api_client.api_requests import AddItemProperty
from recombee_api_client.exceptions import ResponseException


ITEM_PROPERTIES = {
    "track_name": "string",
    "album_name": "string",
    "artists": "set",
    "track_genre": "set",
    "popularity": "int",
    "duration_ms": "int",
    "explicit": "boolean",
    "danceability": "double",
    "energy": "double",
    "key": "int",
    "loudness": "double",
    "mode": "int",
    "speechiness": "double",
    "acousticness": "double",
    "instrumentalness": "double",
    "liveness": "double",
    "valence": "double",
    "tempo": "double",
    "time_signature": "int",
}

REGION_MAP = {"eu-west": Region.EU_WEST}


def get_env(name: str, fallback: str | None = None) -> str:
    val = os.getenv(name, fallback)
    if not val:
        raise ValueError(f"Missing env var: {name}")
    return val


def main():
    load_dotenv()

    database_id = os.getenv("DATABASE_ID")
    if not database_id:
        raise ValueError("Missing DATABASE_ID (or DATABSE_ID) in .env")

    private_token = get_env("PRIVATE_TOKEN")
    region_str = os.getenv("REGION", "eu-west").strip()
    region = REGION_MAP.get(region_str, Region.EU_WEST)

    client = RecombeeClient(database_id, private_token, region=region)

    print(f"Using DB: {database_id} | Region: {region_str}")

    for prop, ptype in ITEM_PROPERTIES.items():
        try:
            client.send(AddItemProperty(prop, ptype))
            print(f"Added: {prop} ({ptype})")
        except ResponseException as e:
            msg = str(e).lower()
            if "already exists" in msg:
                print(f"ℹAlready exists: {prop}")
            else:
                raise

    print("Done creating item properties.")


if __name__ == "__main__":
    main()
