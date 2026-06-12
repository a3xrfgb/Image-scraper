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

# Ask user for search keyword
search_keyword = input("Enter the search keyword to scrape images from Getty Images and Alamy: ").strip()

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
                with open(os.path.join(folder_name, f"{num}.jpg"), "wb") as file:
                    file.write(response.content)
                downloaded_urls.add(url)  # Mark as downloaded
                return True
    except Exception as e:
        print(f"Error downloading image {num}: {e}")
    return False

# Build URLs
getty_url = f"https://www.gettyimages.com/photos/{search_keyword.replace(' ', '-')}"
alamy_url = f"https://www.alamy.com/search.html?qt={search_keyword}"

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

# Open Getty in main tab
driver.get(getty_url)
time.sleep(3)

# Open new tab for Alamy
driver.execute_script("window.open('');")
getty_window = driver.window_handles[0]
alamy_window = driver.window_handles[1]

# Load Alamy
driver.switch_to.window(alamy_window)
driver.get(alamy_url)
time.sleep(3)

# Process Getty Images
driver.switch_to.window(getty_window)
print("Fetching full-resolution images from Getty Images...")
count = 0
idx = 0

try:
    while True:
        # Re-find thumbnails
        thumbnails = driver.find_elements(By.CSS_SELECTOR, "img[src^='https://media.gettyimages.com']")
        
        if idx >= len(thumbnails):
            print("\nReached end of available images on Getty. Scrolling for more...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            # Try to load more if button exists (adjust selector if needed)
            try:
                load_more = driver.find_element(By.CSS_SELECTOR, "button[data-testid='load-more-button']")
                load_more.click()
                time.sleep(3)
            except:
                pass
            idx = 0
            continue
        
        thumbnail = thumbnails[idx]
        idx += 1
        
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thumbnail)
            time.sleep(0.5)
            thumbnail.click()
            time.sleep(2)
            
            # Now on detail page, find full image (adjust selector as needed)
            try:
                full_image = driver.find_element(By.CSS_SELECTOR, "img[src^='https://media.gettyimages.com'][src*='s=2048x2048']")  # Aim for high res
                src = full_image.get_attribute("src")
            except:
                # Fallback: find largest img
                images = driver.find_elements(By.CSS_SELECTOR, "img[src^='https://media.gettyimages.com']")
                src = None
                for img in images:
                    try:
                        if 'thumb' not in img.get_attribute("src"):
                            src = img.get_attribute("src")
                            break
                    except:
                        continue
            
            if src and src.startswith("http"):
                if download_image(src, folder_name, count + 1):
                    count += 1
                    print(f"Downloaded image {count} from Getty")
            
            # Go back to search page
            driver.back()
            time.sleep(2)
        
        except Exception as e:
            print(f"Error processing Getty thumbnail {idx}: {e}")
            continue

except KeyboardInterrupt:
    print("\nStopped processing Getty.")

# Now process Alamy
driver.switch_to.window(alamy_window)
print("\nFetching full-resolution images from Alamy...")
idx = 0  # Reset index

try:
    while True:
        # Re-find thumbnails (Alamy often uses data-src for lazy load)
        thumbnails = driver.find_elements(By.CSS_SELECTOR, "img[data-src^='https://c.alamy.com']")
        if not thumbnails:
            thumbnails = driver.find_elements(By.CSS_SELECTOR, "img[src^='https://c.alamy.com']")
        
        if idx >= len(thumbnails):
            print("\nReached end of available images on Alamy. Scrolling for more...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            # Alamy may have load more button (adjust selector)
            try:
                load_more = driver.find_element(By.CSS_SELECTOR, ".load-more-button")  # Hypothetical, adjust if needed
                load_more.click()
                time.sleep(3)
            except:
                pass
            idx = 0
            continue
        
        thumbnail = thumbnails[idx]
        idx += 1
        
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thumbnail)
            time.sleep(0.5)
            thumbnail.click()
            time.sleep(2)
            
            # On detail page, find preview image
            try:
                full_image = driver.find_element(By.ID, "preview")
                src = full_image.get_attribute("src")
            except:
                # Fallback
                images = driver.find_elements(By.CSS_SELECTOR, "img[src^='https://c.alamy.com']")
                src = None
                for img in images:
                    try:
                        if 'thumb' not in img.get_attribute("src") and 'comp' not in img.get_attribute("src"):
                            src = img.get_attribute("src")
                            break
                    except:
                        continue
            
            if src and src.startswith("http"):
                if download_image(src, folder_name, count + 1):
                    count += 1
                    print(f"Downloaded image {count} from Alamy")
            
            # Go back
            driver.back()
            time.sleep(2)
        
        except Exception as e:
            print(f"Error processing Alamy thumbnail {idx}: {e}")
            continue

except KeyboardInterrupt:
    print("\n\n🛑 Download stopped by user!")

# Final cleanup
driver.quit()

print(f"\n✅ Done! {count} full-resolution images downloaded into '{folder_name}'")