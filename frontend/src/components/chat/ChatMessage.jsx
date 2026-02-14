import { User, Bot, AlertCircle } from 'lucide-react'

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  const isError = message.isError

  const formatTime = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      })
    } catch {
      return '12:00 PM'
    }
  }

  return (
    <div className={`flex items-start gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
          isError ? 'bg-red-100' : 'bg-gray-200'
        }`}>
          {isError ? (
            <AlertCircle className="w-5 h-5 text-red-600" />
          ) : (
            <Bot className="w-5 h-5 text-gray-600" />
          )}
        </div>
      )}

      <div className={`max-w-lg lg:max-w-2xl ${isUser ? 'order-first' : ''}`}>
        <div className={`chat-bubble ${
          isUser 
            ? 'chat-bubble-user' 
            : isError 
              ? 'bg-red-50 text-red-700 border border-red-200' 
              : 'chat-bubble-ai'
        }`}>
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        </div>
        
        <div className={`flex items-center gap-2 mt-1 text-xs text-gray-500 ${
          isUser ? 'justify-end' : 'justify-start'
        }`}>
          <span>
            {formatTime(message.timestamp)}
          </span>
          {isUser && <User size={12} />}
          {!isUser && !isError && <Bot size={12} />}
        </div>
      </div>

      {isUser && (
        <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center flex-shrink-0">
          <User className="w-5 h-5 text-white" />
        </div>
      )}
    </div>
  )
}
