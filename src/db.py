# Free Azure Cosmos DB comes with 1000 RU/s throughput and 25 GB storage
# https://learn.microsoft.com/en-us/azure/cosmos-db/free-tier

# About RUs
# https://learn.microsoft.com/en-us/azure/cosmos-db/request-units
# https://learn.microsoft.com/en-us/azure/cosmos-db/optimize-cost-reads-writes

from typing import List, Dict, Optional
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError

class DB:

    def __init__(self, connection_string: str, database_name: str, container_name: str):
        self.client = CosmosClient.from_connection_string(connection_string)
        self.database = self.client.get_database_client(database_name)
        self.container = self.database.get_container_client(container_name)

    def remove_system_properties(self, item: Dict) -> Dict:
        """Remove system properties from the item"""
        del item["_ts"]
        del item["_self"]
        del item["_rid"]
        del item["_etag"]
        return item

    def create(self, item: Dict) -> None:
        """Create a new item in the database"""
        self.container.create_item(item, enable_automatic_id_generation=True)

    def read(self, id: str) -> Dict:
        """Get an item by its ID"""
        item = self.container.read_item(item=id, partition_key=id)
        return self.remove_system_properties(item)
    
    def read_all(self) -> List[Dict]:
        """Get all items"""
        return [self.remove_system_properties(item) for item in self.container.read_all_items()]

    def delete(self, id: str) -> None:
        """Delete an item by its ID"""
        try:
            self.container.delete_item(item=id, partition_key=id)
        except CosmosResourceNotFoundError:
            pass

    def update(self, id: str, new_item: Dict) -> None:
        """Replaces the item with ID with new_item"""
        self.container.replace_item(item=id, body=new_item)

    def query(self, query: str, parameters: Optional[List[Dict]] = None) -> List[Dict]:
        """Query items using SQL-like syntax"""
        parameters = parameters or []
        return list(self.container.query_items(
            query=query,
            enable_cross_partition_query=True,
            parameters=parameters,
            populate_query_metrics=True
        ))
    
    def print_query_metrics(self) -> None:
        """Print the latest query metrics"""
        metrics_str = self.container.client_connection.last_response_headers['x-ms-documentdb-query-metrics']
        metrics_dict = dict(item.split('=') for item in metrics_str.split(';'))
        print("Query Metrics:")
        print(f"Request Units consumed: {self.container.client_connection.last_response_headers['x-ms-request-charge']}")
        for key, value in metrics_dict.items():
            print(f"{key}: {value}")

DATABASE_NAME = "tori-search-ai-cosmos-db-sql-db"

class ProcessedListingsDB(DB):
    def __init__(self, connection_string: str):
        super().__init__(connection_string, DATABASE_NAME, "tori-search-ai-cosmos-db-processed-listings-container")

    def query_listings_older_than(self, timestamp: str) -> List[Dict]:
        """Get listings that were last checked before the given ISO 8601 timestamp"""
        query = """
        SELECT * FROM c WHERE c.last_checked < @timestamp
        """
        parameters = [{"name": "@timestamp", "value": timestamp}]
        return [self.remove_system_properties(item) for item in self.query(query, parameters)]

    def query_listing_count(self) -> int:
        """Get the number of listings in the database"""
        query = "SELECT VALUE COUNT(1) FROM c"
        return self.query(query)[0]

class RawListingsDB(DB):
    def __init__(self, connection_string: str):
        super().__init__(connection_string, DATABASE_NAME, "tori-search-ai-cosmos-db-raw-listings-container")

    def read_oldest(self) -> Dict:
        """Get the oldest listing from the database"""
        query = "SELECT TOP 1 * FROM c ORDER BY c._ts ASC"
        return self.remove_system_properties(self.query(query)[0])

class EmbeddingsDB(DB):
    def __init__(self, connection_string: str):
        super().__init__(connection_string, DATABASE_NAME, "tori-search-ai-cosmos-db-embeddings-container")

    def vector_search(self, vector: List[float], top_k: int = 10, threshold: float = 0.5) -> List[Dict]:
        """Perform vector similarity search using the VectorDistance function"""
        query = """
        SELECT TOP @top_k c.id,VectorDistance(c.vector, @query_vector) as similarity_score
        FROM c
        WHERE VectorDistance(c.vector, @query_vector) > @threshold
        ORDER BY VectorDistance(c.vector, @query_vector)
        """
        parameters = [
            {"name": "@query_vector", "value": vector},
            {"name": "@top_k", "value": top_k},
            {"name": "@threshold", "value": threshold}
        ]
        return self.query(query, parameters)
