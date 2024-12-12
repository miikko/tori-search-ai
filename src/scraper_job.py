from db import ProcessedListingsDB, RawListingsDB
from scraper import scrape_listings
from config import AZURE_COSMOS_CONNECTION_STRING

# location=0.100018 is the Uusimaa region
# sub_category=1.78.5198 is the "Kaapit" category
# trade_type=1 means that listings are for sale (2 means for free)
closet_listings_url = "https://www.tori.fi/recommerce/forsale/search?location=0.100018&sub_category=1.78.5198&trade_type=1"

def scrape_new_listings():
    processed_listings_db = ProcessedListingsDB(AZURE_COSMOS_CONNECTION_STRING)
    raw_listings_db = RawListingsDB(AZURE_COSMOS_CONNECTION_STRING)
    listings = processed_listings_db.read_all() + raw_listings_db.read_all()
    limit = min(10, 1000 - len(listings))
    new_listings, _ = scrape_listings(closet_listings_url, limit, set(listing["url"] for listing in listings))
    for listing in new_listings:
        raw_listings_db.create(listing)
    print(f"Scraped {len(new_listings)} new listings")

if __name__ == "__main__":
    scrape_new_listings()
