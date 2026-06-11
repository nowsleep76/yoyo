# 손맛노트(광어와복어) 개발 매뉴얼

이 문서는 개발이 진행될 때마다 **기능 단위로 추가/변경 내역**을 누적 기록하는 매뉴얼입니다.
새로운 기능을 추가하거나 기존 기능을 수정할 때마다 아래 "작성 규칙"에 따라 새 항목을 맨 아래에 추가해 주세요.

## 작성 규칙

새 개발 건마다 다음 형식으로 항목을 추가합니다.

```
## [날짜] 기능명 (커밋: xxxxxxx)

- **무엇을**: 추가/변경된 기능 요약
- **사용 방법**: 사용자가 화면에서 어떻게 사용하는지
- **관련 파일**: 주요 파일 경로
- **API**: 관련 API 엔드포인트 (있을 경우)
- **비고**: 제한사항, 폴백 동작, 후속 작업 등
```

---

# v1.0 - 초기 버전 (2026-06-08 ~ 2026-06-11)

> 아래는 현재까지 개발된 전체 기능을 탭/영역별로 정리한 베이스라인입니다.

## 1. 물때 탭 (TidePage)

- **무엇을**: 날짜를 선택하면 해당 일자의 물때(1~15물), 조금/중간/사리 구분, 만조·간조 시각(분 단위), 음력 날짜, 일출/일몰, 시간대별 조위·수온·조류속도·날씨·기온·풍속/풍향·파고·강수확률을 1시간 단위로 보여줍니다.
- **사용 방법**: 하단 네비게이션 "물때" 탭 진입 → 상단 날짜 선택 → 24시간 표/그래프 확인. 야간 시간대는 배경색으로 구분되며, 만조/간조 시각에 표시가 강조됩니다.
- **관련 파일**: `frontend/src/pages/TidePage.jsx`, `frontend/src/pages/TidePage.css`, `backend/services/tide_service.py`, `backend/services/tides_korea.py`, `backend/services/kma_weather_service.py`, `backend/services/khoa_marine_service.py`
- **API**: `GET /api/tide`, `GET /api/tide/hourly`, `GET /api/tide/calendar`
- **비고**:
  - 만조/간조 시각은 2차 미분 기반 극값 탐지로 계산되며, 부산 지역 2026-06-09~06-12는 `tides_korea.py`의 공식 조석표 값으로 대체됨(`tideSource: 'official'`). 그 외는 음력 주기 기반 시뮬레이션(`tideSource: 'simulated'`).
  - 날씨/수온/파고는 KMA/KHOA 실데이터 우선, 실패 시 시뮬레이션(`weatherSource: 'api' | 'simulated'`).

## 2. 탐색 탭 (ExplorePage)

### 2.1 기록 (지도 검색)
- **무엇을**: Leaflet 지도에서 지점을 클릭하면 반경 10km 내 다른 사용자의 조과 기록을 검색해 표 형태로 보여줍니다.
- **사용 방법**: "탐색" 탭 → "기록" 서브탭 → 지도 클릭 → 정렬(최신순/조회수/어종별) 선택 → 결과 표 확인 (어종/크기/무게/수온/수심/바람/조류/거리/사용자/날짜).
- **관련 파일**: `frontend/src/pages/ExplorePage.jsx`
- **API**: `GET /api/catches/nearby`
- **비고**: 거리 계산은 Haversine 공식 사용.

### 2.2 출조계획
- **무엇을**: 날짜와 어종을 입력해 100km 반경 내 해당 어종 조과 기록을 검색합니다.
- **사용 방법**: "탐색" 탭 → "출조계획" 서브탭 → 날짜/어종 입력 → 검색 → 결과 표 확인 (어종/크기/위치/거리/물때/수위/사용자/날짜).
- **관련 파일**: `frontend/src/pages/ExplorePage.jsx`
- **API**: `GET /api/catches/nearby?distance=100&date=...&species=...`

### 2.3 어종별
- **무엇을**: 어종 체크박스로 필터링하고 최신순/지역별로 정렬하여 조과 기록을 탐색합니다.
- **사용 방법**: "탐색" 탭 → "어종별" 서브탭 → 어종 선택 → 정렬 선택 → 결과 확인.
- **관련 파일**: `frontend/src/pages/ExplorePage.jsx`
- **API**: `GET /api/catches`, `GET /api/spots/species`

### 2.4 낚시지수
- **무엇을**: 날짜별 종합 낚시지수, 해황 조건(수온/파고/풍속/가시거리), 어종별(우럭/감성돔/광어/농어) 지수, 06:00~19:00 시간대별 추천 어종을 게이지/카드로 보여줍니다.
- **사용 방법**: "탐색" 탭 → "낚시지수" 서브탭 → 날짜 선택 → 게이지 및 시간대별 카드(최초 8개) 확인.
- **관련 파일**: `frontend/src/pages/ExplorePage.jsx`, `backend/services/fishing_index_service.py`, `backend/routes/fishing_index.py`
- **API**: `GET /api/fishing/index`, `GET /api/fishing/forecast`
- **비고**: 실제 API는 당일~D+3만 호출(1시간 캐시), 그 외/실패 시 날짜 해시 기반 시뮬레이션으로 자동 폴백(`data_source: 'api' | 'simulated'`).

## 3. 기록 탭 (RecordsPage)

### 3.1 조과기록
- **무엇을**: 내 조과 기록을 작성/조회/관리합니다. 닉네임, 히트일시, 어종/크기, 채비 정보(낚싯대/릴/원줄/목줄/채비법), 사진, 위치, 메모, 공개 여부를 입력하면 위치 기반 환경 데이터(물때/수위/조류/바람)가 자동으로 채워집니다.
- **사용 방법**: "기록" 탭 → "조과기록" 서브탭 → 상단 통계 카드(총 조과/평균크기/자주잡는어종) 확인 → "새 기록 추가" 클릭 → 폼 작성(지도에서 위치 선택 시 환경 데이터 자동 조회) → 저장. 목록형/SNS형 보기 전환 가능, 항목 클릭 시 상세 패널 표시.
- **관련 파일**: `frontend/src/pages/RecordsPage.jsx`, `backend/routes/catches.py`, `backend/models/database.py`
- **API**: `POST /api/catches`, `GET /api/catches`, `GET/PUT/DELETE /api/catches/<id>`, `POST /api/catches/<id>/like`, `GET /api/tide/hourly`(환경데이터 자동조회)
- **비고**: 채비 정보는 `localStorage`(`fishingAppSuggestions`)에 저장되어 다음 입력 시 자동완성 제안됨.

### 3.2 방문이력
- **무엇을**: 작성한 조과 기록을 낚시터(`spot_name`) 기준으로 그룹핑하여 방문 이력처럼 보여줍니다.
- **사용 방법**: "기록" 탭 → "방문이력" 서브탭에서 확인.
- **관련 파일**: `frontend/src/pages/RecordsPage.jsx`
- **비고**: 클라이언트 측에서 기존 조과 기록 데이터를 가공하여 표시 (별도 DB 테이블 없음).

### 3.3 즐겨찾기
- **무엇을**: 즐겨찾기한 조과 기록만 모아 그리드로 보여줍니다.
- **사용 방법**: "기록" 탭 → "즐겨찾기" 서브탭에서 확인. 각 기록의 즐겨찾기 토글로 추가/제거.
- **관련 파일**: `frontend/src/pages/RecordsPage.jsx`, `backend/routes/catches.py`
- **API**: `POST /api/catches/<id>/favorite`, `GET /api/catches/favorites`

### 3.4 통계
- **무엇을**: 등급 배지, 점수 바(점수/1000), 5종의 막대그래프(물때별/수온별/위치별 상위10/시간대별/어종별 상위8 조과)를 보여줍니다.
- **사용 방법**: "기록" 탭 → "통계" 서브탭에서 확인.
- **관련 파일**: `frontend/src/pages/RecordsPage.jsx`, `backend/models/database.py`(`get_user_stats_filtered`)
- **API**: `GET /api/user/stats`
- **비고**: 점수 = 총조과수×10 + 최대크기×2 + 평균크기×5 + 좋아요수×5. 등급은 6단계(🎣막내낚시꾼 ~ 👨‍⚓영광의어사).

### 3.5 랭킹
- **무엇을**: 등급랭킹/최대어랭킹/다작랭킹 3개 테이블을 각각 상위 5위까지(이모지 순위) 보여줍니다.
- **사용 방법**: "기록" 탭 → "랭킹" 서브탭에서 확인.
- **관련 파일**: `frontend/src/pages/RecordsPage.jsx`, `backend/routes/catches.py`
- **API**: `GET /api/catches/rankings/grade`, `GET /api/catches/rankings/max-size`, `GET /api/catches/rankings/count`, `GET /api/catches/rankings/likes`

## 4. 설정 탭 (ProfilePage)

- **무엇을**: 사용자 ID(최초 생성 후 변경 불가), 닉네임, 선호 낚싯대/릴/원줄/목줄, 선호 어종(18종 중 다중 선택)을 등록/수정합니다.
- **사용 방법**: "설정" 탭 → 정보 입력 → 저장. 최초 저장 시 user_id가 localStorage에 저장되어 이후 자동으로 사용됨.
- **관련 파일**: `frontend/src/pages/ProfilePage.jsx`, `backend/routes/user.py`
- **API**: `GET/POST/PUT /api/user/profile`

## 5. 공통 컴포넌트

### 5.1 낚시 포인트 지도 (FishingMap)
- **무엇을**: 사용자 위치, 등록된 낚시 포인트(사진의 EXIF GPS 자동 추출 지원), 알려진 스팟(★, 어종 필터 가능)을 지도에 표시합니다. 항로표지(OpenSeaMap), 수심지도(GEBCO, 0-10m/10-30m/30-50m/50m+ 범례) 레이어를 토글할 수 있고, 현재 수위·만조/간조 정보를 1시간마다 갱신하는 오버레이를 제공합니다.
- **관련 파일**: `frontend/src/components/FishingMap.jsx`
- **API**: `GET/POST /api/points`, `DELETE /api/points/<id>`, `POST /api/points/upload`, `GET /api/spots`, `GET /api/spots/species`, `GET /api/tide/hourly`

### 5.2 조위 차트 (TideChart)
- **무엇을**: 24시간 조위 데이터를 라인 차트로 표시하고, 당일 설명 및 만조/간조 뱃지를 보여줍니다.
- **관련 파일**: `frontend/src/components/TideChart.jsx`
- **API**: `GET /api/tide`

### 5.3 날씨 카드 (WeatherCard)
- **무엇을**: 현재 기온, 날씨 상태, 풍속/풍향, 습도, 갱신 시각을 표시합니다.
- **관련 파일**: `frontend/src/components/WeatherCard.jsx`
- **API**: `GET /api/weather`

## 6. 백엔드 인프라

### 6.1 API 키 관리 (TOML 기반)
- **무엇을**: `backend/config.py`의 `Config` 클래스가 `secret.toml`(미커밋, `.gitignore` 처리) + 환경변수를 병합하여 KMA/KHOA/낚시지수 API 키를 관리합니다. 환경변수가 TOML 값보다 우선 적용됩니다.
- **관련 파일**: `backend/config.py`, `backend/secret.toml.example`
- **비고**: `secret.toml`이 없거나 키가 `dummy_`/`your_`로 시작하면 `get_api_key(required=True)` 호출 시 예외 발생.

### 6.2 피딩타임 서비스
- **무엇을**: 어종별(우럭/민물고기/문어/낙지) 활성 시간대를 물때 번호와 음력 나이 기반으로 계산합니다.
- **관련 파일**: `backend/services/feeding_service.py`
- **API**: `GET /api/feeding-times`, `GET /api/feeding-times/calendar`, `GET /api/feeding-times/<spot_id>`

### 6.3 테스트 데이터 생성
- **무엇을**: 인천 50건 + 군산 50건의 랜덤 조과 기록(어종/스팟/채비)을 생성하여 개발/데모용 데이터를 채웁니다.
- **관련 파일**: `backend/routes/catches.py`
- **API**: `POST /api/catches/generate-test`
- **비고**: 운영 환경에서는 비활성화 검토 필요.

---

<!-- 새로운 개발 항목은 이 줄 아래에 "작성 규칙" 형식으로 추가하세요. -->
