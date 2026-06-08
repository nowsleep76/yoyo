import { useState, useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import './RecordsPage.css'

function RecordsPage({ location }) {
  const [activeTab, setActiveTab] = useState('records')
  const [showNewRecordForm, setShowNewRecordForm] = useState(false)
  const [records, setRecords] = useState([])
  const [history, setHistory] = useState([])
  const [favorites, setFavorites] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedRecordId, setSelectedRecordId] = useState(null)

  // 새 기록 입력 상태
  const [selectedLocation, setSelectedLocation] = useState(() => ({
    latitude: location.latitude,
    longitude: location.longitude,
    name: location.name
  }))
  const [formData, setFormData] = useState({
    species: '',
    size_cm: '',
    weight_g: '',
    rod: '',
    reel: '',
    line_weight: '',
    leader: '',
    rig_method: '',
    description: '',
    is_public: false
  })

  // 지도 ref
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)

  // 초기 데이터 로드
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const recordsRes = await fetch('/api/catches')
        const historyRes = await fetch('/api/user/history')
        const favoritesRes = await fetch('/api/user/favorite-spots')
        const statsRes = await fetch('/api/user/stats')

        if (recordsRes.ok) {
          setRecords(await recordsRes.json())
        }
        if (historyRes.ok) {
          setHistory(await historyRes.json())
        }
        if (favoritesRes.ok) {
          setFavorites(await favoritesRes.json())
        }
        if (statsRes.ok) {
          setStats(await statsRes.json())
        }
        setError(null)
      } catch (err) {
        setError('데이터를 불러올 수 없습니다')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  // 지도 초기화
  useEffect(() => {
    if (showNewRecordForm && mapRef.current && !mapInstanceRef.current) {
      mapInstanceRef.current = L.map(mapRef.current).setView(
        [selectedLocation.latitude, selectedLocation.longitude],
        13
      )

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
      }).addTo(mapInstanceRef.current)

      // 지도 클릭 시 위치 선택
      mapInstanceRef.current.on('click', (e) => {
        setSelectedLocation({
          ...selectedLocation,
          latitude: e.latlng.lat,
          longitude: e.latlng.lng
        })
      })
    }

    return () => {
      if (!showNewRecordForm && mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [showNewRecordForm])

  // 지도 마커 업데이트
  useEffect(() => {
    if (!mapInstanceRef.current || !showNewRecordForm) return

    // 기존 마커 제거
    mapInstanceRef.current.eachLayer(layer => {
      if (layer instanceof L.CircleMarker) {
        layer.remove()
      }
    })

    // 새 마커 추가
    L.circleMarker([selectedLocation.latitude, selectedLocation.longitude], {
      radius: 8,
      fillColor: '#0066cc',
      color: '#0066cc',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.8
    }).addTo(mapInstanceRef.current)
  }, [selectedLocation, showNewRecordForm])

  return (
    <div className="records-page">
      <div className="records-header">
        <h1>기록</h1>
        <p className="subtitle">나의 낚시 활동 기록</p>
      </div>

      {stats && (
        <div className="stats-card">
          <div className="stat-item">
            <span className="stat-label">총 조과</span>
            <span className="stat-value">{stats.total_catches}마리</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">평균 크기</span>
            <span className="stat-value">{stats.avg_size?.toFixed(1)}cm</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">자주 잡는 어종</span>
            <span className="stat-value">{stats.favorite_species || '-'}</span>
          </div>
        </div>
      )}

      <div className="record-tabs">
        <button
          className={`record-tab ${activeTab === 'records' ? 'active' : ''}`}
          onClick={() => setActiveTab('records')}
        >
          <i className="fas fa-list"></i>
          조과 기록
        </button>
        <button
          className={`record-tab ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          <i className="fas fa-history"></i>
          방문 이력
        </button>
        <button
          className={`record-tab ${activeTab === 'favorites' ? 'active' : ''}`}
          onClick={() => setActiveTab('favorites')}
        >
          <i className="fas fa-star"></i>
          즐겨찾기
        </button>
      </div>

      {loading && <div className="loading-message">로딩 중...</div>}
      {error && <div className="error-message">{error}</div>}

      {!loading && activeTab === 'records' && (
        <>
          <div className="record-actions-bar">
            <button
              className="btn-new-record"
              onClick={() => setShowNewRecordForm(!showNewRecordForm)}
            >
              <i className="fas fa-plus"></i>
              새 기록 추가
            </button>
          </div>

          {showNewRecordForm && (
            <div className="new-record-form">
              <h3>새로운 조과 기록</h3>

              {/* 지도 - 위치 선택 */}
              <div className="form-section">
                <label>📍 위치 선택</label>
                <div
                  ref={mapRef}
                  className="record-map"
                  style={{ height: '300px', borderRadius: '8px', marginBottom: '15px' }}
                ></div>
                <p className="location-info">
                  선택된 위치: {selectedLocation.name}
                  ({selectedLocation.latitude.toFixed(4)}, {selectedLocation.longitude.toFixed(4)})
                </p>
              </div>

              {/* 기본 정보 */}
              <div className="form-section">
                <label>어종 <span className="required">*</span></label>
                <input
                  type="text"
                  placeholder="예) 우럭, 광어"
                  value={formData.species}
                  onChange={(e) => setFormData({...formData, species: e.target.value})}
                  className="form-input"
                />
              </div>

              <div className="form-row">
                <div className="form-section">
                  <label>크기 (cm)</label>
                  <input
                    type="number"
                    placeholder="예) 45"
                    value={formData.size_cm}
                    onChange={(e) => setFormData({...formData, size_cm: e.target.value})}
                    className="form-input"
                  />
                </div>
                <div className="form-section">
                  <label>무게 (g)</label>
                  <input
                    type="number"
                    placeholder="예) 1200"
                    value={formData.weight_g}
                    onChange={(e) => setFormData({...formData, weight_g: e.target.value})}
                    className="form-input"
                  />
                </div>
              </div>

              {/* 채비 정보 */}
              <h4 style={{marginTop: '20px'}}>🎣 채비 정보</h4>

              <div className="form-row">
                <div className="form-section">
                  <label>낚싯대</label>
                  <input
                    type="text"
                    placeholder="예) 샤마 6ft"
                    value={formData.rod}
                    onChange={(e) => setFormData({...formData, rod: e.target.value})}
                    className="form-input"
                  />
                </div>
                <div className="form-section">
                  <label>릴</label>
                  <input
                    type="text"
                    placeholder="예) 시마노 3000"
                    value={formData.reel}
                    onChange={(e) => setFormData({...formData, reel: e.target.value})}
                    className="form-input"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-section">
                  <label>원줄</label>
                  <input
                    type="text"
                    placeholder="예) PE 1.5호"
                    value={formData.line_weight}
                    onChange={(e) => setFormData({...formData, line_weight: e.target.value})}
                    className="form-input"
                  />
                </div>
                <div className="form-section">
                  <label>목줄</label>
                  <input
                    type="text"
                    placeholder="예) 나일론 3호"
                    value={formData.leader}
                    onChange={(e) => setFormData({...formData, leader: e.target.value})}
                    className="form-input"
                  />
                </div>
              </div>

              <div className="form-section">
                <label>채비법</label>
                <textarea
                  placeholder="예) 벵디그로 볼헤드 + 소프트 플라스틱..."
                  value={formData.rig_method}
                  onChange={(e) => setFormData({...formData, rig_method: e.target.value})}
                  className="form-textarea"
                  rows="3"
                ></textarea>
              </div>

              <div className="form-section">
                <label>메모</label>
                <textarea
                  placeholder="기타 정보, 날씨, 물때 등..."
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="form-textarea"
                  rows="2"
                ></textarea>
              </div>

              <div className="form-section">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.is_public}
                    onChange={(e) => setFormData({...formData, is_public: e.target.checked})}
                  />
                  <span>커뮤니티에 공개</span>
                </label>
              </div>

              <div className="form-actions">
                <button
                  className="btn-save"
                  onClick={async () => {
                    if (!formData.species.trim()) {
                      alert('어종을 입력해주세요')
                      return
                    }

                    try {
                      const response = await fetch('/api/catches', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                          species: formData.species,
                          size_cm: formData.size_cm ? parseFloat(formData.size_cm) : null,
                          weight_g: formData.weight_g ? parseFloat(formData.weight_g) : null,
                          spot_name: selectedLocation.name,
                          location_lat: selectedLocation.latitude,
                          location_lng: selectedLocation.longitude,
                          rod: formData.rod,
                          reel: formData.reel,
                          line_weight: formData.line_weight,
                          leader: formData.leader,
                          rig_method: formData.rig_method,
                          description: formData.description,
                          is_public: formData.is_public,
                          caught_at: new Date().toISOString()
                        })
                      })

                      if (response.ok) {
                        alert('기록이 저장되었습니다')
                        setShowNewRecordForm(false)
                        // 기록 목록 새로고침
                        const res = await fetch('/api/catches')
                        if (res.ok) {
                          setRecords(await res.json())
                        }
                      }
                    } catch (err) {
                      alert('저장 실패: ' + err.message)
                    }
                  }}
                >
                  저장
                </button>
                <button
                  className="btn-cancel"
                  onClick={() => setShowNewRecordForm(false)}
                >
                  취소
                </button>
              </div>
            </div>
          )}

          <div className="records-table-wrapper">
            {records.length === 0 ? (
              <div className="empty-message">
                <i className="fas fa-inbox"></i>
                <p>조과 기록이 없습니다</p>
              </div>
            ) : (
              <>
                <table className="records-table">
                  <thead>
                    <tr>
                      <th>어종</th>
                      <th>크기</th>
                      <th>무게</th>
                      <th>낚싯대</th>
                      <th>릴</th>
                      <th>날짜</th>
                      <th>공개</th>
                      <th>작업</th>
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((record) => (
                      <tr key={record.id} className={selectedRecordId === record.id ? 'selected' : ''}>
                        <td className="species-cell">
                          <strong>{record.species || '-'}</strong>
                        </td>
                        <td>{record.size_cm ? `${record.size_cm}cm` : '-'}</td>
                        <td>{record.weight_g ? `${record.weight_g}g` : '-'}</td>
                        <td>{record.rod || '-'}</td>
                        <td>{record.reel || '-'}</td>
                        <td>{record.caught_at ? new Date(record.caught_at).toLocaleDateString('ko-KR') : '-'}</td>
                        <td>{record.is_public ? '공개' : '비공개'}</td>
                        <td className="action-cell">
                          <button className="btn-row-action" title="상세보기" onClick={() => setSelectedRecordId(record.id)}>
                            <i className="fas fa-eye"></i>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {selectedRecordId && (
                  <div className="record-detail-panel">
                    {(() => {
                      const record = records.find(r => r.id === selectedRecordId)
                      return record ? (
                        <div className="detail-content">
                          <div className="detail-header">
                            <h3>{record.species}</h3>
                            <button className="btn-close" onClick={() => setSelectedRecordId(null)}>
                              <i className="fas fa-times"></i>
                            </button>
                          </div>
                          <div className="detail-grid">
                            <div className="detail-item">
                              <label>크기</label>
                              <p>{record.size_cm ? `${record.size_cm}cm` : '-'}</p>
                            </div>
                            <div className="detail-item">
                              <label>무게</label>
                              <p>{record.weight_g ? `${record.weight_g}g` : '-'}</p>
                            </div>
                            <div className="detail-item">
                              <label>낚싯대</label>
                              <p>{record.rod || '-'}</p>
                            </div>
                            <div className="detail-item">
                              <label>릴</label>
                              <p>{record.reel || '-'}</p>
                            </div>
                            <div className="detail-item">
                              <label>원줄</label>
                              <p>{record.line_weight || '-'}</p>
                            </div>
                            <div className="detail-item">
                              <label>목줄</label>
                              <p>{record.leader || '-'}</p>
                            </div>
                            <div className="detail-item">
                              <label>채비법</label>
                              <p>{record.rig_method || '-'}</p>
                            </div>
                            <div className="detail-item">
                              <label>날씨</label>
                              <p>{record.weather_condition || '-'}</p>
                            </div>
                            <div className="detail-item">
                              <label>물때</label>
                              <p>{record.tide_info || '-'}</p>
                            </div>
                            <div className="detail-item">
                              <label>수온</label>
                              <p>{record.water_temp ? `${record.water_temp}°C` : '-'}</p>
                            </div>
                            <div className="detail-item full-width">
                              <label>설명</label>
                              <p>{record.description || '-'}</p>
                            </div>
                            <div className="detail-item full-width">
                              <label>위치</label>
                              <p>{record.spot_name || '-'} ({record.location_lat?.toFixed(4)}, {record.location_lng?.toFixed(4)})</p>
                            </div>
                          </div>
                        </div>
                      ) : null
                    })()}
                  </div>
                )}
              </>
            )}
          </div>
        </>
      )}

      {!loading && activeTab === 'history' && (
        <div className="history-list">
          {history.length === 0 ? (
            <div className="empty-message">
              <i className="fas fa-inbox"></i>
              <p>방문 이력이 없습니다</p>
            </div>
          ) : (
            history.map((item) => (
              <div key={item.id} className="history-item">
                <div className="history-info">
                  <h3>{item.spot_name}</h3>
                  <p className="detail">{item.visited_at}</p>
                  <p className="detail">조과: {item.catch_count}마리</p>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {!loading && activeTab === 'favorites' && (
        <div className="favorites-list">
          {favorites.length === 0 ? (
            <div className="empty-message">
              <i className="fas fa-inbox"></i>
              <p>즐겨찾기가 없습니다</p>
            </div>
          ) : (
            favorites.map((item) => (
              <div key={item.id} className="favorite-item">
                <div className="favorite-info">
                  <h3>{item.name}</h3>
                  <p className="detail">{item.region || '지역 정보'}</p>
                  <p className="detail">어종: {item.fish_types || '-'}</p>
                </div>
                <button className="btn-unfavorite">
                  <i className="fas fa-star"></i>
                </button>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}

export default RecordsPage
