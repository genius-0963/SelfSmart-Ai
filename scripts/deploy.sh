#!/bin/bash

# SmartShelf AI - Production Deployment Script
# Deploys the application to production environment

set -e

echo "🚀 Deploying SmartShelf AI to Production..."

# Configuration
ENVIRONMENT=${1:-production}
BUILD_DIR="dist"
DOCKER_REGISTRY="smartshelf-ai"
VERSION=$(date +%Y%m%d-%H%M%S)

echo "📋 Deployment Configuration:"
echo "- Environment: $ENVIRONMENT"
echo "- Version: $VERSION"
echo "- Registry: $DOCKER_REGISTRY"

# Build frontend
echo "🎨 Building frontend..."
cd frontend
npm run build
cd ..

# Create production Dockerfile if it doesn't exist
if [ ! -f "Dockerfile" ]; then
    echo "📝 Creating production Dockerfile..."
    cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY copilot_chatbot/ ./copilot_chatbot/
COPY scripts/ ./scripts/
COPY data/ ./data/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose ports
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["python3", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
fi

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t $DOCKER_REGISTRY/smartshelf-ai:$VERSION .
docker tag $DOCKER_REGISTRY/smartshelf-ai:$VERSION $DOCKER_REGISTRY/smartshelf-ai:latest

# Create docker-compose.yml for production
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "📝 Creating production docker-compose file..."
    cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  smartshelf-backend:
    image: smartshelf-ai/smartshelf-ai:latest
    container_name: smartshelf-backend
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=sqlite:///./data/database/smartshelf.db
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  smartshelf-copilot:
    image: smartshelf-ai/smartshelf-ai:latest
    container_name: smartshelf-copilot
    ports:
      - "8001:8001"
    environment:
      - ENVIRONMENT=production
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data/vector_store:/app/data/vector_store
    restart: unless-stopped
    command: ["python3", "-m", "uvicorn", "copilot_chatbot.main:app", "--host", "0.0.0.0", "--port", "8001"]
    depends_on:
      - smartshelf-backend

  nginx:
    image: nginx:alpine
    container_name: smartshelf-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html
      - ./ssl:/etc/nginx/ssl
    restart: unless-stopped
    depends_on:
      - smartshelf-backend
      - smartshelf-copilot

  redis:
    image: redis:alpine
    container_name: smartshelf-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
EOF
fi

# Create nginx configuration
if [ ! -f "nginx.conf" ]; then
    echo "📝 Creating nginx configuration..."
    cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server smartshelf-backend:8000;
    }

    upstream copilot {
        server smartshelf-copilot:8001;
    }

    server {
        listen 80;
        server_name localhost;

        # Frontend
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files $uri $uri/ /index.html;
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Copilot API
        location /copilot/ {
            proxy_pass http://copilot;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF
fi

echo "✅ Production deployment files created!"
echo ""
echo "🐳 To deploy with Docker Compose:"
echo "1. Set environment variables: export OPENAI_API_KEY=your_key"
echo "2. Run: docker-compose -f docker-compose.prod.yml up -d"
echo "3. Check status: docker-compose -f docker-compose.prod.yml ps"
echo ""
echo "🌐 Production access points:"
echo "- Application: http://localhost"
echo "- Backend API: http://localhost/api/"
echo "- Copilot API: http://localhost/copilot/"
echo "- Health: http://localhost/health"
