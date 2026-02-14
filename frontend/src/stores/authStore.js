import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../utils/api'

const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,
      
      login: async (email, password) => {
        set({ isLoading: true })
        try {
          const response = await api.post('/auth/login', { email, password })
          const { user, token } = response.data
          
          set({ 
            user, 
            token, 
            isLoading: false 
          })
          
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`
          return { success: true }
        } catch (error) {
          set({ isLoading: false })
          return { 
            success: false, 
            error: error.response?.data?.message || 'Login failed' 
          }
        }
      },
      
      register: async (userData) => {
        set({ isLoading: true })
        try {
          const response = await api.post('/auth/register', userData)
          const { user, token } = response.data
          
          set({ 
            user, 
            token, 
            isLoading: false 
          })
          
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`
          return { success: true }
        } catch (error) {
          set({ isLoading: false })
          return { 
            success: false, 
            error: error.response?.data?.message || 'Registration failed' 
          }
        }
      },
      
      logout: () => {
        set({ user: null, token: null })
        delete api.defaults.headers.common['Authorization']
      },
      
      checkAuth: async () => {
        const { token } = get()
        if (!token) {
          set({ isLoading: false })
          return
        }
        
        set({ isLoading: true })
        try {
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`
          const response = await api.get('/auth/me')
          set({ 
            user: response.data.user, 
            isLoading: false 
          })
        } catch (error) {
          set({ user: null, token: null, isLoading: false })
          delete api.defaults.headers.common['Authorization']
        }
      },
      
      updateProfile: async (userData) => {
        try {
          const response = await api.put('/auth/profile', userData)
          set({ user: response.data.user })
          return { success: true }
        } catch (error) {
          return { 
            success: false, 
            error: error.response?.data?.message || 'Profile update failed' 
          }
        }
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user, token: state.token })
    }
  )
)

export { useAuthStore }
