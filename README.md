# Google Images Scraper
Use proxies by anymean while scapping the web!

- Get Proxy here -------> [Smart Proxies](https://stormproxies.com/discount.html)

- Get Chrome WebDriver Download------> [ChromeWebDriver Link](https://googlechromelabs.github.io/chrome-for-testing/#stable)
  
- Note: Make sure your Google chrome browser version matches the Chrome WebDriver.
(otherwise it wont work)

A Python script that automatically downloads high-resolution images from Google Images based on a search keyword.

## Features

✨ **High-Resolution Downloads** - Fetches full-size images, not thumbnails  
🚫 **No Duplicates** - Automatically skips already downloaded images  
📁 **Auto-Organize** - Creates folders based on search keywords  
🔄 **Single Tab Operation** - Stays on one tab without opening multiple windows  
⚡ **Smart Error Handling** - Handles stale elements and connection issues gracefully

## Prerequisites

- Python 3.7 or higher
- Chrome browser installed on your system
- Internet connection

## Installation

1. Clone this repository:
```bash
git clone https://github.com/agxagi/google-images-scraper.git
cd google-images-scraper
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the script:
```bash
python google-images-scraper.py
```

2. Enter your search keyword when prompted:
```
Enter the search keyword to scrape from Google Images: cats playing piano
```

3. The script will:
   - Open Chrome browser automatically
   - Navigate to Google Images
   - Load and scroll through images
   - Download images untill browser stopped by user
   - Save them in a folder named after your search keyword

## Output

Images are saved in a folder named after your search keyword (spaces replaced with underscores):
```
cats_playing_piano/
├── 1.jpg
├── 2.jpg
├── 3.jpg
└── ...
```

## Configuration

You can modify these settings in the script:

- **Maximum images**: Change `max_images = 50` to your desired number
- **Scroll depth**: Adjust the range in the scroll loop (currently `range(5)`)
- **Wait times**: Modify `time.sleep()` values for slower/faster execution

## Dependencies

- **selenium**: Browser automation
- **webdriver-manager**: Automatic ChromeDriver management
- **requests**: HTTP library for downloading images

## Troubleshooting

### Chrome driver issues
The script uses `webdriver-manager` to automatically download and manage ChromeDriver. If you encounter issues, make sure Chrome browser is up to date.

### No images downloaded
- Check your internet connection
- Try a different search keyword
- Google may have changed their HTML structure (selectors may need updating)

### Slow performance
- Reduce the number of scroll iterations
- Decrease `time.sleep()` values (may cause missed images)
- Limit `max_images` to a smaller number

## Legal Notice

⚠️ **Important**: This tool is for educational purposes only. When scraping images:

- Respect copyright and intellectual property rights
- Check Google's Terms of Service
- Only use images you have the right to use
- Consider using images with appropriate licenses (Creative Commons, etc.)
- For commercial use, always obtain proper permissions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is provided as-is without any warranties. The authors are not responsible for any misuse of this tool or violations of terms of service. Use responsibly and ethically.
