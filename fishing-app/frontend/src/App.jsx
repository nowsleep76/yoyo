import { useState, useEffect } from 'react'
import Navbar from './components/Navbar'
import TidePage from './pages/TidePage'
import ExplorePage from './pages/ExplorePage'
import RecordsPage from './pages/RecordsPage'
import ProfilePage from './pages/ProfilePage'
import { StorageUtils } from './utils/storage'
import './App.css'

function App() {
  const [currentPage, setCurrentPage] = useState('tide')
  const [userId, setUserId] = useState(() => {
    return StorageUtils.getItem('userId') || null
  })
  const [location, setLocation] = useState({
    latitude: 37.5665,
    longitude: 126.9780,
    name: '내 위치'
  })

  // 현재 위치 요청 (선택사항 - 권한 거부해도 상관없음)
  useEffect(() => {
    if (navigator.geolocation && location.name === '내 위치') {
      // 타임아웃 3초 - 너무 오래 기다리지 않음
      const timeoutId = setTimeout(() => {
        console.warn('위치 정보 요청 타임아웃 (3초)')
      }, 3000)

      navigator.geolocation.getCurrentPosition(
        (position) => {
          clearTimeout(timeoutId)
          setLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            name: '현재 위치'
          })
          console.log('현재 위치 획득 성공')
        },
        (error) => {
          clearTimeout(timeoutId)
          console.warn('위치 정보 요청 실패:', error.code, error.message)
          // 실패해도 기본값(서울)으로 계속 진행
        },
        {
          enableHighAccuracy: false, // 배터리 절약
          timeout: 3000, // 3초 타임아웃
          maximumAge: 3600000 // 1시간 캐시 사용
        }
      )

      return () => clearTimeout(timeoutId)
    }
  }, [])

  const handleLocationChange = (newLocation) => {
    setLocation(newLocation)
  }

  return (
    <div className="app">
      <Navbar currentPage={currentPage} onPageChange={setCurrentPage} />
      {currentPage !== 'profile' && currentPage !== 'tide' && (
        <div className="location-header">
          <div className="location-info">
            <i className="fas fa-map-marker-alt"></i>
            <span className="location-name">{location.name}</span>
            <span className="location-coords">({location.latitude.toFixed(4)}, {location.longitude.toFixed(4)})</span>
          </div>
        </div>
      )}
      <main className="main-content">
        {currentPage === 'tide' && <TidePage location={location} onLocationChange={handleLocationChange} />}
        {currentPage === 'explore' && <ExplorePage location={location} onLocationChange={handleLocationChange} />}
        {currentPage === 'records' && <RecordsPage location={location} userId={userId} />}
        {currentPage === 'profile' && <ProfilePage userId={userId} setUserId={setUserId} />}
      </main>
    </div>
  )
}

export default App
