import os
import io
import time
import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# --- Step 1: User Inputs ---
chrome_path = input("Enter the full path to your ChromeDriver (e.g., C:\\path\\to\\chromedriver.exe): ").strip()
keyword = input("Enter the search keyword (e.g., 'Ethiopian landscape'): ").strip()

# Automatically create a folder named after the keyword
download_path = os.path.join(os.getcwd(), keyword.replace(" ", "_"))
os.makedirs(download_path, exist_ok=True)

print(f"\n📂 Images will be saved in: {download_path}")

# --- Step 2: Configure Chrome (headless optional) ---
chrome_options = Options()
chrome_options.add_argument("--headless")  # comment this line if you want to see the browser
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--no-sandbox")

service = Service(chrome_path)
wd = webdriver.Chrome(service=service, options=chrome_options)


# --- Step 3: Scraping Function ---
def get_images_from_source(wd, source, keyword, max_images=10, delay=1):
    image_urls = set()
    search_urls = {
        "google": f"https://www.google.com/search?q={keyword}&tbm=isch",
        "bing": f"https://www.bing.com/images/search?q={keyword}",
        "duckduckgo": f"https://duckduckgo.com/?q={keyword}&iax=images&ia=images"
    }

    if source not in search_urls:
        print(f"❌ Unknown source: {source}")
        return image_urls

    print(f"\n🔍 Scraping from {source.title()}...")
    wd.get(search_urls[source])
    time.sleep(2)

    last_height = wd.execute_script("return document.body.scrollHeight")

    while len(image_urls) < max_images:
        # Scroll to bottom to load more
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(delay)

        # Get images
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

    print(f"✅ Found {len(image_urls)} images from {source.title()}")
    return image_urls


# --- Step 4: Download Function ---
def download_image(download_path, url, file_name):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Detect and preserve proper file extension
        file_ext = os.path.splitext(url.split("?")[0])[1].lower()
        if file_ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"]:
            file_ext = ".jpg"

        file_path = os.path.join(download_path, f"{file_name}{file_ext}")

        with open(file_path, "wb") as f:
            f.write(response.content)

        print(f"✅ Downloaded: {file_name}{file_ext}")
    except Exception as e:
        print(f"⚠️ Failed to download {url}: {e}")


# --- Step 5: Collect and Save Images from All Sources ---
all_sources = ["google", "bing", "duckduckgo"]
all_urls = set()

for src in all_sources:
    urls = get_images_from_source(wd, src, keyword, max_images=15, delay=1)
    all_urls.update(urls)

print(f"\n📸 Total unique images collected: {len(all_urls)}")

for i, url in enumerate(all_urls):
    download_image(download_path, url, f"{keyword.replace(' ', '_')}_{i}")

wd.quit()
print(f"\n🎉 Scraping complete! All images saved in: {download_path}")
