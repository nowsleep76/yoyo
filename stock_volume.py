# -*- coding: utf-8 -*-
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# 주요 KRX 주식 티커들
krx_stocks = [
    '005930.KS',  # 삼성전자
    '000660.KS',  # SK하이닉스
    '051910.KS',  # LG화학
    '035420.KS',  # NAVER
    '035720.KS',  # 카카오
    '068270.KS',  # 셀트리온
    '207940.KS',  # SM엔터테인먼트
    '012330.KS',  # 현대모비스
    '066570.KS',  # LG전자
    '096770.KS',  # SK이노베이션
    '323410.KS',  # 카카오뱅크
    '055550.KS',  # 신한지주
    '034020.KS',  # 두산중공업
    '000810.KS',  # 삼성화재
    '267250.KS',  # NHN
    '032640.KS',  # LG
    '006400.KS',  # 삼성SDI
    '010950.KS',  # S-Oil
    '011200.KS',  # HMM
    '030200.KS',  # KT
    '000120.KS',  # CJ대한통운
    '003550.KS',  # LG
    '042700.KS',  # 한미반도체
    '000100.KS',  # SK에너지
    '017670.KS',  # SK텔레콤
    '016360.KS',  # 삼성증권
    '161390.KS',  # 한국타이어
    '000990.KS',  # GS홈쇼핑
    '011070.KS',  # LG이노텍
    '009150.KS',  # 삼성전기
]

volume_data = []

print("국내 주식 거래량 데이터 수집 중...")

for ticker in krx_stocks:
    try:
        data = yf.download(ticker, period='1mo', progress=False)
        if len(data) > 0:
            avg_volume = data['Volume'].mean()
            latest_volume = data['Volume'].iloc[-1]
            latest_date = data.index[-1].strftime('%Y-%m-%d')

            volume_data.append({
                'ticker': ticker,
                'avg_vol': int(avg_volume),
                'latest_vol': int(latest_volume),
                'date': latest_date
            })
    except Exception as e:
        pass

# DataFrame 생성 및 정렬
df = pd.DataFrame(volume_data)
df_sorted = df.sort_values('latest_vol', ascending=False).reset_index(drop=True)
df_sorted['rank'] = range(1, len(df_sorted) + 1)

print("\n" + "="*100)
print("국내 주식 거래량 TOP 20 (최신거래량 기준)")
print("="*100)

top_20 = df_sorted.head(20)
print(f"{'순위':<4} {'티커':<12} {'평균거래량':>15} {'최신거래량':>15} {'최신날짜':<12}")
print("-"*100)

for _, row in top_20.iterrows():
    print(f"{int(row['rank']):<4} {row['ticker']:<12} {row['avg_vol']:>15,} {row['latest_vol']:>15,} {row['date']:<12}")

print("="*100)
