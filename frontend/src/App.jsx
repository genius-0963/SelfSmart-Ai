import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'

// Create API instance with better error handling
const api = axios.create({
  baseURL: 'http://localhost:8002',
  timeout: 30000, // Increased timeout to 30 seconds for slower responses
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log('🔵 Sending request:', config.method?.toUpperCase(), config.url, config.data)
    return config
  },
  (error) => {
    console.log('❌ Request error:', error)
    return Promise.reject(error)
  }
)

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log('🟢 Received response:', response.config.url, response.data)
    return response
  },
  (error) => {
    console.log('🔴 Response error:', error.message)
    if (error.code === 'ECONNREFUSED') {
      error.message = 'Backend server is not running. Please start the backend on port 8002.'
    }
    return Promise.reject(error)
  }
)

function App() {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [includeProducts, setIncludeProducts] = useState(false)
  const [showDocs, setShowDocs] = useState(true)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      content: inputMessage,
      role: 'user',
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const endpoint = includeProducts ? '/products/chat' : '/chat'
      const response = await api.post(endpoint, {
        query: inputMessage,
        session_id: 'default'
      })

      const aiMessage = {
        id: Date.now() + 1,
        content: response.data.response,
        role: 'assistant',
        timestamp: new Date().toISOString(),
        productSuggestions: response.data.product_suggestions || []
      }

      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Backend error:', error)
      let errorMsg = 'Cannot connect to backend.'
      if (error.code === 'ECONNREFUSED') {
        errorMsg = '❌ Backend server is not running. Please start it with: python3 -m uvicorn copilot_chatbot.main:app --host 0.0.0.0 --port 8002'
      } else if (error.message?.includes('timeout')) {
        errorMsg = '⏱️ Request timed out. The backend may be slow or unresponsive. Check if it\'s running and try again.'
      } else {
        errorMsg = `❌ Backend Error: ${error.message || 'Unknown error. Make sure the backend is running on http://localhost:8002'}`
      }
      const errorMessage = {
        id: Date.now() + 1,
        content: errorMsg,
        role: 'assistant',
        timestamp: new Date().toISOString(),
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div style={{ 
      height: '100vh', 
      display: 'flex', 
      flexDirection: 'column',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      backgroundColor: '#f7f7f7'
    }}>
      {/* Header */}
      <div style={{
        backgroundColor: '#fff',
        borderBottom: '1px solid #e1e5e9',
        padding: '16px 24px',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            backgroundColor: '#007bff',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 'bold',
            fontSize: '18px'
          }}>
            🤖
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '18px', fontWeight: '600', color: '#2c3e50' }}>
              SmartShelf AI Assistant (Main Chat)
            </h1>
            <p style={{ margin: 0, fontSize: '14px', color: '#6c757d' }}>
              Your intelligent shopping assistant – this is the main page
            </p>
          </div>
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={includeProducts}
                onChange={(e) => setIncludeProducts(e.target.checked)}
                style={{ margin: 0 }}
              />
              <span style={{ fontSize: '14px', color: '#495057' }}>Include products</span>
            </label>
          </div>
          <button
            onClick={() => setShowDocs((prev) => !prev)}
            style={{
              marginTop: '4px',
              fontSize: '12px',
              padding: '4px 10px',
              borderRadius: '999px',
              border: '1px solid #ced4da',
              backgroundColor: showDocs ? '#0d6efd' : '#ffffff',
              color: showDocs ? '#ffffff' : '#495057',
              cursor: 'pointer'
            }}
          >
            {showDocs ? 'Hide docs' : 'Show docs'}
          </button>
        </div>
      </div>

      {/* Inline documentation / quick start */}
      {showDocs && (
        <div style={{
          backgroundColor: '#f8f9fa',
          borderBottom: '1px solid #e1e5e9',
          padding: '12px 24px',
          fontSize: '13px',
          color: '#495057',
        }}>
          <div style={{ fontWeight: 600, marginBottom: '4px' }}>How to use this chatbot</div>
          <ol style={{ paddingLeft: '18px', margin: 0, lineHeight: 1.5 }}>
            <li>Make sure the backend is running: <code>python3 -m uvicorn copilot_chatbot.main:app --host 0.0.0.0 --port 8002</code></li>
            <li>Set your API keys in the <code>.env</code> file: <code>OPENAI_API_KEY=sk-your-actual-key</code> (optional - server will start without it but chat will be limited)</li>
            <li>Ask any question about products, analytics, or general queries in the message box below.</li>
            <li>Enable “Include products” to also call <code>/products/chat</code> for product recommendations.</li>
          </ol>
          <div style={{ marginTop: '4px', fontSize: '12px', color: '#6c757d' }}>
            <strong>Note:</strong> If you see timeout errors, check that the backend started successfully. The server will start even without API keys but chat features will be limited.
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px'
      }}>
        {messages.length === 0 ? (
          <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            color: '#6c757d'
          }}>
            <div style={{
              fontSize: '64px',
              marginBottom: '16px',
              opacity: 0.5
            }}>
              🤖
            </div>
            <h2 style={{ margin: 0, fontSize: '24px', fontWeight: '600', color: '#2c3e50' }}>
              Welcome to SmartShelf AI
            </h2>
            <p style={{ margin: '8px 0 0 0', fontSize: '16px', maxWidth: '400px', lineHeight: '1.5' }}>
              I'm your intelligent shopping assistant. Ask me about products, recommendations, or shopping advice!
            </p>
            <div style={{ marginTop: '24px', textAlign: 'left' }}>
              <p style={{ margin: 0, fontSize: '14px', fontWeight: '600', color: '#495057' }}>
                Try asking:
              </p>
              <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px', fontSize: '14px', color: '#6c757d' }}>
                <li>"What are the best laptops under $1000?"</li>
                <li>"Recommend some wireless headphones"</li>
                <li>"Help me find a good coffee maker"</li>
              </ul>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              style={{
                display: 'flex',
                justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '100%'
              }}
            >
              <div style={{
                maxWidth: '70%',
                backgroundColor: message.role === 'user' ? '#007bff' : 
                               message.isError ? '#f8d7da' : '#fff',
                color: message.role === 'user' ? 'white' : 
                       message.isError ? '#721c24' : '#2c3e50',
                padding: '12px 16px',
                borderRadius: '18px',
                boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                wordWrap: 'break-word'
              }}>
                <p style={{ margin: 0, lineHeight: '1.4' }}>
                  {message.content}
                </p>
                <div style={{
                  fontSize: '11px',
                  opacity: 0.7,
                  marginTop: '4px',
                  textAlign: message.role === 'user' ? 'right' : 'left'
                }}>
                  {new Date(message.timestamp).toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </div>
              </div>
            </div>
          ))
        )}
        
        {isLoading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{
              backgroundColor: '#fff',
              padding: '12px 16px',
              borderRadius: '18px',
              boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
            }}>
              <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                <div style={{
                  width: '8px',
                  height: '8px',
                  backgroundColor: '#007bff',
                  borderRadius: '50%',
                  animation: 'bounce 1.4s infinite ease-in-out both'
                }}></div>
                <div style={{
                  width: '8px',
                  height: '8px',
                  backgroundColor: '#007bff',
                  borderRadius: '50%',
                  animation: 'bounce 1.4s infinite ease-in-out both',
                  animationDelay: '0.16s'
                }}></div>
                <div style={{
                  width: '8px',
                  height: '8px',
                  backgroundColor: '#007bff',
                  borderRadius: '50%',
                  animation: 'bounce 1.4s infinite ease-in-out both',
                  animationDelay: '0.32s'
                }}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Product Suggestions */}
      {messages.some(m => m.productSuggestions?.length > 0) && (
        <div style={{
          backgroundColor: '#fff',
          borderTop: '1px solid #e1e5e9',
          padding: '16px 24px',
          maxHeight: '200px',
          overflowY: 'auto'
        }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: '600', color: '#2c3e50' }}>
            🛍️ Recommended Products
          </h3>
          <div style={{ display: 'flex', gap: '12px', overflowX: 'auto' }}>
            {messages
              .filter(m => m.productSuggestions?.length > 0)
              .pop()
              ?.productSuggestions.map((product, index) => (
                <div
                  key={index}
                  style={{
                    minWidth: '200px',
                    padding: '12px',
                    border: '1px solid #e1e5e9',
                    borderRadius: '8px',
                    backgroundColor: '#f8f9fa'
                  }}
                >
                  <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', fontWeight: '600', color: '#2c3e50' }}>
                    {product.name}
                  </h4>
                  <p style={{ margin: '0 0 8px 0', fontSize: '12px', color: '#6c757d' }}>
                    {product.description}
                  </p>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '14px', fontWeight: '600', color: '#007bff' }}>
                      {product.price}
                    </span>
                    <span style={{ fontSize: '12px', color: '#6c757d' }}>
                      ⭐ {product.rating}
                    </span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div style={{
        backgroundColor: '#fff',
        borderTop: '1px solid #e1e5e9',
        padding: '16px 24px'
      }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={isLoading}
            rows={1}
            style={{
              flex: 1,
              border: '1px solid #ced4da',
              borderRadius: '24px',
              padding: '12px 16px',
              fontSize: '14px',
              resize: 'none',
              outline: 'none',
              fontFamily: 'inherit',
              maxHeight: '120px'
            }}
          />
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            style={{
              backgroundColor: inputMessage.trim() && !isLoading ? '#007bff' : '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '50%',
              width: '48px',
              height: '48px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: inputMessage.trim() && !isLoading ? 'pointer' : 'not-allowed',
              fontSize: '20px'
            }}
          >
            {isLoading ? '⏳' : '➤'}
          </button>
        </div>
      </div>

      <style jsx>{`
        @keyframes bounce {
          0%, 80%, 100% {
            transform: scale(0);
          }
          40% {
            transform: scale(1.0);
          }
        }
      `}</style>
    </div>
  )
}

export default App
