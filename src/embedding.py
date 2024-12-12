import spacy

class Embedder:
    def __init__(self):
        self.nlp = spacy.load('fi_core_news_lg')
    
    def generate_embedding(self, text: str) -> list[float]:
        doc = self.nlp(text)
        return doc.vector.tolist()
