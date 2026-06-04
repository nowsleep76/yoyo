"""
한국 주식 거래량 기준 상승률 분석 대시보드
Streamlit 웹 대시보드
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys

# 페이지 설정
st.set_page_config(
    page_title="한국 주식 분석 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 한국 주식 시가총액 상위 종목
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
def fetch_stock_data(days=7):
    """주식 데이터 수집"""
    results = []

    with st.spinner('📈 데이터 수집 중...'):
        for ticker, company_name in KOREAN_STOCKS.items():
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)

                stock_data = yf.Ticker(ticker).history(start=start_date, end=end_date)

                if len(stock_data) < 2:
                    continue

                today = stock_data.iloc[-1]
                yesterday = stock_data.iloc[-2]

                today_close = today['Close']
                today_volume = today['Volume']
                yesterday_close = yesterday['Close']
                yesterday_volume = yesterday['Volume']

                # 계산
                price_change = ((today_close - yesterday_close) / yesterday_close) * 100
                volume_change = ((today_volume - yesterday_volume) / yesterday_volume) * 100
                weighted_score = price_change * (today_volume / 1000000)

                results.append({
                    'ticker': ticker,
                    'company': company_name,
                    'price': today_close,
                    'price_change': price_change,
                    'volume': today_volume,
                    'volume_change': volume_change,
                    'weighted_score': weighted_score,
                    'history': stock_data['Close']
                })
            except Exception as e:
                continue

    return pd.DataFrame(results).sort_values('weighted_score', ascending=False)

def create_ranking_chart(df):
    """순위 차트 생성"""
    top_10 = df.head(10)

    fig = go.Figure()

    colors = ['#e74c3c' if x > 0 else '#27ae60' for x in top_10['price_change']]

    fig.add_trace(go.Bar(
        y=top_10['company'],
        x=top_10['price_change'],
        orientation='h',
        marker=dict(color=colors),
        text=[f"{x:.2f}%" for x in top_10['price_change']],
        textposition='outside',
        name='상승률'
    ))

    fig.update_layout(
        title="거래량 기준 상승률 TOP 10",
        xaxis_title="상승률 (%)",
        yaxis_title="회사명",
        height=500,
        showlegend=False,
        hovermode='closest'
    )

    return fig

def create_volume_chart(df):
    """거래량 변화 차트"""
    top_10 = df.head(10)

    fig = go.Figure()

    colors = ['#3498db' if x > 0 else '#95a5a6' for x in top_10['volume_change']]

    fig.add_trace(go.Bar(
        y=top_10['company'],
        x=top_10['volume_change'],
        orientation='h',
        marker=dict(color=colors),
        text=[f"{x:.2f}%" for x in top_10['volume_change']],
        textposition='outside',
        name='거래량 변화'
    ))

    fig.update_layout(
        title="거래량 변화율 TOP 10",
        xaxis_title="거래량 변화율 (%)",
        yaxis_title="회사명",
        height=500,
        showlegend=False,
        hovermode='closest'
    )

    return fig

def create_score_chart(df):
    """스코어 차트 (거래량 가중 상승률)"""
    top_10 = df.head(10)

    fig = go.Figure()

    colors = ['#f39c12' if x > 0 else '#bdc3c7' for x in top_10['weighted_score']]

    fig.add_trace(go.Bar(
        y=top_10['company'],
        x=top_10['weighted_score'],
        orientation='h',
        marker=dict(color=colors),
        text=[f"{x:.1f}" for x in top_10['weighted_score']],
        textposition='outside',
        name='스코어'
    ))

    fig.update_layout(
        title="거래량 가중 상승률 스코어 TOP 10",
        xaxis_title="스코어",
        yaxis_title="회사명",
        height=500,
        showlegend=False,
        hovermode='closest'
    )

    return fig

def main():
    # 헤더
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1>📊 한국 주식 분석 대시보드</h1>
        <p style="font-size: 16px; color: #888;">거래량 기준 상승률이 높은 주식 실시간 분석</p>
    </div>
    """, unsafe_allow_html=True)

    # 사이드바
    with st.sidebar:
        st.markdown("### ⚙️ 설정")
        days = st.slider("분석 기간 (일)", min_value=1, max_value=30, value=7)
        refresh_button = st.button("🔄 데이터 새로고침", use_container_width=True)

        st.markdown("---")
        st.markdown("### 📊 대시보드 정보")
        st.info(f"""
        - **종목 수**: {len(KOREAN_STOCKS)}개
        - **업데이트**: 실시간
        - **마지막 업데이트**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)

    # 데이터 수집
    if refresh_button:
        st.cache_data.clear()

    df = fetch_stock_data(days)

    if df.empty:
        st.error("❌ 데이터를 수집할 수 없습니다.")
        return

    # 주요 지표
    st.markdown("### 📈 주요 지표")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        top_gainer = df.iloc[0]
        st.metric(
            "🟢 상승률 1위",
            top_gainer['company'],
            f"{top_gainer['price_change']:+.2f}%"
        )

    with col2:
        avg_change = df['price_change'].mean()
        st.metric(
            "📊 평균 상승률",
            f"{avg_change:.2f}%",
            f"{avg_change - df['price_change'].std():.2f}% ~ {avg_change + df['price_change'].std():.2f}%"
        )

    with col3:
        top_volume = df.loc[df['volume_change'].idxmax()]
        st.metric(
            "📢 거래량 증가 1위",
            top_volume['company'],
            f"{top_volume['volume_change']:+.2f}%"
        )

    with col4:
        top_score = df.iloc[0]
        st.metric(
            "⭐ 최고 점수",
            top_score['company'],
            f"{top_score['weighted_score']:.1f}"
        )

    st.markdown("---")

    # 차트
    st.markdown("### 📉 분석 차트")

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(create_ranking_chart(df), use_container_width=True)

    with col2:
        st.plotly_chart(create_volume_chart(df), use_container_width=True)

    st.plotly_chart(create_score_chart(df), use_container_width=True)

    st.markdown("---")

    # 상세 테이블
    st.markdown("### 📋 상세 데이터 (TOP 20)")

    display_df = df.head(20)[['company', 'ticker', 'price', 'price_change', 'volume', 'volume_change', 'weighted_score']].copy()
    display_df.columns = ['회사명', '티커', '현재가 (원)', '상승률 (%)', '거래량', '거래량변화 (%)', '스코어']

    # 스타일링
    def style_dataframe(val):
        if isinstance(val, float):
            if val > 0:
                return 'color: #e74c3c; font-weight: bold;'
            elif val < 0:
                return 'color: #27ae60; font-weight: bold;'
        return ''

    st.dataframe(
        display_df.style.format({
            '현재가 (원)': '{:,.0f}',
            '상승률 (%)': '{:+.2f}%',
            '거래량': '{:,.0f}',
            '거래량변화 (%)': '{:+.2f}%',
            '스코어': '{:.1f}'
        }).map(style_dataframe),
        use_container_width=True
    )

    st.markdown("---")

    # 푸터
    st.markdown("""
    <div style="text-align: center; color: #888; font-size: 12px; padding: 20px 0;">
        <p>📊 한국 주식 분석 대시보드 | Powered by Streamlit & yfinance</p>
        <p>💡 이 정보는 투자 조언이 아닙니다. 투자 결정은 신중하게 진행하세요.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
