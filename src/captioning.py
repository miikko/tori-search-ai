from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential

class Captioner:

    def __init__(self, endpoint: str, key: str):
        self.client = ImageAnalysisClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )
    
    def close(self):
        self.client.close()

    def generate_caption(self, image_url: str):
        result = self.client.analyze_from_url(
            image_url,
            visual_features=[VisualFeatures.CAPTION]
        )
        return result["captionResult"]["text"]