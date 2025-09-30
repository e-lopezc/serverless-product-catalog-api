#!/bin/bash

# Build Lambda deployment packages for Terraform
# Creates separate ZIP files for brands, categories, and products functions
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$PROJECT_ROOT/src"
BUILD_DIR="$PROJECT_ROOT/build"
DEPLOYMENT_DIR="$PROJECT_ROOT/deployment"

# Lambda function configurations matching Terraform
# Fixed: Use proper associative array declaration
declare -A LAMBDA_FUNCTIONS
LAMBDA_FUNCTIONS["brands"]="handlers.brands"
LAMBDA_FUNCTIONS["categories"]="handlers.categories"
LAMBDA_FUNCTIONS["products"]="handlers.products"

echo -e "${BLUE}🚀 Building Lambda deployment packages...${NC}"

# Validate source directory exists
if [ ! -d "$SRC_DIR" ]; then
    echo -e "${RED}❌ Source directory not found: $SRC_DIR${NC}"
    exit 1
fi

# Clean and create build directories
echo -e "${YELLOW}🧹 Cleaning build directories...${NC}"
rm -rf "$BUILD_DIR" "$DEPLOYMENT_DIR"
mkdir -p "$BUILD_DIR" "$DEPLOYMENT_DIR"

# Install dependencies once (shared across all functions)
DEPS_DIR="$BUILD_DIR/dependencies"
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
mkdir -p "$DEPS_DIR"

if [ -f "$SRC_DIR/requirements.txt" ]; then
    pip install -r "$SRC_DIR/requirements.txt" -t "$DEPS_DIR" --quiet
    echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
else
    echo -e "${RED}❌ requirements.txt not found in $SRC_DIR${NC}"
    exit 1
fi

# Function to get file size in bytes (macOS compatible)
get_file_size_bytes() {
    local file="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        stat -f%z "$file"
    else
        # Linux
        stat -c%s "$file"
    fi
}

# Function to convert bytes to human readable format
bytes_to_human() {
    local bytes=$1
    if [ $bytes -ge 1073741824 ]; then
        echo "$(($bytes / 1073741824))GB"
    elif [ $bytes -ge 1048576 ]; then
        echo "$(($bytes / 1048576))MB"
    elif [ $bytes -ge 1024 ]; then
        echo "$(($bytes / 1024))KB"
    else
        echo "${bytes}B"
    fi
}

# Function to create a Lambda package
create_lambda_package() {
    local function_name=$1
    local handler_path=$2

    echo -e "${BLUE}🔨 Building package for: ${function_name}${NC}"

    # Create function-specific build directory
    local func_build_dir="$BUILD_DIR/$function_name"
    mkdir -p "$func_build_dir"

    # Copy dependencies
    echo "  📋 Copying dependencies..."
    cp -r "$DEPS_DIR"/* "$func_build_dir/" 2>/dev/null || true

    # Copy all source code (shared codebase)
    echo "  📂 Copying source code..."

    # Copy all Python modules
    cp -r "$SRC_DIR/config" "$func_build_dir/"
    cp -r "$SRC_DIR/handlers" "$func_build_dir/"
    cp -r "$SRC_DIR/models" "$func_build_dir/"
    cp -r "$SRC_DIR/services" "$func_build_dir/"
    cp -r "$SRC_DIR/utils" "$func_build_dir/"

    # No wrapper needed - handlers are already in correct structure
    # handlers.brands.lambda_handler
    # handlers.categories.lambda_handler
    # handlers.products.lambda_handler

    # Clean up Python cache files
    echo "  🧼 Cleaning Python cache files..."
    find "$func_build_dir" -type f -name "*.pyc" -delete
    find "$func_build_dir" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$func_build_dir" -type f -name "*.pyo" -delete
    find "$func_build_dir" -type f -name ".DS_Store" -delete

    # Create ZIP package
    echo "  📦 Creating ZIP package..."
    local zip_file="$DEPLOYMENT_DIR/${function_name}.zip"

    cd "$func_build_dir"
    zip -r "$zip_file" . -x "*.git*" "*.pyc" "*/__pycache__/*" "*.DS_Store" -q
    cd - > /dev/null

    # Get package size (macOS compatible)
    local size=$(du -h "$zip_file" | cut -f1 | tr -d ' ')
    echo -e "${GREEN}  ✅ Package created: ${function_name}.zip (${size})${NC}"
}

# Build packages for each Lambda function
for function_name in "${!LAMBDA_FUNCTIONS[@]}"; do
    handler_path="${LAMBDA_FUNCTIONS[$function_name]}"
    create_lambda_package "$function_name" "$handler_path"
done

# Create summary
echo -e "\n${GREEN}🎉 Lambda packages built successfully!${NC}"
echo -e "${BLUE}📦 Deployment packages:${NC}"

total_size=0
for function_name in "${!LAMBDA_FUNCTIONS[@]}"; do
    zip_file="$DEPLOYMENT_DIR/${function_name}.zip"
    if [ -f "$zip_file" ]; then
        size=$(du -h "$zip_file" | cut -f1 | tr -d ' ')
        size_bytes=$(get_file_size_bytes "$zip_file")
        total_size=$((total_size + size_bytes))
        echo "  📄 ${function_name}.zip - ${size}"
    fi
done

# Convert total size to human readable (without bc dependency)
total_size_human=$(bytes_to_human $total_size)
echo -e "${BLUE}📊 Total size: ${total_size_human}${NC}"

# Clean up build directory (keep deployment directory)
echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
rm -rf "$BUILD_DIR"

echo -e "\n${GREEN}✨ Ready to deploy with Terraform!${NC}"
echo -e "${BLUE}💡 Next steps:${NC}"
echo "  1. cd terraform/environments/dev"
echo "  2. terraform plan"
echo "  3. terraform apply"

# Update Terraform variables file with package paths
echo -e "\n${YELLOW}📝 Terraform package paths:${NC}"
for function_name in "${!LAMBDA_FUNCTIONS[@]}"; do
    echo "  ${function_name}: ../../../deployment/${function_name}.zip"
done
