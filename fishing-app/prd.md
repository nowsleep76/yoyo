# 손맛노트(광어와복어) - 제품 요구사항 정의서 (PRD)

> 본 문서는 `fishing-app` 프로젝트의 실제 소스 코드와 git 커밋 이력을 기반으로 작성되었습니다.

## 1. 개요

- **제품명**: 광어와복어 (Navbar 브랜드명, 가칭 "손맛노트")
- **한 줄 정의**: 한국 연안 낚시인을 위한 물때/날씨/낚시지수 정보 제공 + 조과(catch) 기록 및 커뮤니티 랭킹 서비스
- **목적**:
  - 낚시 출조 전 물때, 일출/일몰, 조류, 낚시지수 등 의사결정에 필요한 정보를 한 화면에서 제공
  - 사용자가 직접 조과(어획) 기록을 남기고 사진/위치/채비 정보를 관리
  - 다른 사용자의 기록을 지도/필터 기반으로 탐색하여 출조 계획 수립에 활용
  - 등급/랭킹 시스템을 통한 게임화(gamification) 요소 제공
- **타겟 사용자**: 한국 연안(서해/남해/동해/제주/내수면) 낚시를 즐기는 일반 사용자

## 2. 기술 스택

### Frontend
- React 18.2 + Vite 4.3 (개발 서버 포트 `8001`, `/api` 요청은 `localhost:8000`으로 프록시)
- Leaflet 1.9 (지도), OpenStreetMap / OpenSeaMap(항로표지) / GEBCO(수심) 타일
- Recharts 2.10 (차트)
- exifr 7.1 (사진 EXIF GPS 추출)
- 상태 저장: `localStorage` 기반 `StorageUtils` (frontend/src/utils/storage.js)

### Backend
- Flask 3.0 (Python 3.14), Flask-CORS 4.0
- SQLite (`fishing_app.db`)
- requests 2.31, python-dotenv 1.0, tomli 2.0 (TOML 설정 파싱)
- 업로드 파일은 `backend/uploads/`에 저장, `/uploads/<filename>`으로 서빙 (최대 16MB)

### 외부 API
- 기상청(KMA) 단기예보 API (`VilageFcstInfoService_2.0`)
- 국립해양조사원(KHOA) 해양관측 API (`apis.data.go.kr/1192136/dtRecent`)
- 바다낚시지수 API (`apis.data.go.kr/1763000/FishingBlue/baseFishingIndex`)
- 모든 외부 API는 실패 시 시뮬레이션(가상) 데이터로 자동 폴백

### 설정/보안
- `backend/config.py`의 `Config` 클래스가 `secret.toml` 파일 + 환경변수를 병합하여 API 키 관리
- 환경변수(`KMA_SERVICE_KEY`, `KHOA_SERVICE_KEY`, `FISHING_INDEX_API_KEY`, `FLASK_ENV`, `FLASK_DEBUG`)가 TOML 값보다 우선
- `secret.toml`은 `.gitignore` 처리, `secret.toml.example`을 템플릿으로 제공

## 3. 정보 구조 (IA)

앱은 4개의 메인 탭으로 구성되며, 기본 진입 탭은 **물때**입니다.

| 탭 | 컴포넌트 | 설명 |
|---|---|---|
| 물때 (tide) | `TidePage` | 일자별 물때/조류/일출몰/날씨 정보 |
| 탐색 (explore) | `ExplorePage` | 다른 사용자 기록 탐색, 출조계획, 낚시지수 |
| 기록 (records) | `RecordsPage` | 내 조과 기록 작성/관리, 통계, 랭킹 |
| 설정 (profile) | `ProfilePage` | 사용자 프로필 및 선호 채비/어종 설정 |

위치 정보는 브라우저 Geolocation API로 3초 이내 응답 시 사용, 실패 시 서울(37.5665, 126.9780, '내 위치')로 폴백합니다. 위치 헤더는 '물때'/'설정' 탭을 제외한 화면에 표시됩니다.

> 참고: `LocationPage.jsx`(지역 설정, GPS+12개 프리셋 지역)와 `Home.jsx`(대시보드)는 소스에 존재하지만 `App.jsx` 라우팅에는 연결되어 있지 않습니다 (미사용/레거시 코드).

## 4. 기능 요구사항

### 4.1 물때 탭 (TidePage)

- 날짜 선택 + 탭 네비게이션 통합 UI
- 1시간 단위 조위(높이) 그래프와 시간대별 데이터 표시
- 만조/간조 시각을 분 단위까지 표시 (2차 미분 기반 극값 탐지 알고리즘)
- 물때 번호(1~15물), 조금/중간/사리 구분 및 강도(약/중/강) 표시
- 음력 날짜 변환 표시
- 일출/일몰 시각(천체 이벤트) 표시, 야간 시간대 배경색 구분
- 시간대별 수온, 조류 속도, 날씨, 기온, 풍속/풍향, 파고, 강수확률 표시
- 데이터 출처(`weatherSource`, `tideSource`: `api`/`official`/`simulated`) 구분

### 4.2 탐색 탭 (ExplorePage) — 4개 서브탭

#### 4.2.1 기록 (지도 검색)
- Leaflet 지도에서 지점 클릭 → 반경 10km 원 표시, 해당 영역 내 조과 기록 검색 (`/api/catches/nearby`)
- 정렬: 최신순 / 조회수 / 어종별
- 결과 테이블: 어종, 크기, 무게, 수온, 수심, 바람, 조류, 거리, 사용자, 날짜

#### 4.2.2 출조계획
- 날짜 + 어종 입력 후 검색 (`/api/catches/nearby?distance=100&date=...&species=...`)
- 결과 테이블: 어종, 크기, 위치, 거리, 물때, 수위, 사용자, 날짜

#### 4.2.3 어종별
- 어종 체크박스 필터 + 정렬(최신순/지역별)
- 결과 테이블 표시

#### 4.2.4 낚시지수
- 날짜 선택 후 `/api/fishing/index` 조회
- 종합 낚시지수 게이지, 해황 조건(수온/파고/풍속/가시거리)
- 어종별(우럭/감성돔/광어/농어 등) 지수 게이지
- 06:00~19:00 시간대별 카드 (최초 8개 표시), 시간대별 추천 어종(`best_fish`)

### 4.3 기록 탭 (RecordsPage) — 5개 서브탭

#### 4.3.1 조과기록
- 통계 카드: 총 조과 수 / 평균 크기 / 자주 잡는 어종
- "새 기록 추가" 폼:
  - 닉네임, 히트일시(날짜+시간)
  - 위치 선택 시 `/api/tide/hourly`로 물때/수위/조류/바람 등 환경 데이터 자동 조회
  - 사진 업로드, Leaflet 지도 기반 위치 선택
  - 기본정보(어종/크기), 채비정보(낚싯대/릴/원줄/목줄/채비법 - localStorage(`fishingAppSuggestions`) 자동완성)
  - 메모, 공개/비공개 설정
  - `POST /api/catches`로 저장
- 목록형/SNS형 표시 전환, 기록 상세 패널

#### 4.3.2 방문이력
- 클라이언트 측에서 기록을 `spot_name` 기준으로 그룹핑하여 표시

#### 4.3.3 즐겨찾기
- 즐겨찾기한 기록만 그리드로 표시

#### 4.3.4 통계
- 등급 배지, 점수 바(점수/1000)
- Recharts 막대그래프 5종: 물때별 / 수온별 / 위치별(상위10) / 시간대별 / 어종별(상위8) 조과

#### 4.3.5 랭킹
- 등급랭킹 / 최대어랭킹 / 다작랭킹 3개 테이블 (각 상위 5위, 이모지 순위 표시)

### 4.4 설정 탭 (ProfilePage)

- 사용자 ID(최초 생성 후 변경 불가), 닉네임
- 선호 낚싯대/릴/원줄/목줄
- 선호 어종(18종 중 다중 선택)
- `GET/POST/PUT /api/user/profile`로 저장, 최초 생성 시 user_id를 localStorage에 저장

## 5. API 명세

### 물때 (`/api/tide*`)
| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/tide` | 현재 위치 기준 물때/조위 데이터 |
| GET | `/api/tide/hourly` | 날짜별 24시간 조위/수온/만조·간조/날씨 |
| GET | `/api/tide/calendar` | N일치(기본 7일) 물때 캘린더 |

### 날씨 (`/api/weather`)
| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/weather` | 위경도 기반 현재 날씨(시뮬레이션) |

### 낚시지수 (`/api/fishing/*`)
| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/fishing/index` | 일자별 종합/어종별 낚시지수 (실패 시 시뮬레이션 폴백) |
| GET | `/api/fishing/forecast` | N일치(기본 7일) 낚시지수 예보 |

### 피딩타임 (`/api/feeding-times*`)
| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/feeding-times` | 위경도/날짜 기준 어종별 활성 시간대 |
| GET | `/api/feeding-times/calendar` | N일치(최대 365일) 피딩 캘린더 |
| GET | `/api/feeding-times/<spot_id>` | 특정 포인트의 피딩타임 |

### 낚시 포인트 (`/api/points*`)
| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/points` | 포인트 목록 조회 |
| POST | `/api/points` | 포인트 등록 |
| GET | `/api/points/<id>` | 포인트 상세 |
| DELETE | `/api/points/<id>` | 포인트 삭제 |
| POST | `/api/points/upload` | 이미지 업로드 (png/jpg/jpeg/gif/webp) |

### 알려진 스팟 (`/api/spots*`)
| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/spots` | 스팟 목록 (어종 필터 가능) |
| GET | `/api/spots/species` | 스팟별 어종 목록 |

### 조과 기록 (`/api/catches*`)
| Method | Endpoint | 설명 |
|---|---|---|
| POST | `/api/catches` | 조과 기록 생성 |
| GET | `/api/catches` | 목록 조회 (limit/offset/정렬) |
| GET | `/api/catches/<id>` | 상세 조회 (조회수 증가) |
| PUT | `/api/catches/<id>` | 수정 |
| DELETE | `/api/catches/<id>` | 삭제 |
| POST | `/api/catches/<id>/like` | 좋아요 |
| GET | `/api/catches/feed` | SNS 피드 (어종 필터) |
| POST | `/api/catches/generate-test` | 테스트 데이터 100건 생성 (인천 50 + 군산 50) |
| GET | `/api/catches/nearby` | Haversine 거리 기반 근처 기록 검색 (lat/lng/distance/date/species, 정렬: 조회수/어종/거리) |
| GET | `/api/catches/rankings/grade` | 등급 랭킹 Top 10 |
| GET | `/api/catches/rankings/max-size` | 최대어 랭킹 Top 10 |
| GET | `/api/catches/rankings/count` | 다작 랭킹 Top 10 |
| GET | `/api/catches/rankings/likes` | 좋아요 랭킹 Top 10 |
| POST | `/api/catches/<id>/favorite` | 즐겨찾기 토글 |
| GET | `/api/catches/favorites` | 즐겨찾기 목록 |

### 사용자 (`/api/user/*`)
| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/user/stats` | 사용자 통계 (user_id 선택) |
| GET | `/api/user/history` | 출조 이력 조회 |
| POST | `/api/user/history` | 출조 이력 등록 |
| GET | `/api/user/favorite-spots` | 즐겨찾는 스팟 목록 |
| POST | `/api/user/favorite-spots/<id>` | 즐겨찾는 스팟 추가 |
| DELETE | `/api/user/favorite-spots/<id>` | 즐겨찾는 스팟 삭제 |
| GET | `/api/user/favorite-catches` | 즐겨찾는 조과 기록 목록 |
| GET | `/api/user/profile` | 프로필 조회 |
| POST | `/api/user/profile` | 프로필 생성 |
| PUT | `/api/user/profile` | 프로필 수정 |

### 시스템
| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/health` | 헬스체크 |
| GET | `/uploads/<filename>` | 업로드 파일 서빙 |

## 6. 데이터베이스 설계 (SQLite, `fishing_app.db`)

| 테이블 | 설명 |
|---|---|
| `fishing_points` | 사용자 등록 낚시 포인트 (사진/위치 포함) |
| `known_spots` | 사전 등록된 25개 유명 낚시 스팟 (서해/남해/동해/제주/내수면) |
| `catch_records` | 조과 기록 (어종/크기/무게/환경정보/채비/사진/공개여부 등) |
| `catch_likes` | 조과 기록 좋아요 |
| `fishing_sessions` | 출조 이력 |
| `favorite_spots` | 사용자별 즐겨찾는 스팟 |
| `catch_favorites` | 사용자별 즐겨찾는 조과 기록 |
| `users` | 사용자 프로필 (닉네임, 선호 채비/어종) |

주요 함수: `add_catch_record`, `get_all_catches`, `get_catch_by_id`(조회수 증가 포함), `update_catch_record`, `delete_catch_record`, `like_catch_record`, 즐겨찾기 CRUD, `add_user`/`get_user`/`update_user`, `get_user_stats`/`get_user_stats_filtered`(총 조과수/평균크기/최대크기/좋아요수/선호어종/점수/등급/물때분포/어종분포/시간대분포 반환)

## 7. 등급/점수 시스템

```
점수 = 총조과수×10 + 최대크기×2 + 평균크기×5 + 좋아요수×5
```

| 점수 구간 | 등급 |
|---|---|
| < 51 | 🎣 막내낚시꾼 |
| < 151 | 🌊 물때배우는중 |
| < 301 | 🎯 묵직한손맛 |
| < 501 | 👑 대물사냥꾼 |
| < 801 | 🏆 낚시의신 |
| ≥ 801 | 👨‍⚓ 영광의어사 |

## 8. 외부 API 연동 및 폴백 전략

| 데이터 | 우선순위 1 (실데이터) | 우선순위 2 (공식 보조데이터) | 폴백 (시뮬레이션) |
|---|---|---|---|
| 날씨/기온/풍향/강수 | KMA 단기예보(`VilageFcstInfoService_2.0`) | - | sin 함수 기반 시간대별 가상값 |
| 수온/파고 | KHOA 해양관측(`dtRecent`, 최근접 관측소 검색) | - | sin 함수 기반 가상값 |
| 만조/간조/물때번호 | - | `tides_korea.py`의 공식 조석표(현재 부산 6/9~6/12 보유) | 음력 주기(29.5306일) 기반 시뮬레이션 |
| 낚시지수 | 바다낚시지수 API (당일~D+3, 1시간 캐시) | - | 날짜 해시 기반 가상 지수 (우럭/감성돔/광어/농어) |
| 피딩타임 | - | - | 어종별 `FEEDING_PATTERNS` + 음력 활성도 계산 |

`weatherSource`/`tideSource`/`data_source` 필드를 응답에 포함하여 프론트엔드가 데이터 출처를 표시할 수 있도록 함.

## 9. 개발 이력 (커밋 기준)

| 날짜 | 커밋 | 내용 |
|---|---|---|
| 2026-06-08 | `0e57af8` | 낚시앱 API 응답 형식 개선 |
| 2026-06-09 | `3a142c3` | Version1: 완전한 낚시 앱 구현 - 물때, 탐색, 기록 완성 |
| 2026-06-09 | `3b9bc8c` | 통계 및 랭킹 시스템 구현 완료 |
| 2026-06-09 | `bbe6096` | 물때 탭 개선: 음력 계산 정확화 및 날짜 연동 강화 |
| 2026-06-09 | `1754362` | 물때 탭 UI 개선: 날짜 선택과 탭 네비게이션 통합 |
| 2026-06-09 | `65bae5c` | 물때 탭 기능 대폭 개선: 3시간 단위 데이터, 헤더 고정, 배경 그래디언트 |
| 2026-06-09 | `b8666d4` | 물때 탭 UI 정밀화: 만조/간조 표시 개선, 헤더 한 줄화 |
| 2026-06-09 | `793b0de` | 물때 탭 가독성 개선: 일출/일몰 표시 수정, 만조/간조 구분, 야간 배경색 개선 |
| 2026-06-09 | `35ebbf6` | 물때 표 정밀도 대폭 향상: 분 단위 시간, 만조/간조 수위 변화 표시 |
| 2026-06-10 | `2d9965c` | 테이블 UI 개선: 각 행을 한 라인으로 표시하도록 CSS 레이아웃 수정 |
| 2026-06-10 | `5e9f3d4` | 물때 탭 UI 개선: 네비게이션/데이터 포맷 통합 재설계 |
| 2026-06-10 | `9b91eff` | 실시간 날씨 API 연동 인프라 구축: KMA/KHOA 서비스 + 폴백 시뮬레이션 |
| 2026-06-10 | `6ccc9de` | 기상청 API 키 설정 및 정리: KMA 서비스키 적용 |
| 2026-06-10 | `81a081c` | 바다낚시지수 API 연동: ExplorePage에 낚시지수 탭 신설 |
| 2026-06-10 | `de9571d` | 프로젝트 README 작성: 낚시앱 기능 및 개발 현황 정리 |
| 2026-06-11 | `bd9e629` | 낚시지수 API 자동 폴백: 실패 시 시뮬레이션 모드로 전환 |
| 2026-06-11 | `94e6c76` | Python 모듈 구조 개선: `__init__.py` 추가 |
| 2026-06-11 | `f0e00c0` | 보안: API 키 관리를 TOML 파일 기반으로 강화 |
| 2026-06-11 | `e82fb91` | 물때 정확도 개선: 공식 조석표 데이터 연동 및 KHOA/KMA API 수정 |

## 10. 알려진 제한사항 / 향후 과제

- **공식 조석표 커버리지 부족**: `tides_korea.py`에 부산 지역 2026-06-09~06-12 4일치만 공식 데이터가 있고, 그 외 날짜/지역은 음력 주기 기반 시뮬레이션 사용
- **날씨/해양 데이터 폴백**: KMA/KHOA API 키 미설정 또는 호출 실패 시 시뮬레이션 데이터로 자동 전환되며, `weatherSource` 필드로만 구분 가능
- **낚시지수 API 호출 범위 제한**: 당일~D+3일만 실제 API 호출, 그 외 기간은 시뮬레이션
- **미연동 페이지**: `LocationPage.jsx`(지역 설정), `Home.jsx`(대시보드)는 구현되어 있으나 `App.jsx`에 라우팅되지 않음
- **README 포트 표기 불일치**: `README.md`에는 프론트엔드 포트가 5173으로 기재되어 있으나, 실제 `vite.config.js`는 `8001`(strictPort) 사용
- **테스트 데이터 생성 API**(`/api/catches/generate-test`)는 개발/데모용으로, 운영 환경에서는 비활성화 검토 필요
