import os
from dotenv import load_dotenv

from recombee_api_client.api_client import RecombeeClient, Region
from recombee_api_client.api_requests import AddUserProperty
from recombee_api_client.exceptions import ResponseException

REGION_MAP = {"eu-west": Region.EU_WEST}

USER_PROPERTIES = {
    "preferred_genres": "set",  # ["rock","pop"]
    "mood": "string",  # "happy" / "sad" / "energetic"
    "preferred_energy": "double",  # 0..1
    "preferred_danceability": "double",  # 0..1
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

    for name, ptype in USER_PROPERTIES.items():
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
