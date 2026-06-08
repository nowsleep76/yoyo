# 낚시 정보 앱

한국 낚시 애호가들을 위한 종합 정보 플랫폼입니다. 날씨, 물때, 바람, 낚시 포인트 지도 등의 정보를 제공합니다.

## 주요 기능

### Phase 1: MVP
- ✅ 날씨 정보 (기온, 풍속, 풍향, 습도)
- ✅ 물때 정보 (24시간 조석 곡선, 오늘의 물때 번호)
- ✅ 포인트 지도 (낚시 포인트 추가/조회, Leaflet 지도)
- ✅ 사용자 위치 자동 감지 (GPS)

### Phase 2: 추가 예정
- 사진 업로드 (SNS)
- 커뮤니티 피드 (인스타그램 스타일)
- 수온 정보
- 피딩타임 분석
- 채비법 정보

## 기술 스택

### Backend
- Python Flask
- SQLite
- CORS (Cross-Origin Resource Sharing)

### Frontend
- React 18
- Vite (빌드 도구)
- Leaflet (지도)
- Recharts (차트)

## 설치 및 실행

### Backend 실행

1. 의존성 설치
```bash
cd backend
pip install -r requirements.txt
```

2. Flask 앱 실행
```bash
python app.py
```

백엔드는 `http://localhost:5000`에서 실행됩니다.

### Frontend 실행

1. 의존성 설치
```bash
cd frontend
npm install
```

2. 개발 서버 실행
```bash
npm run dev
```

프론트엔드는 `http://localhost:5173`에서 실행됩니다.

## API 엔드포인트

### 날씨
```
GET /api/weather?lat={위도}&lon={경도}
```

### 물때
```
GET /api/tide?lat={위도}&lon={경도}
```

### 낚시 포인트
```
GET /api/points                 # 전체 포인트 조회
POST /api/points                # 포인트 추가
GET /api/points/{id}            # 특정 포인트 조회
DELETE /api/points/{id}         # 포인트 삭제
```

## 특징

- 🎯 **Mock 데이터**: 실제 API 키 없이도 정상 작동 (이후 실제 기상청, 해양조사원 API 연결 가능)
- 📍 **GPS 위치 감지**: 브라우저 Geolocation으로 자동 위치 감지
- 🗺️ **무료 지도**: OpenStreetMap 활용 (라이선스 자유)
- 🎨 **반응형 디자인**: 모바일/태블릿/데스크톱 모두 지원
- 🇰🇷 **한국어 UI**: 모든 텍스트가 한국어로 표시

## 프로젝트 구조

```
fishing-app/
├── backend/                 # Python Flask REST API
│   ├── app.py              # 메인 앱
│   ├── routes/             # API 라우트
│   ├── models/             # 데이터베이스
│   ├── services/           # 비즈니스 로직
│   └── requirements.txt
│
└── frontend/               # React + Vite
    ├── src/
    │   ├── components/     # 재사용 컴포넌트
    │   ├── pages/         # 페이지
    │   └── App.jsx
    ├── package.json
    └── vite.config.js
```

## 라이선스

MIT
