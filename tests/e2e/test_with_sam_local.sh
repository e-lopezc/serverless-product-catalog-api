#!/bin/bash

# SAM Local E2E Test Workflow Script
# This script handles the complete workflow for running E2E tests with SAM local

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SAM_PORT=3000
DYNAMODB_PORT=8000
DYNAMODB_CONTAINER_NAME="dynamodb-local-test"
TEST_TIMEOUT=300

# Functions
print_header() {
    echo -e "${BLUE}================================================================================================${NC}"
    echo -e "${BLUE}🧪 SAM Local E2E Test Workflow${NC}"
    echo -e "${BLUE}================================================================================================${NC}"
}

print_step() {
    echo -e "\n${BLUE}🔹 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

cleanup() {
    print_step "Cleaning up..."

    # Stop SAM local if running
    if [ ! -z "$SAM_PID" ]; then
        print_step "Stopping SAM local (PID: $SAM_PID)"
        kill $SAM_PID 2>/dev/null || true
        wait $SAM_PID 2>/dev/null || true
    fi

    # Stop DynamoDB Local container if we started it
    if [ "$STARTED_DYNAMODB" = "true" ]; then
        print_step "Stopping DynamoDB Local container"
        docker stop $DYNAMODB_CONTAINER_NAME 2>/dev/null || true
        docker rm $DYNAMODB_CONTAINER_NAME 2>/dev/null || true
    fi

    print_success "Cleanup completed"
}

# Set up trap for cleanup
trap cleanup EXIT

check_dependencies() {
    print_step "Checking dependencies..."

    # Check SAM CLI
    if ! command -v sam &> /dev/null; then
        print_error "SAM CLI not found"
        echo "Install SAM CLI: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
        exit 1
    fi
    print_success "SAM CLI found: $(sam --version)"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found"
        echo "Install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker found: $(docker --version)"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 not found"
        exit 1
    fi
    print_success "Python3 found: $(python3 --version)"

    # Check if requests library is available
    if ! python3 -c "import requests" 2>/dev/null; then
        print_warning "Python 'requests' library not found"
        print_step "Installing requests library..."
        pip3 install requests
        print_success "Requests library installed"
    else
        print_success "Python requests library found"
    fi
}

check_template() {
    print_step "Checking SAM template..."

    TEMPLATE_FILE=""
    for template in template.yaml template.yml sam-template.yaml sam-template.yml; do
        if [ -f "$template" ]; then
            TEMPLATE_FILE="$template"
            break
        fi
    done

    if [ -z "$TEMPLATE_FILE" ]; then
        print_error "No SAM template file found"
        echo "Expected one of: template.yaml, template.yml, sam-template.yaml, sam-template.yml"
        exit 1
    fi

    print_success "Using template: $TEMPLATE_FILE"
}

build_sam_app() {
    print_step "Building SAM application..."

    if [ -d ".aws-sam/build" ]; then
        # Check if build is up to date
        if [ "$TEMPLATE_FILE" -nt ".aws-sam/build" ]; then
            print_warning "Template is newer than build, rebuilding..."
            sam build
        else
            print_success "Build is up to date"
        fi
    else
        print_step "Building for the first time..."
        sam build
    fi

    print_success "SAM application built successfully"
}

start_dynamodb_local() {
    print_step "Starting DynamoDB Local..."

    # Check if DynamoDB Local is already running
    if curl -s http://localhost:$DYNAMODB_PORT > /dev/null 2>&1; then
        print_success "DynamoDB Local already running on port $DYNAMODB_PORT"
        STARTED_DYNAMODB="false"
        return 0
    fi

    # Start DynamoDB Local using Docker
    print_step "Starting DynamoDB Local container..."
    docker run -d \
        --name $DYNAMODB_CONTAINER_NAME \
        -p $DYNAMODB_PORT:8000 \
        amazon/dynamodb-local \
        -jar DynamoDBLocal.jar -sharedDb -inMemory

    STARTED_DYNAMODB="true"

    # Wait for DynamoDB Local to be ready
    print_step "Waiting for DynamoDB Local to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:$DYNAMODB_PORT > /dev/null 2>&1; then
            print_success "DynamoDB Local is ready"
            return 0
        fi
        echo -n "."
        sleep 1
    done

    print_error "DynamoDB Local failed to start"
    exit 1
}

start_sam_local() {
    print_step "Starting SAM local API..."

    # Set environment variables for SAM local
    export DYNAMODB_TABLE=products_catalog
    export AWS_REGION=us-east-1
    export DYNAMODB_ENDPOINT=http://localhost:$DYNAMODB_PORT
    export AWS_ACCESS_KEY_ID=dummy
    export AWS_SECRET_ACCESS_KEY=dummy
    export AWS_SESSION_TOKEN=dummy

    # Start SAM local in background
    sam local start-api \
        --template $TEMPLATE_FILE \
        --port $SAM_PORT \
        --host 0.0.0.0 \
        --warm-containers EAGER &

    SAM_PID=$!

    # Wait for SAM local to be ready
    print_step "Waiting for SAM local to be ready..."
    for i in {1..60}; do
        if curl -s http://localhost:$SAM_PORT/brands > /dev/null 2>&1; then
            print_success "SAM local API is ready on port $SAM_PORT"
            return 0
        fi
        echo -n "."
        sleep 2
    done

    print_error "SAM local API failed to start"
    exit 1
}

run_smoke_test() {
    print_step "Running smoke test..."

    # Test creating a brand
    RESPONSE=$(curl -s -w "%{http_code}" -X POST \
        http://localhost:$SAM_PORT/brands \
        -H "Content-Type: application/json" \
        -d '{"name": "Smoke Test Brand", "description": "Quick test to verify API is working"}')

    HTTP_CODE="${RESPONSE: -3}"
    RESPONSE_BODY="${RESPONSE%???}"

    if [ "$HTTP_CODE" = "201" ]; then
        print_success "Smoke test passed"

        # Extract brand ID and clean up
        BRAND_ID=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['brand_id'])" 2>/dev/null || echo "")
        if [ ! -z "$BRAND_ID" ]; then
            curl -s -X DELETE http://localhost:$SAM_PORT/brands/$BRAND_ID > /dev/null
        fi
    else
        print_error "Smoke test failed (HTTP $HTTP_CODE)"
        echo "Response: $RESPONSE_BODY"
        exit 1
    fi
}

run_e2e_tests() {
    print_step "Running E2E tests..."

    export API_BASE_URL=http://localhost:$SAM_PORT

    # Check if the SAM local E2E test runner exists
    if [ -f "tests/e2e/run_sam_local_e2e_tests.py" ]; then
        print_step "Using SAM local E2E test runner..."
        python3 tests/e2e/run_sam_local_e2e_tests.py $SAM_PORT
    elif [ -f "tests/e2e/run_all_e2e_tests.py" ]; then
        print_step "Using standard E2E test runner with SAM local URL..."
        python3 tests/e2e/run_all_e2e_tests.py
    else
        print_error "No E2E test runner found"
        echo "Expected: tests/e2e/run_sam_local_e2e_tests.py or tests/e2e/run_all_e2e_tests.py"
        exit 1
    fi
}

show_usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -p, --port PORT        SAM local port (default: 3000)"
    echo "  -d, --dynamodb-port    DynamoDB Local port (default: 8000)"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run with default ports"
    echo "  $0 -p 8080           # Run SAM local on port 8080"
    echo "  $0 --port 8080 --dynamodb-port 9000"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            SAM_PORT="$2"
            shift 2
            ;;
        -d|--dynamodb-port)
            DYNAMODB_PORT="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_header

    echo "Configuration:"
    echo "  SAM Local Port: $SAM_PORT"
    echo "  DynamoDB Local Port: $DYNAMODB_PORT"
    echo ""

    check_dependencies
    check_template
    build_sam_app
    start_dynamodb_local
    start_sam_local
    run_smoke_test
    run_e2e_tests

    print_success "All E2E tests completed successfully! 🎉"
}

# Execute main function
main "$@"
