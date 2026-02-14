/**
 * SmartShelf AI - Enhanced Chat Store
 * Production-ready state management with persistence and error handling
 */

import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { persist } from 'zustand/middleware'
import io from 'socket.io-client'
import api from '../utils/api'

const useEnhancedChatStore = create(
  subscribeWithSelector(
    persist(
      (set, get) => ({
        // State
        messages: [],
        sessions: [],
        currentSessionId: null,
        isConnected: false,
        isTyping: false,
        isLoading: false,
        error: null,
        socket: null,
        connectionAttempts: 0,
        maxReconnectAttempts: 5,
        
        // Connection management
        connectSocket: () => {
          const { socket, connectionAttempts, maxReconnectAttempts } = get()
          
          if (socket?.connected) {
            console.log('Socket already connected')
            return
          }
          
          if (connectionAttempts >= maxReconnectAttempts) {
            console.log('Max reconnection attempts reached')
            set({ error: 'Unable to connect to chat server after multiple attempts' })
            return
          }
          
          const newSocket = io(process.env.REACT_APP_WS_URL || 'ws://localhost:8000', {
            transports: ['websocket'],
            upgrade: false,
            rememberUpgrade: false,
            timeout: 10000,
            forceNew: true
          })
          
          newSocket.on('connect', () => {
            console.log('Connected to chat server')
            set({ 
              isConnected: true, 
              error: null,
              connectionAttempts: 0 
            })
          })
          
          newSocket.on('disconnect', (reason) => {
            console.log('Disconnected from chat server:', reason)
            set({ isConnected: false })
            
            // Auto-reconnect logic
            if (reason === 'io server disconnect') {
              // Server disconnected, reconnect manually
              newSocket.connect()
            } else if (reason === 'ping timeout' || reason === 'transport close') {
              // Network issue, attempt reconnection
              const newAttempts = connectionAttempts + 1
              set({ connectionAttempts: newAttempts })
              
              if (newAttempts < maxReconnectAttempts) {
                setTimeout(() => {
                  get().connectSocket()
                }, Math.pow(2, newAttempts) * 1000) // Exponential backoff
              }
            }
          })
          
          newSocket.on('connect_error', (error) => {
            console.error('Connection error:', error)
            const newAttempts = connectionAttempts + 1
            set({ 
              error: `Connection failed (attempt ${newAttempts}/${maxReconnectAttempts})`,
              connectionAttempts: newAttempts
            })
            
            // Retry connection with exponential backoff
            if (newAttempts < maxReconnectAttempts) {
              setTimeout(() => {
                get().connectSocket()
              }, Math.pow(2, newAttempts) * 1000)
            }
          })
          
          newSocket.on('typing', (data) => {
            set({ isTyping: data.isTyping })
          })
          
          newSocket.on('message', (message) => {
            set(state => ({
              messages: [...state.messages, {
                ...message,
                id: message.id || Date.now(),
                timestamp: message.timestamp || new Date().toISOString()
              }]
            }))
          })
          
          newSocket.on('session_update', (sessionData) => {
            set(state => ({
              sessions: state.sessions.map(session =>
                session.id === sessionData.id
                  ? { ...session, ...sessionData }
                  : session
              )
            }))
          })
          
          newSocket.on('error', (error) => {
            console.error('Socket error:', error)
            set({ error: error.message || 'Socket connection error' })
          })
          
          set({ socket: newSocket })
        },
        
        disconnectSocket: () => {
          const { socket } = get()
          if (socket) {
            socket.disconnect()
            set({ 
              socket: null, 
              isConnected: false,
              connectionAttempts: 0
            })
          }
        },
        
        // Session management
        createSession: async (title = 'New Chat') => {
          try {
            set({ isLoading: true, error: null })
            
            const response = await api.post('/api/sessions', {
              title,
              user_id: 'web_user'
            })
            
            const newSession = response.data
            
            set(state => ({
              sessions: [...state.sessions, newSession],
              currentSessionId: newSession.id,
              messages: [],
              isLoading: false
            }))
            
            return newSession
            
          } catch (error) {
            console.error('Error creating session:', error)
            set({ 
              error: error.response?.data?.detail || 'Failed to create session',
              isLoading: false 
            })
            throw error
          }
        },
        
        loadSessions: async () => {
          try {
            set({ isLoading: true, error: null })
            
            const response = await api.get('/api/sessions')
            const sessions = response.data
            
            set({
              sessions,
              currentSessionId: sessions.length > 0 ? sessions[0].id : null,
              isLoading: false
            })
            
            // Load messages for current session
            if (sessions.length > 0) {
              get().loadMessages(sessions[0].id)
            }
            
          } catch (error) {
            console.error('Error loading sessions:', error)
            set({ 
              error: error.response?.data?.detail || 'Failed to load sessions',
              isLoading: false 
            })
          }
        },
        
        setCurrentSession: (sessionId) => {
          set({ currentSessionId: sessionId })
          if (sessionId) {
            get().loadMessages(sessionId)
          } else {
            set({ messages: [] })
          }
        },
        
        deleteSession: async (sessionId) => {
          try {
            await api.delete(`/api/sessions/${sessionId}`)
            
            set(state => {
              const newSessions = state.sessions.filter(session => session.id !== sessionId)
              const newCurrentSessionId = state.currentSessionId === sessionId 
                ? (newSessions.length > 0 ? newSessions[0].id : null)
                : state.currentSessionId
              
              return {
                sessions: newSessions,
                currentSessionId: newCurrentSessionId,
                messages: state.currentSessionId === sessionId ? [] : state.messages
              }
            })
            
          } catch (error) {
            console.error('Error deleting session:', error)
            set({ error: error.response?.data?.detail || 'Failed to delete session' })
          }
        },
        
        // Message management
        loadMessages: async (sessionId) => {
          try {
            set({ isLoading: true, error: null })
            
            const response = await api.get(`/api/sessions/${sessionId}/messages`)
            const messages = response.data.messages || []
            
            set({ messages, isLoading: false })
            
          } catch (error) {
            console.error('Error loading messages:', error)
            set({ 
              error: error.response?.data?.detail || 'Failed to load messages',
              isLoading: false 
            })
          }
        },
        
        sendMessage: async (content, options = {}) => {
          const { currentSessionId, socket } = get()
          if (!currentSessionId) {
            set({ error: 'No active session' })
            return
          }
          
          // Input validation
          if (!content || !content.trim()) {
            set({ error: 'Message cannot be empty' })
            return
          }
          
          if (content.length > 10000) {
            set({ error: 'Message too long (max 10,000 characters)' })
            return
          }
          
          const userMessage = {
            id: Date.now(),
            content: content.trim(),
            role: 'user',
            timestamp: new Date().toISOString(),
            metadata: options.metadata || {}
          }
          
          // Add user message immediately
          set(state => ({
            messages: [...state.messages, userMessage],
            isTyping: true,
            error: null
          }))
          
          try {
            const endpoint = options.includeProducts ? '/api/products/chat' : '/api/chat'
            const response = await api.post(endpoint, {
              query: content,
              session_id: currentSessionId,
              context: options.context || {},
              include_products: options.includeProducts || false
            })
            
            const aiMessage = {
              id: Date.now() + 1,
              content: response.data.response,
              role: 'assistant',
              timestamp: new Date().toISOString(),
              metadata: {
                intent: response.data.intent,
                confidence: response.data.confidence,
                entities: response.data.entities,
                conversation_state: response.data.conversation_state,
                productSuggestions: response.data.product_suggestions || [],
                followUpQuestions: response.data.follow_up_questions || [],
                responseTime: response.data.metadata?.response_time_ms,
                ...response.data.metadata
              }
            }
            
            set(state => ({
              messages: [...state.messages, aiMessage],
              isTyping: false
            }))
            
            // Emit via socket for real-time updates
            if (socket?.connected) {
              socket.emit('message', {
                ...aiMessage,
                session_id: currentSessionId
              })
            }
            
            return response.data
            
          } catch (error) {
            console.error('Error sending message:', error)
            
            const errorMessage = {
              id: Date.now() + 1,
              content: `❌ Error: ${error.response?.data?.detail || 'Failed to send message'}`,
              role: 'assistant',
              timestamp: new Date().toISOString(),
              isError: true
            }
            
            set(state => ({
              messages: [...state.messages, errorMessage],
              isTyping: false,
              error: error.response?.data?.detail || 'Failed to send message'
            }))
            
            throw error
          }
        },
        
        retryMessage: async (messageIndex) => {
          const { messages } = get()
          const messageToRetry = messages[messageIndex]
          
          if (messageToRetry && messageToRetry.role === 'user') {
            // Remove the failed message and retry
            set(state => ({
              messages: state.messages.slice(0, messageIndex),
              error: null
            }))
            
            await get().sendMessage(messageToRetry.content)
          }
        },
        
        clearMessages: () => {
          set({ messages: [] })
        },
        
        // Utility methods
        getSessionById: (sessionId) => {
          const { sessions } = get()
          return sessions.find(session => session.id === sessionId)
        },
        
        getCurrentSession: () => {
          const { currentSessionId, sessions } = get()
          return sessions.find(session => session.id === currentSessionId)
        },
        
        getMessageCount: () => {
          const { messages } = get()
          return messages.length
        },
        
        getMessagesByRole: (role) => {
          const { messages } = get()
          return messages.filter(message => message.role === role)
        },
        
        clearError: () => {
          set({ error: null })
        },
        
        resetConnection: () => {
          const { socket } = get()
          if (socket) {
            socket.disconnect()
          }
          set({ 
            socket: null, 
            isConnected: false, 
            connectionAttempts: 0,
            error: null 
          })
        }
      }),
      {
        name: 'enhanced-chat-store',
        partialize: (state) => ({
          sessions: state.sessions,
          currentSessionId: state.currentSessionId,
          // Don't persist messages, socket, or connection state
        })
      }
    )
  )
)

export { useEnhancedChatStore }
