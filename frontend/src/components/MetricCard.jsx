import React from 'react'
import { ArrowUp, ArrowDown, Minus } from 'lucide-react'

export default function MetricCard({ title, value, change, trend, icon: Icon, format, color }) {
  const formatValue = (val) => {
    if (format === 'currency') {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(val)
    }
    return new Intl.NumberFormat('en-US').format(val)
  }

  const getTrendIcon = () => {
    if (trend === 'up') return <ArrowUp className="w-4 h-4" />
    if (trend === 'down') return <ArrowDown className="w-4 h-4" />
    return <Minus className="w-4 h-4" />
  }

  const getTrendColor = () => {
    if (trend === 'up') return 'text-green-400'
    if (trend === 'down') return 'text-red-600'
    return 'text-muted-foreground'
  }
  
  const getIconColor = () => {
    const colors = {
      green: 'text-green-300 bg-green-500/10 border border-green-500/20',
      blue: 'text-green-300 bg-green-500/10 border border-green-500/20',
      purple: 'text-green-300 bg-green-500/10 border border-green-500/20',
      red: 'text-red-300 bg-red-500/10 border border-red-500/20',
    }
    return colors[color] || 'text-muted-foreground bg-gray-500/10 border border-border'
  }

  return (
    <div className="metric-card">
      <div className="flex items-center justify-between">
        <div>
          <p className="metric-label">{title}</p>
          <p className="metric-value">{formatValue(value)}</p>
        </div>
        <div className={`p-3 rounded-lg ${getIconColor()}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
      <div className="flex items-center mt-4">
        <span className={`metric-change ${getTrendColor()} flex items-center`}>
          {getTrendIcon()}
          {Math.abs(change)}%
        </span>
        <span className="text-sm text-muted-foreground ml-2">vs last period</span>
      </div>
    </div>
  )
}
