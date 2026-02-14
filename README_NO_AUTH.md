# SmartShelf AI - Direct Chat Access (No Authentication)

This setup allows you to run the SmartShelf AI chat service without any authentication requirements, providing direct access to the chat interface.

## Quick Start

### Option 1: Direct HTML Access (Easiest)

1. **Start the backend server:**
   ```bash
   python start_no_auth.py
   ```

2. **Open the chat interface:**
   - Open `chat_direct.html` in your web browser
   - Or open: `file:///Users/subh/Desktop/selfsmart/chat_direct.html`

That's it! You can now chat directly without any login.

### Option 2: Frontend Development Server

If you want to run the React frontend:

1. **Start the backend:**
   ```bash
   python start_no_auth.py
   ```

2. **Start the frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Open:** http://localhost:5173

## What's Removed

- ✅ **Authentication** - No login required
- ✅ **Password validation** - Direct access
- ✅ **User registration** - Not needed
- ✅ **JWT tokens** - Bypassed
- ✅ **Protected routes** - Removed

## What's Still Available

- 🤖 **AI Chat** - Full conversational AI
- 🔍 **Product Search** - Product recommendations
- 📊 **RAG Pipeline** - Context-aware responses
- 🛒 **Product Suggestions** - Shopping assistance
- 📚 **Vector Search** - Document retrieval

## API Endpoints (No Auth Required)

- `POST /chat` - Basic chat
- `POST /products/chat` - Chat with product suggestions
- `POST /search` - Search documents
- `GET /health` - Service health check

## Configuration

The chat service runs on:
- **Backend:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs
- **Direct Chat:** Open `chat_direct.html`

## Troubleshooting

### Backend Not Starting
```bash
# Check Python dependencies
pip install fastapi uvicorn openai chromadb

# Check if port is available
lsof -i :8001
```

### Chat Not Responding
1. Make sure the backend is running on port 8001
2. Check browser console for errors
3. Verify OpenAI API key is configured in `copilot_chatbot/config.py`

### Product Suggestions Not Working
- Product suggestions require pre-built embeddings
- Check the backend logs for embedding loading status

## File Structure

```
selfsmart/
├── start_no_auth.py          # Backend startup script (no auth)
├── chat_direct.html          # Direct chat interface
├── README_NO_AUTH.md         # This file
├── copilot_chatbot/
│   ├── main.py              # Modified backend (no auth required)
│   └── ...                  # Other backend files
└── frontend/
    ├── src/
    │   ├── stores/
    │   │   └── chatStore.js # Modified for no-auth usage
    │   └── ...
    └── ...
```

## Security Note

⚠️ **This configuration is intended for development and testing only.**  
The no-auth setup exposes the chat API without any access controls. Do not use this configuration in production environments.

## Development

To modify the no-auth behavior:

1. **Backend:** Edit `copilot_chatbot/main.py`
2. **Frontend:** Edit `frontend/src/stores/chatStore.js`
3. **Direct HTML:** Edit `chat_direct.html`

The main changes are:
- Default session ID: `"default"`
- Removed authentication dependencies
- Simplified session management
- Direct API endpoints access
