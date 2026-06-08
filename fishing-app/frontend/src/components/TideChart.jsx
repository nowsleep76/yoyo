import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import './TideChart.css'

function TideChart({ latitude, longitude }) {
  const [tideData, setTideData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchTide = async () => {
      try {
        setLoading(true)
        const response = await fetch(
          `/api/tide?lat=${latitude}&lon=${longitude}`
        )
        const data = await response.json()
        setTideData(data)
        setError(null)
      } catch (err) {
        setError('물때 정보를 불러올 수 없습니다')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchTide()
  }, [latitude, longitude])

  if (loading) {
    return <div className="tide-card loading">로딩 중...</div>
  }

  if (error) {
    return <div className="tide-card error">{error}</div>
  }

  return (
    <div className="tide-card">
      <div className="tide-header">
        <h3>물때 정보</h3>
        <span className="tide-number">{tideData.today.description}</span>
      </div>

      <div className="tide-times">
        <h4>오늘 물때 시간</h4>
        <div className="times-list">
          {tideData.today.tide_times.map((time, idx) => (
            <span key={idx} className="time-badge">{time}</span>
          ))}
        </div>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={tideData.hourly}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis
              dataKey="hour"
              stroke="#999"
              tickFormatter={(hour) => `${hour}:00`}
            />
            <YAxis
              stroke="#999"
              label={{ value: '수위 (m)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip
              formatter={(value) => value.toFixed(2)}
              labelFormatter={(hour) => `${hour}:00`}
              contentStyle={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid #ddd',
                borderRadius: '4px'
              }}
            />
            <Line
              type="monotone"
              dataKey="height"
              stroke="#0066cc"
              dot={false}
              strokeWidth={2}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="tide-info">
        <p><i className="fas fa-info-circle"></i> 24시간 물때 변화 추이</p>
      </div>
    </div>
  )
}

export default TideChart
