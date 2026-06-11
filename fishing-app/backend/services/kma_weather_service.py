import requests
from datetime import datetime, timedelta
import math
from typing import Optional, Dict
from config import config

# 기상청 단기예보 API 서비스
# 위경도 → 기상청 격자 좌표(nx, ny) 변환 (Lambert Conformal Conic)
# 출처: 기상청 공식 변환식

class KmaWeatherService:
    BASE_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    CACHE = {}  # {(nx, ny, base_date, base_time): data, 'timestamp': datetime}
    CACHE_TTL = 1800  # 30분

    # 기상청 격자 변환 상수
    RE = 6371.00877  # 지구 반지름(km)
    GRID = 5.0  # 격자 간격(km)
    SLAT1 = 30.0  # 표준 위도 1
    SLAT2 = 60.0  # 표준 위도 2
    OLON = 126.0  # 기준점 경도
    OLAT = 37.0  # 기준점 위도
    XO = 43.0  # 기준점 격자 X
    YO = 136.0  # 기준점 격자 Y

    @staticmethod
    def _latlon_to_grid(lat: float, lon: float) -> tuple:
        """위경도를 기상청 격자 좌표(nx, ny)로 변환"""
        try:
            DEGRAD = math.pi / 180.0
            RADDEG = 180.0 / math.pi

            slat1 = KmaWeatherService.SLAT1 * DEGRAD
            slat2 = KmaWeatherService.SLAT2 * DEGRAD
            olon = KmaWeatherService.OLON * DEGRAD
            olat = KmaWeatherService.OLAT * DEGRAD

            sn = math.tan(math.pi / 4.0 + slat2 / 2.0) / math.tan(math.pi / 4.0 + slat1 / 2.0)
            sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)

            sf = math.tan(math.pi / 4.0 + slat1 / 2.0)
            sf = (math.pow(sf, sn) * math.cos(slat1)) / sn

            ro = math.tan(math.pi / 4.0 + olat / 2.0)
            ro = (KmaWeatherService.RE * sf / math.pow(ro, sn)) * KmaWeatherService.GRID

            ra = math.tan(math.pi / 4.0 + (lat * DEGRAD) / 2.0)
            ra = (KmaWeatherService.RE * sf / math.pow(ra, sn)) * KmaWeatherService.GRID

            theta = lon * DEGRAD - olon
            if theta > math.pi:
                theta -= 2.0 * math.pi
            if theta < -math.pi:
                theta += 2.0 * math.pi

            theta *= sn

            nx = math.floor(ro * math.sin(theta) + KmaWeatherService.XO + 0.5)
            ny = math.floor(ro - ra * math.cos(theta) + KmaWeatherService.YO + 0.5)

            return (int(nx), int(ny))
        except Exception as e:
            print(f"격자 변환 오류: {e}")
            return None

    @staticmethod
    def _get_base_datetime() -> tuple:
        """현재 시각 기준 가장 최근 발표시각(base_date, base_time) 계산
        기상청은 매 3시간마다 발표 (02, 05, 08, 11, 14, 17, 20, 23)
        발표 후 약 10분 지나서 조회 가능
        """
        now = datetime.now()
        hour = now.hour

        # 발표 시각: 02, 05, 08, 11, 14, 17, 20, 23
        base_hours = [2, 5, 8, 11, 14, 17, 20, 23]

        # 현재 시각 기준 최근 발표시각 찾기
        latest_base_hour = 23  # 기본값
        for bh in base_hours:
            if hour >= bh:
                latest_base_hour = bh

        base_date = now.strftime('%Y%m%d')
        base_time = f"{latest_base_hour:02d}00"

        return (base_date, base_time)

    @staticmethod
    def _get_weather_text(pty: int, sky: int) -> str:
        """강수형태(PTY) + 하늘상태(SKY) → 날씨 텍스트 변환
        PTY: 0=없음, 1=비, 2=비/눈, 3=눈
        SKY: 1=맑음, 3=구름많음, 4=흐림
        """
        if pty == 1:
            return "비"
        elif pty == 2:
            return "비/눈"
        elif pty == 3:
            return "눈"
        elif pty == 0:
            if sky == 1:
                return "맑음"
            elif sky == 3:
                return "구름"
            else:
                return "흐림"
        return "맑음"

    @staticmethod
    def get_hourly_weather(lat: float, lon: float, target_date: str) -> Optional[Dict]:
        """선택 위치/날짜의 시간별 날씨 조회

        Args:
            lat: 위도
            lon: 경도
            target_date: 조회 날짜 (YYYY-MM-DD)

        Returns:
            {hour: {temp, weather, precipitation, windSpeed, windDir}} 또는 None
        """
        api_key = config.get_api_key('kma_service_key')
        if not api_key:
            return None

        # 대상 날짜가 예보 커버리지 범위 확인 (오늘부터 D+2, 3일)
        today = datetime.now().date()
        target = datetime.strptime(target_date, '%Y-%m-%d').date()

        # 기상청 예보는 보통 D+2, 3일까지만 제공
        if target < today or (target - today).days > 3:
            return None

        # 격자 변환
        grid = KmaWeatherService._latlon_to_grid(lat, lon)
        if not grid:
            return None

        nx, ny = grid

        # 캐시 확인
        base_date, base_time = KmaWeatherService._get_base_datetime()
        cache_key = (nx, ny, base_date, base_time)

        if cache_key in KmaWeatherService.CACHE:
            cached_data, timestamp = KmaWeatherService.CACHE[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=KmaWeatherService.CACHE_TTL):
                return cached_data

        try:
            # API 호출
            params = {
                'serviceKey': api_key,
                'pageNo': '1',
                'numOfRows': '1000',
                'dataType': 'JSON',
                'base_date': base_date,
                'base_time': base_time,
                'nx': str(nx),
                'ny': str(ny)
            }

            response = requests.get(
                KmaWeatherService.BASE_URL,
                params=params,
                timeout=5
            )
            response.raise_for_status()

            data = response.json()

            if data.get('response', {}).get('header', {}).get('resultCode') != '00':
                return None

            items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])

            if not items:
                return None

            # 대상 날짜의 데이터만 필터링 및 시간별로 정렬
            target_fcst_date = target_date.replace('-', '')
            hourly_data = {}

            # 카테고리별 데이터 수집
            category_data = {}
            for item in items:
                fcst_date = item.get('fcstDate')
                fcst_hour = item.get('fcstTime', '').lstrip('0') or '0'
                hour = int(fcst_hour[:2])  # HH00 → HH

                if fcst_date != target_fcst_date:
                    continue

                category = item.get('category')
                value = item.get('fcstValue')

                if hour not in category_data:
                    category_data[hour] = {}

                category_data[hour][category] = value

            # 시간별 데이터 조립
            for hour in sorted(category_data.keys()):
                hour_data = category_data[hour]

                # 결측값(-999, -998 등 sentinel) 시간대는 건너뛰고 시뮬레이션 값 유지
                try:
                    if float(hour_data.get('TMP', 0)) <= -900 or float(hour_data.get('WSD', 0)) <= -900:
                        continue
                except (TypeError, ValueError):
                    continue

                temp = float(hour_data.get('TMP', 15.0))
                pty = int(hour_data.get('PTY', 0))
                sky = int(hour_data.get('SKY', 1))
                weather = KmaWeatherService._get_weather_text(pty, sky)
                precipitation = int(hour_data.get('POP', 0))
                wind_speed = float(hour_data.get('WSD', 2.5))
                wind_dir_deg = int(hour_data.get('VEC', 0))

                # 풍향 디그리 → 16방위 변환
                directions = ['북', '북북동', '북동', '동북동', '동', '동남동', '남동', '남남동',
                            '남', '남남서', '남서', '서남서', '서', '서북서', '북서', '북북서']
                wind_dir_idx = round(wind_dir_deg / 22.5) % 16
                wind_dir = directions[wind_dir_idx]

                hourly_data[hour] = {
                    'temp': round(temp, 1),
                    'weather': weather,
                    'precipitation': precipitation,
                    'windSpeed': round(wind_speed, 1),
                    'windDir': wind_dir
                }

            # 캐시 저장
            KmaWeatherService.CACHE[cache_key] = (hourly_data, datetime.now())

            return hourly_data if hourly_data else None

        except Exception as e:
            print(f"기상청 API 오류: {e}")
            return None
