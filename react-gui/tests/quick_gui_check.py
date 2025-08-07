"""
Quick GUI Health Check - Fast automated GUI validation.

This tool provides a rapid health check of the GUI without starting services,
useful for quick validation during development.

Usage:
    python quick_gui_check.py

Requirements:
    pip install requests playwright
"""

import requests
import json
import sys
import os
from typing import Dict, Any


def check_backend_health() -> Dict[str, Any]:
    """
    Check if backend is running and healthy.

    Returns:
        Dict containing status and details
    """
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "healthy",
                "details": f"Backend responding (bots: {data.get('bots_count', 0)})"
            }
        else:
            return {
                "status": "error", 
                "details": f"Backend returned {response.status_code}"
            }
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "details": "Backend not responding (not started?)"
        }
    except Exception as e:
        return {
            "status": "error",
            "details": f"Backend check failed: {str(e)}"
        }


def check_frontend_health() -> Dict[str, Any]:
    """
    Check if frontend is accessible and loading.

    Returns:
        Dict containing status and details
    """
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                # Capture console errors
                console_errors = []
                page.on("console", lambda msg: 
                    console_errors.append(msg.text) if msg.type == "error" else None
                )

                # Try to load the page
                page.goto("http://localhost:3000", timeout=10000)
                page.wait_for_selector("body", timeout=5000)

                # Check page title
                title = page.title()
                if "error" in title.lower() or "404" in title:
                    return {
                        "status": "error",
                        "details": f"Error in page title: {title}"
                    }

                # Check for React root
                root_exists = page.locator("#root").count() > 0
                if not root_exists:
                    return {
                        "status": "warning",
                        "details": "React root element not found"
                    }

                # Check for console errors
                if console_errors:
                    return {
                        "status": "warning",
                        "details": f"JavaScript errors: {len(console_errors)} found"
                    }

                return {
                    "status": "healthy",
                    "details": "Frontend loading correctly"
                }

            except Exception as e:
                return {
                    "status": "error",
                    "details": f"Frontend check failed: {str(e)}"
                }
            finally:
                browser.close()

    except ImportError:
        return {
            "status": "error",
            "details": "Playwright not installed (pip install playwright)"
        }


def check_websocket_connectivity() -> Dict[str, Any]:
    """
    Test WebSocket connectivity by checking if the endpoint is accessible.

    Returns:
        Dict containing status and details
    """
    try:
        # Simple HTTP check to WebSocket endpoint
        # Should return 426 Upgrade Required if WebSocket is working
        response = requests.get("http://localhost:8000/ws", timeout=3)

        if response.status_code == 426:  # Upgrade Required
            return {
                "status": "healthy",
                "details": "WebSocket endpoint accessible"
            }
        else:
            return {
                "status": "warning",
                "details": f"Unexpected response: {response.status_code}"
            }
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "details": "WebSocket endpoint not available"
        }
    except Exception as e:
        return {
            "status": "error",
            "details": f"WebSocket check failed: {str(e)}"
        }


def quick_gui_health_check() -> bool:
    """
    Run quick health check on all GUI components.

    Returns:
        bool: True if all checks pass
    """
    print("🏥 Quick GUI Health Check")
    print("=" * 40)

    all_healthy = True

    # Check backend
    print("📡 Backend Health:", end=" ")
    backend_result = check_backend_health()
    if backend_result["status"] == "healthy":
        print(f"✅ {backend_result['details']}")
    elif backend_result["status"] == "warning":
        print(f"⚠️  {backend_result['details']}")
    else:
        print(f"❌ {backend_result['details']}")
        all_healthy = False

    # Check frontend
    print("🌐 Frontend Health:", end=" ")
    frontend_result = check_frontend_health()
    if frontend_result["status"] == "healthy":
        print(f"✅ {frontend_result['details']}")
    elif frontend_result["status"] == "warning":
        print(f"⚠️  {frontend_result['details']}")
    else:
        print(f"❌ {frontend_result['details']}")
        all_healthy = False

    # Check WebSocket
    print("🔌 WebSocket Health:", end=" ")
    ws_result = check_websocket_connectivity()
    if ws_result["status"] == "healthy":
        print(f"✅ {ws_result['details']}")
    elif ws_result["status"] == "warning":
        print(f"⚠️  {ws_result['details']}")
    else:
        print(f"❌ {ws_result['details']}")
        all_healthy = False

    print("=" * 40)

    if all_healthy:
        print("✅ ALL SYSTEMS HEALTHY")
        print("💡 Ready for full testing with smart_gui_tester.py")
    else:
        print("❌ ISSUES DETECTED")
        print("💡 Fix issues before running full tests")

    return all_healthy


def main():
    """Main entry point."""
    print("🤖 Quick GUI Health Check for Bots Framework")
    print()

    success = quick_gui_health_check()

    print()
    if success:
        print("🎉 Quick check passed! Run 'python ../smart_gui_tester.py' for full testing.")
    else:
        print("🔧 Fix the issues above and try again.")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()