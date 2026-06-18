# 실시간 API 데이터 연동 가이드

## 📊 현재 시스템 아키텍처

### 1. 조석 데이터 (Tide Data)
**상태**: ✅ 완전 구현  
**우선순위**:
1. 공식 조석표 (한국 6월 데이터)
2. 음력 기반 반일주기 시뮬레이션

**데이터 소스**:
- 파일: `backend/services/tides_korea.py` (공식 조석표)
- 계산: 반일주기 모델 (12.4시간 사이클)

**물때 계산**:
```
formula: ((lunar_day + 6) % 15) if ((lunar_day + 6) % 15) != 0 else 15
예: 음력 4일 → (4+6)%15 = 10물 (사리/최대 조류)
```

---

### 2. 기상 데이터 (Weather)
**상태**: ✅ 완전 구현  
**API**: 기상청 (KMA) - 단기예보  
**호출**: `backend/services/kma_weather_service.py`

**기능**:
- 위경도 → 기상청 격자 좌표 자동 변환
- 시간별 예보 (기온, 날씨, 강수, 풍속, 풍향)
- 예보 범위: 오늘~3일 뒤
- 캐시: 30분

**API 설정**:
```
환경변수: KMA_SERVICE_KEY
설정파일: secret.toml (api.kma_service_key)
API: https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst
```

---

### 3. 해양 데이터 (Marine)
**상태**: ✅ 완전 구현  
**API**: 국립해양조사원 (KHOA)  
**호출**: `backend/services/khoa_marine_service.py`

**기능**:
- 실시간 수온, 파고 (최신 관측값)
- 시간별 수위, 수온, 조류
- 여러 API 조합 (최신 + 시계열)
- 캐시: 10분

**API 설정**:
```
환경변수: KHOA_SERVICE_KEY
설정파일: secret.toml (api.khoa_service_key)
API 엔드포인트:
  - twRecent: 최신 관측값
  - tideHourly: 시간별 수위
  - WaterTempHourly: 시간별 수온
  - CurrentHourly: 시간별 조류
```

---

## 🔄 실시간 데이터 로드 플로우

### 프론트엔드 (React)
```javascript
// 1. 날짜 변경
setSelectedDate(newDate) 
  → fetchHourlyData() 호출

// 2. 위치 변경
handleLocationChange(newLocation)
  → fetchHourlyData() 호출

// 3. 자동 새로고침 (오늘 날짜만)
useEffect(() => {
  const interval = setInterval(() => {
    if (today === selectedDate) {
      fetchHourlyData(false) // 30초마다
    }
  }, 60000)
})

// 4. API 호출
const data = await apiJson(
  `/api/tide/hourly?lat=${lat}&lon=${lon}&date=${date}`
)

// 5. 데이터 소스 확인
console.log(data.tideSource)      // 'official' | 'simulation'
console.log(data.weatherSource)   // 'api' | 'simulated'
console.log(data.marineSource)    // 'api' | 'simulated'
```

### 백엔드 (Flask)
```python
# 1. 음력 계산
lunar = Converter.Solar2Lunar(Solar(year, month, day))
tide_num = ((lunar.day + 6) % 15) if ... else 15

# 2. 조석 데이터 로드
official_tide = get_tide_table(region, month, day)
if official_tide:
    use official data  # 공식 조석표
else:
    calculate from lunar  # 시뮬레이션

# 3. 기상 데이터 API 호출
kma_weather = KmaWeatherService.get_hourly_weather(lat, lon, date)
if kma_weather:
    override simulated weather

# 4. 해양 데이터 API 호출
khoa_marine = KhoaMarineService.get_hourly_marine(lat, lon, date)
if khoa_marine:
    override simulated marine data

# 5. 응답 반환
return {
    'tideSource': 'official' or 'simulation',
    'weatherSource': 'api' or 'simulated',
    'marineSource': 'api' or 'simulated',
    'hourly': [시간별 데이터],
    ...
}
```

---

## 🚀 API 키 설정 방법

### 방법 1: 환경 변수 (Render/Vercel)
```bash
# Render 환경 설정
KMA_SERVICE_KEY=your_kma_key
KHOA_SERVICE_KEY=your_khoa_key
```

### 방법 2: secret.toml 파일 (로컬 개발)
```toml
[api]
kma_service_key = "your_kma_key"
khoa_service_key = "your_khoa_key"
```

### API 키 발급
- **KMA (기상청)**: https://www.data.go.kr/
- **KHOA (국립해양조사원)**: https://www.khoa.go.kr/

---

## 📱 프론트엔드 UI/UX

### 데이터 선택기
```
┌─────────────────────────────────┐
│ 📅 날짜: 2026-06-18            │ ← 변경 시 자동 로드
│ 📍 위치: 부산해운대 (35.1, 129.1) │ ← 변경 시 자동 로드
└─────────────────────────────────┘
```

### 데이터 상태 표시 (콘솔)
```
[TidePage] API Response Data:
  Tide Source: official
  Weather Source: api
  Marine Source: api
```

### 시간별 데이터 표
```
시간 | 수위 | 조류 | 수온 | 바람 | 날씨
────┼──────┼──────┼──────┼──────┼──────
00:00| 1.2m | 강  | 15℃ | 2.5m/s | 맑음
03:00| 2.5m | 약  | 14℃ | 1.2m/s | 구름
...  |      |     |     |        |
```

---

## 🔍 문제 해결

### API 응답이 없을 때
1. ✅ API 키 확인
   ```bash
   echo $KMA_SERVICE_KEY
   echo $KHOA_SERVICE_KEY
   ```

2. ✅ 로그 확인
   ```bash
   tail -f backend.log | grep -E "KMA|KHOA"
   ```

3. ✅ 캐시 제거
   - KMA 캐시: 30분
   - KHOA 캐시: 10분

4. ✅ Fallback 작동
   - API 실패 → 시뮬레이션 데이터 사용
   - 데이터 손실 없음

---

## 📊 데이터 정확도

| 항목 | 데이터 소스 | 정확도 | 업데이트 주기 |
|------|-----------|-------|-------------|
| 조석 | 공식 조석표 | ★★★★★ | 정적 |
| 물때 | 음력 계산 | ★★★★★ | 정적 |
| 기상 | KMA API | ★★★★☆ | 3시간 |
| 해양 | KHOA API | ★★★★☆ | 실시간 |

---

## 🎯 향후 개선 계획

- [ ] KHOA 조석 예보 API 직접 연동
- [ ] 더 많은 지역 조석표 추가
- [ ] 예측 정확도 향상 (기계학습)
- [ ] 오프라인 모드 지원
- [ ] 데이터 동기화 최적화

---

## 📚 참고 자료

- KMA API: https://www.data.go.kr/tcs/dss/selectApiDetailView.do?publicDataPk=15084693
- KHOA API: https://www.khoa.go.kr/api/
- 조석 정보: https://www.khoa.go.kr/koofs/nrt/
