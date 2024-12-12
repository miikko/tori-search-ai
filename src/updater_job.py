from datetime import datetime, timedelta
import requests
from db import ProcessedListingsDB, EmbeddingsDB
from config import AZURE_COSMOS_CONNECTION_STRING

def update_listing_availability():
    processed_listings_db = ProcessedListingsDB(AZURE_COSMOS_CONNECTION_STRING)
    embeddings_db = EmbeddingsDB(AZURE_COSMOS_CONNECTION_STRING)
    outdated_listings = processed_listings_db.query_listings_older_than((datetime.now() - timedelta(days=1)).isoformat())
    delete_count = 0
    for listing in outdated_listings:
        if requests.get(listing["url"]).status_code != 200:
            processed_listings_db.delete(listing["id"])
            embeddings_db.delete(listing["id"])
            delete_count += 1
        else:
            listing["last_checked"] = datetime.now().isoformat()
            processed_listings_db.update(listing["id"], listing)
    print(f"Updated availability for {len(outdated_listings)} listings. Out of those, {delete_count} were deleted.")

if __name__ == "__main__":
    update_listing_availability()
