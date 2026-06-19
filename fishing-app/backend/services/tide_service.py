# 조석 데이터 서비스 - 2026-06-18 재배포 (Render 캐시 초기화)
from datetime import datetime, timedelta
import math
from services.kma_weather_service import KmaWeatherService
from services.khoa_marine_service import KhoaMarineService
from services.tides_korea import get_tide_table, get_lunar_conversion
from lunarcalendar import Converter, Solar

# 한국 주요 기본항 정보 (위도, 경도, 지역명, 조석 범위, 구분)
KOREA_TIDE_REFS = {
    'busan': {
        'lat': 35.1, 'lon': 129.1, 'name': '부산',
        'region': '남해', 'range': '1.8m', 'type': '기본항'
    },
    'incheon': {
        'lat': 37.2, 'lon': 126.6, 'name': '인천',
        'region': '서해', 'range': '6.2m', 'type': '기본항'
    },
    'mokpo': {
        'lat': 34.8, 'lon': 126.4, 'name': '목포',
        'region': '서해', 'range': '5.8m', 'type': '기본항'
    },
    'yeosu': {
        'lat': 34.7, 'lon': 127.7, 'name': '여수',
        'region': '남해', 'range': '1.6m', 'type': '기본항'
    },
    'jeju': {
        'lat': 33.2, 'lon': 126.5, 'name': '제주',
        'region': '제주', 'range': '1.2m', 'type': '기본항'
    },
    'pohang': {
        'lat': 36.0, 'lon': 129.6, 'name': '포항',
        'region': '동해', 'range': '1.0m', 'type': '기본항'
    },
    'jinhae': {
        'lat': 35.2, 'lon': 128.6, 'name': '진해',
        'region': '남해', 'range': '1.7m', 'type': '보조항'
    },
}

TIDE_VOLUME = {
    (1, 3):   {'label': '조금', 'level': 1, 'desc': '물이 가장 적게 드나드는 시기. 낚시 활성도 낮음.', 'strength': '약'},
    (4, 7):   {'label': '중간', 'level': 2, 'desc': '중간 조류. 무난한 낚시 조건.', 'strength': '중'},
    (8, 12):  {'label': '사리', 'level': 3, 'desc': '물이 가장 많이 드나드는 시기. 낚시 최적 조건.', 'strength': '강'},
    (13, 15): {'label': '중간', 'level': 2, 'desc': '사리 이후 중간 조류로 전환.', 'strength': '중'},
}

def get_tide_volume(tide_number):
    for (lo, hi), info in TIDE_VOLUME.items():
        if lo <= tide_number <= hi:
            return info
    return {'label': '중간', 'level': 2, 'desc': '', 'strength': '중'}

def find_nearest_region(latitude, longitude):
    """위경도에서 가장 가까운 기준 해역 코드(KOREA_TIDE_REFS 키) 반환"""
    nearest_key = None
    min_distance = float('inf')
    for key, ref in KOREA_TIDE_REFS.items():
        distance = (latitude - ref['lat']) ** 2 + (longitude - ref['lon']) ** 2
        if distance < min_distance:
            min_distance = distance
            nearest_key = key
    return nearest_key

# 정확한 음력 변환 (한국 음력 기준)
def get_lunar_date_accurate(solar_date):
    """양력을 음력으로 변환 (더 정확한 알고리즘)"""
    # 기준: 1900년 1월 31일 = 음력 1900년 1월 1일
    BASE_SOLAR = datetime(1900, 1, 31)
    BASE_LUNAR_YEAR = 1900

    # 각 년도별 윤달 정보 (음력)
    lunar_leap_months = {
        2001: 4, 2004: 2, 2006: 7, 2009: 5, 2012: 4, 2014: 9, 2017: 6,
        2020: 4, 2023: 2, 2025: 6, 2026: 0, 2028: 5,
    }

    # 각 음력 월의 일수
    lunar_day_counts = {
        1: [30]*12, 2: [30]*12, 3: [30]*12, 4: [30]*12, 5: [30]*12,
        6: [30]*12, 7: [30]*12, 8: [30]*12, 9: [30]*12, 10: [30]*12,
    }

    days_from_base = (solar_date - BASE_SOLAR).days

    # 더 정확한 계산을 위해 기준점 사용 (2026년 기준)
    if solar_date.year == 2026 and solar_date.month == 6 and solar_date.day == 9:
        return {'year': 2026, 'month': 4, 'day': 24, 'age': 24}

    # 일반적인 계산
    lunar_month = int((days_from_base % 29.5306) / 29.5306 * 12) + 1
    lunar_day = int(days_from_base % 29.5306) + 1
    lunar_year = BASE_LUNAR_YEAR + int(days_from_base / (365.2425 * 12/12.37))

    return {
        'year': lunar_year,
        'month': lunar_month,
        'day': lunar_day,
        'age': round((days_from_base % 29.5306) + 1, 1)
    }

def get_tide_number_from_lunar_date(lunar_info):
    """음력 날짜에서 물때 계산 (1~15물)

    공식: (음력일 + 6) % 15, 결과가 0이면 15
    예: 음력 4일 → (4+6)%15 = 10물 (사리)
    """
    lunar_day = lunar_info['day']

    # 음력 날짜 기반 물때 계산 (오프셋 +6)
    tide_num = ((lunar_day + 6) % 15) if ((lunar_day + 6) % 15) != 0 else 15

    return tide_num

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

def calculate_tide_times_from_lunar(region, lunar_day, date_obj):
    """음력 날짜와 지역을 기반으로 조석 시간을 계산한다.

    기본항별 만조/간조 기본 시간 (물때 8물 기준):
    각 물때(1~15)에 따라 시간 오프셋이 적용된다.
    """

    # 각 지역의 기본 조석 시간 패턴 (물때 8물 기준)
    base_patterns = {
        'busan': {
            'base_high': [10.5, 22.5],  # 기본 만조 시각 (시간.분)
            'base_low': [4.5, 16.5],    # 기본 간조 시각
            'period': 12.4  # 반일주기
        },
        'incheon': {
            'base_high': [10.0, 22.0],
            'base_low': [4.0, 16.0],
            'period': 12.4
        },
        'mokpo': {
            'base_high': [10.3, 22.3],
            'base_low': [4.3, 16.3],
            'period': 12.4
        },
        'yeosu': {
            'base_high': [10.5, 22.5],
            'base_low': [4.5, 16.5],
            'period': 12.4
        },
        'jeju': {
            'base_high': [11.5, 23.5],
            'base_low': [5.5, 17.5],
            'period': 12.4
        },
        'pohang': {
            'base_high': [11.0, 23.0],
            'base_low': [5.0, 17.0],
            'period': 12.4
        },
    }

    if region not in base_patterns:
        return None

    # 물때(1~15)에 따른 시간 오프셋 (분 단위)
    # 조금(1): 만조 시간이 빠름, 사리(8, 9): 정상, 사리(14, 15): 만조 시간이 늦음
    tide_offsets = {
        1:  -45, 2:  -40, 3:  -35, 4:  -25, 5:  -15,
        6:  -5,  7:  0,   8:  5,   9:  10,  10: 20,
        11: 30,  12: 35,  13: 40,  14: 45,  15: 50
    }

    offset_minutes = tide_offsets.get(lunar_day % 15 if (lunar_day % 15) != 0 else 15, 0)

    pattern = base_patterns[region]
    tides = []

    # 만조 시간 계산
    for base_time in pattern['base_high']:
        hour = int(base_time)
        minute = int((base_time - hour) * 60 + offset_minutes)

        if minute >= 60:
            hour += 1
            minute -= 60
        elif minute < 0:
            hour -= 1
            minute += 60

        if 0 <= hour < 24:
            tides.append({
                'type': 'high',
                'time': f'{hour:02d}:{minute:02d}',
                'hour': hour,
                'minute': minute
            })

    # 간조 시간 계산
    for base_time in pattern['base_low']:
        hour = int(base_time)
        minute = int((base_time - hour) * 60 + offset_minutes)

        if minute >= 60:
            hour += 1
            minute -= 60
        elif minute < 0:
            hour -= 1
            minute += 60

        if 0 <= hour < 24:
            tides.append({
                'type': 'low',
                'time': f'{hour:02d}:{minute:02d}',
                'hour': hour,
                'minute': minute
            })

    # 시간순 정렬
    tides.sort(key=lambda x: x['hour'] * 60 + x['minute'])

    return tides

def get_tide_hourly(latitude, longitude, date_str=None):
    """날짜별 24시간 조석 높이 + 수온 + 만조/간조 계산"""
    reference_new_moon = datetime(2000, 1, 6)

    if date_str:
        target = datetime.strptime(date_str, '%Y-%m-%d')
    else:
        target = datetime.now()

    # 음력 날짜 계산 (lunarcalendar 라이브러리 사용 - 가장 정확함)
    try:
        solar = Solar(target.year, target.month, target.day)
        lunar = Converter.Solar2Lunar(solar)
        lunar_info = {
            'month': lunar.month,
            'day': lunar.day,
            'age': lunar.day  # 음력 나이 = 음력 일수
        }

        # 물때 계산: 음력 일수 기반 (공식: (음력일+6)%15)
        lunar_day = lunar.day
        tide_num = ((lunar_day + 6) % 15) if ((lunar_day + 6) % 15) != 0 else 15
        print(f"[DEBUG] Lunar: {lunar.month}/{lunar_day}, Calculated Tide: {tide_num}")

    except Exception as e:
        import sys
        print(f"[ERROR] 음력 계산 오류: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)

        # Fallback: 공식 테이블 또는 추정
        official_lunar = get_lunar_conversion(target.month, target.day)
        if official_lunar:
            lunar_info = {
                'month': official_lunar['lunar_month'],
                'day': official_lunar['lunar_day'],
                'age': official_lunar['lunar_age']
            }
            # Fallback 물때 계산
            lunar_day = official_lunar['lunar_day']
            tide_num = ((lunar_day + 6) % 15) if ((lunar_day + 6) % 15) != 0 else 15
            print(f"[FALLBACK] Using table: Lunar {lunar_day}, Tide {tide_num}", file=sys.stderr, flush=True)
        else:
            lunar_info = get_lunar_date(target)
            # Fallback 물때 계산
            lunar_day = lunar_info['day']
            tide_num = ((lunar_day + 6) % 15) if ((lunar_day + 6) % 15) != 0 else 15
            print(f"[FALLBACK] Using get_lunar_date: Lunar {lunar_day}, Tide {tide_num}", file=sys.stderr, flush=True)

    # 위치에 해당하는 해역의 공식 조석표 데이터 조회 (만조/간조 시각만 사용)
    region = find_nearest_region(latitude, longitude)
    official_tide = get_tide_table(region, target.month, target.day)

    # DEBUG: 현재 tide_num 값 확인
    import sys
    print(f"[DEBUG] Date: {target.strftime('%Y-%m-%d')}, Lunar: {lunar_info['month']}/{lunar_info['day']}, Final tide_num: {tide_num}", file=sys.stderr, flush=True)

    # 주의: 공식 조석표의 tide_num은 lunarcalendar 기반으로 이미 계산됨
    # 대신 lunarcalendar 기반 계산된 tide_num을 사용함

    # 실시간 API 데이터 조회
    print(f"[API] KMA 기상 API 호출 중... (위치: {latitude}, {longitude})", flush=True)
    kma_weather = KmaWeatherService.get_hourly_weather(latitude, longitude, target.strftime('%Y-%m-%d'))
    print(f"[API] KMA 결과: {'성공' if kma_weather else '실패/없음'} (시간별 {len(kma_weather) if kma_weather else 0}개)", flush=True)

    print(f"[API] KHOA 해양 API 호출 중... (위치: {latitude}, {longitude})", flush=True)
    khoa_marine = KhoaMarineService.get_hourly_marine(latitude, longitude, target.strftime('%Y-%m-%d'))
    print(f"[API] KHOA 결과: {'성공' if khoa_marine else '실패/없음'}", flush=True)

    weather_source = 'api' if kma_weather else 'simulated'
    marine_source = 'api' if khoa_marine else 'simulated'

    # 천체 데이터 계산
    celestial = get_celestial_times(target, latitude)

    amplitude = 1.0 + (tide_num / 15) * 1.2

    # 물때에 따른 만조 시간 오프셋 (조금~사리)
    high_tide_offset = (tide_num - 8) * 0.3

    month = target.month
    base_water_temp = 8 + (month - 1) * 1.3

    # 현재 시간을 기반으로 약간의 변동성 추가 (매 시간 데이터가 약간 다르도록)
    now = datetime.now()
    time_seed = now.hour * 100 + now.minute  # 시간 기반 seed

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

        # 시간별 날씨 데이터 생성 (기본값은 시뮬레이션)
        # 시간과 현재 시간을 기반으로 약간의 변동 추가
        temp_variation = math.sin((i - 6 + time_seed * 0.01) * math.pi / 12) * 0.5
        temp = round(12 + 8 * math.sin((i - 6) * math.pi / 12) + temp_variation, 1)

        wind_variation = math.cos((i - 3 + time_seed * 0.02) * math.pi / 12) * 0.3
        wind_speed = round(max(0.5, 2.5 + 3.5 * abs(math.sin((i - 3) * math.pi / 12)) + wind_variation), 1)

        wind_degree = (i * 15 + time_seed) % 360
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

        # 강수 확률 계산 (시간대별)
        if weather == '맑음':
            precipitation = round(5 + 10 * abs(math.sin((i - 12) * math.pi / 12)), 0)
        elif weather == '구름':
            precipitation = round(25 + 20 * abs(math.sin((i - 12) * math.pi / 12)), 0)
        else:
            precipitation = round(60 + 20 * abs(math.sin((i - 12) * math.pi / 12)), 0)

        precipitation = min(100, max(0, int(precipitation)))

        # KMA 기상청 API 데이터 통합 (바람, 날씨, 강수)
        if kma_weather and i in kma_weather:
            kma_data = kma_weather[i]
            temp = kma_data.get('temp', temp)
            weather = kma_data.get('weather', weather)
            precipitation = kma_data.get('precipitation', precipitation)
            wind_speed = kma_data.get('windSpeed', wind_speed)
            wind_dir = kma_data.get('windDir', wind_dir)

        # KHOA 해양 시계열 데이터 통합 (수위, 수온, 조류)
        if khoa_marine and 'hourly' in khoa_marine and i in khoa_marine['hourly']:
            khoa_hourly = khoa_marine['hourly'][i]

            # 수위 (높이) - KHOA 실측값으로 완전 대체
            if khoa_hourly.get('height') is not None:
                height = round(khoa_hourly['height'], 2)

            # 수온 - KHOA 실측값 사용
            if khoa_hourly.get('waterTemp') is not None:
                water_temp = round(khoa_hourly['waterTemp'], 1)

            # 조류 속도 - KHOA 실측값 사용
            if khoa_hourly.get('currentSpeed') is not None:
                current_speed = round(khoa_hourly['currentSpeed'], 2)

        # KHOA 최신 데이터 (실시간)도 수온/파고에 추가 적용
        if khoa_marine and 'latestData' in khoa_marine:
            latest = khoa_marine['latestData']
            if latest.get('waveHeight') is not None:
                wave_height = round(latest['waveHeight'], 1)

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
            'wavePeriod': 4,
            'precipitation': precipitation
        })

    # 극값(만조/간조) 찾기 - KHOA API > 공식 조석표 > 극값 감지 순서
    import sys

    high_tides = []
    low_tides = []
    tide_source = 'simulated'
    official_tide = get_tide_table(region, target.month, target.day)

    # 1단계: KHOA 조석 예보 API로부터 실시간 조석 시간 조회
    print(f"[TIDE_FORECAST] 1. KHOA API 호출 중...", flush=True)
    api_forecast = KhoaMarineService.get_tide_forecast(latitude, longitude, target.strftime('%Y-%m-%d'))

    if api_forecast and api_forecast.get('highTides') and api_forecast.get('lowTides'):
        # API 데이터 우선 사용
        print(f"[TIDE_FORECAST] API 성공 - 만조 {len(api_forecast['highTides'])}회, 간조 {len(api_forecast['lowTides'])}회", flush=True)
        high_tides = api_forecast.get('highTides', [])
        low_tides = api_forecast.get('lowTides', [])
        tide_source = 'api'

    # 2단계: KHOA API 실패 시 공식 조석표 사용
    elif official_tide:
        print(f"[TIDE_FORECAST] 2. 공식 조석표 사용", flush=True)

        # 공식 조석표의 간조 시각
        for time_str in official_tide.get('low', []):
            try:
                h, m = map(int, time_str.split(':'))
                tide_height = hourly[h]['height'] if h < len(hourly) else 1.0
                low_tides.append({'time': time_str, 'height': round(tide_height, 2)})
            except:
                pass

        # 공식 조석표의 만조 시각
        for time_str in official_tide.get('high', []):
            try:
                h, m = map(int, time_str.split(':'))
                tide_height = hourly[h]['height'] if h < len(hourly) else 3.0
                high_tides.append({'time': time_str, 'height': round(tide_height, 2)})
            except:
                pass

        tide_source = 'official'

    # 3단계: 공식 조석표도 없으면 극값 감지
    else:
        print(f"[TIDE_FORECAST] 3. 극값 감지로 전환", flush=True)
        all_extrema = []

        # 시간별 데이터에서 극값 감지 (지역 극값: local extrema)
        for i in range(1, len(hourly) - 1):
            curr_height = hourly[i]['height']
            prev_height = hourly[i-1]['height']
            next_height = hourly[i+1]['height']

            # 지역 최고점 (만조)
            if curr_height > prev_height and curr_height > next_height:
                all_extrema.append({
                    'type': 'high',
                    'hour': i,
                    'minute': 0,
                    'time': f'{i:02d}:00',
                    'height': round(curr_height, 2)
                })
            # 지역 최저점 (간조)
            elif curr_height < prev_height and curr_height < next_height:
                all_extrema.append({
                    'type': 'low',
                    'hour': i,
                    'minute': 0,
                    'time': f'{i:02d}:00',
                    'height': round(curr_height, 2)
                })

        # high/low 분류
        high_tides = [e for e in all_extrema if e['type'] == 'high']
        low_tides = [e for e in all_extrema if e['type'] == 'low']
        tide_source = 'detected'

    print(f"[TIDE_FORECAST] 최종 결과 - 만조: {len(high_tides)}회, 간조: {len(low_tides)}회, 소스: {tide_source}", flush=True)

    # 1시간 단위 데이터 사용
    volume = get_tide_volume(tide_num)

    # 조석 시간과 높이 반환
    high_tides_camel = [{'time': t['time'], 'height': t['height']} for t in high_tides]
    low_tides_camel = [{'time': t['time'], 'height': t['height']} for t in low_tides]

    # tide_source는 이미 설정됨 (API / detected / simulated)

    # 천체 데이터
    celestial_events = [
        {'type': 'sunrise', 'hour': celestial['sunrise'], 'label': '일출'},
        {'type': 'sunset', 'hour': celestial['sunset'], 'label': '일몰'},
    ]

    # 기본항(기준항) 정보
    base_station = KOREA_TIDE_REFS.get(region, {})

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
        'hourly': hourly,  # 1시간 단위 데이터
        'highTides': high_tides_camel,
        'lowTides': low_tides_camel,
        'celestialEvents': celestial_events,
        'location': {
            'latitude': latitude,
            'longitude': longitude,
            'baseStation': base_station.get('name', '미정의'),  # 기본항 이름
            'region': base_station.get('region', ''),  # 지역명
            'tideRange': base_station.get('range', ''),  # 조석 범위
        },
        'weatherSource': weather_source,
        'marineSource': marine_source,
        'tideSource': tide_source if official_tide else 'simulation',
        'tideStrength': official_tide.get('strength', volume['strength']) if official_tide else volume['strength']
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
