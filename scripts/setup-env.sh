#!/bin/bash

# Environment Setup Script for Product Catalog API
# This script helps manage different Python environments and dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
ENVIRONMENT="dev"
PYTHON_VERSION="3.13"
VENV_NAME="venv"
FORCE_RECREATE=false

# Help function
show_help() {
    cat << EOF
Environment Setup Script for Product Catalog API

Usage: $0 [OPTIONS]

OPTIONS:
    -e, --env ENV           Environment type (dev, test, prod) [default: dev]
    -p, --python VERSION    Python version [default: 3.13]
    -v, --venv NAME         Virtual environment name [default: venv]
    -f, --force             Force recreate virtual environment
    -h, --help              Show this help message

ENVIRONMENTS:
    dev     - Development environment with all dev tools
    test    - Testing environment with testing frameworks
    prod    - Production environment with minimal dependencies

EXAMPLES:
    $0                      # Setup development environment
    $0 -e test              # Setup testing environment
    $0 -e prod -f           # Setup production environment, force recreate
    $0 --env dev --python 3.13 --venv myenv

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--python)
            PYTHON_VERSION="$2"
            shift 2
            ;;
        -v|--venv)
            VENV_NAME="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_RECREATE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|test|prod)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT. Must be one of: dev, test, prod"
    exit 1
fi

print_info "Setting up $ENVIRONMENT environment with Python $PYTHON_VERSION"

# Change to project root
cd "$PROJECT_ROOT"

# Check if Python version is available
if ! command -v "python$PYTHON_VERSION" &> /dev/null; then
    if ! command -v "python3" &> /dev/null; then
        print_error "Python $PYTHON_VERSION not found. Please install Python $PYTHON_VERSION first."
        print_info "You can install Python $PYTHON_VERSION using:"
        print_info "  - macOS: brew install python@$PYTHON_VERSION"
        print_info "  - Ubuntu: sudo apt install python$PYTHON_VERSION python$PYTHON_VERSION-venv"
        exit 1
    else
        print_warning "python$PYTHON_VERSION not found, using python3"
        PYTHON_CMD="python3"
    fi
else
    PYTHON_CMD="python$PYTHON_VERSION"
fi

# Check Python version
ACTUAL_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
print_info "Using Python version: $ACTUAL_VERSION"

# Create or recreate virtual environment
if [[ -d "$VENV_NAME" ]]; then
    if [[ "$FORCE_RECREATE" == true ]]; then
        print_warning "Removing existing virtual environment..."
        rm -rf "$VENV_NAME"
    else
        print_info "Virtual environment '$VENV_NAME' already exists. Use -f to recreate."
    fi
fi

if [[ ! -d "$VENV_NAME" ]]; then
    print_info "Creating virtual environment '$VENV_NAME'..."
    $PYTHON_CMD -m venv "$VENV_NAME"
    print_status "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source "$VENV_NAME/bin/activate"

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip

# Install dependencies based on environment
print_info "Installing $ENVIRONMENT dependencies..."

case $ENVIRONMENT in
    "dev")
        print_info "Installing development dependencies..."
        if [[ -f "requirements-dev.txt" ]]; then
            pip install -r requirements-dev.txt
        else
            print_warning "requirements-dev.txt not found, installing basic requirements"
            pip install -r src/requirements.txt
        fi
        print_status "Development environment ready"
        ;;
    "test")
        print_info "Installing testing dependencies..."
        if [[ -f "requirements-test.txt" ]]; then
            pip install -r requirements-test.txt
        else
            print_warning "requirements-test.txt not found, installing basic requirements"
            pip install -r src/requirements.txt
        fi
        print_status "Testing environment ready"
        ;;
    "prod")
        print_info "Installing production dependencies..."
        if [[ -f "requirements-prod.txt" ]]; then
            pip install -r requirements-prod.txt
        else
            print_warning "requirements-prod.txt not found, installing basic requirements"
            pip install -r src/requirements.txt
        fi
        print_status "Production environment ready"
        ;;
esac

# Install the package in development mode if setup.py exists
if [[ -f "setup.py" ]] && [[ "$ENVIRONMENT" == "dev" ]]; then
    print_info "Installing package in development mode..."
    pip install -e .
fi

# Create .env file for local development if it doesn't exist
if [[ "$ENVIRONMENT" == "dev" ]] && [[ ! -f ".env" ]]; then
    print_info "Creating .env file for local development..."
    cat > .env << EOF
# Local Development Environment Variables
DYNAMODB_TABLE=products_catalog
AWS_REGION=us-east-1
DYNAMODB_ENDPOINT=http://localhost:8000
ENVIRONMENT=dev

# AWS Credentials for local development (use AWS CLI or comment out)
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key

# Optional: Enable debug mode
DEBUG=true

# Optional: Log level
LOG_LEVEL=INFO
EOF
    print_status ".env file created"
fi

# Show installed packages
print_info "Installed packages:"
pip list --format=columns

print_status "Environment setup complete!"

echo ""
echo "🎉 $ENVIRONMENT environment is ready!"
echo ""
echo "To activate the environment manually:"
echo "  source $VENV_NAME/bin/activate"
echo ""

if [[ "$ENVIRONMENT" == "dev" ]]; then
    echo "Development commands:"
    echo "  sam build                    # Build the application"
    echo "  sam local start-api          # Start local API"
    echo "  python src/test_brand_model.py  # Run brand model tests"
    echo "  pytest tests/               # Run all tests (if test directory exists)"
    echo ""
    echo "Local services:"
    echo "  docker-compose -f docker-compose.dev.yml up -d  # Start DynamoDB Local"
    echo "  http://localhost:8001       # DynamoDB Admin UI"
    echo ""
fi

if [[ "$ENVIRONMENT" == "test" ]]; then
    echo "Testing commands:"
    echo "  pytest                      # Run all tests"
    echo "  pytest --cov               # Run tests with coverage"
    echo "  pytest -v                  # Run tests with verbose output"
    echo ""
fi

if [[ "$ENVIRONMENT" == "prod" ]]; then
    echo "Production deployment:"
    echo "  sam build --use-container   # Build for production"
    echo "  sam deploy                  # Deploy to AWS"
    echo ""
fi

echo "To deactivate the environment:"
echo "  deactivate"
