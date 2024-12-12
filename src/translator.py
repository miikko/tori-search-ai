from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential

class Translator:

    def __init__(self, endpoint: str, key: str):
        self.client = TextTranslationClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key),
            region="northeurope"
        )
    
    def close(self):
        self.client.close()

    def translate_en_to_fi(self, text: str):
        result = self.client.translate(
            body=[text],
            from_language="en",
            to_language=["fi"]
        )
        return result[0].translations[0].text
