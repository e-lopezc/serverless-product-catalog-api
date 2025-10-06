#!/usr/bin/env python3
"""
SAM Local End-to-End Test Runner
Run E2E tests against SAM local API instead of deployed API
"""

import os
import sys
import subprocess
import time
import requests
import signal
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional


class SAMLocalE2ETestRunner:
    """E2E test runner that uses SAM local instead of deployed API"""

    def __init__(self, sam_local_port: int = 3000):
        self.sam_local_port = sam_local_port
        self.sam_local_url = f"http://localhost:{sam_local_port}"
        self.sam_process: Optional[subprocess.Popen] = None
        self.test_results: List[Dict[str, Any]] = []

        # Test files in order of dependency
        self.test_files = [
            'test_brands_e2e.py',
            'test_categories_e2e.py',
            'test_products_e2e.py'
        ]

    def start_sam_local(self) -> bool:
        """Start SAM local API"""
        print("🚀 Starting SAM local API...")

        # Find the template file
        template_paths = [
            'template.yaml',
            'template.yml',
            'sam-template.yaml',
            'sam-template.yml'
        ]

        template_file = None
        for template_path in template_paths:
            if Path(template_path).exists():
                template_file = template_path
                break

        if not template_file:
            print("❌ No SAM template file found. Expected one of:")
            for path in template_paths:
                print(f"   - {path}")
            return False

        print(f"📄 Using template: {template_file}")

        # Set environment variables for local testing
        env = os.environ.copy()
        env.update({
            'DYNAMODB_TABLE': 'products_catalog',
            'AWS_REGION': 'us-east-1',
            'DYNAMODB_ENDPOINT': 'http://localhost:8000',  # DynamoDB Local
            'AWS_ACCESS_KEY_ID': 'dummy',
            'AWS_SECRET_ACCESS_KEY': 'dummy',
            'AWS_SESSION_TOKEN': 'dummy'
        })

        try:
            # Start SAM local in background
            self.sam_process = subprocess.Popen([
                'sam', 'local', 'start-api',
                '--template', template_file,
                '--port', str(self.sam_local_port),
                '--host', '0.0.0.0',
                '--warm-containers', 'EAGER'  # Keep containers warm
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            print(f"🔄 SAM local starting on port {self.sam_local_port}...")

            # Wait for SAM local to be ready
            return self.wait_for_sam_local()

        except FileNotFoundError:
            print("❌ SAM CLI not found. Install with:")
            print("   pip install aws-sam-cli")
            print("   or follow: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html")
            return False
        except Exception as e:
            print(f"❌ Failed to start SAM local: {str(e)}")
            return False

    def wait_for_sam_local(self, max_wait: int = 60) -> bool:
        """Wait for SAM local to be ready"""
        print("⏳ Waiting for SAM local to be ready...")

        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                # Try to connect to SAM local
                response = requests.get(f"{self.sam_local_url}/brands", timeout=5)

                # SAM local is ready if we get any response (even errors)
                if response.status_code in [200, 404, 500]:
                    print(f"✅ SAM local is ready! ({response.status_code})")
                    return True

            except requests.exceptions.RequestException:
                # SAM local not ready yet
                pass

            print(".", end="", flush=True)
            time.sleep(2)

        print(f"\n❌ SAM local failed to start within {max_wait} seconds")

        # Print SAM local output for debugging
        if self.sam_process:
            try:
                stdout, stderr = self.sam_process.communicate(timeout=1)
                if stdout:
                    print("SAM stdout:", stdout.decode())
                if stderr:
                    print("SAM stderr:", stderr.decode())
            except subprocess.TimeoutExpired:
                pass

        return False

    def stop_sam_local(self):
        """Stop SAM local API"""
        if self.sam_process:
            print("\n🛑 Stopping SAM local...")

            # Try graceful shutdown first
            self.sam_process.terminate()

            try:
                # Wait up to 5 seconds for graceful shutdown
                self.sam_process.wait(timeout=5)
                print("✅ SAM local stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                print("⚠️  Force killing SAM local...")
                self.sam_process.kill()
                self.sam_process.wait()
                print("✅ SAM local force stopped")

            self.sam_process = None

    def check_dynamodb_local(self) -> bool:
        """Check if DynamoDB Local is running"""
        print("🔍 Checking DynamoDB Local...")

        try:
            response = requests.get('http://localhost:8000', timeout=5)
            if response.status_code == 400:  # DynamoDB Local returns 400 for GET
                print("✅ DynamoDB Local is running")
                return True
        except requests.exceptions.RequestException:
            pass

        print("❌ DynamoDB Local not found on port 8000")
        print("   Start DynamoDB Local with:")
        print("   java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb")
        print("   or use Docker:")
        print("   docker run -p 8000:8000 amazon/dynamodb-local")
        return False

    def check_sam_build(self) -> bool:
        """Check if SAM application is built"""
        print("🔍 Checking SAM build status...")

        build_dir = Path('.aws-sam/build')
        if not build_dir.exists():
            print("❌ SAM application not built")
            print("   Run: sam build")
            return False

        # Check if build is recent
        template_file = None
        for name in ['template.yaml', 'template.yml']:
            if Path(name).exists():
                template_file = Path(name)
                break

        if template_file and template_file.exists():
            template_mtime = template_file.stat().st_mtime
            build_mtime = build_dir.stat().st_mtime

            if template_mtime > build_mtime:
                print("⚠️  Template is newer than build directory")
                print("   Consider running: sam build")
            else:
                print("✅ SAM application is built")
        else:
            print("✅ SAM build directory exists")

        return True

    def run_test_file(self, test_file: str) -> Dict[str, Any]:
        """Run a single E2E test file against SAM local"""
        test_path = Path(__file__).parent / test_file
        test_name = test_file.replace('.py', '').replace('test_', '').replace('_e2e', '')

        print(f"\n{'='*80}")
        print(f"🧪 Running {test_name.upper()} E2E Tests (SAM Local)")
        print(f"📁 File: {test_file}")
        print(f"🔗 Target: {self.sam_local_url}")
        print(f"{'='*80}")

        start_time = time.time()

        try:
            # Set environment variable for the test
            env = os.environ.copy()
            env['API_BASE_URL'] = self.sam_local_url

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
        """Run a quick smoke test against SAM local"""
        print("\n🚀 Running smoke test against SAM local...")

        try:
            # Test creating a brand
            response = requests.post(
                f"{self.sam_local_url}/brands",
                json={
                    "name": "SAM Local Smoke Test Brand",
                    "description": "Quick test to verify SAM local API is working"
                },
                timeout=30  # SAM local can be slower
            )

            if response.status_code != 201:
                print(f"❌ Smoke test failed: could not create brand (status: {response.status_code})")
                print(f"Response: {response.text}")
                return False

            brand_data = response.json()
            brand_id = brand_data['data']['brand_id']

            # Clean up the test brand
            delete_response = requests.delete(f"{self.sam_local_url}/brands/{brand_id}", timeout=30)

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
        print("📊 SAM LOCAL E2E TEST SUMMARY")
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
        print(f"   🎯 Success rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "   🎯 Success rate: 0%")

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
        """Run all E2E tests against SAM local"""
        print("🎯 Starting SAM Local End-to-End Test Suite")
        print("=" * 80)
        print(f"🔗 SAM Local URL: {self.sam_local_url}")
        print(f"📝 Test Files: {', '.join(self.test_files)}")

        start_time = time.time()

        try:
            # Pre-flight checks
            if not self.check_sam_build():
                return False

            if not self.check_dynamodb_local():
                return False

            # Start SAM local
            if not self.start_sam_local():
                return False

            # Run smoke test
            if not self.run_smoke_test():
                print("\n❌ Smoke test failed - aborting full test suite")
                return False

            # Verify all test files exist
            tests_dir = Path(__file__).parent
            missing_files = []
            for test_file in self.test_files:
                if not (tests_dir / test_file).exists():
                    missing_files.append(test_file)

            if missing_files:
                print(f"\n❌ Missing test files: {', '.join(missing_files)}")
                return False

            # Run each test file
            print(f"\n🚀 Running {len(self.test_files)} test suites against SAM local...")

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
                print("🎉 ALL SAM LOCAL E2E TESTS PASSED!")
                print(f"⏱️  Total execution time: {total_duration:.2f} seconds")
            else:
                failed_count = sum(1 for result in self.test_results if not result['success'])
                print(f"💥 {failed_count} TEST SUITE(S) FAILED!")
                print(f"⏱️  Total execution time: {total_duration:.2f} seconds")
            print(f"{'='*80}")

            return all_passed

        finally:
            # Always stop SAM local
            self.stop_sam_local()


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n⚠️  Test interrupted by user (Ctrl+C)")
    sys.exit(1)


def main():
    """Main function"""
    print("🧪 Serverless Product Catalog API - SAM Local E2E Test Runner")
    print("=" * 80)

    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    # Check if requests library is available
    try:
        import requests
    except ImportError:
        print("❌ ERROR: 'requests' library not found")
        print("   Install with: pip install requests")
        sys.exit(1)

    # Parse command line arguments
    port = 3000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"❌ Invalid port number: {sys.argv[1]}")
            sys.exit(1)

    print(f"🔗 SAM Local Port: {port}")
    print("💡 Make sure to run 'sam build' before running these tests")
    print("💡 Make sure DynamoDB Local is running on port 8000")

    # Create and run test runner
    runner = SAMLocalE2ETestRunner(port)

    try:
        success = runner.run_all_tests()

        if success:
            print("\n🎊 Success! All SAM local E2E tests completed successfully.")
            sys.exit(0)
        else:
            print("\n🚨 Failure! Some SAM local E2E tests failed.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user (Ctrl+C)")
        runner.stop_sam_local()
        sys.exit(1)

    except Exception as e:
        print(f"\n\n💥 Unexpected error in test runner: {str(e)}")
        import traceback
        traceback.print_exc()
        runner.stop_sam_local()
        sys.exit(1)


if __name__ == '__main__':
    main()
