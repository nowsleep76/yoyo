import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import exifr from 'exifr'
import './FishingMap.css'

function FishingMap({ latitude, longitude }) {
  const mapContainer = useRef(null)
  const map = useRef(null)
  const markersLayerRef = useRef(null)
  const seaMarkLayerRef = useRef(null)
  const depthLayerRef = useRef(null)
  const newPointModeRef = useRef(false)
  const tideControlRef = useRef(null)

  const [points, setPoints] = useState([])
  const [knownSpots, setKnownSpots] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [newPointMode, setNewPointMode] = useState(false)
  const [newPointName, setNewPointName] = useState('')
  const [newPointCoords, setNewPointCoords] = useState(null)
  const [newPointPhoto, setNewPointPhoto] = useState(null)
  const [gpsFromPhoto, setGpsFromPhoto] = useState(false)
  const [newPointReel, setNewPointReel] = useState('')
  const [newPointRod, setNewPointRod] = useState('')
  const [newPointTackle, setNewPointTackle] = useState('')
  const [newPointMemo, setNewPointMemo] = useState('')
  const [uploadingPhoto, setUploadingPhoto] = useState(false)
  const [showSeaMark, setShowSeaMark] = useState(false)
  const [showDepth, setShowDepth] = useState(false)
  const [allSpecies, setAllSpecies] = useState([])
  const [selectedSpecies, setSelectedSpecies] = useState(null)
  const [tideData, setTideData] = useState(null)
  const [currentHour, setCurrentHour] = useState(new Date().getHours())

  useEffect(() => {
    if (map.current) return

    if (mapContainer.current) {
      map.current = L.map(mapContainer.current).setView([latitude, longitude], 10)

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map.current)

      const userMarker = L.circleMarker([latitude, longitude], {
        radius: 8,
        fillColor: '#0066cc',
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
      }).addTo(map.current)
      userMarker.bindPopup('현재 위치')

      markersLayerRef.current = L.layerGroup().addTo(map.current)

      map.current.on('click', (e) => {
        if (newPointModeRef.current) {
          setNewPointCoords({
            lat: e.latlng.lat,
            lng: e.latlng.lng
          })
        }
      })
    }

    return () => {
      if (map.current) {
        map.current.remove()
        map.current = null
      }
    }
  }, [latitude, longitude])

  useEffect(() => {
    fetchPoints()
    fetchSpecies()
    fetchTideData()

    // 매 시간마다 현재 시간 업데이트
    const hourInterval = setInterval(() => {
      setCurrentHour(new Date().getHours())
    }, 60000)

    return () => clearInterval(hourInterval)
  }, [])

  useEffect(() => {
    if (selectedSpecies) {
      fetchKnownSpots(selectedSpecies)
    } else {
      fetchKnownSpots()
    }
  }, [selectedSpecies])

  useEffect(() => {
    // 지도 제어 요소 업데이트
    if (map.current && tideData) {
      updateTideControl()
    }
  }, [tideData, currentHour])

  const fetchPoints = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/points')
      const data = await response.json()
      setPoints(data)
      renderPoints(data)
      setError(null)
    } catch (err) {
      setError('포인트 정보를 불러올 수 없습니다')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const fetchKnownSpots = async (species = null) => {
    try {
      const url = species ? `/api/spots?species=${species}` : '/api/spots'
      const response = await fetch(url)
      const data = await response.json()
      setKnownSpots(data)
      renderKnownSpots(data)
    } catch (err) {
      console.error('알려진 포인트 로드 실패:', err)
    }
  }

  const fetchSpecies = async () => {
    try {
      const response = await fetch('/api/spots/species')
      const data = await response.json()
      setAllSpecies(data.species)
    } catch (err) {
      console.error('어종 목록 로드 실패:', err)
    }
  }

  const fetchTideData = async () => {
    try {
      const today = new Date().toISOString().split('T')[0]
      const response = await fetch(
        `/api/tide/hourly?lat=${latitude}&lon=${longitude}&date=${today}`
      )
      const data = await response.json()
      setTideData(data)
    } catch (err) {
      console.error('조석 데이터 로드 실패:', err)
    }
  }

  const updateTideControl = () => {
    if (!map.current || !tideData) return

    // 기존 제어 요소 제거
    if (tideControlRef.current) {
      map.current.removeControl(tideControlRef.current)
    }

    const current = tideData.hourly[currentHour] || tideData.hourly[0]
    const highTide = tideData.high_tides[0]
    const lowTide = tideData.low_tides[0]

    const controlHTML = `
      <div class="tide-control">
        <h4>🌊 조석 정보</h4>
        <div class="tide-current">
          <div class="current-info">
            <span class="time">${currentHour}:00</span>
            <span class="height">${current.height.toFixed(1)}m</span>
          </div>
        </div>
        ${highTide ? `
          <div class="tide-info high">
            <div class="tide-label">🔴 만조</div>
            <div class="tide-value">${highTide.label}</div>
            <div class="tide-value">${highTide.height.toFixed(1)}m</div>
          </div>
        ` : ''}
        ${lowTide ? `
          <div class="tide-info low">
            <div class="tide-label">🔵 간조</div>
            <div class="tide-value">${lowTide.label}</div>
            <div class="tide-value">${lowTide.height.toFixed(1)}m</div>
          </div>
        ` : ''}
        <div class="tide-scale">
          <div class="scale-title">수위 범위</div>
          <div class="scale-bar">
            <div class="scale-gradient"></div>
            <div class="scale-labels">
              <span>4.0m</span>
              <span>2.0m</span>
              <span>0.0m</span>
            </div>
          </div>
        </div>
      </div>
    `

    const TideControl = L.Control.extend({
      onAdd: () => {
        const div = L.DomUtil.create('div', '')
        div.innerHTML = controlHTML
        L.DomEvent.disableClickPropagation(div)
        return div
      }
    })

    tideControlRef.current = new TideControl({ position: 'topleft' })
    tideControlRef.current.addTo(map.current)
  }

  const renderPoints = (pointsList) => {
    if (!markersLayerRef.current || !map.current) return

    markersLayerRef.current.clearLayers()

    pointsList.forEach((point) => {
      const markerColor = point.fish_types ? '#e74c3c' : '#f39c12'
      const marker = L.circleMarker([point.latitude, point.longitude], {
        radius: 6,
        fillColor: markerColor,
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
      }).addTo(markersLayerRef.current)

      let popupContent = `<div class="point-popup"><strong>${point.name}</strong>`

      if (point.photo_url) {
        popupContent += `<br/><img src="${point.photo_url}" style="width:150px;margin:8px 0;border-radius:4px;" />`
      }

      if (point.reel || point.rod || point.tackle) {
        popupContent += `<br/><small style="color:#666;"><strong>채비:</strong> `
        const tackleParts = []
        if (point.reel) tackleParts.push(`릴: ${point.reel}`)
        if (point.rod) tackleParts.push(`로드: ${point.rod}`)
        if (point.tackle) tackleParts.push(`채비: ${point.tackle}`)
        popupContent += tackleParts.join(' | ')
        popupContent += `</small>`
      }

      if (point.description) popupContent += `<br/><small>${point.description}</small>`

      popupContent += '</div>'

      marker.bindPopup(popupContent)
    })
  }

  const renderKnownSpots = (spotsList) => {
    if (!map.current) return

    spotsList.forEach((spot) => {
      const marker = L.marker([spot.latitude, spot.longitude], {
        icon: L.divIcon({
          html: `<div class="star-marker">★</div>`,
          className: 'known-spot-marker',
          iconSize: [30, 30],
          iconAnchor: [15, 15]
        })
      }).addTo(markersLayerRef.current)

      let popupContent = `<div class="known-spot-popup"><strong>${spot.name}</strong>`
      popupContent += `<br/><small><strong>지역:</strong> ${spot.region}</small>`
      popupContent += `<br/><small><strong>어종:</strong> ${spot.fish_types}</small>`
      if (spot.description) popupContent += `<br/><small>${spot.description}</small>`
      popupContent += '</div>'

      marker.bindPopup(popupContent)
    })
  }

  const handlePhotoChange = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setNewPointPhoto(file)
    setGpsFromPhoto(false)

    try {
      const gps = await exifr.gps(file)
      if (gps?.latitude && gps?.longitude) {
        setNewPointCoords({
          lat: gps.latitude,
          lng: gps.longitude
        })
        setGpsFromPhoto(true)
        if (map.current) {
          map.current.setView([gps.latitude, gps.longitude], 14)
        }
      }
    } catch (_) {
      console.log('사진에서 GPS 정보를 찾을 수 없습니다')
    }
  }

  const handleToggleSeaMark = () => {
    if (seaMarkLayerRef.current) {
      map.current.removeLayer(seaMarkLayerRef.current)
      seaMarkLayerRef.current = null
      setShowSeaMark(false)
    } else {
      seaMarkLayerRef.current = L.tileLayer(
        'https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png',
        {
          attribution: '© OpenSeaMap',
          maxZoom: 18
        }
      ).addTo(map.current)
      setShowSeaMark(true)
    }
  }

  const handleToggleDepth = () => {
    if (depthLayerRef.current) {
      map.current.removeLayer(depthLayerRef.current)
      depthLayerRef.current = null
      setShowDepth(false)
    } else {
      depthLayerRef.current = L.tileLayer.wms(
        'https://www.gebco.net/data_and_products/gebco_web_services/web_map_service/mapserv',
        {
          layers: 'GEBCO_2023_Grid',
          transparent: true,
          format: 'image/png',
          attribution: 'GEBCO'
        }
      ).addTo(map.current)
      setShowDepth(true)
    }
  }

  const handleUploadPhoto = async (file) => {
    if (!file) return ''

    try {
      setUploadingPhoto(true)
      const formData = new FormData()
      formData.append('image', file)

      const response = await fetch('/api/points/upload', {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        return data.url
      }
      return ''
    } catch (err) {
      console.error('사진 업로드 실패:', err)
      return ''
    } finally {
      setUploadingPhoto(false)
    }
  }

  const handleAddPoint = async () => {
    if (!newPointName.trim() || !newPointCoords) {
      alert('포인트명과 위치를 지정해주세요')
      return
    }

    try {
      let photoUrl = ''
      if (newPointPhoto) {
        photoUrl = await handleUploadPhoto(newPointPhoto)
      }

      const response = await fetch('/api/points', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newPointName,
          latitude: newPointCoords.lat,
          longitude: newPointCoords.lng,
          description: '',
          fish_types: '',
          photo_url: photoUrl,
          reel: newPointReel,
          rod: newPointRod,
          tackle: newPointTackle,
          rig_memo: newPointMemo
        })
      })

      if (response.ok) {
        setNewPointName('')
        setNewPointCoords(null)
        setNewPointPhoto(null)
        setGpsFromPhoto(false)
        setNewPointReel('')
        setNewPointRod('')
        setNewPointTackle('')
        setNewPointMemo('')
        setNewPointMode(false)
        newPointModeRef.current = false
        await fetchPoints()
      }
    } catch (err) {
      alert('포인트 추가에 실패했습니다')
      console.error(err)
    }
  }

  const handleToggleNewPointMode = () => {
    const newMode = !newPointMode
    setNewPointMode(newMode)
    newPointModeRef.current = newMode
    if (!newMode) {
      setNewPointCoords(null)
      setNewPointName('')
      setNewPointPhoto(null)
      setGpsFromPhoto(false)
    }
  }

  return (
    <div className="map-card">
      <div className="map-header">
        <h3>낚시 포인트 지도</h3>
        <button
          className={`btn-add-point ${newPointMode ? 'active' : ''}`}
          onClick={handleToggleNewPointMode}
        >
          <i className="fas fa-plus"></i>
          {newPointMode ? '취소' : '포인트 추가'}
        </button>
      </div>

      <div className="map-tools">
        <div className="tool-group">
          <button
            className={`btn-tool ${showSeaMark ? 'active' : ''}`}
            onClick={handleToggleSeaMark}
            title="항로표지/수심 사운딩 표시"
          >
            <i className="fas fa-water"></i>
            항로표지
          </button>
          <button
            className={`btn-tool ${showDepth ? 'active' : ''}`}
            onClick={handleToggleDepth}
            title="해저 수심 표시"
          >
            <i className="fas fa-droplet"></i>
            수심지도
          </button>
        </div>

        {allSpecies.length > 0 && (
          <div className="species-filter">
            <button
              className={`species-chip ${!selectedSpecies ? 'active' : ''}`}
              onClick={() => setSelectedSpecies(null)}
            >
              전체
            </button>
            {allSpecies.map((species) => (
              <button
                key={species}
                className={`species-chip ${selectedSpecies === species ? 'active' : ''}`}
                onClick={() => setSelectedSpecies(species)}
              >
                {species}
              </button>
            ))}
          </div>
        )}
      </div>

      {newPointMode && (
        <div className="add-point-form">
          <div className="form-group">
            <input
              type="text"
              placeholder="포인트명 입력"
              value={newPointName}
              onChange={(e) => setNewPointName(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>📷 사진 (선택사항)</label>
            <input
              type="file"
              accept="image/*"
              onChange={handlePhotoChange}
            />
            {newPointPhoto && (
              <p className="file-info">
                ✓ {newPointPhoto.name}
                {gpsFromPhoto && <span className="gps-badge">📍 GPS 자동 감지됨</span>}
              </p>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>🎣 사용릴</label>
              <input
                type="text"
                placeholder="예: 베이트릴"
                value={newPointReel}
                onChange={(e) => setNewPointReel(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>🪝 로드</label>
              <input
                type="text"
                placeholder="예: 2.7m"
                value={newPointRod}
                onChange={(e) => setNewPointRod(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label>🧵 채비</label>
            <input
              type="text"
              placeholder="예: 외바늘, 두바늘, 찌낚시"
              value={newPointTackle}
              onChange={(e) => setNewPointTackle(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>📝 채비 메모</label>
            <textarea
              placeholder="채비에 대한 추가 설명 (선택사항)"
              value={newPointMemo}
              onChange={(e) => setNewPointMemo(e.target.value)}
              rows="3"
            />
          </div>

          {newPointCoords && (
            <div className="coords-display">
              선택된 위치: ({newPointCoords.lat.toFixed(4)}, {newPointCoords.lng.toFixed(4)})
            </div>
          )}

          <button
            className="btn-confirm"
            onClick={handleAddPoint}
            disabled={!newPointName.trim() || !newPointCoords || uploadingPhoto}
          >
            {uploadingPhoto ? '사진 업로드 중...' : '포인트 저장'}
          </button>

          <p className="info-text">💡 {gpsFromPhoto ? '사진에서 위치를 가져왔습니다' : '지도를 클릭하여 포인트 위치를 선택하세요'}</p>
        </div>
      )}

      <div
        ref={mapContainer}
        className="map-container"
        style={{ height: '400px', width: '100%' }}
      />

      {showDepth && (
        <div className="depth-legend">
          <strong>수심 범례</strong>
          <div className="legend-items">
            <span><i style={{ background: '#0099ff' }}></i> 0~10m</span>
            <span><i style={{ background: '#0066ff' }}></i> 10~30m</span>
            <span><i style={{ background: '#0033ff' }}></i> 30~50m</span>
            <span><i style={{ background: '#000099' }}></i> 50m+</span>
          </div>
        </div>
      )}

      {loading && <div className="map-status">로딩 중...</div>}
      {error && <div className="map-status error">{error}</div>}
      {!loading && !error && (
        <div className="map-status">
          포인트 {points.length}개 | 명소 {knownSpots.length}개 (★)
        </div>
      )}
    </div>
  )
}

export default FishingMap
