import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager

# Ask user for search keyword
search_keyword = input("Enter the search keyword to scrape from Google Images: ").strip()

# Create a folder with the same name
folder_name = search_keyword.replace(" ", "_")
if not os.path.isdir(folder_name):
    os.makedirs(folder_name)

def download_image(url, folder_name, num):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(os.path.join(folder_name, f"{num}.jpg"), "wb") as file:
                file.write(response.content)
    except Exception as e:
        print(f"Error downloading image {num}: {e}")

# Build URL
search_URL = f"https://www.google.com/search?q={search_keyword}&tbm=isch"

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize Chrome
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

print("Opening browser and loading images...")
driver.get(search_URL)
time.sleep(3)

# Scroll down multiple times to load images
for _ in range(4):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

# --- FIX: Use robust XPath for thumbnails ---
thumbnails = driver.find_elements(
    By.XPATH, '//img[contains(@src, "gstatic.com") and contains(@src, "encrypted-tbn0")]'
)

print(f"Found {len(thumbnails)} thumbnails. Fetching full-resolution images...")

count = 0
for idx, thumbnail in enumerate(thumbnails):
    try:
        driver.execute_script("arguments[0].scrollIntoView();", thumbnail)
        time.sleep(0.3)
        thumbnail.click()
        time.sleep(1.5)
    except (ElementClickInterceptedException, ElementNotInteractableException):
        continue
    except Exception:
        continue

    # Look for actual full-size image that appears after clicking
    actual_images = driver.find_elements(By.XPATH, '//img[contains(@src, "https://") and not(contains(@src, "encrypted-tbn0"))]')
    for img in actual_images:
        src = img.get_attribute("src")
        if src and src.startswith("https://") and not src.startswith("data:image"):
            count += 1
            download_image(src, folder_name, count)
            print(f"Downloaded image {count}")
            break

print(f"✅ Done! {count} full-resolution images downloaded into '{folder_name}'")
driver.quit()
