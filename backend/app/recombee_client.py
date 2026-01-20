from recombee_api_client.api_client import RecombeeClient, Region
from .config import DATABASE_ID, PRIVATE_TOKEN, REGION

REGION_MAP = {"eu-west": Region.EU_WEST}

client = RecombeeClient(
    DATABASE_ID, PRIVATE_TOKEN, region=REGION_MAP.get(REGION, Region.EU_WEST)
)
