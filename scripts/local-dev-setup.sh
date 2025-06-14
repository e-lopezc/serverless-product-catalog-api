#!/bin/bash

# Development setup script for Product Catalog API

set -e

echo "🚀 Setting up Product Catalog API development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if required tools are installed
echo "Checking required tools..."

if ! command -v sam &> /dev/null; then
    print_error "AWS SAM CLI is not installed. Please install it first:"
    echo "  brew install aws-sam-cli"
    exit 1
fi
print_status "AWS SAM CLI found"

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker Desktop or OrbStack first."
    exit 1
fi
print_status "Docker found"

if ! command -v aws &> /dev/null; then
    print_warning "AWS CLI not found. You may want to install it:"
    echo "  brew install awscli"
else
    print_status "AWS CLI found"
fi

# Start DynamoDB Local
echo ""
echo "Starting local services..."

if [ "$(docker ps -q -f name=dynamodb-local)" ]; then
    print_status "DynamoDB Local is already running"
else
    echo "Starting DynamoDB Local..."
    docker-compose -f docker-compose.dev.yml up -d
    print_status "DynamoDB Local started on http://localhost:8000"
    print_status "DynamoDB Admin UI available at http://localhost:8001"
fi

# Wait for DynamoDB to be ready
echo "Waiting for DynamoDB Local to be ready..."
timeout=30
while ! nc -z localhost 8000 && [ $timeout -gt 0 ]; do
    sleep 1
    timeout=$((timeout - 1))
done

if [ $timeout -eq 0 ]; then
    print_error "DynamoDB Local failed to start"
    exit 1
fi

print_status "DynamoDB Local is ready"

# Create the table locally
echo ""
echo "Setting up local DynamoDB table..."

# Check if table exists
if aws dynamodb describe-table --table-name products_catalog --endpoint-url http://localhost:8000 &> /dev/null; then
    print_status "Table 'products_catalog' already exists"
else
    echo "Creating table 'products_catalog'..."
    aws dynamodb create-table \
        --table-name products_catalog \
        --attribute-definitions \
            AttributeName=PK,AttributeType=S \
            AttributeName=SK,AttributeType=S \
            AttributeName=brand_id,AttributeType=S \
            AttributeName=product_id,AttributeType=S \
            AttributeName=GSI3PK,AttributeType=S \
            AttributeName=GSI3SK,AttributeType=S \
        --key-schema \
            AttributeName=PK,KeyType=HASH \
            AttributeName=SK,KeyType=RANGE \
        --global-secondary-indexes \
            'IndexName=GSI-1,KeySchema=[{AttributeName=SK,KeyType=HASH},{AttributeName=PK,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}' \
            'IndexName=GSI-2,KeySchema=[{AttributeName=brand_id,KeyType=HASH},{AttributeName=product_id,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}' \
            'IndexName=GSI-3,KeySchema=[{AttributeName=GSI3PK,KeyType=HASH},{AttributeName=GSI3SK,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}' \
        --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
        --endpoint-url http://localhost:8000
    
    print_status "Table 'products_catalog' created successfully"
fi

# Set environment variables for local development
echo ""
echo "Setting up environment variables..."
export DYNAMODB_TABLE=products_catalog
export AWS_REGION=us-east-1
export DYNAMODB_ENDPOINT=http://localhost:8000

print_status "Environment variables set"

echo ""
echo "🎉 Development environment is ready!"
echo ""
echo "Next steps:"
echo "1. Build your SAM application:"
echo "   sam build"
echo ""
echo "2. Start the local API:"
echo "   sam local start-api --docker-network host"
echo ""
echo "3. Your API will be available at:"
echo "   http://localhost:3000"
echo ""
echo "4. DynamoDB Admin UI:"
echo "   http://localhost:8001"
echo ""
echo "5. To stop services:"
echo "   docker-compose -f docker-compose.dev.yml down"
