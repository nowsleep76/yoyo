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
  const [activeTab, setActiveTab] = useState('tide')
  const [displayLocation, setDisplayLocation] = useState(location)

  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)

  // 위치 정보 로드 (localStorage에서)
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

  // 위치가 변경되면 업데이트
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
        console.error('명소 로드 실패:', err)
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
        } else {
          setHourlyData(generateTestData(selectedDate))
        }
      } catch (err) {
        console.error('데이터 로드 실패:', err)
        setHourlyData(generateTestData(selectedDate))
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

  if (!hourlyData && loading) {
    return <div className="tide-page loading">로딩 중...</div>
  }

  if (!displayLocation || !displayLocation.latitude) {
    return <div className="tide-page loading">위치 정보를 불러오는 중...</div>
  }

  const dateStr = selectedDate.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })

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

      {/* 탭 네비게이션 */}
      <div className="tab-navigation">
        <button
          className={`tab-btn ${activeTab === 'tide' ? 'active' : ''}`}
          onClick={() => setActiveTab('tide')}
        >
          물때
        </button>
        <button
          className={`tab-btn ${activeTab === 'wind' ? 'active' : ''}`}
          onClick={() => setActiveTab('wind')}
        >
          바람/파고
        </button>
      </div>

      {/* 날짜 선택 */}
      <div className="date-selector">
        <div className="date-info">{dateStr}</div>
        <div className="date-buttons">
          <button
            disabled={selectedDate.toDateString() === new Date(selectedDate.getTime() - 86400000).toDateString()}
            onClick={() => setSelectedDate(new Date(selectedDate.getTime() - 86400000))}
          >
            ← 어제
          </button>
          <button
            onClick={() => setSelectedDate(new Date())}
            className={selectedDate.toDateString() === new Date().toDateString() ? 'active' : ''}
          >
            오늘
          </button>
          <button
            onClick={() => setSelectedDate(new Date(selectedDate.getTime() + 86400000))}
          >
            내일 →
          </button>
        </div>
      </div>

      {/* 물때 탭 */}
      {activeTab === 'tide' && hourlyData && (
        <div className="tide-content">
          <div className="tide-wrapper">
            {/* 왼쪽: 시간축 */}
            <div className="tide-time-axis">
              {[0, 3, 6, 9, 12, 15, 18, 21, 24].map((hour) => (
                <div key={hour} className="tide-hour">
                  {String(hour).padStart(2, '0')}:00
                </div>
              ))}
            </div>

            {/* 중앙: 타임라인 */}
            <div className="tide-timeline">
              {/* 만조 마커 */}
              {hourlyData.highTides && hourlyData.highTides.map((tide, idx) => {
                const [h, m] = tide.time.split(':').map(Number)
                const percent = ((h * 60 + m) / 1440) * 100
                return (
                  <div key={`high-${idx}`} className="tide-marker high" style={{ top: `${percent}%` }}>
                    <div className="marker-box">
                      <div className="marker-title">만조 {tide.time}</div>
                      <div className="marker-value">({tide.height}m) ▲ {tide.change}</div>
                    </div>
                  </div>
                )
              })}

              {/* 간조 마커 */}
              {hourlyData.lowTides && hourlyData.lowTides.map((tide, idx) => {
                const [h, m] = tide.time.split(':').map(Number)
                const percent = ((h * 60 + m) / 1440) * 100
                return (
                  <div key={`low-${idx}`} className="tide-marker low" style={{ top: `${percent}%` }}>
                    <div className="marker-box">
                      <div className="marker-title">간조 {tide.time}</div>
                      <div className="marker-value">({tide.height}m) ▼ {Math.abs(tide.change)}</div>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* 오른쪽: 시간별 날씨 */}
            <div className="tide-weather">
              {hourlyData.hourly && hourlyData.hourly.map((item, idx) => (
                <div key={idx} className="weather-cell">
                  <div className="weather-hour">{String(idx).padStart(2, '0')}</div>
                  <div className="weather-icon">{getWeatherIcon(item.weather)}</div>
                  <div className="weather-temp">{Math.round(item.temp)}°</div>
                  <div className="weather-wind">{item.windSpeed.toFixed(1)}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 바람/파고 탭 */}
      {activeTab === 'wind' && hourlyData && (
        <div className="wind-content">
          <div className="wind-table-wrapper">
            <table className="wind-table">
              <thead>
                <tr>
                  <th>시간</th>
                  <th>풍향</th>
                  <th>풍속</th>
                  <th>날씨</th>
                  <th>기온</th>
                  <th>파향/파고/주기</th>
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

      {/* 지도 */}
      <div className="map-section">
        <div ref={mapRef} className="tide-map"></div>
      </div>
    </div>
  )
}

// 테스트 데이터 생성
function generateTestData(date) {
  const hourly = []

  for (let h = 0; h < 24; h++) {
    const sine = Math.sin((h / 24) * Math.PI * 2)
    const cosine = Math.cos((h / 24) * Math.PI * 2)
    const height = 1.2 + sine * 0.8

    hourly.push({
      hour: h,
      height: parseFloat(height.toFixed(2)),
      weather: h < 6 ? '맑음' : h < 12 ? '구름' : h < 18 ? '맑음' : '구름',
      temp: 15 + sine * 6,
      windSpeed: 2.5 + cosine * 2.5,
      windDir: getWindDirectionFromDegree(h * 15),
      waterTemp: 18,
      waveHeight: (0.4 + Math.abs(cosine) * 0.5).toFixed(1),
      wavePeriod: 3
    })
  }

  const highTides = [
    { time: '05:30', height: 2.1, change: 520 },
    { time: '17:50', height: 2.0, change: 510 }
  ]

  const lowTides = [
    { time: '11:10', height: 0.2, change: 510 },
    { time: '23:40', height: 0.3, change: 500 }
  ]

  return { hourly, highTides, lowTides }
}

function getWindDirectionFromDegree(degree) {
  const directions = ['북', '북북동', '북동', '동북동', '동', '동남동', '남동', '남남동',
                      '남', '남남서', '남서', '서남서', '서', '서북서', '북서', '북북서']
  const idx = Math.round((degree % 360) / 22.5) % 16
  return directions[idx]
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

export default TidePage
