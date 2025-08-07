"""
Smart GUI Tester - Automated GUI error detection for the bots framework GUI.

This tool automatically starts the backend and frontend services, runs comprehensive
GUI tests, and reports any issues found without requiring manual testing.

Usage:
    python smart_gui_tester.py

Requirements:
    pip install playwright requests
    playwright install
"""

import subprocess
import time
import requests
import json
import sys
import os
from playwright.sync_api import sync_playwright
from typing import List, Dict, Any, Optional


class SmartGUITester:
    """Automated GUI testing and error detection system."""

    def __init__(self, headless: bool = True, timeout: int = 30):
        """
        Initialize the GUI tester.

        Args:
            headless: Whether to run browser in headless mode
            timeout: Timeout for operations in seconds
        """
        self.backend_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        self.headless = headless
        self.timeout = timeout
        self.issues: List[str] = []

    def start_services(self) -> bool:
        """
        Start backend and frontend services automatically.

        Returns:
            bool: True if services started successfully
        """
        try:
            print("🚀 Starting services...")

            # Start backend
            print("  📡 Starting backend...")
            backend_path = os.path.join(os.path.dirname(__file__), "backend")
            if not os.path.exists(backend_path):
                self.issues.append("❌ Backend directory not found")
                return False

            self.backend_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000", "--host", "127.0.0.1"
            ], cwd=backend_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Start frontend
            print("  🌐 Starting frontend...")
            frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
            if not os.path.exists(frontend_path):
                self.issues.append("❌ Frontend directory not found")
                return False

            self.frontend_process = subprocess.Popen([
                "npm", "run", "dev"
            ], cwd=frontend_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Wait for services to start
            return self.wait_for_services()

        except Exception as e:
            self.issues.append(f"❌ Failed to start services: {str(e)}")
            return False

    def wait_for_services(self) -> bool:
        """
        Wait for both services to be ready.

        Returns:
            bool: True if both services are ready
        """
        print("⏳ Waiting for services to start...")

        # Wait for backend
        backend_ready = False
        for i in range(self.timeout):
            try:
                response = requests.get("http://localhost:8000/api/health", timeout=2)
                if response.status_code == 200:
                    print("  ✅ Backend ready")
                    backend_ready = True
                    break
            except requests.exceptions.RequestException:
                time.sleep(1)

        if not backend_ready:
            self.issues.append("❌ Backend failed to start within timeout")
            return False

        # Wait for frontend (give it some time to compile)
        print("  ⏳ Waiting for frontend to compile...")
        time.sleep(10)

        # Test if frontend is accessible
        frontend_ready = False
        for i in range(15):  # Give frontend more time
            try:
                response = requests.get("http://localhost:3000", timeout=2)
                if response.status_code == 200:
                    print("  ✅ Frontend ready")
                    frontend_ready = True
                    break
            except requests.exceptions.RequestException:
                time.sleep(1)

        if not frontend_ready:
            self.issues.append("❌ Frontend failed to start within timeout")
            return False

        return True

    def run_comprehensive_test(self) -> List[str]:
        """
        Run all GUI tests and collect issues.

        Returns:
            List[str]: List of issues found
        """
        test_issues = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()

            # Capture all console messages
            console_messages = []
            page.on("console", lambda msg: console_messages.append({
                "type": msg.type,
                "text": msg.text,
                "location": msg.location
            }))

            # Capture network failures
            network_failures = []
            page.on("response", lambda response: 
                network_failures.append({
                    "url": response.url,
                    "status": response.status,
                    "status_text": response.status_text
                }) if response.status >= 400 else None
            )

            try:
                print("🧪 Running comprehensive GUI tests...")

                # Test 1: App loads
                print("  📱 Testing app load...")
                try:
                    page.goto("http://localhost:3000", timeout=15000)
                    page.wait_for_load_state("networkidle", timeout=10000)
                    print("    ✅ App loaded successfully")
                except Exception as e:
                    test_issues.append(f"❌ App failed to load: {str(e)}")

                # Test 2: Check for React app indicators
                print("  ⚛️  Testing React app initialization...")
                try:
                    # Look for common React app indicators
                    page.wait_for_selector("div#root", timeout=5000)
                    print("    ✅ React app initialized")
                except:
                    test_issues.append("❌ React app not properly initialized")

                # Test 3: Connection status
                print("  🔌 Testing WebSocket connection...")
                try:
                    # Wait for connection indicator or connected state
                    page.wait_for_function(
                        "document.body.innerText.includes('Connected') || document.body.innerText.includes('connected')",
                        timeout=20000
                    )
                    print("    ✅ WebSocket connected")
                except:
                    test_issues.append("❌ WebSocket connection failed or not indicated")

                # Test 4: Look for chat interface elements
                print("  💬 Testing chat interface presence...")
                try:
                    # Look for input field (textarea or input)
                    message_input = page.locator("textarea, input[type='text']").first
                    if message_input.count() > 0:
                        print("    ✅ Message input found")
                    else:
                        test_issues.append("❌ No message input field found")

                    # Look for send button
                    send_button = page.locator("button").filter(has_text="Send").first
                    if send_button.count() == 0:
                        send_button = page.locator("button[type='submit']").first

                    if send_button.count() > 0:
                        print("    ✅ Send button found")
                    else:
                        test_issues.append("❌ No send button found")

                except Exception as e:
                    test_issues.append(f"❌ Error checking chat interface: {str(e)}")

                # Test 5: Try to send a message (if interface is available)
                print("  📤 Testing message sending...")
                try:
                    message_input = page.locator("textarea, input[type='text']").first
                    send_button = page.locator("button").filter(has_text="Send").first

                    if message_input.count() > 0 and send_button.count() > 0:
                        # Fill and send message
                        message_input.fill("Hello, this is an automated test message")
                        send_button.click()

                        # Wait for message to appear in chat
                        page.wait_for_function(
                            "document.body.innerText.includes('Hello, this is an automated test message')",
                            timeout=5000
                        )
                        print("    ✅ Message sent and displayed")

                        # Test 6: Wait for bot response
                        print("  🤖 Testing bot response...")
                        try:
                            # Wait for a response (look for new content that's not our message)
                            initial_content = page.content()

                            # Wait for content to change (indicating bot response)
                            page.wait_for_function(
                                f"document.body.innerText.length > {len(initial_content)}",
                                timeout=30000
                            )
                            print("    ✅ Bot response received")
                        except:
                            test_issues.append("❌ Bot did not respond within timeout")
                    else:
                        test_issues.append("❌ Cannot test message sending - interface elements missing")

                except Exception as e:
                    test_issues.append(f"❌ Error testing message sending: {str(e)}")

                # Test 7: Check for file management features
                print("  📁 Testing file management features...")
                try:
                    # Look for file-related buttons or links
                    file_elements = page.locator("button, a").filter(has_text="File").count()
                    file_elements += page.locator("button, a").filter(has_text="Upload").count()
                    file_elements += page.locator("button, a").filter(has_text="Download").count()
                    file_elements += page.locator("button, a").filter(has_text="Save").count()

                    if file_elements > 0:
                        print("    ✅ File management features detected")
                    else:
                        print("    ⚠️  No file management features detected")

                except Exception as e:
                    test_issues.append(f"❌ Error checking file management: {str(e)}")

                # Test 8: Check for JavaScript errors
                print("  🐛 Checking for JavaScript errors...")
                js_errors = [msg for msg in console_messages if msg["type"] == "error"]
                if js_errors:
                    test_issues.append(f"❌ JavaScript errors found: {len(js_errors)}")
                    for error in js_errors[:3]:  # Show first 3
                        test_issues.append(f"   • {error['text']}")
                    if len(js_errors) > 3:
                        test_issues.append(f"   • ... and {len(js_errors) - 3} more errors")
                else:
                    print("    ✅ No JavaScript errors found")

                # Test 9: Check for network failures
                print("  🌐 Checking for network failures...")
                if network_failures:
                    test_issues.append(f"❌ Network failures detected: {len(network_failures)}")
                    for failure in network_failures[:3]:  # Show first 3
                        test_issues.append(f"   • {failure['status']} {failure['url']}")
                    if len(network_failures) > 3:
                        test_issues.append(f"   • ... and {len(network_failures) - 3} more failures")
                else:
                    print("    ✅ No network failures detected")

                # Test 10: Performance check
                print("  ⚡ Basic performance check...")
                try:
                    # Measure page load performance
                    performance = page.evaluate("performance.timing")
                    load_time = performance["loadEventEnd"] - performance["navigationStart"]

                    if load_time > 10000:  # 10 seconds
                        test_issues.append(f"⚠️  Slow page load time: {load_time}ms")
                    else:
                        print(f"    ✅ Page load time: {load_time}ms")

                except Exception as e:
                    print(f"    ⚠️  Could not measure performance: {str(e)}")

            except Exception as e:
                test_issues.append(f"❌ Test execution failed: {str(e)}")

            finally:
                browser.close()

        return test_issues

    def cleanup(self):
        """Stop all services and clean up."""
        print("🧹 Cleaning up services...")

        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
                print("  ✅ Frontend stopped")
            except:
                self.frontend_process.kill()
                print("  ⚠️  Frontend force killed")

        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                print("  ✅ Backend stopped")
            except:
                self.backend_process.kill()
                print("  ⚠️  Backend force killed")

    def run_full_test(self) -> bool:
        """
        Run complete test suite.

        Returns:
            bool: True if all tests passed
        """
        try:
            # Start services
            if not self.start_services():
                return False

            # Run tests
            test_issues = self.run_comprehensive_test()
            all_issues = self.issues + test_issues

            # Print results
            print("\n" + "="*60)
            print("🧪 SMART GUI TESTER RESULTS")
            print("="*60)

            if not all_issues:
                print("✅ ALL TESTS PASSED - GUI is working correctly!")
                print("\n🎉 Your GUI is healthy and ready to use!")
            else:
                print(f"❌ FOUND {len(all_issues)} ISSUES:")
                print()
                for issue in all_issues:
                    print(f"  {issue}")
                print()
                print("💡 Fix these issues and run the test again.")

            print("="*60)
            return len(all_issues) == 0

        except KeyboardInterrupt:
            print("\n⚠️  Test interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            return False
        finally:
            self.cleanup()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Smart GUI Tester for Bots Framework")
    parser.add_argument("--headless", action="store_true", default=True,
                       help="Run browser in headless mode (default: True)")
    parser.add_argument("--visible", action="store_true", 
                       help="Run browser in visible mode (overrides --headless)")
    parser.add_argument("--timeout", type=int, default=30,
                       help="Timeout for operations in seconds (default: 30)")

    args = parser.parse_args()

    # Handle visible mode
    headless = args.headless and not args.visible

    print("🤖 Smart GUI Tester for Bots Framework")
    print("="*50)
    print(f"Mode: {'Headless' if headless else 'Visible'}")
    print(f"Timeout: {args.timeout}s")
    print()

    tester = SmartGUITester(headless=headless, timeout=args.timeout)
    success = tester.run_full_test()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()