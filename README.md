# Tori Search AI

This is a hobby project that allows users to query a limited subset of Tori.fi cabinet listings with natural language. The project is hosted in Azure. Try out the project by clicking [here](https://tori-search-ai-web-app.azurewebsites.net/). Note that the capabilities are very limited due to the cost free nature of this project. See [DEV_NOTES.md](DEV_NOTES.md) for more information.

For detailed information about the infrastructure, including resource specifications and deployment instructions, refer to [INFRA.md](INFRA.md).

## System Requirements
- Python >= 3.10 (for local development)
- Docker (for local Docker development and image deployment)
- Azure CLI

## Setup Instructions

One can run the project locally either directly in a machine or in a Docker container. In either case, create a `.env` file in the root directory with the following variables:
```env
AZURE_COSMOS_CONNECTION_STRING=your_cosmos_connection_string
VISION_ENDPOINT=your_vision_endpoint
VISION_KEY=your_vision_key
TEXT_TRANSLATION_ENDPOINT=your_translation_endpoint
TEXT_TRANSLATION_KEY=your_translation_key
```

Values for these variables can be found in the Azure portal after deploying the infrastructure.

### Local Environment Setup

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install spaCy model for embeddings:
```bash
python -m spacy download fi_core_news_lg
```

4. Install Chromium for Playwright:
```bash
playwright install --with-deps chromium
```

### Docker Setup

Either build the Docker images yourself or pull pre-built images from Docker Hub.

Build Docker images:
```bash
# Build scraper job image
docker build -t tori-search-ai-scraper-job:latest -f docker/Dockerfile.scraper .
# Build updater job image
docker build -t tori-search-ai-updater-job:latest -f docker/Dockerfile.updater .
# Build processor job image
docker build -t tori-search-ai-processor-job:latest -f docker/Dockerfile.processor .
# Build web app image
docker build -t tori-search-ai-web:latest -f docker/Dockerfile.web .
```

Pull pre-built images from Docker Hub:
```bash
# Pull scraper job image
docker pull hovvk/tori-search-ai-scraper-job:latest
# Pull updater job image
docker pull hovvk/tori-search-ai-updater-job:latest
# Pull processor job image
docker pull hovvk/tori-search-ai-processor-job:latest
# Pull web app image
docker pull hovvk/tori-search-ai-web:latest
```

2. Run containers locally (remove `hovvk/` prefix if you built the images yourself):
```bash
# Run scraper job
docker run --rm -it --env-file .env hovvk/tori-search-ai-scraper-job:latest
# Run updater job
docker run --rm -it --env-file .env hovvk/tori-search-ai-updater-job:latest
# Run processor job
docker run --rm -it --env-file .env hovvk/tori-search-ai-processor-job:latest
# Run web app
docker run --rm -it --env-file .env hovvk/tori-search-ai-web:latest
```
