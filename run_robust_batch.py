#!/usr/bin/env python3
"""
Run the robust batch tracker with your actual data
"""

from robust_batch_tracker import RobustBatchTracker, load_data_from_files

def main():
    """Run the robust batch processing"""
    print("🚀 Starting Robust Batch Order Tracker")
    print("=" * 50)
    
    # Load your actual data
    order_numbers, customer_numbers = load_data_from_files()
    
    print(f"📊 Data Loaded:")
    print(f"   • Order Numbers: {len(order_numbers):,}")
    print(f"   • Customer Numbers: {len(customer_numbers):,}")
    print(f"   • Total Combinations: {len(order_numbers) * len(customer_numbers):,}")
    print()
    
    # Initialize tracker
    tracker = RobustBatchTracker(headless=False)
    
    try:
        print("🔄 Starting batch processing...")
        print("   • Progress will be saved automatically")
        print("   • You can stop and resume anytime")
        print("   • Results saved to CSV after each order")
        print()
        
        # Process the batch
        results = tracker.process_batch_with_resume(order_numbers, customer_numbers)
        
        # Print final summary
        found_count = sum(1 for r in results if r["status"] == "found")
        not_found_count = sum(1 for r in results if r["status"] == "not_found")
        
        print(f"\n{'='*60}")
        print("🎉 BATCH PROCESSING COMPLETED!")
        print(f"{'='*60}")
        print(f"✅ Orders Found: {found_count}")
        print(f"❌ Orders Not Found: {not_found_count}")
        print(f"📊 Success Rate: {(found_count/len(results)*100):.1f}%")
        print(f"🔢 Total Attempts: {sum(r['attempts'] for r in results):,}")
        print(f"📁 Results saved to: robust_batch_results.csv")
        
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted - progress saved!")
        print("   Run the script again to resume from where you left off.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Progress saved - you can resume later.")
    finally:
        tracker.close()

if __name__ == "__main__":
    main()
