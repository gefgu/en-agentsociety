import clickhouse_connect
from functools import lru_cache

# This function creates the client once and reuses it
@lru_cache()
def get_clickhouse_client():
    client = clickhouse_connect.get_client(
        host="localhost",
        port=8123,
        username="default",
        password="clickhouse",
        database="fastsociety",
        # Optional: Add timeouts or pool settings here if needed
    )
    return client