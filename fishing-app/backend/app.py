from flask import Flask, request
from flask_cors import CORS
from models.database import init_db
from dotenv import load_dotenv
from config import config
import os
import sys
import importlib
import importlib.util

# 기존 bytecode 캐시 제거
sys.dont_write_bytecode = True

# 매번 routes와 services 모듈을 강제로 다시 로드합니다
def reload_route_modules():
    """routes와 services 모듈을 강제로 다시 로드합니다."""
    # sys.modules에서 제거
    for module_name in list(sys.modules.keys()):
        if 'services' in module_name or 'routes' in module_name or 'models' in module_name:
            try:
                del sys.modules[module_name]
            except:
                pass

reload_route_modules()
print("[INIT APP] 모듈 캐시 삭제 완료", flush=True)

# importlib를 사용하여 강제로 새로 로드합니다
from routes.weather import weather_bp
from routes.tide import tide_bp
from routes.points import points_bp
from routes.spots import spots_bp
from routes.feeding import feeding_bp
from routes.catches import catches_bp
from routes.user import user_bp
from routes.fishing_index import fishing_index_bp

load_dotenv()

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

app.register_blueprint(weather_bp)
app.register_blueprint(tide_bp)
app.register_blueprint(points_bp)
app.register_blueprint(spots_bp)
app.register_blueprint(feeding_bp)
app.register_blueprint(catches_bp)
app.register_blueprint(user_bp)
app.register_blueprint(fishing_index_bp)

# 캐싱 무효화: 모든 API 응답에 no-cache 헤더 추가
@app.after_request
def add_no_cache_headers(response):
    """모든 API 응답에 캐시 무효화 헤더 추가"""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200

@app.route('/api/debug/routes', methods=['GET'])
def debug_routes():
    try:
        import sys
        import importlib
        routes = [{'rule': str(rule), 'endpoint': rule.endpoint} for rule in app.url_map.iter_rules() if 'tide' in rule.rule]
        modules = [m for m in sys.modules.keys() if 'routes' in m]
        tide_module = importlib.import_module('routes.tide')
        return {
            'routes': routes,
            'modules_loaded': modules,
            'routes_tide_location': str(tide_module.__file__)
        }
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    init_db()
    # Flask 개발 서버 사용 (모듈 캐싱 이슈 해결)
    print("[START] Flask 개발 서버 시작...", flush=True)
    app.run(debug=False, port=8000, host='0.0.0.0', threaded=True, use_reloader=False)
