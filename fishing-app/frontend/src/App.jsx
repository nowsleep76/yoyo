import { useState, useEffect } from 'react'
import Navbar from './components/Navbar'
import TidePage from './pages/TidePage'
import ExplorePage from './pages/ExplorePage'
import RecordsPage from './pages/RecordsPage'
import './App.css'

function App() {
  const [currentPage, setCurrentPage] = useState('tide')
  const [location, setLocation] = useState({
    latitude: 37.5665,
    longitude: 126.9780,
    name: '내 위치'
  })

  useEffect(() => {
    if (navigator.geolocation && location.name === '내 위치') {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            name: '현재 위치'
          })
        },
        (error) => {
          console.warn('위치 정보를 가져올 수 없습니다:', error)
        }
      )
    }
  }, [])

  const handleLocationChange = (newLocation) => {
    setLocation(newLocation)
  }

  return (
    <div className="app">
      <Navbar currentPage={currentPage} onPageChange={setCurrentPage} />
      <main className="main-content">
        {currentPage === 'tide' && <TidePage location={location} onLocationChange={handleLocationChange} />}
        {currentPage === 'explore' && <ExplorePage location={location} />}
        {currentPage === 'records' && <RecordsPage location={location} />}
      </main>
    </div>
  )
}

export default App
