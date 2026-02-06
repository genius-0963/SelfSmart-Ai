import React from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Package,
  TrendingUp,
  DollarSign,
  BarChart3,
  Bot,
  X,
  Brain,
  ShoppingCart,
  AlertTriangle
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Inventory', href: '/inventory', icon: Package },
  { name: 'Forecasting', href: '/forecasting', icon: TrendingUp },
  { name: 'Pricing', href: '/pricing', icon: DollarSign },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'AI Copilot', href: '/copilot', icon: Bot },
]

export default function Sidebar({ onClose }) {
  const location = useLocation()

  return (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-card">
        <div className="flex items-center space-x-2">
          <Brain className="w-8 h-8 text-green-400" />
          <div>
            <h1 className="text-lg font-bold text-foreground">SmartShelf</h1>
            <p className="text-xs text-muted-foreground">AI Analytics</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-md lg:hidden hover:bg-gray-900"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href
          return (
            <NavLink
              key={item.name}
              to={item.href}
              onClick={onClose}
              className={`flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-green-500/10 text-green-300 border-r-2 border-green-500'
                  : 'text-muted-foreground hover:bg-gray-900 hover:text-foreground'
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span>{item.name}</span>
            </NavLink>
          )
        })}
      </nav>

      {/* Quick Stats */}
      <div className="p-4 border-t border-border bg-card">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
          Quick Stats
        </h3>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Active Products</span>
            <span className="text-sm font-medium text-foreground">50</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Alerts</span>
            <span className="text-sm font-medium text-red-400">5</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Revenue (30d)</span>
            <span className="text-sm font-medium text-green-400">$609K</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-border bg-card">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          <span className="text-xs text-muted-foreground">System Online</span>
        </div>
        <p className="text-xs text-muted-foreground mt-1">Version 1.0.0</p>
      </div>
    </div>
  )
}
