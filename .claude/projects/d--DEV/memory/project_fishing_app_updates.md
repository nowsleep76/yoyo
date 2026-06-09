---
name: Phase4_tide_and_explore_updates
description: TidePage 물때 개선, ExplorePage 탐색 기능 개선
metadata:
  type: project
---

## ExplorePage 탐색 기능 (2026-06-09)

### 지도 클릭 기능 추가
- 지도의 모든 위치를 클릭 가능하게 변경
- 클릭 시 주변 10km 범위 내 공개 기록 표시
- 10km 범위를 시각적 원(circle)으로 지도에 표시
- 거리는 Haversine 공식으로 정확히 계산

### 조회 결과 테이블
테이블 컬럼: 어종, 크기, 무게, 수온, 조류, **거리**, 사용자, 날짜
- 거리 컬럼으로 클릭 위치에서의 거리(km) 표시
- 수온, 조류 정보 표시

### 탭별 소팅 (filterType 변경 시 재조회)
- 최신순 (latest): caught_at 기준
- 조회수 (views): view_count 기준  
- 어종별 (species): species 알파벳 순서

### 마커 팝업 정보 강화
팝업에 표시: 어종, 크기, 수온, **바람/날씨**, 조류, 무게, 사용자, 날짜

### 백엔드 API 추가
`GET /api/catches/nearby?lat=X&lng=Y&distance=10&sort=latest`
- 거리 기반 공개 기록 조회
- distance_km 필드 자동 계산
- sort 파라미터로 결과 정렬

### 미구현 항목
**수심(depth) 데이터** - 현재 catch_records 테이블에 depth 필드 없음
- 해로드 앱처럼 수심 정보를 표시하려면 DB 스키마 확장 필요
- 추후 추가 가능

**바람 세기(wind_speed) 데이터** - 현재 weather_condition(텍스트)만 있음
- 바람 세기(m/s) 수치 데이터 필요
- 물때 페이지의 hourly windSpeed와 연계 가능
