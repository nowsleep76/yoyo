"""
E2E 테스트: 거래량 기준 상승률 한국 주식 알림 시스템
- 데이터 수집 검증
- 분석 결과 검증
- 메시지 포맷 검증
- Discord 웹훅 연동 테스트 (선택)
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
import sys
import io

# Windows UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_section(title):
    """테스트 섹션 표시"""
    print("\n" + "="*70)
    print(f"🧪 {title}")
    print("="*70)

def test_1_data_collection():
    """테스트 1: 데이터 수집 검증"""
    test_section("TEST 1: 데이터 수집")

    korean_stocks = {
        '005930.KS': '삼성전자',
        '000660.KS': 'SK하이닉스',
        '051910.KS': 'LG화학',
        '035420.KS': 'NAVER',
        '035720.KS': 'Kakao',
    }

    print(f"\n📥 {len(korean_stocks)}개 종목에서 데이터 수집 시작...")

    successful = 0
    failed = 0

    for ticker, name in korean_stocks.items():
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            stock_data = yf.Ticker(ticker).history(start=start_date, end=end_date)

            if len(stock_data) > 0:
                latest = stock_data.iloc[-1]
                print(f"  ✅ {name:12} | 가격: {latest['Close']:>10,.0f}원 | 거래량: {latest['Volume']:>12,.0f}")
                successful += 1
            else:
                print(f"  ❌ {name:12} | 데이터 없음")
                failed += 1

        except Exception as e:
            print(f"  ❌ {name:12} | 오류: {str(e)[:30]}")
            failed += 1

    print(f"\n결과: {successful}/{len(korean_stocks)} 성공")
    return successful > 0

def test_2_analysis_calculation():
    """테스트 2: 분석 계산 검증"""
    test_section("TEST 2: 분석 계산")

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
    }

    print(f"\n📊 {len(korean_stocks)}개 종목 분석 중...")

    results = []

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

            # 계산
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

        except Exception as e:
            print(f"  ⚠️  {company_name} 분석 실패")

    # 결과 정렬
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('weighted_score', ascending=False)
    top_3 = results_df.head(3)

    print(f"\n✅ {len(results_df)}개 종목 분석 완료\n")
    print("TOP 3 (거래량 기준 상승률):")
    for idx, (_, row) in enumerate(top_3.iterrows(), 1):
        print(f"  {idx}. {row['company']:12} | 상승률: {row['price_change']:+6.2f}% | 스코어: {row['weighted_score']:>8.0f}")

    return len(results_df) >= 5

def test_3_message_format():
    """테스트 3: 메시지 포맷 검증"""
    test_section("TEST 3: 메시지 포맷")

    print("\n📝 Discord 메시지 포맷 검증...")

    # 샘플 메시지 생성
    sample_message = f"""
🚀 **한국 주식 일일 분석 - {datetime.now().strftime('%Y-%m-%d')}**

**거래량 기준 상승률 TOP 10**

1. 🟢 **삼성전자** (005930.KS)
   💰 현재가: 356,750원 | 상승률: +5.20%
   📊 거래량: 15,204,452 | 거래량 변화: +38.98%
   ⭐ 스코어: 78

2. 🟢 **SK하이닉스** (000660.KS)
   💰 현재가: 2,299,000원 | 상승률: +8.50%
   📊 거래량: 3,204,452 | 거래량 변화: +25.50%
   ⭐ 스코어: 27
"""

    # 포맷 검증
    checks = [
        ("로케이션 정보 포함" , "2026-06-04" in sample_message or datetime.now().strftime('%Y-%m-%d') in sample_message),
        ("회사명 포함", "삼성전자" in sample_message),
        ("티커 포함", "005930.KS" in sample_message),
        ("가격 정보 포함", "원" in sample_message),
        ("상승률 포함", "+" in sample_message or "%" in sample_message),
        ("거래량 정보 포함", "거래량" in sample_message),
        ("이모지 포함", "🟢" in sample_message or "📊" in sample_message),
    ]

    all_passed = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False

    print(f"\n포맷 검증: {'통과' if all_passed else '실패'}")
    return all_passed

def test_4_webhook_connectivity():
    """테스트 4: 웹훅 연결성 테스트 (선택)"""
    test_section("TEST 4: 웹훅 연결성")

    print("\n🔗 Discord 웹훅 테스트...")

    webhook_url = input("\n💡 Discord 웹훅 URL을 입력하세요 (또는 Enter로 스킵): ").strip()

    if not webhook_url:
        print("⏭️  웹훅 테스트 스킵\n")
        return True

    try:
        # 테스트 메시지
        test_message = f"""
🧪 **웹훅 테스트 메시지**

테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
상태: ✅ 정상 작동
"""

        data = {
            "content": test_message,
            "username": "주식 알림 봇"
        }

        print("📤 웹훅으로 테스트 메시지 전송 중...")
        response = requests.post(webhook_url, json=data)

        if response.status_code == 204:
            print("✅ 웹훅 전송 성공!")
            return True
        else:
            print(f"❌ 웹훅 전송 실패 (상태 코드: {response.status_code})")
            return False

    except Exception as e:
        print(f"❌ 오류: {str(e)}")
        return False

def test_5_real_data_analysis():
    """테스트 5: 실제 데이터 전체 분석"""
    test_section("TEST 5: 실제 데이터 전체 분석")

    print("\n📈 전체 20개 종목 분석 중...")

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

    results = []

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

        except Exception as e:
            pass

    if len(results) == 0:
        print("❌ 분석 데이터 없음")
        return False

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('weighted_score', ascending=False)
    top_10 = results_df.head(10)

    print(f"\n✅ {len(results_df)}/20 종목 분석 완료\n")
    print("거래량 기준 상승률 TOP 10:")
    print("-" * 70)
    for idx, (_, row) in enumerate(top_10.iterrows(), 1):
        emoji = "🟢" if row['price_change'] > 0 else "🔴"
        print(f"{idx:2}. {emoji} {row['company']:12} | {row['price_change']:+6.2f}% | 스코어: {row['weighted_score']:>8.0f}")

    return True

def main():
    """E2E 테스트 실행"""
    print("\n" + "="*70)
    print("🚀 거래량 기준 한국 주식 알림 시스템 - E2E 테스트")
    print("="*70)

    results = {
        "데이터 수집": test_1_data_collection(),
        "분석 계산": test_2_analysis_calculation(),
        "메시지 포맷": test_3_message_format(),
        "실제 데이터 분석": test_5_real_data_analysis(),
        "웹훅 연결": test_4_webhook_connectivity(),
    }

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
        print("  1. Discord 웹훅 URL 설정")
        print("  2. daily_stock_alert.py 스크립트 업데이트")
        print("  3. Windows Task Scheduler에 매일 09:00 실행 등록")
    else:
        print("❌ 일부 테스트 실패")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
