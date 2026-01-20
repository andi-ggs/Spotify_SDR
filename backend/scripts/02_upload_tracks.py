import os
import pandas as pd
from dotenv import load_dotenv

from recombee_api_client.api_client import RecombeeClient, Region
from recombee_api_client.api_requests import SetItemValues, Batch


REGION_MAP = {"eu-west": Region.EU_WEST}


def main():
    load_dotenv()

    database_id = os.getenv("DATABASE_ID") or os.getenv("DATABSE_ID")
    if not database_id:
        raise ValueError("Missing DATABASE_ID (or DATABSE_ID) in .env")

    private_token = os.getenv("PRIVATE_TOKEN")
    if not private_token:
        raise ValueError("Missing PRIVATE_TOKEN in .env")

    region_str = os.getenv("REGION", "eu-west").strip()
    region = REGION_MAP.get(region_str, Region.EU_WEST)

    csv_path = os.getenv("SPOTIFY_CSV_PATH", "./spotify_dataset.csv")

    client = RecombeeClient(database_id, private_token, region=region)

    df = pd.read_csv(csv_path)
    print(f"Loaded CSV: {csv_path} | rows={len(df)}")

    # Upload in batches
    batch_size = 200
    for start in range(0, len(df), batch_size):
        chunk = df.iloc[start : start + batch_size]

        reqs = []
        for _, row in chunk.iterrows():
            item_id = str(row["track_id"])

            # artists are separated by ';' in your dataset
            artists = [a.strip() for a in str(row["artists"]).split(";") if a.strip()]
            genres = [str(row["track_genre"])] if pd.notna(row["track_genre"]) else []

            values = {
                "track_name": row["track_name"],
                "album_name": row["album_name"],
                "artists": artists,
                "track_genre": genres,
                "popularity": (
                    int(row["popularity"]) if pd.notna(row["popularity"]) else None
                ),
                "duration_ms": (
                    int(row["duration_ms"]) if pd.notna(row["duration_ms"]) else None
                ),
                "explicit": (
                    bool(row["explicit"]) if pd.notna(row["explicit"]) else None
                ),
                "danceability": (
                    float(row["danceability"])
                    if pd.notna(row["danceability"])
                    else None
                ),
                "energy": float(row["energy"]) if pd.notna(row["energy"]) else None,
                "key": int(row["key"]) if pd.notna(row["key"]) else None,
                "loudness": (
                    float(row["loudness"]) if pd.notna(row["loudness"]) else None
                ),
                "mode": int(row["mode"]) if pd.notna(row["mode"]) else None,
                "speechiness": (
                    float(row["speechiness"]) if pd.notna(row["speechiness"]) else None
                ),
                "acousticness": (
                    float(row["acousticness"])
                    if pd.notna(row["acousticness"])
                    else None
                ),
                "instrumentalness": (
                    float(row["instrumentalness"])
                    if pd.notna(row["instrumentalness"])
                    else None
                ),
                "liveness": (
                    float(row["liveness"]) if pd.notna(row["liveness"]) else None
                ),
                "valence": float(row["valence"]) if pd.notna(row["valence"]) else None,
                "tempo": float(row["tempo"]) if pd.notna(row["tempo"]) else None,
                "time_signature": (
                    int(row["time_signature"])
                    if pd.notna(row["time_signature"])
                    else None
                ),
            }

            reqs.append(SetItemValues(item_id, values, cascade_create=True))

        client.send(Batch(reqs))
        print(f"Uploaded {start + len(chunk)}/{len(df)}")

    print("Done uploading tracks to Recombee.")


if __name__ == "__main__":
    main()
