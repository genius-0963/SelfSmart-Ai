#!/bin/bash

# SmartShelf AI - Enhanced Production Deployment Script
# Deploys the enhanced system with monitoring and caching

set -e

# Configuration
PROJECT_NAME="smartshelf-ai"
DOCKER_REGISTRY="your-registry.com"
VERSION="2.0.0"
ENVIRONMENT="production"

echo "🚀 Starting SmartShelf AI Enhanced Deployment..."

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
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check environment variables
    if [ -z "$OPENAI_API_KEY" ]; then
        log_warning "OPENAI_API_KEY not set"
    fi
    
    if [ -z "$AMAZON_API_KEY" ]; then
        log_warning "AMAZON_API_KEY not set"
    fi
    
    log_success "Prerequisites check completed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    # Build backend image
    docker build -f Dockerfile.production -t ${PROJECT_NAME}-backend:${VERSION} .
    
    # Tag for registry if needed
    if [ -n "$DOCKER_REGISTRY" ]; then
        docker tag ${PROJECT_NAME}-backend:${VERSION} ${DOCKER_REGISTRY}/${PROJECT_NAME}-backend:${VERSION}
    fi
    
    log_success "Docker images built successfully"
}

# Push to registry (optional)
push_to_registry() {
    if [ -n "$DOCKER_REGISTRY" ]; then
        log_info "Pushing images to registry..."
        
        docker push ${DOCKER_REGISTRY}/${PROJECT_NAME}-backend:${VERSION}
        
        log_success "Images pushed to registry"
    else
        log_info "Skipping registry push (no registry configured)"
    fi
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."
    
    # Create necessary directories
    mkdir -p logs uploads monitoring/grafana/dashboards monitoring/grafana/datasources nginx/ssl
    
    # Create monitoring configuration if not exists
    if [ ! -f "monitoring/prometheus.yml" ]; then
        cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'smartshelf-backend'
    static_configs:
      - targets: ['smartshelf-backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
EOF
    fi
    
    # Create Grafana datasource if not exists
    if [ ! -f "monitoring/grafana/datasources/prometheus.yml" ]; then
        mkdir -p monitoring/grafana/datasources
        cat > monitoring/grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF
    fi
    
    # Stop existing services
    log_info "Stopping existing services..."
    docker compose -f docker-compose.production.yml down || true
    
    # Start services
    log_info "Starting services..."
    docker compose -f docker-compose.production.yml up -d
    
    log_success "Services deployed successfully"
}

# Wait for services to be healthy
wait_for_health() {
    log_info "Waiting for services to be healthy..."
    
    # Wait for backend
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "Backend is healthy"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Backend failed to become healthy"
            exit 1
        fi
        
        log_info "Waiting for backend... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    # Wait for Redis
    if docker exec smartshelf-redis redis-cli ping &> /dev/null; then
        log_success "Redis is healthy"
    else
        log_error "Redis failed to become healthy"
        exit 1
    fi
    
    # Wait for PostgreSQL
    if docker exec smartshelf-postgres pg_isready -U smartshelf -d smartshelf &> /dev/null; then
        log_success "PostgreSQL is healthy"
    else
        log_error "PostgreSQL failed to become healthy"
        exit 1
    fi
}

# Run health checks
run_health_checks() {
    log_info "Running comprehensive health checks..."
    
    # Backend health check
    BACKEND_HEALTH=$(curl -s http://localhost:8000/health | jq -r '.status // "unknown"')
    if [ "$BACKEND_HEALTH" = "healthy" ]; then
        log_success "Backend health check passed"
    else
        log_warning "Backend health check: $BACKEND_HEALTH"
    fi
    
    # Check metrics endpoint
    if curl -f http://localhost:8000/metrics &> /dev/null; then
        log_success "Metrics endpoint accessible"
    else
        log_warning "Metrics endpoint not accessible"
    fi
    
    # Check Prometheus
    if curl -f http://localhost:9090/-/healthy &> /dev/null; then
        log_success "Prometheus is healthy"
    else
        log_warning "Prometheus not accessible"
    fi
    
    # Check Grafana
    if curl -f http://localhost:3000/api/health &> /dev/null; then
        log_success "Grafana is healthy"
    else
        log_warning "Grafana not accessible"
    fi
}

# Show deployment summary
show_summary() {
    log_success "Deployment completed successfully!"
    echo
    echo "🎯 SmartShelf AI Enhanced Deployment Summary:"
    echo "   Version: $VERSION"
    echo "   Environment: $ENVIRONMENT"
    echo
    echo "📊 Service URLs:"
    echo "   Backend API: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo "   Health Check: http://localhost:8000/health"
    echo "   Metrics: http://localhost:8000/metrics"
    echo "   Prometheus: http://localhost:9090"
    echo "   Grafana: http://localhost:3000 (admin/admin123)"
    echo
    echo "🔧 Management Commands:"
    echo "   View logs: docker compose -f docker-compose.production.yml logs -f"
    echo "   Stop services: docker compose -f docker-compose.production.yml down"
    echo "   Restart services: docker compose -f docker-compose.production.yml restart"
    echo "   Check status: docker compose -f docker-compose.production.yml ps"
    echo
    echo "📈 Monitoring:"
    echo "   System metrics: http://localhost:9090"
    echo "   Dashboards: http://localhost:3000"
    echo "   Logs: ./logs/"
    echo
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    # Remove unused Docker images
    docker image prune -f
    log_success "Cleanup completed"
}

# Main execution
main() {
    echo "🚀 SmartShelf AI Enhanced Deployment Script"
    echo "=========================================="
    echo
    
    # Trap cleanup on exit
    trap cleanup EXIT
    
    # Execute deployment steps
    check_prerequisites
    build_images
    push_to_registry
    deploy_services
    wait_for_health
    run_health_checks
    show_summary
    
    log_success "Enhanced deployment completed successfully! 🎉"
}

# Handle script arguments
case "${1:-deploy}" in
    "build")
        build_images
        ;;
    "push")
        push_to_registry
        ;;
    "deploy")
        main
        ;;
    "health")
        run_health_checks
        ;;
    "cleanup")
        cleanup
        ;;
    "logs")
        docker compose -f docker-compose.production.yml logs -f
        ;;
    "stop")
        docker compose -f docker-compose.production.yml down
        ;;
    "restart")
        docker compose -f docker-compose.production.yml restart
        ;;
    "status")
        docker compose -f docker-compose.production.yml ps
        ;;
    *)
        echo "Usage: $0 {build|push|deploy|health|cleanup|logs|stop|restart|status}"
        echo "  build    - Build Docker images"
        echo "  push     - Push images to registry"
        echo "  deploy   - Full deployment (default)"
        echo "  health   - Run health checks"
        echo "  cleanup  - Clean up unused resources"
        echo "  logs     - Show service logs"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  status   - Show service status"
        exit 1
        ;;
esac
