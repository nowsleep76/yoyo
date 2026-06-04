import '../styles/KPICard.css'

function KPICard({ title, value, unit, type, isPositive = true }) {
  const formatNumber = (num) => {
    if (Math.abs(num) >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M'
    }
    if (Math.abs(num) >= 1000) {
      return (num / 1000).toFixed(0) + 'K'
    }
    return Math.round(num).toLocaleString('ko-KR')
  }

  let icon = '📊'
  if (type === 'sales') icon = '💰'
  if (type === 'growth') icon = isPositive ? '📈' : '📉'
  if (type === 'count') icon = '📦'

  const displayValue = type === 'growth' ? value.toFixed(1) : formatNumber(value)

  return (
    <div className={`kpi-card kpi-${type}`}>
      <div className="kpi-icon">{icon}</div>
      <div className="kpi-content">
        <h3 className="kpi-title">{title}</h3>
        <div className={`kpi-value ${isPositive ? 'positive' : 'negative'}`}>
          {type === 'growth' && (isPositive ? '+' : '-')}
          {displayValue}
          <span className="kpi-unit">{unit}</span>
        </div>
      </div>
    </div>
  )
}

export default KPICard
