from flask import Blueprint, request, jsonify
import importlib
import sys

print("[INIT] routes/tide.py 로드됨", flush=True)

tide_bp = Blueprint('tide', __name__)

# 동적 import 함수 (캐시 문제 해결)
def get_service_function(func_name):
    """항상 최신 모듈을 로드하도록 강제"""
    # 캐시된 모듈 제거
    for module_name in list(sys.modules.keys()):
        if 'services.tide_service' in module_name:
            del sys.modules[module_name]

    from services import tide_service
    return getattr(tide_service, func_name)

@tide_bp.route('/api/tide', methods=['GET'])
def fetch_tide():
    get_tide_data = get_service_function('get_tide_data')
    latitude = request.args.get('lat', type=float, default=37.5665)
    longitude = request.args.get('lon', type=float, default=126.9780)

    tide_data = get_tide_data(latitude, longitude)

    return jsonify(tide_data)

@tide_bp.route('/api/tide/hourly', methods=['GET'])
def fetch_tide_hourly():
    print("[ROUTE] fetch_tide_hourly 호출됨", flush=True)
    get_tide_hourly = get_service_function('get_tide_hourly')

    latitude = request.args.get('lat', type=float, default=37.5665)
    longitude = request.args.get('lon', type=float, default=126.9780)
    date_str = request.args.get('date', type=str, default=None)

    print(f"[ROUTE] 파라미터: lat={latitude}, lon={longitude}, date={date_str}", flush=True)
    hourly_data = get_tide_hourly(latitude, longitude, date_str)
    print(f"[ROUTE] 결과: {len(hourly_data.get('highTides', []))}회 만조, {len(hourly_data.get('lowTides', []))}회 간조", flush=True)

    return jsonify(hourly_data)

@tide_bp.route('/api/tide/calendar', methods=['GET'])
def fetch_tide_calendar():
    latitude = request.args.get('lat', type=float, default=37.5665)
    longitude = request.args.get('lon', type=float, default=126.9780)
    days = request.args.get('days', type=int, default=7)

    calendar_data = get_tide_calendar(latitude, longitude, days)

    return jsonify({'calendar': calendar_data})
