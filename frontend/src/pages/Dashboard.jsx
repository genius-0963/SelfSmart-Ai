import { useEffect, useRef, useState } from 'react'
import { useChatStore } from '../stores/chatStore'
import ChatMessage from '../components/chat/ChatMessage'
import ChatInput from '../components/chat/ChatInput'
import ProductSuggestions from '../components/chat/ProductSuggestions'
import { Send, Bot } from 'lucide-react'

export default function Dashboard() {
  const {
    messages,
    isTyping,
    currentSession,
    sendMessage,
    createSession,
    connectSocket,
    loadSessions
  } = useChatStore()

  const messagesEndRef = useRef(null)
  const [includeProducts, setIncludeProducts] = useState(false)

  useEffect(() => {
    connectSocket()
    loadSessions()
    
    if (!currentSession) {
      createSession()
    }

    return () => {
      // Cleanup socket on unmount
    }
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSendMessage = async (content) => {
    if (!content.trim() || !currentSession) return
    await sendMessage(content, includeProducts)
  }

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Chat Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
              <Bot className="w-6 h-6 text-primary-600" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">
                SmartShelf AI Assistant
              </h1>
              <p className="text-sm text-gray-500">
                {currentSession ? 'Active conversation' : 'Start a new conversation'}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={includeProducts}
                onChange={(e) => setIncludeProducts(e.target.checked)}
                className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">Include product suggestions</span>
            </label>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && !isTyping && (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Bot className="w-16 h-16 mb-4 text-gray-300" />
            <h3 className="text-lg font-medium mb-2">Welcome to SmartShelf AI</h3>
            <p className="text-center max-w-md">
              I'm your intelligent shopping assistant. Ask me about products, 
              recommendations, or anything else related to shopping!
            </p>
            <div className="mt-6 text-sm text-gray-400">
              <p>Try asking:</p>
              <ul className="mt-2 space-y-1">
                <li>• "What are the best laptops under $1000?"</li>
                <li>• "Recommend some wireless headphones"</li>
                <li>• "Help me find a good coffee maker"</li>
              </ul>
            </div>
          </div>
        )}

        <div className="space-y-4">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          
          {isTyping && (
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5 text-gray-600" />
              </div>
              <div className="typing-indicator bg-gray-100 rounded-2xl">
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
              </div>
            </div>
          )}
        </div>
        <div ref={messagesEndRef} />
      </div>

      {/* Product Suggestions */}
      {messages.some(m => m.productSuggestions?.length > 0) && (
        <ProductSuggestions />
      )}

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <ChatInput onSendMessage={handleSendMessage} disabled={isTyping} />
      </div>
    </div>
  )
}
