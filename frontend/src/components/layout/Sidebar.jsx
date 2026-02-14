import { NavLink, useLocation } from 'react-router-dom'
import { 
  MessageSquare, 
  BarChart3, 
  Settings, 
  Plus, 
  Trash2,
  LogOut
} from 'lucide-react'
import { useChatStore } from '../../stores/chatStore'
import { useAuthStore } from '../../stores/authStore'
import { useState } from 'react'

export default function Sidebar() {
  const location = useLocation()
  const { sessions, currentSession, createSession, deleteSession, setCurrentSession } = useChatStore()
  const { logout } = useAuthStore()
  const [isCreating, setIsCreating] = useState(false)

  const handleNewChat = async () => {
    if (isCreating) return
    setIsCreating(true)
    await createSession()
    setIsCreating(false)
  }

  const handleDeleteSession = async (e, sessionId) => {
    e.preventDefault()
    e.stopPropagation()
    await deleteSession(sessionId)
  }

  const navItems = [
    { to: '/', icon: MessageSquare, label: 'Chat' },
    { to: '/analytics', icon: BarChart3, label: 'Analytics' },
    { to: '/settings', icon: Settings, label: 'Settings' },
  ]

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <button
          onClick={handleNewChat}
          disabled={isCreating}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
        >
          <Plus size={18} />
          {isCreating ? 'Creating...' : 'New Chat'}
        </button>
      </div>

      {/* Navigation */}
      <nav className="p-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.to || 
                          (item.to === '/' && location.pathname === '/')
          
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                isActive
                  ? 'bg-primary-50 text-primary-600'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              <Icon size={18} />
              <span className="font-medium">{item.label}</span>
            </NavLink>
          )
        })}
      </nav>

      {/* Chat Sessions */}
      <div className="flex-1 overflow-y-auto p-4">
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
          Recent Chats
        </h3>
        <div className="space-y-1">
          {sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => setCurrentSession(session)}
              className={`group flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${
                currentSession?.id === session.id
                  ? 'bg-primary-50 text-primary-600'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {session.title || 'New Chat'}
                </p>
                <p className="text-xs text-gray-500">
                  {new Date(session.created_at).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={(e) => handleDeleteSession(e, session.id)}
                className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* User Actions */}
      <div className="p-4 border-t border-gray-200">
        <button
          onClick={logout}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
        >
          <LogOut size={18} />
          <span className="font-medium">Logout</span>
        </button>
      </div>
    </div>
  )
}
