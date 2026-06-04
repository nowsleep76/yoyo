"""
한국 주식 차트 뷰어
개별 종목의 상세 차트를 표시하는 Streamlit 앱
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(
    page_title="한국 주식 차트 뷰어",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 한국 주식 종목 목록
KOREAN_STOCKS = {
    '005930.KS': '삼성전자',
    '000660.KS': 'SK하이닉스',
    '051910.KS': 'LG화학',
    '035420.KS': 'NAVER',
    '035720.KS': 'Kakao',
    '006400.KS': '삼성SDI',
    '005380.KS': '현대자동차',
    '000270.KS': '기아',
    '068270.KS': '셀트리온',
    '028260.KS': 'Samsung C&T',
    '207940.KS': 'SK네트웍스',
    '000810.KS': '삼성화재',
    '009150.KS': '삼성전기',
    '032640.KS': 'LG에너지',
    '047810.KS': '한국항공우주',
    '003550.KS': 'LG전자',
    '015760.KS': 'NSP',
    '011780.KS': 'SK바이오팜',
    '036570.KS': '엔씨소프트',
    '259960.KS': '크래프톤',
}

@st.cache_data(ttl=3600)
def fetch_stock_data(ticker, days=90):
    """주식 데이터 수집"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        stock_data = yf.Ticker(ticker).history(start=start_date, end=end_date)
        return stock_data
    except Exception as e:
        st.error(f"데이터를 불러올 수 없습니다: {e}")
        return None

def create_candlestick_chart(df, title):
    """캔들스틱 차트 생성"""
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        increasing=dict(line=dict(color='#e74c3c'), fillcolor='#e74c3c'),
        decreasing=dict(line=dict(color='#27ae60'), fillcolor='#27ae60'),
    )])

    fig.update_layout(
        title=title,
        yaxis_title='가격 (원)',
        xaxis_title='날짜',
        template='plotly_white',
        height=500,
        hovermode='x unified',
        xaxis_rangeslider_visible=False,
        font=dict(size=12)
    )

    return fig

def create_volume_chart(df):
    """거래량 차트"""
    colors = ['#e74c3c' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#27ae60'
              for i in range(len(df))]

    fig = go.Figure(data=[go.Bar(
        x=df.index,
        y=df['Volume'],
        marker=dict(color=colors),
        name='거래량'
    )])

    fig.update_layout(
        title='거래량',
        yaxis_title='거래량',
        xaxis_title='날짜',
        template='plotly_white',
        height=300,
        showlegend=False,
        hovermode='x unified',
        font=dict(size=12)
    )

    return fig

def main():
    # 헤더
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1>📈 한국 주식 차트 뷰어</h1>
        <p style="font-size: 16px; color: #888;">개별 종목의 상세 차트 분석</p>
    </div>
    """, unsafe_allow_html=True)

    # 사이드바
    with st.sidebar:
        st.markdown("### ⚙️ 설정")

        # 종목 선택
        selected_company = st.selectbox(
            "종목 선택",
            options=list(KOREAN_STOCKS.values()),
            index=0
        )

        # 선택된 종목의 티커 찾기
        selected_ticker = [k for k, v in KOREAN_STOCKS.items() if v == selected_company][0]

        # 기간 설정
        days = st.slider("분석 기간 (일)", min_value=7, max_value=365, value=90)

        # 새로고침
        st.markdown("---")
        if st.button("🔄 데이터 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        st.markdown("### 📊 정보")
        st.info(f"""
        **선택된 종목**: {selected_company}

        **티커**: {selected_ticker}

        **업데이트**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)

    # 데이터 수집
    stock_data = fetch_stock_data(selected_ticker, days)

    if stock_data is None or stock_data.empty:
        st.error("❌ 데이터를 불러올 수 없습니다.")
        return

    # 주요 통계
    st.markdown("### 📊 주요 통계")

    col1, col2, col3, col4 = st.columns(4)

    latest = stock_data.iloc[-1]
    previous = stock_data.iloc[-2] if len(stock_data) > 1 else latest

    price_change = ((latest['Close'] - previous['Close']) / previous['Close'] * 100) if previous['Close'] > 0 else 0

    with col1:
        st.metric(
            "현재가",
            f"₩{latest['Close']:,.0f}",
            f"{price_change:+.2f}%"
        )

    with col2:
        st.metric(
            "고가",
            f"₩{stock_data['High'].max():,.0f}"
        )

    with col3:
        st.metric(
            "저가",
            f"₩{stock_data['Low'].min():,.0f}"
        )

    with col4:
        avg_volume = stock_data['Volume'].mean()
        st.metric(
            "평균 거래량",
            f"{avg_volume:,.0f}"
        )

    st.markdown("---")

    # 차트
    st.markdown("### 📈 가격 차트")
    st.plotly_chart(
        create_candlestick_chart(stock_data, f"{selected_company} 캔들스틱 차트"),
        use_container_width=True
    )

    st.markdown("### 📊 거래량 차트")
    st.plotly_chart(
        create_volume_chart(stock_data),
        use_container_width=True
    )

    st.markdown("---")

    # 상세 데이터 테이블
    st.markdown("### 📋 상세 데이터")

    display_df = stock_data.copy().reset_index()
    display_df.columns = ['날짜', '시가', '고가', '저가', '종가', '거래량', '배당금']

    display_df['날짜'] = display_df['날짜'].dt.strftime('%Y-%m-%d')

    st.dataframe(
        display_df.sort_values('날짜', ascending=False),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # 푸터
    st.markdown("""
    <div style="text-align: center; color: #888; font-size: 12px; padding: 20px 0;">
        <p>📈 한국 주식 차트 뷰어 | Powered by Streamlit & yfinance</p>
        <p>💡 이 정보는 투자 조언이 아닙니다. 투자 결정은 신중하게 진행하세요.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
