#!/usr/bin/env python3
"""
Simple runner script for Du Order Tracker
"""

import json
import sys
from du_order_tracker import DuOrderTracker

def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: config.json not found. Using default settings.")
        return {
            "order_details": {
                "order_number": "CM0002233177",
                "mobile_number": "63275635"
            },
            "browser_settings": {
                "headless": False,
                "window_size": "1920,1080",
                "wait_timeout": 10
            }
        }

def main():
    """Main runner function"""
    print("Du Order Tracker")
    print("================")
    
    # Load configuration
    config = load_config()
    
    # Extract settings
    order_number = config["order_details"]["order_number"]
    mobile_number = config["order_details"]["mobile_number"]
    headless = config["browser_settings"]["headless"]
    
    print(f"Order Number: {order_number}")
    print(f"Mobile Number: {mobile_number}")
    print(f"Headless Mode: {headless}")
    print()
    
    # Initialize tracker
    tracker = DuOrderTracker(headless=headless)
    
    try:
        print("Starting order tracking...")
        results = tracker.track_order(order_number, mobile_number)
        
        # Save results
        filename = tracker.save_results(results)
        
        # Display results
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
            sys.exit(1)
        
        print("\nOrder tracking completed successfully!")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
    finally:
        tracker.close()

if __name__ == "__main__":
    main()
