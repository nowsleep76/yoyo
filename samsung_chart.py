import ssl
import os
import warnings
warnings.filterwarnings('ignore')

ssl._create_default_https_context = ssl._create_unverified_context
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

import requests
requests.packages.urllib3.disable_warnings()

# pykrx 세션 패치
import pykrx.website.krx.market.wrap as krx_wrap
_orig_session = requests.Session

class NoVerifySession(requests.Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verify = False

requests.Session = NoVerifySession

from pykrx import stock
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import rcParams
import pandas as pd
from datetime import datetime, timedelta

rcParams['font.family'] = 'Malgun Gothic'
rcParams['axes.unicode_minus'] = False

end = datetime.today().strftime("%Y%m%d")
start = (datetime.today() - timedelta(days=180)).strftime("%Y%m%d")

print(f"삼성전자 데이터 조회 중... ({start} ~ {end})")
df = stock.get_market_ohlcv_by_date(start, end, "005930")

if df.empty:
    print("데이터를 가져올 수 없습니다.")
    exit()

df.index = pd.to_datetime(df.index)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8),
                                 gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
fig.suptitle("삼성전자 (005930) - 최근 6개월", fontsize=16, fontweight='bold')

colors = ['#e74c3c' if c >= o else '#2ecc71'
          for c, o in zip(df['종가'], df['시가'])]

ax1.plot(df.index, df['종가'], color='#3498db', linewidth=1.5, label='종가')
ax1.fill_between(df.index, df['종가'], df['종가'].min(), alpha=0.1, color='#3498db')

ma20 = df['종가'].rolling(20).mean()
ma60 = df['종가'].rolling(60).mean()
ax1.plot(df.index, ma20, color='#e67e22', linewidth=1, linestyle='--', label='MA20')
ax1.plot(df.index, ma60, color='#9b59b6', linewidth=1, linestyle='--', label='MA60')

max_idx = df['종가'].idxmax()
min_idx = df['종가'].idxmin()
ax1.annotate(f"최고 {df['종가'][max_idx]:,.0f}원",
             xy=(max_idx, df['종가'][max_idx]),
             xytext=(10, 10), textcoords='offset points',
             fontsize=8, color='red',
             arrowprops=dict(arrowstyle='->', color='red', lw=1))
ax1.annotate(f"최저 {df['종가'][min_idx]:,.0f}원",
             xy=(min_idx, df['종가'][min_idx]),
             xytext=(10, -20), textcoords='offset points',
             fontsize=8, color='green',
             arrowprops=dict(arrowstyle='->', color='green', lw=1))

ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:,.0f}'))
ax1.set_ylabel("주가 (원)", fontsize=10)
ax1.legend(loc='upper left', fontsize=9)
ax1.grid(True, alpha=0.3)

ax2.bar(df.index, df['거래량'], color=colors, alpha=0.7, width=1)
ax2.set_ylabel("거래량", fontsize=10)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1e6:.1f}M'))
ax2.grid(True, alpha=0.3)

ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
plt.xticks(rotation=45)

current = df['종가'].iloc[-1]
prev = df['종가'].iloc[-2]
change = current - prev
change_pct = change / prev * 100
color = 'red' if change >= 0 else 'blue'

fig.text(0.99, 0.99,
         f"현재가: {current:,.0f}원  {change:+,.0f} ({change_pct:+.2f}%)",
         ha='right', va='top', fontsize=11, color=color, fontweight='bold')

plt.tight_layout()
plt.savefig("d:/DEV/samsung_chart.png", dpi=150, bbox_inches='tight')
print(f"현재가: {current:,.0f}원  변동: {change:+,.0f}원 ({change_pct:+.2f}%)")
print("차트 저장: d:/DEV/samsung_chart.png")
plt.show()
