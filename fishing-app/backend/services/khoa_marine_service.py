import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
from config import config

# 국립해양조사원(KHOA) 조위관측소 최신 관측 데이터 API (공공데이터포털 1192136/dtRecent)
# https://www.data.go.kr/data/15038980/openapi.do
# 전국 조위관측소의 최신 관측값(수온/기온/기압/조위/염분/유속 등)을 한번에 반환
# - ObsCode 없이 호출하면 전체 관측소 목록을 반환하므로, 응답에 포함된 각 관측소의
#   위경도와 요청 위치를 비교해 최근접 관측소를 선택한다.
# - 실시간 데이터만 제공하므로 target_date가 오늘인 경우에만 조회한다.

class KhoaMarineService:
    BASE_URL = "https://apis.data.go.kr/1192136/dtRecent"
    CACHE = None  # (data_list, timestamp)
    CACHE_TTL = 600  # 10분

    @staticmethod
    def _get_field(item: Dict, *keys):
        """응답 필드명 표기가 통일되지 않은 경우를 대비해 여러 후보 키를 시도"""
        for key in keys:
            if key in item and item[key] not in (None, '', '-'):
                return item[key]
        return None

    @staticmethod
    def _fetch_all() -> Optional[list]:
        """전체 조위관측소 최신 관측 데이터 조회 (캐시 적용)"""
        api_key = config.get_api_key('khoa_service_key')
        if not api_key:
            return None

        if KhoaMarineService.CACHE:
            cached_data, timestamp = KhoaMarineService.CACHE
            if datetime.now() - timestamp < timedelta(seconds=KhoaMarineService.CACHE_TTL):
                return cached_data

        try:
            params = {
                'serviceKey': api_key,
                'numOfRows': 200,
                'pageNo': 1,
                'resultType': 'json',
            }

            response = requests.get(KhoaMarineService.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            body = data.get('response', {}).get('body', {})
            items = body.get('items', {})
            if isinstance(items, dict):
                items = items.get('item', [])
            if isinstance(items, dict):
                items = [items]
            if not items:
                return None

            KhoaMarineService.CACHE = (items, datetime.now())
            return items

        except Exception as e:
            print(f"KHOA API 오류: {e}")
            return None

    @staticmethod
    def _find_nearest(lat: float, lon: float, items: list) -> Optional[Dict]:
        """응답에 포함된 관측소 위경도 기준 최근접 관측소 데이터 선택"""
        nearest = None
        min_distance = float('inf')

        for item in items:
            station_lat = KhoaMarineService._get_field(item, 'lat', 'Lat', 'obs_lat', 'obsLat', 'latitude')
            station_lon = KhoaMarineService._get_field(item, 'lon', 'Lon', 'obs_lon', 'obsLon', 'longitude')

            if station_lat is None or station_lon is None:
                continue

            try:
                station_lat = float(station_lat)
                station_lon = float(station_lon)
            except (TypeError, ValueError):
                continue

            distance = ((lat - station_lat) ** 2 + (lon - station_lon) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest = item

        return nearest

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
        # KHOA는 실시간 데이터만 제공하므로 target_date가 오늘인 경우에만 조회
        today = datetime.now().date()
        target = datetime.strptime(target_date, '%Y-%m-%d').date()
        if target != today:
            return None

        items = KhoaMarineService._fetch_all()
        if not items:
            return None

        nearest = KhoaMarineService._find_nearest(lat, lon, items)
        if not nearest:
            return None

        marine_data = {}

        water_temp = KhoaMarineService._get_field(nearest, 'water_temp', 'waterTemp', 'WaterTemp', 'wtem')
        if water_temp is not None:
            try:
                marine_data['waterTemp'] = float(water_temp)
            except (TypeError, ValueError):
                pass

        wave_height = KhoaMarineService._get_field(nearest, 'wave_height', 'waveHeight', 'WaveHeight', 'wvhgt')
        if wave_height is not None:
            try:
                marine_data['waveHeight'] = float(wave_height)
            except (TypeError, ValueError):
                pass

        return marine_data or None
