#!/usr/bin/env python3
"""
Railway deployment with fixed ChromeDriver setup
Uses webdriver-manager for automatic ChromeDriver management
"""

import os
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import csv

class RailwayOrderTracker:
    def __init__(self, headless=True):
        """Initialize Railway-compatible order tracker"""
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
                logging.FileHandler('railway_tracker.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self, headless=True):
        """Setup Chrome WebDriver with Railway-compatible options"""
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Use webdriver-manager for automatic ChromeDriver management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.logger.info("Chrome WebDriver initialized successfully on Railway")
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise
    
    def track_order(self, order_number, mobile_number):
        """Track order on du.ae website"""
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
                return {"error": "Order number field not found"}
            
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
                return {"error": "Mobile number field not found"}
            
            # Find and click track button
            try:
                track_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#command > div.form-section > button"))
                )
                track_button.click()
                self.logger.info("Clicked track order button")
            except TimeoutException:
                self.logger.error("Could not find track button")
                return {"error": "Track button not found"}
            
            # Wait for results and check for errors
            self.logger.info("Waiting for page to load...")
            time.sleep(3)
            
            # Check for error messages
            try:
                error_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Errors were found') or contains(text(), 'Please check the errors') or contains(text(), 'Invalid') or contains(text(), 'not found')]")
                if error_elements:
                    self.logger.info("❌ Error detected: Order/customer mismatch")
                    return {"error": "Order/customer mismatch", "status": "no_match"}
            except Exception as e:
                self.logger.debug(f"Error checking for error messages: {e}")
            
            # If no errors, wait a bit more for valid results
            time.sleep(2)
            self.logger.info("Wait completed, proceeding to capture results")
            
            # Capture the results
            results = self.capture_results()
            return results
            
        except Exception as e:
            self.logger.error(f"Error tracking order: {e}")
            return {"error": str(e)}
    
    def capture_results(self):
        """Capture the order tracking results from the page"""
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
            
        except Exception as e:
            self.logger.error(f"Error capturing results: {e}")
            results["error"] = str(e)
        
        return results
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Browser driver closed")

class RailwayBatchTracker:
    def __init__(self, headless=True):
        """Initialize Railway batch tracker"""
        self.tracker = None
        self.setup_logging()
        self.setup_tracker(headless)
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('railway_batch_tracker.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_tracker(self, headless=True):
        """Setup the order tracker"""
        try:
            self.tracker = RailwayOrderTracker(headless=headless)
            self.logger.info("Railway Batch Tracker initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize tracker: {e}")
            raise
    
    def process_single_order(self, order_number, customer_numbers):
        """Process a single order against all customer numbers"""
        order_result = {
            "order_number": order_number,
            "status": "not_found",
            "matched_customer": None,
            "order_status": None,
            "delivery_date": None,
            "total_amount": None,
            "items": None,
            "attempts": 0,
            "error": None,
            "timestamp": datetime.now().isoformat()
        }
        
        for customer_number in customer_numbers:
            order_result["attempts"] += 1
            
            try:
                self.logger.info(f"Testing {order_number} with customer {customer_number}")
                
                # Track the order
                results = self.tracker.track_order(order_number, customer_number)
                
                # Check for error/mismatch first
                if results.get("error") == "Order/customer mismatch":
                    self.logger.info(f"❌ Mismatch: {order_number} with customer {customer_number}")
                    continue
                
                # Check if we got valid results
                if "error" not in results and results.get("tracking_info"):
                    # Extract order information
                    tracking_info = results.get("tracking_info", {})
                    
                    # Look for order status in the tracking info
                    for key, value in tracking_info.items():
                        if "order status" in key.lower() or "delivered" in value.lower():
                            order_result["status"] = "found"
                            order_result["matched_customer"] = customer_number
                            order_result["order_status"] = self.extract_order_status(value)
                            order_result["delivery_date"] = self.extract_delivery_date(value)
                            order_result["total_amount"] = self.extract_total_amount(value)
                            order_result["items"] = self.extract_items(value)
                            
                            self.logger.info(f"✅ MATCH FOUND: {order_number} with customer {customer_number}")
                            return order_result
                
                # If no match found, continue to next customer
                self.logger.info(f"❌ No match for {order_number} with customer {customer_number}")
                
            except Exception as e:
                self.logger.error(f"Error testing {order_number} with {customer_number}: {e}")
                order_result["error"] = str(e)
                continue
        
        # If we get here, no customer matched
        self.logger.warning(f"❌ No match found for order {order_number} after trying {len(customer_numbers)} customers")
        return order_result
    
    def extract_order_status(self, text):
        """Extract order status from tracking text"""
        if "delivered" in text.lower():
            return "Delivered"
        elif "in progress" in text.lower():
            return "In Progress"
        elif "ready to ship" in text.lower():
            return "Ready to Ship"
        else:
            return "Unknown"
    
    def extract_delivery_date(self, text):
        """Extract delivery date from tracking text"""
        import re
        date_pattern = r'(\w{3}\s+\d{1,2},\s+\d{4})'
        match = re.search(date_pattern, text)
        return match.group(1) if match else None
    
    def extract_total_amount(self, text):
        """Extract total amount from tracking text"""
        import re
        amount_pattern = r'AED\s+([\d,]+\.?\d*)'
        matches = re.findall(amount_pattern, text)
        return matches[-1] if matches else None
    
    def extract_items(self, text):
        """Extract items from tracking text"""
        items = []
        if "Home Wireless" in text:
            items.append("Home Wireless Plus")
        if "New Sim" in text:
            items.append("New Sim")
        return items
    
    def close(self):
        """Close the tracker"""
        if self.tracker:
            self.tracker.close()

def load_data_from_files():
    """Load order and customer numbers"""
    # Customer numbers
    customer_numbers = [
        "27722242", "06564007", "67630940", "54125200", "02124059", "55308497", "51937865", "56600354",
        "22767233", "02195850", "52061732", "49964116", "07044859", "57463568", "07086205", "44060166",
        "28668092", "25615795", "02205658", "67822022", "07421159", "85890583", "29825284", "06664647",
        "58161250", "00000000", "44732323", "89091031", "02880707", "51112422", "65727178", "58429866",
        "27757795", "43440885", "55573361", "67736939", "58740405", "01065173", "07543613", "24657490",
        "66382630", "08297176", "26924685", "09680762", "05707628", "56139964", "66447451", "44969503",
        "53929432", "09698036", "85839688", "85781027", "85877087", "66876784", "55961312", "61064474",
        "64466695", "55586115", "09430193", "07988535", "45660007", "06101119", "07302290", "57016655",
        "05892895", "68030843", "67607073", "56334115", "67181917", "07645763", "59167443", "06208544",
        "65340535", "52729759", "21318304", "05510075", "54539010", "28997693", "07882476", "28820304",
        "02618165", "24092557", "28227971", "03998877", "56726743", "01546512", "86760879", "44993038",
        "43559488", "04259170", "08956249", "81161796", "07717094", "06138291", "69369360", "59558998",
        "63871828", "68950063", "56736704", "68798683", "21131061", "51661745", "26535497", "57080106",
        "04765634", "63155227", "51674869", "21050867", "02077815", "62756674", "07130201", "56735764",
        "27902323", "08800626", "02501554", "05558063", "09045753", "68406128", "01793463", "50000000",
        "51620894", "51122792", "69520367", "03711199", "04700500", "27383881", "02469028", "45863240",
        "86799283", "62449454", "51236390", "52558559", "04546665", "03711938", "88665588", "45450619",
        "62217344", "09161078", "57553595", "44477754", "01524230", "52411593", "07784854", "02360476",
        "59390184", "57542348", "07924126", "56735508", "42968164", "58391410", "21662598", "51293905",
        "44851386", "07363701", "21901564", "54161242", "27423366", "29865202", "54241369", "22239387",
        "58676912", "08077688", "63311001", "67035302", "54882665", "63896909", "01187775", "86596799",
        "57110111", "65952736", "03326050", "64151756", "69302054", "69191993", "45838417", "64403376",
        "65659789", "68230021", "23181878", "59175026", "65208425", "57163811", "09145451", "09180655",
        "24967136", "42732830", "62525101", "88846346", "63989671", "27888347", "58527805", "06987286",
        "53540799", "44396957", "58134927"
    ]
    
    # Generate order numbers (CM0002153161 to CM0002155000)
    order_numbers = []
    for i in range(3161, 5001):
        order_numbers.append(f"CM000215{i}")
    
    return order_numbers, customer_numbers

def main():
    """Main function for Railway deployment"""
    print("🚀 Railway Fixed Batch Order Tracker Starting...")
    print("=" * 60)
    
    # Load data
    order_numbers, customer_numbers = load_data_from_files()
    
    print(f"📊 Data Loaded:")
    print(f"   • Order Numbers: {len(order_numbers):,}")
    print(f"   • Customer Numbers: {len(customer_numbers):,}")
    print(f"   • Total Combinations: {len(order_numbers) * len(customer_numbers):,}")
    print()
    
    # Initialize tracker
    tracker = RailwayBatchTracker(headless=True)
    
    try:
        print("🔄 Starting batch processing on Railway...")
        print("   • Using fixed ChromeDriver setup")
        print("   • Running in headless mode")
        print("   • Progress auto-saved")
        print()
        
        # Process first few orders as test
        test_orders = order_numbers[:5]  # Test with first 5 orders
        results = []
        
        for i, order_number in enumerate(test_orders, 1):
            print(f"Processing order {i}/{len(test_orders)}: {order_number}")
            order_result = tracker.process_single_order(order_number, customer_numbers)
            results.append(order_result)
            
            # Save progress
            with open('railway_results.json', 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"Order {order_number}: {order_result['status']}")
        
        # Print summary
        found_count = sum(1 for r in results if r["status"] == "found")
        not_found_count = sum(1 for r in results if r["status"] == "not_found")
        
        print(f"\n{'='*60}")
        print("🎉 RAILWAY BATCH PROCESSING COMPLETED!")
        print(f"{'='*60}")
        print(f"✅ Orders Found: {found_count}")
        print(f"❌ Orders Not Found: {not_found_count}")
        print(f"📊 Success Rate: {(found_count/len(results)*100):.1f}%")
        print(f"🔢 Total Attempts: {sum(r['attempts'] for r in results):,}")
        
        # Keep alive for Railway
        print("\n🔄 Process completed. Keeping alive...")
        time.sleep(3600)  # Keep alive for 1 hour
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logging.error(f"Railway processing error: {e}")
    finally:
        tracker.close()

if __name__ == "__main__":
    main()
