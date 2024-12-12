from flask import Flask, render_template, request, jsonify
from db import ProcessedListingsDB, EmbeddingsDB
from embedding import Embedder
from translator import Translator
from config import (
    AZURE_COSMOS_CONNECTION_STRING, 
    TEXT_TRANSLATION_ENDPOINT, 
    TEXT_TRANSLATION_KEY
)

app = Flask(__name__, static_folder='static', static_url_path='/static')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    
    if not query:
        return jsonify([])
    
    # Initialize services
    processed_listings_db = ProcessedListingsDB(AZURE_COSMOS_CONNECTION_STRING)
    embeddings_db = EmbeddingsDB(AZURE_COSMOS_CONNECTION_STRING)
    embedder = Embedder()
    translator = Translator(TEXT_TRANSLATION_ENDPOINT, TEXT_TRANSLATION_KEY)
    
    # Translate query to Finnish and get embeddings
    query_fi = translator.translate_en_to_fi(query).lower()
    query_embedding = embedder.generate_embedding(query_fi)
    embeddings = embeddings_db.vector_search(query_embedding, top_k=10)
    matches = [processed_listings_db.read(embedding["id"]) for embedding in embeddings]
    
    return jsonify(matches)

if __name__ == '__main__':
    app.run(debug=True)