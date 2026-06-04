"""
한국 주식 거래량 기준 상승률 일일 분석 (콘솔 버전)
- 매일 거래량 기준 상승률이 높은 주식 TOP 10 분석
- 콘솔에 표시 및 로그 파일 저장
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sys
import io
import os

# Windows UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

class StockAnalyzer:
    def __init__(self):
        self.results = []
        self.output_lines = []
        self.log_file = os.path.join(os.path.dirname(__file__), 'stock_alert_log.txt')

    def add_line(self, text):
        """출력 라인 추가"""
        self.output_lines.append(text)
        print(text)

    def get_today_stock_data(self):
        """오늘 하루 거래량 기준 상승률이 높은 주식 찾기"""
        self.add_line(f"\n{'='*80}")
        self.add_line(f"📊 한국 주식 거래량 기준 상승률 분석 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.add_line(f"{'='*80}\n")

        self.add_line(f"📈 {len(korean_stocks)}개 종목 분석 중...\n")

        for ticker, company_name in korean_stocks.items():
            try:
                # 1주일 데이터 가져오기
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
                weighted_score = price_change * (today_volume / 1000000)

                self.results.append({
                    'ticker': ticker,
                    'company': company_name,
                    'price': today_close,
                    'price_change': price_change,
                    'volume': today_volume,
                    'volume_change': volume_change,
                    'weighted_score': weighted_score
                })

            except Exception as e:
                pass

        # 거래량 가중 상승률로 정렬
        if self.results:
            results_df = pd.DataFrame(self.results)
            results_df = results_df.sort_values('weighted_score', ascending=False)
            return results_df.head(10)

        return pd.DataFrame()

    def display_results(self, top_stocks):
        """결과를 콘솔에 표시"""
        if len(top_stocks) == 0:
            self.add_line("❌ 분석할 데이터가 없습니다.")
            return

        # 헤더
        self.add_line(f"{'순위':<6} {'회사명':<15} {'티커':<12} {'현재가':<12} {'상승률':<10} {'거래량':<15} {'거래량변화':<10} {'스코어':<10}")
        self.add_line("-" * 110)

        # 데이터
        for idx, (_, row) in enumerate(top_stocks.iterrows(), 1):
            emoji = "🟢" if row['price_change'] > 0 else "🔴"

            rank = f"{idx}. {emoji}"
            company = f"{row['company'][:12]}"
            ticker = row['ticker']
            price = f"₩{row['price']:,.0f}"
            change = f"{row['price_change']:+.2f}%"
            volume = f"{row['volume']:,.0f}"
            vol_change = f"{row['volume_change']:+.2f}%"
            score = f"{row['weighted_score']:,.0f}"

            line = f"{rank:<8} {company:<15} {ticker:<12} {price:<12} {change:<10} {volume:<15} {vol_change:<10} {score:<10}"
            self.add_line(line)

        self.add_line("\n" + "="*80)

    def display_detailed_results(self, top_stocks):
        """상세 정보 표시"""
        self.add_line("\n📋 상세 정보:\n")

        for idx, (_, row) in enumerate(top_stocks.iterrows(), 1):
            emoji = "🟢" if row['price_change'] > 0 else "🔴"

            self.add_line(f"\n{idx}. {emoji} {row['company']} ({row['ticker']})")
            self.add_line(f"   💰 현재가: {row['price']:,.0f}원")
            self.add_line(f"   📈 상승률: {row['price_change']:+.2f}%")
            self.add_line(f"   📊 거래량: {row['volume']:,.0f}")
            self.add_line(f"   🔄 거래량 변화: {row['volume_change']:+.2f}%")
            self.add_line(f"   ⭐ 점수: {row['weighted_score']:,.0f}")

        self.add_line("\n" + "="*80)

    def save_to_log(self):
        """로그 파일에 저장"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write('\n'.join(self.output_lines))
                f.write('\n\n')
            print(f"\n💾 로그 저장 완료: {self.log_file}")
        except Exception as e:
            print(f"\n⚠️  로그 저장 실패: {e}")

    def run(self):
        """분석 실행"""
        top_stocks = self.get_today_stock_data()

        if len(top_stocks) > 0:
            self.display_results(top_stocks)
            self.display_detailed_results(top_stocks)
            self.save_to_log()
        else:
            self.add_line("❌ 분석할 데이터가 없습니다.")

def main():
    analyzer = StockAnalyzer()
    analyzer.run()

if __name__ == "__main__":
    main()
