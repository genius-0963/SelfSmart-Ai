#!/bin/bash

# SmartShelf AI - Local Development Deployment
# Runs the enhanced system without Docker for development

set -e

echo "🚀 Starting SmartShelf AI Local Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 is not installed"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is not installed"
        exit 1
    fi
    
    # Check Node.js (for frontend)
    if ! command -v node &> /dev/null; then
        log_warning "Node.js is not installed - frontend won't start"
    fi
    
    log_success "Prerequisites check completed"
}

# Install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
        log_success "Python dependencies installed"
    else
        log_warning "requirements.txt not found"
    fi
    
    # Install additional dependencies for enhanced features
    log_info "Installing enhanced dependencies..."
    pip3 install pydantic-settings redis aiohttp psutil
    log_success "Enhanced dependencies installed"
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."
    
    # Create necessary directories
    mkdir -p logs uploads data monitoring/grafana/dashboards monitoring/grafana/datasources
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success "Created .env from .env.example"
        else
            cat > .env << EOF
# SmartShelf AI Environment Configuration
DEBUG=true
LOG_LEVEL=INFO
ENVIRONMENT=development

# API Keys (set these for full functionality)
OPENAI_API_KEY=your-openai-api-key-here
DEEPSEEK_API_KEY=your-deepseek-api-key-here
AMAZON_API_KEY=your-amazon-api-key-here

# Database Configuration
DATABASE_URL=sqlite:///./smartshelf.db
REDIS_URL=redis://localhost:6379

# Performance Configuration
CACHE_TTL=3600
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=30

# Security Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
RATE_LIMIT_PER_MINUTE=60
EOF
            log_success "Created default .env file"
        fi
    fi
}

# Start enhanced backend
start_backend() {
    log_info "Starting enhanced backend..."
    
    # Check if Redis is running (optional)
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            log_success "Redis is running"
        else
            log_warning "Redis is not running - caching will be disabled"
        fi
    else
        log_warning "Redis not installed - caching will be disabled"
    fi
    
    # Start the enhanced backend
    cd copilot_chatbot
    python3 enhanced_main.py &
    BACKEND_PID=$!
    cd ..
    
    log_success "Enhanced backend started (PID: $BACKEND_PID)"
    echo $BACKEND_PID > .backend.pid
}

# Start frontend (if available)
start_frontend() {
    if [ -d "frontend" ] && command -v node &> /dev/null; then
        log_info "Starting frontend..."
        
        cd frontend
        
        # Install dependencies if needed
        if [ ! -d "node_modules" ]; then
            npm install
        fi
        
        # Start development server
        npm run dev &
        FRONTEND_PID=$!
        
        cd ..
        log_success "Frontend started (PID: $FRONTEND_PID)"
        echo $FRONTEND_PID > .frontend.pid
    else
        log_warning "Frontend not available or Node.js not installed"
    fi
}

# Wait for services to be ready
wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # Wait for backend
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "Backend is healthy"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Backend failed to start"
            return 1
        fi
        
        log_info "Waiting for backend... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
}

# Show deployment summary
show_summary() {
    log_success "Local deployment completed successfully!"
    echo
    echo "🎯 SmartShelf AI Local Deployment Summary:"
    echo "   Environment: Development"
    echo "   Backend: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo "   Health Check: http://localhost:8000/health"
    echo "   Metrics: http://localhost:8000/metrics"
    echo
    
    if [ -d "frontend" ] && [ -f ".frontend.pid" ]; then
        echo "   Frontend: http://localhost:3000"
    fi
    
    echo
    echo "🔧 Management Commands:"
    echo "   View logs: tail -f logs/app.log"
    echo "   Stop services: ./scripts/deploy-local.sh stop"
    echo "   Restart services: ./scripts/deploy-local.sh restart"
    echo "   Check status: ./scripts/deploy-local.sh status"
    echo
    echo "📝 Notes:"
    echo "   - Redis is optional but recommended for caching"
    echo "   - Set API keys in .env for full functionality"
    echo "   - Frontend requires Node.js to be installed"
    echo
}

# Stop services
stop_services() {
    log_info "Stopping services..."
    
    # Stop backend
    if [ -f ".backend.pid" ]; then
        BACKEND_PID=$(cat .backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            log_success "Backend stopped"
        fi
        rm .backend.pid
    fi
    
    # Stop frontend
    if [ -f ".frontend.pid" ]; then
        FRONTEND_PID=$(cat .frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            log_success "Frontend stopped"
        fi
        rm .frontend.pid
    fi
}

# Check status
check_status() {
    echo "📊 Service Status:"
    echo
    
    # Check backend
    if [ -f ".backend.pid" ]; then
        BACKEND_PID=$(cat .backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo "✅ Backend: Running (PID: $BACKEND_PID)"
        else
            echo "❌ Backend: Not running"
        fi
    else
        echo "❌ Backend: Not running"
    fi
    
    # Check frontend
    if [ -f ".frontend.pid" ]; then
        FRONTEND_PID=$(cat .frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            echo "✅ Frontend: Running (PID: $FRONTEND_PID)"
        else
            echo "❌ Frontend: Not running"
        fi
    else
        echo "❌ Frontend: Not running"
    fi
    
    # Check health endpoints
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo "✅ Backend Health: OK"
    else
        echo "❌ Backend Health: Not accessible"
    fi
    
    echo
}

# Main deployment function
main() {
    echo "🚀 SmartShelf AI Local Deployment Script"
    echo "=========================================="
    echo
    
    check_prerequisites
    install_dependencies
    setup_environment
    start_backend
    start_frontend
    wait_for_services
    show_summary
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        sleep 2
        main
        ;;
    "status")
        check_status
        ;;
    "logs")
        if [ -f "logs/app.log" ]; then
            tail -f logs/app.log
        else
            log_warning "No log file found"
        fi
        ;;
    *)
        echo "Usage: $0 {deploy|stop|restart|status|logs}"
        echo "  deploy   - Start all services (default)"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  status   - Check service status"
        echo "  logs     - Show application logs"
        exit 1
        ;;
esac
