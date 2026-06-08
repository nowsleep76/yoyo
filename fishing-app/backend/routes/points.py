from flask import Blueprint, request, jsonify, current_app
from models.database import (
    add_fishing_point,
    get_all_points,
    get_point_by_id,
    delete_point,
    update_point
)
from werkzeug.utils import secure_filename
import os
from datetime import datetime

points_bp = Blueprint('points', __name__)

@points_bp.route('/api/points', methods=['GET'])
def list_points():
    points = get_all_points()
    return jsonify(points)

@points_bp.route('/api/points', methods=['POST'])
def create_point():
    data = request.get_json()

    if not data or 'name' not in data or 'latitude' not in data or 'longitude' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    point_id = add_fishing_point(
        name=data['name'],
        latitude=data['latitude'],
        longitude=data['longitude'],
        description=data.get('description', ''),
        fish_types=data.get('fish_types', ''),
        photo_url=data.get('photo_url', ''),
        reel=data.get('reel', ''),
        rod=data.get('rod', ''),
        tackle=data.get('tackle', ''),
        rig_memo=data.get('rig_memo', '')
    )

    return jsonify({
        'id': point_id,
        'name': data['name'],
        'latitude': data['latitude'],
        'longitude': data['longitude'],
        'description': data.get('description', ''),
        'fish_types': data.get('fish_types', ''),
        'photo_url': data.get('photo_url', ''),
        'reel': data.get('reel', ''),
        'rod': data.get('rod', ''),
        'tackle': data.get('tackle', ''),
        'rig_memo': data.get('rig_memo', '')
    }), 201

@points_bp.route('/api/points/<int:point_id>', methods=['GET'])
def get_point(point_id):
    point = get_point_by_id(point_id)

    if not point:
        return jsonify({'error': 'Point not found'}), 404

    return jsonify(point)

@points_bp.route('/api/points/<int:point_id>', methods=['DELETE'])
def remove_point(point_id):
    point = get_point_by_id(point_id)

    if not point:
        return jsonify({'error': 'Point not found'}), 404

    delete_point(point_id)

    return jsonify({'message': 'Point deleted'}), 200

@points_bp.route('/api/points/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        filename = secure_filename(f'{datetime.now().timestamp()}_{file.filename}')
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        return jsonify({'url': f'/uploads/{filename}'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
