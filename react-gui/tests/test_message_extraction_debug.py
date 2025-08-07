#!/usr/bin/env python3
"""
Debug script specifically for message extraction in the chat interface.
Captures console logs to see how messages are being processed.
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys


class MessageExtractionDebugger:
    def __init__(self, frontend_url="http://localhost:3000"):
        self.frontend_url = frontend_url
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """Setup Chrome driver with console logging enabled."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        # Enable console logs
        chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Chrome driver initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            raise

    def get_console_logs(self):
        """Get all console logs from the browser."""
        try:
            logs = self.driver.get_log('browser')
            return logs
        except Exception as e:
            print(f"⚠️  Could not get console logs: {e}")
            return []

    def wait_for_page_load(self):
        """Wait for the page to fully load."""
        print("🔄 Waiting for page to load...")
        self.driver.get(self.frontend_url)

        # Wait for React to load
        WebDriverWait(self.driver, 15).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )

        # Wait for input box to appear (indicates app is ready)
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "textarea"))
        )

        print("✅ Page loaded and ready")
        time.sleep(2)  # Give React time to settle

    def send_test_message(self):
        """Send a test message and capture the response."""
        print("📤 Sending test message...")

        # Find input box and send message
        input_box = self.driver.find_element(By.TAG_NAME, "textarea")
        test_message = "Hello, this is a test message for debugging!"

        input_box.clear()
        input_box.send_keys(test_message)

        # Click send button
        send_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Send')]")
        send_button.click()

        print(f"✅ Sent message: '{test_message}'")

        # Wait for response (up to 15 seconds)
        print("⏳ Waiting for bot response...")
        time.sleep(15)

        print("✅ Response period complete")

    def analyze_message_extraction_logs(self):
        """Analyze console logs specifically for message extraction debug info."""
        print("🔍 Analyzing message extraction logs...")

        logs = self.get_console_logs()

        # Filter for our specific debug messages
        relevant_logs = []
        for log in logs:
            message = log.get('message', '')
            if any(keyword in message for keyword in [
                'Processing node:',
                'Node data:',
                'Final messageList:',
                'Total messages extracted:',
                'Conversation tree keys:',
                'Current node ID:',
                'bot_response received:',
                'setBotState'
            ]):
                relevant_logs.append(log)

        print(f"📊 Found {len(relevant_logs)} relevant debug messages")

        if relevant_logs:
            print("\n🔍 Debug Messages:")
            print("-" * 60)
            for log in relevant_logs:
                timestamp = log.get('timestamp', 0)
                level = log.get('level', 'INFO')
                message = log.get('message', '')
                print(f"[{level}] {message}")
            print("-" * 60)
        else:
            print("❌ No relevant debug messages found")
            print("💡 This might indicate the debug logs aren't being captured properly")

        # Also show all console logs for debugging
        print(f"\n📋 All console logs ({len(logs)} total):")
        for log in logs[-20:]:  # Show last 20 logs
            print(f"  [{log.get('level', 'INFO')}] {log.get('message', '')}")

        return len(relevant_logs) > 0

    def run_debug(self):
        """Run the complete message extraction debug."""
        print("🚀 Starting Message Extraction Debug")
        print("=" * 60)

        try:
            self.wait_for_page_load()
            self.send_test_message()
            success = self.analyze_message_extraction_logs()

            print("=" * 60)
            if success:
                print("✅ Debug completed successfully - check logs above")
            else:
                print("❌ Debug completed but no relevant logs found")

            return success

        except Exception as e:
            print(f"❌ Debug failed: {e}")
            return False

    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()


if __name__ == "__main__":
    debugger = None
    try:
        debugger = MessageExtractionDebugger()
        success = debugger.run_debug()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        exit(1)
    finally:
        if debugger:
            debugger.cleanup()