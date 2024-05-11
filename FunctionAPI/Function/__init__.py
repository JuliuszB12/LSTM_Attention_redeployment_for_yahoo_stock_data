import azure.functions as func
import os
import json
import joblib
import mlflow
from mlflow.tracking import MlflowClient
from azureml.core.authentication import MsiAuthentication
from azureml.core.webservice import AksWebservice
from azureml.core import Workspace


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Try to get JSON from the request body
        req_body = req.get_json()
    except ValueError:
        # If JSON parsing fails, return a 400 error
        return func.HttpResponse("Invalid JSON", status_code=400)

    name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello {name}!", status_code=200)
    else:
        return func.HttpResponse("Please pass a name in the request body", status_code=400)
