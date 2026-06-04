import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import '../styles/StockChart.css'

function StockChart({ data }) {
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
          <p className="tooltip-date">{data.date}</p>
          <p className="tooltip-sales">매출: ₩{(data.sales).toLocaleString('ko-KR')}</p>
          <p className="tooltip-orders">주문건수: {(data.orders).toLocaleString('ko-KR')}건</p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="stock-chart">
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="date"
            angle={-45}
            textAnchor="end"
            height={80}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            tickFormatter={formatYAxis}
            tick={{ fontSize: 12 }}
            label={{ value: '금액 (₩)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ paddingTop: '20px' }} />
          <Bar
            dataKey="sales"
            fill="#4472C4"
            name="일일 매출"
            radius={[8, 8, 0, 0]}
            opacity={0.8}
          />
          <Line
            type="monotone"
            dataKey="sales"
            stroke="#70AD47"
            strokeWidth={2}
            name="매출 추세"
            dot={{ fill: '#70AD47', r: 4 }}
            activeDot={{ r: 6 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

export default StockChart
