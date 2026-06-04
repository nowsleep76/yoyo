import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.font_manager as fm
import os

# Windows에서 한글 폰트 설정
system_font_path = 'C:\\Windows\\Fonts'
font_path = os.path.join(system_font_path, 'malgun.ttf')

if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = 'Malgun Gothic'
    print("한글 폰트 설정 완료: Malgun Gothic (맑은고딕)")
else:
    plt.rcParams['font.family'] = 'DejaVu Sans'
    print("Warning: 한글 폰트를 찾을 수 없습니다.")

plt.rcParams['axes.unicode_minus'] = False

# 한국 주식 시가총액 상위 10개 (티커)
korean_stocks = {
    '005930.KS': '삼성전자',
    '000660.KS': 'SK하이닉스',
    '051910.KS': 'LG화학',
    '035420.KS': 'NAVER',
    '035720.KS': 'Kakao',
    '006400.KS': '삼성SDI',
    '005380.KS': '현대자동차',
    '000270.KS': '기아',
    '068270.KS': '셀트리온',
    '028260.KS': 'Samsung C&T'
}

# 1년 전 날짜 계산
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

# 데이터 다운로드
print("\n한국 주식 데이터 다운로드 중...")
data = {}
for ticker, name in korean_stocks.items():
    try:
        print(f"  {name} ({ticker}) 다운로드 중...")
        stock_data = yf.Ticker(ticker).history(start=start_date, end=end_date)
        if not stock_data.empty and 'Close' in stock_data.columns:
            data[name] = stock_data['Close']
    except Exception as e:
        print(f"  {name} 다운로드 실패: {e}")

# 데이터프레임 생성
if not data:
    print("다운로드된 데이터가 없습니다.")
    exit(1)

df = pd.DataFrame(data)

# 정규화 (시작가를 100으로 설정)
normalized_df = (df / df.iloc[0]) * 100

# 차트 그리기
fig, ax = plt.subplots(figsize=(16, 9))
for company in normalized_df.columns:
    ax.plot(normalized_df.index, normalized_df[company], label=company, linewidth=2.5)

ax.set_title('한국 시가총액 상위 10개 회사 - 1년 추세', fontsize=16, fontweight='bold')
ax.set_xlabel('날짜', fontsize=12)
ax.set_ylabel('주가 변화 (시작가 = 100)', fontsize=12)
ax.legend(loc='best', fontsize=11, ncol=2)
ax.grid(True, alpha=0.3)
ax.tick_params(axis='x', rotation=45)
plt.tight_layout()

# 차트 저장
plt.savefig('korean_top10_stock_chart.png', dpi=300, bbox_inches='tight')
print("\n차트가 'korean_top10_stock_chart.png'로 저장되었습니다.")

# 기본 통계 출력
print("\n\n=== 1년간 한국 주식 시가총액 상위 10개 변화 통계 ===")
print(f"{'회사명':<18} {'시작가':<15} {'현재가':<15} {'변화율(%)':<12}")
print("-" * 65)
for company in df.columns:
    start_price = df[company].iloc[0]
    end_price = df[company].iloc[-1]
    change_pct = ((end_price - start_price) / start_price) * 100
    print(f"{company:<18} {start_price:<15.0f} {end_price:<15.0f} {change_pct:>10.2f}%")

plt.show()
