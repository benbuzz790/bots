#!/usr/bin/env python3
"""
Simple GUI Test - Quick test runner for the GUI testing suite.

This script provides a simple way to test the GUI without complex setup.

Usage:
    python simple_gui_test.py
"""

import sys
import os
import subprocess
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed."""
    missing_deps = []

    try:
        import requests
    except ImportError:
        missing_deps.append("requests")

    try:
        import playwright
    except ImportError:
        missing_deps.append("playwright")

    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"   • {dep}")
        print()
        print("Install with:")
        print(f"   pip install {' '.join(missing_deps)}")
        if "playwright" in missing_deps:
            print("   playwright install")
        return False

    return True


def run_quick_check():
    """Run quick health check."""
    print("🚀 Running Quick GUI Health Check...")
    print()

    # Import and run the quick check
    sys.path.insert(0, str(Path(__file__).parent.parent))

    try:
        from quick_gui_check import quick_gui_health_check
        return quick_gui_health_check()
    except ImportError as e:
        print(f"❌ Could not import quick_gui_check: {e}")
        return False
    except Exception as e:
        print(f"❌ Quick check failed: {e}")
        return False


def run_smart_gui_tester():
    """Run the comprehensive smart_gui_tester."""
    print("🚀 Running Smart GUI Tester...")
    print()

    # Look for smart_gui_tester.py in parent directory
    smart_tester_path = Path(__file__).parent.parent / "smart_gui_tester.py"

    if not smart_tester_path.exists():
        print("❌ smart_gui_tester.py not found in parent directory")
        print("💡 Make sure smart_gui_tester.py is in the react-gui directory")
        return False

    try:
        result = subprocess.run([
            sys.executable, str(smart_tester_path), "--headless"
        ], timeout=600)  # 10 minute timeout

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("❌ Smart GUI tester timed out after 10 minutes")
        return False
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error running smart GUI tester: {str(e)}")
        return False


def main():
    """Main entry point."""
    print("🧪 Simple GUI Test Runner for Bots Framework")
    print("=" * 50)
    print()

    # Check dependencies first
    if not check_dependencies():
        print("💡 Install dependencies and try again")
        sys.exit(1)

    print("✅ Dependencies are available")
    print()

    # Ask user what they want to do
    print("What would you like to do?")
    print("1. Quick Health Check (2 minutes)")
    print("2. Full Comprehensive Test (10 minutes)")
    print("0. Exit")
    print()

    try:
        choice = input("Select option (0-2): ").strip()

        if choice == "0":
            print("👋 Goodbye!")
            sys.exit(0)
        elif choice == "1":
            print()
            success = run_quick_check()
        elif choice == "2":
            print()
            success = run_smart_gui_tester()
        else:
            print("❌ Invalid choice")
            sys.exit(1)

        print()
        if success:
            print("🎉 Test completed successfully!")
        else:
            print("❌ Test failed - check the output above for details")

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import os
    import subprocess
    import requests
    from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed."""
    missing_deps = []
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    try:
        import playwright
    except ImportError:
        missing_deps.append("playwright")
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"   • {dep}")
        print()
        print("Install with:")
        print(f"   pip install {' '.join(missing_deps)}")
        if "playwright" in missing_deps:
            print("   playwright install")
        return False
    
    return True


def check_backend_health():
    """Check if backend is running."""
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return True, f"Backend responding (bots: {data.get('bots_count', 0)})"
        else:
            return False, f"Backend returned {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Backend not responding (not started?)"
    except Exception as e:
        return False, f"Backend check failed: {str(e)}"


def check_frontend_health():
    """Check if frontend is running."""
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            return True, "Frontend responding"
        else:
            return False, f"Frontend returned {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Frontend not responding (not started?)"
    except Exception as e:
        return False, f"Frontend check failed: {str(e)}"


def run_quick_check():
    """Run quick health check."""
    print("🚀 Running Quick GUI Health Check...")
    print("=" * 40)
    
    all_healthy = True
    
    # Check backend
    print("📡 Backend Health:", end=" ")
    backend_ok, backend_msg = check_backend_health()
    if backend_ok:
        print(f"✅ {backend_msg}")
    else:
        print(f"❌ {backend_msg}")
        all_healthy = False
    
    # Check frontend
    print("🌐 Frontend Health:", end=" ")
    frontend_ok, frontend_msg = check_frontend_health()
    if frontend_ok:
        print(f"✅ {frontend_msg}")
    else:
        print(f"❌ {frontend_msg}")
        all_healthy = False
    
    print("=" * 40)
    
    if all_healthy:
        print("✅ ALL SYSTEMS HEALTHY")
        print("💡 Ready for full testing!")
    else:
        print("❌ ISSUES DETECTED")
        print("💡 Start backend/frontend servers and try again")
    
    return all_healthy


def run_smart_gui_tester():
    """Run the comprehensive smart_gui_tester."""
    print("🚀 Running Smart GUI Tester...")
    print()
    
    # Look for smart_gui_tester.py in parent directory
    smart_tester_path = Path(__file__).parent.parent / "smart_gui_tester.py"
    
    if not smart_tester_path.exists():
        print("❌ smart_gui_tester.py not found in parent directory")
        print("💡 Make sure smart_gui_tester.py is in the react-gui directory")
        return False
    
    try:
        result = subprocess.run([
            sys.executable, str(smart_tester_path), "--headless"
        ], timeout=600)  # 10 minute timeout
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Smart GUI tester timed out after 10 minutes")
        return False
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error running smart GUI tester: {str(e)}")
        return False


def main():
    """Main entry point."""
    print("🧪 Simple GUI Test Runner for Bots Framework")
    print("=" * 50)
    print()
    
    # Check dependencies first
    if not check_dependencies():
        print("💡 Install dependencies and try again")
        sys.exit(1)
    
    print("✅ Dependencies are available")
    print()
    
    # Ask user what they want to do
    print("What would you like to do?")
    print("1. Quick Health Check (2 minutes)")
    print("2. Full Comprehensive Test (10 minutes)")
    print("0. Exit")
    print()
    
    try:
        choice = input("Select option (0-2): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            sys.exit(0)
        elif choice == "1":
            print()
            success = run_quick_check()
        elif choice == "2":
            print()
            success = run_smart_gui_tester()
        else:
            print("❌ Invalid choice")
            sys.exit(1)
        
        print()
        if success:
            print("🎉 Test completed successfully!")
        else:
            print("❌ Test failed - check the output above for details")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
    main()
