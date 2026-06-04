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
    '003550.KS',  # 구글?
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
        print(f"  [{i:2}/{len(krx_stocks)}] {ticker}...", end='')
        data = yf.download(ticker, period='1mo', progress=False)
        if len(data) > 0:
            # 올바른 방식으로 데이터 접근
            avg_volume = int(data[('Volume', ticker)].mean())
            latest_volume = int(data[('Volume', ticker)].iloc[-1])
            latest_date = str(data.index[-1].strftime('%Y-%m-%d'))
            latest_price = float(data[('Close', ticker)].iloc[-1])

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
        print(f" ERROR: {str(e)[:30]}")

if len(volume_data) == 0:
    print("\nError: No data collected")
else:
    # DataFrame 생성 및 정렬
    df = pd.DataFrame(volume_data)
    df_sorted = df.sort_values('latest_vol', ascending=False).reset_index(drop=True)

    print("\n" + "="*115)
    print("국내 주식 거래량 TOP 20 (최신거래량 기준)")
    print("="*115)

    top_20 = df_sorted.head(20)
    header = f"{'순위':<4} {'티커':<12} {'현재가':>11} {'평균거래량':>15} {'최신거래량':>15} {'조회일자':<11}"
    print(header)
    print("-"*115)

    for rank, (_, row) in enumerate(top_20.iterrows(), 1):
        print(f"{rank:<4} {row['ticker']:<12} {row['price']:>11,.0f} {row['avg_vol']:>15,} {row['latest_vol']:>15,} {row['date']:<11}")

    print("="*115)
    print(f"\n수집 완료: {len(df_sorted)}개 종목")
    print(f"조회 기준: 최근 1개월 데이터 (최신거래량 기준 정렬)")
