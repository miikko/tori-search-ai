from constructs import Construct
from cdktf_cdktf_provider_azurerm.cognitive_account import CognitiveAccount
from cdktf_cdktf_provider_azurerm.resource_group import ResourceGroup

def create_ai(scope: Construct, name_prefix: str, rg: ResourceGroup):
    account_configs = [
        {
            "name": f"{name_prefix}-computer-vision-account",
            "kind": "ComputerVision",
        },
        {
            "name": f"{name_prefix}-text-translation-account",
            "kind": "TextTranslation",
        }
    ]
    connection_info = {}
    for config in account_configs:
        account = CognitiveAccount(
            scope,
            config["name"],
            resource_group_name=rg.name,
            location=rg.location,
            name=config["name"],
            kind=config["kind"],
            sku_name="F0",
            local_auth_enabled=True
        )
        connection_info[config["kind"]] = {
            "endpoint": account.endpoint,
            "key": account.primary_access_key
        }
    return connection_info