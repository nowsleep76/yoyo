# KHOA 해양관측 API 설정 가이드

## 🌊 현재 상태

✅ **백엔드 구현**: 완료
- KHOA 시계열 데이터 조회 로직 추가됨
- 시간별 수위, 수온, 조류 데이터 지원
- Tide Service에 통합 완료

❌ **API 키**: 미설정
- `.env` 파일에 `KHOA_SERVICE_KEY=` (비어있음)
- KHOA API 호출 불가능

---

## 📋 KHOA API 키 신청 절차

### Step 1: 공공데이터포털 접속
1. https://www.data.go.kr 접속
2. 로그인 (회원가입 필요시 진행)

### Step 2: API 검색
**검색어**: `국립해양조사원 해양관측`

또는 직접 링크:
- https://www.data.go.kr/data/15038980/openapi.do (조위 시계열)
- https://www.data.go.kr/data/15038992/openapi.do (수온 시계열)
- https://www.data.go.kr/data/15038999/openapi.do (해류 시계열)

### Step 3: API 신청
각 API별로:
1. **"활용신청"** 클릭
2. **용도**: `낚시 정보 앱 개발 (개인)`
3. **승인**: 자동승인 (약 1시간)

### Step 4: 인증키 복사
- 마이페이지 → **개발자 정보** → **인증키**
- 공개키(serviceKey) 복사

### Step 5: .env 파일 설정
```bash
# /fishing-app/backend/.env

KMA_SERVICE_KEY=8d2753e1897e4caa6fafd7a1fc79a936e66a4ab9d98e1473c04cdf7cf2500911
KHOA_SERVICE_KEY=YOUR_KHOA_API_KEY_HERE  # ← 여기에 붙여넣기
FISHING_INDEX_API_KEY=8d2753e1897e4caa6fafd7a1fc79a936e66a4ab9d98e1473c04cdf7cf2500911
```

### Step 6: 백엔드 재시작
```bash
# 터미널에서
cd fishing-app/backend
pkill -f "python app.py"  # 기존 프로세스 종료
python app.py  # 재시작
```

---

## 🔍 API 신청 후 확인

### 방법 1: 실시간 데이터 확인
앱에서 **오늘 날짜**의 물때 탭을 열면:
```
[데이터 소스 배지]
✓ 공식 조석표 (조석표 데이터)
✓ 기상청 실시간 (KMA 날씨)
✓ KHOA 해양관측 (시간별 수위/수온/조류) ← 이 배지가 나타남
```

### 방법 2: API 응답 확인
```bash
curl "http://localhost:8000/api/tide/hourly?lat=35.1595&lon=129.1603&date=2026-06-12" | python -m json.tool | grep -A 5 "marineSource"
```

응답에서 `"marineSource": "api"` 가 나타나면 성공

### 방법 3: 백엔드 로그
```
tail -f /d/DEV/fishing-app/backend/backend.log | grep KHOA
```
- 정상: 로그 없음 (성공적으로 호출)
- 에러: `KHOA API 오류: ...` 메시지 출력

---

## 📊 API 신청 후 데이터 변화

### 오늘 날짜 (2026-06-12)

| 항목 | 신청 전 | 신청 후 |
|------|--------|--------|
| 시간별 수위 | 시뮬레이션 | KHOA 실측값 |
| 수온 | 고정값 | 시간별 실측값 |
| 조류 강도 | 시뮬레이션 | 실측 조류 속도 |
| 기상청 데이터 | 시뮬레이션 | 실시간 예보 |
| Data Source | `marine: simulated` | `marine: api` |

### 과거/미래 날짜 (2026-06-11, 2026-06-15)

| 항목 | 현재 | 개선 예정 |
|------|------|---------|
| 시간별 수위 | 시뮬레이션 | KMA 기후 API 추가 시 개선 |
| 수온 | 시뮬레이션 | KMA 기후 API 추가 시 개선 |
| 조류 강도 | 시뮬레이션 | 시뮬레이션 |

---

## 🎯 구현 상세 정보

### KHOA API 엔드포인트

```
1. 조위 시계열 (수위)
   URL: https://apis.data.go.kr/1192136/tideHourly
   필드: ObsCode, Date, Time → Height(수위)

2. 수온 시계열
   URL: https://apis.data.go.kr/1192136/WaterTempHourly
   필드: ObsCode, Date, Time → Temperature(수온)

3. 해류 시계열 (조류)
   URL: https://apis.data.go.kr/1192136/CurrentHourly
   필드: ObsCode, Date, Time → Velocity(조류속도)
```

### 백엔드 통합 코드

**파일**: `services/khoa_marine_service.py`

```python
# 시간별 데이터 조회
khoa_marine = KhoaMarineService.get_hourly_marine(lat, lon, target_date)

# 반환 구조
{
    'hourly': {
        0: {'height': 2.15, 'waterTemp': 18.5, 'currentSpeed': 0.25},  # 0시
        1: {'height': 2.18, 'waterTemp': 18.4, 'currentSpeed': 0.28},  # 1시
        ...
        23: {'height': 2.12, 'waterTemp': 18.6, 'currentSpeed': 0.22}  # 23시
    },
    'latestData': {
        'waterTemp': 18.7,  # 최신 실시간값
        'waveHeight': 0.8
    }
}
```

**파일**: `services/tide_service.py`

```python
# Tide Service에서 KHOA 데이터 병합
if khoa_marine and 'hourly' in khoa_marine:
    khoa_hourly = khoa_marine['hourly'][hour]
    
    # 시뮬레이션값 대체
    if khoa_hourly.get('height'):
        height = khoa_hourly['height']  # 수위
    if khoa_hourly.get('waterTemp'):
        water_temp = khoa_hourly['waterTemp']  # 수온
    if khoa_hourly.get('currentSpeed'):
        current_speed = khoa_hourly['currentSpeed']  # 조류
```

---

## 🐛 트러블슈팅

### Q: API 신청했는데 작동이 안 됨

**A**: 다음을 확인하세요:

1. **API 키 복사 확인**
   ```bash
   cat /d/DEV/fishing-app/backend/.env | grep KHOA
   # 결과: KHOA_SERVICE_KEY=xxx...
   ```

2. **백엔드 재시작 확인**
   ```bash
   ps aux | grep "python app.py"
   # Flask가 실행 중인지 확인
   ```

3. **로그 확인**
   ```bash
   curl -s "http://localhost:8000/api/tide/hourly?lat=35.1595&lon=129.1603&date=2026-06-12" | python -m json.tool | grep marineSource
   # "marineSource": "api" 인지 확인
   ```

### Q: KHOA API가 항상 null을 반환함

**A**: 다음 가능성이 있습니다:

1. **API 상태 확인**: KHOA 공공데이터포털에서 API 상태 확인
2. **관측소 부재**: 요청 위치에 가까운 관측소가 없을 수 있음
3. **날짜 범위**: KHOA는 실시간 데이터만 제공 (오늘 데이터만)

### Q: 과거 날짜도 KHOA 데이터를 받을 수 있나?

**A**: 현재는 **불가능**합니다:
- KHOA API: 실시간 데이터만 제공
- 과거 데이터: KMA 기후 API로 보완 예정 (별도 구현)

---

## 📅 다음 단계

### Phase 2: KMA 기후 데이터 추가 (선택사항)
- 과거/미래 날짜의 평균 기후값 조회
- 소요 시간: 3시간
- 우선순위: 낮음 (현재 시뮬레이션으로 충분)

### Phase 3: 사용자 지정 관측소 선택 (미래)
- UI에서 가장 가까운 관측소 선택 가능
- 정확도 향상

---

## 📞 문의

KHOA API 신청 과정에서 문제가 생기면:
1. data.go.kr 고객센터: 1544-6665
2. KHOA 공식 사이트: https://www.khoa.go.kr

---

**상태**: ✅ 백엔드 완성, 대기: KHOA API 키 설정
