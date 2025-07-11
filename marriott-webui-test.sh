#!/bin/bash

# 🏨 Marriott InfoBlox WebUI - Test & Status Script
# This script checks status, shows logs, and provides troubleshooting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_header() { echo -e "${PURPLE}$1${NC}"; }
print_step() { echo -e "${CYAN}▶${NC} $1"; }

# Configuration
PROJECT_ROOT="/Users/tshoush/apps/infoblox-mcp-server"
CORPORATE_DIR="$PROJECT_ROOT/corporate-infoblox-webui"
PORT=3000

print_header "🏨 Marriott InfoBlox WebUI - Test & Status Check"
print_header "=============================================="

# Navigate to project directory
if [ ! -d "$PROJECT_ROOT" ]; then
    print_error "Project directory not found: $PROJECT_ROOT"
    exit 1
fi

cd "$PROJECT_ROOT"
print_info "Working from: $(pwd)"

# Check if corporate directory exists
if [ ! -d "$CORPORATE_DIR" ]; then
    print_error "Corporate directory not found: $CORPORATE_DIR"
    print_info "Please run the setup script first: ./marriott-webui-setup.sh"
    exit 1
fi

cd "$CORPORATE_DIR"
print_info "Corporate directory: $(pwd)"

# Function to show menu
show_menu() {
    print_header "📋 Available Actions:"
    echo "1. Check Status"
    echo "2. View Logs"
    echo "3. Test Application"
    echo "4. Restart Services"
    echo "5. Stop Services"
    echo "6. Start Services"
    echo "7. Rebuild Application"
    echo "8. Troubleshoot"
    echo "9. Exit"
    echo ""
    read -p "Choose an action (1-9): " choice
}

# Function to check status
check_status() {
    print_step "Checking application status..."
    
    # Check Docker containers
    print_info "Container Status:"
    if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep marriott; then
        print_status "Containers are running"
    else
        print_warning "No Marriott containers found running"
        print_info "All containers:"
        docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    fi
    
    echo ""
    
    # Check application health
    print_info "Application Health:"
    if curl -s http://localhost:$PORT/health >/dev/null 2>&1; then
        response=$(curl -s http://localhost:$PORT/health)
        print_status "Application is responding: $response"
    else
        print_warning "Application is not responding on port $PORT"
    fi
    
    # Check database
    print_info "Database Status:"
    if docker exec marriott-infoblox-webui-db pg_isready -U webui -d marriott_webui >/dev/null 2>&1; then
        print_status "Database is ready"
    else
        print_warning "Database is not ready"
    fi
    
    # Check Redis
    print_info "Redis Status:"
    if docker exec marriott-infoblox-webui-redis redis-cli ping >/dev/null 2>&1; then
        print_status "Redis is ready"
    else
        print_warning "Redis is not ready"
    fi
}

# Function to view logs
view_logs() {
    print_step "Viewing application logs..."
    echo ""
    print_info "Choose log type:"
    echo "1. All services"
    echo "2. Main application only"
    echo "3. Database only"
    echo "4. Redis only"
    echo "5. Follow logs (real-time)"
    echo ""
    read -p "Choose (1-5): " log_choice
    
    case $log_choice in
        1)
            print_info "Showing all service logs (last 50 lines):"
            docker-compose logs --tail=50
            ;;
        2)
            print_info "Showing main application logs (last 50 lines):"
            docker logs --tail=50 marriott-infoblox-webui
            ;;
        3)
            print_info "Showing database logs (last 50 lines):"
            docker logs --tail=50 marriott-infoblox-webui-db
            ;;
        4)
            print_info "Showing Redis logs (last 50 lines):"
            docker logs --tail=50 marriott-infoblox-webui-redis
            ;;
        5)
            print_info "Following logs in real-time (Ctrl+C to stop):"
            docker-compose logs -f
            ;;
        *)
            print_error "Invalid choice"
            ;;
    esac
}

# Function to test application
test_application() {
    print_step "Testing application functionality..."
    
    # Test 1: Basic connectivity
    print_info "Test 1: Basic connectivity"
    if curl -s http://localhost:$PORT >/dev/null 2>&1; then
        print_status "✅ Application is accessible"
    else
        print_error "❌ Application is not accessible"
    fi
    
    # Test 2: Health endpoint
    print_info "Test 2: Health endpoint"
    health_response=$(curl -s http://localhost:$PORT/health 2>/dev/null || echo "failed")
    if echo "$health_response" | grep -q "healthy\|running"; then
        print_status "✅ Health check passed: $health_response"
    else
        print_error "❌ Health check failed: $health_response"
    fi
    
    # Test 3: Container health
    print_info "Test 3: Container health checks"
    
    # Check main app
    if docker inspect marriott-infoblox-webui --format='{{.State.Health.Status}}' 2>/dev/null | grep -q "healthy"; then
        print_status "✅ Main application container is healthy"
    else
        print_warning "⚠️ Main application container health unknown"
    fi
    
    # Check database
    if docker exec marriott-infoblox-webui-db pg_isready -U webui >/dev/null 2>&1; then
        print_status "✅ Database is healthy"
    else
        print_error "❌ Database is not healthy"
    fi
    
    # Check Redis
    if docker exec marriott-infoblox-webui-redis redis-cli ping >/dev/null 2>&1; then
        print_status "✅ Redis is healthy"
    else
        print_error "❌ Redis is not healthy"
    fi
    
    # Test 4: Port accessibility
    print_info "Test 4: Port accessibility"
    if netstat -an 2>/dev/null | grep ":$PORT " | grep -q LISTEN; then
        print_status "✅ Port $PORT is listening"
    else
        print_warning "⚠️ Port $PORT may not be accessible"
    fi
    
    print_header "🌐 Access Information:"
    print_info "Application URL: http://localhost:$PORT"
    print_info "To access from browser, open: http://localhost:$PORT"
}

# Function to restart services
restart_services() {
    print_step "Restarting services..."
    docker-compose restart
    print_status "Services restarted"
    
    print_info "Waiting for services to be ready..."
    sleep 10
    check_status
}

# Function to stop services
stop_services() {
    print_step "Stopping services..."
    docker-compose down
    print_status "Services stopped"
}

# Function to start services
start_services() {
    print_step "Starting services..."
    docker-compose up -d
    print_status "Services started"
    
    print_info "Waiting for services to be ready..."
    sleep 15
    check_status
}

# Function to rebuild application
rebuild_application() {
    print_step "Rebuilding application..."
    print_warning "This will stop the application and rebuild from scratch"
    read -p "Are you sure? (y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
        print_status "Application rebuilt and started"
        
        print_info "Waiting for services to be ready..."
        sleep 20
        check_status
    else
        print_info "Rebuild cancelled"
    fi
}

# Function to troubleshoot
troubleshoot() {
    print_step "Running troubleshooting diagnostics..."
    
    print_info "1. Docker system information:"
    docker system df
    echo ""
    
    print_info "2. Available disk space:"
    df -h . 2>/dev/null || echo "Disk space check failed"
    echo ""
    
    print_info "3. Docker container details:"
    docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Size}}"
    echo ""
    
    print_info "4. Network connectivity:"
    if command -v netstat >/dev/null 2>&1; then
        netstat -an | grep ":$PORT " || echo "Port $PORT not found in netstat"
    else
        print_warning "netstat not available"
    fi
    echo ""
    
    print_info "5. Recent container logs (errors only):"
    docker logs marriott-infoblox-webui 2>&1 | grep -i error | tail -5 || echo "No recent errors found"
    echo ""
    
    print_info "6. Environment check:"
    if [ -f ".env" ]; then
        print_status "Environment file exists"
        echo "Key variables:"
        grep -E "^(CORPORATE_NAME|PORT|DATABASE_URL)" .env || echo "Variables not found"
    else
        print_error "Environment file missing"
    fi
    echo ""
    
    print_header "🔧 Common Solutions:"
    echo "1. If containers won't start: docker-compose down && docker-compose up -d"
    echo "2. If port is busy: docker-compose down && docker system prune -f"
    echo "3. If database issues: docker volume rm \$(docker volume ls -q | grep postgres)"
    echo "4. If build issues: docker-compose build --no-cache"
    echo "5. If permission issues: sudo chown -R \$USER:docker /var/run/docker.sock"
}

# Main menu loop
while true; do
    echo ""
    show_menu
    
    case $choice in
        1)
            check_status
            ;;
        2)
            view_logs
            ;;
        3)
            test_application
            ;;
        4)
            restart_services
            ;;
        5)
            stop_services
            ;;
        6)
            start_services
            ;;
        7)
            rebuild_application
            ;;
        8)
            troubleshoot
            ;;
        9)
            print_info "Goodbye! 👋"
            exit 0
            ;;
        *)
            print_error "Invalid choice. Please select 1-9."
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done
