# -*- coding: utf-8 -*-
import yfinance as yf

ticker = '005930.KS'

print(f"Downloading {ticker}...")
try:
    data = yf.download(ticker, period='1mo', progress=False)
    print(f"Success! Data shape: {data.shape}")
    print(f"Data type: {type(data)}")
    print(f"Columns: {data.columns.tolist()}")
    print(f"Volume type: {type(data['Volume'])}")
    print(f"Last row Volume: {data['Volume'].iloc[-1]}")
    print(f"Last row Volume type: {type(data['Volume'].iloc[-1])}")
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
