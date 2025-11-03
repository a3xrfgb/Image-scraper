import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Ask user for search keyword
search_keyword = input("Enter the search keyword to scrape from Google Images: ").strip()

# Create a folder with the same name
folder_name = search_keyword.replace(" ", "_")
if not os.path.isdir(folder_name):
    os.makedirs(folder_name)

def download_image(url, folder_name, num):
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

# Initialize Chrome
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

print("Opening browser and loading images...")
driver.get(search_URL)
time.sleep(3)

# Scroll down multiple times to load images
for _ in range(5):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

# Find all image thumbnails
thumbnails = driver.find_elements(By.CSS_SELECTOR, "img.rg_i")

if not thumbnails:
    print("No thumbnails found. Trying alternative selector...")
    thumbnails = driver.find_elements(By.CSS_SELECTOR, "img.YQ4gaf")

print(f"Found {len(thumbnails)} thumbnails. Fetching full-resolution images...")

count = 0
for idx, thumbnail in enumerate(thumbnails[:50]):  # Limit to 50 images
    try:
        # Scroll thumbnail into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thumbnail)
        time.sleep(0.5)
        
        # Click thumbnail
        thumbnail.click()
        time.sleep(2)
        
        # Method 1: Try to find the full-size image in the preview panel
        try:
            # Look for images in the side panel
            full_image = driver.find_element(By.CSS_SELECTOR, "img.sFlh5c.pT0Scc.iPVvYb")
            src = full_image.get_attribute("src")
            
            if src and src.startswith("http") and "encrypted-tbn0" not in src:
                if download_image(src, folder_name, count + 1):
                    count += 1
                    print(f"Downloaded image {count}")
                    continue
        except NoSuchElementException:
            pass
        
        # Method 2: Try alternative selectors
        try:
            images = driver.find_elements(By.CSS_SELECTOR, "img[src^='http']")
            for img in images:
                src = img.get_attribute("src")
                if src and src.startswith("http") and "encrypted-tbn0" not in src and "gstatic" not in src:
                    if download_image(src, folder_name, count + 1):
                        count += 1
                        print(f"Downloaded image {count}")
                        break
        except Exception:
            pass
            
    except (ElementClickInterceptedException, ElementNotInteractableException):
        continue
    except Exception as e:
        print(f"Error processing thumbnail {idx}: {e}")
        continue

print(f"✅ Done! {count} full-resolution images downloaded into '{folder_name}'")
driver.quit()
