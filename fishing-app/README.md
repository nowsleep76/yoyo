# 🎣 낚시 정보 앱 (Fishing Information App)

한국 어부와 낚시 애호가를 위한 종합 낚시 정보 애플리케이션입니다.

---

## 📋 주요 기능

### 1. 물때 탭 (Tide Tab)
- **실시간 조석 정보** - 시간별 수위, 만조/간조 시각
- **24시간 데이터** - 1시간 또는 3시간 단위 선택 가능
- **해양 조건** - 수온, 조류 강도, 파고, 풍속, 풍향
- **기상 정보** - 날씨, 기온, 강수확률
- **천문 정보** - 일출/일몰 시각, 음력 날짜

**API 통합:**
- ✅ 기상청 단기예보 API (KMA) - 시간별 기온, 날씨, 강수확률, 풍속
- ⏳ 국립해양조사원 해양관측 API (KHOA) - 파고, 수온 (준비 중)

### 2. 탐색 탭 (Explore Tab)
- **공개 기록 조회** - 커뮤니티 낚시 기록 지도 표시
- **출조 계획** - 날짜/어종별 과거 조과 검색
- **어종별 필터링** - 어종 선택 후 상세 정보 조회
- **🆕 낚시지수** - 위치/날짜별 종합 낚시지수 및 어종별 추천도

**낚시지수 상세:**
- 종합 지수 (0-10 게이지)
- 해양 조건 (수온, 파고, 풍속, 가시거리)
- 어종별 지수 (우럭, 감성돔, 광어, 농어)
- 시간별 최적 어종 (6시~19시)

### 3. 기록 탭 (Records Tab)
- **조과 기록 등록** - 사진, 어종, 크기, 무게, 위치 등 저장
- **개인 기록 관리** - 등록한 조과 목록 조회/수정/삭제
- **공개/비공개 설정** - 커뮤니티 공유 여부 선택

### 4. 프로필 탭 (Profile Tab)
- **낚시 통계** - 총 조과수, 평균 크기, 선호 어종
- **프로필 설정** - 사용자 정보 관리

---

## 🛠️ 기술 스택

### Frontend
- React 18, Vite, Leaflet (지도), CSS3

### Backend
- Flask 3.0, Python 3.14, SQLite, Requests

### External APIs
- **기상청 (KMA)** - 단기예보 조회
- **국립해양조사원 (KHOA)** - 해양관측 정보 (준비 중)
- **바다낚시지수** - 낚시지수 조회

---

## 🚀 시작하기

### 설치

**백엔드**
```bash
cd fishing-app/backend
pip install -r requirements.txt
```

**프론트엔드**
```bash
cd fishing-app/frontend
npm install
```

### 환경 설정

`.env` 파일 생성 (백엔드 루트):
```
KMA_SERVICE_KEY=your_kma_key_here
KHOA_SERVICE_KEY=your_khoa_key_here
FISHING_INDEX_API_KEY=your_fishing_index_key_here
```

### 실행

**백엔드** (터미널 1)
```bash
cd fishing-app/backend
python app.py
# localhost:8000
```

**프론트엔드** (터미널 2)
```bash
cd fishing-app/frontend
npm run dev
# localhost:5173
```

**프로덕션 빌드**
```bash
cd fishing-app/frontend
npm run build
```

---

## 📁 프로젝트 구조

```
fishing-app/
├── backend/
│   ├── app.py                        # Flask 애플리케이션
│   ├── requirements.txt              # Python 의존성
│   ├── .env.example                  # 환경변수 예시
│   ├── .gitignore
│   ├── models/
│   │   └── database.py               # SQLite
│   ├── routes/
│   │   ├── tide.py                   # 물때 API
│   │   ├── catches.py                # 조과 기록 API
│   │   ├── user.py                   # 사용자 정보 API
│   │   ├── fishing_index.py          # 낚시지수 API
│   │   └── ...
│   └── services/
│       ├── tide_service.py           # 물때 비즈니스 로직
│       ├── kma_weather_service.py    # 기상청 API 통합
│       ├── khoa_marine_service.py    # KHOA API 통합
│       ├── fishing_index_service.py  # 낚시지수 API 통합
│       └── ...
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── src/
    │   ├── App.jsx
    │   ├── pages/
    │   │   ├── TidePage.jsx          # 물때 탭
    │   │   ├── ExplorePage.jsx       # 탐색 탭 (낚시지수 포함)
    │   │   ├── RecordsPage.jsx       # 기록 탭
    │   │   └── ProfilePage.jsx       # 프로필 탭
    │   ├── components/
    │   │   └── Navbar.jsx            # 네비게이션
    │   └── utils/
    │       └── storage.js            # localStorage 관리
    └── dist/                          # 프로덕션 빌드
```

---

## 🔑 API 키 발급

### 기상청 (KMA)
1. https://data.go.kr 접속
2. "기상청_단기예보" 검색
3. "활용신청" 클릭 (자동승인, ~1시간)
4. 마이페이지 → 개발자 정보 → 인증키 복사

### 국립해양조사원 (KHOA)
1. https://data.go.kr 접속
2. "국립해양조사원_해양관측" 검색
3. "활용신청" 클릭 (1-2일 소요)
4. 승인 후 인증키 복사

### 바다낚시지수
1. https://data.go.kr 접속
2. "바다낚시지수" 검색
3. "활용신청" 클릭
4. 인증키 복사

---

## 🎯 최근 업데이트 (2026-06-10)

### 추가된 기능
- ✅ **실시간 날씨 API** - 기상청 단기예보 통합
- ✅ **바다낚시지수 API** - 낚시지수 조회 및 표시
- ✅ **ExplorePage 낚시지수 탭** - 날짜/위치별 낚시지수 조회

### 개선사항
- 물때 탭 UI/UX 개선
- 날짜/캘린더 네비게이션 통합
- 1시간/3시간 간격 선택
- 실시간 vs 예측 데이터 표시

### 버그 수정
- GPS 위치 정보 바 중복 표시 제거
- 데이터 한 줄 표시 개선
- 음력 필드 키 정규화

---

## 🔐 보안

- API 키는 `.env`에 저장하고 `.gitignore`로 제외
- 위치 정보는 localStorage에 로컬 저장
- 조과 기록 공개/비공개 선택 가능
- CORS 활성화

---

## 📞 지원

문제 발생 시:
1. GitHub Issues 확인
2. 상세 재현 방법 + 스크린샷과 함께 이슈 등록
3. 환경 정보 포함 (OS, Python, Node 버전)

---

## 📄 라이선스

MIT License

---

**Happy Fishing! 🎣**
