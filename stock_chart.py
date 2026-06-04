import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.dates as mdates

plt.rcParams['font.family'] = 'sans-serif'

# 시가총액 상위 10개 회사 (2024년 기준)
top_10_tickers = ['MSFT', 'AAPL', 'NVDA', 'GOOGL', 'AMZN', 'TSLA', 'META', 'BRK.A', 'AVGO', 'WM']

# 1년 전 날짜 계산
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

# 데이터 다운로드
print("주식 데이터 다운로드 중...")
data = {}
for ticker in top_10_tickers:
    try:
        print(f"  {ticker} 다운로드 중...")
        stock_data = yf.Ticker(ticker).history(start=start_date, end=end_date)
        if not stock_data.empty and 'Close' in stock_data.columns:
            data[ticker] = stock_data['Close']
    except Exception as e:
        print(f"  {ticker} 다운로드 실패: {e}")

# 데이터프레임 생성
if not data:
    print("다운로드된 데이터가 없습니다.")
    exit(1)

df = pd.DataFrame(data)

# 정규화 (시작가를 100으로 설정하여 비교)
normalized_df = (df / df.iloc[0]) * 100

# 차트 그리기
plt.figure(figsize=(14, 8))
for ticker in top_10_tickers:
    if ticker in normalized_df.columns:
        plt.plot(normalized_df.index, normalized_df[ticker], label=ticker, linewidth=2)

plt.title('시가총액 상위 10개 회사 주가 변화 (1년)', fontsize=16, fontweight='bold')
plt.xlabel('날짜', fontsize=12)
plt.ylabel('가격 변화 (시작가 = 100)', fontsize=12)
plt.legend(loc='best', fontsize=10)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()

# 차트 저장
plt.savefig('top10_stock_chart.png', dpi=300, bbox_inches='tight')
print("\n차트가 'top10_stock_chart.png'로 저장되었습니다.")

# 기본 통계 출력
print("\n\n=== 1년간 주가 변화 통계 ===")
print(f"{'회사':<8} {'시작가':<10} {'현재가':<10} {'변화(%)':<10}")
print("-" * 40)
for ticker in top_10_tickers:
    if ticker in df.columns:
        start_price = df[ticker].iloc[0]
        end_price = df[ticker].iloc[-1]
        change_pct = ((end_price - start_price) / start_price) * 100
        print(f"{ticker:<8} ${start_price:<9.2f} ${end_price:<9.2f} {change_pct:>8.2f}%")

plt.show()
