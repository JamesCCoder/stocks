import os
import pandas as pd
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Query
from app.models.stock import DownloadRequest
from app.utils.alpha_vantage import get_daily_data
from app.utils.alpha_vantage import get_daily_data_for_symbol
from stocks_test import allStocks
from stocks import allStocks1
from app.utils.globals import (
    total_stocks,
    completed_count,
    success_count,
    failure_count,
    no_update_needed_count,
    stocks_data,
)

router = APIRouter()

@router.post("/download_all_stocks")
async def download_all_stocks(request: DownloadRequest):
    global total_stocks, completed_count, success_count, failure_count, no_update_needed_count
    
    folder_name = request.folder_name

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    total_stocks = len(allStocks)
    completed_count = 0
    success_count = 0
    failure_count = 0
    no_update_needed_count = 0

    today = pd.Timestamp.now()
    # 调整yesterday变量，考虑周六和周日的情况
    if today.dayofweek == 5:  # 如果今天是周六
        yesterday = today - pd.Timedelta(days=1)
    elif today.dayofweek == 6:  # 如果今天是周日
        yesterday = today - pd.Timedelta(days=2)
    else:
        yesterday = today - pd.Timedelta(days=1)

    yesterday = yesterday.normalize()
    

    for symbol in allStocks:
        file_name = os.path.join(folder_name, f'{symbol}_daily_data.csv')
        need_update = False
        start_date = None

        if os.path.exists(file_name):
            existing_data = pd.read_csv(file_name, index_col=0, parse_dates=True)

            if existing_data.empty:
                need_update = True
            else:
                last_date = existing_data.index.max()
                if last_date >= yesterday:
                    no_update_needed_count += 1
                    completed_count += 1
                    print(f"No update needed for {symbol}")
                    print(f"{completed_count}/{total_stocks} completed")
                    continue
                elif last_date < pd.Timestamp.now() - pd.DateOffset(years=1):
                    need_update = True
                    start_date = pd.Timestamp.now() - pd.DateOffset(years=1)
                elif last_date < yesterday:
                    start_date = last_date + pd.Timedelta(days=1)
                    need_update = True
        else:
            need_update = True
            start_date = pd.Timestamp.now() - pd.DateOffset(years=1)

        if need_update:
            try:
                data = get_daily_data(symbol)

                if start_date is not None:
                    data = data[data.index >= start_date]
                else:
                    data = data[data.index >= pd.Timestamp.now() - pd.DateOffset(years=1)]

                if os.path.exists(file_name) and not existing_data.empty:
                    data = pd.concat([data, existing_data])
                    data = data[~data.index.duplicated(keep='first')]

                data.to_csv(file_name)
                success_count += 1
                completed_count += 1
                print(f"Data for {symbol} saved to {file_name}")
                print(f"{completed_count}/{total_stocks} completed")
            except Exception as e:
                failure_count += 1
                completed_count += 1
                print(f"Error fetching data for {symbol}: {e}")
                print(f"{completed_count}/{total_stocks} completed")
        else:
            no_update_needed_count += 1
            completed_count += 1
            print(f"No update needed for {symbol}")
            print(f"{completed_count}/{total_stocks} completed")

    return {
        "total_completed": completed_count,
        "successful_downloads": success_count,
        "failed_downloads": failure_count,
        "no_update_needed": no_update_needed_count
    }


@router.get("/latest_stock_data")
async def get_latest_stock_data(folder_name: str = Query(..., description="The folder name where CSV files are stored")):
    folder_path = os.path.join(os.getcwd(), folder_name)
    
    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail="Folder not found")

    latest_data = []
    for symbol in allStocks1:
        file_name = os.path.join(folder_path, f'{symbol}_daily_data.csv')
        if os.path.exists(file_name):
            data = pd.read_csv(file_name, index_col=0, parse_dates=True)
            if not data.empty:
                latest_day = data.index.max()
                latest_data.append({
                    "symbol": symbol,
                    "date": latest_day.strftime('%Y-%m-%d'),
                    "open": data.loc[latest_day, "1. open"],
                    "high": data.loc[latest_day, "2. high"],
                    "low": data.loc[latest_day, "3. low"],
                    "close": data.loc[latest_day, "4. close"],
                    "volume": data.loc[latest_day, "5. volume"]
                })
    return latest_data


@router.get("/stock_daily_data")
async def get_stock_daily_data(symbol: str, folder_name: str):
    try:
        data = get_daily_data_for_symbol(symbol, folder_name)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))