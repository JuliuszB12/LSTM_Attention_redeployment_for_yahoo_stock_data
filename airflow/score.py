import json
import numpy as np
import mlflow.pyfunc
from azureml.core.model import Model


def init():
    global model
    model_path = Model.get_model_path('LSTM_Attention_stock_price_regression')
    model = mlflow.pyfunc.load_model(model_path)


def run(raw_data):
    data = json.loads(raw_data)
    array = np.array(data)
    result = model.predict(array)
    return result.tolist()
