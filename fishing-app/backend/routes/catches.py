from flask import Blueprint, request, jsonify
from models.database import (
    add_catch_record, get_all_catches, get_catch_by_id, update_catch_record,
    delete_catch_record, like_catch_record
)

catches_bp = Blueprint('catches', __name__, url_prefix='/api/catches')

@catches_bp.route('', methods=['POST'])
def create_catch():
    """조과 기록 생성"""
    try:
        data = request.get_json()

        catch_id = add_catch_record(
            species=data.get('species', ''),
            size_cm=data.get('size_cm'),
            weight_g=data.get('weight_g'),
            spot_id=data.get('spot_id'),
            spot_name=data.get('spot_name', ''),
            location_lat=data.get('location_lat'),
            location_lng=data.get('location_lng'),
            gps_accuracy=data.get('gps_accuracy'),
            rod=data.get('rod', ''),
            reel=data.get('reel', ''),
            line_weight=data.get('line_weight', ''),
            leader=data.get('leader', ''),
            rig_method=data.get('rig_method', ''),
            caught_at=data.get('caught_at'),
            weather_condition=data.get('weather_condition', ''),
            tide_info=data.get('tide_info', ''),
            water_temp=data.get('water_temp'),
            description=data.get('description', ''),
            photos=data.get('photos', ''),
            is_public=data.get('is_public', False),
            user_id=data.get('user_id')
        )

        return jsonify({'id': catch_id, 'message': '조과 기록이 저장되었습니다'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@catches_bp.route('', methods=['GET'])
def fetch_catches():
    """조과 기록 조회"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        sort = request.args.get('sort', 'latest', type=str)

        catches = get_all_catches(limit=limit, offset=offset, sort_by=sort)

        return jsonify(catches), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@catches_bp.route('/<int:catch_id>', methods=['GET'])
def fetch_catch(catch_id):
    """조과 기록 상세 조회"""
    try:
        catch = get_catch_by_id(catch_id)

        if not catch:
            return jsonify({'error': '조과 기록을 찾을 수 없습니다'}), 404

        return jsonify(catch), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@catches_bp.route('/<int:catch_id>', methods=['PUT'])
def update_catch(catch_id):
    """조과 기록 수정"""
    try:
        data = request.get_json()

        success = update_catch_record(catch_id, **data)

        if not success:
            return jsonify({'error': '업데이트할 데이터가 없습니다'}), 400

        return jsonify({'message': '조과 기록이 수정되었습니다'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@catches_bp.route('/<int:catch_id>', methods=['DELETE'])
def delete_catch(catch_id):
    """조과 기록 삭제"""
    try:
        delete_catch_record(catch_id)

        return jsonify({'message': '조과 기록이 삭제되었습니다'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@catches_bp.route('/<int:catch_id>/like', methods=['POST'])
def add_like(catch_id):
    """조과 기록 좋아요"""
    try:
        like_catch_record(catch_id)

        return jsonify({'message': '좋아요를 추가했습니다'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@catches_bp.route('/feed', methods=['GET'])
def fetch_feed():
    """SNS 피드 조회"""
    try:
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        sort = request.args.get('sort', 'latest', type=str)
        species = request.args.get('species', None, type=str)

        catches = get_all_catches(limit=limit, offset=offset, sort_by=sort)

        # 어종 필터링
        if species:
            catches = [c for c in catches if c.get('species') == species]

        return jsonify(catches), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
