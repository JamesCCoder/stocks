import time
import os
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
from app.config import settings

ts = TimeSeries(key=settings.API_KEY, output_format='pandas')

def get_daily_data(symbol: str):
    data, meta_data = ts.get_daily(symbol=symbol, outputsize='full')
    data.index = pd.to_datetime(data.index)
    return data


def get_daily_data_for_symbol(symbol: str, folder_name: str):
    file_path = os.path.join(folder_name, f'{symbol}_daily_data.csv')
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No data found for symbol: {symbol}")
    
    df = pd.read_csv(file_path)
    df['Symbol'] = symbol
    return df.to_dict(orient='records')