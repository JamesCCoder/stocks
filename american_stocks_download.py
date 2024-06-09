from config import API_KEY
import os
import time
import pandas as pd
from alpha_vantage.timeseries import TimeSeries

from stocks import allStocks


# 替换成你的 Alpha Vantage API 密钥
api_key = API_KEY

# 创建存储CSV文件的文件夹
folder_name = 'american_stocks_day'
if not os.path.exists(folder_name):
    os.makedirs(folder_name)

# 股票代码列表（示例）
# stock_symbols = ['AAPL']  # 示例股票代码

ts = TimeSeries(key=api_key, output_format='pandas')

total_stocks = 5590  # 总数为 5592
completed_count = 0  # 初始化完成数
success_count = 0  # 成功下载数
failure_count = 0  # 失败下载数
no_update_needed_count = 0  # 不需要更新数

# 获取每只股票的历史数据并保存或更新CSV文件
for symbol in allStocks:
    file_name = os.path.join(folder_name, f'{symbol}_data.csv')
    need_update = False
    start_date = None

    # 检查CSV文件是否存在
    if os.path.exists(file_name):
        existing_data = pd.read_csv(file_name, index_col=0, parse_dates=True)

        # 检查文件是否为空
        if existing_data.empty:
            need_update = True
        else:
            # 检查现有数据是否包含昨天的数据
            last_date = existing_data.index.max()
            yesterday = (pd.Timestamp.now() - pd.Timedelta(days=1)).normalize()
            if last_date >= yesterday:
                no_update_needed_count += 1
                completed_count += 1
                print(f"No update needed for {symbol}")
                print(f"{completed_count}/{total_stocks} completed")
                continue  # 跳过该股票代码，处理下一个
            elif last_date < pd.Timestamp.now() - pd.DateOffset(years = 1):
                need_update = True
                start_date = pd.Timestamp.now() - pd.DateOffset(years = 1)
            elif last_date < yesterday:
                # 如果最近的数据少于两周，计算需要补充的数据日期范围
                start_date = last_date + pd.Timedelta(days=1)
                need_update = True
    else:
        need_update = True
        start_date = pd.Timestamp.now() - pd.DateOffset(years = 1)

    if need_update:
        try:
            # 获取每日数据
            data, meta_data = ts.get_daily(symbol=symbol, outputsize='full')
            data.index = pd.to_datetime(data.index)

            # 选择需要的日期范围的数据
            if start_date is not None:
                data = data[data.index >= start_date]
            else:
                data = data[data.index >= pd.Timestamp.now() - pd.DateOffset(years = 1)]

            # 如果文件存在且不为空，将新数据追加到现有文件
            if os.path.exists(file_name) and not existing_data.empty:
                data = pd.concat([data, existing_data])  # 新数据在前
                data = data[~data.index.duplicated(keep='first')]

            # 保存到CSV文件
            data.to_csv(file_name)
            success_count += 1
            completed_count += 1
            print(f"Data for {symbol} saved to {file_name}")
            print(f"{completed_count}/{total_stocks} completed")
            # # 延迟以避免超过API请求限制
            # time.sleep(12)
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

print("\nSummary:")
print(f"Total completed: {completed_count}")
print(f"Successful downloads: {success_count}")
print(f"Failed downloads: {failure_count}")
print(f"No update needed: {no_update_needed_count}")