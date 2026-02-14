import { Bell, Search, User } from 'lucide-react'
import { useState } from 'react'

export default function Header() {
  const [showProfile, setShowProfile] = useState(false)

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      {/* Search */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            placeholder="Search conversations..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-4">
        {/* Notifications */}
        <button className="relative p-2 text-gray-600 hover:bg-gray-50 rounded-lg transition-colors">
          <Bell size={20} />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>

        {/* User Profile */}
        <div className="relative">
          <button
            onClick={() => setShowProfile(!showProfile)}
            className="flex items-center gap-3 p-2 hover:bg-gray-50 rounded-lg transition-colors"
          >
            <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
              <User size={16} className="text-white" />
            </div>
            <div className="text-left">
              <p className="text-sm font-medium text-gray-900">Guest User</p>
              <p className="text-xs text-gray-500">guest@smartshelf.ai</p>
            </div>
          </button>

          {/* Profile Dropdown */}
          {showProfile && (
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
              <div className="px-4 py-2 border-b border-gray-200">
                <p className="text-sm font-medium text-gray-900">Guest User</p>
                <p className="text-xs text-gray-500">guest@smartshelf.ai</p>
              </div>
              <a
                href="/settings"
                className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                Settings
              </a>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
