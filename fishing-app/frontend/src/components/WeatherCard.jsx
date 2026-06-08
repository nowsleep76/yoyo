import { useEffect, useState } from 'react'
import './WeatherCard.css'

function WeatherCard({ latitude, longitude }) {
  const [weather, setWeather] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchWeather = async () => {
      try {
        setLoading(true)
        const response = await fetch(
          `/api/weather?lat=${latitude}&lon=${longitude}`
        )
        const data = await response.json()
        setWeather(data)
        setError(null)
      } catch (err) {
        setError('날씨 정보를 불러올 수 없습니다')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchWeather()
  }, [latitude, longitude])

  if (loading) {
    return <div className="weather-card loading">로딩 중...</div>
  }

  if (error) {
    return <div className="weather-card error">{error}</div>
  }

  return (
    <div className="weather-card">
      <div className="weather-header">
        <h3>날씨 정보</h3>
        <span className="location">{weather.location}</span>
      </div>

      <div className="weather-main">
        <div className="temp-display">
          <span className="temperature">{Math.round(weather.temperature)}°C</span>
          <span className="weather-status">{weather.weather}</span>
        </div>
      </div>

      <div className="weather-details">
        <div className="detail-item">
          <div className="detail-label">풍속</div>
          <div className="detail-value">
            <i className="fas fa-wind"></i>
            {weather.wind_speed} m/s
          </div>
        </div>
        <div className="detail-item">
          <div className="detail-label">풍향</div>
          <div className="detail-value">
            <i className="fas fa-compass"></i>
            {weather.wind_direction}
          </div>
        </div>
        <div className="detail-item">
          <div className="detail-label">습도</div>
          <div className="detail-value">
            <i className="fas fa-droplet"></i>
            {weather.humidity}%
          </div>
        </div>
      </div>

      <div className="weather-timestamp">
        {new Date(weather.timestamp).toLocaleTimeString('ko-KR')}
      </div>
    </div>
  )
}

export default WeatherCard
