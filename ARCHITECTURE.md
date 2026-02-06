# SMARTSHELF AI - System Architecture

## Component Architecture Diagram

```ascii
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SMARTSHELF AI PLATFORM                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   FRONTEND      │    │   BACKEND API   │    │   ML PIPELINE   │        │
│  │   (React/Next)  │◄──►│   (FastAPI)     │◄──►│   (Prophet/LSTM)│        │
│  │                 │    │                 │    │                 │        │
│  │ • Dashboard     │    │ • REST Endpoints│    │ • Forecasting   │        │
│  │ • Charts        │    │ • Validation    │    │ • Pricing       │        │
│  │ • Chat UI       │    │ • CORS          │    │ • Inventory     │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│           │                       │                       │              │
│           │                       │                       │              │
│           ▼                       ▼                       ▼              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   STATE STORE   │    │   DATABASE      │    │   MODEL STORE   │        │
│  │   (Zustand)     │    │   (SQLite)      │    │   (Pickle)      │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│                                                         │                  │
│                                                         ▼                  │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                        AI COPILOT ENGINE                            │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────────┐ │  │
│  │  │   RAG       │  │   LLM        │  │   CONTEXT RETRIEVAL         │ │  │
│  │  │   Pipeline  │  │   Integration│  │   (Vector Search)           │ │  │
│  │  └─────────────┘  └──────────────┘  └─────────────────────────────┘ │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                           │                        │                      │
│                           ▼                        ▼                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │  VECTOR STORE   │    │   DOCUMENTS     │    │   CACHE         │        │
│  │  (ChromaDB)     │    │   (Knowledge)   │    │   (Redis)       │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibility Matrix

| Component | Primary Responsibilities | Key Technologies | Success Metrics |
|-----------|-------------------------|------------------|-----------------|
| **Frontend Dashboard** | User interface, data visualization, real-time updates | React, Recharts, TailwindCSS, Zustand | <100ms page loads, intuitive UX |
| **Backend API** | Request handling, data processing, business logic | FastAPI, Pydantic, SQLAlchemy, Uvicorn | <50ms API response, 99.9% uptime |
| **ML Pipeline** | Forecasting, pricing optimization, inventory analysis | Prophet, LSTM, scikit-learn, pandas | >90% forecast accuracy, <1s inference |
| **AI Copilot** | Conversational AI, context retrieval, decision support | RAG, ChromaDB, OpenAI/Claude, Sentence Transformers | <2s response, relevant context |
| **Data Layer** | Storage, indexing, data integrity | SQLite, Pandas, CSV/JSON | <10ms query, data consistency |
| **Vector Store** | Semantic search, embeddings, similarity matching | ChromaDB, FAISS, sentence-transformers | <100ms retrieval, >85% relevance |

## Data Flow Architecture

```ascii
1. DATA INGESTION
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ CSV Upload  │───▶│ Validation  │───▶│ Database    │
   └─────────────┘    └─────────────┘    └─────────────┘

2. ML PROCESSING
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ Raw Data    │───▶│ Feature     │───▶│ Model       │
   │ Extraction  │    │ Engineering │    │ Training    │
   └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │
                           ▼                   ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ Demand      │    │ Pricing     │    │ Inventory  │
   │ Forecast    │    │ Optimization│    │ Intelligence│
   └─────────────┘    └─────────────┘    └─────────────┘

3. AI COPILOT FLOW
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ User Query  │───▶│ Vector      │───▶│ Context     │
   │ Processing  │    │ Search      │    │ Retrieval   │
   └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │
                           ▼                   ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ LLM         │    │ Response    │    │ UI          │
   │ Generation  │    │ Formatting  │    │ Display     │
   └─────────────┘    └─────────────┘    └─────────────┘

4. REAL-TIME UPDATES
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ Model       │───▶│ API         │───▶│ Frontend    │
   │ Predictions │    │ Endpoints   │    │ Dashboard   │
   └─────────────┘    └─────────────┘    └─────────────┘
```

## Technology Stack Justification

### Frontend Stack
- **React**: Component-based architecture, extensive ecosystem, hackathon-friendly
- **TailwindCSS**: Rapid UI development, responsive design, minimal custom CSS
- **Recharts**: Declarative charting, React integration, beautiful visualizations
- **Zustand**: Lightweight state management, simple API, better than Redux for hackathon

### Backend Stack
- **FastAPI**: Auto-generated docs, async support, type hints, excellent for APIs
- **Pydantic**: Data validation, serialization, OpenAPI integration
- **SQLAlchemy**: ORM support, database abstraction, migration tools
- **SQLite**: Zero configuration, portable, perfect for hackathon demo

### ML Stack
- **Prophet**: Time-series forecasting, handles seasonality, Facebook's battle-tested
- **scikit-learn**: Classical ML, preprocessing, evaluation metrics
- **pandas/numpy**: Data manipulation, industry standard
- **joblib**: Model serialization, efficient loading

### AI Copilot Stack
- **ChromaDB**: Vector database, local deployment, semantic search
- **sentence-transformers**: Open-source embeddings, no API keys needed
- **OpenAI/Claude**: LLM integration, reasoning capabilities (API key required)
- **RAG Pattern**: Context-aware responses, reduces hallucination

## Integration Points

### API Integration Matrix
```
Frontend ↔ Backend:
- WebSocket: Real-time dashboard updates
- REST API: CRUD operations, data queries
- File Upload: CSV data ingestion

Backend ↔ ML Pipeline:
- Direct imports: Model loading/inference
- Async tasks: Model training, batch processing
- File system: Model serialization

Backend ↔ AI Copilot:
- HTTP requests: Query processing
- Shared database: Context, chat history
- Vector store: Semantic search integration

ML Pipeline ↔ AI Copilot:
- Data sharing: Model outputs as context
- Feature access: Explanations, insights
- Prediction APIs: Real-time decision support
```

### Security & Performance
- **CORS**: Cross-origin request handling
- **Rate Limiting**: API abuse prevention
- **Input Validation**: Pydantic models everywhere
- **Error Handling**: Comprehensive exception management
- **Caching**: Redis for frequent queries
- **Async Processing**: Non-blocking operations

## Scalability Vision

### Phase 1 (Hackathon)
- Single-store deployment
- SQLite database
- Local model serving
- Basic UI dashboard

### Phase 2 (MVP)
- Multi-tenant architecture
- PostgreSQL database
- Containerized deployment
- Enhanced UI/UX

### Phase 3 (Scale)
- Microservices architecture
- Cloud deployment (AWS/GCP)
- Real-time data streaming
- Mobile applications
- Third-party integrations
