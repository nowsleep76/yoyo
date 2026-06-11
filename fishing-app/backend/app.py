from flask import Flask
from flask_cors import CORS
from models.database import init_db
from dotenv import load_dotenv
from config import config
from routes.weather import weather_bp
from routes.tide import tide_bp
from routes.points import points_bp
from routes.spots import spots_bp
from routes.feeding import feeding_bp
from routes.catches import catches_bp
from routes.user import user_bp
from routes.fishing_index import fishing_index_bp
import os

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

@app.route('/api/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    init_db()
    app.run(debug=False, port=8000, host='0.0.0.0', threaded=True)
