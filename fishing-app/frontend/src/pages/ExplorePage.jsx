import { useState, useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import './ExplorePage.css'

function ExplorePage({ location, onLocationChange }) {
  const [activeTab, setActiveTab] = useState('records') // 'records' or 'plan'
  const [allCatches, setAllCatches] = useState([])
  const [selectedCatches, setSelectedCatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filterType, setFilterType] = useState('latest')
  const [selectedLocation, setSelectedLocation] = useState(null)
  const [nearbyLoading, setNearbyLoading] = useState(false)
  const [weatherData, setWeatherData] = useState({})

  // 출조 계획 탭 상태
  const [planDate, setPlanDate] = useState(new Date().toISOString().split('T')[0])
  const [planSpecies, setPlanSpecies] = useState('')
  const [planResults, setPlanResults] = useState([])
  const [planLoading, setPlanLoading] = useState(false)

  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const markersRef = useRef([])
  const circleRef = useRef(null)

  // 공개 기록 로드
  useEffect(() => {
    const fetchCatches = async () => {
      try {
        setLoading(true)
        const response = await fetch(`/api/catches/feed?sort=${filterType}`)
        if (response.ok) {
          const data = await response.json()
          // is_public인 기록만 필터링
          const publicCatches = data.filter(c => c.is_public)
          setAllCatches(publicCatches)
          setError(null)
        }
      } catch (err) {
        setError('조과 정보를 불러올 수 없습니다')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchCatches()
  }, [filterType])

  // Haversine 거리 계산
  const haversineDistance = (lat1, lng1, lat2, lng2) => {
    const R = 6371
    const dLat = (lat2 - lat1) * Math.PI / 180
    const dLng = (lng2 - lng1) * Math.PI / 180
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2)
    const c = 2 * Math.asin(Math.sqrt(a))
    return R * c
  }

  // 지도 클릭 이벤트 - 주변 10km 기록 조회 + 위치 변경
  const handleMapClick = async (e) => {
    const clickedLat = e.latlng.lat
    const clickedLng = e.latlng.lng

    // App 전체에 위치 변경 알림
    if (onLocationChange) {
      onLocationChange({
        latitude: clickedLat,
        longitude: clickedLng,
        name: `클릭 위치`
      })
    }

    setSelectedLocation({ lat: clickedLat, lng: clickedLng })
    setNearbyLoading(true)

    try {
      const response = await fetch(
        `/api/catches/nearby?lat=${clickedLat}&lng=${clickedLng}&distance=10&sort=${filterType}`
      )
      if (response.ok) {
        const data = await response.json()
        setSelectedCatches(data)
      }
    } catch (err) {
      console.error('주변 기록 조회 실패:', err)
    } finally {
      setNearbyLoading(false)
    }

    // 기존 원 제거
    if (circleRef.current) {
      circleRef.current.remove()
    }

    // 10km 원 표시
    circleRef.current = L.circle(
      [clickedLat, clickedLng],
      {
        color: '#3b82f6',
        fillColor: '#3b82f6',
        fillOpacity: 0.1,
        radius: 10000,
        weight: 2,
        dashArray: '5, 5'
      }
    ).addTo(mapInstanceRef.current)

    // 지도 중심 이동
    mapInstanceRef.current.setView([clickedLat, clickedLng], 12)
  }

  // 출조 계획 검색
  const handlePlanSearch = async () => {
    if (!planDate || !planSpecies.trim()) {
      alert('날짜와 어종을 입력해주세요')
      return
    }

    setPlanLoading(true)
    try {
      const response = await fetch(
        `/api/catches/nearby?lat=${location.latitude}&lng=${location.longitude}&distance=100&date=${planDate}&species=${encodeURIComponent(planSpecies)}`
      )
      if (response.ok) {
        const data = await response.json()
        // 거리순 정렬
        const sorted = [...data].sort((a, b) => (a.distance_km || 0) - (b.distance_km || 0))
        setPlanResults(sorted)
      }
    } catch (err) {
      console.error('출조 계획 조회 실패:', err)
    } finally {
      setPlanLoading(false)
    }
  }

  // 지도 초기화
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return

    const lat = location?.latitude || 37.5665
    const lng = location?.longitude || 126.9780

    mapInstanceRef.current = L.map(mapRef.current).setView(
      [lat, lng],
      11
    )

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19
    }).addTo(mapInstanceRef.current)

    // 지도 클릭 이벤트
    mapInstanceRef.current.on('click', handleMapClick)

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.off('click', handleMapClick)
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [])

  // 탭 변경시 주변 기록 다시 조회 (거리순 정렬)
  useEffect(() => {
    if (!selectedLocation) return

    const fetchNearby = async () => {
      setNearbyLoading(true)
      try {
        const response = await fetch(
          `/api/catches/nearby?lat=${selectedLocation.lat}&lng=${selectedLocation.lng}&distance=10&sort=${filterType}`
        )
        if (response.ok) {
          const data = await response.json()
          // 거리순 정렬 (가까운 순)
          const sorted = [...data].sort((a, b) => (a.distance_km || 0) - (b.distance_km || 0))
          setSelectedCatches(sorted)
        }
      } catch (err) {
        console.error('주변 기록 조회 실패:', err)
      } finally {
        setNearbyLoading(false)
      }
    }

    fetchNearby()
  }, [filterType, selectedLocation])

  // 마커 업데이트
  useEffect(() => {
    if (!mapInstanceRef.current) return

    // 기존 마커 제거
    markersRef.current.forEach(marker => {
      if (marker && marker.remove) {
        marker.remove()
      }
    })
    markersRef.current = []

    // 새 마커 추가
    allCatches.forEach(catchRecord => {
      if (catchRecord.location_lat && catchRecord.location_lng) {
        const catchDate = new Date(catchRecord.caught_at)
        const dateStr = catchDate.toLocaleDateString('ko-KR', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit'
        })

        const popupHTML = `
          <div style="font-family: 'Noto Sans KR', Arial, sans-serif; padding: 10px; font-size: 12px;">
            <strong style="display: block; margin-bottom: 6px; color: #0066cc; font-size: 13px;">${catchRecord.species || '미분류'} ${catchRecord.size_cm || '-'}cm</strong>
            <div style="border-top: 1px solid #e0e0e0; padding-top: 6px; margin-bottom: 6px;">
              <small style="display: block;">🌡️ 수온: ${catchRecord.water_temp || '-'}°C</small>
              <small style="display: block;">📊 수심: ${catchRecord.depth_m ? catchRecord.depth_m + 'm' : '-'}</small>
              <small style="display: block;">💨 바람: ${catchRecord.wind_speed ? catchRecord.wind_speed.toFixed(1) + 'm/s' : (catchRecord.weather_condition || '-')}</small>
              <small style="display: block;">🌊 조류: ${catchRecord.tide_info || '-'}</small>
              <small style="display: block;">⚖️ 무게: ${catchRecord.weight_g || '-'}g</small>
            </div>
            <small style="display: block; color: #666;">👤 ${catchRecord.user_id || '익명'}</small>
            <small style="display: block; color: #999; margin-top: 4px;">📅 ${dateStr}</small>
          </div>
        `

        const marker = L.circleMarker(
          [catchRecord.location_lat, catchRecord.location_lng],
          {
            radius: 8,
            fillColor: '#ff6b35',
            color: '#ff6b35',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
          }
        )
          .bindPopup(popupHTML)
          .addTo(mapInstanceRef.current)

        markersRef.current.push(marker)
      }
    })
  }, [allCatches])

  return (
    <div className="explore-page">
      <div className="explore-header">
        <h1>탐색</h1>
        <p className="subtitle">최근 조과 정보</p>
      </div>

      {/* 탭 선택 */}
      <div className="explore-tabs">
        <button
          className={`explore-tab ${activeTab === 'records' ? 'active' : ''}`}
          onClick={() => setActiveTab('records')}
        >
          <i className="fas fa-list"></i>
          기록
        </button>
        <button
          className={`explore-tab ${activeTab === 'plan' ? 'active' : ''}`}
          onClick={() => setActiveTab('plan')}
        >
          <i className="fas fa-calendar-alt"></i>
          출조 계획
        </button>
      </div>

      {/* 기록 탭 */}
      {activeTab === 'records' && (
      <div className="explore-container">
        <div className="explore-map-section">
          <div
            ref={mapRef}
            className="explore-map"
            style={{ height: '400px', borderRadius: '8px', marginBottom: '15px' }}
          ></div>

          <div className="filter-tabs">
            <button
              className={`filter-tab ${filterType === 'latest' ? 'active' : ''}`}
              onClick={() => setFilterType('latest')}
            >
              <i className="fas fa-clock"></i>
              최신순
            </button>
            <button
              className={`filter-tab ${filterType === 'views' ? 'active' : ''}`}
              onClick={() => setFilterType('views')}
            >
              <i className="fas fa-eye"></i>
              조회수
            </button>
            <button
              className={`filter-tab ${filterType === 'species' ? 'active' : ''}`}
              onClick={() => setFilterType('species')}
            >
              <i className="fas fa-fish"></i>
              어종별
            </button>
          </div>
        </div>

        <div className="explore-results-section">
          {loading && <div className="loading-message">로딩 중...</div>}
          {error && <div className="error-message">{error}</div>}

          {!loading && allCatches.length === 0 && (
            <div className="empty-message">
              <i className="fas fa-inbox"></i>
              <p>공개 조과 기록이 없습니다</p>
            </div>
          )}

          {!loading && allCatches.length > 0 && selectedCatches.length === 0 && !selectedLocation && (
            <div className="empty-message">
              <i className="fas fa-map-marker-alt"></i>
              <p>지도에서 위치를 클릭하세요</p>
            </div>
          )}

          {!loading && selectedLocation && selectedCatches.length === 0 && !nearbyLoading && (
            <div className="empty-message">
              <i className="fas fa-inbox"></i>
              <p>이 위치에서 10km 이내 조과 기록이 없습니다</p>
            </div>
          )}

          {nearbyLoading && (
            <div className="loading-message">주변 기록을 불러오는 중...</div>
          )}

          {!loading && selectedCatches.length > 0 && (
            <>
              <div className="location-header">
                <h3>📍 {selectedLocation.lat.toFixed(4)}, {selectedLocation.lng.toFixed(4)}</h3>
                <p className="record-count">10km 이내 {selectedCatches.length}개의 공개 기록</p>
              </div>

              <div className="catch-results-table-wrapper">
                <table className="catch-results-table">
                  <thead>
                    <tr>
                      <th>어종</th>
                      <th>크기</th>
                      <th>무게</th>
                      <th>수온</th>
                      <th>수심</th>
                      <th>바람</th>
                      <th>조류</th>
                      <th>거리</th>
                      <th>사용자</th>
                      <th>날짜</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedCatches.map((item) => (
                      <tr key={item.id}>
                        <td className="species-cell"><strong>{item.species}</strong></td>
                        <td>{item.size_cm ? `${item.size_cm}cm` : '-'}</td>
                        <td>{item.weight_g ? `${item.weight_g}g` : '-'}</td>
                        <td>{item.water_temp ? `${item.water_temp}°C` : '-'}</td>
                        <td>{item.depth_m ? `${item.depth_m}m` : '-'}</td>
                        <td>{item.wind_speed ? `${item.wind_speed.toFixed(1)}m/s` : '-'}</td>
                        <td>{item.tide_info || '-'}</td>
                        <td><strong>{item.distance_km ? `${item.distance_km}km` : '-'}</strong></td>
                        <td className="user-cell">
                          <small>{item.user_id || '익명'}</small>
                        </td>
                        <td>
                          <small>{new Date(item.caught_at).toLocaleDateString('ko-KR', {
                            year: '2-digit',
                            month: '2-digit',
                            day: '2-digit'
                          })}</small>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
      )}

      {/* 출조 계획 탭 */}
      {activeTab === 'plan' && (
      <div className="plan-container">
        <div className="plan-search-section">
          <h3>🎣 출조 계획</h3>
          <div className="plan-inputs">
            <div className="plan-input-group">
              <label>출조 날짜</label>
              <input
                type="date"
                value={planDate}
                onChange={(e) => setPlanDate(e.target.value)}
                className="form-input"
              />
            </div>
            <div className="plan-input-group">
              <label>대상 어종</label>
              <input
                type="text"
                placeholder="예) 우럭, 광어"
                value={planSpecies}
                onChange={(e) => setPlanSpecies(e.target.value)}
                className="form-input"
              />
            </div>
            <button className="btn-search" onClick={handlePlanSearch}>
              <i className="fas fa-search"></i>
              검색
            </button>
          </div>
        </div>

        {planLoading && <div className="loading-message">검색 중...</div>}

        {!planLoading && planResults.length === 0 && planDate && (
          <div className="empty-message">
            <i className="fas fa-user-plus"></i>
            <p>🎉 첫번째 게시자가 되세요!!</p>
          </div>
        )}

        {!planLoading && planResults.length > 0 && (
          <div className="plan-results">
            <h4>{planSpecies} - {planDate} 출조 정보</h4>
            <div className="plan-list-table-wrapper">
              <table className="plan-list-table">
                <thead>
                  <tr>
                    <th>어종</th>
                    <th>크기</th>
                    <th>위치</th>
                    <th>거리</th>
                    <th>물때</th>
                    <th>수위</th>
                    <th>사용자</th>
                    <th>날짜</th>
                  </tr>
                </thead>
                <tbody>
                  {planResults.map((item) => (
                    <tr key={item.id}>
                      <td className="species-cell"><strong>{item.species}</strong></td>
                      <td>{item.size_cm ? `${item.size_cm}cm` : '-'}</td>
                      <td className="location-cell"><small>{item.spot_name || '-'}</small></td>
                      <td><strong>{item.distance_km ? `${item.distance_km}km` : '-'}</strong></td>
                      <td>{item.tide_number ? `${item.tide_number}물` : '-'}</td>
                      <td>{item.water_level ? `${item.water_level.toFixed(1)}m` : '-'}</td>
                      <td><small>{item.user_nickname || '익명'}</small></td>
                      <td>
                        <small>{new Date(item.caught_at).toLocaleDateString('ko-KR', {
                          year: '2-digit',
                          month: '2-digit',
                          day: '2-digit'
                        })}</small>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
      )}
    </div>
  )
}

export default ExplorePage
