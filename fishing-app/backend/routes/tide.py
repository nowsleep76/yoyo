from flask import Blueprint, request, jsonify
from services.tide_service import get_tide_data, get_tide_calendar, get_tide_hourly

print("[INIT] routes/tide.py 로드됨", flush=True)

tide_bp = Blueprint('tide', __name__)
print(f"[INIT] tide_bp 생성됨, get_tide_hourly={get_tide_hourly}", flush=True)

@tide_bp.route('/api/tide', methods=['GET'])
def fetch_tide():
    latitude = request.args.get('lat', type=float, default=37.5665)
    longitude = request.args.get('lon', type=float, default=126.9780)

    tide_data = get_tide_data(latitude, longitude)

    return jsonify(tide_data)

@tide_bp.route('/api/tide/hourly', methods=['GET'])
def fetch_tide_hourly():
    import sys
    sys.stdout.write("[ROUTE] fetch_tide_hourly 호출됨\n")
    sys.stdout.flush()
    latitude = request.args.get('lat', type=float, default=37.5665)
    longitude = request.args.get('lon', type=float, default=126.9780)
    date_str = request.args.get('date', type=str, default=None)

    hourly_data = get_tide_hourly(latitude, longitude, date_str)

    return jsonify(hourly_data)

@tide_bp.route('/api/tide/calendar', methods=['GET'])
def fetch_tide_calendar():
    latitude = request.args.get('lat', type=float, default=37.5665)
    longitude = request.args.get('lon', type=float, default=126.9780)
    days = request.args.get('days', type=int, default=7)

    calendar_data = get_tide_calendar(latitude, longitude, days)

    return jsonify({'calendar': calendar_data})
