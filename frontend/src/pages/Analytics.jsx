import { useState, useEffect } from 'react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

export default function Analytics() {
  const [timeRange, setTimeRange] = useState('7d')
  const [analyticsData, setAnalyticsData] = useState({
    conversations: [],
    userActivity: [],
    productPerformance: [],
    topCategories: []
  })

  useEffect(() => {
    // Mock data - replace with actual API call
    setAnalyticsData({
      conversations: [
        { date: '2024-01-01', count: 45 },
        { date: '2024-01-02', count: 52 },
        { date: '2024-01-03', count: 38 },
        { date: '2024-01-04', count: 65 },
        { date: '2024-01-05', count: 71 },
        { date: '2024-01-06', count: 58 },
        { date: '2024-01-07', count: 82 },
      ],
      userActivity: [
        { hour: '00:00', active_users: 12 },
        { hour: '04:00', active_users: 8 },
        { hour: '08:00', active_users: 45 },
        { hour: '12:00', active_users: 78 },
        { hour: '16:00', active_users: 92 },
        { hour: '20:00', active_users: 65 },
      ],
      productPerformance: [
        { category: 'Electronics', views: 1250, clicks: 320, conversion: 25.6 },
        { category: 'Clothing', views: 980, clicks: 210, conversion: 21.4 },
        { category: 'Home & Garden', views: 750, clicks: 180, conversion: 24.0 },
        { category: 'Sports', views: 620, clicks: 145, conversion: 23.4 },
        { category: 'Books', views: 540, clicks: 95, conversion: 17.6 },
      ],
      topCategories: [
        { name: 'Electronics', value: 35, color: '#3b82f6' },
        { name: 'Clothing', value: 28, color: '#10b981' },
        { name: 'Home & Garden', value: 20, color: '#f59e0b' },
        { name: 'Sports', value: 12, color: '#ef4444' },
        { name: 'Books', value: 5, color: '#8b5cf6' },
      ]
    })
  }, [timeRange])

  const stats = [
    { label: 'Total Conversations', value: '2,847', change: '+12.5%', positive: true },
    { label: 'Active Users', value: '1,234', change: '+8.2%', positive: true },
    { label: 'Product Clicks', value: '8,456', change: '+15.3%', positive: true },
    { label: 'Avg. Response Time', value: '1.2s', change: '-0.3s', positive: true },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600">Monitor your AI assistant performance and user engagement</p>
        </div>
        
        <div className="flex items-center gap-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </select>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white p-6 rounded-lg border border-gray-200">
            <p className="text-sm font-medium text-gray-600">{stat.label}</p>
            <p className="text-2xl font-bold text-gray-900 mt-2">{stat.value}</p>
            <div className="flex items-center mt-2">
              <span className={`text-sm font-medium ${
                stat.positive ? 'text-green-600' : 'text-red-600'
              }`}>
                {stat.change}
              </span>
              <span className="text-sm text-gray-500 ml-2">vs last period</span>
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Conversations Over Time */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Conversations Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analyticsData.conversations}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="count" 
                stroke="#3b82f6" 
                strokeWidth={2}
                name="Conversations"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* User Activity by Hour */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">User Activity by Hour</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analyticsData.userActivity}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="active_users" fill="#10b981" name="Active Users" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Product Performance */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Product Performance</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analyticsData.productPerformance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="views" fill="#8b5cf6" name="Views" />
              <Bar dataKey="clicks" fill="#f59e0b" name="Clicks" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top Categories */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Product Categories</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={analyticsData.topCategories}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {analyticsData.topCategories.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
