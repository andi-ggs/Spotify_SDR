import os
from dotenv import load_dotenv
from recombee_api_client.api_client import RecombeeClient, Region
from recombee_api_client.api_requests import AddUserProperty
from recombee_api_client.exceptions import ResponseException

REGION_MAP = {"eu-west": Region.EU_WEST}

USER_PROPERTIES_V2 = {
    # explicit prefs (knowledge-based)
    "preferred_genres": "set",
    "mood": "string",
    "preferred_energy": "double",
    "preferred_danceability": "double",
    "preferred_acousticness": "double",
    "preferred_instrumentalness": "double",
    "preferred_valence": "double",
    "preferred_speechiness": "double",
    "preferred_liveness": "double",
    "preferred_tempo": "double",
    # derived from behavior (listen time + likes)
    "avg_listen_seconds": "double",
    "avg_listen_ratio": "double",
    # learned taste profile from likes (weighted by listen ratio)
    "taste_energy": "double",
    "taste_danceability": "double",
    "taste_acousticness": "double",
    "taste_instrumentalness": "double",
    "taste_valence": "double",
    "taste_speechiness": "double",
    "taste_liveness": "double",
    "taste_tempo": "double",
}


def main():
    load_dotenv()
    database_id = os.getenv("DATABASE_ID") or os.getenv("DATABSE_ID")
    private_token = os.getenv("PRIVATE_TOKEN")
    region_str = os.getenv("REGION", "eu-west").strip()
    region = REGION_MAP.get(region_str, Region.EU_WEST)

    if not database_id or not private_token:
        raise ValueError("Missing DATABASE_ID and/or PRIVATE_TOKEN in .env")

    client = RecombeeClient(database_id, private_token, region=region)

    for name, ptype in USER_PROPERTIES_V2.items():
        try:
            client.send(AddUserProperty(name, ptype))
            print(f"Added user property: {name} ({ptype})")
        except ResponseException as e:
            if "already exists" in str(e).lower():
                print(f"Already exists: {name}")
            else:
                raise


if __name__ == "__main__":
    main()
