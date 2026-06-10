"""한국 주요 해역의 조석표 데이터"""

# 형식: (날짜, 간조1, 만조, 간조2, 만조2)
# 2026년 6월 부산 해역 기준 조석표
KOREA_TIDES_2026_06 = {
    9: {'low': ['04:16', '17:14'], 'high': ['10:34', '23:23'], 'tide_num': 15, 'strength': '18%'},
    10: {'low': ['04:52', '17:48'], 'high': ['11:10', '23:59'], 'tide_num': 1, 'strength': '10%'},
    11: {'low': ['05:30', '18:26'], 'high': ['11:50', '00:37'], 'tide_num': 2, 'strength': '12%'},
    12: {'low': ['06:10', '19:08'], 'high': ['12:33', '01:20'], 'tide_num': 3, 'strength': '13%'},
}

def get_tide_for_date(day):
    """주어진 일자의 조석 정보 반환"""
    return KOREA_TIDES_2026_06.get(day)

# 음력 변환 기준 데이터
LUNAR_CONVERSION_2026 = {
    (6, 9): {'lunar_month': 4, 'lunar_day': 24, 'lunar_age': 24},
    (6, 10): {'lunar_month': 4, 'lunar_day': 25, 'lunar_age': 25},
    (6, 11): {'lunar_month': 4, 'lunar_day': 26, 'lunar_age': 26},
    (6, 12): {'lunar_month': 4, 'lunar_day': 27, 'lunar_age': 27},
}
