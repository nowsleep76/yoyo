import { useEffect, useState, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import './TidePage.css'

function TidePage({ location, onLocationChange }) {
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [hourlyData, setHourlyData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [dateList, setDateList] = useState([])
  const [showLocationSelector, setShowLocationSelector] = useState(false)
  const [selectedRegion, setSelectedRegion] = useState(null)
  const [spots, setSpots] = useState([])
  const [displayLocation, setDisplayLocation] = useState(location)
  const [activeTab, setActiveTab] = useState('tide')

  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)

  // 위치 정보 로드
  useEffect(() => {
    const savedLocation = localStorage.getItem('selectedLocation')
    if (savedLocation) {
      try {
        const loc = JSON.parse(savedLocation)
        setDisplayLocation(loc)
        if (onLocationChange) {
          onLocationChange(loc)
        }
      } catch (err) {
        console.error('위치 로드 실패:', err)
        setDisplayLocation(location)
      }
    } else {
      setDisplayLocation(location)
    }
  }, [])

  useEffect(() => {
    if (location && location.latitude && location.longitude) {
      setDisplayLocation(location)
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

  // 날짜 목록 생성
  useEffect(() => {
    const dates = []
    for (let i = 0; i < 10; i++) {
      const date = new Date()
      date.setDate(date.getDate() + i)
      dates.push(date)
    }
    setDateList(dates)
  }, [])

  // 조위 데이터 페칭
  useEffect(() => {
    if (!selectedDate || !displayLocation || !displayLocation.latitude) {
      return
    }

    const fetchHourlyData = async () => {
      try {
        setLoading(true)
        const dateStr = selectedDate.toISOString().split('T')[0]

        const response = await fetch(
          `/api/tide/hourly?lat=${displayLocation.latitude}&lon=${displayLocation.longitude}&date=${dateStr}`
        )

        if (!response.ok) {
          throw new Error('데이터 로드 실패')
        }

        const data = await response.json()
        if (data && data.hourly) {
          setHourlyData(data)
        }
      } catch (err) {
        console.error('데이터 로드 실패:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchHourlyData()
  }, [selectedDate, displayLocation])

  // 위치 변경 처리
  const handleLocationChange = (newLocation) => {
    setDisplayLocation(newLocation)
    localStorage.setItem('selectedLocation', JSON.stringify(newLocation))
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
  }, [displayLocation])

  if (!displayLocation || !displayLocation.latitude) {
    return <div className="tide-page loading">위치 정보를 불러오는 중...</div>
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

  // 만조/간조 맵
  const tideMap = {}
  if (hourlyData?.highTides) {
    hourlyData.highTides.forEach(tide => {
      const [h] = (tide.time || '').split(':').map(Number)
      if (!isNaN(h)) {
        tideMap[h] = { type: 'high', ...tide }
      }
    })
  }
  if (hourlyData?.lowTides) {
    hourlyData.lowTides.forEach(tide => {
      const [h] = (tide.time || '').split(':').map(Number)
      if (!isNaN(h)) {
        tideMap[h] = { type: 'low', ...tide }
      }
    })
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
        <div className="info-item">
          <span className="info-label">날짜</span>
          <span className="info-value">{dateStr}</span>
        </div>
        <div className="info-item">
          <span className="info-label">음력</span>
          <span className="info-value">{lunarDate.month}월 {lunarDate.day}일</span>
        </div>
        <div className="info-item">
          <span className="info-label">물때</span>
          <span className="info-value">{hourlyData.tideNumber}물</span>
        </div>
        <div className="info-item">
          <span className="info-label">조류</span>
          <span className="info-value">{hourlyData.volume?.label || '중간'}</span>
        </div>
      </div>

      {/* 날짜 선택 & 탭 네비게이션 */}
      <div className="date-tab-bar">
        <div className="date-selector">
          <button
            disabled={selectedDate.toDateString() === new Date(selectedDate.getTime() - 86400000).toDateString()}
            onClick={() => setSelectedDate(new Date(selectedDate.getTime() - 86400000))}
            className="date-nav-btn"
            title="어제"
          >
            ← 어제
          </button>
          <button
            onClick={() => setSelectedDate(new Date())}
            className={`date-nav-btn ${selectedDate.toDateString() === new Date().toDateString() ? 'active' : ''}`}
            title="오늘"
          >
            오늘
          </button>
          <button
            onClick={() => setSelectedDate(new Date(selectedDate.getTime() + 86400000))}
            className="date-nav-btn"
            title="내일"
          >
            내일 →
          </button>
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
          {/* 1시간 단위 테이블 */}
          <div className="hourly-table-container">
            <table className="hourly-table">
              <thead>
                <tr>
                  <th>시간</th>
                  <th>수위</th>
                  <th>변화</th>
                  <th>만/간 대비</th>
                  <th>조류</th>
                  <th>바람</th>
                  <th>파고</th>
                  <th>날씨</th>
                  <th>천체</th>
                  <th>만조/간조</th>
                </tr>
              </thead>
              <tbody>
                {hourlyData.hourly && hourlyData.hourly.map((item, idx) => {
                  const prevHeight = idx > 0 ? hourlyData.hourly[idx - 1].height : item.height
                  const change = item.height - prevHeight
                  const changeIcon = change > 0.01 ? '↑' : change < -0.01 ? '↓' : '→'
                  const timeStr = String(idx).padStart(2, '0') + ':00'
                  const celestialEvents = celestialMap[idx] || []
                  const tideInfo = tideMap[idx]

                  // 간조/만조 대비 변화 계산
                  const lowTide = Math.min(...hourlyData.hourly.map(h => h.height))
                  const highTide = Math.max(...hourlyData.hourly.map(h => h.height))
                  const tideRange = highTide - lowTide
                  const tidePercent = tideRange > 0 ? Math.round(((item.height - lowTide) / tideRange) * 100) : 50

                  return (
                    <tr key={idx}>
                      <td className="time-cell">{timeStr}</td>
                      <td className="height-cell">{item.height.toFixed(2)}m</td>
                      <td className="change-cell">
                        <span className={`change-badge ${change > 0 ? 'up' : change < 0 ? 'down' : 'flat'}`}>
                          {changeIcon}{Math.abs(change).toFixed(2)}
                        </span>
                      </td>
                      <td className="tide-range-cell">
                        <div className="tide-bar-container">
                          <div className="tide-bar" style={{ width: `${tidePercent}%` }}></div>
                          <span className="tide-percent">{tidePercent}%</span>
                        </div>
                      </td>
                      <td className="current-cell">
                        <div className="current-bar-container">
                          <div className="current-bar" style={{ width: `${(item.currentSpeed / Math.max(...hourlyData.hourly.map(h => h.currentSpeed))) * 100}%` }}></div>
                          <span className="current-value">{item.currentSpeed.toFixed(2)}</span>
                        </div>
                      </td>
                      <td className="wind-cell">
                        <span className="wind-value">{item.windSpeed.toFixed(1)}m/s</span>
                      </td>
                      <td className="wave-cell">
                        <span className="wave-value">{item.waveHeight.toFixed(1)}m</span>
                      </td>
                      <td className="weather-cell">
                        <span className="weather-icon">{getWeatherIcon(item.weather)}</span>
                        <span className="temp-info">{Math.round(item.temp)}°</span>
                      </td>
                      <td className="celestial-cell">
                        {celestialEvents.map((event, eidx) => (
                          <span key={eidx} className="event-badge">
                            {event.type === 'sunrise' && '🌅'}
                            {event.type === 'sunset' && '🌇'}
                            {event.type === 'moonrise' && '🌙'}
                            {event.type === 'moonset' && '🌙'}
                          </span>
                        ))}
                      </td>
                      <td className="tide-cell">
                        {tideInfo && (
                          <span className={`tide-badge ${tideInfo.type}`}>
                            {tideInfo.type === 'high' ? '▲' : '▼'}{tideInfo.height.toFixed(2)}m
                          </span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
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
                </tr>
              </thead>
              <tbody>
                {hourlyData.hourly && hourlyData.hourly.map((item, idx) => (
                  <tr key={idx}>
                    <td className="time-cell">
                      <strong>{String(idx).padStart(2, '0')}시</strong>
                    </td>
                    <td className="wind-dir-cell">
                      <div className="wind-direction">
                        <span className="arrow" style={{ transform: `rotate(${getWindDegree(item.windDir)}deg)` }}>↓</span>
                        <div className="dir-text">{item.windDir}</div>
                      </div>
                    </td>
                    <td className="wind-speed-cell">
                      <div className="current">{item.windSpeed.toFixed(1)}m/s</div>
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
                  </tr>
                ))}
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
