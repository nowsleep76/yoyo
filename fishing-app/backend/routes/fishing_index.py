from flask import Blueprint, request, jsonify
from services.fishing_index_service import FishingIndexService

fishing_index_bp = Blueprint('fishing_index', __name__)

@fishing_index_bp.route('/api/fishing/index', methods=['GET'])
def get_fishing_index():
    """특정 위치와 날짜의 낚시지수 조회

    API 실패 시 자동으로 시뮬레이션 데이터 반환
    """
    latitude = request.args.get('lat', type=float, default=37.5665)
    longitude = request.args.get('lon', type=float, default=126.9780)
    date_str = request.args.get('date', type=str, default=None)

    if not date_str:
        from datetime import datetime
        date_str = datetime.now().strftime('%Y-%m-%d')

    fishing_data = FishingIndexService.get_fishing_index(latitude, longitude, date_str)

    # 항상 데이터 반환 (API 또는 시뮬레이션)
    if fishing_data:
        return jsonify(fishing_data)
    else:
        # 폴백: 시뮬레이션 데이터 생성
        fallback_data = FishingIndexService._generate_simulated_data(latitude, longitude, date_str)
        return jsonify(fallback_data)

@fishing_index_bp.route('/api/fishing/forecast', methods=['GET'])
def get_fishing_forecast():
    """주간 낚시지수 예보"""
    latitude = request.args.get('lat', type=float, default=37.5665)
    longitude = request.args.get('lon', type=float, default=126.9780)
    days = request.args.get('days', type=int, default=7)

    forecast_data = FishingIndexService.get_fishing_forecast(latitude, longitude, days)

    if forecast_data:
        return jsonify(forecast_data)
    else:
        return jsonify({
            'error': '낚시지수 예보를 조회할 수 없습니다',
            'forecast': []
        }), 404
