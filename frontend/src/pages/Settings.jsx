import { useState } from 'react'
import { Bell, Lock, Palette, Globe, Database } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Settings() {
  const [activeTab, setActiveTab] = useState('profile')
  const [isLoading, setIsLoading] = useState(false)
  
  const [profileData, setProfileData] = useState({
    name: 'Guest User',
    email: 'guest@smartshelf.ai',
    bio: ''
  })

  const [preferences, setPreferences] = useState({
    notifications: true,
    emailUpdates: false,
    darkMode: false,
    language: 'en',
    autoSave: true
  })

  const tabs = [
    { id: 'profile', label: 'Profile', icon: Bell },
    { id: 'security', label: 'Security', icon: Lock },
    { id: 'preferences', label: 'Preferences', icon: Palette },
    { id: 'data', label: 'Data & Privacy', icon: Database },
  ]

  const handleProfileUpdate = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    
    // Simulate profile update
    setTimeout(() => {
      toast.success('Profile updated successfully!')
      setIsLoading(false)
    }, 500)
  }

  const handlePreferenceChange = (key, value) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value
    }))
    toast.success('Preference updated!')
  }

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>
        
        <div className="flex gap-6">
          {/* Sidebar */}
          <div className="w-64">
            <nav className="space-y-1">
              {tabs.map((tab) => {
                const Icon = tab.icon
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2 text-left rounded-lg transition-colors ${
                      activeTab === tab.id
                        ? 'bg-primary-50 text-primary-600'
                        : 'text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <Icon size={18} />
                    <span className="font-medium">{tab.label}</span>
                  </button>
                )
              })}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Profile Information</h2>
                
                <form onSubmit={handleProfileUpdate} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Full Name
                    </label>
                    <input
                      type="text"
                      value={profileData.name}
                      onChange={(e) => setProfileData(prev => ({ ...prev, name: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={profileData.email}
                      onChange={(e) => setProfileData(prev => ({ ...prev, email: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Bio
                    </label>
                    <textarea
                      value={profileData.bio}
                      onChange={(e) => setProfileData(prev => ({ ...prev, bio: e.target.value }))}
                      rows={4}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="Tell us about yourself..."
                    />
                  </div>
                  
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                  >
                    {isLoading ? 'Saving...' : 'Save Changes'}
                  </button>
                </form>
              </div>
            )}

            {/* Security Tab */}
            {activeTab === 'security' && (
              <div className="space-y-6">
                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">Change Password</h2>
                  
                  <form className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Current Password
                      </label>
                      <input
                        type="password"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        New Password
                      </label>
                      <input
                        type="password"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Confirm New Password
                      </label>
                      <input
                        type="password"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                    </div>
                    
                    <button
                      type="submit"
                      className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                    >
                      Update Password
                    </button>
                  </form>
                </div>

                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">Two-Factor Authentication</h2>
                  <p className="text-gray-600 mb-4">
                    Add an extra layer of security to your account with 2FA.
                  </p>
                  <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                    Enable 2FA
                  </button>
                </div>
              </div>
            )}

            {/* Preferences Tab */}
            {activeTab === 'preferences' && (
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Preferences</h2>
                
                <div className="space-y-6">
                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">Notifications</h3>
                    <div className="space-y-3">
                      <label className="flex items-center justify-between">
                        <span className="text-gray-700">Push notifications</span>
                        <input
                          type="checkbox"
                          checked={preferences.notifications}
                          onChange={(e) => handlePreferenceChange('notifications', e.target.checked)}
                          className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                        />
                      </label>
                      
                      <label className="flex items-center justify-between">
                        <span className="text-gray-700">Email updates</span>
                        <input
                          type="checkbox"
                          checked={preferences.emailUpdates}
                          onChange={(e) => handlePreferenceChange('emailUpdates', e.target.checked)}
                          className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                        />
                      </label>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">Appearance</h3>
                    <div className="space-y-3">
                      <label className="flex items-center justify-between">
                        <span className="text-gray-700">Dark mode</span>
                        <input
                          type="checkbox"
                          checked={preferences.darkMode}
                          onChange={(e) => handlePreferenceChange('darkMode', e.target.checked)}
                          className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                        />
                      </label>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">Language</h3>
                    <select
                      value={preferences.language}
                      onChange={(e) => handlePreferenceChange('language', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="en">English</option>
                      <option value="es">Spanish</option>
                      <option value="fr">French</option>
                      <option value="de">German</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* Data & Privacy Tab */}
            {activeTab === 'data' && (
              <div className="space-y-6">
                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">Data Management</h2>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                      <div>
                        <h3 className="font-medium text-gray-900">Export your data</h3>
                        <p className="text-sm text-gray-600">Download all your conversations and settings</p>
                      </div>
                      <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                        Export
                      </button>
                    </div>
                    
                    <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                      <div>
                        <h3 className="font-medium text-gray-900">Delete your account</h3>
                        <p className="text-sm text-gray-600">Permanently remove your account and all data</p>
                      </div>
                      <button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
                        Delete Account
                      </button>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">Privacy Settings</h2>
                  
                  <div className="space-y-3">
                    <label className="flex items-center justify-between">
                      <span className="text-gray-700">Share usage analytics</span>
                      <input
                        type="checkbox"
                        defaultChecked={false}
                        className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                      />
                    </label>
                    
                    <label className="flex items-center justify-between">
                      <span className="text-gray-700">Personalized recommendations</span>
                      <input
                        type="checkbox"
                        defaultChecked={true}
                        className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                      />
                    </label>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
