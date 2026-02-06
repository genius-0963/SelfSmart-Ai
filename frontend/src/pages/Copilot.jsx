import React, { useState, useEffect, useRef } from 'react'
import { Send, Bot, User, Lightbulb, MessageCircle } from 'lucide-react'

export default function Copilot() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: 'Hello! I\'m SmartShelf AI, your intelligent retail assistant. How can I help you make data-driven decisions today?',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    // Simulate API call
    setTimeout(() => {
      const response = generateResponse(input)
      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])
      setLoading(false)
    }, 1000)
  }

  const generateResponse = (query) => {
    const lowerQuery = query.toLowerCase()
    
    if (lowerQuery.includes('inventory') || lowerQuery.includes('stock')) {
      return 'Based on current inventory levels, you have 5 products at risk of stockout and 12 with low stock. I recommend prioritizing the Office Chair (FUR001) which is currently out of stock, and the Wireless Mouse (ELE002) with only 8 units remaining. Would you like me to show you the complete reorder recommendations?'
    }
    
    if (lowerQuery.includes('revenue') || lowerQuery.includes('sales')) {
      return 'Your total revenue for the last 30 days is $609,523.18, representing a 12% increase from the previous period. Electronics is your top-performing category with $245,890 in revenue. Would you like me to break down the performance by specific products?'
    }
    
    if (lowerQuery.includes('forecast') || lowerQuery.includes('demand')) {
      return 'My demand forecasting models predict a 15% increase in demand for Electronics products over the next 30 days with 87% confidence. The forecast accuracy across all products is currently 87%. Would you like to see the detailed forecast for specific products?'
    }
    
    if (lowerQuery.includes('price') || lowerQuery.includes('pricing')) {
      return 'I\'ve identified 8 products with pricing optimization opportunities totaling $592 in potential revenue impact. The Laptop Pro (ELE001) could be increased to $1,099 with 87% confidence. Would you like to see all pricing recommendations?'
    }
    
    return 'I\'m here to help you make data-driven decisions for your retail business. I can assist with inventory management, demand forecasting, pricing optimization, and sales analytics. What specific area would you like to explore?'
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-card border-b border-border p-4">
        <div className="flex items-center space-x-3">
          <Bot className="w-6 h-6 text-green-400" />
          <div>
            <h1 className="text-lg font-semibold text-foreground">AI Copilot</h1>
            <p className="text-sm text-muted-foreground">Your intelligent retail assistant</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(message => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`flex items-start space-x-2 max-w-lg ${
              message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
            }`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                message.type === 'user' ? 'bg-green-500' : 'bg-gray-800'
              }`}>
                {message.type === 'user' ? (
                  <User className="w-5 h-5 text-white" />
                ) : (
                  <Bot className="w-5 h-5 text-white" />
                )}
              </div>
              <div className={`rounded-lg p-3 ${
                message.type === 'user' 
                  ? 'bg-green-500/15 text-green-100 border border-green-500/20' 
                  : 'bg-card text-foreground border border-border'
              }`}>
                <p className="text-sm">{message.content}</p>
                <p className={`text-xs mt-1 ${
                  message.type === 'user' ? 'text-green-200/70' : 'text-muted-foreground'
                }`}>
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="flex justify-start">
            <div className="flex items-start space-x-2">
              <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-card border border-border rounded-lg p-3">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      <div className="bg-card border-t border-border p-4">
        <div className="flex flex-wrap gap-2 mb-3">
          <button
            onClick={() => setInput('Show me inventory alerts')}
            className="px-3 py-1 text-sm bg-gray-900 hover:bg-gray-800 border border-border rounded-full flex items-center space-x-1 text-foreground"
          >
            <Lightbulb className="w-3 h-3" />
            <span>Inventory Alerts</span>
          </button>
          <button
            onClick={() => setInput('What\'s my revenue trend?')}
            className="px-3 py-1 text-sm bg-gray-900 hover:bg-gray-800 border border-border rounded-full flex items-center space-x-1 text-foreground"
          >
            <MessageCircle className="w-3 h-3" />
            <span>Revenue Trend</span>
          </button>
          <button
            onClick={() => setInput('Which products should I reorder?')}
            className="px-3 py-1 text-sm bg-gray-900 hover:bg-gray-800 border border-border rounded-full flex items-center space-x-1 text-foreground"
          >
            <Lightbulb className="w-3 h-3" />
            <span>Reorder Suggestions</span>
          </button>
        </div>
        
        {/* Input */}
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask me anything about your retail business..."
            className="flex-1 px-4 py-2 border border-border bg-background text-foreground rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-4 py-2 bg-green-600 text-black rounded-lg hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <Send className="w-4 h-4" />
            <span>Send</span>
          </button>
        </div>
      </div>
    </div>
  )
}
