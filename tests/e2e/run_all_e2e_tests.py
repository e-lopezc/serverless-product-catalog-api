#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Runner
Run all E2E tests for the serverless product catalog API
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path
from typing import List, Dict, Any


class E2ETestRunner:
    """Comprehensive E2E test runner for the entire API"""

    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url.rstrip('/')
        self.test_results: List[Dict[str, Any]] = []

        # Test files in order of dependency
        self.test_files = [
            'test_brands_e2e.py',
            'test_categories_e2e.py',
            'test_products_e2e.py'
        ]

    def check_api_health(self) -> bool:
        """Check if the API is accessible"""
        print("🔍 Checking API health...")

        endpoints_to_check = [
            f"{self.api_base_url}/brands",
            f"{self.api_base_url}/categories",
            f"{self.api_base_url}/products"
        ]

        for endpoint in endpoints_to_check:
            try:
                response = requests.get(endpoint, timeout=10)
                print(f"   {endpoint}: {response.status_code}")

                # Accept 200 (success) or 500 (internal error, but API is reachable)
                if response.status_code not in [200, 500]:
                    print(f"❌ API endpoint {endpoint} returned unexpected status: {response.status_code}")
                    return False

            except requests.exceptions.RequestException as e:
                print(f"❌ Failed to reach {endpoint}: {str(e)}")
                return False

        print("✅ API is accessible")
        return True

    def run_test_file(self, test_file: str) -> Dict[str, Any]:
        """Run a single E2E test file"""
        test_path = Path(__file__).parent / test_file
        test_name = test_file.replace('.py', '').replace('test_', '').replace('_e2e', '')

        print(f"\n{'='*80}")
        print(f"🧪 Running {test_name.upper()} E2E Tests")
        print(f"📁 File: {test_file}")
        print(f"{'='*80}")

        start_time = time.time()

        try:
            # Set environment variable for the test
            env = os.environ.copy()
            env['API_BASE_URL'] = self.api_base_url

            result = subprocess.run(
                [sys.executable, str(test_path)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                env=env
            )

            end_time = time.time()
            duration = end_time - start_time

            # Print the output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            test_result = {
                'test_name': test_name,
                'test_file': test_file,
                'success': result.returncode == 0,
                'exit_code': result.returncode,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr
            }

            if result.returncode == 0:
                print(f"✅ {test_name.upper()} tests PASSED ({duration:.2f}s)")
            else:
                print(f"❌ {test_name.upper()} tests FAILED (exit code: {result.returncode}, {duration:.2f}s)")

            return test_result

        except subprocess.TimeoutExpired:
            end_time = time.time()
            duration = end_time - start_time

            print(f"⏰ {test_name.upper()} tests TIMED OUT (> 5 minutes)")

            return {
                'test_name': test_name,
                'test_file': test_file,
                'success': False,
                'exit_code': -1,
                'duration': duration,
                'stdout': '',
                'stderr': 'Test timed out after 5 minutes'
            }

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            print(f"💥 {test_name.upper()} tests ERROR: {str(e)}")

            return {
                'test_name': test_name,
                'test_file': test_file,
                'success': False,
                'exit_code': -2,
                'duration': duration,
                'stdout': '',
                'stderr': str(e)
            }

    def run_smoke_test(self) -> bool:
        """Run a quick smoke test to verify basic API functionality"""
        print("\n🚀 Running smoke test...")

        try:
            # Test creating a brand
            response = requests.post(
                f"{self.api_base_url}/brands",
                json={
                    "name": "Smoke Test Brand",
                    "description": "Quick test to verify API is working"
                },
                timeout=10
            )

            if response.status_code != 201:
                print(f"❌ Smoke test failed: could not create brand (status: {response.status_code})")
                return False

            brand_data = response.json()
            brand_id = brand_data['data']['brand_id']

            # Clean up the test brand
            delete_response = requests.delete(f"{self.api_base_url}/brands/{brand_id}", timeout=10)

            if delete_response.status_code != 200:
                print(f"⚠️  Warning: Could not clean up smoke test brand {brand_id}")

            print("✅ Smoke test passed")
            return True

        except Exception as e:
            print(f"❌ Smoke test failed: {str(e)}")
            return False

    def print_summary(self):
        """Print a comprehensive test summary"""
        print(f"\n{'='*80}")
        print("📊 END-TO-END TEST SUMMARY")
        print(f"{'='*80}")

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        total_duration = sum(result['duration'] for result in self.test_results)

        print(f"📈 Overall Results:")
        print(f"   Total test suites: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⏱️  Total duration: {total_duration:.2f} seconds")
        print(f"   🎯 Success rate: {(passed_tests/total_tests)*100:.1f}%")

        print(f"\n📋 Detailed Results:")
        for result in self.test_results:
            status_icon = "✅" if result['success'] else "❌"
            print(f"   {status_icon} {result['test_name'].upper():<12} {result['duration']:>6.2f}s  {result['test_file']}")

        if failed_tests > 0:
            print(f"\n💥 Failed Test Details:")
            for result in self.test_results:
                if not result['success']:
                    print(f"\n   ❌ {result['test_name'].upper()}:")
                    print(f"      Exit Code: {result['exit_code']}")
                    if result['stderr']:
                        print(f"      Error: {result['stderr'][:200]}...")

    def run_all_tests(self) -> bool:
        """Run all E2E tests in sequence"""
        print("🎯 Starting Comprehensive End-to-End Test Suite")
        print("=" * 80)
        print(f"🔗 API Base URL: {self.api_base_url}")
        print(f"📝 Test Files: {', '.join(self.test_files)}")

        start_time = time.time()

        # Check API health first
        if not self.check_api_health():
            print("\n❌ API health check failed - aborting tests")
            return False

        # Run smoke test
        if not self.run_smoke_test():
            print("\n❌ Smoke test failed - aborting full test suite")
            return False

        # Get test directory
        tests_dir = Path(__file__).parent

        # Verify all test files exist
        missing_files = []
        for test_file in self.test_files:
            if not (tests_dir / test_file).exists():
                missing_files.append(test_file)

        if missing_files:
            print(f"\n❌ Missing test files: {', '.join(missing_files)}")
            return False

        # Run each test file
        print(f"\n🚀 Running {len(self.test_files)} test suites...")

        for test_file in self.test_files:
            result = self.run_test_file(test_file)
            self.test_results.append(result)

            # Short delay between test suites
            time.sleep(2)

        end_time = time.time()
        total_duration = end_time - start_time

        # Print summary
        self.print_summary()

        # Final result
        all_passed = all(result['success'] for result in self.test_results)

        print(f"\n{'='*80}")
        if all_passed:
            print("🎉 ALL END-TO-END TESTS PASSED!")
            print(f"⏱️  Total execution time: {total_duration:.2f} seconds")
        else:
            failed_count = sum(1 for result in self.test_results if not result['success'])
            print(f"💥 {failed_count} TEST SUITE(S) FAILED!")
            print(f"⏱️  Total execution time: {total_duration:.2f} seconds")
        print(f"{'='*80}")

        return all_passed


def main():
    """Main function"""
    print("🧪 Serverless Product Catalog API - End-to-End Test Runner")
    print("=" * 80)

    # Get API base URL
    api_url = os.getenv('API_BASE_URL')

    if not api_url:
        print("❌ ERROR: API_BASE_URL environment variable not set")
        print("\n💡 Usage:")
        print("   export API_BASE_URL=https://your-api-id.execute-api.region.amazonaws.com/stage")
        print("   python run_all_e2e_tests.py")
        print("\n📝 Example:")
        print("   export API_BASE_URL=https://abc123.execute-api.us-east-1.amazonaws.com/dev")
        print("   python run_all_e2e_tests.py")
        sys.exit(1)

    print(f"🔗 Target API: {api_url}")

    # Check if requests library is available
    try:
        import requests
    except ImportError:
        print("❌ ERROR: 'requests' library not found")
        print("   Install with: pip install requests")
        sys.exit(1)

    # Create and run test runner
    runner = E2ETestRunner(api_url)

    try:
        success = runner.run_all_tests()

        if success:
            print("\n🎊 Success! All end-to-end tests completed successfully.")
            sys.exit(0)
        else:
            print("\n🚨 Failure! Some end-to-end tests failed.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user (Ctrl+C)")
        print("🧹 Note: Any test data created during tests may need manual cleanup")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n💥 Unexpected error in test runner: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
