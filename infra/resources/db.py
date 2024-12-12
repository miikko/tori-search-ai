from constructs import Construct
from imports.azapi.resource import Resource
from cdktf_cdktf_provider_azurerm.cosmosdb_account import CosmosdbAccount
from cdktf_cdktf_provider_azurerm.cosmosdb_sql_database import CosmosdbSqlDatabase
from cdktf_cdktf_provider_azurerm.cosmosdb_sql_container import CosmosdbSqlContainer
from cdktf_cdktf_provider_azurerm.resource_group import ResourceGroup

def create_db(scope: Construct, name_prefix: str, rg: ResourceGroup):
    # Max throughput for free tier
    max_throughput = 1000
    # A container with vector indexing must have dedicated throughput
    embeddings_throughput = 400
    cosmos_db_account = CosmosdbAccount(
        scope,
        f"{name_prefix}-cosmos-db-account",
        resource_group_name=rg.name,
        location=rg.location,
        name=f"{name_prefix}-cosmos-db-account",
        offer_type="Standard",
        free_tier_enabled=True,
        consistency_policy={
            # About consistency levels
            # https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels#session-consistency
            "consistency_level": "Session"
        },
        capacity={
            "total_throughput_limit": max_throughput
        },
        kind="GlobalDocumentDB",
        geo_location=[{
            "location": rg.location,
            "failoverPriority": 0 # Likely a bug in the cdktf Python mapping that this key needs to be camel case instead of snake case
        }],
        burst_capacity_enabled=True,
        public_network_access_enabled=True,
        capabilities=[{
            "name": "EnableNoSQLVectorSearch"
        }],
        local_authentication_disabled=False
    )
    sql_db = CosmosdbSqlDatabase(
        scope,
        f"{name_prefix}-cosmos-db-sql-db",
        name=f"{name_prefix}-cosmos-db-sql-db",
        resource_group_name=rg.name,
        account_name=cosmos_db_account.name,
        throughput=max_throughput - embeddings_throughput
    )
    container_configs = [
        {
            "name": f"{name_prefix}-cosmos-db-raw-listings-container",
            "included_paths": [],
            "excluded_paths": ["/*"]
        },
        {
            "name": f"{name_prefix}-cosmos-db-processed-listings-container",
            "included_paths": ["/last_checked/?"],
            "excluded_paths": ["/*"]
        }
    ]
    for config in container_configs:
        CosmosdbSqlContainer(
            scope,
            config["name"],
            name=config["name"],
            resource_group_name=rg.name,
            account_name=cosmos_db_account.name,
            database_name=sql_db.name,
            partition_key_paths=["/id"],
            partition_key_kind="Hash",
            partition_key_version=1, # Use value 2 if partition key value can be longer than 101 characters
            indexing_policy={
                "indexing_mode": "consistent",
                "included_path": [{"path": path} for path in config["included_paths"]],
                "excluded_path": [{"path": path} for path in config["excluded_paths"]]
            }
        )
    # Creating a container with vector indexing is not supported with the AzureRM provider
    Resource(
        scope,
        f"{name_prefix}-cosmos-db-embeddings-container",
        type="Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-12-01-preview",
        name=f"{name_prefix}-cosmos-db-embeddings-container",
        location=rg.location,
        parent_id=sql_db.id,
        body={
            "properties": {
                "options": {
                    "throughput": embeddings_throughput
                },
                "resource": {
                    "id": f"{name_prefix}-cosmos-db-embeddings-container",
                    "indexingPolicy": {
                        "indexingMode": "consistent",
                        "includedPaths": [{"path": "/*"}],
                        "excludedPaths": [{"path": "/_etag/?"}, {"path": "/vector/*"}],
                        # Flat vector index type supports vectors with up to 505 dimensions
                        # Use "quantizedFlat" or "diskANN" if expected number of vectors in this container exceeds 1000
                        # Reference: https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/vector-search#vector-indexing-policies
                        "vectorIndexes": [{ "type": "flat", "path": "/vector"}]
                    },
                    "partitionKey": {
                        "kind": "Hash",
                        "paths": ["/id"],
                        "version": 1
                    },
                    "vectorEmbeddingPolicy": {
                        "vectorEmbeddings": [{
                            "dataType": "float32",
                            "dimensions": 300,
                            "distanceFunction": "cosine",
                            "path": "/vector"
                        }]
                    }
                }
            }
        }
    )
    return cosmos_db_account.primary_sql_connection_string