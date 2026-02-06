# SMARTSHELF AI - Retail Decision Copilot

A hackathon-winning AI retail intelligence platform that helps small retailers make intelligent business decisions using machine learning forecasting, pricing analytics, inventory intelligence, and an AI conversational copilot.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   ML Models     │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Prophet/LSTM)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  AI Copilot     │
                       │  (RAG + LLM)    │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Vector Store   │
                       │  (ChromaDB)     │
                       └─────────────────┘
```

## Quick Start

```bash
# One-time setup (creates venv, installs deps, generates data, initializes DB)
./scripts/setup.sh

# Start all services (backend:8000, copilot:8001, frontend:3000)
./scripts/dev.sh
```

### Manual run (if you prefer separate terminals)

```bash
# Backend API
python3 -m uvicorn backend.app.main:app --reload --port 8000

# Copilot service
python3 -m uvicorn copilot_chatbot.main:app --reload --port 8001

# Frontend
cd frontend
npm install
npm run dev
```

### URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Copilot API**: http://localhost:8001

## Features

- 🤖 **AI Copilot**: Intelligent chatbot with retail domain knowledge
- 📊 **Demand Forecasting**: Time-series ML predictions for sales
- 💰 **Pricing Optimization**: Smart pricing recommendations
- 📦 **Inventory Intelligence**: Stockout and overstock alerts
- 📈 **Analytics Dashboard**: Real-time business insights

## Demo Flow

1. Upload retail data → ML processing → Forecast visualization
2. Alerts triggered → Pricing insights → Copilot interaction
3. AI explanations → Decision recommendations → Judge impact
