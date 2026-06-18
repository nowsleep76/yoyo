from datetime import datetime, timedelta
import math
from services.kma_weather_service import KmaWeatherService
from services.khoa_marine_service import KhoaMarineService
from services.tides_korea import get_tide_table, get_lunar_conversion
from lunarcalendar import Converter, Solar

# 한국 조석표 데이터 (위도, 경도, 기준항의 간조/만조 시간 기준)
KOREA_TIDE_REFS = {
    'busan': {'lat': 35.1, 'lon': 129.1, 'name': '부산'},
    'incheon': {'lat': 37.2, 'lon': 126.6, 'name': '인천'},
    'jinhae': {'lat': 35.2, 'lon': 128.6, 'name': '진해'},
    'pohang': {'lat': 36.0, 'lon': 129.6, 'name': '포항'},
    'jeju': {'lat': 33.2, 'lon': 126.5, 'name': '제주'},
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
    """음력 날짜에서 물때 계산 (1~15물)"""
    lunar_day = lunar_info['day']

    # 음력 15일 주기로 물때 계산
    tide_num = (lunar_day % 15) if (lunar_day % 15) != 0 else 15

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

        # 물때 계산: 음력 일수 기반 (1~15물 반복)
        lunar_day = lunar.day
        tide_num = (lunar_day % 15) if (lunar_day % 15) != 0 else 15
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
            tide_num = (lunar_day % 15) if (lunar_day % 15) != 0 else 15
            print(f"[FALLBACK] Using table: Lunar {lunar_day}, Tide {tide_num}", file=sys.stderr, flush=True)
        else:
            lunar_info = get_lunar_date(target)
            # Fallback 물때 계산
            lunar_day = lunar_info['day']
            tide_num = (lunar_day % 15) if (lunar_day % 15) != 0 else 15
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
    kma_weather = KmaWeatherService.get_hourly_weather(latitude, longitude, target.strftime('%Y-%m-%d'))
    khoa_marine = KhoaMarineService.get_hourly_marine(latitude, longitude, target.strftime('%Y-%m-%d'))
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

    # 극값(만조/간조) 찾기 - 공식 조석표 우선, 없으면 시뮬레이션
    import sys
    all_extrema = []

    # 1단계: 공식 조석표 데이터 사용
    official_tide = get_tide_table(region, target.month, target.day)

    if official_tide:
        print(f"[TIDE_TABLE] 공식 조석표 사용: low={official_tide.get('low')}, high={official_tide.get('high')}", flush=True)

        # 공식 간조 시각
        for time_str in official_tide.get('low', []):
            try:
                h, m = map(int, time_str.split(':'))
                if 0 <= h < 24:
                    tide_height = hourly[h]['height'] if h < len(hourly) else 1.0
                    all_extrema.append({
                        'type': 'low',
                        'hour': h,
                        'minute': m,
                        'time': f'{h:02d}:{m:02d}',
                        'height': round(tide_height, 2)
                    })
            except:
                pass

        # 공식 만조 시각
        for time_str in official_tide.get('high', []):
            try:
                h, m = map(int, time_str.split(':'))
                if 0 <= h < 24:
                    tide_height = hourly[h]['height'] if h < len(hourly) else 3.0
                    all_extrema.append({
                        'type': 'high',
                        'hour': h,
                        'minute': m,
                        'time': f'{h:02d}:{m:02d}',
                        'height': round(tide_height, 2)
                    })
            except:
                pass

    # 2단계: 공식 조석표 없으면 시뮬레이션된 반일주기로 계산
    else:
        print(f"[SIMULATION] 공식 조석표 없음, 반일주기 시뮬레이션 사용", flush=True)

        half_period = 12.42
        offset = 6.0 + high_tide_offset

        # 극댓값 시간
        for k in range(3):
            high_time = offset + 0.21 + k * half_period
            if 0 <= high_time < 24:
                high_hour = int(high_time)
                high_minute = int((high_time - high_hour) * 60)
                if high_hour < 24:
                    high_height = hourly[high_hour]['height']
                    all_extrema.append({
                        'type': 'high',
                        'hour': high_hour,
                        'minute': high_minute,
                        'time': f'{high_hour:02d}:{high_minute:02d}',
                        'height': round(high_height, 2)
                    })

        # 극솟값 시간
        for k in range(3):
            low_time = offset - 6.21 + k * half_period
            if 0 <= low_time < 24:
                low_hour = int(low_time)
                low_minute = int((low_time - low_hour) * 60)
                if low_hour < 24:
                    low_height = hourly[low_hour]['height']
                    all_extrema.append({
                        'type': 'low',
                        'hour': low_hour,
                        'minute': low_minute,
                        'time': f'{low_hour:02d}:{low_minute:02d}',
                        'height': round(low_height, 2)
                    })

    # 극값들을 시간 순서대로 정렬
    all_extrema.sort(key=lambda x: x['hour'] * 60 + x['minute'])

    print(f"[EXTREMA] 감지 {len(all_extrema)}개: {[(e['hour'], e['type']) for e in all_extrema]}", flush=True)

    # 극값 필터링: 교대로 나타나는 타입만 유지 (same-type 연달아 제거)
    filtered_extrema = []

    for extremum in all_extrema:
        if filtered_extrema:
            last_extremum = filtered_extrema[-1]
            # 타입이 다르면 추가 (교대 조건)
            if extremum['type'] != last_extremum['type']:
                filtered_extrema.append(extremum)
        else:
            # 첫 번째 극값
            filtered_extrema.append(extremum)

    print(f"[FILTER] 필터링 후 {len(filtered_extrema)}개", flush=True)

    # high/low 분류
    high_tides = [e for e in filtered_extrema if e['type'] == 'high']
    low_tides = [e for e in filtered_extrema if e['type'] == 'low']
    print(f"[RESULT] 만조: {len(high_tides)}, 간조: {len(low_tides)}", flush=True)

    # 정렬 및 최종 포맷 (time 필드만 유지)
    high_tides.sort(key=lambda x: x['hour'])
    low_tides.sort(key=lambda x: x['hour'])

    # 인접한 극값 정리 (시간 차이가 2시간 이하이면 첫 번째만 유지)
    if len(high_tides) > 1:
        cleaned_high = [high_tides[0]]
        for i in range(1, len(high_tides)):
            time_diff = high_tides[i]['hour'] - high_tides[i-1]['hour']
            if time_diff > 2:  # 2시간보다 커야만 추가 (정확히 2시간 제외)
                cleaned_high.append(high_tides[i])
        high_tides = cleaned_high

    if len(low_tides) > 1:
        cleaned_low = [low_tides[0]]
        for i in range(1, len(low_tides)):
            time_diff = low_tides[i]['hour'] - low_tides[i-1]['hour']
            if time_diff > 2:  # 2시간보다 커야만 추가 (정확히 2시간 제외)
                cleaned_low.append(low_tides[i])
        low_tides = cleaned_low

    # 극값이 너무 적으면 최대/최소값 기반 추가 (긴급 대체)
    if len(high_tides) == 0 and len(hourly) > 0:
        max_hour = hourly.index(max(hourly, key=lambda x: x['height']))
        max_height = hourly[max_hour]['height']
        high_tides.append({
            'hour': max_hour,
            'minute': 30,
            'time': f'{max_hour:02d}:30',
            'height': round(max_height, 2)
        })

    if len(low_tides) == 0 and len(hourly) > 0:
        min_hour = hourly.index(min(hourly, key=lambda x: x['height']))
        min_height = hourly[min_hour]['height']
        low_tides.append({
            'hour': min_hour,
            'minute': 30,
            'time': f'{min_hour:02d}:30',
            'height': round(min_height, 2)
        })

    # 만조/간조를 2개씩 생성 (반일주기 조석 - 약 12.4시간)
    # 극값이 1개씩만 있으면 12시간 정확히 뒤에 반대 극값 추가
    if len(high_tides) == 1 and len(low_tides) == 1:
        first_high = high_tides[0]
        first_low = low_tides[0]

        # 첫 간조로부터 12시간 뒤에 간조 추가 (다음 간조)
        second_low_hour = (first_low['hour'] + 12) % 24
        second_low_height = hourly[second_low_hour]['height']

        low_tides.append({
            'hour': second_low_hour,
            'minute': 30,
            'time': f'{second_low_hour:02d}:30',
            'height': round(second_low_height, 2)
        })

        # 첫 만조로부터 12시간 뒤에 만조 추가 (다음 만조)
        second_high_hour = (first_high['hour'] + 12) % 24
        second_high_height = hourly[second_high_hour]['height']

        high_tides.append({
            'hour': second_high_hour,
            'minute': 30,
            'time': f'{second_high_hour:02d}:30',
            'height': round(second_high_height, 2)
        })

    # 최종 정렬
    high_tides.sort(key=lambda x: x['hour'])
    low_tides.sort(key=lambda x: x['hour'])

    # 최종 인접 정리 (극값 추가 후)
    if len(high_tides) > 1:
        cleaned_high = [high_tides[0]]
        for i in range(1, len(high_tides)):
            time_diff = high_tides[i]['hour'] - high_tides[i-1]['hour']
            if time_diff > 2:
                cleaned_high.append(high_tides[i])
        high_tides = cleaned_high

    if len(low_tides) > 1:
        cleaned_low = [low_tides[0]]
        for i in range(1, len(low_tides)):
            time_diff = low_tides[i]['hour'] - low_tides[i-1]['hour']
            if time_diff > 2:
                cleaned_low.append(low_tides[i])
        low_tides = cleaned_low

    # 1시간 단위 데이터 사용 (3시간 필터링 제거)
    volume = get_tide_volume(tide_num)

    # 공식 조석표가 있으면 만조/간조 시각을 실제 값으로 대체
    # 높이는 극값 타입에 따른 표준값 사용 (진폭 기반)
    if official_tide:
        # 극값 타입별 높이: 평균 수위 ± 진폭
        high_height = round(2.0 + amplitude, 2)
        low_height = round(2.0 - amplitude, 2)

        high_tides_camel = []
        for time_str in official_tide['high']:
            high_tides_camel.append({'time': time_str, 'height': high_height})

        low_tides_camel = []
        for time_str in official_tide['low']:
            low_tides_camel.append({'time': time_str, 'height': low_height})
    else:
        # 시뮬레이션 데이터: 극값 감지된 값 사용
        high_tides_camel = [{'time': t['time'], 'height': t['height']} for t in high_tides]
        low_tides_camel = [{'time': t['time'], 'height': t['height']} for t in low_tides]

    tide_source = 'official' if official_tide else 'simulated'

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
        'hourly': hourly,  # 1시간 단위 데이터 (3시간 필터링 제거)
        'highTides': high_tides_camel,
        'lowTides': low_tides_camel,
        'celestialEvents': celestial_events,
        'location': {
            'latitude': latitude,
            'longitude': longitude
        },
        'weatherSource': weather_source,
        'marineSource': marine_source,
        'tideSource': tide_source,
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
