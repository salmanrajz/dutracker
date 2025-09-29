#!/usr/bin/env python3
"""
Robust Batch Order Tracker with Resume Capability
Processes 2,500 order numbers against 300 customer numbers
Can resume from where it left off if interrupted
"""

import csv
import json
import time
import logging
import os
from datetime import datetime
from du_order_tracker import DuOrderTracker

class RobustBatchTracker:
    def __init__(self, headless=True, resume_file="batch_progress.json"):
        """
        Initialize the Robust Batch Tracker
        
        Args:
            headless (bool): Run browser in headless mode
            resume_file (str): File to save progress for resuming
        """
        self.tracker = None
        self.resume_file = resume_file
        self.setup_logging()
        self.setup_tracker(headless)
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('robust_batch_tracker.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_tracker(self, headless=True):
        """Setup the order tracker"""
        try:
            self.tracker = DuOrderTracker(headless=headless)
            self.logger.info("Robust Batch Tracker initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize tracker: {e}")
            raise
    
    def load_progress(self):
        """Load progress from resume file"""
        if os.path.exists(self.resume_file):
            try:
                with open(self.resume_file, 'r') as f:
                    progress = json.load(f)
                self.logger.info(f"Loaded progress: {progress['completed_orders']} orders completed")
                return progress
            except Exception as e:
                self.logger.error(f"Error loading progress: {e}")
                return None
        return None
    
    def save_progress(self, progress):
        """Save progress to resume file"""
        try:
            with open(self.resume_file, 'w') as f:
                json.dump(progress, f, indent=2)
            self.logger.info(f"Progress saved: {progress['completed_orders']} orders completed")
        except Exception as e:
            self.logger.error(f"Error saving progress: {e}")
    
    def process_batch_with_resume(self, order_numbers, customer_numbers, output_csv="robust_batch_results.csv"):
        """
        Process batch with resume capability
        
        Args:
            order_numbers (list): List of order numbers to test
            customer_numbers (list): List of customer numbers to test against
            output_csv (str): Output CSV filename
        """
        # Load existing progress
        progress = self.load_progress()
        
        if progress:
            completed_orders = set(progress['completed_orders'])
            results = progress.get('results', [])
            start_index = progress.get('last_processed_index', 0)
            self.logger.info(f"Resuming from order {start_index + 1}")
        else:
            completed_orders = set()
            results = []
            start_index = 0
            self.logger.info("Starting fresh batch processing")
        
        total_orders = len(order_numbers)
        total_customers = len(customer_numbers)
        
        self.logger.info(f"Processing {total_orders} orders × {total_customers} customers")
        
        for i in range(start_index, total_orders):
            order_number = order_numbers[i]
            
            # Skip if already completed
            if order_number in completed_orders:
                self.logger.info(f"Skipping already completed order: {order_number}")
                continue
            
            self.logger.info(f"Processing order {i+1}/{total_orders}: {order_number}")
            
            try:
                order_result = self.process_single_order(order_number, customer_numbers)
                results.append(order_result)
                completed_orders.add(order_number)
                
                # Save progress after each order
                progress_data = {
                    'completed_orders': list(completed_orders),
                    'results': results,
                    'last_processed_index': i,
                    'timestamp': datetime.now().isoformat()
                }
                self.save_progress(progress_data)
                
                # Save CSV after each order
                self.save_results_csv(results, f"progress_{output_csv}")
                
                # Small delay between orders
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error processing order {order_number}: {e}")
                # Continue with next order even if one fails
                continue
        
        # Save final results
        self.save_results_csv(results, output_csv)
        self.logger.info(f"Batch processing completed. Results saved to {output_csv}")
        
        # Clean up progress file
        if os.path.exists(self.resume_file):
            os.remove(self.resume_file)
            self.logger.info("Progress file cleaned up")
        
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
                
                # Check for error/mismatch first
                if results.get("error") == "Order/customer mismatch":
                    self.logger.info(f"❌ Mismatch: {order_number} with customer {customer_number}")
                    continue
                
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
    
    def save_results_csv(self, results, filename):
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

def load_data_from_files():
    """Load order and customer numbers from files"""
    # Load customer numbers
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
    """Main function for robust batch processing"""
    
    # Load data
    order_numbers, customer_numbers = load_data_from_files()
    
    print(f"Loaded {len(order_numbers)} order numbers")
    print(f"Loaded {len(customer_numbers)} customer numbers")
    print(f"Total combinations to test: {len(order_numbers)} × {len(customer_numbers)} = {len(order_numbers) * len(customer_numbers):,}")
    
    # Initialize robust batch tracker
    batch_tracker = RobustBatchTracker(headless=False)
    
    try:
        # Process the batch with resume capability
        results = batch_tracker.process_batch_with_resume(order_numbers, customer_numbers)
        
        # Print summary
        found_count = sum(1 for r in results if r["status"] == "found")
        not_found_count = sum(1 for r in results if r["status"] == "not_found")
        
        print(f"\n{'='*60}")
        print("ROBUST BATCH PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"Total Orders Processed: {len(results)}")
        print(f"Orders Found: {found_count}")
        print(f"Orders Not Found: {not_found_count}")
        print(f"Success Rate: {(found_count/len(results)*100):.1f}%")
        print(f"Total Attempts: {sum(r['attempts'] for r in results):,}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user. Progress saved - you can resume later.")
        logging.info("Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Error in batch processing: {e}")
        logging.error(f"Batch processing error: {e}")
        print("Progress saved - you can resume later.")
    
    finally:
        batch_tracker.close()

if __name__ == "__main__":
    main()
