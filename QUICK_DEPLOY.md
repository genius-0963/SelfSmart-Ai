# 🚀 Quick Global Deployment Guide

## ⚡ 5-Minute Deployment

### 1. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env
# Add your OPENAI_API_KEY and ANTHROPIC_API_KEY
```

### 2. Deploy Locally (Testing)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python -m copilot_chatbot.main

# Test it
curl http://localhost:8001/health
```

### 3. Deploy to Production
```bash
# One-command deployment
./scripts/deploy-production.sh

# Or manually
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Access Your Service
- **API**: http://localhost:8001
- **Health**: http://localhost:8001/health  
- **Docs**: http://localhost:8001/docs

## 🌐 Cloud Deployment (Render - Easiest)

1. **Push to GitHub**
2. **Go to [render.com](https://render.com)**
3. **Connect your repository**
4. **Add environment variables:**
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`
5. **Deploy automatically** 🎉

## 📱 Test Your API

```bash
# Health check
curl http://localhost:8001/health

# Chat test
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, how can you help me?"}'

# Product suggestions
curl -X POST "http://localhost:8001/products/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "Recommend some products"}'
```

## 🔧 What's Included

✅ **Production-ready Docker image**  
✅ **Nginx reverse proxy**  
✅ **SSL/HTTPS support**  
✅ **Rate limiting**  
✅ **Health monitoring**  
✅ **Persistent data storage**  
✅ **Redis caching**  
✅ **Security headers**  
✅ **Auto-restart**  
✅ **Global CORS**  

## 🎯 Your 4 Core Endpoints

1. **POST /chat** - Basic AI chat
2. **POST /products/chat** - Chat with product suggestions  
3. **POST /search** - Context search
4. **GET /health** - Service health check

---

**🚀 Your SmartShelf AI Chat Service is ready for global deployment!**
