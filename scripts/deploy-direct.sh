#!/bin/bash

# SmartShelf AI Chat Service - Direct Python Deployment
# For systems without Docker

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check virtual environment
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        source venv/bin/activate
    fi
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        log_error ".env file not found. Please copy .env.example to .env and configure it."
        exit 1
    fi
    
    # Check API keys
    if ! grep -q "OPENAI_API_KEY=sk-" .env || grep -q "OPENAI_API_KEY=$" .env; then
        log_error "Please set OPENAI_API_KEY in .env file"
        exit 1
    fi
    
    if ! grep -q "ANTHROPIC_API_KEY=" .env || grep -q "ANTHROPIC_API_KEY=$" .env; then
        log_error "Please set ANTHROPIC_API_KEY in .env file"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."
    
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log_success "Dependencies installed"
}

# Start the service
start_service() {
    log_info "Starting SmartShelf AI Chat Service..."
    
    # Load environment variables
    export $(cat .env | grep -v '^#' | xargs)
    
    # Start the service
    python -m copilot_chatbot.main
}

# Health check
health_check() {
    log_info "Waiting for service to start..."
    sleep 10
    
    for i in {1..30}; do
        if curl -f http://localhost:8001/health &>/dev/null; then
            log_success "Service is healthy and running!"
            return 0
        fi
        log_info "Health check attempt $i/30..."
        sleep 2
    done
    
    log_error "Health check failed"
    return 1
}

# Main deployment
deploy() {
    log_info "Starting direct Python deployment..."
    
    check_prerequisites
    install_dependencies
    
    # Start service in background
    log_info "Starting service in background..."
    start_service &
    SERVICE_PID=$!
    
    # Wait a moment then check health
    sleep 5
    if health_check; then
        log_success "🎉 Deployment successful!"
        log_info "Service is running at: http://localhost:8001"
        log_info "API Docs: http://localhost:8001/docs"
        log_info "Health Check: http://localhost:8001/health"
        log_info "Process ID: $SERVICE_PID"
        log_info "Stop with: kill $SERVICE_PID"
    else
        log_error "❌ Deployment failed"
        kill $SERVICE_PID 2>/dev/null || true
        exit 1
    fi
}

# Handle arguments
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "start")
        check_prerequisites
        start_service
        ;;
    "health")
        health_check
        ;;
    "stop")
        pkill -f "copilot_chatbot.main" || log_info "No running service found"
        ;;
    *)
        echo "Usage: $0 {deploy|start|health|stop}"
        echo "  deploy - Full deployment (default)"
        echo "  start  - Start service only"
        echo "  health - Run health check"
        echo "  stop   - Stop service"
        exit 1
        ;;
esac
