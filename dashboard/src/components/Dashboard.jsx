import { useState, useEffect } from 'react'
import Papa from 'papaparse'
import KPICard from './KPICard'
import StockChart from './StockChart'
import CategoryChart from './CategoryChart'
import '../styles/Dashboard.css'

function Dashboard() {
  const [dailyData, setDailyData] = useState([])
  const [monthlyData, setMonthlyData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const loadData = async () => {
      try {
        const dailyRes = await fetch('/daily_sales.csv')
        const dailyText = await dailyRes.text()
        const dailyParsed = Papa.parse(dailyText, { header: true, dynamicTyping: true })

        const monthlyRes = await fetch('/monthly_performance.csv')
        const monthlyText = await monthlyRes.text()
        const monthlyParsed = Papa.parse(monthlyText, { header: true, dynamicTyping: true })

        setDailyData(dailyParsed.data.filter(row => row.Date))
        setMonthlyData(monthlyParsed.data.filter(row => row.Month))
        setLoading(false)
      } catch (err) {
        setError(err.message)
        setLoading(false)
      }
    }

    loadData()
  }, [])

  if (loading) return <div className="loading">데이터 로딩 중...</div>
  if (error) return <div className="error">오류: {error}</div>

  // 최신 데이터 계산
  const latestDate = dailyData.length > 0 ? dailyData[dailyData.length - 1].Date : null
  const previousDate = dailyData.length > 1 ? dailyData[dailyData.length - 2].Date : null

  const todaySales = dailyData
    .filter(d => d.Date === latestDate)
    .reduce((sum, d) => sum + d.Sales, 0)

  const yesterdaySales = dailyData
    .filter(d => d.Date === previousDate)
    .reduce((sum, d) => sum + d.Sales, 0)

  const growthRate = yesterdaySales > 0 ? ((todaySales - yesterdaySales) / yesterdaySales * 100) : 0

  const totalOrders = dailyData
    .filter(d => d.Date === latestDate)
    .reduce((sum, d) => sum + d.OrderCount, 0)

  const totalUsers = dailyData
    .filter(d => d.Date === latestDate)
    .reduce((sum, d) => sum + d.Users, 0)

  // 차트용 데이터 변환
  const chartData = dailyData.reduce((acc, item) => {
    const existing = acc.find(d => d.date === item.Date)
    if (existing) {
      existing.sales += item.Sales
      existing.orders += item.OrderCount
    } else {
      acc.push({
        date: item.Date,
        sales: item.Sales,
        orders: item.OrderCount,
        users: item.Users
      })
    }
    return acc
  }, []).sort((a, b) => new Date(a.date) - new Date(b.date))

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🏪 홈앤쇼핑 대시보드</h1>
        <p className="last-updated">마지막 업데이트: {latestDate}</p>
      </header>

      <section className="kpi-section">
        <div className="kpi-grid">
          <KPICard
            title="오늘 매출"
            value={todaySales}
            unit="₩"
            type="sales"
          />
          <KPICard
            title="전일 매출"
            value={yesterdaySales}
            unit="₩"
            type="sales"
          />
          <KPICard
            title="성장률"
            value={growthRate}
            unit="%"
            type="growth"
            isPositive={growthRate >= 0}
          />
          <KPICard
            title="주문건수"
            value={totalOrders}
            unit="건"
            type="count"
          />
          <KPICard
            title="활성 사용자"
            value={totalUsers}
            unit="명"
            type="count"
          />
        </div>
      </section>

      <section className="chart-section">
        <h2>📈 일별 매출 추이</h2>
        <StockChart data={chartData} />
      </section>

      <section className="chart-section">
        <h2>🎯 카테고리별 매출 분석</h2>
        <CategoryChart dailyData={dailyData} />
      </section>
    </div>
  )
}

export default Dashboard
