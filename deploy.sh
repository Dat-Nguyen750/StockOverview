#!/bin/bash

# Production Deployment Script for Stock Evaluator API
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="stock-evaluator"
BACKUP_DIR="./backups"
LOG_FILE="./deploy.log"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a $LOG_FILE
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a $LOG_FILE
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root"
fi

# Function to validate environment
validate_environment() {
    log "Validating environment variables..."
    
    required_vars=(
        "FMP_API_KEY"
        "SERP_API_KEY"
        "GOOGLE_GEMINI_API_KEY"
        "SECRET_KEY"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        error "Missing required environment variables: ${missing_vars[*]}"
    fi
    
    log "Environment validation passed"
}

# Function to create backup
create_backup() {
    log "Creating backup..."
    
    mkdir -p $BACKUP_DIR
    backup_name="${APP_NAME}-$(date +%Y%m%d-%H%M%S)"
    
    # Backup current deployment
    if docker-compose ps | grep -q "stock-evaluator-api"; then
        docker-compose down
        log "Stopped current deployment"
    fi
    
    # Backup data volumes
    if docker volume ls | grep -q "stock_evaluator_redis_data"; then
        docker run --rm -v stock_evaluator_redis_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/${backup_name}-redis.tar.gz -C /data .
        log "Redis data backed up"
    fi
    
    # Backup logs
    if [[ -d "./logs" ]]; then
        tar czf "$BACKUP_DIR/${backup_name}-logs.tar.gz" logs/
        log "Logs backed up"
    fi
    
    log "Backup completed: $backup_name"
}

# Function to deploy
deploy() {
    log "Starting deployment..."
    
    # Pull latest changes
    if [[ -d ".git" ]]; then
        log "Pulling latest changes..."
        git pull origin main || warning "Could not pull latest changes"
    fi
    
    # Build and start services
    log "Building Docker images..."
    docker-compose build --no-cache
    
    log "Starting services..."
    docker-compose up -d
    
    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    timeout=300
    counter=0
    
    while [[ $counter -lt $timeout ]]; do
        if docker-compose ps | grep -q "healthy"; then
            log "All services are healthy"
            break
        fi
        sleep 5
        counter=$((counter + 5))
    done
    
    if [[ $counter -ge $timeout ]]; then
        error "Services failed to become healthy within $timeout seconds"
    fi
    
    # Test the API
    log "Testing API health..."
    sleep 10
    
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log "API health check passed"
    else
        error "API health check failed"
    fi
    
    log "Deployment completed successfully"
}

# Function to rollback
rollback() {
    log "Starting rollback..."
    
    # Stop current deployment
    docker-compose down
    
    # Find latest backup
    latest_backup=$(ls -t $BACKUP_DIR/*-redis.tar.gz 2>/dev/null | head -1)
    
    if [[ -n "$latest_backup" ]]; then
        log "Restoring from backup: $latest_backup"
        
        # Restore Redis data
        docker run --rm -v stock_evaluator_redis_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine sh -c "cd /data && tar xzf /backup/$(basename $latest_backup)"
        
        # Restart services
        docker-compose up -d
        
        log "Rollback completed"
    else
        error "No backup found for rollback"
    fi
}

# Function to show status
status() {
    log "Current deployment status:"
    docker-compose ps
    
    echo ""
    log "Service logs (last 20 lines):"
    docker-compose logs --tail=20
}

# Function to show usage
usage() {
    echo "Usage: $0 {deploy|rollback|status|validate}"
    echo ""
    echo "Commands:"
    echo "  deploy    - Deploy the application"
    echo "  rollback  - Rollback to previous deployment"
    echo "  status    - Show current deployment status"
    echo "  validate  - Validate environment variables"
    echo ""
    echo "Environment variables required:"
    echo "  FMP_API_KEY"
    echo "  SERP_API_KEY"
    echo "  GOOGLE_GEMINI_API_KEY"
    echo "  SECRET_KEY"
}

# Main script logic
case "$1" in
    deploy)
        validate_environment
        create_backup
        deploy
        ;;
    rollback)
        rollback
        ;;
    status)
        status
        ;;
    validate)
        validate_environment
        ;;
    *)
        usage
        exit 1
        ;;
esac 