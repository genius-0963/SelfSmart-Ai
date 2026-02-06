# SmartShelf AI - Complete Project Structure

```
smartshelf-ai/
├── README.md                           # Project overview and quick start
├── ARCHITECTURE.md                     # System architecture and design decisions
├── PROJECT_STRUCTURE.md                # This file - detailed structure explanation
├── requirements.txt                    # Python dependencies (backend + ML + copilot)
├── docker-compose.yml                  # Container orchestration
├── .env.example                        # Environment variables template
├── .gitignore                          # Git ignore patterns
│
├── backend/                            # FastAPI backend service
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI application entry point
│   │   ├── config.py                   # Configuration management
│   │   ├── database.py                 # Database connection and setup
│   │   ├── models/                     # Pydantic models for API
│   │   │   ├── __init__.py
│   │   │   ├── product.py
│   │   │   ├── sales.py
│   │   │   ├── forecast.py
│   │   │   └── inventory.py
│   │   ├── schemas/                    # SQLAlchemy database models
│   │   │   ├── __init__.py
│   │   │   ├── product.py
│   │   │   ├── sales.py
│   │   │   ├── inventory.py
│   │   │   └── forecast.py
│   │   ├── api/                        # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── data.py             # Data upload and management
│   │   │   │   ├── forecast.py         # Forecasting endpoints
│   │   │   │   ├── pricing.py          # Pricing optimization
│   │   │   │   ├── inventory.py        # Inventory alerts
│   │   │   │   ├── analytics.py        # Dashboard analytics
│   │   │   │   └── copilot.py          # AI copilot integration
│   │   ├── core/                       # Core business logic
│   │   │   ├── __init__.py
│   │   │   ├── security.py             # Authentication and security
│   │   │   ├── exceptions.py           # Custom exceptions
│   │   │   └── logging.py              # Logging configuration
│   │   └── services/                   # Business service layer
│   │       ├── __init__.py
│   │       ├── data_service.py
│   │       ├── forecast_service.py
│   │       ├── pricing_service.py
│   │       └── inventory_service.py
│   ├── tests/                          # Backend tests
│   │   ├── __init__.py
│   │   ├── test_api.py
│   │   ├── test_models.py
│   │   └── test_services.py
│   └── requirements.txt                # Backend-specific dependencies
│
├── ml_models/                          # Machine learning pipeline
│   ├── __init__.py
│   ├── base.py                         # Base model class
│   ├── pipeline.py                     # ML orchestration
│   ├── utils.py                        # ML utilities
│   ├── forecasting/                    # Demand forecasting models
│   │   ├── __init__.py
│   │   ├── prophet_model.py            # Prophet time-series forecasting
│   │   ├── lstm_model.py               # LSTM neural network
│   │   ├── features.py                 # Feature engineering
│   │   ├── train.py                    # Training pipeline
│   │   └── evaluate.py                 # Model evaluation
│   ├── pricing/                        # Pricing optimization
│   │   ├── __init__.py
│   │   ├── elasticity.py               # Price elasticity analysis
│   │   ├── optimizer.py                # Pricing optimization algorithm
│   │   ├── competitor.py               # Competitive pricing analysis
│   │   └── markdown.py                 # Markdown recommendations
│   └── inventory/                      # Inventory intelligence
│       ├── __init__.py
│       ├── stockout.py                 # Stock-out prediction
│       ├── overstock.py                # Overstock detection
│       ├── reorder.py                  # Reorder point calculation
│       └── abc_analysis.py             # ABC inventory analysis
│
├── copilot_chatbot/                    # AI Copilot engine
│   ├── __init__.py
│   ├── main.py                         # Copilot service entry point
│   ├── config.py                       # Copilot configuration
│   ├── rag/                            # Retrieval-Augmented Generation
│   │   ├── __init__.py
│   │   ├── retriever.py                # Vector search implementation
│   │   ├── embedder.py                 # Text embedding generation
│   │   ├── documents.py                # Document processing
│   │   └── pipeline.py                 # RAG pipeline orchestration
│   ├── llm/                            # LLM integration
│   │   ├── __init__.py
│   │   ├── openai_client.py            # OpenAI API integration
│   │   ├── claude_client.py            # Claude API integration
│   │   ├── prompts.py                  # Prompt templates
│   │   └── response_parser.py          # Response formatting
│   ├── vector_store/                   # Vector database management
│   │   ├── __init__.py
│   │   ├── chromadb_client.py          # ChromaDB integration
│   │   ├── embeddings.py               # Embedding management
│   │   └── search.py                   # Vector search operations
│   ├── conversation/                   # Conversation management
│   │   ├── __init__.py
│   │   ├── history.py                  # Chat history storage
│   │   ├── context.py                  # Context window management
│   │   └── session.py                  # Session management
│   └── requirements.txt                # Copilot-specific dependencies
│
├── frontend/                           # React dashboard
│   ├── public/
│   │   ├── index.html
│   │   ├── favicon.ico
│   │   └── manifest.json
│   ├── src/
│   │   ├── index.js                    # React app entry point
│   │   ├── App.js                      # Main application component
│   │   ├── index.css                   # Global styles
│   │   ├── components/                 # Reusable UI components
│   │   │   ├── common/                 # Common components
│   │   │   │   ├── Header.jsx
│   │   │   │   ├── Sidebar.jsx
│   │   │   │   ├── Loading.jsx
│   │   │   │   └── ErrorBoundary.jsx
│   │   │   ├── Dashboard/              # Dashboard components
│   │   │   │   ├── MetricsOverview.jsx
│   │   │   │   ├── SalesChart.jsx
│   │   │   │   ├── RevenueCard.jsx
│   │   │   │   └── QuickStats.jsx
│   │   │   ├── Forecasting/            # Forecasting UI
│   │   │   │   ├── ForecastChart.jsx
│   │   │   │   ├── ProductSelector.jsx
│   │   │   │   ├── ConfidenceInterval.jsx
│   │   │   │   └── ForecastTable.jsx
│   │   │   ├── Pricing/                # Pricing optimization UI
│   │   │   │   ├── PricingTable.jsx
│   │   │   │   ├── OptimizationSuggestions.jsx
│   │   │   │   ├── ElasticityChart.jsx
│   │   │   │   └── CompetitorAnalysis.jsx
│   │   │   ├── Inventory/              # Inventory management UI
│   │   │   │   ├── AlertsList.jsx
│   │   │   │   ├── StockLevelGauge.jsx
│   │   │   │   ├── ReorderRecommendations.jsx
│   │   │   │   └── ABCAnalysisChart.jsx
│   │   │   └── Copilot/                # AI Copilot interface
│   │   │       ├── ChatInterface.jsx
│   │   │       ├── MessageBubble.jsx
│   │   │       ├── InsightCard.jsx
│   │   │       ├── QuerySuggestions.jsx
│   │   │       └── VoiceInput.jsx
│   │   ├── pages/                      # Page components
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── ForecastingPage.jsx
│   │   │   ├── PricingPage.jsx
│   │   │   ├── InventoryPage.jsx
│   │   │   └── CopilotPage.jsx
│   │   ├── hooks/                      # Custom React hooks
│   │   │   ├── useApi.js               # API interaction hook
│   │   │   ├── useWebSocket.js         # WebSocket connection
│   │   │   ├── useLocalStorage.js      # Local storage management
│   │   │   └── useDebounce.js          # Debounce utility
│   │   ├── utils/                      # Utility functions
│   │   │   ├── api.js                  # API client configuration
│   │   │   ├── formatters.js           # Data formatting utilities
│   │   │   ├── validators.js           # Form validation
│   │   │   └── constants.js            # Application constants
│   │   └── store/                      # State management (Zustand)
│   │       ├── index.js                # Store configuration
│   │       ├── dashboardStore.js       # Dashboard state
│   │       ├── forecastStore.js        # Forecast state
│   │       ├── pricingStore.js         # Pricing state
│   │       ├── inventoryStore.js       # Inventory state
│   │       └── copilotStore.js         # Copilot state
│   ├── package.json                    # Node.js dependencies
│   ├── package-lock.json               # Dependency lock file
│   └── .env.example                    # Frontend environment variables
│
├── data/                               # Data storage and processing
│   ├── raw/                            # Raw uploaded data
│   │   └── sample_retail_data.csv      # Sample retail dataset
│   ├── processed/                      # Processed and cleaned data
│   │   ├── sales_cleaned.csv
│   │   ├── products_cleaned.csv
│   │   └── inventory_cleaned.csv
│   ├── models/                         # Trained ML models
│   │   ├── demand_forecast.pkl
│   │   ├── pricing_model.pkl
│   │   └── inventory_model.pkl
│   └── database/                       # Database files
│       └── smartshelf.db               # SQLite database
│
├── configs/                            # Configuration files
│   ├── dev/
│   │   ├── backend.yaml                # Development backend config
│   │   ├── ml_models.yaml              # ML model parameters
│   │   └── copilot.yaml                # Copilot configuration
│   ├── prod/
│   │   ├── backend.yaml                # Production backend config
│   │   ├── ml_models.yaml              # Production ML config
│   │   └── copilot.yaml                # Production copilot config
│   └── logging.yaml                    # Logging configuration
│
├── scripts/                            # Utility and deployment scripts
│   ├── setup.sh                       # Environment setup script
│   ├── generate_data.py                # Synthetic data generator
│   ├── train_models.py                 # ML model training script
│   ├── build_index.py                  # Vector index building
│   ├── deploy.sh                       # Deployment script
│   └── backup.sh                       # Database backup script
│
└── docs/                               # Documentation
    ├── API.md                          # API documentation
    ├── ML_MODELS.md                    # ML models documentation
    ├── DEPLOYMENT.md                   # Deployment guide
    ├── CONTRIBUTING.md                 # Contribution guidelines
    └── DEMO_SCRIPT.md                  # Demo script for presentations
```

## Separation of Concerns

### Backend Layer (FastAPI)
- **Responsibility**: API endpoints, data validation, business logic
- **Isolation**: Pure Python, no frontend dependencies
- **Testing**: Unit tests for all endpoints and services
- **Deployment**: Containerizable, scalable independently

### ML Pipeline Layer
- **Responsibility**: Model training, inference, feature engineering
- **Isolation**: Standalone Python modules, configurable via YAML
- **Testing**: Model evaluation, cross-validation, performance benchmarks
- **Deployment**: Batch processing or real-time inference

### AI Copilot Layer
- **Responsibility**: Conversational AI, context retrieval, LLM integration
- **Isolation**: Independent microservice with own data store
- **Testing**: Response quality, relevance metrics, conversation flow
- **Deployment**: Separate service, can use different infrastructure

### Frontend Layer (React)
- **Responsibility**: User interface, data visualization, user interactions
- **Isolation**: Pure JavaScript/React, communicates via REST/WebSocket
- **Testing**: Component tests, integration tests, E2E tests
- **Deployment**: Static assets, CDN-friendly

## Module Dependency Graph

```ascii
Frontend
    │
    ├──► Backend API
    │       │
    │       ├──► ML Pipeline
    │       │       ├──► Data Layer
    │       │       └──► Model Store
    │       │
    │       ├──► AI Copilot
    │       │       ├──► Vector Store
    │       │       ├──► LLM APIs
    │       │       └──► Documents
    │       │
    │       └──► Database
    │               ├──► Raw Data
    │               └────► Processed Data
    │
    └──► Browser Storage (Local/Session)
```

## Key Design Principles

1. **Modularity**: Each component can be developed, tested, and deployed independently
2. **Scalability**: Architecture supports horizontal scaling and microservices
3. **Maintainability**: Clear separation of concerns, well-documented interfaces
4. **Testability**: Comprehensive testing strategy for each layer
5. **Performance**: Async processing, caching, optimized data structures
6. **Security**: Input validation, authentication, secure API design
