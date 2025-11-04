#!/usr/bin/env python3
"""
Environment Verification Script for Product Catalog API
This script verifies that the development environment is properly set up
"""

import sys
import os
import subprocess
import json
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text: str) -> None:
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(text: str) -> None:
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str) -> None:
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text: str) -> None:
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text: str) -> None:
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def run_command(cmd: List[str], capture_output: bool = True, timeout: int = 30) -> Tuple[bool, str]:
    """Run a command and return success status and output"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            check=False
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout} seconds"
    except FileNotFoundError:
        return False, f"Command not found: {cmd[0]}"
    except Exception as e:
        return False, str(e)

def check_python_version() -> bool:
    """Check if Python version is compatible"""
    print_header("PYTHON VERSION CHECK")

    version = sys.version_info
    print_info(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major == 3 and version.minor >= 11:
        print_success(f"Python {version.major}.{version.minor} is compatible")
        if version.minor >= 13:
            print_success("Python 3.13+ detected - optimal version!")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor} is not compatible")
        print_error("Required: Python 3.11+ (Recommended: Python 3.13+)")
        return False

def check_required_tools() -> Dict[str, bool]:
    """Check for required development tools"""
    print_header("REQUIRED TOOLS CHECK")

    tools = {
        'aws': ['aws', '--version'],
        'sam': ['sam', '--version'],
        'docker': ['docker', '--version'],
        'pip': ['pip', '--version'],
        'git': ['git', '--version']
    }

    results = {}

    for tool, cmd in tools.items():
        success, output = run_command(cmd)
        if success:
            version_line = output.strip().split('\n')[0]
            print_success(f"{tool}: {version_line}")
            results[tool] = True
        else:
            print_error(f"{tool}: Not found or not working")
            results[tool] = False

    return results

def check_project_structure() -> bool:
    """Check if project structure is correct"""
    print_header("PROJECT STRUCTURE CHECK")

    required_files = [
        'template.yaml',
        'samconfig.toml',
        'src/requirements.txt',
        'src/config/settings.py',
        'src/handlers/brands.py',
        'src/models/brand.py',
        'src/services/brand_service.py',
        'src/utils/db_operations.py',
        'src/utils/exceptions.py',
        'src/utils/response.py',
        'docker-compose.dev.yml',
        'scripts/local-dev-setup.sh',
        'scripts/setup-env.sh'
    ]

    required_dirs = [
        'src',
        'src/config',
        'src/handlers',
        'src/models',
        'src/services',
        'src/utils',
        'scripts'
    ]

    all_good = True

    # Check directories
    print_info("Checking directories...")
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print_success(f"Directory: {dir_path}")
        else:
            print_error(f"Missing directory: {dir_path}")
            all_good = False

    # Check files
    print_info("Checking files...")
    for file_path in required_files:
        if os.path.isfile(file_path):
            print_success(f"File: {file_path}")
        else:
            print_error(f"Missing file: {file_path}")
            all_good = False

    return all_good

def check_python_dependencies() -> bool:
    """Check if Python dependencies are installed"""
    print_header("PYTHON DEPENDENCIES CHECK")

    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

    if in_venv:
        print_success("Virtual environment detected")
        print_info(f"Python executable: {sys.executable}")
    else:
        print_warning("Not in a virtual environment")
        print_warning("It's recommended to use a virtual environment")

    # Check core dependencies
    core_deps = [
        ('boto3', 'AWS SDK'),
        ('botocore', 'AWS Core Library'),
        ('validators', 'URL Validation'),
        ('typing_extensions', 'Type Hints')
    ]

    all_deps_ok = True

    for dep, description in core_deps:
        try:
            spec = importlib.util.find_spec(dep)
            if spec is not None:
                # Try to import to check if it's actually usable
                module = importlib.import_module(dep)
                version = getattr(module, '__version__', 'unknown')
                print_success(f"{dep} ({description}): v{version}")
            else:
                print_error(f"{dep} ({description}): Not found")
                all_deps_ok = False
        except ImportError as e:
            print_error(f"{dep} ({description}): Import error - {e}")
            all_deps_ok = False
        except Exception as e:
            print_warning(f"{dep} ({description}): Warning - {e}")

    return all_deps_ok

def check_aws_config() -> bool:
    """Check AWS configuration"""
    print_header("AWS CONFIGURATION CHECK")

    # Check AWS CLI configuration
    success, output = run_command(['aws', 'configure', 'list'])
    if success:
        print_success("AWS CLI is configured")
        print_info("Configuration details:")
        for line in output.strip().split('\n'):
            if line.strip():
                print(f"  {line}")
    else:
        print_error("AWS CLI is not configured")
        print_info("Run 'aws configure' to set up your credentials")
        return False

    # Check if we can access AWS (optional)
    print_info("Testing AWS connectivity...")
    success, output = run_command(['aws', 'sts', 'get-caller-identity'], timeout=10)
    if success:
        try:
            identity = json.loads(output)
            print_success(f"AWS Identity verified: {identity.get('Arn', 'Unknown')}")
        except json.JSONDecodeError:
            print_warning("AWS connectivity test successful but response format unexpected")
    else:
        print_warning("Could not verify AWS connectivity (this is okay for local development)")
        print_info("Make sure your AWS credentials are correct for deployment")

    return True

def check_docker_services() -> bool:
    """Check if Docker services are running"""
    print_header("DOCKER SERVICES CHECK")

    # Check if Docker is running
    success, output = run_command(['docker', 'info'])
    if not success:
        print_error("Docker is not running")
        print_info("Start Docker Desktop or your Docker service")
        return False

    print_success("Docker is running")

    # Check for DynamoDB Local container
    success, output = run_command(['docker', 'ps', '--filter', 'name=dynamodb-local', '--format', 'table {{.Names}}\t{{.Status}}'])
    if success and 'dynamodb-local' in output:
        print_success("DynamoDB Local container is running")

        # Test DynamoDB Local connectivity with proper DynamoDB API call
        print_info("Testing DynamoDB Local connectivity...")
        success, output = run_command([
            'aws', 'dynamodb', 'list-tables',
            '--endpoint-url', 'http://localhost:8000',
            '--region', 'us-east-1'
        ], timeout=10)

        if success:
            print_success("DynamoDB Local is accessible and responding")
            # Check if our table exists
            if 'products_catalog' in output:
                print_success("Products catalog table found")
            else:
                print_warning("Products catalog table not found")
                print_info("Run: ./scripts/local-dev-setup.sh to create the table")
        else:
            print_warning("DynamoDB Local container running but not responding to API calls")
            print_info("Try restarting: docker-compose -f docker-compose.dev.yml restart")
    else:
        print_warning("DynamoDB Local container is not running")
        print_info("Start with: docker-compose -f docker-compose.dev.yml up -d")

    return True

def check_sam_functionality() -> bool:
    """Check SAM functionality"""
    print_header("SAM FUNCTIONALITY CHECK")

    # Check if template.yaml is valid
    if not os.path.isfile('template.yaml'):
        print_error("template.yaml not found")
        return False

    success, output = run_command(['sam', 'validate'])
    if success:
        print_success("SAM template is valid")
    else:
        print_error("SAM template validation failed")
        print_error(output)
        return False

    # Check if we can build (dry run)
    print_info("Testing SAM build...")
    success, output = run_command(['sam', 'build', '--help'])
    if success:
        print_success("SAM build command is available")
    else:
        print_error("SAM build command failed")
        return False

    return True

def check_environment_variables() -> bool:
    """Check environment variables"""
    print_header("ENVIRONMENT VARIABLES CHECK")

    env_vars = {
        'DYNAMODB_TABLE': 'DynamoDB table name',
        'AWS_REGION': 'AWS region',
        'DYNAMODB_ENDPOINT': 'DynamoDB endpoint (for local dev)'
    }

    all_set = True

    for var, description in env_vars.items():
        value = os.getenv(var)
        if value:
            if var == 'DYNAMODB_ENDPOINT' and 'localhost' in value:
                print_success(f"{var}: {value} (local development)")
            else:
                print_success(f"{var}: {value}")
        else:
            print_warning(f"{var}: Not set ({description})")
            if var != 'DYNAMODB_ENDPOINT':  # DYNAMODB_ENDPOINT is optional
                all_set = False

    if not all_set:
        print_info("Set environment variables or create a .env file")
        print_info("Run './scripts/setup-env.sh' to create default .env file")

    return True  # Environment variables are not critical for verification

def test_imports() -> bool:
    """Test if our custom modules can be imported"""
    print_header("MODULE IMPORT TEST")

    # Add src to Python path
    src_path = os.path.join(os.getcwd(), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    modules = [
        ('config.settings', 'Configuration settings'),
        ('utils.exceptions', 'Custom exceptions'),
        ('utils.response', 'Response utilities'),
        ('models.brand', 'Brand model'),
        ('services.brand_service', 'Brand service'),
        ('handlers.brands', 'Brand handler')
    ]

    all_imports_ok = True

    for module_name, description in modules:
        try:
            importlib.import_module(module_name)
            print_success(f"{module_name}: {description}")
        except ImportError as e:
            print_error(f"{module_name}: Import failed - {e}")
            all_imports_ok = False
        except Exception as e:
            print_warning(f"{module_name}: Warning - {e}")

    return all_imports_ok

def run_basic_functionality_test() -> bool:
    """Run a basic functionality test"""
    print_header("BASIC FUNCTIONALITY TEST")

    try:
        # Add src to Python path
        src_path = os.path.join(os.getcwd(), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        # Test basic model functionality
        from models.brand import Brand
        from utils.exceptions import ValidationError

        print_info("Testing brand validation...")

        # This should not raise an exception
        try:
            Brand._validate_name("Test Brand")
            Brand._validate_description("This is a test description for validation")
            Brand._validate_website("https://example.com")
            print_success("Brand validation methods working correctly")
        except ValidationError as e:
            print_error(f"Brand validation failed: {e}")
            return False

        # This should raise an exception
        try:
            Brand._validate_name("")  # Empty name should fail
            print_error("Brand validation is not working - empty name should fail")
            return False
        except ValidationError:
            print_success("Brand validation correctly rejects invalid input")

        print_success("Basic functionality test passed")
        return True

    except Exception as e:
        print_error(f"Basic functionality test failed: {e}")
        return False

def generate_summary(results: Dict[str, bool]) -> None:
    """Generate a summary of all checks"""
    print_header("VERIFICATION SUMMARY")

    passed_checks = sum(1 for result in results.values() if result)
    total_checks = len(results)

    print(f"\n{Colors.BOLD}Overall Status: {passed_checks}/{total_checks} checks passed{Colors.END}\n")

    # Group results
    critical_checks = ['python_version', 'project_structure', 'python_dependencies', 'module_imports']
    recommended_checks = ['required_tools', 'aws_config', 'docker_services', 'sam_functionality']
    optional_checks = ['environment_variables', 'basic_functionality']

    def print_group(title: str, checks: List[str]) -> None:
        print(f"{Colors.BOLD}{title}:{Colors.END}")
        for check in checks:
            if check in results:
                status = "✓" if results[check] else "✗"
                color = Colors.GREEN if results[check] else Colors.RED
                print(f"  {color}{status} {check.replace('_', ' ').title()}{Colors.END}")
        print()

    print_group("Critical Checks", critical_checks)
    print_group("Recommended Checks", recommended_checks)
    print_group("Optional Checks", optional_checks)

    # Provide recommendations
    if not all(results.get(check, False) for check in critical_checks):
        print_error("❌ Critical issues found! Please fix these before proceeding:")
        for check in critical_checks:
            if not results.get(check, False):
                print(f"   - Fix {check.replace('_', ' ')}")
        print()

    if not all(results.get(check, False) for check in recommended_checks):
        print_warning("⚠️  Some recommended tools are missing:")
        for check in recommended_checks:
            if not results.get(check, False):
                print(f"   - Set up {check.replace('_', ' ')}")
        print()

    if passed_checks == total_checks:
        print_success("🎉 All checks passed! Your environment is ready for development.")
    elif passed_checks >= len(critical_checks + recommended_checks):
        print_success("✅ Environment is ready for basic development.")
        print_info("Consider addressing optional items for the best experience.")
    else:
        print_warning("⚠️  Environment needs attention before development.")
        print_info("Please address the issues above and run this script again.")

def main():
    """Main verification function"""
    print(f"{Colors.BOLD}{Colors.PURPLE}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                 PRODUCT CATALOG API                        ║")
    print("║              Environment Verification                      ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")

    # Change to script directory to ensure proper paths
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)

    print_info(f"Working directory: {os.getcwd()}")
    print_info(f"Python executable: {sys.executable}")

    # Run all checks
    results = {}

    results['python_version'] = check_python_version()
    results.update(check_required_tools())
    results['project_structure'] = check_project_structure()
    results['python_dependencies'] = check_python_dependencies()
    results['aws_config'] = check_aws_config()
    results['docker_services'] = check_docker_services()
    results['sam_functionality'] = check_sam_functionality()
    results['environment_variables'] = check_environment_variables()
    results['module_imports'] = test_imports()
    results['basic_functionality'] = run_basic_functionality_test()

    # Generate summary
    generate_summary(results)

    # Exit with appropriate code
    critical_passed = all(results.get(check, False) for check in ['python_version', 'project_structure', 'python_dependencies', 'module_imports'])

    if critical_passed:
        print_info("Run './scripts/setup-env.sh' if you need to set up the environment")
        print_info("Run 'sam build && sam local start-api' to start the API")
        sys.exit(0)
    else:
        print_error("Critical issues found. Please fix them before proceeding.")
        sys.exit(1)

if __name__ == '__main__':
    main()
