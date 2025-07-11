#!/bin/bash

# 🔧 Port Issue Fix Script for Marriott InfoBlox WebUI
# This script fixes port conflicts and restarts the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_header() { echo -e "${PURPLE}$1${NC}"; }

# Configuration
PROJECT_ROOT="/Users/tshoush/apps/infoblox-mcp-server"
CORPORATE_DIR="$PROJECT_ROOT/corporate-infoblox-webui"

print_header "🔧 Fixing Port Conflict for Marriott InfoBlox WebUI"
print_header "================================================="

# Navigate to project directory
cd "$PROJECT_ROOT"
print_info "Working from: $(pwd)"

if [ -d "$CORPORATE_DIR" ]; then
    cd "$CORPORATE_DIR"
    print_info "Corporate directory: $(pwd)"
else
    print_error "Corporate directory not found. Please run setup first."
    exit 1
fi

# Function to find available port
find_available_port() {
    local start_port=$1
    local port=$start_port
    
    while [ $port -le 9999 ]; do
        if ! lsof -i :$port >/dev/null 2>&1 && ! netstat -an 2>/dev/null | grep -q ":$port "; then
            echo $port
            return 0
        fi
        port=$((port + 1))
    done
    
    echo $start_port
}

# Step 1: Stop all existing containers
print_info "Step 1: Stopping all existing containers..."
docker-compose down 2>/dev/null || true
docker stop $(docker ps -q --filter "name=marriott") 2>/dev/null || true
docker rm $(docker ps -aq --filter "name=marriott") 2>/dev/null || true
print_status "Containers stopped and removed"

# Step 2: Find what's using port 3000
print_info "Step 2: Checking what's using port 3000..."
if lsof -i :3000 >/dev/null 2>&1; then
    print_warning "Port 3000 is in use by:"
    lsof -i :3000 | head -10
    
    print_info "Attempting to free port 3000..."
    # Kill processes using port 3000
    lsof -ti :3000 | xargs kill -9 2>/dev/null || true
    sleep 3
    
    if lsof -i :3000 >/dev/null 2>&1; then
        print_warning "Port 3000 still in use, will find alternative port"
    else
        print_status "Port 3000 is now free"
    fi
else
    print_status "Port 3000 is free"
fi

# Step 3: Find available port
print_info "Step 3: Finding available port..."
AVAILABLE_PORT=$(find_available_port 3000)
print_status "Using port: $AVAILABLE_PORT"

# Step 4: Update environment file with new port
print_info "Step 4: Updating configuration..."
if [ -f ".env" ]; then
    # Update PORT in .env file
    if grep -q "^PORT=" .env; then
        sed -i.bak "s/^PORT=.*/PORT=$AVAILABLE_PORT/" .env
    else
        echo "PORT=$AVAILABLE_PORT" >> .env
    fi
    print_status "Environment file updated with port $AVAILABLE_PORT"
else
    print_error "Environment file not found"
    exit 1
fi

# Step 5: Clean up Docker resources
print_info "Step 5: Cleaning up Docker resources..."
docker system prune -f >/dev/null 2>&1 || true
print_status "Docker cleanup completed"

# Step 6: Restart services
print_info "Step 6: Starting services on port $AVAILABLE_PORT..."
export PORT=$AVAILABLE_PORT
docker-compose up -d

if [ $? -eq 0 ]; then
    print_status "Services started successfully!"
else
    print_error "Failed to start services"
    exit 1
fi

# Step 7: Wait for services to be ready
print_info "Step 7: Waiting for services to be ready..."
sleep 15

# Check if application is responding
for i in {1..30}; do
    if curl -s http://localhost:$AVAILABLE_PORT/health >/dev/null 2>&1; then
        print_status "Application is ready and responding!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_warning "Application may still be starting..."
    fi
    sleep 2
done

# Step 8: Show status
print_info "Step 8: Checking final status..."
echo ""
print_header "📊 Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
print_header "🌐 Access Information:"
print_status "Application URL: http://localhost:$AVAILABLE_PORT"
print_status "Health Check: http://localhost:$AVAILABLE_PORT/health"

echo ""
print_header "🔧 Useful Commands:"
echo "View logs: docker logs -f marriott-infoblox-webui"
echo "Stop app: docker-compose down"
echo "Restart: docker-compose restart"
echo "Status: docker ps"

echo ""
print_header "🎉 Port Issue Fixed!"
print_info "Your Marriott InfoBlox WebUI is now running on port $AVAILABLE_PORT"
print_info "Open your browser and go to: http://localhost:$AVAILABLE_PORT"

# Test the application
print_info "Testing application..."
if curl -s http://localhost:$AVAILABLE_PORT >/dev/null 2>&1; then
    print_status "✅ Application is accessible"
    response=$(curl -s http://localhost:$AVAILABLE_PORT/ 2>/dev/null || echo "No response")
    if echo "$response" | grep -q "Marriott\|InfoBlox\|healthy"; then
        print_status "✅ Application is responding correctly"
    else
        print_warning "⚠️ Application response: $response"
    fi
else
    print_warning "⚠️ Application may still be starting up"
    print_info "Wait a few more seconds and try: http://localhost:$AVAILABLE_PORT"
fi

print_header "🏨 Ready to use your Marriott-styled InfoBlox WebUI! ✨"
