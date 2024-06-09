import time
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
from app.config import settings

ts = TimeSeries(key=settings.API_KEY, output_format='pandas')

def get_daily_data(symbol: str):
    data, meta_data = ts.get_daily(symbol=symbol, outputsize='full')
    data.index = pd.to_datetime(data.index)
    return data
