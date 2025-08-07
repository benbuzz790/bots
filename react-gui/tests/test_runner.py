#!/usr/bin/env python3
"""
Comprehensive test runner for the tree navigation system.

This script runs all navigation tests and provides detailed reporting
on the functionality, performance, and reliability of the navigation system.
"""

import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

class NavigationTestRunner:
    """Runs and reports on all navigation system tests."""

    def __init__(self):
        self.results: Dict[str, Any] = {
            'backend_tests': {},
            'frontend_tests': {},
            'integration_tests': {},
            'performance_metrics': {},
            'summary': {}
        }

    def run_backend_tests(self) -> bool:
        """Run backend navigation tests."""
        print("🔧 Running Backend Navigation Tests...")

        backend_test_files = [
            'backend/test_navigation.py',
            'backend/test_integration_navigation.py'
        ]

        all_passed = True

        for test_file in backend_test_files:
            if not Path(test_file).exists():
                print(f"⚠️  Test file not found: {test_file}")
                continue

            print(f"  Running {test_file}...")
            start_time = time.time()

            try:
                result = subprocess.run([
                    sys.executable, '-m', 'pytest', 
                    test_file, '-v', '--tb=short'
                ], capture_output=True, text=True, timeout=300)

                duration = time.time() - start_time

                self.results['backend_tests'][test_file] = {
                    'passed': result.returncode == 0,
                    'duration': duration,
                    'output': result.stdout,
                    'errors': result.stderr
                }

                if result.returncode == 0:
                    print(f"  ✅ {test_file} passed ({duration:.2f}s)")
                else:
                    print(f"  ❌ {test_file} failed ({duration:.2f}s)")
                    print(f"     Error: {result.stderr[:200]}...")
                    all_passed = False

            except subprocess.TimeoutExpired:
                print(f"  ⏰ {test_file} timed out")
                all_passed = False
            except Exception as e:
                print(f"  💥 {test_file} crashed: {e}")
                all_passed = False

        return all_passed

    def run_frontend_tests(self) -> bool:
        """Run frontend navigation tests."""
        print("\n🎨 Running Frontend Navigation Tests...")

        frontend_dir = Path('frontend')
        if not frontend_dir.exists():
            print("⚠️  Frontend directory not found")
            return False

        # Check if npm/yarn is available
        package_manager = self._detect_package_manager()
        if not package_manager:
            print("⚠️  No package manager (npm/yarn) found")
            return False

        print(f"  Using package manager: {package_manager}")

        try:
            # Install dependencies if needed
            if not (frontend_dir / 'node_modules').exists():
                print("  Installing dependencies...")
                subprocess.run([
                    package_manager, 'install'
                ], cwd=frontend_dir, check=True, timeout=300)

            # Run tests
            print("  Running frontend tests...")
            start_time = time.time()

            result = subprocess.run([
                package_manager, 'run', 'test', '--', '--run'
            ], cwd=frontend_dir, capture_output=True, text=True, timeout=300)

            duration = time.time() - start_time

            self.results['frontend_tests'] = {
                'passed': result.returncode == 0,
                'duration': duration,
                'output': result.stdout,
                'errors': result.stderr
            }

            if result.returncode == 0:
                print(f"  ✅ Frontend tests passed ({duration:.2f}s)")
                return True
            else:
                print(f"  ❌ Frontend tests failed ({duration:.2f}s)")
                print(f"     Error: {result.stderr[:200]}...")
                return False

        except subprocess.TimeoutExpired:
            print("  ⏰ Frontend tests timed out")
            return False
        except Exception as e:
            print(f"  💥 Frontend tests crashed: {e}")
            return False

    def run_integration_tests(self) -> bool:
        """Run end-to-end integration tests."""
        print("\n🔗 Running Integration Tests...")

        # Start backend server for integration tests
        backend_process = None
        try:
            print("  Starting backend server...")
            backend_process = subprocess.Popen([
                sys.executable, '-m', 'uvicorn', 
                'backend.main:app', '--port', '8001'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Wait for server to start
            time.sleep(3)

            # Run integration tests
            integration_test_files = [
                'backend/test_integration_navigation.py::TestNavigationIntegration::test_websocket_connection_lifecycle',
                'backend/test_integration_navigation.py::TestNavigationIntegration::test_complete_navigation_workflow'
            ]

            all_passed = True
            start_time = time.time()

            for test_case in integration_test_files:
                print(f"  Running {test_case.split('::')[-1]}...")

                result = subprocess.run([
                    sys.executable, '-m', 'pytest', 
                    test_case, '-v'
                ], capture_output=True, text=True, timeout=120)

                if result.returncode != 0:
                    print(f"    ❌ Failed: {result.stderr[:100]}...")
                    all_passed = False
                else:
                    print(f"    ✅ Passed")

            duration = time.time() - start_time
            self.results['integration_tests'] = {
                'passed': all_passed,
                'duration': duration
            }

            if all_passed:
                print(f"  ✅ Integration tests passed ({duration:.2f}s)")
            else:
                print(f"  ❌ Integration tests failed ({duration:.2f}s)")

            return all_passed

        except Exception as e:
            print(f"  💥 Integration tests crashed: {e}")
            return False
        finally:
            if backend_process:
                backend_process.terminate()
                backend_process.wait(timeout=10)

    def run_performance_tests(self) -> Dict[str, float]:
        """Run performance benchmarks."""
        print("\n⚡ Running Performance Tests...")

        metrics = {}

        try:
            # Test navigation speed
            print("  Testing navigation speed...")
            result = subprocess.run([
                sys.executable, '-c', '''
import time
import sys
sys.path.append("backend")
from bot_manager import BotManager
from models import NavigationDirection
from unittest.mock import Mock

# Create test setup
bot_manager = BotManager()
bot_id = "perf-test"
mock_bot = Mock()

# Simple conversation structure
root = Mock()
root.content = "Root"
root.role = "user" 
root.parent = None
root.replies = []

child = Mock()
child.content = "Child"
child.role = "assistant"
child.parent = root
child.replies = []

root.replies = [child]
mock_bot.conversation = child
bot_manager._bots[bot_id] = mock_bot

# Benchmark navigation operations
operations = 1000
start_time = time.time()

for i in range(operations):
    try:
        direction = NavigationDirection.UP if i % 2 == 0 else NavigationDirection.DOWN
        bot_manager.navigator.navigate(bot_id, direction)
    except:
        pass

end_time = time.time()
duration = end_time - start_time
ops_per_second = operations / duration

print(f"Navigation speed: {ops_per_second:.2f} ops/sec")
print(f"Average latency: {(duration/operations)*1000:.2f}ms")
'''
            ], capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                output_lines = result.stdout.strip().split('\n')
                for line in output_lines:
                    if 'ops/sec' in line:
                        ops_per_sec = float(line.split(':')[1].strip().split()[0])
                        metrics['navigation_ops_per_second'] = ops_per_sec
                        print(f"    Navigation speed: {ops_per_sec:.2f} ops/sec")
                    elif 'latency' in line:
                        latency = float(line.split(':')[1].strip().split('ms')[0])
                        metrics['average_latency_ms'] = latency
                        print(f"    Average latency: {latency:.2f}ms")

            # Test tree serialization speed
            print("  Testing tree serialization speed...")
            result = subprocess.run([
                sys.executable, '-c', '''
import time
import sys
sys.path.append("backend")
from tree_serializer import TreeSerializer
from unittest.mock import Mock

serializer = TreeSerializer()

# Create complex tree structure
def create_mock_tree(depth=5, branching=3):
    def create_node(content, role, level):
        node = Mock()
        node.content = content
        node.role = role
        node.parent = None
        node.replies = []

        if level < depth:
            for i in range(branching):
                child = create_node(f"{content}_child_{i}", "assistant" if role == "user" else "user", level + 1)
                child.parent = node
                node.replies.append(child)

        return node

    return create_node("root", "user", 0)

mock_bot = Mock()
mock_bot.conversation = create_mock_tree()

# Benchmark serialization
operations = 100
start_time = time.time()

for _ in range(operations):
    tree = serializer.convert_bot_conversation(mock_bot)

end_time = time.time()
duration = end_time - start_time
ops_per_second = operations / duration

print(f"Serialization speed: {ops_per_second:.2f} ops/sec")
'''
            ], capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if 'Serialization speed' in line:
                        ops_per_sec = float(line.split(':')[1].strip().split()[0])
                        metrics['serialization_ops_per_second'] = ops_per_sec
                        print(f"    Serialization speed: {ops_per_sec:.2f} ops/sec")

        except Exception as e:
            print(f"  💥 Performance tests failed: {e}")

        self.results['performance_metrics'] = metrics
        return metrics

    def _detect_package_manager(self) -> str:
        """Detect available package manager."""
        for pm in ['npm', 'yarn']:
            try:
                subprocess.run([pm, '--version'], 
                             capture_output=True, check=True)
                return pm
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        return ""

    def generate_report(self) -> str:
        """Generate comprehensive test report."""
        report = []
        report.append("=" * 60)
        report.append("🌳 TREE NAVIGATION SYSTEM TEST REPORT")
        report.append("=" * 60)

        # Summary
        total_tests = 0
        passed_tests = 0

        # Backend results
        if self.results['backend_tests']:
            report.append("\n📊 Backend Test Results:")
            for test_file, result in self.results['backend_tests'].items():
                status = "✅ PASS" if result['passed'] else "❌ FAIL"
                report.append(f"  {test_file}: {status} ({result['duration']:.2f}s)")
                total_tests += 1
                if result['passed']:
                    passed_tests += 1

        # Frontend results
        if self.results['frontend_tests']:
            result = self.results['frontend_tests']
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            report.append(f"\n🎨 Frontend Tests: {status} ({result['duration']:.2f}s)")
            total_tests += 1
            if result['passed']:
                passed_tests += 1

        # Integration results
        if self.results['integration_tests']:
            result = self.results['integration_tests']
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            report.append(f"\n🔗 Integration Tests: {status} ({result['duration']:.2f}s)")
            total_tests += 1
            if result['passed']:
                passed_tests += 1

        # Performance metrics
        if self.results['performance_metrics']:
            report.append("\n⚡ Performance Metrics:")
            metrics = self.results['performance_metrics']

            if 'navigation_ops_per_second' in metrics:
                ops = metrics['navigation_ops_per_second']
                status = "🚀 EXCELLENT" if ops > 1000 else "✅ GOOD" if ops > 100 else "⚠️ SLOW"
                report.append(f"  Navigation Speed: {ops:.2f} ops/sec {status}")

            if 'average_latency_ms' in metrics:
                latency = metrics['average_latency_ms']
                status = "🚀 EXCELLENT" if latency < 1 else "✅ GOOD" if latency < 10 else "⚠️ SLOW"
                report.append(f"  Average Latency: {latency:.2f}ms {status}")

            if 'serialization_ops_per_second' in metrics:
                ops = metrics['serialization_ops_per_second']
                status = "🚀 EXCELLENT" if ops > 500 else "✅ GOOD" if ops > 50 else "⚠️ SLOW"
                report.append(f"  Serialization Speed: {ops:.2f} ops/sec {status}")

        # Overall summary
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        report.append(f"\n📈 Overall Results:")
        report.append(f"  Tests Passed: {passed_tests}/{total_tests}")
        report.append(f"  Success Rate: {success_rate:.1f}%")

        if success_rate >= 90:
            report.append("  Status: 🎉 EXCELLENT - Navigation system is ready for production!")
        elif success_rate >= 75:
            report.append("  Status: ✅ GOOD - Navigation system is functional with minor issues")
        elif success_rate >= 50:
            report.append("  Status: ⚠️ NEEDS WORK - Navigation system has significant issues")
        else:
            report.append("  Status: ❌ CRITICAL - Navigation system is not functional")

        # Recommendations
        report.append(f"\n💡 Recommendations:")

        if success_rate < 100:
            report.append("  • Review failed tests and fix underlying issues")

        if self.results.get('performance_metrics', {}).get('navigation_ops_per_second', 0) < 100:
            report.append("  • Optimize navigation algorithms for better performance")

        if self.results.get('performance_metrics', {}).get('average_latency_ms', 0) > 10:
            report.append("  • Reduce navigation latency through caching or optimization")

        if not self.results.get('frontend_tests', {}).get('passed', False):
            report.append("  • Fix frontend navigation components and interactions")

        if not self.results.get('integration_tests', {}).get('passed', False):
            report.append("  • Resolve WebSocket communication and state synchronization issues")

        report.append("\n" + "=" * 60)

        return "\n".join(report)

    def run_all_tests(self) -> bool:
        """Run all navigation tests and generate report."""
        print("🚀 Starting Comprehensive Navigation System Tests...\n")

        start_time = time.time()

        # Run all test suites
        backend_passed = self.run_backend_tests()
        frontend_passed = self.run_frontend_tests()
        integration_passed = self.run_integration_tests()

        # Run performance benchmarks
        self.run_performance_tests()

        total_duration = time.time() - start_time

        # Generate and display report
        report = self.generate_report()
        print(f"\n{report}")

        print(f"\n⏱️  Total test duration: {total_duration:.2f} seconds")

        # Save detailed results
        with open('navigation_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print("📄 Detailed results saved to: navigation_test_results.json")

        # Return overall success
        return backend_passed and frontend_passed and integration_passed


def main():
    """Main test runner entry point."""
    runner = NavigationTestRunner()

    try:
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()