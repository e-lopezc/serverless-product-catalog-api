# Product Catalog API - Setup Guide

This guide covers the setup and development environment configuration for the serverless Product Catalog API.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Requirements Files Structure](#requirements-files-structure)
- [Environment Setup](#environment-setup)
- [Local Development](#local-development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Python 3.13+** - The application uses Python 3.13 features
- **AWS CLI** - For AWS resource management
- **AWS SAM CLI** - For local development and deployment
- **Docker Desktop** or **OrbStack** - For local DynamoDB
- **Git** - Version control

### Installation Commands

```bash
# macOS (using Homebrew)
brew install python@3.13
brew install awscli
brew install aws-sam-cli
brew install --cask docker

# Ubuntu/Debian
sudo apt update
sudo apt install python3.13 python3.13-venv python3.13-dev
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# Install SAM CLI
pip install aws-sam-cli
```

### AWS Configuration

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, Region, and Output format
```

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd serverless-product-catalog-api
   ```

2. **Set up development environment**
   ```bash
   ./scripts/setup-env.sh
   ```

3. **Start local services**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ./scripts/local-dev-setup.sh
   ```

4. **Build and run the API**
   ```bash
   sam build
   sam local start-api --docker-network host
   ```

## Requirements Files Structure

Our project uses multiple requirements files for different environments:

### File Organization

```
serverless-product-catalog-api/
├── src/requirements.txt          # Production dependencies (used by Lambda)
├── requirements-dev.txt          # Development dependencies
├── requirements-test.txt         # Testing dependencies
├── requirements-prod.txt         # Production-only (minimal)
└── scripts/setup-env.sh         # Environment setup script
```

### Requirements Files Explained

#### `src/requirements.txt` (Lambda Runtime)
- **Location**: `src/requirements.txt`
- **Purpose**: Production dependencies for Lambda functions
- **Used by**: AWS SAM build process (`CodeUri: src/`)
- **Contains**: Minimal dependencies for production runtime
- **Python Version**: 3.13 compatible

```txt
boto3>=1.35.0
botocore>=1.35.0
typing-extensions>=4.8.0
validators>=0.25.0
certifi>=2023.11.17
```

#### `requirements-dev.txt` (Development)
- **Purpose**: All development tools and utilities
- **Includes**: Linting, formatting, documentation, debugging tools
- **Usage**: `pip install -r requirements-dev.txt`

#### `requirements-test.txt` (Testing)
- **Purpose**: Testing frameworks and utilities
- **Includes**: pytest, moto (AWS mocking), coverage tools
- **Usage**: `pip install -r requirements-test.txt`

#### `requirements-prod.txt` (Production Minimal)
- **Purpose**: Pinned versions for production deployment
- **Contains**: Exact versions for reproducible builds
- **Usage**: Production CI/CD pipelines

### Why This Structure?

1. **Lambda Size Optimization**: Only essential dependencies in `src/requirements.txt`
2. **Development Flexibility**: Full toolchain in `requirements-dev.txt`
3. **Testing Isolation**: Test-specific tools in `requirements-test.txt`
4. **Production Stability**: Pinned versions in `requirements-prod.txt`
5. **SAM Compatibility**: SAM automatically uses `src/requirements.txt`

## Environment Setup

### Automated Setup (Recommended)

Use our setup script for different environments:

```bash
# Development environment (default)
./scripts/setup-env.sh

# Testing environment
./scripts/setup-env.sh --env test

# Production environment
./scripts/setup-env.sh --env prod

# Custom configuration
./scripts/setup-env.sh --env dev --python 3.13 --venv myenv --force
```

### Manual Setup

1. **Create virtual environment**
   ```bash
   python3.13 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   # For development
   pip install -r requirements-dev.txt

   # For testing only
   pip install -r requirements-test.txt

   # For production
   pip install -r requirements-prod.txt
   ```

3. **Set environment variables**
   ```bash
   export DYNAMODB_TABLE=products_catalog
   export AWS_REGION=us-east-1
   export DYNAMODB_ENDPOINT=http://localhost:8000
   ```

### Environment Variables

Create a `.env` file for local development:

```env
# Local Development Environment Variables
DYNAMODB_TABLE=products_catalog
AWS_REGION=us-east-1
DYNAMODB_ENDPOINT=http://localhost:8000
ENVIRONMENT=dev

# Optional: AWS Credentials (use AWS CLI instead)
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key

# Optional: Debug settings
DEBUG=true
LOG_LEVEL=INFO
```

## Local Development

### 1. Start Local Services

```bash
# Start DynamoDB Local and Admin UI
docker-compose -f docker-compose.dev.yml up -d

# Verify services are running
curl http://localhost:8000  # DynamoDB Local
open http://localhost:8001  # DynamoDB Admin UI
```

### 2. Initialize Database

```bash
# Run the setup script to create tables
./scripts/local-dev-setup.sh
```

### 3. Build and Run API

```bash
# Build the SAM application
sam build

# Start local API server
sam local start-api --docker-network host

# API will be available at http://localhost:3000
```

### 4. Test the API

```bash
# Test brand creation
curl -X POST http://localhost:3000/brands \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Brand","description":"A test brand","website":"https://test.com"}'

# List all brands
curl http://localhost:3000/brands

# Get specific brand
curl http://localhost:3000/brands/{brand-id}
```

### Development Workflow

1. **Code Changes**: Edit files in `src/`
2. **Rebuild**: `sam build` (only if dependencies change)
3. **Test Locally**: API automatically reloads code changes
4. **Run Tests**: `python src/test_brand_model.py`
5. **Debug**: Use VS Code debugger with provided configuration

## Testing

### Unit Tests

```bash
# Run the brand model test
python src/test_brand_model.py

# Run with pytest (if test directory exists)
pytest tests/ -v
```

### Integration Tests

```bash
# Start local services first
docker-compose -f docker-compose.dev.yml up -d
./scripts/local-dev-setup.sh

# Run integration tests
sam local start-api --docker-network host &
# Run your API tests here
```

### Test with Coverage

```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html  # View coverage report
```

## Deployment

### Development Deployment

```bash
sam build
sam deploy --guided  # First time deployment
sam deploy           # Subsequent deployments
```

### Production Deployment

```bash
# Use production requirements
cp requirements-prod.txt src/requirements.txt

# Build for production
sam build --use-container

# Deploy to production
sam deploy --config-env prod
```

### Infrastructure (Terraform)

```bash
cd environments/dev
terraform init
terraform plan
terraform apply
```

## Troubleshooting

### Common Issues

#### Python Version Issues

```bash
# Check Python version
python3.13 --version

# If python3.13 not found
brew install python@3.13  # macOS
sudo apt install python3.13  # Ubuntu
```

#### DynamoDB Local Issues

```bash
# Restart DynamoDB Local
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d

# Check if table exists
aws dynamodb list-tables --endpoint-url http://localhost:8000
```

#### SAM Build Issues

```bash
# Clean build
sam build --use-container

# Check SAM version
sam --version

# Update SAM CLI
pip install --upgrade aws-sam-cli
```

#### Import/Module Issues

```bash
# Ensure you're in the right directory
cd serverless-product-catalog-api

# Activate virtual environment
source venv/bin/activate

# Check Python path
python -c "import sys; print(sys.path)"
```

### Dependency Issues

#### Requirements File Not Found

```bash
# Ensure you're using the right requirements file
ls -la *requirements*.txt

# Create missing requirements file
./scripts/setup-env.sh --env dev
```

#### Version Conflicts

```bash
# Clean install
rm -rf venv
./scripts/setup-env.sh --force

# Check installed packages
pip list
pip check  # Check for conflicts
```

### AWS Issues

#### Credentials

```bash
# Check AWS configuration
aws configure list
aws sts get-caller-identity

# Reconfigure if needed
aws configure
```

#### Permissions

Ensure your AWS user has the following permissions:
- DynamoDB: Create, Read, Update, Delete tables and items
- Lambda: Create, Update, Invoke functions
- API Gateway: Create, Update, Deploy APIs
- IAM: Create, Update roles (for SAM deployment)

### Performance Issues

#### Lambda Cold Starts

- Keep `src/requirements.txt` minimal
- Use production requirements for deployment
- Consider Lambda provisioned concurrency for high-traffic APIs

#### DynamoDB Performance

- Use appropriate partition keys
- Monitor read/write capacity
- Use DAX for caching if needed

## Best Practices

### Requirements Management

1. **Keep Lambda dependencies minimal** - Use only essential packages in `src/requirements.txt`
2. **Pin versions for production** - Use exact versions in `requirements-prod.txt`
3. **Separate concerns** - Different requirements files for different purposes
4. **Regular updates** - Keep dependencies updated for security
5. **Test compatibility** - Always test with Python 3.13

### Development Practices

1. **Use virtual environments** - Isolate project dependencies
2. **Environment variables** - Never hardcode configuration
3. **Local testing** - Test with DynamoDB Local before deployment
4. **Code quality** - Use linting and formatting tools
5. **Documentation** - Keep this guide updated

### Security

1. **Never commit credentials** - Use AWS CLI profiles or IAM roles
2. **Use HTTPS** - All API endpoints should use HTTPS
3. **Validate inputs** - Implement proper validation (already done in brand model)
4. **Monitor dependencies** - Use tools like `safety` to check for vulnerabilities

## Additional Resources

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [Python 3.13 Documentation](https://docs.python.org/3.13/)
- [AWS Lambda Python Runtime](https://docs.aws.amazon.com/lambda/latest/dg/python-programming-model.html)
