# Infrastructure Documentation

This document describes the Azure infrastructure used in the Tori Search AI project. The infrastructure is defined using CDK for Terraform (CDKTF) and consists of several free tier Azure services so keeping the project running costs nothing **AT THE TIME OF WRITING THIS DOCUMENT** (assuming there are no other resources in the subscription). All resources are deployed in the Azure North Europe region.

**DISCLAIMER**: Azure service tiers, pricing, and free tier limitations may change at any time. The author(s) of this repository make no guarantees about the continued availability of free tier services or their limitations. Users should always verify the current pricing and limitations of all Azure services before deployment. The author(s) are not liable for any charges incurred from using resources defined in this repository.

## Infrastructure Components

### State Backend
- **Resource Group**: `tori-search-ai-state-rg`
- **App Service Plan**: `tori-search-ai-state-plan` (F1 Free tier)
- **Web App**: `tori-search-ai-state` (Basic Python web app for storing Terraform state)

### Main Infrastructure Stack
**Resource Group**: `tori-search-ai-rg`

#### Azure Cosmos DB
- **Account**: `tori-search-ai-cosmos-db-account`
- **Database**: `tori-search-ai-cosmos-db-sql-db`
- **Containers**:
  - `tori-search-ai-cosmos-db-raw-listings-container` (for storing scraped listings)
  - `tori-search-ai-cosmos-db-processed-listings-container` (for storing processed listings)
  - `tori-search-ai-cosmos-db-embeddings-container` (with vector search capabilities)
- **SKU**: Lifetime free tier (see [here](https://learn.microsoft.com/en-us/azure/cosmos-db/free-tier) for more information)
- **Capacity**: Provisioned throughput (see [here](https://learn.microsoft.com/en-us/azure/cosmos-db/provisioned-throughput) for more information)
- **Consistency Level**: Session (see [here](https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels#session-consistency) for more information)
- **Limitations**:
  - Free tier comes with 1000 RU/s, split between the listing containers (600 RU/s shared) and the embeddings container (400 RU/s dedicated)
  - 25 GB storage

#### Azure AI Computer Vision
- **Account**: `tori-search-ai-computer-vision-account`
- **SKU**: Free F0 tier
- **Limitations**:
  - 20 transactions per minute
  - 5,000 transactions per month
  - Captioning only supports English

#### Azure AI Translator
- **Account**: `tori-search-ai-text-translation-account`
- **SKU**: Free F0 tier
- **Limitations**:
  - 2 million characters per month
  - Max 50 000 characters per request

#### Azure Container Apps
- **Environment**: `tori-search-ai-container-app-environment`
- **Jobs**:
  - `tori-search-ai-scraper-job` (runs hourly)
  - `tori-search-ai-updater-job` (runs daily at 12:30 AM UTC)
  - `tori-search-ai-processor-job` (runs hourly at 10 minutes past)
- **Limitations**:
  - 180 000 vCore seconds per month

#### Azure App Service
- **Service Plan**: `tori-search-ai-service-plan` (F1 Free tier)
- **Web App**: `tori-search-ai-web-app` (Website + Server)

## Infrastructure Management

### Prerequisites
1. Install Node.js and CDKTF CLI:
   - Install Node.js from https://nodejs.org/
   - Install Terraform CLI: https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli#install-terraform
   - Install CDKTF CLI:
   ```bash
   npm install --global cdktf-cli@0.20.10
   ```

2. Install infrastructure dependencies:
   ```bash
   cd infra
   pip install -r requirements.txt
   ```

### State Backend Setup
1. Create a `.env` file in `infra/state` directory:
   ```env
   STATE_SERVER_USERNAME=<your_chosen_username>
   STATE_SERVER_PASSWORD=<your_chosen_password>
   ```
   CDKTF will use these credentials to access the state server.

2. Create the required Azure resources for the state backend:
   ```bash
   # Create resource group
   az group create --name tori-search-ai-state-rg --location northeurope

   # Create app service plan
   az appservice plan create --name tori-search-ai-state-plan \
       --resource-group tori-search-ai-state-rg \
       --location northeurope \
       --is-linux \
       --sku F1

   # Create web app
   az webapp create --name tori-search-ai-state \
       --resource-group tori-search-ai-state-rg \
       --plan tori-search-ai-state-plan \
       --https-only true \
       --public-network-access enabled \
       --runtime PYTHON:3.10 \
       --startup-file startup.sh

   # Deploy state server code to web app
   cd infra/state
   zip -r infra-state.zip .
   az webapp deploy --name tori-search-ai-state \
       --resource-group tori-search-ai-state-rg \
       --type zip \
       --src-path infra-state.zip \
       --restart true
   rm -rf infra-state.zip
   cd ../..
   ```

### Main Infrastructure Deployment

1. Create a `.env` file in the `infra` directory:
   ```env
   AZURE_SUBSCRIPTION_ID=<your_azure_subscription_id>
   ```

2. Initialize AzAPI provider bindings:
   ```bash
   cdktf get
   ```

3. Deploy the infrastructure:
   ```bash
   cdktf deploy ToriSearchAIStack
   ```

   This will create all the required Azure resources defined in this document.

### Destruction
To destroy the infrastructure:

1. First destroy the main infrastructure:
   ```bash
   cdktf destroy ToriSearchAIStack
   ```

2. Then destroy the state backend:
   ```bash
   az group delete --name tori-search-ai-state-rg
   ```