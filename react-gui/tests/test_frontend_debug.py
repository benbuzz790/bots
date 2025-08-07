#!/usr/bin/env python3
"""
Automated frontend debugging - uses Selenium to interact with the React app
and capture console logs, network requests, and UI state.
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys


class FrontendDebugger:
    def __init__(self, frontend_url="http://localhost:3000"):
        self.frontend_url = frontend_url
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """Setup Chrome driver with console logging enabled."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Enable logging
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Enable console logs
        chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Chrome driver initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            print("💡 Make sure ChromeDriver is installed and in PATH")
            raise

    def get_console_logs(self):
        """Get all console logs from the browser."""
        try:
            logs = self.driver.get_log('browser')
            return [log for log in logs if log['level'] in ['INFO', 'WARNING', 'SEVERE']]
        except Exception as e:
            print(f"⚠️  Could not get console logs: {e}")
            return []

    def test_page_load(self):
        """Test if the page loads successfully."""
        print("🔍 Testing page load...")
        try:
            self.driver.get(self.frontend_url)
            
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            title = self.driver.title
            print(f"   ✅ Page loaded: {title}")
            
            # Check for React errors
            error_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Application Error')]")
            if error_elements:
                print("   ❌ React application error detected")
                return False
            
            return True
        except Exception as e:
            print(f"   ❌ Page load failed: {e}")
            return False

    def test_input_box_presence(self):
        """Test if input box is present and functional."""
        print("🔍 Testing input box presence...")
        try:
            # Wait for input box to appear
            input_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "textarea"))
            )
            
            if input_box.is_displayed() and input_box.is_enabled():
                print("   ✅ Input box is present and enabled")
                return True
            else:
                print("   ❌ Input box is present but not functional")
                return False
                
        except Exception as e:
            print(f"   ❌ Input box not found: {e}")
            return False

    def test_send_message(self):
        """Test sending a message and check for response."""
        print("🔍 Testing message sending...")
        try:
            # Find input box
            input_box = self.driver.find_element(By.TAG_NAME, "textarea")
            
            # Clear and type message
            test_message = "Hello, automated test!"
            input_box.clear()
            input_box.send_keys(test_message)
            print(f"   ✅ Typed message: '{test_message}'")
            
            # Find and click send button
            send_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Send')]")
            if send_button.is_enabled():
                send_button.click()
                print("   ✅ Send button clicked")
                
                # Wait a moment for processing
                time.sleep(3)
                
                # Check if input was cleared (indicates message was sent)
                current_value = input_box.get_attribute('value')
                if not current_value.strip():
                    print("   ✅ Input cleared after send")
                    return True
                else:
                    print(f"   ❌ Input not cleared: '{current_value}'")
                    return False
            else:
                print("   ❌ Send button is disabled")
                return False
                
        except Exception as e:
            print(f"   ❌ Message sending failed: {e}")
            return False

    def analyze_console_logs(self):
        """Analyze console logs for errors and debug info."""
        print("🔍 Analyzing console logs...")
        logs = self.get_console_logs()
        
        errors = [log for log in logs if log['level'] == 'SEVERE']
        warnings = [log for log in logs if log['level'] == 'WARNING']
        infos = [log for log in logs if log['level'] == 'INFO']
        
        print(f"   📊 Console summary: {len(errors)} errors, {len(warnings)} warnings, {len(infos)} info")
        
        if errors:
            print("   ❌ Console errors found:")
            for error in errors[-5:]:  # Show last 5 errors
                print(f"      {error['message']}")
        
        # Look for specific debug messages
        debug_messages = [log for log in logs if 'debug:' in log['message'].lower() or 'websocket' in log['message'].lower()]
        if debug_messages:
            print("   🔍 Debug messages found:")
            for msg in debug_messages[-10:]:  # Show last 10 debug messages
                print(f"      {msg['message']}")
        
        return len(errors) == 0

    def test_ui_elements(self):
        """Test presence of key UI elements."""
        print("🔍 Testing UI elements...")
        elements_to_check = [
            ("textarea", "Input box"),
            ("button", "Send button"),
            ("//*[contains(text(), 'Connected')]", "Connection status"),
        ]
        
        all_present = True
        for selector, name in elements_to_check:
            try:
                if selector.startswith("//"):
                    elements = self.driver.find_elements(By.XPATH, selector)
                else:
                    elements = self.driver.find_elements(By.TAG_NAME, selector)
                
                if elements:
                    print(f"   ✅ {name} found")
                else:
                    print(f"   ❌ {name} not found")
                    all_present = False
            except Exception as e:
                print(f"   ❌ Error checking {name}: {e}")
                all_present = False
        
        return all_present

    def run_full_debug(self):
        """Run complete frontend debugging suite."""
        print("🚀 Starting Automated Frontend Debug")
        print("=" * 60)
        
        tests = [
            ("Page Load", self.test_page_load),
            ("UI Elements", self.test_ui_elements),
            ("Input Box", self.test_input_box_presence),
            ("Send Message", self.test_send_message),
            ("Console Analysis", self.analyze_console_logs),
        ]
        
        passed = 0
        for test_name, test_func in tests:
            result = test_func()
            if result:
                passed += 1
            print()
        
        print("=" * 60)
        print(f"🏁 Frontend Debug Complete: {passed}/{len(tests)} tests passed")
        
        return passed == len(tests)

    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()


if __name__ == "__main__":
    debugger = None
    try:
        debugger = FrontendDebugger()
        success = debugger.run_full_debug()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        exit(1)
    finally:
        if debugger:
            debugger.cleanup()
