import os
import pandas as pd
from fastapi import APIRouter, HTTPException
from app.models.stock import DownloadRequest
from app.utils.alpha_vantage import get_daily_data
from stocks import allStocks

router = APIRouter()

# 初始化全局变量
total_stocks = len(allStocks)
completed_count = 0
success_count = 0
failure_count = 0
no_update_needed_count = 0

@router.post("/download_all_stocks")
async def download_all_stocks(request: DownloadRequest):
    global total_stocks, completed_count, success_count, failure_count, no_update_needed_count

    folder_name = request.folder_name

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    completed_count = 0
    success_count = 0
    failure_count = 0
    no_update_needed_count = 0

    for symbol in allStocks:
        file_name = os.path.join(folder_name, f'{symbol}_data.csv')
        need_update = False
        start_date = None

        if os.path.exists(file_name):
            existing_data = pd.read_csv(file_name, index_col=0, parse_dates=True)

            if existing_data.empty:
                need_update = True
            else:
                last_date = existing_data.index.max()
                yesterday = (pd.Timestamp.now() - pd.Timedelta(days=1)).normalize()
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

@router.get("/summary")
async def summary():
    global total_stocks, completed_count, success_count, failure_count, no_update_needed_count

    return {
        "total_completed": completed_count,
        "successful_downloads": success_count,
        "failed_downloads": failure_count,
        "no_update_needed": no_update_needed_count
    }