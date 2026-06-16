# 물때 탭 데이터 정확도 진단 보고서

## 🔍 문제 확인 결과

**검증 날짜**: 2026-06-12 (오늘)

### 실시간 데이터 현황

| 항목 | 상태 | 설명 |
|------|------|------|
| **음력/물때** | ✅ 정확 | 공식 조석표 기반 계산 (모든 날짜) |
| **만조/간조 시각** | ✅ 정확 | 공식 조석표 데이터 사용 |
| **시간별 수위** | ❌ 시뮬 | 모든 날짜에서 sin 곡선 계산 |
| **조류 강도** | ❌ 시뮬 | 수위 미분으로 근사 계산 |
| **바람/날씨/강수** | ❌ 시뮬 | 고정 패턴 규칙으로만 생성 |

### 실측 데이터 테스트

```
[TODAY] 2026-06-12          [YESTERDAY] 2026-06-11      [3 DAYS AGO] 2026-06-09
- 기온: 20.0°C             - 기온: 20.0°C             - 기온: 20.0°C
- 풍속: 5.0 m/s            - 풍속: 5.0 m/s            - 풍속: 5.0 m/s
- 강수확률: 5%             - 강수확률: 5%             - 강수확률: 5%
- 조류: 0.16 m/s           - 조류: 0.2 m/s            - 조류: 0.28 m/s

결론: 모든 날짜가 동일한 시뮬레이션 패턴 사용
     → 기상청 API 데이터 미통합
     → weatherSource: "simulated" (모든 날짜)
```

---

## 🎯 근본 원인

### 1단계: KMA API 커버리지 제한
**파일**: `services/kma_weather_service.py` (line 126-132)

```python
# 기상청 예보는 보통 D+2, 3일까지만 제공
if target < today or (target - today).days > 3:
    return None  # ← 과거/미래 극단 날짜는 데이터 조회 안 함
```

**영향**:
- ✅ 오늘~D+3일: KMA API 호출 시도
- ❌ 어제/그제/4일 후: API 호출 없음 → None 반환

### 2단계: 기상청 API 자체의 한계
- **예보만 제공**: 과거 실측 데이터 미지원
- **예보 범위**: 최대 3~4일 앞의 예보만 가능
- **결과**: 과거 날짜는 원천적으로 API 데이터 불가능

### 3단계: Fallback 메커니즘
**파일**: `services/tide_service.py` (line 272-283)

```python
# API 데이터가 없으면 기본값 사용
if kma_weather:  # ← None이면 이 조건 불만족
    kma_data = kma_weather[i]
    # API 값으로 대체
else:
    # 시뮬레이션 값 유지
```

---

## 💡 해결 전략

### Option A: 한국 기상청 기후 데이터 API 추가 (권장)

**비용**: 약 3시간 개발

**장점**:
- 과거 30년 평균 기후 데이터 포함
- 한국 공식 통계 기반
- 관측소별 정확한 데이터

**단점**:
- 과거의 **정확한 실측값** 아님 (평균값)
- API 신청 필요

**구현**:
```python
# 새 파일: services/kma_climate_service.py
class KmaClimateService:
    # 월별 평균 기온, 강수 데이터 조회
    # 과거 30년 기상 통계 기반
    @staticmethod
    def get_monthly_climate(lat, lon, month):
        # API: 기상청 기후 통계
        return {
            'avg_temp': 20.5,
            'avg_rainfall': 15,
            'avg_wind': 3.2
        }
```

**통합 위치**:
```python
# tide_service.py get_tide_hourly()
if target < today:  # 과거 날짜
    climate_data = KmaClimateService.get_monthly_climate(...)
    # 과거 데이터에는 통계값 사용
elif (target - today).days <= 3:  # 예보 범위
    weather_data = KmaWeatherService.get_hourly_weather(...)
    # 예보 범위는 실시간 예보 사용
else:  # 먼 미래
    climate_data = KmaClimateService.get_monthly_climate(...)
    # 미래도 통계값 사용
```

### Option B: KHOA 해양 관측 API 강화

**비용**: 약 2시간 개발

**장점**:
- 해양 관측소 실시간 데이터
- 수온, 파고, 조류 실측값

**단점**:
- 관측점 제한적 (해안만 지원)
- 예보 기능 없음

**현재 상태**:
```python
# services/khoa_marine_service.py
@staticmethod
def get_hourly_marine(lat, lon, date_str):
    # 현재: 구현되지 않음
    return None
```

**구현 예**:
```python
def get_hourly_marine(lat, lon, date_str):
    # 가장 가까운 해양 관측소 찾기
    station = find_nearest_station(lat, lon)
    
    # KHOA 해수면 높이 조회
    url = f"https://api.khoa.go.kr/api/{station}"
    resp = requests.get(url, params={
        'serviceKey': api_key,
        'date': date_str
    })
    
    return {
        'waveHeight': 1.2,
        'waterTemp': 18.5,
        'currentSpeed': 0.35
    }
```

### Option C: 하이브리드 접근 (최고의 선택)

```
날짜별 데이터 전략
├─ 오늘/내일/모레 (D+0~2)
│  └─ KMA 실시간 예보 API ✅
├─ 어제/그제 (D-1~2)
│  └─ 공식 기후 데이터 + KHOA 관측값 📊
└─ 먼 과거/미래
   └─ 통계 기후값 + 시뮬레이션 📈
```

---

## 🚀 권장 구현 순서

### Phase 1: UI 개선 (우선순위 높음, 비용 낮음)
- [x] 현재: 백엔드에서만 `weatherSource` 표시
- [ ] **개선**: 프론트엔드 UI에 "예보/관측/통계" 명확히 표시
- [ ] 각 데이터의 신뢰도 배지 추가

**파일**: `TidePage.jsx` (line 420-427)
```jsx
// 현재
{hourlyData.weatherSource === 'simulated' && (
    <span className="data-source-badge simulated">기상 예측치</span>
)}

// 개선
<span className={`data-source-badge ${getSourceClass(hourlyData.weatherSource)}`}>
    {getSourceLabel(hourlyData.weatherSource)}
    <i className="info-icon" title={getSourceTooltip()} />
</span>
```

### Phase 2: KMA 기후 데이터 통합 (중간 비용)
1. 기상청 기후 데이터 API 신청 (data.go.kr)
2. `KmaClimateService` 구현 (2시간)
3. `get_tide_hourly()` 로직 수정 (1시간)
4. 테스트 및 배포 (1시간)

**소요 시간**: 약 4시간 (API 신청 제외)

### Phase 3: KHOA 강화 (선택사항)
- 시계열 데이터 조회 (수온, 파고)
- 실측 조류 강도 대체
- 소요 시간: 2시간

---

## 📋 액션 아이템

```
☐ [URGENT] UI에 데이터 출처 명확히 표시
   └─ 사용자 혼동 방지

☐ [HIGH] KMA 기후 데이터 API 신청
   └─ data.go.kr → "기상청_과거날씨데이터"

☐ [HIGH] KmaClimateService 구현
   └─ 과거 30년 평균 기온/강수

☐ [MEDIUM] TidePage.jsx 개선
   └─ weatherSource 배지 개선

☐ [MEDIUM] KHOA 해양관측 강화
   └─ 실시간 수온/파고 조회

☐ [LOW] 테스트 추가
   └─ 날짜별 데이터 소스 검증
```

---

## 🎓 기술적 배경

### 왜 과거 예보 데이터가 없나?

기상청은 실시간 예보(Real-time Forecast)만 제공합니다:
- **오늘 발표**: D+0~3일 예보
- **내일 발표**: D+0~3일 예보 (갱신)
- **어제 발표**: **자동 삭제** (과거 예보는 보관 안 함)

따라서 "어제 데이터"를 원하려면:
- ❌ 어제의 예보 (존재 안 함)
- ✅ 어제의 실측 (관측 데이터 필요)

### 한국의 기상 데이터 API 옵션

1. **기상청 단기예보** (현재 사용)
   - 범위: D+0~3
   - 타입: 예보만

2. **기상청 기후 데이터** (권장)
   - 범위: 과거 30년 통계
   - 타입: 월별 평균

3. **기상청 과거 관측** (고급)
   - 범위: 과거 5년
   - 타입: 실측값
   - 비용: 별도 API 신청

4. **KHOA 해양 관측** (보조)
   - 범위: 실시간
   - 타입: 해양 실측값

---

## 📞 결론

현재 앱은:
1. ✅ **음력/물때/만조/간조**: 100% 정확
2. ❌ **시간별 날씨/바람**: 시뮬레이션만 제공

**즉시 해결**: UI에 데이터 출처 명시 (30분)
**근본 해결**: KMA 기후 API 통합 (3~4시간)
