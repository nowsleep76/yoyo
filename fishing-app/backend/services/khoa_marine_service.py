import requests
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

# 국립해양조사원(KHOA) 실시간 해양관측 API 서비스
# 각 해역의 대표 관측소 위경도 정보로 최근접 관측소 매핑
# 실시간 데이터만 제공하므로 target_date가 오늘인 경우에만 조회

class KhoaMarineService:
    BASE_URL = "http://apis.data.go.kr/1763000/oceanscience/oceanProductSearch/searchListResearch"
    CACHE = {}  # {observation_code: (data, timestamp)}
    CACHE_TTL = 600  # 10분

    # 주요 해역 대표 관측소 (Code, 위도, 경도, 이름)
    # 실제로는 전국 관측소가 있지만, 여기서는 주요 지역만 포함
    OBSERVATION_STATIONS = [
        {'code': '52402', 'lat': 37.254, 'lon': 126.600, 'name': '인천'},
        {'code': '52403', 'lat': 37.425, 'lon': 126.605, 'name': '덕적도'},
        {'code': '52405', 'lat': 37.633, 'lon': 126.975, 'name': '동해'},
        {'code': '52406', 'lat': 36.985, 'lon': 127.108, 'name': '거문도'},
        {'code': '52411', 'lat': 35.280, 'lon': 128.620, 'name': '부산'},
        {'code': '52413', 'lat': 35.095, 'lon': 129.380, 'name': '울산'},
        {'code': '52419', 'lat': 33.241, 'lon': 126.564, 'name': '제주'},
        {'code': '52420', 'lat': 33.100, 'lon': 126.180, 'name': '마라도'},
        {'code': '52421', 'lat': 37.024, 'lon': 125.150, 'name': '칠발도'},
    ]

    @staticmethod
    def _find_nearest_station(lat: float, lon: float) -> Optional[Dict]:
        """위경도 기준 최근접 관측소 찾기"""
        if not lat or not lon:
            return None

        min_distance = float('inf')
        nearest_station = None

        for station in KhoaMarineService.OBSERVATION_STATIONS:
            # 간단한 유클리드 거리 계산 (정확한 지리적 거리는 필요시 Haversine 적용)
            distance = ((lat - station['lat']) ** 2 + (lon - station['lon']) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest_station = station

        return nearest_station

    @staticmethod
    def _get_hourly_data(obs_code: str) -> Optional[Dict]:
        """관측소 코드로 실시간 해양관측 데이터 조회

        Args:
            obs_code: 관측소 코드 (예: '52402')

        Returns:
            {waveHeight, waterTemp} 또는 None
        """
        api_key = os.getenv('KHOA_SERVICE_KEY')
        if not api_key:
            return None

        # 캐시 확인
        if obs_code in KhoaMarineService.CACHE:
            cached_data, timestamp = KhoaMarineService.CACHE[obs_code]
            if datetime.now() - timestamp < timedelta(seconds=KhoaMarineService.CACHE_TTL):
                return cached_data

        try:
            # 실시간 관측 API 호출
            # 기본 endpoint: 근처의 실시간 관측값을 반환하는 것으로 가정
            params = {
                'serviceKey': api_key,
                'obs_code': obs_code,
                'response_format': 'JSON'
            }

            response = requests.get(
                KhoaMarineService.BASE_URL,
                params=params,
                timeout=5
            )
            response.raise_for_status()

            data = response.json()

            # API 응답 구조에 따라 파싱
            # 아래는 기본 가정이며, 실제 응답 구조에 맞춰 수정 필요
            if data.get('status') != 'success' and data.get('response') is None:
                return None

            result = data.get('response', {})

            # 실시간 데이터 추출
            # 대부분의 KHOA API는 가장 최근 관측값을 single object 형태로 반환
            if isinstance(result, dict):
                wave_height = result.get('waveHeight') or result.get('wave_height')
                water_temp = result.get('waterTemp') or result.get('water_temp')

                marine_data = {}
                if wave_height is not None:
                    marine_data['waveHeight'] = float(wave_height)
                if water_temp is not None:
                    marine_data['waterTemp'] = float(water_temp)

                if marine_data:
                    # 캐시 저장
                    KhoaMarineService.CACHE[obs_code] = (marine_data, datetime.now())
                    return marine_data

            return None

        except Exception as e:
            print(f"KHOA API 오류 ({obs_code}): {e}")
            return None

    @staticmethod
    def get_hourly_marine(lat: float, lon: float, target_date: str) -> Optional[Dict]:
        """선택 위치/날짜의 해양관측 데이터 조회

        Args:
            lat: 위도
            lon: 경도
            target_date: 조회 날짜 (YYYY-MM-DD)

        Returns:
            {waveHeight, waterTemp} 또는 None
        """
        api_key = os.getenv('KHOA_SERVICE_KEY')
        if not api_key:
            return None

        # KHOA는 실시간 데이터만 제공하므로 target_date가 오늘인 경우에만 조회
        today = datetime.now().date()
        target = datetime.strptime(target_date, '%Y-%m-%d').date()

        if target != today:
            # 과거/미래 날짜는 데이터 없음
            return None

        # 최근접 관측소 찾기
        nearest_station = KhoaMarineService._find_nearest_station(lat, lon)
        if not nearest_station:
            return None

        # 관측소 데이터 조회
        return KhoaMarineService._get_hourly_data(nearest_station['code'])
