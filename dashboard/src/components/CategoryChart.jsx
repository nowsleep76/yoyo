import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'
import '../styles/CategoryChart.css'

function CategoryChart({ dailyData }) {
  // 카테고리별 매출 집계
  const categoryData = dailyData.reduce((acc, item) => {
    const existing = acc.find(d => d.name === item.Category)
    if (existing) {
      existing.sales += item.Sales
      existing.orders += item.OrderCount
    } else {
      acc.push({
        name: item.Category,
        sales: item.Sales,
        orders: item.OrderCount
      })
    }
    return acc
  }, []).sort((a, b) => b.sales - a.sales)

  const colors = ['#4472C4', '#70AD47', '#FFC000', '#ED7D31', '#A5A5A5']

  const formatYAxis = (value) => {
    if (value >= 1000000) {
      return (value / 1000000).toFixed(0) + 'M'
    }
    return (value / 1000).toFixed(0) + 'K'
  }

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="custom-tooltip">
          <p className="tooltip-category">{data.name}</p>
          <p className="tooltip-sales">매출: ₩{(data.sales).toLocaleString('ko-KR')}</p>
          <p className="tooltip-orders">주문: {(data.orders).toLocaleString('ko-KR')}건</p>
        </div>
      )
    }
    return null
  }

  const PieTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      const total = categoryData.reduce((sum, d) => sum + d.sales, 0)
      const percent = ((data.sales / total) * 100).toFixed(1)
      return (
        <div className="custom-tooltip">
          <p className="tooltip-category">{data.name}</p>
          <p className="tooltip-sales">₩{(data.sales).toLocaleString('ko-KR')}</p>
          <p className="tooltip-percent">{percent}%</p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="category-chart-container">
      <div className="category-bar">
        <h3>카테고리별 매출 현황</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={categoryData} margin={{ top: 20, right: 30, left: 0, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="name"
              angle={-45}
              textAnchor="end"
              height={80}
              tick={{ fontSize: 12 }}
            />
            <YAxis
              tickFormatter={formatYAxis}
              tick={{ fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar dataKey="sales" fill="#4472C4" name="매출" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="category-pie">
        <h3>매출 비중</h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={categoryData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, value, index }) => {
                const total = categoryData.reduce((sum, d) => sum + d.sales, 0)
                const percent = ((value / total) * 100).toFixed(1)
                return `${name} ${percent}%`
              }}
              outerRadius={100}
              fill="#8884d8"
              dataKey="sales"
            >
              {categoryData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
              ))}
            </Pie>
            <Tooltip content={<PieTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default CategoryChart
