from flask import Blueprint, request, jsonify
from services.tide_service import get_tide_data, get_tide_calendar, get_tide_hourly
from datetime import datetime
from services.tides_korea import get_tide_for_date, LUNAR_CONVERSION_2026

tide_bp = Blueprint('tide', __name__)

@tide_bp.route('/api/tide', methods=['GET'])
def fetch_tide():
    latitude = request.args.get('lat', type=float, default=37.5665)
    longitude = request.args.get('lon', type=float, default=126.9780)

    tide_data = get_tide_data(latitude, longitude)

    return jsonify(tide_data)

@tide_bp.route('/api/tide/hourly', methods=['GET'])
def fetch_tide_hourly():
    latitude = request.args.get('lat', type=float, default=37.5665)
    longitude = request.args.get('lon', type=float, default=126.9780)
    date_str = request.args.get('date', type=str, default=None)

    # 일반 계산 방식으로 hourly_data 항상 먼저 조회
    hourly_data = get_tide_hourly(latitude, longitude, date_str)

    # 정확한 데이터를 먼저 시도
    if date_str:
        target = datetime.strptime(date_str, '%Y-%m-%d')
        tide_info = get_tide_for_date(target.day)
        lunar_info = LUNAR_CONVERSION_2026.get((target.month, target.day))

        if tide_info and lunar_info:
            # get_tide_hourly()에서 이미 highTides/lowTides를 height와 함께 반환하므로
            # lunar 필드 키를 정규화하여 업데이트
            hourly_data.update({
                'lunar': {
                    'month': lunar_info.get('lunar_month'),
                    'day': lunar_info.get('lunar_day'),
                    'age': lunar_info.get('lunar_age')
                },
                'tideStrength': tide_info.get('strength', '중')
            })

    return jsonify(hourly_data)

@tide_bp.route('/api/tide/calendar', methods=['GET'])
def fetch_tide_calendar():
    latitude = request.args.get('lat', type=float, default=37.5665)
    longitude = request.args.get('lon', type=float, default=126.9780)
    days = request.args.get('days', type=int, default=7)

    calendar_data = get_tide_calendar(latitude, longitude, days)

    return jsonify({'calendar': calendar_data})
