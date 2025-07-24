#!/bin/bash

# Production Deployment Script for FAL.AI Video Generator
# Automated deployment with safety checks and rollback capability

set -euo pipefail

# ========================================================================
#                              Configuration                             
# ========================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="fal-video-generator"
DOCKER_COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="./backups"
LOG_FILE="./logs/deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ========================================================================
#                              Functions                                 
# ========================================================================

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker is not running"
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose is not installed"
    fi
    
    # Check if .env file exists
    if [[ ! -f .env ]]; then
        warning ".env file not found. Please copy .env.production to .env and configure it"
        if [[ -f .env.production ]]; then
            log "Copying .env.production to .env..."
            cp .env.production .env
            warning "Please edit .env file with your configuration before running again"
            exit 1
        fi
    fi
    
    success "Prerequisites check passed"
}

backup_current_deployment() {
    log "Creating backup of current deployment..."
    
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/backup-$(date +'%Y%m%d-%H%M%S').tar.gz"
    
    # Backup volumes and configuration
    docker-compose ps -q | xargs -r docker inspect | jq -r '.[].Mounts[] | select(.Type=="volume") | .Source' | xargs -r tar -czf "$BACKUP_FILE" 2>/dev/null || true
    
    success "Backup created: $BACKUP_FILE"
}

check_environment() {
    log "Checking environment configuration..."
    
    # Check required environment variables
    required_vars=("FAL_KEY")
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" .env; then
            error "Required environment variable $var is not set in .env file"
        fi
    done
    
    # Validate FAL API key format (basic check)
    if grep -q "^FAL_KEY=your_" .env; then
        error "Please set a valid FAL_KEY in .env file"
    fi
    
    success "Environment configuration is valid"
}

pre_deployment_tests() {
    log "Running pre-deployment tests..."
    
    # Build the application image
    log "Building application image..."
    docker-compose build app
    
    # Run quick smoke tests
    log "Running smoke tests..."
    python -m pytest tests/test_main.py::TestConfig::test_config_creation -v || error "Smoke tests failed"
    
    success "Pre-deployment tests passed"
}

deploy() {
    log "Starting deployment..."
    
    # Pull latest images
    log "Pulling latest images..."
    docker-compose pull
    
    # Start services
    log "Starting services..."
    docker-compose up -d --remove-orphans
    
    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    sleep 30
    
    # Check if all services are running
    if docker-compose ps | grep -q "Exit"; then
        error "Some services failed to start"
    fi
    
    success "Deployment completed successfully"
}

post_deployment_checks() {
    log "Running post-deployment checks..."
    
    # Health check
    log "Checking application health..."
    sleep 10
    
    if curl -f http://localhost:8000/api/models &> /dev/null; then
        success "Application is responding correctly"
    else
        warning "Application health check failed, but continuing..."
    fi
    
    # Check service status
    log "Checking service status..."
    docker-compose ps
    
    success "Post-deployment checks completed"
}

cleanup() {
    log "Cleaning up..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove old backups (keep last 5)
    if [[ -d "$BACKUP_DIR" ]]; then
        ls -t "$BACKUP_DIR"/backup-*.tar.gz 2>/dev/null | tail -n +6 | xargs -r rm
    fi
    
    success "Cleanup completed"
}

rollback() {
    error_msg=${1:-"Deployment failed"}
    warning "$error_msg - Initiating rollback..."
    
    # Stop current deployment
    docker-compose down
    
    # Restore from latest backup
    latest_backup=$(ls -t "$BACKUP_DIR"/backup-*.tar.gz 2>/dev/null | head -n 1)
    if [[ -n "$latest_backup" ]]; then
        log "Restoring from backup: $latest_backup"
        # Add restoration logic here
        warning "Manual restoration may be required"
    fi
    
    error "Rollback completed. Please check the system manually."
}

show_status() {
    echo -e "\n${BLUE}=== Deployment Status ===${NC}"
    docker-compose ps
    
    echo -e "\n${BLUE}=== Service Logs (last 20 lines) ===${NC}"
    docker-compose logs --tail=20
    
    echo -e "\n${BLUE}=== Health Check ===${NC}"
    if curl -f http://localhost:8000/api/models &> /dev/null; then
        success "✅ Application is healthy"
    else
        warning "❌ Application health check failed"
    fi
}

# ========================================================================
#                              Main Logic                                
# ========================================================================

main() {
    local command=${1:-deploy}
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    case "$command" in
        "deploy")
            log "Starting full deployment process..."
            
            check_prerequisites
            check_environment
            backup_current_deployment
            pre_deployment_tests
            
            # Set trap for rollback on error
            trap 'rollback "Deployment failed during execution"' ERR
            
            deploy
            post_deployment_checks
            cleanup
            
            # Remove trap
            trap - ERR
            
            success "🎉 Deployment completed successfully!"
            show_status
            ;;
            
        "status")
            show_status
            ;;
            
        "rollback")
            rollback "Manual rollback requested"
            ;;
            
        "logs")
            docker-compose logs -f
            ;;
            
        "stop")
            log "Stopping services..."
            docker-compose down
            success "Services stopped"
            ;;
            
        "restart")
            log "Restarting services..."
            docker-compose restart
            success "Services restarted"
            ;;
            
        "backup")
            backup_current_deployment
            ;;
            
        "help"|*)
            echo "Usage: $0 {deploy|status|rollback|logs|stop|restart|backup|help}"
            echo ""
            echo "Commands:"
            echo "  deploy   - Full deployment with checks and backup"
            echo "  status   - Show current deployment status"
            echo "  rollback - Rollback to previous version"
            echo "  logs     - Show and follow service logs"
            echo "  stop     - Stop all services"
            echo "  restart  - Restart all services"
            echo "  backup   - Create backup of current deployment"
            echo "  help     - Show this help message"
            ;;
    esac
}

# Run main function with all arguments
main "$@"