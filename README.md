# Serverless Product Catalog API

A serverless REST API for product catalog management built with AWS services and Infrastructure as Code.

[![AWS](https://img.shields.io/badge/AWS-Cloud-orange)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://www.python.org/)
[![Terraform](https://img.shields.io/badge/Terraform-IaC-purple)](https://www.terraform.io/)
[![SAM](https://img.shields.io/badge/AWS%20SAM-Deployment-yellow)](https://aws.amazon.com/serverless/sam/)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [API Endpoints](#api-endpoints)
- [Getting Started](#getting-started)
- [Documentation](#documentation)
- [Production Enhancements](#production-enhancements)

## Overview

Product catalog API with support for brands, categories, and products.

- **Serverless** - Lambda and API Gateway, automatic scaling
- **Infrastructure as Code** - Terraform modules
- **Single-Table Design** - DynamoDB with Global Secondary Indexes
- **Local Development** - Docker Compose with DynamoDB Local
- **Testing** - Unit, integration, and E2E test suites

## Features

### Core Functionality
- Brand Management - CRUD operations
- Category Management - CRUD operations
- Product Management - Full lifecycle with stock updates
- Relationships - Products linked to brands and categories
- Query by brand or category
- Pagination for large datasets

### Technical
- RESTful API design
- Input validation
- Error handling with proper status codes
- CORS enabled
- CloudWatch logging

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Client    │────▶│  API Gateway     │────▶│  Lambda         │
│  (HTTP)     │     │  (HTTP API v2)   │     │  Functions      │
└─────────────┘     └──────────────────┘     └────────┬────────┘
                                                      |
                                                      ▼
                                              ┌─────────────────┐
                                              │   DynamoDB      │
                                              │  (Single Table) │
                                              └─────────────────┘
```

**Design Decisions:**

- HTTP API Gateway - Lower latency and cost vs REST API
- Lambda per resource - Separate functions for brands, categories, products
- Single table design - DynamoDB best practice with GSIs
- Python 3.13 - Latest Lambda runtime


## Technology Stack

### AWS Services
- API Gateway (HTTP API v2) - API routing
- Lambda - Serverless compute
- DynamoDB - NoSQL database
- CloudWatch - Logging and monitoring
- IAM - Security and permissions

### Tools
- Python 3.13
- AWS SAM CLI - Local development and deployment
- Terraform - Infrastructure as Code
- Docker Compose - Local DynamoDB
- pytest - Testing

## API Endpoints

### Brands
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/brands` | List all brands |
| POST | `/brands` | Create a new brand |
| GET | `/brands/{id}` | Get brand by ID |
| PUT | `/brands/{id}` | Update brand |
| DELETE | `/brands/{id}` | Delete brand |

### Categories
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/categories` | List all categories |
| POST | `/categories` | Create a new category |
| GET | `/categories/{id}` | Get category by ID |
| PUT | `/categories/{id}` | Update category |
| DELETE | `/categories/{id}` | Delete category |

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products` | List all products |
| POST | `/products` | Create a new product |
| GET | `/products/{id}` | Get product by ID |
| PUT | `/products/{id}` | Update product |
| DELETE | `/products/{id}` | Delete product |
| PATCH | `/products/{id}/stock` | Update stock quantity |
| GET | `/products/by-brand/{brand_id}` | List products by brand |
| GET | `/products/by-category/{category_id}` | List products by category |

See [SERVERLESS_API_TESTING.md](SERVERLESS_API_TESTING.md) for detailed API testing guide with examples.

## Getting Started

### Prerequisites

- Python 3.13+
- AWS CLI configured
- AWS SAM CLI
- Docker Desktop or OrbStack
- Terraform (for infrastructure deployment)

### Quick Start

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

4. **Build and run the API locally**
   ```bash
   sam build
   sam local start-api --docker-network host
   ```

5. **Test the API**
   ```bash
   curl http://localhost:3000/brands
   ```

### Deployment

#### Terraform
```bash
cd terraform/environments/dev
terraform init
terraform plan
terraform apply -parallelism=1 -var-file=dev.tfvars
```

See [SETUP.md](SETUP.md) for detailed setup instructions.

## Documentation

- [SETUP.md](SETUP.md) - Setup and development guide
- [SERVERLESS_API_TESTING.md](SERVERLESS_API_TESTING.md) - API testing with examples
- [terraform/environments/dev/DEPLOYMENT_NOTES.md](terraform/environments/dev/DEPLOYMENT_NOTES.md) - Terraform deployment notes
- [tests/e2e/README.md](tests/e2e/README.md) - E2E testing

## Project Structure

```
serverless-product-catalog-api/
├── src/                          # Application source code
│   ├── handlers/                 # Lambda function handlers
│   ├── models/                   # Data models
│   ├── services/                 # Business logic
│   └── utils/                    # Utilities
├── terraform/                    # Infrastructure as Code
│   ├── modules/                  # Reusable Terraform modules
│   │   ├── api_gateway/
│   │   ├── lambda/
│   │   ├── dynamodb/
│   │   └── iam/
│   └── environments/             # Environment-specific configs
├── tests/                        # Test suites
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── e2e/                      # End-to-end tests
├── scripts/                      # Utility scripts
├── template.yaml                 # SAM template
└── docker-compose.dev.yml       # Local development services
```

## Testing

### Run Unit Tests
```bash
pytest tests/unit/ -v
```

### Run Integration Tests
```bash
pytest tests/integration/ -v
```

### Run E2E Tests
```bash
export API_BASE_URL=https://your-api-id.execute-api.region.amazonaws.com/dev
python tests/e2e/run_all_e2e_tests.py
```

## Security

- No hardcoded credentials
- IAM roles with least privilege
- Input validation on all endpoints
- HTTPS-only
- CloudWatch audit logging

## Production Enhancements

This project demonstrates core serverless architecture patterns, Infrastructure as Code, and testing best practices but here's what I'd add for production ready deployments:

**Observability & Reliability**
- Activate X-Ray tracing (already configured in Terraform with IAM permissions)
- CloudWatch alarms for error rates and latency spikes
- Dead Letter Queues for failed Lambda invocations
- Circuit breakers and retry logic with exponential backoff

**Security**
- Authentication via Cognito or API Gateway authorizers
- AWS WAF rules for common attack patterns
- Secrets Manager for sensitive config (currently using environment variables)

**Deployment Strategy**
- CI/CD pipeline with automated tests (unit/integration/e2e tests are ready)
- Blue-green or canary deployments for zero-downtime releases
- Multi-environment promotion flow (dev → staging → prod)

**Performance at Scale**
- DynamoDB DAX caching layer for hot data
- Lambda provisioned concurrency to eliminate cold starts
- API Gateway response caching for read-heavy endpoints

**Data Durability**
- Point-in-time recovery for DynamoDB (easy toggle)
- Automated backups and retention policies
- Cross-region replication if needed for DR

The focus here was building a solid foundation with proper testing, modular Terraform code, and local development workflow. The architecture is modular and scales well — the items above are incremental improvements you'd layer on based on actual usage patterns and requirements

## License

Educational and portfolio use.

---

AWS services incur costs. Clean up resources after testing.
