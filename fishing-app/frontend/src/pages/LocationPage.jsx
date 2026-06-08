import { useState } from 'react'
import './LocationPage.css'

const LOCATIONS = [
  { name: '인천', latitude: 37.4563, longitude: 126.7052 },
  { name: '태안', latitude: 36.7456, longitude: 126.2979 },
  { name: '서천', latitude: 36.2811, longitude: 126.6919 },
  { name: '군산', latitude: 35.9676, longitude: 126.7368 },
  { name: '목포', latitude: 34.8118, longitude: 126.3922 },
  { name: '여수', latitude: 34.7604, longitude: 127.6622 },
  { name: '통영', latitude: 34.8544, longitude: 128.4330 },
  { name: '부산', latitude: 35.1796, longitude: 129.0756 },
  { name: '울산', latitude: 35.5384, longitude: 129.3114 },
  { name: '포항', latitude: 36.0190, longitude: 129.3435 },
  { name: '강릉', latitude: 37.7519, longitude: 128.8761 },
  { name: '제주', latitude: 33.4996, longitude: 126.5312 },
]

function LocationPage({ onLocationChange }) {
  const [selectedLocation, setSelectedLocation] = useState(null)

  const handleLocationSelect = (location) => {
    setSelectedLocation(location.name)
    onLocationChange({
      latitude: location.latitude,
      longitude: location.longitude,
      name: location.name
    })
  }

  const handleGPSClick = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          onLocationChange({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            name: '현재 위치'
          })
          setSelectedLocation('current')
        },
        (error) => {
          alert('위치 정보를 가져올 수 없습니다: ' + error.message)
        }
      )
    } else {
      alert('이 브라우저는 GPS를 지원하지 않습니다')
    }
  }

  return (
    <div className="location-page">
      <div className="location-header">
        <h1>지역 설정</h1>
        <p className="subtitle">낚시할 지역을 선택하세요</p>
      </div>

      <div className="gps-section">
        <button className="btn-gps" onClick={handleGPSClick}>
          <i className="fas fa-location-dot"></i>
          현재 위치 자동 감지
        </button>
        {selectedLocation === 'current' && (
          <p className="selected-info">✓ 현재 위치로 설정되었습니다</p>
        )}
      </div>

      <div className="divider">또는</div>

      <div className="locations-section">
        <h3>한국 주요 낚시 지역</h3>
        <div className="locations-grid">
          {LOCATIONS.map((location) => (
            <button
              key={location.name}
              className={`location-btn ${selectedLocation === location.name ? 'selected' : ''}`}
              onClick={() => handleLocationSelect(location)}
            >
              <i className="fas fa-water"></i>
              <span>{location.name}</span>
              {selectedLocation === location.name && (
                <i className="fas fa-check"></i>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="info-box">
        <i className="fas fa-info-circle"></i>
        <p>선택한 지역의 날씨, 물때, 정보가 홈과 물때 페이지에 반영됩니다.</p>
      </div>
    </div>
  )
}

export default LocationPage
