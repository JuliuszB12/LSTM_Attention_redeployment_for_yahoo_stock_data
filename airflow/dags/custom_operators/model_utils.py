from typing import Callable
import pandas as pd
import numpy as np
from stockstats import wrap
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.layers import Layer, Softmax, Input, LSTM, Dense
import tensorflow.keras.backend as K
from tensorflow.keras.models import Model

model_name = "LSTM_Attention_stock_price_regression"


def preprocess_data(sequence_length: int, read_blob: Callable[[str], pd.DataFrame],  tickers: str, account_name: str, 
                    container_name: str) -> \
        tuple[np.ndarray[np.ndarray[np.ndarray[np.float64]]], np.ndarray[np.float64], MinMaxScaler, MinMaxScaler]:
    """
    | Params:\n
    | sequence_length - length of LSTM time series\n
    | tickers - list of tickers for stock data\n
    | connect_str - connection string for Azure Blob Storage\n
    container_name - n ame of container in Azure Blob Storage
    """
    df = read_blob(account_name, container_name)
    df = df.rename(columns={'timestamp': 'date'})
    df = pd.get_dummies(df, columns=['symbol'], prefix='', prefix_sep='')
    df[tickers] = df[tickers].astype(int)
    lower_tickers = [x.lower() for x in tickers]
    x_lstm = []
    y_lstm = []

    for i in tickers:
        temp_df = df[df[i] == 1].copy()
        if len(temp_df) % sequence_length == 0:
            temp_df = temp_df.iloc[sequence_length-3:]
        elif len(temp_df) % sequence_length == 1:
            temp_df = temp_df.iloc[sequence_length-2:]
        elif len(temp_df) % sequence_length == 2:
            temp_df = temp_df.iloc[sequence_length-1:]
        elif len(temp_df) > sequence_length:
            rows_to_drop = len(temp_df) % sequence_length
            temp_df = temp_df.iloc[rows_to_drop-3:]
        else:
            raise Exception("Too short data")
        temp_df = wrap(temp_df)
        temp_df = temp_df[lower_tickers+['close', 'macd', 'boll_ub', 'boll_lb', 'rsi_30', 'cci_30', 'dx_30',
                                         'close_30_sma', 'close_60_sma', 'aroon']]
        temp_df["Y"] = temp_df['close'].shift(-3)
        temp_df = temp_df.fillna(0)
        temp_df = temp_df.iloc[:-3]
        x_train = temp_df.drop(['Y'], axis=1)
        y_train = temp_df['Y'].to_numpy().reshape(-1, 1)
        scaler = MinMaxScaler()
        columns_to_scale = [col for col in x_train.columns if col not in lower_tickers]
        x_train[columns_to_scale] = scaler.fit_transform(x_train[columns_to_scale])
        y_scaler = MinMaxScaler()
        y_train = y_scaler.fit_transform(y_train)
        for i in range(len(x_train) - sequence_length + 1):
            x_lstm.append(x_train.iloc[i:i + sequence_length].to_numpy())
            y_lstm.append(y_train[i + sequence_length - 1, 0])
    x_lstm = np.array(x_lstm)
    y_lstm = np.array(y_lstm)
    return x_lstm, y_lstm, scaler, y_scaler


class CustomAttention(Layer):
    def __init__(self, **kwargs):
        super(CustomAttention, self).__init__(**kwargs)

    def build(self, input_shape):
        self.W = self.add_weight(name="att_weight", shape=(input_shape[-1], 1),
                                 initializer="normal")
        self.b = self.add_weight(name="att_bias", shape=(input_shape[1], 1),
                                 initializer="zeros")
        super(CustomAttention, self).build(input_shape)

    def call(self, x):
        # Applying a simple attention mechanism
        e = K.tanh(K.dot(x, self.W) + self.b)
        e = K.squeeze(e, axis=-1)
        alpha = Softmax(axis=-1)(e)
        alpha = K.expand_dims(alpha, axis=-1)
        context = x * alpha
        context = K.sum(context, axis=1)
        return context


def build_model(input_shape: tuple[int, int], unit_number: int) -> Model:
    """
    | Params:\n
    | input_shape - length of LSTM time series and input for each time step\n
    unit_number - number of units in LSTM layer
    """
    inputs = Input(shape=input_shape)
    lstm_out = LSTM(unit_number, return_sequences=True)(inputs)  # Return sequences for attention
    attention_out = CustomAttention()(lstm_out)
    outputs = Dense(1)(attention_out)  # Predicting the next stock price
    model = Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model
