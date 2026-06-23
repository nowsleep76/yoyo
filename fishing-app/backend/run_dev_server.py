#!/usr/bin/env python
"""
개발용 HTTP 서버 - 항상 최신 코드를 사용합니다.
각 요청마다 Flask 앱을 새로 로드합니다.
"""
import sys
import importlib
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Flask 앱을 매번 새로 로드합니다
        if 'app' in sys.modules:
            del sys.modules['app']

        # routes 모듈들도 삭제합니다
        for mod_name in list(sys.modules.keys()):
            if 'routes' in mod_name or 'services' in mod_name:
                del sys.modules[mod_name]

        # 새로운 앱을 로드합니다
        from app import app

        # test_client를 사용해서 요청을 처리합니다
        with app.test_client() as client:
            response = client.get(self.path)

            # 응답을 HTTP로 반환합니다
            self.send_response(response.status_code)
            for header, value in response.headers:
                self.send_header(header, value)
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()

            self.wfile.write(response.get_data())

    def do_POST(self):
        # POST도 처리합니다 (같은 방식)
        if 'app' in sys.modules:
            del sys.modules['app']

        for mod_name in list(sys.modules.keys()):
            if 'routes' in mod_name or 'services' in mod_name:
                del sys.modules[mod_name]

        from app import app

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        with app.test_client() as client:
            response = client.post(
                self.path,
                data=body,
                content_type=self.headers.get('Content-Type', 'application/json')
            )

            self.send_response(response.status_code)
            for header, value in response.headers:
                self.send_header(header, value)
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            self.wfile.write(response.get_data())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[HTTP] {format % args}", flush=True)

if __name__ == '__main__':
    sys.path.insert(0, '/d/DEV/fishing-app/backend')

    print("[DEV SERVER] 개발 HTTP 서버 시작...", flush=True)
    print("[DEV SERVER] 포트 8000에서 수신 대기중... (항상 최신 코드 사용)", flush=True)

    server = HTTPServer(('0.0.0.0', 8000), RequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[DEV SERVER] 서버 종료", flush=True)
