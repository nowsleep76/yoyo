# 낚시 앱 고도화: 위치 공유 및 출조 계획 기능

## Context
사용자가 다음 개선사항을 요청:
1. 앱 전체에서 선택된 위치 표시
2. 탐색 페이지: 지도 클릭 시 위치 변경 + 거리 기반 공개 기록 정렬
3. 탐색 페이지에 "출조계획" 탭 추가: 날짜+어종으로 게시물 검색
4. 테스트 데이터 100개 재생성 (인천 50개, 군산 50개)

## Current State
- App.jsx: location 상태 관리 + handleLocationChange 함수 존재
- TidePage: 위치 선택 UI (지도, 명소 목록)
- ExplorePage: 공개 기록 조회 + 지도 표시 (클릭 미지원)
- RecordsPage: 새 기록 추가 + 리스트/SNS 모드
- Backend: 거리 기반 조회 API 존재 (/api/catches/nearby)

## Required Changes

### 1. 위치 표시 헤더 추가
**파일**: App.jsx, App.css
- App.jsx main 최상단에 위치 정보 헤더 추가
- 실시간 업데이트되도록 location state 활용
- 좌표 + 지역명 표시

### 2. ExplorePage 기능 확장
**파일**: ExplorePage.jsx, ExplorePage.css

#### 2-1. 기존 탭 (기록)
- 지도 클릭 이벤트: 위치 변경 → App의 handleLocationChange 호출
- 공개 기록만 필터링 (기존 /api/catches/feed 활용)
- 거리 기반 정렬 추가: Haversine 공식으로 계산 후 정렬
- 리스트 형식 (RecordsPage의 리스트 모드 스타일 재사용)

#### 2-2. 새 탭: "출조계획"
- 탭 UI: "기록" | "출조계획" 버튼
- 입력 UI:
  ```
  출조 날짜: [date input]
  대상어종: [text input with autocomplete]
  ```
- 검색 로직:
  1. API: `/api/catches/nearby?lat=X&lng=Y&date=YYYY-MM-DD`에 어종 필터 추가
  2. 같은 날짜 + 같은 어종의 공개 게시물 조회
  3. 거리순 정렬
  4. 없으면 "첫번째 게시자가 되세요!!" 메시지

### 3. Backend API 확장
**파일**: /api/catches/nearby (기존) + 새 쿼리 파라미터

- 현재: `/api/catches/nearby?lat=X&lng=Y&distance=10&sort=latest`
- 추가: `?date=YYYY-MM-DD&species=어종`
- 로직: 거리 + 날짜 + 어종으로 필터링

### 4. ExplorePage → App 위치 연동
**파일**: ExplorePage.jsx, App.jsx

- ExplorePage가 onLocationChange 콜백 받기 (TidePage처럼)
- 지도 클릭 시: `props.onLocationChange({latitude, longitude, name})`
- App에서 location state 업데이트 → 헤더에 표시

### 5. 테스트 데이터 재생성
**파일**: /api/catches/generate-test (기존 엔드포인트 수정)

#### 인천 지역 (50개)
- 좌표: 37.27~37.49 (위도), 126.57~126.70 (경도)
- 어종: 우럭, 광어, 농어, 전갈이
- 날짜: 최근 30일
- 모든 필드 채우기: species, size_cm, user_nickname, tide_number, water_level, tidal_current, wind_speed, description, is_public=true

#### 군산 지역 (50개)
- 좌표: 35.95~36.05 (위도), 126.55~126.72 (경도)
- 어종: 우럭, 광어, 감성돔, 방어
- 날짜: 최근 30일
- 모든 필드 채우기

## Critical Files
1. `/d/DEV/fishing-app/frontend/src/App.jsx` - 위치 헤더 추가 + onLocationChange 전달
2. `/d/DEV/fishing-app/frontend/src/pages/ExplorePage.jsx` - 탭 추가 + 위치 연동 + 거리 정렬
3. `/d/DEV/fishing-app/frontend/src/pages/ExplorePage.css` - 출조계획 입력 UI 스타일
4. `/d/DEV/fishing-app/backend/routes/catches.py` - generate-test 수정 + nearby API 필터 추가
5. `/d/DEV/fishing-app/frontend/src/App.css` - 위치 헤더 스타일

## Reusable Patterns
- RecordsPage의 리스트 테이블 스타일 → ExplorePage 기록 탭에 재사용
- TidePage의 onLocationChange 패턴 → ExplorePage도 동일하게 구현
- Haversine 거리 계산 → 이미 ExplorePage에 구현되어 있음

## Verification
1. 위치 헤더가 실시간 업데이트되는지 확인
2. ExplorePage 지도 클릭 → location 변경 → 헤더 업데이트 확인
3. 기록 탭: 거리순 정렬 확인
4. 출조계획 탭: 날짜+어종으로 게시물 조회 확인
5. 테스트 데이터: 인천 50개 + 군산 50개 생성 확인
