from typing import Optional
import numpy as np
from sklearn.metrics import mean_squared_error
import mlflow
from mlflow.tracking import MlflowClient


def get_latest_model_version(model_name: str, client: MlflowClient) -> Optional[str]:
    versions = client.search_model_versions(f"name='{model_name}'")
    latest_version = max(versions, key=lambda version: int(version.version))
    if latest_version is not None:
        return latest_version.version
    return None


def compare_and_update_production_stage(model_name: str, mse: float, x_val:
np.ndarray[np.ndarray[np.ndarray[np.float64]]], y_val: np.ndarray[np.float64]) -> str:
    client = MlflowClient()
    try:
        prod_version = client.get_model_version_by_alias(model_name, "production").version
    except mlflow.exceptions.RestException:
        prod_version = None
    if prod_version is not None:
        model_uri = f"models:/{model_name}/{prod_version}"
        loaded_model = mlflow.pyfunc.load_model(model_uri)
        predictions_prev_model = loaded_model.predict(x_val)
        mse_prev_model = mean_squared_error(y_val, predictions_prev_model)
        if mse < mse_prev_model:
            better_version = get_latest_model_version(model_name, client)
            client.set_registered_model_alias(model_name, "production", better_version)
            return 'new_version'
        else:
            return 'old_version'

    else:
        better_version = get_latest_model_version(model_name, client)
        client.set_registered_model_alias(model_name, "production", better_version)
        return 'new_model'
