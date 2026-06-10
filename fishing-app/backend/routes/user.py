from flask import Blueprint, request, jsonify
from models.database import (
    add_fishing_session, get_fishing_history, add_favorite_spot,
    get_favorite_spots, remove_favorite_spot, get_user_stats,
    add_user, get_user, update_user, get_user_stats_filtered
)

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

@user_bp.route('/stats', methods=['GET'])
def fetch_stats():
    """사용자 통계 조회 (user_id가 있으면 개인, 없으면 전체)"""
    try:
        user_id = request.args.get('user_id')
        stats = get_user_stats_filtered(user_id=user_id)
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

@user_bp.route('/favorite-catches', methods=['GET'])
def fetch_favorite_catches():
    """즐겨찾기한 조과 조회"""
    try:
        from models.database import get_favorite_catches
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        favorites = get_favorite_catches(limit=limit, offset=offset)

        return jsonify(favorites), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ===== 사용자 프로필 API =====

@user_bp.route('/profile', methods=['GET'])
def get_profile():
    """사용자 프로필 조회"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400

        user = get_user(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify(user), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@user_bp.route('/profile', methods=['POST'])
def create_profile():
    """새 사용자 프로필 생성"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        nickname = data.get('nickname')

        if not user_id or not nickname:
            return jsonify({'error': 'user_id and nickname are required'}), 400

        result = add_user(
            user_id=user_id,
            nickname=nickname,
            preferred_rod=data.get('preferred_rod', ''),
            preferred_reel=data.get('preferred_reel', ''),
            preferred_line_weight=data.get('preferred_line_weight', ''),
            preferred_leader=data.get('preferred_leader', ''),
            preferred_species=data.get('preferred_species', '')
        )

        if result is None:
            return jsonify({'error': 'User already exists'}), 409

        return jsonify({'id': result, 'message': '프로필이 생성되었습니다'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@user_bp.route('/profile', methods=['PUT'])
def update_profile():
    """사용자 프로필 수정"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400

        data = request.get_json()
        success = update_user(user_id, **data)

        if not success:
            return jsonify({'error': 'Failed to update profile'}), 400

        updated_user = get_user(user_id)
        return jsonify(updated_user), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
