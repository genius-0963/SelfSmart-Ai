import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import io from 'socket.io-client'
import api from '../utils/api'

const useChatStore = create(
  subscribeWithSelector((set, get) => ({
    messages: [],
    isTyping: false,
    isConnected: false,
    currentSession: { id: 'default', name: 'Default Session', title: 'New Chat', created_at: new Date().toISOString() },
    sessions: [{ id: 'default', name: 'Default Session', title: 'New Chat', created_at: new Date().toISOString() }],
    socket: null,
    
    // Socket connection
    connectSocket: () => {
      const socket = io()
      
      socket.on('connect', () => {
        console.log('Connected to chat server')
        set({ isConnected: true })
      })
      
      socket.on('disconnect', () => {
        console.log('Disconnected from chat server')
        set({ isConnected: false })
      })
      
      socket.on('typing', (isTyping) => {
        set({ isTyping })
      })
      
      socket.on('message', (message) => {
        set(state => ({
          messages: [...state.messages, message]
        }))
      })
      
      set({ socket })
    },
    
    disconnectSocket: () => {
      const { socket } = get()
      if (socket) {
        socket.disconnect()
        set({ socket: null, isConnected: false })
      }
    },
    
    // Chat sessions
    loadSessions: async () => {
      // Simplified - just use default session
      set({ sessions: [{ id: 'default', name: 'Default Session', title: 'New Chat', created_at: new Date().toISOString() }] })
    },
    
    createSession: async () => {
      // Simplified - just return default session
      const defaultSession = { id: 'default', name: 'Default Session', title: 'New Chat', created_at: new Date().toISOString() }
      set({ 
        currentSession: defaultSession,
        messages: []
      })
      return defaultSession
    },
    
    setCurrentSession: (session) => {
      set({ currentSession: session })
      if (session) {
        get().loadMessages(session.id)
      } else {
        set({ messages: [] })
      }
    },
    
    // Messages
    loadMessages: async (sessionId) => {
      // Simplified - start with empty messages
      set({ messages: [] })
    },
    
    sendMessage: async (content, includeProducts = false) => {
      const { currentSession, socket } = get()
      if (!currentSession) return
      
      const userMessage = {
        id: Date.now(),
        content,
        role: 'user',
        timestamp: new Date().toISOString()
      }
      
      set(state => ({
        messages: [...state.messages, userMessage]
      }))
      
      // Show typing indicator
      set({ isTyping: true })
      
      try {
        const endpoint = includeProducts ? '/api/products/chat' : '/api/chat'
        const response = await api.post(endpoint, {
          query: content,
          session_id: currentSession.id
        })
        
        const aiMessage = {
          id: Date.now() + 1,
          content: response.data.response,
          role: 'assistant',
          timestamp: new Date().toISOString(),
          productSuggestions: response.data.product_suggestions || []
        }
        
        set(state => ({
          messages: [...state.messages, aiMessage],
          isTyping: false
        }))
        
        // Emit via socket for real-time updates
        if (socket?.connected) {
          socket.emit('message', aiMessage)
        }
        
      } catch (error) {
        console.error('Backend connection failed:', error)
        set({ isTyping: false })
        
        const errorMessage = {
          id: Date.now() + 1,
          content: `❌ Backend Connection Error: Unable to connect to the AI backend. Please ensure the backend server is running on http://localhost:8002\n\nError: ${error.message || 'Network error'}`,
          role: 'assistant',
          timestamp: new Date().toISOString(),
          isError: true
        }
        
        set(state => ({
          messages: [...state.messages, errorMessage]
        }))
      }
    },
    
    clearMessages: () => {
      set({ messages: [] })
    },
    
    deleteSession: async (sessionId) => {
      // Simplified - don't allow deleting default session
      if (sessionId === 'default') return
    }
  }))
)

export { useChatStore }
