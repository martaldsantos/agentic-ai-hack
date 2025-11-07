import os
import json
from typing import Annotated
from azure.cosmos import CosmosClient
from functools import lru_cache

# Cache the Cosmos client to avoid recreating it on each call
@lru_cache(maxsize=1)
def _get_cosmos_client():
    """Get or create a cached Cosmos DB client."""
    endpoint = os.environ.get("COSMOS_ENDPOINT")
    key = os.environ.get("COSMOS_KEY")
    
    if not endpoint or not key:
        raise ValueError("COSMOS_ENDPOINT and COSMOS_KEY environment variables must be set")
    
    return CosmosClient(endpoint, key)

# Define standalone functions that can be used as tools in Agent Framework

def get_document_by_claim_id(claim_id: Annotated[str, "The claim_id to retrieve"]) -> Annotated[str, "JSON document from Cosmos DB"]:
    """Retrieve a document by its claim_id using a cross-partition query."""
    database_name = "insurance_claims"
    container_name = "crash_reports"
    
    try:
        client = _get_cosmos_client()
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        # Use SQL query to find document by claim_id across all partitions
        query = "SELECT * FROM c WHERE c.claim_id = @claim_id"
        parameters = [{"name": "@claim_id", "value": claim_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True,
            max_item_count=1
        ))
        
        if not items:
            return f"❌ No document found with claim_id '{claim_id}' in container '{container_name}'."
        
        # Return the first matching document
        document = items[0]
        return json.dumps(document, indent=2, ensure_ascii=False)
        
    except ValueError as ve:
        return f"❌ Configuration error: {str(ve)}"
    except Exception as e:
        return f"❌ Error retrieving document by claim_id '{claim_id}': {str(e)}"

# Export the function
__all__ = ['get_document_by_claim_id']
