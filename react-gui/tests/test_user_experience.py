#!/usr/bin/env python3
"""
Test actual user experience - what the user sees after sending messages.
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_user_experience():
    print("🧪 Testing Real User Experience")
    print("=" * 50)
    
    # Setup Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Load the page
        print("1️⃣ Loading page...")
        driver.get("http://localhost:3000")
        
        # Wait for page to load completely
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Check initial state
        print("2️⃣ Checking initial state...")
        try:
            # Wait for connection
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Connected')]"))
            )
            print("   ✅ Connected to backend")
        except:
            print("   ❌ Failed to connect or connection status not found")
            return False
        
        # Check for message area
        print("3️⃣ Checking message display area...")
        message_area = driver.find_elements(By.CLASS_NAME, "message")
        print(f"   📊 Initial messages: {len(message_area)}")
        
        # Send a message
        print("4️⃣ Sending test message...")
        input_box = driver.find_element(By.TAG_NAME, "textarea")
        test_message = "Hello! This should appear in the chat."
        input_box.clear()
        input_box.send_keys(test_message)
        
        send_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Send')]")
        send_button.click()
        print(f"   ✅ Sent message: '{test_message}'")
        
        # Wait for response and check what actually appears
        print("5️⃣ Waiting for response and checking display...")
        time.sleep(3)  # Wait for processing
        
        # Check if our message appears
        page_text = driver.find_element(By.TAG_NAME, "body").text
        if test_message in page_text:
            print("   ✅ User message appears on page")
        else:
            print("   ❌ User message NOT visible on page")
        
        # Check for bot response
        if "Mock response" in page_text:
            print("   ✅ Bot response appears on page")
        else:
            print("   ❌ Bot response NOT visible on page")
        
        # Check console for errors
        logs = driver.get_log('browser')
        errors = [log for log in logs if log['level'] == 'SEVERE']
        if errors:
            print("   ❌ Console errors found:")
            for error in errors[-3:]:
                print(f"      {error['message']}")
        else:
            print("   ✅ No console errors")
        
        print("\n📊 Page content after message:")
        print(page_text[:500] + "..." if len(page_text) > 500 else page_text)
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_user_experience()
