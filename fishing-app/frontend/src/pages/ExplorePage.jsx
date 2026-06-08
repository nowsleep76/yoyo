import { useState, useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import './ExplorePage.css'

function ExplorePage({ location }) {
  const [allCatches, setAllCatches] = useState([])
  const [selectedCatches, setSelectedCatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filterType, setFilterType] = useState('latest')
  const [selectedLocation, setSelectedLocation] = useState(null)

  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const markersRef = useRef([])

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

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [])

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
        const handleMarkerClick = () => {
          // 같은 위치의 모든 기록 필터링
          const nearbyRecords = allCatches.filter(c =>
            Math.abs(c.location_lat - catchRecord.location_lat) < 0.01 &&
            Math.abs(c.location_lng - catchRecord.location_lng) < 0.01
          )
          setSelectedCatches(nearbyRecords)
          setSelectedLocation({
            lat: catchRecord.location_lat,
            lng: catchRecord.location_lng
          })
        }

        const catchDate = new Date(catchRecord.caught_at)
        const dateStr = catchDate.toLocaleDateString('ko-KR', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit'
        })

        const popupHTML = `
          <div style="font-family: 'Noto Sans KR', Arial, sans-serif; padding: 8px; font-size: 12px;">
            <strong style="display: block; margin-bottom: 4px; color: #0066cc;">${catchRecord.species || '미분류'}</strong>
            <small style="display: block;">크기: ${catchRecord.size_cm || '-'}cm</small>
            <small style="display: block;">사용자: ${catchRecord.user_id || '익명'}</small>
            <small style="display: block; color: #999;">📅 ${dateStr}</small>
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
          .on('click', handleMarkerClick)
          .addTo(mapInstanceRef.current)

        markersRef.current.push(marker)
      }
    })
  }, [allCatches, allCatches.length])

  return (
    <div className="explore-page">
      <div className="explore-header">
        <h1>탐색</h1>
        <p className="subtitle">최근 조과 정보</p>
      </div>

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

          {!loading && selectedLocation && selectedCatches.length === 0 && (
            <div className="empty-message">
              <i className="fas fa-inbox"></i>
              <p>이 위치에 조과 기록이 없습니다</p>
            </div>
          )}

          {!loading && selectedCatches.length > 0 && (
            <>
              <div className="location-header">
                <h3>📍 {selectedLocation.lat.toFixed(4)}, {selectedLocation.lng.toFixed(4)}</h3>
                <p className="record-count">{selectedCatches.length}개의 기록</p>
              </div>

              <div className="catch-results-table-wrapper">
                <table className="catch-results-table">
                  <thead>
                    <tr>
                      <th>어종</th>
                      <th>크기</th>
                      <th>무게</th>
                      <th>낚싯대</th>
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
                        <td>{item.rod || '-'}</td>
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
    </div>
  )
}

export default ExplorePage
