from datetime import datetime, timedelta
import math

TIDE_VOLUME = {
    (1, 3):   {'label': '조금', 'level': 1, 'desc': '물이 가장 적게 드나드는 시기. 낚시 활성도 낮음.'},
    (4, 7):   {'label': '중간', 'level': 2, 'desc': '중간 조류. 무난한 낚시 조건.'},
    (8, 12):  {'label': '사리', 'level': 3, 'desc': '물이 가장 많이 드나드는 시기. 낚시 최적 조건.'},
    (13, 15): {'label': '중간', 'level': 2, 'desc': '사리 이후 중간 조류로 전환.'},
}

def get_tide_volume(tide_number):
    for (lo, hi), info in TIDE_VOLUME.items():
        if lo <= tide_number <= hi:
            return info
    return {'label': '중간', 'level': 2, 'desc': ''}

def get_lunar_age():
    reference_new_moon = datetime(2000, 1, 6)
    days_since = (datetime.now() - reference_new_moon).days
    lunar_age = (days_since % 29.5) + 1
    return lunar_age

def get_tide_number():
    lunar_age = get_lunar_age()
    tide_number = int((lunar_age / 29.5) * 15) + 1
    tide_number = min(15, max(1, tide_number))
    return tide_number

def get_tide_data(latitude, longitude):
    now = datetime.now()
    tide_number = get_tide_number()

    hourly_data = []
    for i in range(24):
        time = now.replace(hour=i, minute=0, second=0, microsecond=0)

        tidal_height = 2.0 + 1.5 * math.sin(i * math.pi / 12)

        hourly_data.append({
            'time': time.isoformat(),
            'height': round(tidal_height, 2),
            'hour': i
        })

    tide_times = []
    if tide_number <= 7:
        tide_times = ['고: 08:30', '저: 14:45', '고: 21:10']
    elif tide_number <= 8:
        tide_times = ['고: 09:00', '저: 15:15', '고: 21:40']
    else:
        tide_times = ['고: 09:30', '저: 15:45', '고: 22:10']

    volume = get_tide_volume(tide_number)

    return {
        'tide_number': tide_number,
        'location': {
            'latitude': latitude,
            'longitude': longitude
        },
        'today': {
            'tide_times': tide_times,
            'description': f'{tide_number}물',
            'volume': volume
        },
        'hourly': hourly_data,
        'timestamp': datetime.now().isoformat()
    }

def get_celestial_times(date, latitude):
    """일출, 일몰, 월출, 월몰 시간 계산 (근사값)"""
    month = date.month
    day = date.day

    # 위도에 따른 일출/일몰 시간 (한국 기준 근사값)
    if month in [12, 1, 2]:  # 겨울
        sunrise_hour, sunrise_min = 7, 15
        sunset_hour, sunset_min = 17, 20
    elif month in [3, 4, 5]:  # 봄
        sunrise_hour, sunrise_min = 6, 10
        sunset_hour, sunset_min = 18, 45
    elif month in [6, 7, 8]:  # 여름
        sunrise_hour, sunrise_min = 5, 20
        sunset_hour, sunset_min = 19, 30
    else:  # 가을
        sunrise_hour, sunrise_min = 6, 20
        sunset_hour, sunset_min = 18, 10

    # 날짜에 따른 미세 조정
    day_adjustment = (day % 15) // 3
    sunrise_min = (sunrise_min + day_adjustment * 5) % 60
    sunset_min = (sunset_min + day_adjustment * 3) % 60

    return {
        'sunrise': sunrise_hour,
        'sunrise_minute': sunrise_min,
        'sunset': sunset_hour,
        'sunset_minute': sunset_min
    }

def get_lunar_date(target_date):
    """양력 → 음력 변환 (근사 계산)"""
    reference_new_moon = datetime(2000, 1, 6)  # 2000년 1월 6일 새달
    days_since = (target_date - reference_new_moon).days
    lunar_age = (days_since % 29.5306) + 1  # 음력 달의 정확한 주기: 29.5306일

    # 음력 월 계산 (대략 29.5일 = 1개월)
    lunar_month = int(lunar_age / 29.5306)
    if lunar_month == 0:
        lunar_month = 12
    lunar_day = int((lunar_age % 29.5306)) + 1
    if lunar_day > 29:
        lunar_day = 29

    return {
        'month': lunar_month,
        'day': lunar_day,
        'age': round(lunar_age, 1)
    }

def get_tide_hourly(latitude, longitude, date_str=None):
    """날짜별 24시간 조석 높이 + 수온 + 만조/간조 계산"""
    reference_new_moon = datetime(2000, 1, 6)

    if date_str:
        target = datetime.strptime(date_str, '%Y-%m-%d')
    else:
        target = datetime.now()

    days_since = (target - reference_new_moon).days
    lunar_age = (days_since % 29.5306) + 1  # 더 정확한 음력 주기 사용
    tide_num = int((lunar_age / 29.5306) * 15) + 1
    tide_num = min(15, max(1, tide_num))

    # 음력 날짜 계산
    lunar_info = get_lunar_date(target)

    # 천체 데이터 계산
    celestial = get_celestial_times(target, latitude)

    amplitude = 1.0 + (tide_num / 15) * 1.2

    # 물때에 따른 만조 시간 오프셋 (조금~사리)
    high_tide_offset = (tide_num - 8) * 0.3

    month = target.month
    base_water_temp = 8 + (month - 1) * 1.3

    hourly = []
    for i in range(24):
        # 반일주기 조석: 약 12.4시간 주기로 2개의 만조와 2개의 간조
        phase1 = (i - 6 - high_tide_offset) * math.pi / 12.42
        phase2 = (i - 6 - high_tide_offset) * 2 * math.pi / 12.42

        # 두 개의 sine 곡선 합산 (주로 첫 번째 성분이 지배적)
        height = 2.0 + amplitude * math.sin(phase1) + (amplitude * 0.2) * math.sin(phase2)
        height = round(height, 2)

        water_temp = round(base_water_temp + 0.8 * math.sin((i - 6) * math.pi / 12), 1)

        # 조류 강도 계산: 만조/간조 근처 약함, 중간 강함 (0.1~1.0 m/s)
        # 수위 변화가 가장 큼 → 조류도 강함
        current_phase = (i - 6 - high_tide_offset) * math.pi / 12.42
        current_speed = round(0.5 * abs(math.cos(current_phase)), 2)

        # 시간별 날씨 데이터 생성
        temp = round(12 + 8 * math.sin((i - 6) * math.pi / 12), 1)
        wind_speed = round(2.5 + 3.5 * abs(math.sin((i - 3) * math.pi / 12)), 1)
        wind_degree = (i * 15) % 360
        wave_height = round(0.3 + 0.6 * abs(math.sin((i - 6) * math.pi / 12)), 1)

        # 날씨 결정 (시간대별)
        if i < 6:
            weather = '맑음'
        elif i < 12:
            weather = '구름'
        elif i < 18:
            weather = '맑음'
        else:
            weather = '구름'

        wind_directions = ['북', '북북동', '북동', '동북동', '동', '동남동', '남동', '남남동',
                          '남', '남남서', '남서', '서남서', '서', '서북서', '북서', '북북서']
        wind_dir = wind_directions[int(wind_degree / 22.5) % 16]

        hourly.append({
            'hour': i,
            'height': height,
            'waterTemp': water_temp,
            'currentSpeed': current_speed,
            'weather': weather,
            'temp': temp,
            'windSpeed': wind_speed,
            'windDir': wind_dir,
            'waveHeight': wave_height,
            'wavePeriod': 4
        })

    # 경계 시간대를 위해 이전/다음 값 계산
    prev_i = -1
    prev_phase1 = (prev_i - 6 - high_tide_offset) * math.pi / 12.42
    prev_phase2 = (prev_i - 6 - high_tide_offset) * 2 * math.pi / 12.42
    prev_height = 2.0 + amplitude * math.sin(prev_phase1) + (amplitude * 0.2) * math.sin(prev_phase2)

    next_i = 24
    next_phase1 = (next_i - 6 - high_tide_offset) * math.pi / 12.42
    next_phase2 = (next_i - 6 - high_tide_offset) * 2 * math.pi / 12.42
    next_height = 2.0 + amplitude * math.sin(next_phase1) + (amplitude * 0.2) * math.sin(next_phase2)

    # 극값(만조/간조) 찾기 - 2차 미분으로 극값 감지
    high_tides, low_tides = [], []

    # 부드러운 극값 감지를 위해 2시간 윈도우 사용
    for i in range(1, 23):
        curr_h = hourly[i]['height']
        prev_h = hourly[i-1]['height']
        next_h = hourly[i+1]['height']

        # 2차 미분: (다음값 - 현재값) - (현재값 - 이전값)
        second_deriv = (next_h - curr_h) - (curr_h - prev_h)

        # 극값 시점의 분을 계산 (선형 보간)
        if prev_h != curr_h:
            # 극값이 i-1과 i 사이에 있으면 분을 계산
            if (curr_h > prev_h and second_deriv < -0.01) or (curr_h < prev_h and second_deriv > 0.01):
                # 비율로 분을 계산 (0~59)
                ratio = abs(curr_h - prev_h) / (abs(next_h - prev_h) + 0.001)
                minute = int(ratio * 60) if ratio < 1 else 30
            else:
                minute = 30
        else:
            minute = 0

        # 만조: 2차 미분 < 0 (아래로 볼록)
        if second_deriv < -0.05:
            # 6시간 이상 떨어져 있으면 추가
            if not any(abs(t['hour'] - i) < 6 for t in high_tides):
                time_str = f'{i:02d}:{minute:02d}'
                high_tides.append({'hour': i, 'minute': minute, 'time': time_str, 'height': round(curr_h, 2)})

        # 간조: 2차 미분 > 0 (위로 볼록)
        elif second_deriv > 0.05:
            # 6시간 이상 떨어져 있으면 추가
            if not any(abs(t['hour'] - i) < 6 for t in low_tides):
                time_str = f'{i:02d}:{minute:02d}'
                low_tides.append({'hour': i, 'minute': minute, 'time': time_str, 'height': round(curr_h, 2)})

    # 간조가 없으면 최소값을 간조로 추가
    if not low_tides and len(hourly) > 0:
        min_hour = hourly.index(min(hourly, key=lambda x: x['height']))
        min_height = hourly[min_hour]['height']
        low_tides.append({'hour': min_hour, 'minute': 0, 'time': f'{min_hour:02d}:00', 'height': round(min_height, 2)})

    # 만조가 없으면 최대값을 만조로 추가
    if not high_tides and len(hourly) > 0:
        max_hour = hourly.index(max(hourly, key=lambda x: x['height']))
        max_height = hourly[max_hour]['height']
        high_tides.append({'hour': max_hour, 'minute': 0, 'time': f'{max_hour:02d}:00', 'height': round(max_height, 2)})

    # 3시간 단위 데이터 필터링
    hourly_3h = [h for h in hourly if h['hour'] % 3 == 0]

    volume = get_tide_volume(tide_num)

    # highTides, lowTides 형식 변환 (camelCase, time 필드 추가)
    high_tides_camel = [{'time': t['time'], 'height': t['height']} for t in high_tides]
    low_tides_camel = [{'time': t['time'], 'height': t['height']} for t in low_tides]

    # 천체 데이터
    celestial_events = [
        {'type': 'sunrise', 'hour': celestial['sunrise'], 'label': '일출'},
        {'type': 'sunset', 'hour': celestial['sunset'], 'label': '일몰'},
    ]

    return {
        'date': target.strftime('%Y-%m-%d'),
        'weekday': ['월','화','수','목','금','토','일'][target.weekday()],
        'tideNumber': tide_num,
        'description': f'{tide_num}물',
        'volume': volume,
        'lunar': {
            'month': lunar_info['month'],
            'day': lunar_info['day'],
            'age': lunar_info['age']
        },
        'sunrise': f"{celestial['sunrise']:02d}:{celestial['sunrise_minute']:02d}",
        'sunset': f"{celestial['sunset']:02d}:{celestial['sunset_minute']:02d}",
        'hourly': hourly_3h,  # 3시간 단위 데이터
        'highTides': high_tides_camel,
        'lowTides': low_tides_camel,
        'allHourly': hourly,  # 모든 시간별 데이터 (필요시)
        'celestialEvents': celestial_events,
        'location': {
            'latitude': latitude,
            'longitude': longitude
        }
    }

def get_tide_calendar(latitude, longitude, days=7):
    reference_new_moon = datetime(2000, 1, 6)
    result = []

    for i in range(days):
        date = datetime.now() + timedelta(days=i)
        days_since = (date - reference_new_moon).days
        lunar_age = (days_since % 29.5) + 1
        tide_num = int((lunar_age / 29.5) * 15) + 1
        tide_num = min(15, max(1, tide_num))

        volume = get_tide_volume(tide_num)

        result.append({
            'date': date.strftime('%Y-%m-%d'),
            'weekday': ['월', '화', '수', '목', '금', '토', '일'][date.weekday()],
            'tide_number': tide_num,
            'description': f'{tide_num}물',
            'volume': volume
        })

    return result
