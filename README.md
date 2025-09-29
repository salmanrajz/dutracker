# Du Order Tracker

A Python-based automation tool to track orders on the du.ae website using Selenium WebDriver.

## Features

- Automated order tracking on du.ae website
- Screenshot capture for reference
- JSON results export
- Comprehensive logging
- Configurable settings
- Error handling and recovery

## Prerequisites

- Python 3.7 or higher
- Chrome browser installed
- ChromeDriver (automatically managed by the script)

## Installation

1. Clone or download this repository
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the script with default settings:

```bash
python du_order_tracker.py
```

This will use the order details from the script:
- Order Number: CM0002680507
- Mobile Number: 0561716359

### Configuration

Edit `config.json` to customize settings:

```json
{
  "order_details": {
    "order_number": "CM0002680507",
    "mobile_number": "0561716359"
  },
  "browser_settings": {
    "headless": false,
    "window_size": "1920,1080",
    "wait_timeout": 10
  },
  "output_settings": {
    "save_screenshots": true,
    "save_results": true,
    "log_level": "INFO"
  }
}
```

### Programmatic Usage

```python
from du_order_tracker import DuOrderTracker

# Initialize tracker
tracker = DuOrderTracker(headless=True)

# Track order
results = tracker.track_order("CM0002680507", "0561716359")

# Save results
tracker.save_results(results, "my_order_results.json")

# Close browser
tracker.close()
```

## Output

The script generates:

1. **Console Output**: Real-time tracking information
2. **Screenshots**: PNG files of the tracking results page
3. **JSON Results**: Detailed tracking information in JSON format
4. **Log Files**: Comprehensive logging in `du_tracker.log`

### Sample Output

```
==================================================
ORDER TRACKING RESULTS
==================================================
Order Number: CM0002680507
Mobile Number: 0561716359
Timestamp: 2024-01-15 14:30:25
Order Status: Processing

Tracking Information:
  status: Your order is being processed
  estimated_delivery: 2-3 business days

Screenshot saved: order_tracking_1705320625.png

Full results saved to: order_tracking_20240115_143025.json
```

## File Structure

```
dutracker/
├── du_order_tracker.py    # Main tracking script
├── requirements.txt       # Python dependencies
├── config.json           # Configuration settings
├── README.md             # This file
├── du_tracker.log        # Log file (generated)
└── order_tracking_*.json # Results files (generated)
└── order_tracking_*.png  # Screenshot files (generated)
```

## Troubleshooting

### Common Issues

1. **ChromeDriver Issues**: The script automatically manages ChromeDriver, but if you encounter issues, ensure Chrome browser is installed.

2. **Element Not Found**: The website structure might change. The script includes fallback selectors, but you may need to update the selectors.

3. **Timeout Errors**: Increase the `wait_timeout` in config.json if the website is slow to load.

### Debug Mode

Run with headless=False to see the browser in action:

```python
tracker = DuOrderTracker(headless=False)
```

## Logging

The script creates detailed logs in `du_tracker.log` including:
- Navigation steps
- Element interactions
- Error messages
- Success confirmations

## Error Handling

The script includes comprehensive error handling for:
- Network timeouts
- Element not found errors
- Browser crashes
- Invalid order numbers

## Security Notes

- The script does not store or transmit your personal information
- All data is processed locally
- Screenshots and logs are saved locally only

## License

This project is for educational and personal use only. Please respect the du.ae website's terms of service.

## Contributing

Feel free to submit issues and enhancement requests!

## Support

For issues or questions, please check the logs in `du_tracker.log` for detailed error information.
# dutracker
