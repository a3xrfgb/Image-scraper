import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    ElementClickInterceptedException, 
    ElementNotInteractableException, 
    NoSuchElementException,
    StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager
from io import BytesIO
from PIL import Image

# Ask user for search keyword
search_keyword = input("Enter the search keyword to scrape from Google Images: ").strip()

# Create a folder with the same name
folder_name = search_keyword.replace(" ", "_")
if not os.path.isdir(folder_name):
    os.makedirs(folder_name)

downloaded_urls = set()  # Track downloaded URLs to avoid duplicates

def download_image(url, folder_name, num):
    # Skip if already downloaded
    if url in downloaded_urls:
        print(f"Skipping duplicate image: {num}")
        return False
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        if response.status_code == 200:
            # Check if the content is actually an image
            content_type = response.headers.get('content-type', '')
            if 'image' in content_type:
                img_data = response.content
                try:
                    img = Image.open(BytesIO(img_data))
                    width, height = img.size
                    if min(width, height) < 1024:
                        print(f"Skipping image {num}: resolution {width}x{height} too low (must be at least 1k in both dimensions)")
                        return False
                except Exception as e:
                    print(f"Could not determine resolution for image {num}: {e}")
                    return False
                
                with open(os.path.join(folder_name, f"{num}.jpg"), "wb") as file:
                    file.write(img_data)
                downloaded_urls.add(url)  # Mark as downloaded
                return True
    except Exception as e:
        print(f"Error downloading image {num}: {e}")
    return False

# Build URL
search_URL = f"https://www.google.com/search?q={search_keyword}&tbm=isch"

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-popup-blocking")

# Initialize Chrome
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

print("Opening browser and loading images...")
driver.get(search_URL)
time.sleep(3)

# Store the main window handle
main_window = driver.current_window_handle

# Scroll down multiple times to load images
for _ in range(5):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

print("Fetching full-resolution images...")
print("Press Ctrl+C to stop downloading at any time.\n")

count = 0
idx = 0

try:
    while True:  # Run indefinitely until user stops
        try:
            # Make sure we're on the main window
            if driver.current_window_handle != main_window:
                driver.switch_to.window(main_window)
            
            # Close any extra tabs that might have opened
            if len(driver.window_handles) > 1:
                for handle in driver.window_handles:
                    if handle != main_window:
                        driver.switch_to.window(handle)
                        driver.close()
                driver.switch_to.window(main_window)
            
            # Re-find thumbnails each iteration to avoid stale elements
            thumbnails = driver.find_elements(By.CSS_SELECTOR, "img.rg_i")
            
            if not thumbnails:
                thumbnails = driver.find_elements(By.CSS_SELECTOR, "img.YQ4gaf")
            
            # Break if we've processed all available thumbnails
            if idx >= len(thumbnails):
                print("\nReached end of available images. Scrolling for more...")
                # Scroll down more to load additional images
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Try to click "Show more results" button if it exists
                try:
                    show_more = driver.find_element(By.CSS_SELECTOR, "input.mye4qd")
                    show_more.click()
                    time.sleep(3)
                    print("Loaded more images...")
                except:
                    pass
                
                # Reset to continue with newly loaded images
                idx = len(thumbnails) - 10 if len(thumbnails) > 10 else 0
                continue
            
            thumbnail = thumbnails[idx]
            idx += 1
            
            try:
                # Scroll thumbnail into view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thumbnail)
                time.sleep(0.5)
                
                # Click thumbnail to open preview
                thumbnail.click()
                time.sleep(2)
                
            except (ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException):
                continue
            
            # Method 1: Try to find the full-size image in the preview panel
            try:
                full_image = driver.find_element(By.CSS_SELECTOR, "img.sFlh5c.pT0Scc.iPVvYb")
                src = full_image.get_attribute("src")
                
                if src and src.startswith("http") and "encrypted-tbn0" not in src:
                    if download_image(src, folder_name, count + 1):
                        count += 1
                        print(f"Downloaded image {count}")
                        continue
            except (NoSuchElementException, StaleElementReferenceException):
                pass
            
            # Method 2: Try alternative selectors for the preview image
            try:
                images = driver.find_elements(By.CSS_SELECTOR, "img[src^='http']")
                for img in images:
                    try:
                        src = img.get_attribute("src")
                        # Filter out thumbnails and Google's own images
                        if (src and src.startswith("http") and 
                            "encrypted-tbn0" not in src and 
                            "gstatic" not in src and
                            "google.com/images" not in src):
                            
                            if download_image(src, folder_name, count + 1):
                                count += 1
                                print(f"Downloaded image {count}")
                                break
                    except StaleElementReferenceException:
                        continue
            except Exception as e:
                print(f"Error processing thumbnail {idx}: {e}")
                continue
                
        except StaleElementReferenceException:
            print(f"Stale element at index {idx}, retrying...")
            continue
        except Exception as e:
            print(f"Error processing thumbnail {idx}: {e}")
            continue

except KeyboardInterrupt:
    print("\n\n🛑 Download stopped by user!")

# Final cleanup: close any extra windows
if len(driver.window_handles) > 1:
    for handle in driver.window_handles:
        if handle != main_window:
            driver.switch_to.window(handle)
            driver.close()
    driver.switch_to.window(main_window)

print(f"\n✅ Done! {count} full-resolution images downloaded into '{folder_name}'")
print(f"📊 Processed {idx} thumbnails total")
driver.quit()