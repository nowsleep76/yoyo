import { useEffect, useState, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { StorageUtils, SafeFetch } from '../utils/storage'
import './TidePage.css'

function TidePage({ location, onLocationChange }) {
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [hourlyData, setHourlyData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showLocationSelector, setShowLocationSelector] = useState(false)
  const [selectedRegion, setSelectedRegion] = useState(null)
  const [spots, setSpots] = useState([])
  // ✅ FIX: displayLocation 초기화를 lazy initializer에서 처리 (StorageUtils 사용)
  const [displayLocation, setDisplayLocation] = useState(() => {
    const saved = StorageUtils.getItem('selectedLocation')
    if (saved) {
      try {
        return JSON.parse(saved)
      } catch (e) {
        console.warn('저장된 위치 파싱 실패:', e)
      }
    }
    // 기본값으로 기본 좌표 반환 (location prop이 아직 available하지 않을 수 있음)
    return {
      latitude: 37.5665,
      longitude: 126.9780,
      name: '내 위치'
    }
  })
  const [activeTab, setActiveTab] = useState('tide')
  const [displayInterval, setDisplayInterval] = useState(1) // 1시간 또는 3시간

  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const dateInputRef = useRef(null)

  // ✅ FIX: 저장된 위치를 App에 한 번만 반영 (마운트 시에만, StorageUtils 사용)
  useEffect(() => {
    const saved = StorageUtils.getItem('selectedLocation')
    if (saved && onLocationChange) {
      try {
        const loc = JSON.parse(saved)
        onLocationChange(loc)
      } catch (err) {
        console.error('위치 로드 실패:', err)
      }
    }
  }, [])

  // ✅ FIX: 값 비교 기반 setState (참조 변경만으로는 업데이트 안 함)
  useEffect(() => {
    if (location?.latitude && location?.longitude) {
      setDisplayLocation(prev => {
        // 값이 실제로 다를 때만 업데이트
        if (prev?.latitude === location.latitude && prev?.longitude === location.longitude) {
          return prev // 변경 없음
        }
        return location
      })
    }
  }, [location])

  // 명소 데이터 로드
  useEffect(() => {
    const fetchSpots = async () => {
      try {
        const response = await fetch('/api/spots')
        if (response.ok) {
          const data = await response.json()
          setSpots(data || [])
        }
      } catch (err) {
        setSpots([
          { id: 1, name: '부산 해운대', region: '남해', latitude: 35.1595, longitude: 129.1603, fish_types: '우럭, 감성돔' },
          { id: 2, name: '울산 방어', region: '남해', latitude: 35.2872, longitude: 129.3719, fish_types: '방어, 우럭' },
          { id: 3, name: '경주 감포', region: '동해', latitude: 35.9996, longitude: 129.6112, fish_types: '우럭, 광어' },
          { id: 4, name: '제주 협재', region: '제주', latitude: 33.4171, longitude: 126.2335, fish_types: '부시리, 돌돔' },
          { id: 5, name: '전남 거문도', region: '남해', latitude: 34.1347, longitude: 127.3050, fish_types: '우럭, 광어' }
        ])
      }
    }
    fetchSpots()
  }, [])

  // 조위 데이터 페칭
  const fetchHourlyData = async (showLoading = true) => {
    if (!selectedDate || !displayLocation || !displayLocation.latitude) {
      return
    }

    try {
      if (showLoading) setLoading(true)
      setError(null)
      const dateStr = selectedDate.toISOString().split('T')[0]

      console.log(`[TidePage] Fetching data for: ${dateStr}, Location: (${displayLocation.latitude}, ${displayLocation.longitude})`)

      const response = await fetch(
        `/api/tide/hourly?lat=${displayLocation.latitude}&lon=${displayLocation.longitude}&date=${dateStr}`
      )

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: 데이터 로드 실패`)
      }

      const data = await response.json()

      // 데이터 검증 로깅 (받은 직후)
      console.log('[TidePage] API Response Data:')
      console.log('  Date:', data.date)
      console.log('  Lunar:', `${data.lunar?.month}/${data.lunar?.day}`)
      console.log('  Tide Number:', data.tideNumber)
      console.log('  Tide Source:', data.tideSource)
      console.log('  Marine Source:', data.marineSource)
      console.log('  Weather Source:', data.weatherSource)

      if (data && data.hourly) {
        setHourlyData(data)
        setError(null)
      } else {
        throw new Error('응답 데이터 형식이 올바르지 않습니다')
      }
    } catch (err) {
      console.error('[TidePage] 조위 데이터 로드 실패:', err)
      setError(`데이터를 불러올 수 없습니다: ${err.message}`)
      setHourlyData(null)
    } finally {
      if (showLoading) setLoading(false)
    }
  }

  // 날짜 또는 위치 변경 시 데이터 페칭
  useEffect(() => {
    fetchHourlyData(true)
  }, [selectedDate, displayLocation?.latitude, displayLocation?.longitude])

  // 매분 자동 새로고침 (실시간 데이터 업데이트)
  useEffect(() => {
    const refreshInterval = setInterval(() => {
      // 오늘 날짜인 경우에만 자동 새로고침
      const today = new Date().toISOString().split('T')[0]
      const selectedDateStr = selectedDate.toISOString().split('T')[0]

      if (today === selectedDateStr && !loading) {
        console.log('[TidePage] Auto-refresh (realtime update)...')
        fetchHourlyData(false) // 로딩 표시 없이 백그라운드에서 업데이트
      }
    }, 60000) // 60초마다

    return () => clearInterval(refreshInterval)
  }, [selectedDate, loading])

  // 위치 변경 처리 (StorageUtils 사용)
  const handleLocationChange = (newLocation) => {
    setDisplayLocation(newLocation)
    const saved = StorageUtils.setItem('selectedLocation', JSON.stringify(newLocation))
    if (!saved) {
      console.warn('위치 저장 실패 - 메모리에만 유지됩니다')
    }
    if (onLocationChange) {
      onLocationChange(newLocation)
    }
    setShowLocationSelector(false)
    setSelectedRegion(null)
  }

  // 지도 초기화
  useEffect(() => {
    if (!mapRef.current || !displayLocation || !displayLocation.latitude) return
    if (mapInstanceRef.current) return

    try {
      mapInstanceRef.current = L.map(mapRef.current).setView(
        [displayLocation.latitude, displayLocation.longitude],
        12
      )

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
      }).addTo(mapInstanceRef.current)

      L.circleMarker([displayLocation.latitude, displayLocation.longitude], {
        radius: 8,
        fillColor: '#0066cc',
        color: '#0066cc',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
      }).addTo(mapInstanceRef.current)
    } catch (err) {
      console.error('지도 초기화 실패:', err)
    }

    return () => {
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.remove()
        } catch (e) {
          console.warn('지도 제거 실패:', e)
        }
        mapInstanceRef.current = null
      }
    }
  }, [displayLocation?.latitude, displayLocation?.longitude])

  if (!displayLocation || !displayLocation.latitude) {
    return <div className="tide-page loading">위치 정보를 불러오는 중...</div>
  }

  if (error) {
    return (
      <div className="tide-page error">
        <div style={{ padding: '20px', textAlign: 'center', color: '#d32f2f' }}>
          <h2>⚠️ 오류 발생</h2>
          <p>{error}</p>
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: '10px',
              padding: '8px 16px',
              backgroundColor: '#1976d2',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            다시 시도
          </button>
        </div>
      </div>
    )
  }

  if (loading || !hourlyData) {
    return <div className="tide-page loading">날씨 데이터 로딩 중... ({displayLocation.name})</div>
  }

  const dateStr = selectedDate.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })

  // 백엔드에서 제공하는 음력 정보 사용 (더 정확함)
  const lunarDate = hourlyData?.lunar || { month: '-', day: '-' }

  // 천체 이벤트 맵
  const celestialMap = {}
  if (hourlyData?.celestialEvents) {
    hourlyData.celestialEvents.forEach(event => {
      if (!celestialMap[event.hour]) {
        celestialMap[event.hour] = []
      }
      celestialMap[event.hour].push(event)
    })
  }

  // 모든 만조/간조 데이터 통합 (시간순 정렬)
  const allTides = []
  if (hourlyData?.highTides) {
    hourlyData.highTides.forEach(tide => {
      // height가 없으면 기본값 사용
      allTides.push({ type: 'high', height: tide.height ?? 0, ...tide })
    })
  }
  if (hourlyData?.lowTides) {
    hourlyData.lowTides.forEach(tide => {
      // height가 없으면 기본값 사용
      allTides.push({ type: 'low', height: tide.height ?? 0, ...tide })
    })
  }

  // 시간순 정렬
  allTides.sort((a, b) => {
    const aTime = parseInt(a.time.split(':')[0]) * 60 + parseInt(a.time.split(':')[1])
    const bTime = parseInt(b.time.split(':')[0]) * 60 + parseInt(b.time.split(':')[1])
    return aTime - bTime
  })

  // DEBUG: allTides 순서 확인
  console.log('[TidePage] allTides 순서:', allTides.map(t => `${t.time} ${t.type === 'high' ? '만조' : '간조'}`).join(' → '))

  // 각 극값에 대해 직전 극값과의 수위 변화 계산
  allTides.forEach((tide, idx) => {
    if (idx > 0) {
      const prevTide = allTides[idx - 1]
      tide.heightChange = (tide.height ?? 0) - (prevTide.height ?? 0)
    } else {
      tide.heightChange = 0
    }
  })

  // 현재 시간대의 극값 정보만 반환 (간조 또는 만조 중 하나)
  const getTideSingleInfo = (hour, interval) => {
    if (allTides.length === 0) return null

    // 이 시간대에 속하는 극값 찾기
    const tideInHour = allTides.find(tide => {
      const tideHour = parseInt(tide.time.split(':')[0])
      if (interval === 1) {
        return tideHour === hour
      } else if (interval === 3) {
        return hour <= tideHour && tideHour < hour + 3
      }
      return false
    })

    if (!tideInHour) return null

    // 현재 극값의 인덱스 찾기
    const currentIdx = allTides.indexOf(tideInHour)

    // 직전 극값 찾기 (다른 타입)
    let prevTide = null
    if (currentIdx > 0) {
      prevTide = allTides[currentIdx - 1]
    } else {
      prevTide = allTides[allTides.length - 1]
    }

    // 수위 변화값 계산
    let diff = 0
    if (tideInHour.type === 'high') {
      // 만조: 직전 간조 대비 상승값
      diff = tideInHour.height - prevTide.height
    } else {
      // 간조: 직전 만조 대비 하락값
      diff = prevTide.height - tideInHour.height
    }

    return {
      type: tideInHour.type === 'high' ? 'high' : 'low',
      label: tideInHour.type === 'high' ? '만조' : '간조',
      time: tideInHour.time,
      height: tideInHour.height,
      diff: Math.abs(diff)
    }
  }

  return (
    <div className="tide-page">
      {/* 헤더 */}
      <div className="tide-header">
        <div className="header-content">
          <h1>{displayLocation.name}</h1>
          <button className="location-btn" onClick={() => setShowLocationSelector(true)}>
            📍 변경
          </button>
        </div>
      </div>

      {/* 위치 선택 모달 */}
      {showLocationSelector && (
        <div className="location-modal-overlay" onClick={() => {
          setShowLocationSelector(false)
          setSelectedRegion(null)
        }}>
          <div className="location-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>낚시 명소 선택</h2>
              <button className="close-btn" onClick={() => {
                setShowLocationSelector(false)
                setSelectedRegion(null)
              }}>✕</button>
            </div>

            {!selectedRegion ? (
              <div className="region-selector">
                <div className="region-title">지역 선택</div>
                <div className="region-buttons">
                  {['남해', '동해', '서해', '제주'].map((region) => (
                    <button
                      key={region}
                      className="region-btn"
                      onClick={() => setSelectedRegion(region)}
                    >
                      {region}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="spots-list">
                <button className="back-btn" onClick={() => setSelectedRegion(null)}>
                  ← 돌아가기
                </button>
                <div className="spots-title">{selectedRegion} 명소</div>
                <div className="spots-grid">
                  {spots.filter((s) => s.region === selectedRegion).map((spot) => (
                    <button
                      key={spot.id}
                      className="spot-btn"
                      onClick={() => {
                        const newLoc = {
                          latitude: spot.latitude,
                          longitude: spot.longitude,
                          name: spot.name
                        }
                        handleLocationChange(newLoc)
                      }}
                    >
                      <div className="spot-name">{spot.name}</div>
                      <div className="spot-species">{spot.fish_types}</div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 물때 정보 헤더 */}
      <div className="tide-info-header">
        <div className="header-info-line">
          <span className="date-info">{dateStr}</span>
          <span className="separator">/</span>
          <span className="lunar-info">음력 {lunarDate.month}월 {lunarDate.day}일</span>
          <span className="separator">/</span>
          <span className="tide-info">{hourlyData.tideNumber}물</span>
          <span className="separator">/</span>
          <span className="current-info">조류 {hourlyData.volume?.label || '중간'}</span>
          <button
            className="refresh-btn"
            onClick={() => fetchHourlyData(true)}
            title="실시간 데이터 새로고침"
            style={{ marginLeft: '10px', padding: '4px 8px', cursor: 'pointer' }}
          >
            🔄 새로고침
          </button>
          {hourlyData.tideSource === 'official' ? (
            <span className="data-source-badge official">공식 조석표</span>
          ) : (
            <span className="data-source-badge simulated">조석 예측치</span>
          )}
          {hourlyData.weatherSource === 'api' ? (
            <span className="data-source-badge official">기상청 실시간</span>
          ) : (
            <span className="data-source-badge simulated">기상 시뮬레이션</span>
          )}
          {hourlyData.marineSource === 'api' ? (
            <span className="data-source-badge official">KHOA 해양관측</span>
          ) : (
            <span className="data-source-badge simulated">해양 시뮬레이션</span>
          )}
        </div>
      </div>

      {/* 날짜 제어 & 탭 네비게이션 통합 */}
      <div className="date-tab-bar">
        <div className="date-control-bar">
          <div className="quick-date-buttons">
            <button
              onClick={() => setSelectedDate(new Date(selectedDate.getTime() - 86400000))}
              className="quick-date-btn"
              title="어제"
            >
              어제
            </button>
            <button
              onClick={() => setSelectedDate(new Date())}
              className={`quick-date-btn ${selectedDate.toDateString() === new Date().toDateString() ? 'active' : ''}`}
              title="오늘"
            >
              오늘
            </button>
            <button
              onClick={() => setSelectedDate(new Date(selectedDate.getTime() + 86400000))}
              className="quick-date-btn"
              title="내일"
            >
              내일
            </button>
          </div>

          <div className="nav-icon-buttons">
            <button
              onClick={() => setSelectedDate(new Date(selectedDate.getTime() - 86400000))}
              className="nav-icon-btn"
              title="이전날짜"
            >
              ◀◀
            </button>
            <button
              onClick={() => dateInputRef.current?.click()}
              className="nav-icon-btn calendar-btn"
              title="달력 선택"
            >
              📅
            </button>
            <input
              ref={dateInputRef}
              type="date"
              style={{ display: 'none' }}
              onChange={(e) => {
                if (e.target.value) {
                  setSelectedDate(new Date(e.target.value + 'T00:00:00'))
                }
              }}
              value={selectedDate.toISOString().split('T')[0]}
            />
            <button
              onClick={() => setSelectedDate(new Date(selectedDate.getTime() + 86400000))}
              className="nav-icon-btn"
              title="다음날짜"
            >
              ▶▶
            </button>
          </div>

          <div className="interval-buttons">
            <button
              className={`interval-btn ${displayInterval === 1 ? 'active' : ''}`}
              onClick={() => setDisplayInterval(1)}
              title="1시간 간격"
            >
              1시간
            </button>
            <button
              className={`interval-btn ${displayInterval === 3 ? 'active' : ''}`}
              onClick={() => setDisplayInterval(3)}
              title="3시간 간격"
            >
              3시간
            </button>
          </div>
        </div>

        <div className="tab-navigation">
          <button
            className={`tab-btn ${activeTab === 'tide' ? 'active' : ''}`}
            onClick={() => setActiveTab('tide')}
          >
            <i className="fas fa-water"></i> 물때
          </button>
          <button
            className={`tab-btn ${activeTab === 'wind' ? 'active' : ''}`}
            onClick={() => setActiveTab('wind')}
          >
            <i className="fas fa-wind"></i> 바람/파고
          </button>
        </div>
      </div>

      {/* 물때 탭 */}
      {activeTab === 'tide' && (
        <div className="tide-content-wrapper">
          {loading && <div className="loading">데이터 로드 중...</div>}
          {hourlyData && (
            <div className="hourly-table-container">
              <table className="hourly-table">
                <thead>
                  <tr>
                    <th>시간</th>
                    <th>수위(변화)</th>
                    <th>조류</th>
                    <th>바람</th>
                    <th>날씨</th>
                    <th>일출/일몰</th>
                    <th>만조/간조</th>
                  </tr>
                </thead>
                <tbody>
                  {hourlyData.hourly && hourlyData.hourly
                    .filter(item => displayInterval === 1 || item.hour % displayInterval === 0)
                    .map((item, idx) => {
                  // 원본 배열에서 이전 시간의 높이 찾기
                  const prevItem = hourlyData.hourly.find(h => h.hour === item.hour - 1)
                  const prevHeight = prevItem ? prevItem.height : item.height
                  const change = item.height - prevHeight
                  const changeSign = change > 0.01 ? '+' : change < -0.01 ? '-' : '±'
                  const changeClass = change > 0.01 ? 'increase' : change < -0.01 ? 'decrease' : 'flat'
                  const timeStr = String(item.hour).padStart(2, '0') + ':00'

                  // 일출/일몰 시간 표시 (문자열로 받음)
                  const sunriseTime = hourlyData.sunrise // "05:35" 형식
                  const sunsetTime = hourlyData.sunset // "19:39" 형식
                  const sunriseHour = parseInt(sunriseTime.split(':')[0])
                  const sunsetHour = parseInt(sunsetTime.split(':')[0])

                  // displayInterval에 따라 다른 기준으로 표시
                  let sunEvent = '-'
                  if (displayInterval === 1) {
                    // 1시간 간격: 정확한 시간만 표시
                    if (item.hour === sunriseHour) {
                      sunEvent = `🌅 ${sunriseTime}`
                    } else if (item.hour === sunsetHour) {
                      sunEvent = `🌇 ${sunsetTime}`
                    }
                  } else if (displayInterval === 3) {
                    // 3시간 간격: 근접한 시간에만 표시 (item.hour 이상 item.hour+3 미만)
                    if (item.hour <= sunriseHour && sunriseHour < item.hour + 3) {
                      sunEvent = `🌅 ${sunriseTime}`
                    } else if (item.hour <= sunsetHour && sunsetHour < item.hour + 3) {
                      sunEvent = `🌇 ${sunsetTime}`
                    }
                  }

                  // 시간대별 배경 그래디언션 (야간/주간)
                  const isNight = item.hour < sunriseHour || item.hour >= sunsetHour
                  const bgClass = isNight ? 'night' : 'day'

                  // 조류 세기 판정
                  const currentStrength = item.currentSpeed < 0.15 ? '약' : item.currentSpeed < 0.35 ? '중' : '강'

                  // 시간대의 극값 정보 (간조 또는 만조 중 하나)
                  const tideInfo = getTideSingleInfo(item.hour, displayInterval)

                  return (
                    <tr key={idx} className={bgClass}>
                      <td className="time-cell">{timeStr}</td>
                      <td className={`height-cell height-change ${changeClass}`}>
                        {item.height.toFixed(2)}m({changeSign}{Math.abs(change).toFixed(2)}m)
                      </td>
                      <td className="current-cell">
                        <div className="current-bar-container">
                          <div className="current-bar" style={{ width: `${(item.currentSpeed / Math.max(...hourlyData.hourly.map(h => h.currentSpeed))) * 100}%` }}></div>
                          <span className="current-value">{item.currentSpeed.toFixed(2)}m/s({currentStrength})</span>
                        </div>
                      </td>
                      <td className="wind-cell">
                        {item.windSpeed.toFixed(1)}m/s({item.windDir})
                      </td>
                      <td className="weather-cell">
                        <span className="weather-icon">{getWeatherIcon(item.weather)}</span>
                        <span className="temp-info">{Math.round(item.temp)}°</span>
                      </td>
                      <td className="sun-cell">
                        {sunEvent}
                      </td>
                      <td className={`tide-cell ${tideInfo ? (tideInfo.type === 'high' ? 'tide-up' : 'tide-down') : ''}`}>
                        {tideInfo ? (
                          <div style={{ fontSize: '0.9em', fontWeight: '500' }}>
                            <span style={{ color: tideInfo.type === 'high' ? '#0066cc' : '#cc0000' }}>
                              {tideInfo.label} {tideInfo.time}
                            </span>
                            <span style={{ marginLeft: '8px' }}>
                              ({tideInfo.type === 'high' ? '↑' : '↓'} {tideInfo.diff.toFixed(2)}m)
                            </span>
                          </div>
                        ) : (
                          '-'
                        )}
                      </td>
                    </tr>
                  )
                })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* 바람/파고 탭 */}
      {activeTab === 'wind' && hourlyData && (
        <div className="wind-content-wrapper">
          <div className="wind-table-wrapper">
            <table className="wind-table">
              <thead>
                <tr>
                  <th>시간</th>
                  <th>풍향</th>
                  <th>풍속</th>
                  <th>날씨</th>
                  <th>기온</th>
                  <th>파고</th>
                  <th>강수확률</th>
                </tr>
              </thead>
              <tbody>
                {hourlyData.hourly && hourlyData.hourly
                  .filter(item => displayInterval === 1 || item.hour % displayInterval === 0)
                  .map((item, idx) => {
                  const sunriseHour = parseInt(hourlyData.sunrise.split(':')[0])
                  const sunsetHour = parseInt(hourlyData.sunset.split(':')[0])
                  const isNight = item.hour < sunriseHour || item.hour >= sunsetHour
                  const bgClass = isNight ? 'night' : 'day'

                  return (
                    <tr key={idx} className={bgClass}>
                      <td className="time-cell">
                        <strong>{String(item.hour).padStart(2, '0')}:00</strong>
                      </td>
                      <td className="wind-dir-cell">
                        <div className="wind-direction">
                          <span className="arrow" style={{ transform: `rotate(${getWindDegree(item.windDir)}deg)` }}>↓</span>
                          <div className="dir-text">{item.windDir}</div>
                        </div>
                      </td>
                      <td className="wind-speed-cell">
                        <div className="direction-speed">{item.windDir} {item.windSpeed.toFixed(1)}m/s</div>
                        <div className="max">최대 {(item.windSpeed * 1.6).toFixed(1)}m/s</div>
                      </td>
                      <td className="weather-cell">
                        {getWeatherIcon(item.weather)}
                      </td>
                      <td className="temp-cell">
                        {Math.round(item.temp)}°
                      </td>
                      <td className="wave-cell">
                        <div className="wave-icon">🌊</div>
                        <div>{item.waveHeight}m</div>
                        <div className="period">{item.wavePeriod}s</div>
                      </td>
                      <td className="precipitation-cell">
                        <div className="precip-value">{item.precipitation || 0}%</div>
                        <div className="precip-bar" style={{ width: `${item.precipitation || 0}%`, maxWidth: '60px' }}></div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

function getWeatherIcon(weather) {
  const icons = {
    '맑음': '☀️',
    '구름': '☁️',
    '흐림': '🌧️',
    '비': '🌧️',
    '눈': '❄️'
  }
  return icons[weather] || '☀️'
}

function getWindDegree(direction) {
  const map = {
    '북': 0, '북북동': 22.5, '북동': 45, '동북동': 67.5,
    '동': 90, '동남동': 112.5, '남동': 135, '남남동': 157.5,
    '남': 180, '남남서': 202.5, '남서': 225, '서남서': 247.5,
    '서': 270, '서북서': 292.5, '북서': 315, '북북서': 337.5
  }
  return map[direction] || 0
}

export default TidePage
