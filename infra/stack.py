from constructs import Construct
from cdktf import TerraformStack
from imports.azapi.provider import AzapiProvider
from cdktf_cdktf_provider_azurerm.provider import AzurermProvider
from cdktf_cdktf_provider_azurerm.resource_group import ResourceGroup
from cdktf import HttpBackend
from config import STATE_SERVER_USERNAME, STATE_SERVER_PASSWORD, AZURE_SUBSCRIPTION_ID
from resources.db import create_db
from resources.ai import create_ai
from resources.compute import create_compute
from resources.web import create_web_app

class Stack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)
        name_prefix = "tori-search-ai"
        AzurermProvider(
            self,
            "azurerm",
            features=[{"features": {}}],
            subscription_id=AZURE_SUBSCRIPTION_ID,
            resource_providers_to_register=["Microsoft.App"]
        )
        AzapiProvider(
            self,
            "azapi",
            subscription_id=AZURE_SUBSCRIPTION_ID
        )
        HttpBackend(
            self,
            address="https://tori-search-ai-state.azurewebsites.net/tori-search-ai-state",
            lock_address="https://tori-search-ai-state.azurewebsites.net/tori-search-ai-state",
            unlock_address="https://tori-search-ai-state.azurewebsites.net/tori-search-ai-state",
            username=STATE_SERVER_USERNAME,
            password=STATE_SERVER_PASSWORD
        )
        rg = ResourceGroup(
            self,
            f"{name_prefix}-rg",
            location="northeurope",
            name=f"{name_prefix}-rg",
        )
        db_conn_string = create_db(self, name_prefix, rg)
        ai_connection_info = create_ai(self, name_prefix, rg)
        env_vars = {
            "AZURE_COSMOS_CONNECTION_STRING": db_conn_string,
            "VISION_ENDPOINT": ai_connection_info["ComputerVision"]["endpoint"],
            "VISION_KEY": ai_connection_info["ComputerVision"]["key"],
            "TEXT_TRANSLATION_ENDPOINT": ai_connection_info["TextTranslation"]["endpoint"],
            "TEXT_TRANSLATION_KEY": ai_connection_info["TextTranslation"]["key"]
        }
        create_compute(self, name_prefix, rg, env_vars)
        create_web_app(self, name_prefix, rg, env_vars)

