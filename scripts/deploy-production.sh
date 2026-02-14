#!/bin/bash

# SmartShelf AI Chat Service - Production Deployment Script
# This script handles the complete production deployment process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="smartshelf-chat"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
ENVIRONMENT="${ENVIRONMENT:-production}"

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
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        log_warning ".env file not found. Creating from template..."
        cp .env.example .env
        log_warning "Please edit .env file with your API keys and configuration."
        log_warning "Then run this script again."
        exit 1
    fi
    
    # Check required environment variables
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

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    
    local image_name="${PROJECT_NAME}"
    if [ -n "$DOCKER_REGISTRY" ]; then
        image_name="${DOCKER_REGISTRY}/${image_name}"
    fi
    
    docker build \
        -f Dockerfile.prod \
        -t "${image_name}:${IMAGE_TAG}" \
        -t "${image_name}:latest" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        --build-arg VERSION="$IMAGE_TAG" \
        .
    
    log_success "Docker image built successfully"
}

# Push to registry (if configured)
push_to_registry() {
    if [ -n "$DOCKER_REGISTRY" ]; then
        log_info "Pushing image to registry..."
        local image_name="${DOCKER_REGISTRY}/${PROJECT_NAME}"
        
        docker push "${image_name}:${IMAGE_TAG}"
        docker push "${image_name}:latest"
        
        log_success "Image pushed to registry"
    else
        log_info "No Docker registry configured, skipping push"
    fi
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."
    
    # Set environment variables for docker-compose
    export BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    export VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    export VERSION="$IMAGE_TAG"
    
    # Stop existing services
    log_info "Stopping existing services..."
    docker-compose -f docker-compose.prod.yml down
    
    # Start new services
    log_info "Starting new services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    log_success "Services deployed successfully"
}

# Health check
health_check() {
    log_info "Performing health check..."
    
    # Wait for services to start
    sleep 30
    
    # Check main service health
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8001/health &>/dev/null; then
            log_success "Health check passed"
            return 0
        fi
        
        log_info "Health check attempt $attempt/$max_attempts failed, retrying in 10 seconds..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Health check failed after $max_attempts attempts"
    return 1
}

# Show deployment status
show_status() {
    log_info "Deployment status:"
    docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    log_info "Service URLs:"
    echo "  - Chat API: http://localhost:8001"
    echo "  - Health Check: http://localhost:8001/health"
    echo "  - API Docs: http://localhost:8001/docs"
    
    if docker-compose -f docker-compose.prod.yml ps | grep -q "nginx"; then
        echo "  - Nginx Proxy: http://localhost"
    fi
}

# Cleanup old images
cleanup() {
    log_info "Cleaning up old Docker images..."
    docker image prune -f
    log_success "Cleanup completed"
}

# Main deployment function
deploy() {
    log_info "Starting production deployment..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Image Tag: $IMAGE_TAG"
    
    check_prerequisites
    build_image
    push_to_registry
    deploy_services
    
    if health_check; then
        show_status
        cleanup
        log_success "🎉 Production deployment completed successfully!"
    else
        log_error "❌ Deployment failed - health check did not pass"
        log_error "Check logs with: docker-compose -f docker-compose.prod.yml logs"
        exit 1
    fi
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "build")
        check_prerequisites
        build_image
        ;;
    "push")
        push_to_registry
        ;;
    "health")
        health_check
        ;;
    "status")
        show_status
        ;;
    "logs")
        docker-compose -f docker-compose.prod.yml logs -f
        ;;
    "stop")
        docker-compose -f docker-compose.prod.yml down
        log_success "Services stopped"
        ;;
    "restart")
        docker-compose -f docker-compose.prod.yml restart
        log_success "Services restarted"
        ;;
    *)
        echo "Usage: $0 {deploy|build|push|health|status|logs|stop|restart}"
        echo ""
        echo "Commands:"
        echo "  deploy  - Full production deployment (default)"
        echo "  build   - Build Docker image only"
        echo "  push    - Push image to registry"
        echo "  health  - Run health check"
        echo "  status  - Show deployment status"
        echo "  logs    - Show service logs"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        exit 1
        ;;
esac
