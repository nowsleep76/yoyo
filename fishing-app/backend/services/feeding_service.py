from datetime import datetime, timedelta
import math

# 물때에 따른 어종별 활성도 데이터
# (물때, 어종) -> (활성도, 피딩시간)
FEEDING_PATTERNS = {
    '우럭': {
        'peak_hours': {
            (1, 2): [(6, 10), (18, 22)],  # 1물, 2물
            (3, 4): [(7, 11), (19, 23)],  # 3물, 4물
            (5, 6): [(8, 12), (20, 24)],  # 5물, 6물
            (7, 8): [(9, 13), (21, 1)],   # 7물, 8물
            (9, 10): [(10, 14), (22, 2)], # 9물, 10물
            (11, 12): [(9, 13), (21, 1)], # 11물, 12물
            (13, 14): [(8, 12), (20, 24)],# 13물, 14물
            (15,): [(6, 10), (18, 22)],   # 15물(사리)
        }
    },
    '민물고기': {
        'peak_hours': {
            (1, 2): [(7, 11), (19, 23)],
            (3, 4): [(8, 12), (20, 24)],
            (5, 6): [(9, 13), (21, 1)],
            (7, 8): [(10, 14), (22, 2)],
            (9, 10): [(9, 13), (21, 1)],
            (11, 12): [(8, 12), (20, 24)],
            (13, 14): [(7, 11), (19, 23)],
            (15,): [(6, 10), (18, 22)],
        }
    },
    '문어': {
        'peak_hours': {
            (1, 2): [(5, 9), (17, 21)],
            (3, 4): [(6, 10), (18, 22)],
            (5, 6): [(7, 11), (19, 23)],
            (7, 8): [(8, 12), (20, 24)],
            (9, 10): [(9, 13), (21, 1)],
            (11, 12): [(8, 12), (20, 24)],
            (13, 14): [(7, 11), (19, 23)],
            (15,): [(5, 9), (17, 21)],
        }
    },
    '낙지': {
        'peak_hours': {
            (1, 2): [(5, 9), (17, 21)],
            (3, 4): [(6, 10), (18, 22)],
            (5, 6): [(7, 11), (19, 23)],
            (7, 8): [(8, 12), (20, 24)],
            (9, 10): [(9, 13), (21, 1)],
            (11, 12): [(8, 12), (20, 24)],
            (13, 14): [(7, 11), (19, 23)],
            (15,): [(5, 9), (17, 21)],
        }
    }
}

def get_feeding_times(latitude, longitude, date_str=None):
    """
    주어진 위치와 날짜의 피딩타임을 반환

    Args:
        latitude: 위도
        longitude: 경도
        date_str: YYYY-MM-DD 형식 (None이면 오늘)

    Returns:
        list: 어종별 피딩타임 정보
    """
    if date_str is None:
        date_obj = datetime.now()
    else:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')

    # 물때 번호 계산 (음력 나이 기반)
    reference_new_moon = datetime(2000, 1, 6)
    days_since = (date_obj - reference_new_moon).days
    lunar_age = (days_since % 29.5) + 1
    lunar_age = int((lunar_age / 29.5) * 15) + 1
    lunar_age = min(15, max(1, lunar_age))

    feeding_times = []

    for species, pattern in FEEDING_PATTERNS.items():
        peak_hours = pattern['peak_hours']

        # 물때에 맞는 피딩시간 찾기
        peak_time = None
        for tide_range, times in peak_hours.items():
            if lunar_age in tide_range:
                peak_time = times[0]  # 첫 번째 피딩타임 사용
                break

        if peak_time is None:
            peak_time = (8, 12)  # 기본값

        # 활성도 계산 (물때에 따라 다름)
        activity_level = calculate_activity_level(lunar_age)

        feeding_times.append({
            'species': species,
            'peak_hour_start': peak_time[0],
            'peak_hour_end': peak_time[1],
            'activity_level': activity_level,
            'description': f"{peak_time[0]}시 ~ {peak_time[1]}시 활발"
        })

    return feeding_times

def calculate_activity_level(lunar_age):
    """
    물때 번호에 따른 활성도 계산 (1-5)
    사리(15)일 때 최고 활성도

    Args:
        lunar_age: 물때 번호 (1-15)

    Returns:
        int: 활성도 (1-5)
    """
    if lunar_age == 1 or lunar_age == 15:
        return 5  # 새물, 사리
    elif lunar_age in [2, 14]:
        return 4  # 정조기
    elif lunar_age in [3, 13]:
        return 3  # 중간
    else:
        return 2  # 약한 활동

def get_feeding_calendar(latitude, longitude, days=30):
    """
    향후 N일간의 피딩타임 캘린더 생성

    Args:
        latitude: 위도
        longitude: 경도
        days: 일수 (기본값 30)

    Returns:
        dict: 날짜별 피딩타임 정보
    """
    calendar = {}
    today = datetime.now()

    for i in range(days):
        date = today + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        calendar[date_str] = get_feeding_times(latitude, longitude, date_str)

    return calendar
