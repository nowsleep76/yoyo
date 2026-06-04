# -*- coding: utf-8 -*-
import yfinance as yf
import pandas as pd

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
    '009150.KS',  # 삼성전기
    '011070.KS',  # LG이노텍
    '078000.KS',  # 지투지글로벌
]

volume_data = []

print("국내 주식 거래량 데이터 수집 중...")

for i, ticker in enumerate(krx_stocks, 1):
    try:
        print(f"  [{i}/{len(krx_stocks)}] {ticker} 수집 중...", end='')
        data = yf.download(ticker, period='1mo', progress=False)
        if len(data) > 0:
            # Volume 열의 마지막 값 추출 (Series에서 scalar 값으로)
            avg_volume = int(data['Volume'].mean())
            latest_volume = int(data['Volume'].iloc[-1])
            latest_date = str(data.index[-1].strftime('%Y-%m-%d'))
            latest_price = float(data['Close'].iloc[-1])

            volume_data.append({
                'ticker': ticker,
                'avg_vol': avg_volume,
                'latest_vol': latest_volume,
                'date': latest_date,
                'price': latest_price
            })
            print(" OK")
        else:
            print(" NO DATA")
    except Exception as e:
        print(f" ERROR")

if len(volume_data) == 0:
    print("Error: No data collected")
else:
    # DataFrame 생성 및 정렬
    df = pd.DataFrame(volume_data)
    df_sorted = df.sort_values('latest_vol', ascending=False).reset_index(drop=True)

    print("\n" + "="*110)
    print("국내 주식 거래량 TOP 20 (최신거래량 기준)")
    print("="*110)

    top_20 = df_sorted.head(20)
    for rank, (_, row) in enumerate(top_20.iterrows(), 1):
        print(f"{rank:2}. {row['ticker']:<12} | 현재가: {row['price']:>10,.0f} | 평균거래량: {row['avg_vol']:>12,} | 최신거래량: {row['latest_vol']:>12,}")

    print("="*110)
    print(f"\n수집된 총 주식 수: {len(df_sorted)}")
    print(f"조회 기준: 최근 1개월 거래량 데이터")
