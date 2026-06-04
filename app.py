import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(
    page_title="홈앤쇼핑 일일 매출 현황",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS로 한글 폰트 설정
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
    * {
        font-family: 'Noto Sans KR', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# 데이터 로드
@st.cache_data
def load_data():
    df = pd.read_csv('daily_sales.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    return df

df = load_data()

# 페이지 제목
st.title('🏪 홈앤쇼핑 일일 매출 현황')

# 최신 두 날짜 구하기
latest_date = df['Date'].max()
previous_date = latest_date - timedelta(days=1)

# 오늘과 어제 데이터
today_sales = df[df['Date'] == latest_date]['Sales'].sum()
yesterday_sales = df[df['Date'] == previous_date]['Sales'].sum()
growth_rate = ((today_sales - yesterday_sales) / yesterday_sales * 100) if yesterday_sales > 0 else 0

# 형식화 함수
def format_won(value):
    """숫자를 원화 형식으로 변환"""
    return f"₩{value:,.0f}"

def format_percent(value):
    """퍼센트 형식"""
    sign = "+" if value >= 0 else "-"
    return f"{sign}{abs(value):.1f}%"

# 메트릭 카드 표시
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "오늘 매출",
        format_won(today_sales)
    )

with col2:
    st.metric(
        "어제 매출",
        format_won(yesterday_sales)
    )

with col3:
    st.metric(
        "어제 대비 증감률",
        format_percent(growth_rate)
    )

st.divider()

# 일별 매출 추이 - 주식 차트 데이터 생성
daily_ohlc = df.groupby('Date')['Sales'].agg(['min', 'max', 'first', 'last']).reset_index()
daily_ohlc.columns = ['Date', 'Low', 'High', 'Open', 'Close']

st.subheader("📈 일별 매출 추이 (주식 차트)")

fig_stock = go.Figure(data=[go.Candlestick(
    x=daily_ohlc['Date'],
    open=daily_ohlc['Open'],
    high=daily_ohlc['High'],
    low=daily_ohlc['Low'],
    close=daily_ohlc['Close'],
    increasing=dict(line=dict(color='#70AD47'), fillcolor='#70AD47'),
    decreasing=dict(line=dict(color='#ED7D31'), fillcolor='#ED7D31'),
    hovertext=[f"날짜: {date.strftime('%Y-%m-%d')}<br>시가: ₩{open_:,.0f}<br>고가: ₩{high_:,.0f}<br>저가: ₩{low_:,.0f}<br>종가: ₩{close_:,.0f}"
               for date, open_, high_, low_, close_ in
               zip(daily_ohlc['Date'], daily_ohlc['Open'], daily_ohlc['High'], daily_ohlc['Low'], daily_ohlc['Close'])],
    hoverinfo='text'
)])

fig_stock.update_layout(
    title='',
    yaxis_title='매출',
    xaxis_title='날짜',
    template='plotly_white',
    height=350,
    margin=dict(l=0, r=0, t=0, b=0),
    font=dict(family='Noto Sans KR', size=12),
    yaxis=dict(
        tickformat=',.0f',
        tickprefix='₩',
        gridcolor='rgba(200, 200, 200, 0.2)'
    ),
    xaxis=dict(
        gridcolor='rgba(200, 200, 200, 0.2)'
    ),
    hovermode='x unified'
)

st.plotly_chart(fig_stock, use_container_width=True)

st.divider()

# 카테고리별 매출 비중
category_sales = df.groupby('Category')['Sales'].sum().reset_index().sort_values('Sales', ascending=False)

st.subheader("🎯 카테고리별 매출 비중")

colors = ['#4472C4', '#70AD47', '#FFC000', '#ED7D31', '#A5A5A5']

fig_pie = go.Figure(data=[go.Pie(
    labels=category_sales['Category'],
    values=category_sales['Sales'],
    marker=dict(colors=colors),
    hovertemplate='<b>%{label}</b><br>매출: ₩%{value:,.0f}<br>비중: %{percent}<extra></extra>',
    textposition='inside',
    textinfo='label+percent'
)])

fig_pie.update_layout(
    height=350,
    showlegend=True,
    margin=dict(l=0, r=0, t=0, b=0),
    font=dict(family='Noto Sans KR', size=11),
    legend=dict(
        orientation='v',
        yanchor='middle',
        y=0.5,
        xanchor='left',
        x=1.05
    )
)

fig_pie.update_traces(
    textfont=dict(size=10, color='white', family='Noto Sans KR')
)

st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# 하단 상세 데이터 테이블
st.subheader("📋 일일 카테고리별 매출 현황")

# 테이블용 데이터 정렬 - 모바일용 컬럼 선택
table_data = df.copy()
table_data['Date'] = table_data['Date'].dt.strftime('%Y-%m-%d')
table_data = table_data.sort_values(['Date', 'Category'], ascending=[False, True])

# 모바일용 컬럼 (핵심 정보만)
display_columns = {
    'Date': '날짜',
    'Category': '카테고리',
    'Sales': '매출',
    'OrderCount': '주문건수'
}

table_display = table_data[list(display_columns.keys())].copy()
table_display.columns = display_columns.values()

# 금액 형식화
table_display['매출'] = table_display['매출'].apply(lambda x: f"₩{x:,.0f}")

st.dataframe(
    table_display,
    use_container_width=True,
    hide_index=True,
    height=300
)
