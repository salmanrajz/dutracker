#!/usr/bin/env python3
"""
Railway deployment version of the batch tracker
Optimized for cloud deployment with headless browser
"""

import os
import time
from robust_batch_tracker import RobustBatchTracker, load_data_from_files

def main():
    """Railway deployment main function"""
    print("🚀 Railway Batch Order Tracker Starting...")
    print("=" * 50)
    
    # Load data
    order_numbers, customer_numbers = load_data_from_files()
    
    print(f"📊 Data Loaded:")
    print(f"   • Order Numbers: {len(order_numbers):,}")
    print(f"   • Customer Numbers: {len(customer_numbers):,}")
    print(f"   • Total Combinations: {len(order_numbers) * len(customer_numbers):,}")
    print()
    
    # Initialize tracker with headless mode for cloud
    tracker = RobustBatchTracker(headless=True)
    
    try:
        print("🔄 Starting batch processing on Railway...")
        print("   • Running in headless mode")
        print("   • Progress auto-saved")
        print("   • Results saved to CSV")
        print()
        
        # Process the batch
        results = tracker.process_batch_with_resume(order_numbers, customer_numbers)
        
        # Print final summary
        found_count = sum(1 for r in results if r["status"] == "found")
        not_found_count = sum(1 for r in results if r["status"] == "not_found")
        
        print(f"\n{'='*60}")
        print("🎉 RAILWAY BATCH PROCESSING COMPLETED!")
        print(f"{'='*60}")
        print(f"✅ Orders Found: {found_count}")
        print(f"❌ Orders Not Found: {not_found_count}")
        print(f"📊 Success Rate: {(found_count/len(results)*100):.1f}%")
        print(f"🔢 Total Attempts: {sum(r['attempts'] for r in results):,}")
        print(f"📁 Results saved to: robust_batch_results.csv")
        
        # Keep the process alive for Railway
        print("\n🔄 Process completed. Keeping alive for file access...")
        time.sleep(3600)  # Keep alive for 1 hour
        
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted - progress saved!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Progress saved - you can resume later.")
    finally:
        tracker.close()

if __name__ == "__main__":
    main()
