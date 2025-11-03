import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# --- Step 1: User Inputs ---
chrome_path = input("Enter the full path to your ChromeDriver (e.g., /Users/yourname/chromedriver): ").strip()
keyword = input("Enter the search keyword (e.g., 'Albert Einstein'): ").strip()

# Automatically create folder for keyword
download_path = os.path.join(os.getcwd(), keyword.replace(" ", "_"))
os.makedirs(download_path, exist_ok=True)
print(f"\n📂 Images will be saved in: {download_path}")

# --- Step 2: Setup Chrome (headless optional) ---
chrome_options = Options()
chrome_options.add_argument("--headless")  # Comment this line if you want to see the browser
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--no-sandbox")

service = Service(chrome_path)
wd = webdriver.Chrome(service=service, options=chrome_options)


# --- Step 3: Function to scrape Google Images ---
def get_google_images(wd, keyword, max_images=30, delay=1):
    print(f"\n🔍 Searching for: {keyword}")
    search_url = f"https://www.google.com/search?q={keyword}&tbm=isch"
    wd.get(search_url)
    image_urls = set()

    last_height = wd.execute_script("return document.body.scrollHeight")

    while len(image_urls) < max_images:
        # Scroll down to load more images
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(delay)

        # Extract images
        imgs = wd.find_elements(By.TAG_NAME, "img")
        for img in imgs:
            src = img.get_attribute("src")
            if src and src.startswith("http") and not src.startswith("data:"):
                image_urls.add(src)
                if len(image_urls) >= max_images:
                    break

        new_height = wd.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    print(f"✅ Found {len(image_urls)} images from Google")
    return image_urls


# --- Step 4: Function to download images ---
def download_image(download_path, url, file_name):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Preserve or fix extension
        file_ext = os.path.splitext(url.split("?")[0])[1].lower()
        if file_ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"]:
            file_ext = ".jpg"

        file_path = os.path.join(download_path, f"{file_name}{file_ext}")
        with open(file_path, "wb") as f:
            f.write(response.content)

        print(f"✅ Downloaded: {file_name}{file_ext}")
    except Exception as e:
        print(f"⚠️ Failed to download {url}: {e}")


# --- Step 5: Run scraper and save images ---
urls = get_google_images(wd, keyword, max_images=50, delay=1)

print(f"\n📸 Total images to download: {len(urls)}")

for i, url in enumerate(urls):
    download_image(download_path, url, f"{keyword.replace(' ', '_')}_{i}")

wd.quit()
print(f"\n🎉 Scraping complete! All images saved in: {download_path}")
