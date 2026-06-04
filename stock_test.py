# -*- coding: utf-8 -*-
import yfinance as yf

print("Testing yfinance with Samsung Electronics...")
try:
    data = yf.download('005930.KS', period='5d', progress=False)
    print(f"Data fetched successfully: {len(data)} rows")
    print(data[['Close', 'Volume']].tail())
except Exception as e:
    print(f"Error: {e}")
