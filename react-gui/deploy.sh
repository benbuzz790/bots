#!/bin/bash

# Production Deployment Script for React GUI Bot Framework
# This script handles complete production deployment with security hardening

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="bot-gui"
DOMAIN="${DOMAIN:-localhost}"
EMAIL="${EMAIL:-admin@localhost}"
ENVIRONMENT="${ENVIRONMENT:-production}"

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
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if running as root (not recommended)
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root is not recommended for security reasons."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    log_success "Prerequisites check passed"
}

# Generate SSL certificates
generate_ssl_certificates() {
    log_info "Generating SSL certificates..."
    
    mkdir -p ssl
    
    if [[ ! -f "ssl/cert.pem" ]] || [[ ! -f "ssl/key.pem" ]]; then
        if [[ "$DOMAIN" == "localhost" ]]; then
            # Generate self-signed certificate for localhost
            openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem \
                -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
            log_warning "Generated self-signed certificate for localhost. Not suitable for production!"
        else
            # For production, you should use Let's Encrypt or proper certificates
            log_error "For production deployment with domain $DOMAIN, please provide proper SSL certificates in ssl/ directory"
            log_info "You can use Let's Encrypt: certbot certonly --standalone -d $DOMAIN"
            exit 1
        fi
    else
        log_success "SSL certificates already exist"
    fi
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."
    
    # Create environment file if it doesn't exist
    if [[ ! -f ".env" ]]; then
        cp .env.production .env
        log_info "Created .env file from .env.production template"
        log_warning "Please review and customize .env file for your environment"
    fi
    
    # Create necessary directories
    mkdir -p storage logs
    
    # Set proper permissions
    chmod 755 storage logs
    
    log_success "Environment setup complete"
}

# Build and deploy
build_and_deploy() {
    log_info "Building and deploying application..."
    
    # Pull latest images
    docker-compose pull
    
    # Build application
    log_info "Building application images..."
    docker-compose build --no-cache
    
    # Stop existing containers
    log_info "Stopping existing containers..."
    docker-compose down
    
    # Start services
    log_info "Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Check health
    if curl -f http://localhost:8000/api/health &> /dev/null; then
        log_success "Application is running and healthy"
    else
        log_error "Application health check failed"
        docker-compose logs
        exit 1
    fi
}

# Run verification
run_verification() {
    log_info "Running system verification..."
    
    # Install Python dependencies for verification
    if command -v python3 &> /dev/null; then
        python3 -m pip install requests websockets --quiet
        
        # Run verification script
        if python3 verify_complete_system.py --wait-for-services; then
            log_success "System verification passed"
        else
            log_error "System verification failed"
            return 1
        fi
    else
        log_warning "Python3 not available, skipping automated verification"
        log_info "Please manually verify the system at https://$DOMAIN"
    fi
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Prometheus should already be started via docker-compose
    if curl -f http://localhost:9090 &> /dev/null; then
        log_success "Prometheus is running at http://localhost:9090"
    else
        log_warning "Prometheus may not be running properly"
    fi
    
    log_info "Consider setting up Grafana for visualization:"
    log_info "docker run -d -p 3000:3000 --name grafana grafana/grafana"
}

# Main deployment function
main() {
    log_info "Starting production deployment of React GUI Bot Framework"
    log_info "Domain: $DOMAIN"
    log_info "Environment: $ENVIRONMENT"
    
    cd "$SCRIPT_DIR"
    
    check_prerequisites
    generate_ssl_certificates
    setup_environment
    build_and_deploy
    
    if run_verification; then
        setup_monitoring
        
        log_success "Deployment completed successfully!"
        log_info "Application is available at: https://$DOMAIN"
        log_info "API documentation: https://$DOMAIN/docs"
        log_info "Health check: https://$DOMAIN/api/health"
        log_info "Monitoring: http://localhost:9090 (Prometheus)"
        
        log_info "To view logs: docker-compose logs -f"
        log_info "To stop: docker-compose down"
        log_info "To update: ./deploy.sh"
    else
        log_error "Deployment verification failed. Please check the logs."
        docker-compose logs
        exit 1
    fi
}

# Run main function
main "$@"
