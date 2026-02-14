import { useState, useRef } from 'react'
import { Send, Paperclip } from 'lucide-react'

export default function ChatInput({ onSendMessage, disabled }) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef(null)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (message.trim() && !disabled) {
      onSendMessage(message.trim())
      setMessage('')
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleInputChange = (e) => {
    setMessage(e.target.value)
    
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(e.target.scrollHeight, 120)}px`
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-3">
      {/* Attachment Button */}
      <button
        type="button"
        className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
        title="Attach file (coming soon)"
        disabled
      >
        <Paperclip size={20} />
      </button>

      {/* Message Input */}
      <div className="flex-1">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          disabled={disabled}
          rows={1}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ minHeight: '40px', maxHeight: '120px' }}
        />
      </div>

      {/* Send Button */}
      <button
        type="submit"
        disabled={!message.trim() || disabled}
        className="p-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <Send size={20} />
      </button>
    </form>
  )
}
