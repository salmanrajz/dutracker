#!/usr/bin/env python3
"""
Batch Order Tracker for Du.ae
Processes multiple order numbers against multiple customer numbers
"""

import csv
import json
import time
import logging
from datetime import datetime
from du_order_tracker import DuOrderTracker

class BatchOrderTracker:
    def __init__(self, headless=True):
        """
        Initialize the Batch Order Tracker
        
        Args:
            headless (bool): Run browser in headless mode
        """
        self.tracker = None
        self.setup_logging()
        self.setup_tracker(headless)
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('batch_tracker.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_tracker(self, headless=True):
        """Setup the order tracker"""
        try:
            self.tracker = DuOrderTracker(headless=headless)
            self.logger.info("Batch Order Tracker initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize tracker: {e}")
            raise
    
    def process_batch(self, order_numbers, customer_numbers, output_csv="batch_results.csv"):
        """
        Process batch of order numbers against customer numbers
        
        Args:
            order_numbers (list): List of order numbers to test
            customer_numbers (list): List of customer numbers to test against
            output_csv (str): Output CSV filename
        """
        results = []
        total_orders = len(order_numbers)
        total_customers = len(customer_numbers)
        
        self.logger.info(f"Starting batch processing: {total_orders} orders × {total_customers} customers")
        
        for i, order_number in enumerate(order_numbers, 1):
            self.logger.info(f"Processing order {i}/{total_orders}: {order_number}")
            order_result = self.process_single_order(order_number, customer_numbers)
            results.append(order_result)
            
            # Save progress after each order
            self.save_progress_csv(results, f"progress_{output_csv}")
            
            # Small delay between orders
            time.sleep(2)
        
        # Save final results
        self.save_final_csv(results, output_csv)
        self.logger.info(f"Batch processing completed. Results saved to {output_csv}")
        
        return results
    
    def process_single_order(self, order_number, customer_numbers):
        """
        Process a single order against all customer numbers
        
        Args:
            order_number (str): Order number to test
            customer_numbers (list): List of customer numbers to test
            
        Returns:
            dict: Result for this order
        """
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
                
                # Check if we got valid results (not an error)
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
        # Look for date patterns like "Feb 01, 2025"
        date_pattern = r'(\w{3}\s+\d{1,2},\s+\d{4})'
        match = re.search(date_pattern, text)
        return match.group(1) if match else None
    
    def extract_total_amount(self, text):
        """Extract total amount from tracking text"""
        import re
        # Look for AED amounts
        amount_pattern = r'AED\s+([\d,]+\.?\d*)'
        matches = re.findall(amount_pattern, text)
        return matches[-1] if matches else None
    
    def extract_items(self, text):
        """Extract items from tracking text"""
        # Simple extraction - look for item names
        items = []
        if "Home Wireless" in text:
            items.append("Home Wireless Plus")
        if "New Sim" in text:
            items.append("New Sim")
        return items
    
    def save_progress_csv(self, results, filename):
        """Save progress to CSV file"""
        self.save_to_csv(results, filename)
    
    def save_final_csv(self, results, filename):
        """Save final results to CSV file"""
        self.save_to_csv(results, filename)
    
    def save_to_csv(self, results, filename):
        """Save results to CSV file"""
        if not results:
            return
        
        fieldnames = [
            "order_number", "status", "matched_customer", "order_status", 
            "delivery_date", "total_amount", "items", "attempts", "error", "timestamp"
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                # Convert items list to string for CSV
                if result.get("items"):
                    result["items"] = ", ".join(result["items"])
                
                writer.writerow(result)
        
        self.logger.info(f"Results saved to CSV: {filename}")
    
    def close(self):
        """Close the tracker"""
        if self.tracker:
            self.tracker.close()

def main():
    """Main function for batch processing"""
    
    # Example data - replace with your actual data
    order_numbers = [
        "CM0002233177",
        "CM0002680507",
        # Add more order numbers here
    ]
    
    customer_numbers = [
        "63275635",
        "0561716359",
        "971561716359",
        # Add more customer numbers here
    ]
    
    # Initialize batch tracker
    batch_tracker = BatchOrderTracker(headless=False)
    
    try:
        # Process the batch
        results = batch_tracker.process_batch(order_numbers, customer_numbers)
        
        # Print summary
        found_count = sum(1 for r in results if r["status"] == "found")
        not_found_count = sum(1 for r in results if r["status"] == "not_found")
        
        print(f"\n{'='*50}")
        print("BATCH PROCESSING SUMMARY")
        print(f"{'='*50}")
        print(f"Total Orders Processed: {len(results)}")
        print(f"Orders Found: {found_count}")
        print(f"Orders Not Found: {not_found_count}")
        print(f"Success Rate: {(found_count/len(results)*100):.1f}%")
        
    except Exception as e:
        print(f"Error in batch processing: {e}")
        logging.error(f"Batch processing error: {e}")
    
    finally:
        batch_tracker.close()

if __name__ == "__main__":
    main()
