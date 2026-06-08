from flask import Blueprint, request, jsonify
from models.database import (
    add_fishing_session, get_fishing_history, add_favorite_spot,
    get_favorite_spots, remove_favorite_spot, get_user_stats
)

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

@user_bp.route('/stats', methods=['GET'])
def fetch_stats():
    """사용자 통계 조회"""
    try:
        stats = get_user_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@user_bp.route('/history', methods=['GET'])
def fetch_history():
    """방문 이력 조회"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        history = get_fishing_history(limit=limit, offset=offset)

        return jsonify(history), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@user_bp.route('/history', methods=['POST'])
def create_session():
    """방문 이력 추가"""
    try:
        data = request.get_json()

        session_id = add_fishing_session(
            spot_id=data.get('spot_id'),
            spot_name=data.get('spot_name', ''),
            visited_at=data.get('visited_at'),
            duration_minutes=data.get('duration_minutes'),
            catch_count=data.get('catch_count', 0),
            weather=data.get('weather', ''),
            tide_info=data.get('tide_info', ''),
            notes=data.get('notes', '')
        )

        return jsonify({'id': session_id, 'message': '방문 이력이 저장되었습니다'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@user_bp.route('/favorite-spots', methods=['GET'])
def fetch_favorites():
    """즐겨찾기 조회"""
    try:
        favorites = get_favorite_spots()

        return jsonify(favorites), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@user_bp.route('/favorite-spots/<int:spot_id>', methods=['POST'])
def add_favorite(spot_id):
    """즐겨찾기 추가"""
    try:
        data = request.get_json() or {}

        fav_id = add_favorite_spot(
            spot_id=spot_id,
            spot_name=data.get('spot_name', ''),
            spot_type=data.get('spot_type', 'known')
        )

        return jsonify({'id': fav_id, 'message': '즐겨찾기에 추가되었습니다'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@user_bp.route('/favorite-spots/<int:favorite_id>', methods=['DELETE'])
def remove_favorite(favorite_id):
    """즐겨찾기 제거"""
    try:
        remove_favorite_spot(favorite_id)

        return jsonify({'message': '즐겨찾기에서 제거되었습니다'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
