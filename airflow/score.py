import json
import joblib
import numpy as np
import mlflow.pyfunc
from azureml.core.model import Model


def init():
    global model
    global scaler
    global y_scaler
    model_path = Model.get_model_path('LSTM_Attention_stock_price_regression')
    model = mlflow.pyfunc.load_model(model_path)
    scaler = joblib.load(model_path + 'scaler.joblib')
    y_scaler = joblib.load(model_path + 'y_scaler.joblib')


def run(raw_data):
    data = json.loads(raw_data)
    array = np.array(data)
    data_to_scale = array[:, :, 2:].reshape(-1, array.shape[-1] - 2)
    scaled_data = scaler.transform(data_to_scale)
    array[:, :, 2:] = scaled_data.reshape(array.shape[0], array.shape[1], -1)
    result = model.predict(array)
    result = y_scaler.inverse_transform(result)
    result = json.dumps(result.tolist())
    return result
