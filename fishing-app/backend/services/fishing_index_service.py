import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
from config import config

# 해양수산부 국립해양조사원 바다낚시지수 조회 API

class FishingIndexService:
    BASE_URL = "http://apis.data.go.kr/1763000/FishingBlue/baseFishingIndex"
    CACHE = {}  # {(date, lat, lon): (data, timestamp)}
    CACHE_TTL = 3600  # 1시간

    # 주요 해역 낚시터 기본 설정 (API에서 제공하는 지역 코드)
    FISHING_REGIONS = {
        'busan': {'lat': 35.1595, 'lon': 129.1603, 'name': '부산 해운대', 'area_code': '0001'},
        'incheon': {'lat': 37.4559, 'lon': 126.7053, 'name': '인천 강화', 'area_code': '0002'},
        'jeju': {'lat': 33.4171, 'lon': 126.2335, 'name': '제주 협재', 'area_code': '0003'},
    }

    @staticmethod
    def get_fishing_index(lat: float, lon: float, target_date: str) -> Optional[Dict]:
        """위치와 날짜에 따른 바다낚시지수 조회

        API 실패 시 자동으로 시뮬레이션 데이터 반환
        """
        # 대상 날짜 유효성 확인 (오늘부터 D+3까지만)
        today = datetime.now().date()
        target = datetime.strptime(target_date, '%Y-%m-%d').date()

        if target < today or (target - today).days > 3:
            # 범위 밖이면 시뮬레이션으로 대체
            return FishingIndexService._generate_simulated_data(lat, lon, target_date)

        # 캐시 확인
        cache_key = (target_date, round(lat, 2), round(lon, 2))
        if cache_key in FishingIndexService.CACHE:
            cached_data, timestamp = FishingIndexService.CACHE[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=FishingIndexService.CACHE_TTL):
                return cached_data

        # API 호출 시도
        api_key = config.get_api_key('fishing_index_api_key')
        if api_key:
            try:
                # 최근접 지역 찾기
                nearest_region = FishingIndexService._find_nearest_region(lat, lon)
                if not nearest_region:
                    return FishingIndexService._generate_simulated_data(lat, lon, target_date)

                # API 호출
                target_date_str = target_date.replace('-', '')
                params = {
                    'serviceKey': api_key,
                    'search_area_code': nearest_region['area_code'],
                    'search_date': target_date_str,
                    'output': 'json'
                }

                response = requests.get(
                    FishingIndexService.BASE_URL,
                    params=params,
                    timeout=10
                )
                response.raise_for_status()

                data = response.json()

                # API 응답 파싱
                if data.get('resultCode') == '00' or data.get('result'):
                    result = data.get('result', {})

                    # 종합 낚시지수 (0-10)
                    overall_index = int(result.get('baseFishingIndex', 5))

                    # 어종별 지수
                    fish_species = {
                        '우럭': int(result.get('redfin_Index', 5)),
                        '감성돔': int(result.get('blackSeabream_Index', 5)),
                        '광어': int(result.get('flatfish_Index', 5)),
                        '농어': int(result.get('seabass_Index', 5)),
                    }

                    # 해황 조건
                    conditions = {
                        'water_temp': float(result.get('waterTemperature', 18.0)),
                        'wave_height': float(result.get('waveHeight', 0.5)),
                        'wind_speed': float(result.get('windSpeed', 3.0)),
                        'visibility': FishingIndexService._get_visibility(result.get('visibility', 3))
                    }

                    # 시간별 지수
                    hourly = FishingIndexService._generate_hourly_index(
                        overall_index,
                        target_date
                    )

                    fishing_data = {
                        'date': target_date,
                        'location': nearest_region['name'],
                        'lat': lat,
                        'lon': lon,
                        'overall_index': overall_index,
                        'fish_species': fish_species,
                        'conditions': conditions,
                        'hourly': hourly,
                        'data_source': 'api'  # 실제 API 데이터
                    }

                    # 캐시 저장
                    FishingIndexService.CACHE[cache_key] = (fishing_data, datetime.now())
                    return fishing_data

            except Exception as e:
                print(f"낚시지수 API 오류 (자동 폴백): {e}")
                # API 실패 → 시뮬레이션으로 대체
                return FishingIndexService._generate_simulated_data(lat, lon, target_date)

        # API 키 없음 → 시뮬레이션
        return FishingIndexService._generate_simulated_data(lat, lon, target_date)

    @staticmethod
    def _find_nearest_region(lat: float, lon: float) -> Optional[Dict]:
        """위경도 기준 가장 가까운 낚시 지역 찾기"""
        min_distance = float('inf')
        nearest = None

        for region_key, region_data in FishingIndexService.FISHING_REGIONS.items():
            distance = ((lat - region_data['lat']) ** 2 + (lon - region_data['lon']) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest = region_data

        return nearest

    @staticmethod
    def _get_visibility(visibility_code: int) -> str:
        """가시거리 코드를 문자로 변환"""
        visibility_map = {
            0: '매우 나쁨',
            1: '나쁨',
            2: '보통',
            3: '좋음',
            4: '매우 좋음'
        }
        return visibility_map.get(visibility_code, '보통')

    @staticmethod
    def _generate_simulated_data(lat: float, lon: float, target_date: str) -> Dict:
        """API 호출 실패 시 시뮬레이션 데이터 생성"""
        nearest_region = FishingIndexService._find_nearest_region(lat, lon)

        # 날짜 기반 의사난수 생성 (같은 날짜면 같은 데이터)
        target_hash = sum(ord(c) for c in target_date)
        overall_index = (target_hash % 7) + 4  # 4-10

        fish_species = {
            '우럭': (target_hash * 2) % 10,
            '감성돔': (target_hash * 3) % 10,
            '광어': (target_hash * 5) % 10,
            '농어': (target_hash * 7) % 10,
        }

        conditions = {
            'water_temp': 16.0 + (target_hash % 6),
            'wave_height': 0.5 + (target_hash % 10) * 0.1,
            'wind_speed': 2.0 + (target_hash % 6),
            'visibility': ['나쁨', '보통', '좋음', '매우좋음'][target_hash % 4]
        }

        hourly = FishingIndexService._generate_hourly_index(
            overall_index,
            target_date
        )

        return {
            'date': target_date,
            'location': nearest_region['name'] if nearest_region else '위치 감지 불가',
            'lat': lat,
            'lon': lon,
            'overall_index': overall_index,
            'fish_species': fish_species,
            'conditions': conditions,
            'hourly': hourly,
            'data_source': 'simulated'  # 시뮬레이션 데이터 표시
        }

    @staticmethod
    def _generate_hourly_index(overall_index: int, target_date: str) -> list:
        """시간별 낚시지수 생성 (시뮬레이션)"""
        import math
        hourly = []

        for hour in range(6, 20):  # 06:00 ~ 19:00
            # 시간에 따른 변동성 추가
            variation = 2 * math.sin((hour - 6) * math.pi / 7)
            hour_index = max(0, min(10, overall_index + variation))

            # 시간대별 최적 어종 결정
            fish_preferences = {
                (6, 9): '감성돔',  # 새벽~아침
                (10, 14): '우럭',  # 오전~정오
                (15, 19): '광어'  # 오후~저녁
            }

            best_fish = '우럭'
            for time_range, fish in fish_preferences.items():
                if time_range[0] <= hour <= time_range[1]:
                    best_fish = fish
                    break

            hourly.append({
                'hour': hour,
                'index': round(hour_index, 1),
                'best_fish': best_fish,
                'activity': '활발' if hour_index >= 6 else '보통' if hour_index >= 4 else '저조'
            })

        return hourly

    @staticmethod
    def get_fishing_forecast(lat: float, lon: float, days: int = 7) -> Optional[Dict]:
        """주간 낚시지수 예보

        Args:
            lat: 위도
            lon: 경도
            days: 조회 일수 (기본 7일)

        Returns:
            {
                'forecast': [
                    {'date': '2026-06-10', 'index': 7, 'best_condition': '맑음'},
                    ...
                ]
            }
        """
        forecast = []

        for i in range(days):
            target_date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
            fishing_data = FishingIndexService.get_fishing_index(lat, lon, target_date)

            if fishing_data:
                forecast.append({
                    'date': target_date,
                    'index': fishing_data['overall_index'],
                    'best_fish': max(
                        fishing_data['fish_species'].items(),
                        key=lambda x: x[1]
                    )[0],
                    'conditions': fishing_data['conditions']
                })

        return {'forecast': forecast} if forecast else None
