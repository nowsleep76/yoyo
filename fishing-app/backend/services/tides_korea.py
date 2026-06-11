"""한국 주요 해역의 공식 조석표 데이터 (국립해양조사원 발표 기준)

데이터가 없는 지역/날짜는 tide_service의 추정(시뮬레이션) 값으로 대체됩니다.
새 데이터를 추가할 때는 KOREA_TIDE_TABLES[location][(month, day)] 형식으로 입력하세요.
location 키는 tide_service.KOREA_TIDE_REFS 의 키와 일치해야 합니다.
"""

# 지역별 실제 조석표: {(월, 일): {'low': [간조 시각...], 'high': [만조 시각...], 'tide_num': 물때, 'strength': 조류 강도}}
KOREA_TIDE_TABLES = {
    'busan': {
        (6, 9):  {'low': ['04:16', '17:14'], 'high': ['10:34', '23:23'], 'tide_num': 15, 'strength': '18%'},
        (6, 10): {'low': ['04:52', '17:48'], 'high': ['11:10', '23:59'], 'tide_num': 1,  'strength': '10%'},
        (6, 11): {'low': ['05:30', '18:26'], 'high': ['11:50', '00:37'], 'tide_num': 2,  'strength': '12%'},
        (6, 12): {'low': ['06:10', '19:08'], 'high': ['12:33', '01:20'], 'tide_num': 3,  'strength': '13%'},
    },
}

# 음력 변환 (지역과 무관, 날짜 기준 공통)
LUNAR_CONVERSION_2026 = {
    (6, 9):  {'lunar_month': 4, 'lunar_day': 24, 'lunar_age': 24},
    (6, 10): {'lunar_month': 4, 'lunar_day': 25, 'lunar_age': 25},
    (6, 11): {'lunar_month': 4, 'lunar_day': 26, 'lunar_age': 26},
    (6, 12): {'lunar_month': 4, 'lunar_day': 27, 'lunar_age': 27},
}


def get_tide_table(location_key, month, day):
    """주어진 지역/날짜(2026년 기준)의 공식 조석표 정보 반환. 없으면 None."""
    return KOREA_TIDE_TABLES.get(location_key, {}).get((month, day))


def get_lunar_conversion(month, day):
    """주어진 날짜(2026년 기준)의 음력 변환 정보 반환. 없으면 None."""
    return LUNAR_CONVERSION_2026.get((month, day))
