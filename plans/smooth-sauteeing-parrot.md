# 낚시 앱 V2: 통계 및 랭킹 시스템

## Context
사용자가 다음 기능을 요청:
1. 기록 페이지에 **통계 탭** - 나의 낚시 실적 + 재미있는 등급
2. 기록 페이지에 **랭킹 탭** - 전체 사용자 랭킹 (등급, 최대어, 다작)

## Current State
- RecordsPage: 현재 3개 탭 (조과 기록, 방문 이력, 즐겨찾기)
- 백엔드: 기본 통계 API 존재 (/api/user/stats)
- 테스트 데이터: 100개 (인천 50개, 군산 50개)

## Required Changes

### 1. 재미있는 낚시 등급 시스템
**등급 기준 (종합 점수 기반):**

```
점수 계산 = (총 마리수 × 10) + (최대어 cm × 2) + (평균 크기 × 5) + (좋아요수 × 5)

등급 배분:
- 0-50점: 🎣 막내 낚시꾼 ("이제 시작이에요!")
- 51-150점: 🌊 물때 배우는중 ("물때 감을 익혀요!")
- 151-300점: 🎯 묵직한 손맛 ("조황을 알아요!")
- 301-500점: 👑 대물사냥꾼 ("큰 고기가 나를 부릅니다!")
- 501-800점: 🏆 낚시의 신 ("바다가 나를 따라요!")
- 801+점: 👨‍⚓ 영광의 어사 ("낚시의 전설입니다!")
```

### 2. RecordsPage 탭 구조
현재: records | history | favorites
추가: records | history | favorites | **통계** | **랭킹**

### 3. 통계 탭 (내 정보)
```
┌─────────────────────────────────┐
│     나의 낚시 통계               │
├─────────────────────────────────┤
│ 등급: 👑 대물사냥꾼               │
│ 점수: 425/1000                   │
│                                 │
│ 📊 주요 지표:                    │
│ • 총 조과: 42마리                │
│ • 최대어: 51.2cm (우럭)          │
│ • 평균 크기: 38.5cm              │
│ • 좋아요 받음: 156개             │
│                                 │
│ 🎯 다음 등급까지: 75점 남음      │
└─────────────────────────────────┘
```

### 4. 랭킹 탭 (전체 사용자)
```
📊 등급 랭킹
┌───┬──────────┬────────┬─────┐
│순 │ 사용자   │ 등급   │ 점수 │
├───┼──────────┼────────┼─────┤
│1️⃣ │ user1    │ 👑 대물│ 520 │
│2️⃣ │ user2    │ 👑 대물│ 480 │
│3️⃣ │ user3    │ 🎯 손맛│ 385 │
└───┴──────────┴────────┴─────┘

🏆 최대어 랭킹
┌───┬──────────┬────────┬────────┐
│순 │ 사용자   │ 어종   │ 크기   │
├───┼──────────┼────────┼────────┤
│1️⃣ │ user1    │ 광어   │ 52.3cm │
│2️⃣ │ user2    │ 우럭   │ 51.2cm │
│3️⃣ │ user3    │ 감성돔 │ 48.5cm │
└───┴──────────┴────────┴────────┘

🐟 다작 랭킹 (마리수)
┌───┬──────────┬────────┐
│순 │ 사용자   │ 마리수 │
├───┼──────────┼────────┤
│1️⃣ │ user1    │ 52마리 │
│2️⃣ │ user2    │ 42마리 │
│3️⃣ │ user3    │ 38마리 │
└───┴──────────┴────────┘
```

### 5. Backend API 개선

#### 5-1. 사용자 통계 API 확장
`GET /api/user/stats`
```json
{
  "totalCatches": 42,
  "maxSize": 51.2,
  "maxSpecies": "우럭",
  "averageSize": 38.5,
  "likes": 156,
  "score": 425,
  "grade": "👑 대물사냥꾼",
  "gradeDescription": "큰 고기가 나를 부릅니다!"
}
```

#### 5-2. 전체 랭킹 API 추가
- `GET /api/catches/rankings/grade` - 등급 랭킹 (상위 10명)
- `GET /api/catches/rankings/max-size` - 최대어 랭킹 (상위 10명)
- `GET /api/catches/rankings/count` - 다작 랭킹 (상위 10명)

### 6. Frontend 구현

#### RecordsPage.jsx 변경
```javascript
const [activeTab, setActiveTab] = useState('records')
// 추가: 'stats' 탭 + 'rankings' 탭

// stats 탭: 내 통계 표시
// rankings 탭: 3개의 랭킹 섹션 표시
```

## Critical Files
1. `/d/DEV/fishing-app/backend/routes/catches.py` - 랭킹 API 추가
2. `/d/DEV/fishing-app/frontend/src/pages/RecordsPage.jsx` - 탭 추가 + 통계/랭킹 UI
3. `/d/DEV/fishing-app/frontend/src/pages/RecordsPage.css` - 통계 & 랭킹 스타일

## Grade Calculation Logic
```python
def calculate_score(total_catches, max_size, average_size, likes):
    return (total_catches * 10) + (max_size * 2) + (average_size * 5) + (likes * 5)

def get_grade(score):
    if score < 51:
        return "🎣 막내 낚시꾼"
    elif score < 151:
        return "🌊 물때 배우는중"
    elif score < 301:
        return "🎯 묵직한 손맛"
    elif score < 501:
        return "👑 대물사냥꾼"
    elif score < 801:
        return "🏆 낚시의 신"
    else:
        return "👨‍⚓ 영광의 어사"
```

## Verification
1. 통계 탭 열었을 때 내 점수 + 등급 표시
2. 랭킹 탭에서 3개의 랭킹 모두 정렬 확인
3. 점수 계산이 정확한지 검증
4. 등급 기준이 정확히 적용되는지 확인
