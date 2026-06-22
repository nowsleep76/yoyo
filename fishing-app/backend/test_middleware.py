import sys
sys.path.insert(0, '.')

from app import app

# 요청 전후로 로깅하는 미들웨어 추가
@app.before_request
def log_request():
    import flask
    print(f"[BEFORE] {flask.request.method} {flask.request.path}", flush=True)

@app.after_request
def log_response(response):
    import flask
    print(f"[AFTER] {flask.request.method} {flask.request.path} -> {response.status_code}", flush=True)
    return response

if __name__ == '__main__':
    app.run(debug=False, port=8000, host='0.0.0.0', use_reloader=False)
