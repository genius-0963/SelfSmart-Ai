import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  TrendingUp,
  TrendingDown,
  Package,
  DollarSign,
  AlertTriangle,
  Users,
  ShoppingCart,
  Brain,
  ArrowUp,
  ArrowDown
} from 'lucide-react'
import MetricCard from '../components/MetricCard'
import RevenueChart from '../components/RevenueChart'
import InventoryAlerts from '../components/InventoryAlerts'
import TopProducts from '../components/TopProducts'
import QuickActions from '../components/QuickActions'

export default function Dashboard() {
  const [metrics, setMetrics] = useState({
    revenue: { value: 609523, change: 12.5, trend: 'up' },
    orders: { value: 5512, change: 8.2, trend: 'up' },
    products: { value: 50, change: 2.1, trend: 'up' },
    alerts: { value: 5, change: -15.3, trend: 'down' }
  })

  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setLoading(false)
    }, 1000)
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner w-8 h-8"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
        <p className="text-muted-foreground">Welcome to SmartShelf AI - Your intelligent retail analytics platform</p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Revenue"
          value={metrics.revenue.value}
          change={metrics.revenue.change}
          trend={metrics.revenue.trend}
          icon={DollarSign}
          format="currency"
          color="green"
        />
        <MetricCard
          title="Total Orders"
          value={metrics.orders.value}
          change={metrics.orders.change}
          trend={metrics.orders.trend}
          icon={ShoppingCart}
          format="number"
          color="blue"
        />
        <MetricCard
          title="Active Products"
          value={metrics.products.value}
          change={metrics.products.change}
          trend={metrics.products.trend}
          icon={Package}
          format="number"
          color="purple"
        />
        <MetricCard
          title="Active Alerts"
          value={metrics.alerts.value}
          change={metrics.alerts.change}
          trend={metrics.alerts.trend}
          icon={AlertTriangle}
          format="number"
          color="red"
        />
      </div>

      {/* Charts and Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Chart */}
        <div className="bg-card border border-border p-6 rounded-lg">
          <h2 className="text-lg font-semibold text-foreground mb-4">Revenue Trend</h2>
          <RevenueChart />
        </div>

        {/* Top Products */}
        <div className="bg-card border border-border p-6 rounded-lg">
          <h2 className="text-lg font-semibold text-foreground mb-4">Top Products</h2>
          <TopProducts />
        </div>
      </div>

      {/* Alerts and Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Inventory Alerts */}
        <div className="lg:col-span-2">
          <InventoryAlerts />
        </div>

        {/* Quick Actions */}
        <div>
          <QuickActions />
        </div>
      </div>

      {/* AI Insights */}
      <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/5 p-6 rounded-lg border border-green-500/20">
        <div className="flex items-center space-x-3 mb-4">
          <Brain className="w-6 h-6 text-green-400" />
          <h2 className="text-lg font-semibold text-foreground">AI Insights</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-card border border-border p-4 rounded-lg">
            <p className="text-sm text-muted-foreground mb-1">Demand Forecast</p>
            <p className="font-medium text-foreground">15% increase expected next month</p>
          </div>
          <div className="bg-card border border-border p-4 rounded-lg">
            <p className="text-sm text-muted-foreground mb-1">Pricing Opportunity</p>
            <p className="font-medium text-foreground">8 products need price adjustments</p>
          </div>
          <div className="bg-card border border-border p-4 rounded-lg">
            <p className="text-sm text-muted-foreground mb-1">Inventory Health</p>
            <p className="font-medium text-foreground">87% optimal stock levels</p>
          </div>
        </div>
      </div>
    </div>
  )
}
