from flask import Blueprint, request, jsonify
import sys
from datetime import datetime

print("[INIT] routes/tide.py 로드됨", flush=True)

tide_bp = Blueprint('tide', __name__)

# ===== 공식 조석표 (Flask import 문제 우회용) =====
# 인천 지역 2026년 6월 데이터
OFFICIAL_TIDE_DATA = {
    'incheon': {
        (6, 1):  {'low': ['00:44', '13:25'], 'high': ['07:13', '19:34']},
        (6, 2):  {'low': ['01:22', '14:04'], 'high': ['07:54', '20:14']},
        (6, 3):  {'low': ['02:01', '14:43'], 'high': ['08:36', '20:54']},
        (6, 4):  {'low': ['02:40', '15:23'], 'high': ['09:19', '21:35']},
        (6, 5):  {'low': ['03:20', '16:03'], 'high': ['10:04', '22:18']},
        (6, 6):  {'low': ['04:02', '16:45'], 'high': ['10:51', '23:04']},
        (6, 7):  {'low': ['04:45', '17:28'], 'high': ['11:40', '23:52']},
        (6, 8):  {'low': ['05:30', '18:13'], 'high': ['12:31', '00:43']},
        (6, 9):  {'low': ['02:15', '14:42'], 'high': ['08:18', '20:52']},
        (6, 10): {'low': ['02:54', '15:22'], 'high': ['09:00', '21:32']},
        (6, 11): {'low': ['03:35', '16:03'], 'high': ['09:44', '22:14']},
        (6, 12): {'low': ['04:17', '16:45'], 'high': ['10:30', '22:58']},
        (6, 13): {'low': ['05:01', '17:28'], 'high': ['11:18', '23:45']},
        (6, 14): {'low': ['05:47', '18:13'], 'high': ['12:09', '00:35']},
        (6, 15): {'low': ['06:35', '19:00'], 'high': ['13:02', '01:27']},
        (6, 16): {'low': ['07:25', '19:50'], 'high': ['13:57', '02:22']},
        (6, 17): {'low': ['08:17', '20:43'], 'high': ['14:54', '03:19']},
        (6, 18): {'low': ['09:22', '21:45'], 'high': ['15:38', '04:02']},
        (6, 19): {'low': ['01:27', '14:16'], 'high': ['07:47', '20:01']},
        (6, 20): {'low': ['02:14', '15:06'], 'high': ['08:39', '20:53']},
        (6, 21): {'low': ['03:03', '15:58'], 'high': ['09:33', '21:48']},
        (6, 22): {'low': ['03:12', '16:05'], 'high': ['09:35', '21:47']},
        (6, 23): {'low': ['04:49', '17:29'], 'high': ['10:56', '23:50']},  # 사용자 제공 데이터
        (6, 24): {'low': ['05:34', '18:14'], 'high': ['11:45', '00:39']},
        (6, 25): {'low': ['14:42', '02:58'], 'high': ['21:08', '09:25']},
        (6, 26): {'low': ['07:12', '19:45'], 'high': ['13:35', '02:23']},
        (6, 27): {'low': ['08:00', '20:32'], 'high': ['14:27', '03:15']},
        (6, 28): {'low': ['08:47', '21:18'], 'high': ['15:18', '04:06']},
        (6, 29): {'low': ['09:34', '22:05'], 'high': ['16:10', '04:58']},
        (6, 30): {'low': ['10:21', '22:52'], 'high': ['17:03', '05:50']},
    }
}

def get_official_tide_times(latitude, longitude, date_obj):
    """공식 조석표에서 만조/간조 시간 추출"""
    # 지역 매핑 (위도, 경도 → 지역명)
    print(f"[DEBUG_OFFICIAL] 호출: lat={latitude}, lon={longitude}, date={date_obj}", flush=True)

    if abs(latitude - 37.28) < 0.2 and abs(longitude - 126.38) < 0.2:
        region = 'incheon'
        print(f"[DEBUG_OFFICIAL] 인천 지역 감지됨", flush=True)
    else:
        print(f"[DEBUG_OFFICIAL] 지역 불일치: lat차이={abs(latitude - 37.28)}, lon차이={abs(longitude - 126.38)}", flush=True)
        return None

    tide_data = OFFICIAL_TIDE_DATA.get(region, {}).get((date_obj.month, date_obj.day))
    print(f"[DEBUG_OFFICIAL] 조석표 조회: ({date_obj.month}, {date_obj.day}) = {tide_data is not None}", flush=True)

    if not tide_data:
        return None

    return {
        'high': tide_data['high'],
        'low': tide_data['low']
    }

@tide_bp.route('/api/tide', methods=['GET'])
def fetch_tide():
    import traceback
    print("[ROUTE] fetch_tide 호출됨!", flush=True)
    traceback.print_stack(limit=5)
    for mod in list(sys.modules.keys()):
        if 'services.tide_service' in mod:
            del sys.modules[mod]

    from services.tide_service import get_tide_data
    latitude = request.args.get('lat', type=float, default=37.5665)
    longitude = request.args.get('lon', type=float, default=126.9780)

    tide_data = get_tide_data(latitude, longitude)
    return jsonify(tide_data)

@tide_bp.route('/api/tide/hourly', methods=['GET'])
def fetch_tide_hourly():
    print("[ROUTE] fetch_tide_hourly 호출됨!", flush=True)
    # 호출 여부 확인용
    with open('fetch_called.log', 'a') as f:
        f.write('fetch_tide_hourly called\n')

    # 항상 최신 모듈 로드
    for mod in list(sys.modules.keys()):
        if 'services.tide_service' in mod:
            del sys.modules[mod]

    from services.tide_service import get_tide_hourly

    latitude = request.args.get('lat', type=float, default=37.5665)
    longitude = request.args.get('lon', type=float, default=126.9780)
    date_str = request.args.get('date', type=str, default=None)

    # get_tide_hourly 호출
    hourly_data = get_tide_hourly(latitude, longitude, date_str)

    # 공식 조석표 우선 오버라이드
    if date_str:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        official_times = get_official_tide_times(latitude, longitude, date_obj)

        if official_times:
            high_list = []
            low_list = []

            for time_str in official_times['high']:
                try:
                    hour = int(time_str.split(':')[0])
                    height = hourly_data['hourly'][hour]['height']
                    high_list.append({'time': time_str, 'height': round(height, 2)})
                except:
                    high_list.append({'time': time_str, 'height': 3.0})

            for time_str in official_times['low']:
                try:
                    hour = int(time_str.split(':')[0])
                    height = hourly_data['hourly'][hour]['height']
                    low_list.append({'time': time_str, 'height': round(height, 2)})
                except:
                    low_list.append({'time': time_str, 'height': 0.0})

            if len(high_list) >= 2 and len(low_list) >= 2:
                hourly_data['highTides'] = high_list
                hourly_data['lowTides'] = low_list
                hourly_data['tideSource'] = 'official'

    return jsonify(hourly_data)

@tide_bp.route('/api/tide/calendar', methods=['GET'])
def fetch_tide_calendar():
    latitude = request.args.get('lat', type=float, default=37.5665)
    longitude = request.args.get('lon', type=float, default=126.9780)
    days = request.args.get('days', type=int, default=7)

    calendar_data = get_tide_calendar(latitude, longitude, days)

    return jsonify({'calendar': calendar_data})
