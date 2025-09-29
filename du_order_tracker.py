#!/usr/bin/env python3
"""
Du Order Tracker
A tool to automatically track orders on du.ae website
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import os

class DuOrderTracker:
    def __init__(self, headless=True):
        """
        Initialize the Du Order Tracker
        
        Args:
            headless (bool): Run browser in headless mode
        """
        self.url = "https://shop.du.ae/en/order-tracking"
        self.driver = None
        self.setup_logging()
        self.setup_driver(headless)
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('du_tracker.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self, headless=True):
        """Setup Chrome WebDriver with options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise
    
    def track_order(self, order_number, mobile_number):
        """
        Track order on du.ae website
        
        Args:
            order_number (str): Order number (e.g., CM0002680507)
            mobile_number (str): Mobile number (e.g., 0561716359)
        
        Returns:
            dict: Order tracking results
        """
        try:
            self.logger.info(f"Starting order tracking for order: {order_number}")
            
            # Navigate to the order tracking page
            self.driver.get(self.url)
            self.logger.info("Navigated to du.ae order tracking page")
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, 10)
            
            # Find and fill order number field
            try:
                order_input = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#command > div.form__inner > div:nth-child(1) > input[type=text]"))
                )
                order_input.clear()
                order_input.send_keys(order_number)
                self.logger.info(f"Entered order number: {order_number}")
            except TimeoutException:
                self.logger.error("Could not find order number input field")
                raise
            
            # Find and fill mobile number field
            try:
                mobile_input = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#command > div.form__inner > div:nth-child(2) > input"))
                )
                mobile_input.clear()
                mobile_input.send_keys(mobile_number)
                self.logger.info(f"Entered mobile number: {mobile_number}")
            except TimeoutException:
                self.logger.error("Could not find mobile number input field")
                raise
            
            # Find and click track button
            try:
                track_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#command > div.form-section > button"))
                )
                track_button.click()
                self.logger.info("Clicked track order button")
            except TimeoutException:
                # Try alternative selectors
                try:
                    track_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    track_button.click()
                    self.logger.info("Clicked track order button (alternative selector)")
                except NoSuchElementException:
                    try:
                        track_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Track')]")
                        track_button.click()
                        self.logger.info("Clicked track order button (fallback selector)")
                    except NoSuchElementException:
                        self.logger.error("Could not find track button")
                        raise
            
            # Wait for results to load and check for errors
            self.logger.info("Waiting for page to load...")
            time.sleep(3)  # Reduced wait time
            
            # Check for error messages first
            try:
                error_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Errors were found') or contains(text(), 'Please check the errors') or contains(text(), 'Invalid') or contains(text(), 'not found')]")
                if error_elements:
                    self.logger.info("❌ Error detected: Order/customer mismatch - moving to next customer")
                    return {"error": "Order/customer mismatch", "status": "no_match"}
            except Exception as e:
                self.logger.debug(f"Error checking for error messages: {e}")
            
            # If no errors, wait a bit more for valid results
            time.sleep(2)
            self.logger.info("Wait completed, proceeding to capture results")
            
            # Capture the results
            results = self.capture_results()
            
            # Save data in separate file as requested
            self.save_data_separate_file(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error tracking order: {e}")
            return {"error": str(e)}
    
    def capture_results(self):
        """
        Capture the order tracking results from the page
        
        Returns:
            dict: Order tracking information
        """
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "order_status": "Unknown",
            "tracking_info": {},
            "page_content": ""
        }
        
        try:
            # Wait for results to appear
            wait = WebDriverWait(self.driver, 10)
            
            # Try to find order status information
            try:
                status_element = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".order-status, .status, [class*='status']"))
                )
                results["order_status"] = status_element.text
                self.logger.info(f"Found order status: {results['order_status']}")
            except TimeoutException:
                self.logger.warning("Could not find order status element")
            
            # Try to find tracking details
            try:
                tracking_elements = self.driver.find_elements(By.CSS_SELECTOR, ".tracking-info, .order-details, [class*='tracking']")
                for element in tracking_elements:
                    if element.text.strip():
                        results["tracking_info"][element.get_attribute("class") or "info"] = element.text
            except Exception as e:
                self.logger.warning(f"Could not extract tracking details: {e}")
            
            # Capture page content for manual review
            results["page_content"] = self.driver.page_source
            
            # Take a screenshot for reference
            screenshot_path = f"order_tracking_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            results["screenshot"] = screenshot_path
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            
        except Exception as e:
            self.logger.error(f"Error capturing results: {e}")
            results["error"] = str(e)
        
        return results
    
    def save_results(self, results, filename=None):
        """
        Save tracking results to JSON file
        
        Args:
            results (dict): Tracking results
            filename (str): Optional filename
        """
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"order_tracking_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Results saved to: {filename}")
        return filename
    
    def save_data_separate_file(self, results, filename=None):
        """
        Save data in a separate file as requested
        
        Args:
            results (dict): Tracking results
            filename (str): Optional filename
        """
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"order_data_{timestamp}.json"
        
        # Create a simplified data structure for the separate file
        data_to_save = {
            "timestamp": results.get('timestamp', time.strftime("%Y-%m-%d %H:%M:%S")),
            "order_status": results.get('order_status', 'Unknown'),
            "tracking_info": results.get('tracking_info', {}),
            "page_title": self.driver.title if self.driver else "Unknown",
            "current_url": self.driver.current_url if self.driver else "Unknown"
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Data saved to separate file: {filename}")
        return filename
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Browser driver closed")

def main():
    """Main function to run the order tracker"""
    # Order details
    order_number = "CM0002680507"
    mobile_number = "0561716359"
    
    # Initialize tracker
    tracker = DuOrderTracker(headless=False)  # Set to True for headless mode
    
    try:
        # Track the order
        results = tracker.track_order(order_number, mobile_number)
        
        # Save results
        filename = tracker.save_results(results)
        
        # Print results
        print("\n" + "="*50)
        print("ORDER TRACKING RESULTS")
        print("="*50)
        print(f"Order Number: {order_number}")
        print(f"Mobile Number: {mobile_number}")
        print(f"Timestamp: {results.get('timestamp', 'N/A')}")
        print(f"Order Status: {results.get('order_status', 'N/A')}")
        
        if results.get('tracking_info'):
            print("\nTracking Information:")
            for key, value in results['tracking_info'].items():
                print(f"  {key}: {value}")
        
        if results.get('screenshot'):
            print(f"\nScreenshot saved: {results['screenshot']}")
        
        print(f"\nFull results saved to: {filename}")
        
        if results.get('error'):
            print(f"\nError: {results['error']}")
    
    except Exception as e:
        print(f"Error: {e}")
        logging.error(f"Main execution error: {e}")
    
    finally:
        # Close the browser
        tracker.close()

if __name__ == "__main__":
    main()
