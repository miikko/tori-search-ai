from db import RawListingsDB, ProcessedListingsDB, EmbeddingsDB
from captioning import Captioner
from translator import Translator
from embedding import Embedder
from config import AZURE_COSMOS_CONNECTION_STRING, VISION_ENDPOINT, VISION_KEY, TEXT_TRANSLATION_ENDPOINT, TEXT_TRANSLATION_KEY

def process_new_listings():
    raw_listings_db = RawListingsDB(AZURE_COSMOS_CONNECTION_STRING)
    processed_listings_db = ProcessedListingsDB(AZURE_COSMOS_CONNECTION_STRING)
    embeddings_db = EmbeddingsDB(AZURE_COSMOS_CONNECTION_STRING)
    captioner = Captioner(VISION_ENDPOINT, VISION_KEY)
    translator = Translator(TEXT_TRANSLATION_ENDPOINT, TEXT_TRANSLATION_KEY)
    embedder = Embedder()
    img_count = 0
    processed_count = 0
    while True:
        listing = raw_listings_db.read_oldest()
        img_count += len(listing["image_urls"])
        # Azure Vision Free Tier allows 20 images per minute before throttling.
        if img_count > 20:
            break
        raw_listings_db.delete(listing["id"])
        saved_embeddings = False
        try:
            captions = [captioner.generate_caption(image_url) for image_url in listing["image_urls"]]
            listing["captions"] = [translator.translate_en_to_fi(caption) for caption in captions]
            text = listing['title']+listing['about']+",".join(listing['captions'])
            embedding = embedder.generate_embedding(text)
            embeddings_db.create({"vector": embedding, "id": listing['id']})
            saved_embeddings = True
            processed_listings_db.create(listing)
            processed_count += 1
        except Exception as e:
            print(f"Error processing listing {listing['url']}: {e}")
            if saved_embeddings:
                embeddings_db.delete(listing["id"])
    print(f"Processed {processed_count} listings")
    captioner.close()
    translator.close()

if __name__ == "__main__":
    process_new_listings()
