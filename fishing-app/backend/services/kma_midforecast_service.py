import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from config import config

# 기상청 중기예보 API
# 3~10일 후의 날씨 예보 제공

class KmaMidForecastService:
    BASE_URL = "https://apis.data.go.kr/1360000/MidFcstInfoService"
    CACHE = {}  # {key: (data, timestamp)}
    CACHE_TTL = 3600  # 1시간 캐시

    # 지역코드 매핑: (위도, 경도) → 지역코드
    REGION_CODES = {
        # 서울/경기/강원
        (37.5665, 126.9780): '11A00000',  # 서울
        (37.28, 126.38): '11B00000',      # 인천 (을왕리 근처)
        (37.2755, 127.0086): '11C10600', # 수원
        (37.8722, 127.1098): '11D10600', # 춘천

        # 부산/울산/경남
        (35.1795, 129.0756): '21A00000',  # 부산
        (35.4897, 129.3895): '23A00000',  # 울산
        (35.2271, 128.5494): '24A00000',  # 대구

        # 목포/여수/제주
        (34.7738, 126.6202): '25A00000',  # 목포
        (34.7604, 127.7622): '26A00000',  # 여수
        (33.5063, 126.5312): '39A00000',  # 제주
    }

    @staticmethod
    def _get_from_cache(key: str) -> Optional[tuple]:
        """캐시에서 데이터 조회"""
        if key in KmaMidForecastService.CACHE:
            data, timestamp = KmaMidForecastService.CACHE[key]
            if datetime.now() - timestamp < timedelta(seconds=KmaMidForecastService.CACHE_TTL):
                return data
            del KmaMidForecastService.CACHE[key]
        return None

    @staticmethod
    def _find_nearest_region(latitude: float, longitude: float) -> str:
        """위도/경도에서 가장 가까운 지역코드 찾기"""
        nearest_code = '11B00000'  # 기본값: 인천
        min_distance = float('inf')

        for (lat, lon), code in KmaMidForecastService.REGION_CODES.items():
            distance = ((latitude - lat) ** 2 + (longitude - lon) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest_code = code

        return nearest_code

    @staticmethod
    def _get_forecast_time() -> str:
        """예보 발표 시간 결정 (0200, 0500, 0800, 1100, 1400, 1700, 2000, 2300)"""
        now = datetime.now()
        hour = now.hour

        # 가장 최근의 발표 시간 선택
        if hour < 2:
            return (datetime.now() - timedelta(days=1)).strftime('%Y%m%d') + '2300'
        elif hour < 5:
            return now.strftime('%Y%m%d') + '0200'
        elif hour < 8:
            return now.strftime('%Y%m%d') + '0500'
        elif hour < 11:
            return now.strftime('%Y%m%d') + '0800'
        elif hour < 14:
            return now.strftime('%Y%m%d') + '1100'
        elif hour < 17:
            return now.strftime('%Y%m%d') + '1400'
        elif hour < 20:
            return now.strftime('%Y%m%d') + '1700'
        elif hour < 23:
            return now.strftime('%Y%m%d') + '2000'
        else:
            return now.strftime('%Y%m%d') + '2300'

    @staticmethod
    def get_midforecast(latitude: float, longitude: float, target_date: str = None) -> Optional[Dict]:
        """기상청 중기예보 조회

        Args:
            latitude: 위도
            longitude: 경도
            target_date: 목표 날짜 (YYYY-MM-DD, 기본값: 오늘)

        Returns:
            {
                'daily': [
                    {
                        'date': 'YYYY-MM-DD',
                        'minTemp': float,
                        'maxTemp': float,
                        'minTempNight': float,
                        'maxTempDay': float,
                        'description': str,  # 날씨 설명
                        'precipitation': float,  # mm
                        'wind': str,  # 풍향
                        'windSpeed': float,  # m/s
                    },
                    ...
                ],
                'source': 'api'
            }
        """
        api_key = config.get_api_key('kma_midforecast_key')
        if not api_key:
            print(f"[KMA_MID] API 키 없음")
            return None

        try:
            # 지역코드 결정
            reg_id = KmaMidForecastService._find_nearest_region(latitude, longitude)

            # 예보 발표 시간
            tm_ef = KmaMidForecastService._get_forecast_time()

            # 캐시 확인
            cache_key = f"mid_{reg_id}_{tm_ef}"
            cached = KmaMidForecastService._get_from_cache(cache_key)
            if cached:
                print(f"[KMA_MID] 캐시에서 조회: {reg_id}")
                return cached

            # API 호출 - 육상 예보
            print(f"[KMA_MID] 중기예보 API 호출: regId={reg_id}, tmEf={tm_ef}", flush=True)

            params = {
                'serviceKey': api_key,
                'pageNo': 1,
                'numOfRows': 10,
                'dataType': 'JSON',
                'regId': reg_id,
                'tmEf': tm_ef
            }

            response = requests.get(
                f"{KmaMidForecastService.BASE_URL}/getMidLandFcst",
                params=params,
                timeout=5,
                verify=False
            )
            response.raise_for_status()
            data = response.json()

            # 응답 파싱
            result = data.get('response', {})
            body = result.get('body', {})

            if body.get('totalCount', 0) == 0:
                print(f"[KMA_MID] 응답 데이터 없음")
                return None

            items = body.get('items', {})
            if isinstance(items, dict):
                items = items.get('item', [])
            if not items:
                print(f"[KMA_MID] 항목 없음")
                return None

            # 일별 예보 파싱
            daily_forecast = []

            for item in items if isinstance(items, list) else [items]:
                try:
                    # 날짜 파싱
                    fcst_date = str(item.get('fcstDate', ''))
                    if len(fcst_date) != 8:
                        continue

                    date_str = f"{fcst_date[:4]}-{fcst_date[4:6]}-{fcst_date[6:8]}"

                    # 온도 정보
                    min_temp = float(item.get('minTa', 0))
                    max_temp = float(item.get('maxTa', 0))

                    # 강수량
                    rnSt = str(item.get('rnSt', '0')).strip()
                    precipitation = 0.0
                    try:
                        if rnSt and rnSt not in ('-', ''):
                            precipitation = float(rnSt)
                    except:
                        pass

                    # 날씨 설명
                    wf = str(item.get('wf', '맑음')).strip()
                    description = wf if wf else '맑음'

                    # 풍향/풍속
                    wd = str(item.get('wd', '남')).strip()
                    ws = float(item.get('ws', 0))

                    daily_forecast.append({
                        'date': date_str,
                        'minTemp': min_temp,
                        'maxTemp': max_temp,
                        'minTempNight': min_temp,
                        'maxTempDay': max_temp,
                        'description': description,
                        'precipitation': precipitation,
                        'wind': wd,
                        'windSpeed': ws
                    })

                except Exception as e:
                    print(f"[KMA_MID] 항목 파싱 오류: {e}")
                    continue

            if not daily_forecast:
                print(f"[KMA_MID] 파싱된 예보 없음")
                return None

            result_data = {
                'daily': daily_forecast,
                'source': 'api'
            }

            # 캐시 저장
            KmaMidForecastService.CACHE[cache_key] = (result_data, datetime.now())

            print(f"[KMA_MID] 중기예보 조회 성공: {len(daily_forecast)}일", flush=True)
            return result_data

        except requests.exceptions.RequestException as e:
            print(f"[KMA_MID] API 호출 오류: {e}")
            return None
        except Exception as e:
            print(f"[KMA_MID] 처리 오류: {e}")
            return None

    @staticmethod
    def get_daily_weather(latitude: float, longitude: float, target_date: str) -> Optional[Dict]:
        """특정 날짜의 날씨 예보 조회"""
        forecast = KmaMidForecastService.get_midforecast(latitude, longitude)

        if not forecast:
            return None

        # 목표 날짜와 일치하는 데이터 찾기
        for day_forecast in forecast.get('daily', []):
            if day_forecast['date'] == target_date:
                return day_forecast

        return None
