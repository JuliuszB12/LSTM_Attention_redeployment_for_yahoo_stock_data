import os
import json
import pandas as pd
from kafka import KafkaConsumer
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from .azure_utils import tickers, account_name, container_data


def consume_kafka_task() -> None:
    """
    Airflow task\n
    Consume latest data that Kafka received from Airbyte and save it locally
    """
    # Kafka configuration
    topic_name = 'stock'
    bootstrap_servers = ['10.1.0.4:9092']
    group_id = 'consumer'

    # Create a KafkaConsumer
    consumer = KafkaConsumer(
        topic_name,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset='latest',
        enable_auto_commit=True,  # Enable auto commit if processing is simple
        group_id=group_id
    )

    # Condition to consume data from topic
    consume = True

    # Init empty DataFrame
    columns = {
        'timestamp': 'datetime64[ns]',
        'close': 'float64',
        'high': 'float64',
        'open': 'float64',
        'low': 'float64',
        'volume': 'int64',
        'symbol': 'object'
    }
    total_df = pd.DataFrame({key: pd.Series(dtype=type_) for key, type_ in columns.items()})

    # Consume messages
    try:
        while consume:
            for message in consumer.poll(timeout_ms=1000).values():
                for msg in message:
                    # Decode the message value from bytes to a string
                    message_value = msg.value.decode('utf-8')

                    # Convert the JSON string to a Python dictionary
                    data = json.loads(message_value)
                    # Process the data
                    chart_result = data['_airbyte_data']['chart']['result'][0]
                    timestamps = chart_result['timestamp']
                    quotes = chart_result['indicators']['quote'][0]
                    symbol = chart_result['meta']['symbol']

                    # Create a DataFrame from processed data
                    df = pd.DataFrame({
                        'timestamp': pd.to_datetime(timestamps, unit='s'),
                        'low': quotes['low'],
                        'close': quotes['close'],
                        'high': quotes['high'],
                        'open': quotes['open'],
                        'volume': quotes['volume'],
                        'symbol': [symbol] * len(timestamps)
                    })

                    df[['low', 'close', 'high', 'open']] = df[['low', 'close', 'high', 'open']].round(2)

                    # Filter last timestamp and add to initial DataFrame
                    last_row_df = df.iloc[-110:]
                    total_df = pd.concat([total_df, last_row_df], ignore_index=True)
                    consume = not set(tickers).issubset(total_df['symbol'])

                    # consumer.commit()
    finally:
        # Save data locally
        for i in tickers:
            for j in range(110, 2, -1):
                row = total_df[total_df['symbol'] == i].iloc[-j]
                if pd.isna(row['close']):
                    continue
                else:
                    date_path_format = row['timestamp'].strftime('%Y/%m/%d/%H/%M/')
                    folder_path = f"data/{i}/{date_path_format}"
                    date_name_format = row['timestamp'].strftime('%Y%m%d%H%M')
                    os.makedirs(folder_path, exist_ok=True)
                    filename = f"{i}{date_name_format}.pkl"
                    temp_df = pd.DataFrame(total_df[total_df['symbol'] == i].iloc[-j:-j+1])
                    temp_df.to_pickle(folder_path+filename)
        consumer.close()


def upload_blob_task() -> None:
    """
    Airflow task\n
    Compare local data with Azure Blob Storage container and upload if necessary
    """
    path = 'data/'
    url = f"https://{account_name}.blob.core.windows.net"
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url=url, credential=credential)
    container_client = blob_service_client.get_container_client(container_data)
    for subdir, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(subdir, file)
            blob_name = file_path.replace(path, '').replace('\\', '/').strip('/')
            blob_client = container_client.get_blob_client(blob_name)
            if not blob_client.exists():
                print(f"Uploading new blob: {blob_name}")
                with open(file_path, "rb") as data:
                    blob_client.upload_blob(data)
            else:
                print(f"Blob already exists, skipping: {blob_name}")
