from flask import Blueprint, request, jsonify
from services.feeding_service import get_feeding_times, get_feeding_calendar

feeding_bp = Blueprint('feeding', __name__, url_prefix='/api/feeding-times')

@feeding_bp.route('', methods=['GET'])
def fetch_feeding_times():
    """
    특정 위치의 피딩타임 조회

    Query Parameters:
        - lat: 위도
        - lon: 경도
        - date: YYYY-MM-DD (선택, 기본값: 오늘)
    """
    try:
        lat = request.args.get('lat', 37.5665, type=float)
        lon = request.args.get('lon', 126.9780, type=float)
        date = request.args.get('date', None, type=str)

        feeding_times = get_feeding_times(lat, lon, date)

        return jsonify({
            'latitude': lat,
            'longitude': lon,
            'date': date,
            'feeding_times': feeding_times
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@feeding_bp.route('/calendar', methods=['GET'])
def fetch_feeding_calendar():
    """
    향후 N일간의 피딩타임 캘린더 조회

    Query Parameters:
        - lat: 위도
        - lon: 경도
        - days: 일수 (기본값: 30)
    """
    try:
        lat = request.args.get('lat', 37.5665, type=float)
        lon = request.args.get('lon', 126.9780, type=float)
        days = request.args.get('days', 30, type=int)

        if days > 365:
            days = 365

        calendar = get_feeding_calendar(lat, lon, days)

        return jsonify({
            'latitude': lat,
            'longitude': lon,
            'days': days,
            'calendar': calendar
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@feeding_bp.route('/<int:spot_id>', methods=['GET'])
def fetch_spot_feeding_times(spot_id):
    """
    특정 명소의 피딩타임 조회 (향후 명소별 좌표 DB에서 조회)
    """
    try:
        date = request.args.get('date', None, type=str)

        # 향후 DB에서 spot_id로 위치 조회
        # spot = get_spot_by_id(spot_id)
        # lat, lon = spot.latitude, spot.longitude

        # 임시: 기본값 사용
        lat = 37.5665
        lon = 126.9780

        feeding_times = get_feeding_times(lat, lon, date)

        return jsonify({
            'spot_id': spot_id,
            'date': date,
            'feeding_times': feeding_times
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
