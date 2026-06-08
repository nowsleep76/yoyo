from datetime import datetime
import math

LOCATION_MAP = {
    (37.5665, 126.9780): '서울',
    (35.1796, 129.0756): '부산',
    (35.8714, 128.6014): '대구',
    (36.8015, 127.1089): '대전',
    (35.1595, 126.8526): '광주',
    (37.2636, 127.0086): '수원',
    (37.4419, 127.1430): '성남',
    (37.3382, 127.1137): '인천',
    (37.0642, 127.1050): '용인',
    (33.5563, 126.5050): '제주'
}

WEATHER_CONDITIONS = ['맑음', '구름', '흐림', '약한 비', '중간 비', '소나기']

def find_nearest_location(lat, lon):
    min_distance = float('inf')
    nearest_location = '서울'

    for (loc_lat, loc_lon), loc_name in LOCATION_MAP.items():
        distance = math.sqrt((lat - loc_lat) ** 2 + (lon - loc_lon) ** 2)
        if distance < min_distance:
            min_distance = distance
            nearest_location = loc_name

    return nearest_location

def get_weather(latitude, longitude):
    location = find_nearest_location(latitude, longitude)

    hour = datetime.now().hour
    weather_idx = (hour // 3) % len(WEATHER_CONDITIONS)
    temperature = 15 + (hour % 12) - 5

    return {
        'location': location,
        'latitude': latitude,
        'longitude': longitude,
        'temperature': temperature,
        'weather': WEATHER_CONDITIONS[weather_idx],
        'wind_speed': 5 + (hour % 8),
        'wind_direction': ['북', '북동', '동', '남동', '남', '남서', '서', '북서'][hour % 8],
        'humidity': 60 + (hour % 30),
        'timestamp': datetime.now().isoformat()
    }
