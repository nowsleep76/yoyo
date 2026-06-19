import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
from config import config

# 국립해양조사원(KHOA) 해양관측 API
# 1. 최신 관측값 API (dtRecent): 실시간 수온, 파고 조회
# 2. 조위 시계열 API (tideHourly): 시간별 수위 조회 (오늘 기준)
# 3. 해수 온도 시계열 API (WaterTempHourly): 시간별 수온 조회
# 4. 해류 시계열 API (CurrentHourly): 시간별 조류 조회

class KhoaMarineService:
    BASE_URL_RECENT = "https://apis.data.go.kr/1192136/twRecent"
    BASE_URL_DT_RECENT = "https://apis.data.go.kr/1192136/dtRecent"  # Fallback
    BASE_URL_TIDE = "https://apis.data.go.kr/1192136/tideHourly"
    BASE_URL_WATER_TEMP = "https://apis.data.go.kr/1192136/WaterTempHourly"
    BASE_URL_CURRENT = "https://apis.data.go.kr/1192136/CurrentHourly"
    CACHE = {}  # {key: (data, timestamp)}
    CACHE_TTL = 600  # 10분

    @staticmethod
    def _get_field(item: Dict, *keys):
        """응답 필드명 표기가 통일되지 않은 경우를 대비해 여러 후보 키를 시도"""
        for key in keys:
            if key in item and item[key] not in (None, '', '-'):
                return item[key]
        return None

    @staticmethod
    def _get_from_cache(key: str) -> Optional[tuple]:
        """캐시에서 데이터 조회 (TTL 확인)"""
        if key in KhoaMarineService.CACHE:
            data, timestamp = KhoaMarineService.CACHE[key]
            if datetime.now() - timestamp < timedelta(seconds=KhoaMarineService.CACHE_TTL):
                return data
            del KhoaMarineService.CACHE[key]
        return None

    @staticmethod
    def _fetch_all() -> Optional[list]:
        """전체 조위관측소 최신 관측 데이터 조회 (캐시 적용)"""
        api_key = config.get_api_key('khoa_service_key')
        if not api_key:
            return None

        cache_key = 'khoa_recent_all'
        cached = KhoaMarineService._get_from_cache(cache_key)
        if cached:
            return cached

        params = {
            'serviceKey': api_key,
            'numOfRows': 200,
            'pageNo': 1,
            'resultType': 'json',
        }

        # twRecent API 시도 (Primary)
        try:
            print(f"[KHOA] twRecent API 호출 중...")
            response = requests.get(KhoaMarineService.BASE_URL_RECENT, params=params, timeout=5, verify=False)
            response.raise_for_status()
            data = response.json()

            body = data.get('response', {}).get('body', {})
            items = body.get('items', {})
            if isinstance(items, dict):
                items = items.get('item', [])
            if isinstance(items, dict):
                items = [items]

            if items:
                print(f"[KHOA] twRecent 성공: {len(items)}개 관측소")
                KhoaMarineService.CACHE[cache_key] = (items, datetime.now())
                return items
        except Exception as e:
            print(f"[KHOA] twRecent API 오류: {e}")

        # dtRecent API 시도 (Fallback)
        try:
            print(f"[KHOA] dtRecent API 폴백 중...")
            response = requests.get(KhoaMarineService.BASE_URL_DT_RECENT, params=params, timeout=5, verify=False)
            response.raise_for_status()
            data = response.json()

            body = data.get('response', {}).get('body', {})
            items = body.get('items', {})
            if isinstance(items, dict):
                items = items.get('item', [])
            if isinstance(items, dict):
                items = [items]

            if items:
                print(f"[KHOA] dtRecent 성공: {len(items)}개 관측소")
                KhoaMarineService.CACHE[cache_key] = (items, datetime.now())
                return items
        except Exception as e:
            print(f"[KHOA] dtRecent API 폴백 오류: {e}")

        print(f"[KHOA] 관측 데이터 조회 실패")
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
    def _get_obs_code(lat: float, lon: float) -> Optional[str]:
        """위경도로부터 가장 가까운 관측소의 ObsCode 조회"""
        items = KhoaMarineService._fetch_all()
        if not items:
            return None

        nearest = KhoaMarineService._find_nearest(lat, lon, items)
        if not nearest:
            return None

        # ObsCode 찾기 (다양한 필드명 시도)
        obs_code = KhoaMarineService._get_field(nearest, 'obs_code', 'ObsCode', 'obsCode', 'code')
        return obs_code

    @staticmethod
    def _fetch_hourly_tide(obs_code: str, date_str: str) -> Optional[Dict]:
        """시간별 조위(수위) 데이터 조회 (KHOA tideHourly API)

        Returns: {hour: height_in_meters} 형식
        """
        api_key = config.get_api_key('khoa_service_key')
        if not api_key or not obs_code:
            return None

        cache_key = f'tide_{obs_code}_{date_str}'
        cached = KhoaMarineService._get_from_cache(cache_key)
        if cached:
            return cached

        try:
            date_yyyymmdd = date_str.replace('-', '')
            params = {
                'serviceKey': api_key,
                'ObsCode': obs_code,
                'Date': date_yyyymmdd,
                'numOfRows': 100,
                'resultType': 'json'
            }

            response = requests.get(KhoaMarineService.BASE_URL_TIDE, params=params, timeout=5, verify=False)
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

            hourly_tide = {}
            for item in items:
                hour_str = item.get('TM', '')  # HHmm 형식
                height = item.get('HT')  # 수위 (미터)

                if hour_str and height:
                    try:
                        hour = int(hour_str[:2])
                        height_val = float(height)
                        hourly_tide[hour] = height_val
                    except (ValueError, TypeError):
                        continue

            KhoaMarineService.CACHE[cache_key] = (hourly_tide, datetime.now())
            return hourly_tide if hourly_tide else None

        except Exception as e:
            print(f"KHOA 조위 시계열 API 오류: {e}")
            return None

    @staticmethod
    def _fetch_hourly_water_temp(obs_code: str, date_str: str) -> Optional[Dict]:
        """시간별 수온 데이터 조회 (KHOA WaterTempHourly API)

        Returns: {hour: temperature_in_celsius} 형식
        """
        api_key = config.get_api_key('khoa_service_key')
        if not api_key or not obs_code:
            return None

        cache_key = f'water_temp_{obs_code}_{date_str}'
        cached = KhoaMarineService._get_from_cache(cache_key)
        if cached:
            return cached

        try:
            date_yyyymmdd = date_str.replace('-', '')
            params = {
                'serviceKey': api_key,
                'ObsCode': obs_code,
                'Date': date_yyyymmdd,
                'numOfRows': 100,
                'resultType': 'json'
            }

            response = requests.get(KhoaMarineService.BASE_URL_WATER_TEMP, params=params, timeout=5, verify=False)
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

            hourly_water_temp = {}
            for item in items:
                hour_str = item.get('TM', '')  # HHmm 형식
                temp = item.get('WT')  # 수온 (섭씨)

                if hour_str and temp:
                    try:
                        hour = int(hour_str[:2])
                        temp_val = float(temp)
                        hourly_water_temp[hour] = temp_val
                    except (ValueError, TypeError):
                        continue

            KhoaMarineService.CACHE[cache_key] = (hourly_water_temp, datetime.now())
            return hourly_water_temp if hourly_water_temp else None

        except Exception as e:
            print(f"KHOA 수온 시계열 API 오류: {e}")
            return None

    @staticmethod
    def _fetch_hourly_current(obs_code: str, date_str: str) -> Optional[Dict]:
        """시간별 조류(해류) 데이터 조회 (KHOA CurrentHourly API)

        Returns: {hour: current_speed_in_m_per_s} 형식
        """
        api_key = config.get_api_key('khoa_service_key')
        if not api_key or not obs_code:
            return None

        cache_key = f'current_{obs_code}_{date_str}'
        cached = KhoaMarineService._get_from_cache(cache_key)
        if cached:
            return cached

        try:
            date_yyyymmdd = date_str.replace('-', '')
            params = {
                'serviceKey': api_key,
                'ObsCode': obs_code,
                'Date': date_yyyymmdd,
                'numOfRows': 100,
                'resultType': 'json'
            }

            response = requests.get(KhoaMarineService.BASE_URL_CURRENT, params=params, timeout=5, verify=False)
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

            hourly_current = {}
            for item in items:
                hour_str = item.get('TM', '')  # HHmm 형식
                speed = item.get('CV')  # 조류 속도 (m/s)

                if hour_str and speed:
                    try:
                        hour = int(hour_str[:2])
                        speed_val = float(speed)
                        hourly_current[hour] = speed_val
                    except (ValueError, TypeError):
                        continue

            KhoaMarineService.CACHE[cache_key] = (hourly_current, datetime.now())
            return hourly_current if hourly_current else None

        except Exception as e:
            print(f"KHOA 조류 시계열 API 오류: {e}")
            return None

    @staticmethod
    def get_hourly_marine(lat: float, lon: float, target_date: str) -> Optional[Dict]:
        """선택 위치/날짜의 시간별 해양관측 데이터 통합 조회

        Args:
            lat: 위도
            lon: 경도
            target_date: 조회 날짜 (YYYY-MM-DD)

        Returns:
            {
                hourly: {
                    hour: {height, waterTemp, currentSpeed}
                },
                latestData: {waterTemp, waveHeight}  (실시간)
            } 또는 None
        """
        # 관측소 코드 조회
        obs_code = KhoaMarineService._get_obs_code(lat, lon)
        if not obs_code:
            return None

        # 시간별 데이터 조회
        hourly_tide = KhoaMarineService._fetch_hourly_tide(obs_code, target_date)
        hourly_water_temp = KhoaMarineService._fetch_hourly_water_temp(obs_code, target_date)
        hourly_current = KhoaMarineService._fetch_hourly_current(obs_code, target_date)

        # 어느 것이라도 데이터가 없으면 None 반환
        if not any([hourly_tide, hourly_water_temp, hourly_current]):
            return None

        # 시간별 데이터 병합 (0~23시)
        hourly_marine = {}
        for hour in range(24):
            hourly_marine[hour] = {
                'height': hourly_tide.get(hour) if hourly_tide else None,
                'waterTemp': hourly_water_temp.get(hour) if hourly_water_temp else None,
                'currentSpeed': hourly_current.get(hour) if hourly_current else None
            }

        # 최신 실시간 데이터도 병합
        items = KhoaMarineService._fetch_all()
        nearest = KhoaMarineService._find_nearest(lat, lon, items) if items else None
        latest_data = {}

        if nearest:
            water_temp = KhoaMarineService._get_field(nearest, 'water_temp', 'waterTemp', 'WaterTemp', 'wtem')
            if water_temp is not None:
                try:
                    latest_data['waterTemp'] = float(water_temp)
                except (TypeError, ValueError):
                    pass

            wave_height = KhoaMarineService._get_field(nearest, 'wave_height', 'waveHeight', 'WaveHeight', 'wvhgt')
            if wave_height is not None:
                try:
                    latest_data['waveHeight'] = float(wave_height)
                except (TypeError, ValueError):
                    pass

        return {
            'hourly': hourly_marine,
            'latestData': latest_data
        }

    @staticmethod
    def get_tide_forecast(latitude: float, longitude: float, date_str: str) -> Optional[Dict]:
        """KHOA 조석 예보 API - 만조/간조 시간 및 높이 조회

        Args:
            latitude: 위도
            longitude: 경도
            date_str: 날짜 (YYYY-MM-DD 형식)

        Returns:
            {
                'highTides': [{'time': 'HH:MM', 'height': float}, ...],
                'lowTides': [{'time': 'HH:MM', 'height': float}, ...],
                'source': 'api'
            }
        """
        api_key = config.get_api_key('khoa_service_key')
        if not api_key:
            print(f"[KHOA_TIDE] API 키 없음")
            return None

        # 관측소 코드 조회
        obs_code = KhoaMarineService._get_obs_code(latitude, longitude)
        if not obs_code:
            print(f"[KHOA_TIDE] 관측소 코드 조회 실패")
            return None

        try:
            date_yyyymmdd = date_str.replace('-', '')

            # KHOA 조석 예보 API
            api_url = "https://apis.data.go.kr/1192136/TideResponse"
            params = {
                'serviceKey': api_key,
                'ObsCode': obs_code,
                'Date': date_yyyymmdd,
                'resultType': 'json'
            }

            print(f"[KHOA_TIDE] 조석 예보 API 호출: ObsCode={obs_code}, Date={date_yyyymmdd}", flush=True)
            response = requests.get(api_url, params=params, timeout=5, verify=False)
            response.raise_for_status()
            data = response.json()

            # 응답 파싱
            body = data.get('response', {}).get('body', {})
            items = body.get('items', {})

            if isinstance(items, dict):
                items = items.get('item', [])
            if isinstance(items, dict):
                items = [items]

            if not items or len(items) == 0:
                print(f"[KHOA_TIDE] 응답 데이터 없음")
                return None

            high_tides = []
            low_tides = []

            # 각 항목 파싱 (만조/간조)
            for item in items:
                # 시간: HH:MM 형식 (예: "07:47")
                time_str = KhoaMarineService._get_field(item, 'time', 'Time', 'tm', 'TM')

                # 높이: float 값 (예: 3.8)
                height_str = KhoaMarineService._get_field(item, 'height', 'Height', 'heig', 'HEIG', 'value')

                # 극값 타입: H(만조) 또는 L(간조)
                type_str = KhoaMarineService._get_field(item, 'type', 'Type', 'gubun', 'GUBUN')

                if not time_str or not height_str or not type_str:
                    continue

                try:
                    height = float(height_str)
                except (TypeError, ValueError):
                    height = 0.0

                tide_info = {'time': time_str, 'height': height}

                # 만조(H) 또는 간조(L) 분류
                if 'H' in str(type_str).upper():
                    high_tides.append(tide_info)
                elif 'L' in str(type_str).upper():
                    low_tides.append(tide_info)

            # 시간순 정렬
            high_tides.sort(key=lambda x: x['time'])
            low_tides.sort(key=lambda x: x['time'])

            print(f"[KHOA_TIDE] 조석 데이터 수신: 만조 {len(high_tides)}회, 간조 {len(low_tides)}회", flush=True)

            if len(high_tides) == 0 and len(low_tides) == 0:
                print(f"[KHOA_TIDE] 조석 데이터 파싱 실패")
                return None

            return {
                'highTides': high_tides,
                'lowTides': low_tides,
                'source': 'api'
            }

        except requests.exceptions.RequestException as e:
            print(f"[KHOA_TIDE] API 호출 오류: {e}")
            return None
        except Exception as e:
            print(f"[KHOA_TIDE] 처리 오류: {e}")
            return None
