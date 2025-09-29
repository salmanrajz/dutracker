#!/usr/bin/env python3
"""
Convert JSON tracking results to CSV format
"""

import json
import csv
import os
from datetime import datetime

def convert_json_to_csv(json_file, csv_file=None):
    """
    Convert JSON tracking results to CSV format
    
    Args:
        json_file (str): Path to JSON file
        csv_file (str): Output CSV file path (optional)
    """
    if not csv_file:
        csv_file = json_file.replace('.json', '.csv')
    
    # Read JSON file
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract tracking information
    tracking_info = data.get('tracking_info', {})
    
    # Create CSV data
    csv_data = []
    
    for key, value in tracking_info.items():
        # Parse the tracking information
        if "order status" in key.lower() or "delivered" in value.lower():
            # Extract order details
            order_status = extract_order_status(value)
            delivery_date = extract_delivery_date(value)
            total_amount = extract_total_amount(value)
            items = extract_items(value)
            order_number = extract_order_number(value)
            
            csv_data.append({
                'order_number': order_number,
                'order_status': order_status,
                'delivery_date': delivery_date,
                'total_amount': total_amount,
                'items': items,
                'raw_data': value,
                'timestamp': data.get('timestamp', datetime.now().isoformat())
            })
    
    # Write to CSV
    if csv_data:
        fieldnames = ['order_number', 'order_status', 'delivery_date', 'total_amount', 'items', 'raw_data', 'timestamp']
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        
        print(f"✅ Converted {len(csv_data)} records to CSV: {csv_file}")
    else:
        print("❌ No tracking data found to convert")

def extract_order_status(text):
    """Extract order status from text"""
    if "delivered" in text.lower():
        return "Delivered"
    elif "in progress" in text.lower():
        return "In Progress"
    elif "ready to ship" in text.lower():
        return "Ready to Ship"
    else:
        return "Unknown"

def extract_delivery_date(text):
    """Extract delivery date from text"""
    import re
    # Look for date patterns like "Feb 01, 2025"
    date_pattern = r'(\w{3}\s+\d{1,2},\s+\d{4})'
    match = re.search(date_pattern, text)
    return match.group(1) if match else None

def extract_total_amount(text):
    """Extract total amount from text"""
    import re
    # Look for AED amounts
    amount_pattern = r'AED\s+([\d,]+\.?\d*)'
    matches = re.findall(amount_pattern, text)
    return matches[-1] if matches else None

def extract_items(text):
    """Extract items from text"""
    items = []
    if "Home Wireless" in text:
        items.append("Home Wireless Plus")
    if "New Sim" in text:
        items.append("New Sim")
    return ", ".join(items)

def extract_order_number(text):
    """Extract order number from text"""
    import re
    # Look for CM numbers
    order_pattern = r'CM\d+'
    match = re.search(order_pattern, text)
    return match.group(0) if match else None

def main():
    """Convert all JSON files in current directory to CSV"""
    json_files = [f for f in os.listdir('.') if f.startswith('order_tracking_') and f.endswith('.json')]
    
    if not json_files:
        print("No JSON files found to convert")
        return
    
    for json_file in json_files:
        print(f"Converting {json_file}...")
        convert_json_to_csv(json_file)

if __name__ == "__main__":
    main()
