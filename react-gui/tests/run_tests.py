#!/usr/bin/env python3
"""
Comprehensive test runner for React GUI foundation with defensive programming validation.
Runs all tests with proper reporting, coverage analysis, and error handling.
"""

import sys
import os
import subprocess
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestRunner:
    """Test runner with defensive programming and comprehensive reporting."""

    def __init__(self, test_dir: Path):
        """Initialize test runner with defensive validation."""
        assert isinstance(test_dir, Path), f"test_dir must be Path, got {type(test_dir)}"
        assert test_dir.exists(), f"Test directory does not exist: {test_dir}"
        assert test_dir.is_dir(), f"Test directory is not a directory: {test_dir}"

        self.test_dir = test_dir
        self.results: Dict[str, Any] = {
            "start_time": None,
            "end_time": None,
            "duration": 0,
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
            "coverage": {},
            "test_files": []
        }

    def discover_tests(self) -> List[Path]:
        """Discover all test files with defensive validation."""
        test_files = []

        # Find all Python test files
        for pattern in ["test_*.py", "*_test.py"]:
            test_files.extend(self.test_dir.rglob(pattern))

        # Find all TypeScript test files
        for pattern in ["*.test.ts", "*.test.tsx", "*.spec.ts", "*.spec.tsx"]:
            test_files.extend(self.test_dir.rglob(pattern))

        # Validate discovered files
        validated_files = []
        for file_path in test_files:
            assert file_path.exists(), f"Test file does not exist: {file_path}"
            assert file_path.is_file(), f"Test path is not a file: {file_path}"
            validated_files.append(file_path)

        return validated_files

    def run_python_tests(self, test_files: List[Path]) -> Dict[str, Any]:
        """Run Python tests with pytest and defensive validation."""
        assert isinstance(test_files, list), f"test_files must be list, got {type(test_files)}"

        python_files = [f for f in test_files if f.suffix == ".py"]
        if not python_files:
            return {"status": "skipped", "reason": "No Python test files found"}

        # Prepare pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            "--verbose",
            "--tb=short",
            "--strict-markers",
            "--strict-config",
            f"--rootdir={self.test_dir.parent}",
            "--json-report",
            f"--json-report-file={self.test_dir}/python_test_results.json",
            "--cov=backend",
            f"--cov-report=json:{self.test_dir}/python_coverage.json",
            "--cov-report=term-missing",
        ]

        # Add test files
        cmd.extend([str(f) for f in python_files])

        print(f"Running Python tests with command: {' '.join(cmd)}")

        try:
            # Run pytest
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=self.test_dir.parent,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            end_time = time.time()

            # Parse results
            results = {
                "status": "completed",
                "return_code": result.returncode,
                "duration": end_time - start_time,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

            # Load JSON report if available
            json_report_path = self.test_dir / "python_test_results.json"
            if json_report_path.exists():
                try:
                    with open(json_report_path, 'r') as f:
                        json_report = json.load(f)
                    results["json_report"] = json_report
                except Exception as e:
                    results["json_report_error"] = str(e)

            # Load coverage report if available
            coverage_path = self.test_dir / "python_coverage.json"
            if coverage_path.exists():
                try:
                    with open(coverage_path, 'r') as f:
                        coverage_report = json.load(f)
                    results["coverage"] = coverage_report
                except Exception as e:
                    results["coverage_error"] = str(e)

            return results

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "Python tests timed out after 5 minutes"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def run_typescript_tests(self, test_files: List[Path]) -> Dict[str, Any]:
        """Run TypeScript tests with Jest and defensive validation."""
        assert isinstance(test_files, list), f"test_files must be list, got {type(test_files)}"

        ts_files = [f for f in test_files if f.suffix in [".ts", ".tsx"]]
        if not ts_files:
            return {"status": "skipped", "reason": "No TypeScript test files found"}

        # Check if Jest is available
        frontend_dir = self.test_dir.parent / "frontend"
        if not frontend_dir.exists():
            return {"status": "skipped", "reason": "Frontend directory not found"}

        package_json = frontend_dir / "package.json"
        if not package_json.exists():
            return {"status": "skipped", "reason": "package.json not found"}

        # Prepare Jest command
        cmd = ["npm", "test", "--", "--watchAll=false", "--coverage", "--json"]

        print(f"Running TypeScript tests with command: {' '.join(cmd)}")

        try:
            # Run Jest
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            end_time = time.time()

            # Parse results
            results = {
                "status": "completed",
                "return_code": result.returncode,
                "duration": end_time - start_time,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

            # Try to parse Jest JSON output
            try:
                # Jest outputs JSON to stdout
                lines = result.stdout.split('\n')
                json_line = None
                for line in lines:
                    if line.strip().startswith('{') and '"testResults"' in line:
                        json_line = line
                        break

                if json_line:
                    jest_report = json.loads(json_line)
                    results["jest_report"] = jest_report
            except Exception as e:
                results["jest_report_error"] = str(e)

            return results

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "TypeScript tests timed out after 5 minutes"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests with special handling."""
        integration_dir = self.test_dir / "integration"
        if not integration_dir.exists():
            return {"status": "skipped", "reason": "Integration test directory not found"}

        integration_files = list(integration_dir.glob("test_*.py"))
        if not integration_files:
            return {"status": "skipped", "reason": "No integration test files found"}

        # Run integration tests with special markers
        cmd = [
            sys.executable, "-m", "pytest",
            "--verbose",
            "--tb=short",
            "-m", "integration",
            f"--rootdir={self.test_dir.parent}",
            "--json-report",
            f"--json-report-file={self.test_dir}/integration_test_results.json",
        ]

        cmd.extend([str(f) for f in integration_files])

        print(f"Running integration tests with command: {' '.join(cmd)}")

        try:
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=self.test_dir.parent,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for integration tests
            )
            end_time = time.time()

            results = {
                "status": "completed",
                "return_code": result.returncode,
                "duration": end_time - start_time,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

            # Load JSON report if available
            json_report_path = self.test_dir / "integration_test_results.json"
            if json_report_path.exists():
                try:
                    with open(json_report_path, 'r') as f:
                        json_report = json.load(f)
                    results["json_report"] = json_report
                except Exception as e:
                    results["json_report_error"] = str(e)

            return results

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "Integration tests timed out after 10 minutes"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def run_defensive_tests(self) -> Dict[str, Any]:
        """Run defensive programming tests specifically."""
        cmd = [
            sys.executable, "-m", "pytest",
            "--verbose",
            "--tb=short",
            "-m", "defensive",
            f"--rootdir={self.test_dir.parent}",
            "--json-report",
            f"--json-report-file={self.test_dir}/defensive_test_results.json",
        ]

        print(f"Running defensive programming tests with command: {' '.join(cmd)}")

        try:
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=self.test_dir.parent,
                capture_output=True,
                text=True,
                timeout=300
            )
            end_time = time.time()

            results = {
                "status": "completed",
                "return_code": result.returncode,
                "duration": end_time - start_time,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

            # Load JSON report if available
            json_report_path = self.test_dir / "defensive_test_results.json"
            if json_report_path.exists():
                try:
                    with open(json_report_path, 'r') as f:
                        json_report = json.load(f)
                    results["json_report"] = json_report
                except Exception as e:
                    results["json_report_error"] = str(e)

            return results

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "Defensive tests timed out after 5 minutes"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive test report with defensive validation."""
        assert isinstance(results, dict), f"results must be dict, got {type(results)}"

        report_lines = [
            "=" * 80,
            "REACT GUI FOUNDATION TEST REPORT",
            "=" * 80,
            f"Start Time: {results.get('start_time', 'Unknown')}",
            f"End Time: {results.get('end_time', 'Unknown')}",
            f"Total Duration: {results.get('duration', 0):.2f} seconds",
            "",
            "TEST SUMMARY",
            "-" * 40,
        ]

        # Python tests summary
        if "python_tests" in results:
            python_results = results["python_tests"]
            report_lines.extend([
                f"Python Tests: {python_results.get('status', 'Unknown')}",
                f"  Duration: {python_results.get('duration', 0):.2f} seconds",
                f"  Return Code: {python_results.get('return_code', 'Unknown')}",
            ])

            if "json_report" in python_results:
                json_report = python_results["json_report"]
                summary = json_report.get("summary", {})
                report_lines.extend([
                    f"  Total: {summary.get('total', 0)}",
                    f"  Passed: {summary.get('passed', 0)}",
                    f"  Failed: {summary.get('failed', 0)}",
                    f"  Skipped: {summary.get('skipped', 0)}",
                ])

        # TypeScript tests summary
        if "typescript_tests" in results:
            ts_results = results["typescript_tests"]
            report_lines.extend([
                "",
                f"TypeScript Tests: {ts_results.get('status', 'Unknown')}",
                f"  Duration: {ts_results.get('duration', 0):.2f} seconds",
                f"  Return Code: {ts_results.get('return_code', 'Unknown')}",
            ])

            if "jest_report" in ts_results:
                jest_report = ts_results["jest_report"]
                report_lines.extend([
                    f"  Total: {jest_report.get('numTotalTests', 0)}",
                    f"  Passed: {jest_report.get('numPassedTests', 0)}",
                    f"  Failed: {jest_report.get('numFailedTests', 0)}",
                    f"  Skipped: {jest_report.get('numPendingTests', 0)}",
                ])

        # Integration tests summary
        if "integration_tests" in results:
            integration_results = results["integration_tests"]
            report_lines.extend([
                "",
                f"Integration Tests: {integration_results.get('status', 'Unknown')}",
                f"  Duration: {integration_results.get('duration', 0):.2f} seconds",
                f"  Return Code: {integration_results.get('return_code', 'Unknown')}",
            ])

        # Defensive tests summary
        if "defensive_tests" in results:
            defensive_results = results["defensive_tests"]
            report_lines.extend([
                "",
                f"Defensive Tests: {defensive_results.get('status', 'Unknown')}",
                f"  Duration: {defensive_results.get('duration', 0):.2f} seconds",
                f"  Return Code: {defensive_results.get('return_code', 'Unknown')}",
            ])

        # Coverage summary
        if "python_tests" in results and "coverage" in results["python_tests"]:
            coverage = results["python_tests"]["coverage"]
            if "totals" in coverage:
                totals = coverage["totals"]
                coverage_percent = totals.get("percent_covered", 0)
                report_lines.extend([
                    "",
                    "COVERAGE SUMMARY",
                    "-" * 40,
                    f"Total Coverage: {coverage_percent:.1f}%",
                    f"Lines Covered: {totals.get('covered_lines', 0)}",
                    f"Lines Missing: {totals.get('missing_lines', 0)}",
                ])

        # Errors and failures
        errors = []
        for test_type, test_results in results.items():
            if isinstance(test_results, dict) and test_results.get("return_code", 0) != 0:
                errors.append(f"{test_type}: {test_results.get('stderr', 'Unknown error')}")

        if errors:
            report_lines.extend([
                "",
                "ERRORS AND FAILURES",
                "-" * 40,
            ])
            report_lines.extend(errors)

        report_lines.extend([
            "",
            "=" * 80,
        ])

        return "\n".join(report_lines)

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results."""
        print("Starting comprehensive test run...")

        start_time = time.time()
        self.results["start_time"] = time.strftime("%Y-%m-%d %H:%M:%S")

        # Discover test files
        test_files = self.discover_tests()
        self.results["test_files"] = [str(f) for f in test_files]

        print(f"Discovered {len(test_files)} test files")

        # Run different test suites
        results = {}

        # Python tests
        print("\n" + "="*50)
        print("RUNNING PYTHON TESTS")
        print("="*50)
        results["python_tests"] = self.run_python_tests(test_files)

        # TypeScript tests
        print("\n" + "="*50)
        print("RUNNING TYPESCRIPT TESTS")
        print("="*50)
        results["typescript_tests"] = self.run_typescript_tests(test_files)

        # Integration tests
        print("\n" + "="*50)
        print("RUNNING INTEGRATION TESTS")
        print("="*50)
        results["integration_tests"] = self.run_integration_tests()

        # Defensive programming tests
        print("\n" + "="*50)
        print("RUNNING DEFENSIVE PROGRAMMING TESTS")
        print("="*50)
        results["defensive_tests"] = self.run_defensive_tests()

        # Calculate totals
        end_time = time.time()
        self.results["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self.results["duration"] = end_time - start_time

        # Merge results
        results.update(self.results)

        return results

    def save_results(self, results: Dict[str, Any], output_file: Optional[Path] = None) -> None:
        """Save test results to JSON file with defensive validation."""
        assert isinstance(results, dict), f"results must be dict, got {type(results)}"

        if output_file is None:
            output_file = self.test_dir / "test_results.json"

        assert isinstance(output_file, Path), f"output_file must be Path, got {type(output_file)}"

        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"Test results saved to: {output_file}")
        except Exception as e:
            print(f"Error saving test results: {e}")


def main():
    """Main entry point with argument parsing and defensive validation."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive tests for React GUI foundation"
    )
    parser.add_argument(
        "--test-dir",
        type=Path,
        default=Path(__file__).parent,
        help="Directory containing tests"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for test results JSON"
    )
    parser.add_argument(
        "--python-only",
        action="store_true",
        help="Run only Python tests"
    )
    parser.add_argument(
        "--typescript-only",
        action="store_true",
        help="Run only TypeScript tests"
    )
    parser.add_argument(
        "--integration-only",
        action="store_true",
        help="Run only integration tests"
    )
    parser.add_argument(
        "--defensive-only",
        action="store_true",
        help="Run only defensive programming tests"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Defensive validation
    if not args.test_dir.exists():
        print(f"Error: Test directory does not exist: {args.test_dir}")
        sys.exit(1)

    if not args.test_dir.is_dir():
        print(f"Error: Test directory is not a directory: {args.test_dir}")
        sys.exit(1)

    # Create test runner
    runner = TestRunner(args.test_dir)

    try:
        # Run tests based on arguments
        if args.python_only:
            test_files = runner.discover_tests()
            results = {"python_tests": runner.run_python_tests(test_files)}
        elif args.typescript_only:
            test_files = runner.discover_tests()
            results = {"typescript_tests": runner.run_typescript_tests(test_files)}
        elif args.integration_only:
            results = {"integration_tests": runner.run_integration_tests()}
        elif args.defensive_only:
            results = {"defensive_tests": runner.run_defensive_tests()}
        else:
            results = runner.run_all_tests()

        # Generate and display report
        report = runner.generate_report(results)
        print("\n" + report)

        # Save results
        runner.save_results(results, args.output)

        # Exit with appropriate code
        exit_code = 0
        for test_type, test_results in results.items():
            if isinstance(test_results, dict) and test_results.get("return_code", 0) != 0:
                exit_code = 1
                break

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error running tests: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()