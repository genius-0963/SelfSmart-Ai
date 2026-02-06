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
# Install dependencies
pip install -r requirements.txt
npm install

# Start backend
cd backend && uvicorn main:app --reload

# Start frontend
cd frontend && npm start

# Generate sample data
python data_pipeline/generate_data.py
```

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
