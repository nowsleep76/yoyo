import { useState, useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { StorageUtils } from '../utils/storage'
import './RecordsPage.css'

function RecordsPage({ location, userId }) {
  const [activeTab, setActiveTab] = useState('records')
  const [recordsDisplayMode, setRecordsDisplayMode] = useState('list') // 'list' or 'sns'
  const [showNewRecordForm, setShowNewRecordForm] = useState(false)
  const [records, setRecords] = useState([])
  const [history, setHistory] = useState([])
  const [favorites, setFavorites] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedRecordId, setSelectedRecordId] = useState(null)

  // 통계 및 랭킹 상태
  const [myStats, setMyStats] = useState(null)
  const [gradeRankings, setGradeRankings] = useState([])
  const [maxSizeRankings, setMaxSizeRankings] = useState([])
  const [countRankings, setCountRankings] = useState([])
  const [likesRankings, setLikesRankings] = useState([])
  const [rankingsLoading, setRankingsLoading] = useState(false)

  // 게시물 즐겨찾기 상태
  const [favoriteCatchIds, setFavoriteCatchIds] = useState(new Set())

  // 새 기록 입력 상태
  const [selectedLocation, setSelectedLocation] = useState(() => ({
    latitude: location.latitude,
    longitude: location.longitude,
    name: location.name
  }))
  const [autoData, setAutoData] = useState({
    tideNumber: null,
    waterLevel: null,
    tidalCurrent: null,
    windSpeed: null
  })
  const [suggestions, setSuggestions] = useState({
    species: [],
    rod: [],
    reel: [],
    lineWeight: [],
    leader: [],
    rigMethod: []
  })
  const [formData, setFormData] = useState({
    species: '',
    size_cm: '',
    rod: '',
    reel: '',
    line_weight: '',
    leader: '',
    rig_method: '',
    hit_date: new Date().toISOString().split('T')[0],
    hit_time: '',
    user_nickname: '',
    photos: [],
    description: '',
    is_public: true
  })

  // 지도 ref
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)

  // 초기 데이터 로드 및 자동완성 초기화
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const recordsRes = await fetch('/api/catches?limit=200')
        const historyRes = await fetch('/api/user/history')
        const favoritesRes = await fetch('/api/user/favorite-spots')
        const statsUrl = userId ? `/api/user/stats?user_id=${userId}` : '/api/user/stats'
        const statsRes = await fetch(statsUrl)

        if (recordsRes.ok) {
          const records = await recordsRes.json()
          setRecords(records)
          // 자동완성 데이터 추출
          initializeSuggestions(records)
        }
        if (historyRes.ok) {
          setHistory(await historyRes.json())
        }
        if (favoritesRes.ok) {
          setFavorites(await favoritesRes.json())
        }
        if (statsRes.ok) {
          setStats(await statsRes.json())
          setMyStats(await statsRes.json())
        }

        // 랭킹 데이터 로드
        loadRankings()

        setError(null)
      } catch (err) {
        setError('데이터를 불러올 수 없습니다')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    // 랭킹 데이터 로드 함수
    const loadRankings = async () => {
      try {
        const gradeRes = await fetch('/api/catches/rankings/grade')
        const sizeRes = await fetch('/api/catches/rankings/max-size')
        const countRes = await fetch('/api/catches/rankings/count')

        if (gradeRes.ok) setGradeRankings(await gradeRes.json())
        if (sizeRes.ok) setMaxSizeRankings(await sizeRes.json())
        if (countRes.ok) setCountRankings(await countRes.json())
      } catch (err) {
        console.error('랭킹 로드 실패:', err)
      }
    }

    // 자동완성 초기화 함수 (StorageUtils 사용)
    const initializeSuggestions = (records) => {
      const savedSuggestions = StorageUtils.getItem('fishingAppSuggestions')
      if (savedSuggestions) {
        try {
          setSuggestions(JSON.parse(savedSuggestions))
        } catch (e) {
          console.warn('저장된 자동완성 데이터 파싱 실패:', e)
          setSuggestions({})
        }
      } else {
        const newSuggestions = {
          species: [...new Set(records.map(r => r.species).filter(Boolean))],
          rod: [...new Set(records.map(r => r.rod).filter(Boolean))],
          reel: [...new Set(records.map(r => r.reel).filter(Boolean))],
          lineWeight: [...new Set(records.map(r => r.line_weight).filter(Boolean))],
          leader: [...new Set(records.map(r => r.leader).filter(Boolean))],
          rigMethod: [...new Set(records.map(r => r.rig_method).filter(Boolean))]
        }
        setSuggestions(newSuggestions)
        const saved = StorageUtils.setItem('fishingAppSuggestions', JSON.stringify(newSuggestions))
        if (!saved) {
          console.warn('자동완성 데이터 저장 실패')
        }
      }

      // 프로필 데이터 로드해서 기본값 설정
      if (userId) {
        fetch(`/api/user/profile?user_id=${userId}`)
          .then(res => res.ok ? res.json() : null)
          .then(profile => {
            if (profile) {
              const nickname = profile.nickname || ''
              setFormData(prev => ({
                ...prev,
                user_nickname: nickname,
                rod: profile.preferred_rod || '',
                reel: profile.preferred_reel || '',
                line_weight: profile.preferred_line_weight || '',
                leader: profile.preferred_leader || ''
              }))
              // 기록을 현재 사용자의 닉네임으로 필터링
              setRecords(prev => prev.filter(r => r.user_nickname === nickname))
            }
          })
          .catch(err => console.log('프로필 로드 실패:', err))
      } else {
        // 사용자 ID가 없으면 StorageUtils에서 닉네임 로드
        const savedNickname = StorageUtils.getItem('userNickname')
        if (savedNickname) {
          setFormData(prev => ({...prev, user_nickname: savedNickname}))
        }
      }
    }

    fetchData()
  }, [])

  // 위치 및 히트 날짜/시간 변경 시 물때/수위/조류/바람 자동 데이터 로드
  useEffect(() => {
    if (!showNewRecordForm || !selectedLocation.latitude) return

    const fetchEnvironmentalData = async () => {
      try {
        // 히트 날짜가 입력되면 그 날짜 사용, 아니면 오늘 날짜
        const dateStr = formData.hit_date || new Date().toISOString().split('T')[0]

        const response = await fetch(
          `/api/tide/hourly?lat=${selectedLocation.latitude}&lon=${selectedLocation.longitude}&date=${dateStr}`
        )
        if (response.ok) {
          const data = await response.json()

          // 히트 시간이 입력되면 그 시간 사용, 아니면 현재 시간
          let hourIndex = 0
          if (formData.hit_time) {
            const [hitHour] = formData.hit_time.split(':')
            hourIndex = parseInt(hitHour)
          } else {
            hourIndex = new Date().getHours()
          }

          const targetHour = data.hourly?.[hourIndex] || {}

          setAutoData({
            tideNumber: data.tideNumber || null,
            waterLevel: targetHour?.height || null,
            tidalCurrent: targetHour?.currentSpeed || null,
            windSpeed: targetHour?.windSpeed || null
          })
        }
      } catch (err) {
        console.error('환경 데이터 로드 실패:', err)
      }
    }

    fetchEnvironmentalData()
  }, [selectedLocation, showNewRecordForm, formData.hit_date, formData.hit_time])

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
        <button
          className={`record-tab ${activeTab === 'stats' ? 'active' : ''}`}
          onClick={() => setActiveTab('stats')}
        >
          <i className="fas fa-chart-bar"></i>
          통계
        </button>
        <button
          className={`record-tab ${activeTab === 'rankings' ? 'active' : ''}`}
          onClick={() => setActiveTab('rankings')}
        >
          <i className="fas fa-trophy"></i>
          랭킹
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
            <div className="display-mode-toggle">
              <button
                className={`mode-btn ${recordsDisplayMode === 'list' ? 'active' : ''}`}
                onClick={() => setRecordsDisplayMode('list')}
                title="리스트 모드"
              >
                <i className="fas fa-list"></i>
              </button>
              <button
                className={`mode-btn ${recordsDisplayMode === 'sns' ? 'active' : ''}`}
                onClick={() => setRecordsDisplayMode('sns')}
                title="SNS 모드"
              >
                <i className="fas fa-images"></i>
              </button>
            </div>
          </div>

          {showNewRecordForm && (
            <div className="new-record-form">
              {/* 헤더: 닉네임 & 히트 일시 */}
              <div className="form-header-section">
                <div className="header-content">
                  <div className="header-item">
                    <label>👤 닉네임</label>
                    <input
                      type="text"
                      placeholder="사용자 닉네임"
                      value={formData.user_nickname}
                      onChange={(e) => {
                        setFormData({...formData, user_nickname: e.target.value})
                        StorageUtils.setItem('userNickname', e.target.value)
                      }}
                      className="form-input"
                    />
                  </div>
                  <div className="header-item">
                    <label>🎣 히트 일시 <span className="required">*</span></label>
                    <div className="datetime-inputs">
                      <input
                        type="date"
                        value={formData.hit_date}
                        onChange={(e) => setFormData({...formData, hit_date: e.target.value})}
                        className="form-input"
                      />
                      <input
                        type="time"
                        value={formData.hit_time}
                        onChange={(e) => setFormData({...formData, hit_time: e.target.value})}
                        className="form-input"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* 📊 현재 환경 정보 (자동 감지) */}
              <div className="form-section auto-data-section">
                <h4>📊 현재 환경 (자동 감지)</h4>
                <div className="auto-data-grid">
                  <div className="auto-data-item">
                    <span className="label">물때</span>
                    <span className="value">{autoData.tideNumber ? `${autoData.tideNumber}물` : '-'}</span>
                  </div>
                  <div className="auto-data-item">
                    <span className="label">수위</span>
                    <span className="value">{autoData.waterLevel ? `${autoData.waterLevel.toFixed(1)}m` : '-'}</span>
                  </div>
                  <div className="auto-data-item">
                    <span className="label">조류</span>
                    <span className="value">{autoData.tidalCurrent ? `${autoData.tidalCurrent.toFixed(1)}m/s` : '-'}</span>
                  </div>
                  <div className="auto-data-item">
                    <span className="label">바람</span>
                    <span className="value">{autoData.windSpeed ? `${autoData.windSpeed.toFixed(1)}m/s` : '-'}</span>
                  </div>
                </div>
              </div>

              {/* 📸 사진 업로드 */}
              <div className="form-section">
                <h4>📸 사진 업로드</h4>
                <input
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={(e) => {
                    const files = Array.from(e.target.files || [])
                    setFormData({...formData, photos: files})
                  }}
                  className="form-file-input"
                />
                <p className="help-text">사진의 메타 정보(날짜, 위치 등)를 자동으로 분석합니다</p>
              </div>

              {/* 📍 위치 선택 */}
              <div className="form-section">
                <h4>📍 위치 선택</h4>
                <div
                  ref={mapRef}
                  className="record-map"
                  style={{ height: '250px', borderRadius: '8px', marginBottom: '12px' }}
                ></div>
                <p className="location-info">
                  📍 {selectedLocation.name} ({selectedLocation.latitude.toFixed(4)}, {selectedLocation.longitude.toFixed(4)})
                </p>
              </div>

              {/* 🎣 기본 정보 */}
              <div className="form-section">
                <h4>🎣 기본 정보</h4>
                <div>
                  <label>어종 <span className="required">*</span></label>
                  <input
                    type="text"
                    list="species-list"
                    placeholder="예) 우럭, 광어"
                    value={formData.species}
                    onChange={(e) => setFormData({...formData, species: e.target.value})}
                    className="form-input"
                  />
                  <datalist id="species-list">
                    {suggestions.species.map((s) => <option key={s} value={s} />)}
                  </datalist>
                </div>

                <div className="form-row" style={{marginTop: '10px'}}>
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
                </div>
              </div>

              {/* 🎣 채비 정보 (자동완성) */}
              <div className="form-section">
                <h4>🎣 채비 정보</h4>

                <div className="form-row">
                  <div className="form-section">
                    <label>낚싯대</label>
                    <input
                      type="text"
                      list="rod-list"
                      placeholder="예) 샤마 6ft"
                      value={formData.rod}
                      onChange={(e) => setFormData({...formData, rod: e.target.value})}
                      className="form-input"
                    />
                    <datalist id="rod-list">
                      {suggestions.rod.map((r) => <option key={r} value={r} />)}
                    </datalist>
                  </div>
                  <div className="form-section">
                    <label>릴</label>
                    <input
                      type="text"
                      list="reel-list"
                      placeholder="예) 시마노 3000"
                      value={formData.reel}
                      onChange={(e) => setFormData({...formData, reel: e.target.value})}
                      className="form-input"
                    />
                    <datalist id="reel-list">
                      {suggestions.reel.map((r) => <option key={r} value={r} />)}
                    </datalist>
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-section">
                    <label>원줄</label>
                    <input
                      type="text"
                      list="line-list"
                      placeholder="예) PE 1.5호"
                      value={formData.line_weight}
                      onChange={(e) => setFormData({...formData, line_weight: e.target.value})}
                      className="form-input"
                    />
                    <datalist id="line-list">
                      {suggestions.lineWeight.map((l) => <option key={l} value={l} />)}
                    </datalist>
                  </div>
                  <div className="form-section">
                    <label>목줄</label>
                    <input
                      type="text"
                      list="leader-list"
                      placeholder="예) 나일론 3호"
                      value={formData.leader}
                      onChange={(e) => setFormData({...formData, leader: e.target.value})}
                      className="form-input"
                    />
                    <datalist id="leader-list">
                      {suggestions.leader.map((l) => <option key={l} value={l} />)}
                    </datalist>
                  </div>
                </div>

                <div className="form-section">
                  <label>채비법</label>
                  <textarea
                    placeholder="예) 벵디그로 볼헤드 + 소프트 플라스틱..."
                    value={formData.rig_method}
                    onChange={(e) => setFormData({...formData, rig_method: e.target.value})}
                    className="form-textarea"
                    rows="2"
                  ></textarea>
                </div>
              </div>

              {/* 📝 추가 정보 */}
              <div className="form-section">
                <h4>📝 추가 정보</h4>
                <label>메모</label>
                <textarea
                  placeholder="기타 정보, 느낀점 등..."
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="form-textarea"
                  rows="2"
                ></textarea>

                <label className="checkbox-label" style={{marginTop: '12px'}}>
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

                    if (!formData.hit_date) {
                      alert('히트 날짜를 입력해주세요')
                      return
                    }

                    try {
                      // 자동완성 데이터 업데이트
                      const updatedSuggestions = {
                        ...suggestions,
                        species: formData.species && !suggestions.species.includes(formData.species)
                          ? [formData.species, ...suggestions.species].slice(0, 10)
                          : suggestions.species,
                        rod: formData.rod && !suggestions.rod.includes(formData.rod)
                          ? [formData.rod, ...suggestions.rod].slice(0, 10)
                          : suggestions.rod,
                        reel: formData.reel && !suggestions.reel.includes(formData.reel)
                          ? [formData.reel, ...suggestions.reel].slice(0, 10)
                          : suggestions.reel,
                        lineWeight: formData.line_weight && !suggestions.lineWeight.includes(formData.line_weight)
                          ? [formData.line_weight, ...suggestions.lineWeight].slice(0, 10)
                          : suggestions.lineWeight,
                        leader: formData.leader && !suggestions.leader.includes(formData.leader)
                          ? [formData.leader, ...suggestions.leader].slice(0, 10)
                          : suggestions.leader,
                        rigMethod: formData.rig_method && !suggestions.rigMethod.includes(formData.rig_method)
                          ? [formData.rig_method, ...suggestions.rigMethod].slice(0, 10)
                          : suggestions.rigMethod
                      }
                      const saved = StorageUtils.setItem('fishingAppSuggestions', JSON.stringify(updatedSuggestions))
                      if (!saved) {
                        console.warn('자동완성 데이터 저장 실패')
                      }

                      // 히트 일시 조합 (날짜 + 시간)
                      let caughtAt = formData.hit_date
                      if (formData.hit_time) {
                        caughtAt += 'T' + formData.hit_time + ':00'
                      } else {
                        caughtAt += 'T00:00:00'
                      }

                      const response = await fetch('/api/catches', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                          species: formData.species,
                          size_cm: formData.size_cm ? parseFloat(formData.size_cm) : null,
                          spot_name: selectedLocation.name,
                          location_lat: selectedLocation.latitude,
                          location_lng: selectedLocation.longitude,
                          rod: formData.rod,
                          reel: formData.reel,
                          line_weight: formData.line_weight,
                          leader: formData.leader,
                          rig_method: formData.rig_method,
                          user_nickname: formData.user_nickname,
                          tide_number: autoData.tideNumber,
                          water_level: autoData.waterLevel,
                          tidal_current: autoData.tidalCurrent,
                          wind_speed: autoData.windSpeed,
                          description: formData.description,
                          photos: formData.photos.length > 0 ? true : false,
                          is_public: formData.is_public,
                          caught_at: caughtAt
                        })
                      })

                      if (response.ok) {
                        alert('기록이 저장되었습니다')
                        setShowNewRecordForm(false)
                        setSuggestions(updatedSuggestions)
                        // 기록 목록 새로고침
                        const res = await fetch('/api/catches')
                        if (res.ok) {
                          setRecords(await res.json())
                        }
                      }
                    } catch (err) {
                      alert('저장 실패: ' + err.message)
                      console.error(err)
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

          {recordsDisplayMode === 'list' ? (
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
                        <th>날짜</th>
                        <th>시간</th>
                        <th>위치</th>
                        <th>어종</th>
                        <th>사이즈</th>
                        <th>물때</th>
                        <th>수위</th>
                        <th>작업</th>
                      </tr>
                    </thead>
                    <tbody>
                      {records.map((record) => {
                        const caughtDate = record.caught_at ? new Date(record.caught_at) : null
                        return (
                          <tr key={record.id} className={selectedRecordId === record.id ? 'selected' : ''}>
                            <td>{caughtDate ? caughtDate.toLocaleDateString('ko-KR', {month: 'short', day: 'numeric'}) : '-'}</td>
                            <td>{record.hit_time ? record.hit_time.substring(0, 5) : (caughtDate ? caughtDate.toLocaleTimeString('ko-KR', {hour: '2-digit', minute: '2-digit'}) : '-')}</td>
                            <td className="location-cell"><small>{record.spot_name || '-'}</small></td>
                            <td className="species-cell">
                              <strong>{record.species || '-'}</strong>
                            </td>
                            <td>{record.size_cm ? `${record.size_cm}cm` : '-'}</td>
                            <td>{record.tide_number ? `${record.tide_number}물` : '-'}</td>
                            <td>{record.water_level ? `${record.water_level.toFixed(1)}m` : '-'}</td>
                            <td className="action-cell">
                              <button className="btn-row-action" title="상세보기" onClick={() => setSelectedRecordId(record.id)}>
                                <i className="fas fa-eye"></i>
                              </button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </>
              )}
            </div>
          ) : (
            <div className="sns-feed">
              {records.length === 0 ? (
                <div className="empty-message">
                  <i className="fas fa-inbox"></i>
                  <p>조과 기록이 없습니다</p>
                </div>
              ) : (
                <div className="sns-cards-grid">
                  {records.map((record) => {
                    const caughtDate = record.caught_at ? new Date(record.caught_at) : null
                    return (
                      <div key={record.id} className="sns-card" onClick={() => setSelectedRecordId(record.id)}>
                        <div className="sns-card-image">
                          <div className="placeholder-image">
                            <i className="fas fa-image"></i>
                          </div>
                        </div>
                        <div className="sns-card-header">
                          <div className="card-user-info">
                            <span className="user-name">{record.user_nickname || '익명'}</span>
                            <span className="card-date">
                              {caughtDate ? caughtDate.toLocaleDateString('ko-KR') : '-'}
                            </span>
                          </div>
                        </div>
                        <div className="sns-card-content">
                          <h3 className="card-species">{record.species || '-'}</h3>
                          <div className="card-stats">
                            <span className="stat">📏 {record.size_cm ? `${record.size_cm}cm` : '-'}</span>
                            <span className="stat">🌊 {record.tide_number ? `${record.tide_number}물` : '-'}</span>
                            <span className="stat">📊 {record.water_level ? `${record.water_level.toFixed(1)}m` : '-'}</span>
                          </div>
                          <div className="card-env-info">
                            {record.water_temp && <span className="env-badge">🌡️ {record.water_temp}°C</span>}
                            {record.wind_speed && <span className="env-badge">💨 {record.wind_speed}m/s</span>}
                            {record.tidal_current && <span className="env-badge">⚡ 조류 {record.tidal_current}</span>}
                            {record.weather_condition && <span className="env-badge">☀️ {record.weather_condition}</span>}
                          </div>
                          <p className="card-description">{record.description || record.spot_name || '설명 없음'}</p>
                          <div className="card-location">
                            <i className="fas fa-map-marker-alt"></i>
                            <span>{record.spot_name || '-'}</span>
                          </div>
                        </div>
                        <div className="sns-card-footer">
                          <span className="like-btn">
                            <i className="fas fa-heart"></i> {record.like_count || 0}
                          </span>
                          <span className="view-btn">
                            <i className="fas fa-eye"></i> {record.view_count || 0}
                          </span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}

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
                              <label>히트 시간</label>
                              <p>{record.hit_time ? record.hit_time.substring(0, 5) : '-'}</p>
                            </div>
                            <div className="detail-item">
                              <label>물때</label>
                              <p>{record.tide_number ? `${record.tide_number}물` : '-'}</p>
                            </div>
                            <div className="detail-item">
                              <label>수위</label>
                              <p>{record.water_level ? `${record.water_level.toFixed(1)}m` : '-'}</p>
                            </div>
                            <div className="detail-item">
                              <label>조류</label>
                              <p>{record.tidal_current ? `${record.tidal_current.toFixed(1)}m/s` : '-'}</p>
                            </div>
                            <div className="detail-item">
                              <label>바람</label>
                              <p>{record.wind_speed ? `${record.wind_speed.toFixed(1)}m/s` : '-'}</p>
                            </div>
                            <div className="detail-item">
                              <label>수온</label>
                              <p>{record.water_temp ? `${record.water_temp}°C` : '-'}</p>
                            </div>
                            <div className="detail-item">
                              <label>수심</label>
                              <p>{record.depth_m ? `${record.depth_m}m` : '-'}</p>
                            </div>
                            <div className="detail-item">
                              <label>사용자</label>
                              <p>{record.user_nickname || '-'}</p>
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
                            <div className="detail-item full-width">
                              <label>메모</label>
                              <p>{record.description || '-'}</p>
                            </div>
                            <div className="detail-item full-width">
                              <label>위치</label>
                              <p>{record.spot_name || '-'} ({record.location_lat?.toFixed(4)}, {record.location_lng?.toFixed(4)})</p>
                            </div>
                            <div className="detail-item">
                              <label>공개 상태</label>
                              <p>{record.is_public ? '공개' : '비공개'}</p>
                            </div>
                          </div>
                        </div>
                      ) : null
              })()}
            </div>
          )}
        </>
      )}

      {!loading && activeTab === 'history' && (() => {
        // 기록 데이터로부터 방문 이력 생성
        const visitMap = {}
        records.forEach(record => {
          const spot = record.spot_name || '미정'
          if (!visitMap[spot]) {
            visitMap[spot] = {
              spot_name: spot,
              count: 0,
              dates: [],
              totalSize: 0,
              species: []
            }
          }
          visitMap[spot].count += 1
          visitMap[spot].totalSize += record.size_cm || 0
          if (record.caught_at) {
            visitMap[spot].dates.push(new Date(record.caught_at))
          }
          if (record.species && !visitMap[spot].species.includes(record.species)) {
            visitMap[spot].species.push(record.species)
          }
        })

        const visitHistory = Object.values(visitMap).sort((a, b) => {
          const aDate = a.dates.length > 0 ? Math.max(...a.dates) : 0
          const bDate = b.dates.length > 0 ? Math.max(...b.dates) : 0
          return bDate - aDate
        })

        return (
          <div className="history-list">
            {visitHistory.length === 0 ? (
              <div className="empty-message">
                <i className="fas fa-inbox"></i>
                <p>방문 이력이 없습니다</p>
              </div>
            ) : (
              visitHistory.map((item, idx) => (
                <div key={idx} className="history-item">
                  <div className="history-header">
                    <h3>{item.spot_name}</h3>
                    <span className="visit-count">{item.count}회</span>
                  </div>
                  <div className="history-details">
                    <p className="detail">방문 날짜: {item.dates.length > 0 ? new Date(Math.max(...item.dates)).toLocaleDateString('ko-KR') : '-'}</p>
                    <p className="detail">조과: {item.count}마리 (평균 {(item.totalSize / item.count).toFixed(1)}cm)</p>
                    <p className="detail">주요 어종: {item.species.slice(0, 3).join(', ')}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        )
      })()}

      {!loading && activeTab === 'favorites' && (() => {
        // Favorited된 기록만 필터링
        const favoritedRecords = records.filter(r => r.is_favorited || favoriteCatchIds.has(r.id))

        return (
          <div className="favorites-list">
            {favoritedRecords.length === 0 ? (
              <div className="empty-message">
                <i className="fas fa-inbox"></i>
                <p>즐겨찾기 게시물이 없습니다</p>
              </div>
            ) : (
              <div className="favorite-grid">
                {favoritedRecords.map((record) => {
                  const caughtDate = record.caught_at ? new Date(record.caught_at) : null
                  return (
                    <div key={record.id} className="favorite-card" onClick={() => setSelectedRecordId(record.id)}>
                      <div className="favorite-image">
                        <div className="placeholder-image">
                          <i className="fas fa-image"></i>
                        </div>
                        <button
                          className="btn-favorite"
                          title="즐겨찾기 해제"
                          onClick={(e) => {
                            e.stopPropagation()
                            // 즐겨찾기 해제
                          }}
                        >
                          <i className="fas fa-star"></i>
                        </button>
                      </div>
                      <div className="favorite-info">
                        <h3>{record.species}</h3>
                        <p className="user">{record.user_nickname || '익명'}</p>
                        <p className="date">{caughtDate ? caughtDate.toLocaleDateString('ko-KR') : '-'}</p>
                        <p className="size">크기: {record.size_cm ? `${record.size_cm}cm` : '-'}</p>
                        <p className="location">{record.spot_name || '-'}</p>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )
      })()}

      {!loading && activeTab === 'stats' && (
        <div className="stats-section">
          {myStats ? (
            <div className="my-stats-card">
              <div className="stats-header">
                <div className="grade-display">
                  <h2>나의 등급</h2>
                  <div className="grade-badge">
                    <span className="grade-emoji">{myStats.grade?.emoji || '🎣'}</span>
                    <span className="grade-name">{myStats.grade?.name || '낚시꾼'}</span>
                  </div>
                  <p className="grade-desc">{myStats.grade?.desc}</p>
                </div>
              </div>

              <div className="stats-grid">
                <div className="stat-box">
                  <span className="stat-icon">📊</span>
                  <span className="stat-label">총 조과</span>
                  <span className="stat-value">{myStats.total_catches || 0}마리</span>
                </div>
                <div className="stat-box">
                  <span className="stat-icon">🏆</span>
                  <span className="stat-label">최대어</span>
                  <span className="stat-value">{myStats.max_size?.toFixed(1) || '-'}cm</span>
                </div>
                <div className="stat-box">
                  <span className="stat-icon">📏</span>
                  <span className="stat-label">평균 크기</span>
                  <span className="stat-value">{myStats.avg_size?.toFixed(1) || '-'}cm</span>
                </div>
                <div className="stat-box">
                  <span className="stat-icon">❤️</span>
                  <span className="stat-label">좋아요</span>
                  <span className="stat-value">{myStats.like_count || 0}개</span>
                </div>
              </div>

              <div className="score-section">
                <h4>종합 점수</h4>
                <div className="score-bar">
                  <div className="score-progress" style={{width: `${Math.min((myStats.score || 0) / 10, 100)}%`}}></div>
                </div>
                <p className="score-text">{myStats.score || 0}점 / 1000점</p>
              </div>

              <div className="charts-section">
                {(() => {
                  // 데이터 분석 함수들
                  const getTideData = () => {
                    const tideMap = {}
                    records.forEach(r => {
                      if (r.tide_number) {
                        const tide = `${r.tide_number}물`
                        tideMap[tide] = (tideMap[tide] || 0) + 1
                      }
                    })
                    return Object.entries(tideMap).map(([name, count]) => ({ name, 건수: count }))
                  }

                  const getTempData = () => {
                    const tempMap = {}
                    records.forEach(r => {
                      if (r.water_temp) {
                        const temp = Math.round(r.water_temp / 2) * 2
                        const label = `${temp}°C`
                        tempMap[label] = (tempMap[label] || 0) + 1
                      }
                    })
                    return Object.entries(tempMap).sort((a, b) => parseInt(a[0]) - parseInt(b[0])).map(([name, count]) => ({ name, 건수: count }))
                  }

                  const getLocationData = () => {
                    const locMap = {}
                    records.forEach(r => {
                      const loc = r.spot_name || '미정'
                      locMap[loc] = (locMap[loc] || 0) + 1
                    })
                    return Object.entries(locMap).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([name, count]) => ({ name, 건수: count }))
                  }

                  const getTimeData = () => {
                    const timeMap = { '오전(5-11)': 0, '오후(12-17)': 0, '저녁(18-23)': 0 }
                    records.forEach(r => {
                      if (r.caught_at) {
                        const hour = new Date(r.caught_at).getHours()
                        if (hour < 12) timeMap['오전(5-11)']++
                        else if (hour < 18) timeMap['오후(12-17)']++
                        else timeMap['저녁(18-23)']++
                      }
                    })
                    return Object.entries(timeMap).map(([name, count]) => ({ name, 건수: count }))
                  }

                  const getSpeciesData = () => {
                    const specMap = {}
                    records.forEach(r => {
                      if (r.species) {
                        specMap[r.species] = (specMap[r.species] || 0) + 1
                      }
                    })
                    return Object.entries(specMap).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([name, count]) => ({ name, 건수: count }))
                  }

                  const chartHeight = 300
                  const tideData = getTideData()
                  const tempData = getTempData()
                  const locationData = getLocationData()
                  const timeData = getTimeData()
                  const speciesData = getSpeciesData()

                  return (
                    <>
                      {tideData.length > 0 && (
                        <div className="chart-container">
                          <h4>물때별 조과</h4>
                          <ResponsiveContainer width="100%" height={chartHeight}>
                            <BarChart data={tideData}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="name" />
                              <YAxis />
                              <Tooltip />
                              <Bar dataKey="건수" fill="#8884d8" />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      )}

                      {tempData.length > 0 && (
                        <div className="chart-container">
                          <h4>수온별 조과</h4>
                          <ResponsiveContainer width="100%" height={chartHeight}>
                            <BarChart data={tempData}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="name" />
                              <YAxis />
                              <Tooltip />
                              <Bar dataKey="건수" fill="#82ca9d" />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      )}

                      {locationData.length > 0 && (
                        <div className="chart-container">
                          <h4>위치별 조과 (상위 10개)</h4>
                          <ResponsiveContainer width="100%" height={chartHeight}>
                            <BarChart data={locationData}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                              <YAxis />
                              <Tooltip />
                              <Bar dataKey="건수" fill="#ffc658" />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      )}

                      {timeData.length > 0 && (
                        <div className="chart-container">
                          <h4>시간대별 조과</h4>
                          <ResponsiveContainer width="100%" height={chartHeight}>
                            <BarChart data={timeData}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="name" />
                              <YAxis />
                              <Tooltip />
                              <Bar dataKey="건수" fill="#ff7c7c" />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      )}

                      {speciesData.length > 0 && (
                        <div className="chart-container">
                          <h4>어종별 조과 (상위 8개)</h4>
                          <ResponsiveContainer width="100%" height={chartHeight}>
                            <BarChart data={speciesData}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                              <YAxis />
                              <Tooltip />
                              <Bar dataKey="건수" fill="#8dd1e1" />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      )}
                    </>
                  )
                })()}
              </div>
            </div>
          ) : (
            <div className="empty-message">
              <i className="fas fa-inbox"></i>
              <p>통계 데이터가 없습니다</p>
            </div>
          )}
        </div>
      )}

      {!loading && activeTab === 'rankings' && (
        <div className="rankings-section">
          {/* 등급 랭킹 */}
          <div className="ranking-card">
            <h3>📊 등급 랭킹</h3>
            {gradeRankings.length > 0 ? (
              <table className="ranking-table">
                <thead>
                  <tr>
                    <th>순위</th>
                    <th>사용자</th>
                    <th>등급</th>
                    <th>점수</th>
                  </tr>
                </thead>
                <tbody>
                  {gradeRankings.map((item, idx) => (
                    <tr key={idx}>
                      <td className="rank">{['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣'][idx] || `${idx + 1}`}</td>
                      <td className="user-name">{item.userId}</td>
                      <td>{item.grade}</td>
                      <td className="score">{item.score}점</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="no-data">데이터가 없습니다</p>
            )}
          </div>

          {/* 최대어 랭킹 */}
          <div className="ranking-card">
            <h3>🏆 최대어 랭킹</h3>
            {maxSizeRankings.length > 0 ? (
              <table className="ranking-table">
                <thead>
                  <tr>
                    <th>순위</th>
                    <th>사용자</th>
                    <th>어종</th>
                    <th>크기</th>
                  </tr>
                </thead>
                <tbody>
                  {maxSizeRankings.map((item, idx) => (
                    <tr key={idx}>
                      <td className="rank">{['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣'][idx] || `${idx + 1}`}</td>
                      <td className="user-name">{item.userId}</td>
                      <td>{item.species}</td>
                      <td className="size">{item.size?.toFixed(1)}cm</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="no-data">데이터가 없습니다</p>
            )}
          </div>

          {/* 다작 랭킹 */}
          <div className="ranking-card">
            <h3>🐟 다작 랭킹</h3>
            {countRankings.length > 0 ? (
              <table className="ranking-table">
                <thead>
                  <tr>
                    <th>순위</th>
                    <th>사용자</th>
                    <th>마리수</th>
                  </tr>
                </thead>
                <tbody>
                  {countRankings.map((item, idx) => (
                    <tr key={idx}>
                      <td className="rank">{['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣'][idx] || `${idx + 1}`}</td>
                      <td className="user-name">{item.userId}</td>
                      <td className="count">{item.count}마리</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="no-data">데이터가 없습니다</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default RecordsPage
