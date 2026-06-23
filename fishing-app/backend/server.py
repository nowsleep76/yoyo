#!/usr/bin/env python
"""
프로덕션 서버 - 항상 최신 코드를 사용합니다.
각 요청마다 Flask 앱을 새로 인스턴스화합니다.
"""
import sys
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
import json

class WSGIHandler(BaseHTTPRequestHandler):
    def run_wsgi(self, method):
        """매번 새로운 app을 로드하고 요청을 처리합니다."""
        # 모듈 캐시 완전 제거
        for mod in list(sys.modules.keys()):
            if 'fishing' in mod or 'app' in mod or 'routes' in mod or 'services' in mod or 'models' in mod:
                try:
                    del sys.modules[mod]
                except:
                    pass

        # 새로운 app을 로드합니다
        import importlib.util
        spec = importlib.util.spec_from_file_location("app", "/d/DEV/fishing-app/backend/app.py")
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        app = app_module.app

        # test_client를 사용해 요청을 처리합니다
        environ = {
            'REQUEST_METHOD': method,
            'PATH_INFO': self.path.split('?')[0],
            'QUERY_STRING': self.path.split('?')[1] if '?' in self.path else '',
            'SERVER_NAME': self.server.server_name,
            'SERVER_PORT': str(self.server.server_port),
            'wsgi.url_scheme': 'http',
            'wsgi.input': BytesIO(self.rfile.read(int(self.headers.get('Content-Length', 0)))),
        }

        with app.test_client() as client:
            if method == 'GET':
                response = client.get(self.path)
            elif method == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                response = client.post(self.path, data=body, content_type=self.headers.get('Content-Type'))
            else:
                response = client.options(self.path)

            # 응답 전송
            self.send_response(response.status_code)
            for key, value in response.headers:
                self.send_header(key, value)
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response.get_data())

    def do_GET(self):
        self.run_wsgi('GET')

    def do_POST(self):
        self.run_wsgi('POST')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        pass  # 요청 로그 생략

if __name__ == '__main__':
    os.chdir('/d/DEV/fishing-app/backend')
    sys.path.insert(0, '/d/DEV/fishing-app/backend')

    print("[SERVER] 프로덕션 서버 시작 (포트 8000, 항상 최신 코드 사용)", flush=True)
    server = HTTPServer(('0.0.0.0', 8000), WSGIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[SERVER] 종료", flush=True)
