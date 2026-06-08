from flask import Blueprint, request, jsonify
from services.weather_service import get_weather

weather_bp = Blueprint('weather', __name__)

@weather_bp.route('/api/weather', methods=['GET'])
def fetch_weather():
    latitude = request.args.get('lat', type=float, default=37.5665)
    longitude = request.args.get('lon', type=float, default=126.9780)

    weather_data = get_weather(latitude, longitude)

    return jsonify(weather_data)
