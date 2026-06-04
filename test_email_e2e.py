"""
E2E 테스트: 이메일을 통한 거래량 기준 상승률 한국 주식 알림
- Gmail SMTP 연결 테스트
- 이메일 형식 검증
- 실제 이메일 전송 테스트
"""

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

def test_section(title):
    """테스트 섹션 표시"""
    print("\n" + "="*70)
    print(f"🧪 {title}")
    print("="*70)

def test_1_gmail_setup():
    """테스트 1: Gmail 설정 확인"""
    test_section("TEST 1: Gmail 설정")

    print("\n📧 Gmail SMTP 설정 확인...\n")

    print("필수 설정 항목:")
    print("  1. ✅ Gmail 계정 (예: yourmail@gmail.com)")
    print("  2. ✅ 앱 비밀번호 (Gmail 2단계 인증 후 생성)")
    print("  3. ✅ 수신자 이메일 (hbyoo@hnsmall.com)")

    print("\n📋 Gmail 앱 비밀번호 생성 방법:")
    print("  1. https://myaccount.google.com/apppasswords 접속")
    print("  2. 계정 선택 → 앱 선택 (Mail) → 기기 선택 (Windows)")
    print("  3. '생성' 클릭 → 16자리 비밀번호 복사")
    print("  4. 띄어쓰기 제거 후 사용")

    sender_email = input("\n📧 발신 Gmail 주소를 입력하세요: ").strip()
    sender_password = input("🔐 Gmail 앱 비밀번호를 입력하세요: ").strip()

    if not sender_email or not sender_password:
        print("\n❌ 필수 정보가 입력되지 않았습니다.")
        return None, None

    return sender_email, sender_password

def test_2_smtp_connection(sender_email, sender_password):
    """테스트 2: SMTP 연결 테스트"""
    test_section("TEST 2: Gmail SMTP 연결")

    print(f"\n🔗 Gmail SMTP 연결 중... ({sender_email})")
    print("   서버: smtp.gmail.com:587")

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.quit()

        print("✅ SMTP 연결 성공!")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ 인증 실패")
        print("   - Gmail 주소와 앱 비밀번호를 확인하세요")
        print("   - 2단계 인증이 활성화되어 있는지 확인하세요")
        return False

    except Exception as e:
        print(f"❌ 연결 실패: {str(e)}")
        return False

def test_3_data_collection():
    """테스트 3: 데이터 수집"""
    test_section("TEST 3: 주식 데이터 수집")

    korean_stocks = {
        '005930.KS': '삼성전자',
        '000660.KS': 'SK하이닉스',
        '051910.KS': 'LG화학',
        '035420.KS': 'NAVER',
        '035720.KS': 'Kakao',
    }

    print(f"\n📥 {len(korean_stocks)}개 종목 데이터 수집 중...")

    results = []
    successful = 0

    for ticker, company_name in korean_stocks.items():
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            stock_data = yf.Ticker(ticker).history(start=start_date, end=end_date)

            if len(stock_data) < 2:
                continue

            today = stock_data.iloc[-1]
            yesterday = stock_data.iloc[-2]

            today_close = today['Close']
            today_volume = today['Volume']
            yesterday_close = yesterday['Close']
            yesterday_volume = yesterday['Volume']

            price_change = ((today_close - yesterday_close) / yesterday_close) * 100
            volume_change = ((today_volume - yesterday_volume) / yesterday_volume) * 100
            weighted_score = price_change * (today_volume / 1000000)

            results.append({
                'company': company_name,
                'ticker': ticker,
                'price': today_close,
                'price_change': price_change,
                'volume': today_volume,
                'volume_change': volume_change,
                'weighted_score': weighted_score
            })
            successful += 1

        except Exception as e:
            pass

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('weighted_score', ascending=False)

    print(f"✅ {successful}/{len(korean_stocks)} 종목 수집 완료\n")

    print("TOP 3:")
    for idx, (_, row) in enumerate(results_df.head(3).iterrows(), 1):
        print(f"  {idx}. {row['company']:12} | {row['price_change']:+6.2f}% | 스코어: {row['weighted_score']:>8.0f}")

    return results_df.head(10)

def test_4_email_format(top_stocks):
    """테스트 4: 이메일 형식 검증"""
    test_section("TEST 4: 이메일 형식")

    print("\n✉️  이메일 HTML 형식 검증 중...\n")

    # HTML 생성
    html = f"""
    <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 20px auto; background: white; padding: 20px; border-radius: 8px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 5px; text-align: center; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th {{ background-color: #f0f0f0; padding: 12px; text-align: left; border-bottom: 2px solid #667eea; }}
                td {{ padding: 12px; border-bottom: 1px solid #eee; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 한국 주식 거래량 기준 상승률</h1>
                    <p>{datetime.now().strftime('%Y년 %m월 %d일')}</p>
                </div>
                <table>
                    <thead>
                        <tr style="background-color: #667eea; color: white;">
                            <th>순위</th>
                            <th>회사명</th>
                            <th>상승률</th>
                            <th>스코어</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for idx, (_, row) in enumerate(top_stocks.iterrows(), 1):
        html += f"""
                        <tr>
                            <td>{idx}</td>
                            <td><strong>{row['company']}</strong> ({row['ticker']})</td>
                            <td>{row['price_change']:+.2f}%</td>
                            <td>{row['weighted_score']:,.0f}</td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
            </div>
        </body>
    </html>
    """

    # 형식 검증
    checks = [
        ("이메일 제목 포함", "한국 주식" in html or "거래량" in html),
        ("날짜 정보 포함", datetime.now().strftime('%Y') in html),
        ("회사명 포함", "삼성" in html or "SK" in html),
        ("가격 정보 포함", "%" in html),
        ("테이블 형식", "<table>" in html),
        ("CSS 스타일", "<style>" in html),
        ("UTF-8 인코딩", "charset=UTF-8" in html),
    ]

    all_passed = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False

    return html, all_passed

def test_5_send_test_email(sender_email, sender_password):
    """테스트 5: 테스트 이메일 전송"""
    test_section("TEST 5: 테스트 이메일 전송")

    recipient = "hbyoo@hnsmall.com"

    print(f"\n📧 테스트 이메일 전송:")
    print(f"   발신: {sender_email}")
    print(f"   수신: {recipient}")

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[테스트] 주식 알림 시스템 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        msg['From'] = sender_email
        msg['To'] = recipient

        html_content = """
        <html>
            <body style="font-family: Arial; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 20px auto; background: white; padding: 20px; border-radius: 8px;">
                    <h2 style="color: #667eea;">✅ 테스트 이메일</h2>
                    <p>거래량 기준 한국 주식 알림 시스템이 정상적으로 작동합니다.</p>
                    <p><strong>발신 시간:</strong> """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
                    <p style="color: #999; font-size: 12px;">이것은 자동으로 생성된 테스트 메일입니다.</p>
                </div>
            </body>
        </html>
        """

        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        print("\n📤 이메일 전송 중...")

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print("✅ 테스트 이메일 전송 성공!")
        print(f"\n💡 {recipient}의 받은편지함을 확인하세요.")
        return True

    except Exception as e:
        print(f"❌ 테스트 이메일 전송 실패: {e}")
        return False

def main():
    """E2E 테스트 실행"""
    print("\n" + "="*70)
    print("🚀 이메일 기반 한국 주식 알림 시스템 - E2E 테스트")
    print("="*70)

    # TEST 1: Gmail 설정
    sender_email, sender_password = test_1_gmail_setup()
    if not sender_email or not sender_password:
        print("\n❌ 테스트 종료")
        return

    results = {
        "SMTP 연결": test_2_smtp_connection(sender_email, sender_password),
    }

    if not results["SMTP 연결"]:
        print("\n❌ SMTP 연결 실패로 테스트 중단")
        return

    # TEST 3: 데이터 수집
    top_stocks = test_3_data_collection()
    results["데이터 수집"] = len(top_stocks) > 0

    # TEST 4: 이메일 형식
    html_content, format_passed = test_4_email_format(top_stocks)
    results["이메일 형식"] = format_passed

    # TEST 5: 테스트 이메일 전송
    test_email_sent = test_5_send_test_email(sender_email, sender_password)
    results["테스트 이메일"] = test_email_sent

    # 최종 결과
    print("\n" + "="*70)
    print("📋 E2E 테스트 결과 요약")
    print("="*70 + "\n")

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {test_name}")
        if not passed:
            all_passed = False

    print("\n" + "="*70)
    if all_passed:
        print("✅ 모든 테스트 통과!")
        print("\n🎉 다음 단계:")
        print("  1. daily_stock_alert_email.py 스크립트 업데이트")
        print("     - SENDER_EMAIL, SENDER_PASSWORD 설정")
        print("  2. Windows Task Scheduler에 매일 09:00 실행 등록")
        print("  3. 매일 09:00에 자동으로 이메일 수신 시작")
    else:
        print("❌ 일부 테스트 실패")
    print("="*70 + "\n")

    # 설정 정보 저장
    if all_passed:
        print("💾 설정 정보를 저장하시겠습니까? (Y/n): ", end="")
        save = input().strip().lower()
        if save != 'n':
            print(f"\n📧 발신 이메일: {sender_email}")
            print(f"📧 수신 이메일: hbyoo@hnsmall.com")
            print("\n이 정보를 daily_stock_alert_email.py에 입력하세요:")
            print(f'  SENDER_EMAIL = "{sender_email}"')
            print(f'  SENDER_PASSWORD = "{sender_password}"')

if __name__ == "__main__":
    main()
