import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import io

# Windows UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ==================== 이메일 설정 ====================
from email_config import (
    SENDER_EMAIL,
    SENDER_PASSWORD,
    RECIPIENT_EMAIL,
    SMTP_SERVER,
    SMTP_PORT
)
# =====================================================

# 한국 주식 시가총액 상위 종목들
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

def get_today_stock_data():
    """오늘 하루 거래량 기준 상승률이 높은 주식 찾기"""
    print(f"\n{'='*70}")
    print(f"📊 한국 주식 일일 분석 리포트 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    results = []

    for ticker, company_name in korean_stocks.items():
        try:
            # 1주일 데이터 가져오기 (오늘 포함)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            stock_data = yf.Ticker(ticker).history(start=start_date, end=end_date)

            if len(stock_data) < 2:
                continue

            # 어제와 오늘 데이터
            today = stock_data.iloc[-1]
            yesterday = stock_data.iloc[-2]

            today_close = today['Close']
            today_volume = today['Volume']
            yesterday_close = yesterday['Close']
            yesterday_volume = yesterday['Volume']

            # 계산
            price_change = ((today_close - yesterday_close) / yesterday_close) * 100
            volume_change = ((today_volume - yesterday_volume) / yesterday_volume) * 100

            # 거래량 가중 상승률
            weighted_score = price_change * (today_volume / 1000000)

            results.append({
                'ticker': ticker,
                'company': company_name,
                'price': today_close,
                'price_change': price_change,
                'volume': today_volume,
                'volume_change': volume_change,
                'weighted_score': weighted_score
            })

        except Exception as e:
            print(f"⚠️  {company_name} 데이터 조회 실패: {e}")

    # 거래량 가중 상승률로 정렬
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('weighted_score', ascending=False)

    return results_df.head(10)

def format_html_email(top_stocks):
    """이메일 HTML 형식으로 포맷팅"""
    html = f"""
    <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 20px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 5px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .header p {{ margin: 5px 0 0 0; font-size: 14px; }}
                .date {{ color: #999; font-size: 12px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th {{ background-color: #f0f0f0; padding: 12px; text-align: left; border-bottom: 2px solid #667eea; font-weight: bold; }}
                td {{ padding: 12px; border-bottom: 1px solid #eee; }}
                tr:hover {{ background-color: #f9f9f9; }}
                .positive {{ color: #e74c3c; font-weight: bold; }}
                .negative {{ color: #27ae60; font-weight: bold; }}
                .neutral {{ color: #95a5a6; }}
                .rank {{ font-weight: bold; color: #667eea; }}
                .footer {{ text-align: center; margin-top: 20px; color: #999; font-size: 12px; border-top: 1px solid #eee; padding-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 한국 주식 거래량 기준 상승률</h1>
                    <p class="date">{datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}</p>
                </div>

                <table>
                    <thead>
                        <tr style="background-color: #667eea; color: white;">
                            <th style="border: none;">순위</th>
                            <th style="border: none;">회사명 (티커)</th>
                            <th style="border: none; text-align: right;">현재가</th>
                            <th style="border: none; text-align: right;">상승률</th>
                            <th style="border: none; text-align: right;">거래량</th>
                            <th style="border: none; text-align: right;">거래량 변화</th>
                            <th style="border: none; text-align: right;">스코어</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for idx, (_, row) in enumerate(top_stocks.iterrows(), 1):
        change_class = "positive" if row['price_change'] > 0 else "negative" if row['price_change'] < 0 else "neutral"
        vol_change_class = "positive" if row['volume_change'] > 0 else "negative" if row['volume_change'] < 0 else "neutral"

        html += f"""
                        <tr>
                            <td class="rank">{idx}</td>
                            <td><strong>{row['company']}</strong><br/><small style="color: #999;">({row['ticker']})</small></td>
                            <td style="text-align: right;">{row['price']:,.0f}원</td>
                            <td style="text-align: right;"><span class="{change_class}">{row['price_change']:+.2f}%</span></td>
                            <td style="text-align: right;">{row['volume']:,.0f}</td>
                            <td style="text-align: right;"><span class="{vol_change_class}">{row['volume_change']:+.2f}%</span></td>
                            <td style="text-align: right;"><strong>{row['weighted_score']:,.0f}</strong></td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>

                <div class="footer">
                    <p>📈 거래량이 높으면서 상승률도 높은 종목을 자동으로 분석합니다.</p>
                    <p>💡 이 정보는 투자 조언이 아닙니다. 투자 결정은 신중하게 진행하세요.</p>
                    <p>자동생성 보고서 | Daily Stock Alert System</p>
                </div>
            </div>
        </body>
    </html>
    """
    return html

def send_email(subject, html_content):
    """이메일 전송"""
    try:
        print(f"\n📧 이메일 전송 중...")
        print(f"   발신: {SENDER_EMAIL}")
        print(f"   수신: {RECIPIENT_EMAIL}")

        # 이메일 구성
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL

        # HTML 부분
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        # Gmail SMTP 연결 및 전송
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        print("✅ 이메일 전송 완료!\n")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ 이메일 인증 실패")
        print("   - Gmail 계정과 비밀번호를 확인하세요")
        print("   - 2단계 인증이 활성화된 경우 앱 비밀번호를 사용하세요")
        print("   - https://myaccount.google.com/apppasswords\n")
        return False

    except Exception as e:
        print(f"❌ 이메일 전송 실패: {e}\n")
        return False

def main():
    # 이메일 설정 확인
    if not SENDER_PASSWORD:
        print("❌ 오류: SENDER_PASSWORD가 설정되지 않았습니다.")
        print("\n설정 방법:")
        print("1. Gmail 계정에서 2단계 인증 활성화")
        print("2. https://myaccount.google.com/apppasswords 접속")
        print("3. 앱 비밀번호 생성 (Python/Mail)")
        print("4. 생성된 비밀번호를 SENDER_PASSWORD에 붙여넣기\n")
        return

    print("📈 한국 주식 거래량 기준 상승률 분석 중...")

    # 주식 데이터 수집 및 분석
    top_stocks = get_today_stock_data()

    if len(top_stocks) == 0:
        print("❌ 분석할 데이터가 없습니다.")
        return

    # 결과 콘솔 출력
    print("="*70)
    print("TOP 10 (거래량 기준 상승률)")
    print("="*70)
    for idx, (_, row) in enumerate(top_stocks.iterrows(), 1):
        emoji = "🟢" if row['price_change'] > 0 else "🔴"
        print(f"\n{idx}. {emoji} {row['company']} ({row['ticker']})")
        print(f"   현재가: {row['price']:,.0f}원")
        print(f"   상승률: {row['price_change']:+.2f}%")
        print(f"   거래량: {row['volume']:,.0f}")
        print(f"   거래량 변화: {row['volume_change']:+.2f}%")
        print(f"   스코어: {row['weighted_score']:,.0f}")

    # HTML 이메일 생성
    subject = f"[주식 알림] 거래량 기준 상승률 TOP 10 - {datetime.now().strftime('%Y-%m-%d')}"
    html_content = format_html_email(top_stocks)

    # 이메일 전송
    send_email(subject, html_content)

if __name__ == "__main__":
    main()
