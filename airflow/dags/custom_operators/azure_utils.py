import os
from datetime import datetime, timedelta
import requests
import pandas as pd
import pickle
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from azureml.core.authentication import MsiAuthentication
from azureml.core import Model, Workspace
import mlflow
from mlflow.tracking import MlflowClient


def read_blob(account_name: str, container_name: str) -> pd.DataFrame:
    """
    Read blob data from Azure Blob Storage container
    """
    url = f"https://{account_name}.blob.core.windows.net"
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url=url, credential=credential)
    container_client = blob_service_client.get_container_client(container_name)

    # Calculate the date 3 months ago
    three_months_ago = datetime.now() - timedelta(days=90)

    # List to hold all DataFrames
    dataframes = []

    try:
        blobs = container_client.list_blobs()
        for blob in blobs:
            # Example blob name: 'some_folder_name/yyyy/mm/dd/HH/MM/file_name.pkl'
            parts = blob.name.split('/')
            if len(parts) > 5 and parts[1].isdigit() and parts[2].isdigit() and parts[3].isdigit():
                # Parse the date from the blob name
                year = int(parts[1])
                month = int(parts[2])
                day = int(parts[3])
                blob_date = datetime(year, month, day)

                # Check if the blob date is within the last three months
                if blob_date > three_months_ago:
                    blob_client = container_client.get_blob_client(blob)
                    blob_data = blob_client.download_blob().readall()
                    data = pickle.loads(blob_data)
                    if isinstance(data, pd.DataFrame):  # Check if data is a DataFrame
                        dataframes.append(data)
                    else:
                        raise Exception(f"Blob {blob.name} does not contain a DataFrame.")

        # Concatenate all DataFrames into one
        if dataframes:
            final_df = pd.concat(dataframes, ignore_index=True)
            return final_df
        else:
            raise Exception("No DataFrame blobs found from the last 3 months.")

    except Exception as e:
        print(f"An error occurred: {e}")


def auth_ws_register_model(model_name: str, tickers: list[str]) -> tuple[Workspace, Model]:
    # Download mlflow production version of trained model
    mlflow.set_tracking_uri("http://10.4.0.4:5000")
    client = MlflowClient()
    prod_version = client.get_model_version_by_alias(model_name, "production")
    model_uri = f"models:/{model_name}/{prod_version.version}"
    local_path = mlflow.artifacts.download_artifacts(model_uri, dst_path=f'{os.getcwd()}/artifacts')
    artifact_uri = f'runs:/{prod_version.run_id}/scaler.joblib'
    _ = mlflow.artifacts.download_artifacts(artifact_uri, dst_path=local_path)
    artifact_uri = f'runs:/{prod_version.run_id}/y_scaler.joblib'
    _ = mlflow.artifacts.download_artifacts(artifact_uri, dst_path=local_path)
    tickers_len = len(tickers)
    with open(local_path + 'tickers_len.txt', 'w') as file:
        file.write(str(tickers_len))

    # Auth to Azure ML Workspace with System-assigned managed identity
    msi_auth = MsiAuthentication()
    subscription_id, resource_group = get_azure_vm_metadata()
    ws = Workspace(subscription_id=subscription_id,
                   resource_group=resource_group,
                   workspace_name="mlserving",
                   auth=msi_auth)

    # Register model version
    model = Model.register(workspace=ws, model_name=model_name, model_path=local_path)
    return ws, model


def get_azure_vm_metadata() -> tuple[str, str]:
    metadata_url = "http://169.254.169.254/metadata/instance?api-version=2021-02-01"
    headers = {
        "Metadata": "true"
    }
    response = requests.get(metadata_url, headers=headers)
    if response.status_code == 200:
        metadata = response.json()
        subscription_id = metadata['compute']['subscriptionId']
        resource_group = metadata['compute']['resourceGroupName']
        return subscription_id, resource_group
    else:
        return "Failed to retrieve metadata", response.status_code


tickers = ['AMZN', 'AXP']
_, resource_group = get_azure_vm_metadata()
account_name = resource_group + '3de90'
container_data = "kafkadata"
