import WeatherCard from '../components/WeatherCard'
import TideChart from '../components/TideChart'
import FishingMap from '../components/FishingMap'
import './Home.css'

function Home({ location }) {
  return (
    <div className="home">
      <div className="home-header">
        <h1>낚시 정보 대시보드</h1>
        <p className="subtitle">
          {location.name} - {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}
        </p>
      </div>

      <div className="home-content">
        <WeatherCard latitude={location.latitude} longitude={location.longitude} />
        <TideChart latitude={location.latitude} longitude={location.longitude} />
        <FishingMap latitude={location.latitude} longitude={location.longitude} />
      </div>
    </div>
  )
}

export default Home
