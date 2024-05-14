#!/bin/bash

# Fetch Airbyte workspace ID
workspace_id=$(curl -u airbyte:password -X POST http://localhost:8000/api/v1/workspaces/list \
-H "Content-Type: application/json" \
-d '{}' | python3 -c "import sys, json; print(json.load(sys.stdin)['workspaces'][0]['workspaceId'])")

# Create Yahoo Finance Price source with the Airbyte workspace ID
source_id=$(curl -u airbyte:password -X POST http://localhost:8000/api/v1/sources/create \
-H "Content-Type: application/json" \
-d '{
    "sourceDefinitionId": "09a517d3-803f-448d-97bf-0b1ee64b90ef",
    "workspaceId": "'$workspace_id'",
    "connectionConfiguration": {
        "tickers": "AMZN, AXP",
        "interval": "1d",
        "range": "1y"
    },
    "name": "Yahoo source"
}' | python3 -c "import sys, json; print(json.load(sys.stdin)['sourceId'])")

# Create Kafka destination with the Airbyte workspace ID
destination_id=$(curl -u airbyte:password -X POST http://localhost:8000/api/v1/destinations/create \
-H "Content-Type: application/json" \
-d '{
    "destinationDefinitionId": "9f760101-60ae-462f-9ee6-b7a9dafd454d",
    "workspaceId": "'$workspace_id'",
    "connectionConfiguration": {
        "acks": "all",
        "batch_size": 16384,
        "bootstrap_servers": "10.1.0.4:9092",
        "buffer_memory": "33554432",
        "client_dns_lookup": "use_all_dns_ips",
        "compression_type": "none",
        "delivery_timeout_ms": 120000,
        "enable_idempotence": true,
        "linger_ms": "1",
        "max_block_ms": "60000",
        "max_in_flight_requests_per_connection": 5,
        "max_request_size": 1048576,
        "protocol": {
            "security_protocol": "PLAINTEXT"
        },
        "receive_buffer_bytes": -1,
        "request_timeout_ms": 30000,
        "retries": 2147483647,
        "send_buffer_bytes": -1,
        "socket_connection_setup_timeout_ms": "10000",
        "socket_connection_setup_timeout_max_ms": "30000",
        "topic_pattern": "stock",
        "client_id": "airbyte-producer",
        "sync_producer": false,
        "test_topic": "testing"
    },
    "name": "Kafka destination"
}' | python3 -c "import sys, json; print(json.load(sys.stdin)['destinationId'])")

# Create connection between created source and destination
curl -u airbyte:password -X POST http://localhost:8000/api/v1/connections/create \
-H "Content-Type: application/json" \
-d '{
    "sourceId": "'$source_id'",
    "destinationId": "'$destination_id'",
    "syncCatalog": {
        "streams": [
            {
                "stream": {
                    "name": "price",
                    "jsonSchema": {
                        "type": "object",
                        "properties": {
                            "chart": {
                                "type": "object",
                                "properties": {
                                    "result": {
                                        "type": "array",
                                        "items": {}
                                    }
                                }
                            }
                        }
                    },
                    "supportedSyncModes": ["full_refresh"],
                    "sourceDefinedCursor": false,
                    "defaultCursorField": [],
                    "sourceDefinedPrimaryKey": [],
                    "namespace": null
                },
                "config": {
                    "syncMode": "full_refresh",
                    "cursorField": [],
                    "destinationSyncMode": "append",
                    "primaryKey": [],
                    "selected": true,
                    "aliasName": "alias_price"
                }
            }
        ]
    },
    "scheduleType" : "cron",
    "scheduleData": {
        "cron": {
            "cronExpression": "*/7 * * * * ?",
            "cronTimeZone": "UTC"
            }
    },
    "status": "active",
    "name": "Yahoo to Kafka"
}'
