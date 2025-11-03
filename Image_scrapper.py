oimport os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager

# --- Step 1: User Inputs ---
keyword = input("Enter the search keyword (e.g., 'iceland landscapes'): ").strip()

# Create folder automatically
download_path = os.path.join(os.getcwd(), keyword.replace(" ", "_"))
os.makedirs(download_path, exist_ok=True)
print(f"\n📂 Images will be saved in: {download_path}")

# --- Step 2: Configure Chrome ---
chrome_options = Options()
chrome_options.add_argument("--headless")  # comment this line to see browser
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--window-size=1920,1080")

service = Service(ChromeDriverManager().install())
wd = webdriver.Chrome(service=service, options=chrome_options)

# --- Step 3: Scroll + High-res Fetch ---
def get_highres_images(wd, keyword, max_images=200, delay=1):
    search_url = f"https://www.google.com/search?q={keyword}&tbm=isch"
    wd.get(search_url)
    image_urls = set()
    skips = 0

    def scroll_down():
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(delay)

    print(f"\n🔍 Collecting full-resolution images for '{keyword}' ...")

    while len(image_urls) < max_images:
        # Try multiple selectors (Google changes often)
        thumbnails = wd.find_elements(By.CSS_SELECTOR, "img[jsname='Q4LuWd'], img.YQ4gaf, img.sFlh5c")
        print(f"🖼️ Found {len(thumbnails)} thumbnails so far...")

        if len(thumbnails) == 0:
            scroll_down()
            continue

        for thumb in thumbnails[len(image_urls)+skips:max_images]:
            try:
                wd.execute_script("arguments[0].scrollIntoView();", thumb)
                thumb.click()
                time.sleep(1.5)
            except (ElementClickInterceptedException, ElementNotInteractableException):
                skips += 1
                continue

            # Multiple fallback patterns for high-res images
            images = wd.find_elements(By.CSS_SELECTOR, "img.n3VNCb, img.r48jcc, img.sFlh5c, img.YQ4gaf")
            for image in images:
                src = image.get_attribute("src")
                if src and src.startswith("http") and not src.startswith("data:"):
                    if src not in image_urls:
                        image_urls.add(src)
                        print(f"✅ Found high-res image {len(image_urls)}")
            if len(image_urls) >= max_images:
                break
        else:
            scroll_down()

        # Try clicking “Show more results” if available
        try:
            more_button = wd.find_element(By.CSS_SELECTOR, ".YstHxe input")
            wd.execute_script("arguments[0].click();", more_button)
        except Exception:
            pass

        if len(thumbnails) == 0:
            break

    print(f"\n✅ Collected {len(image_urls)} unique image URLs.")
    return image_urls


# --- Step 4: Download Function ---
def download_image(download_path, url, file_name):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        ext = os.path.splitext(url.split("?")[0])[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"]:
            ext = ".jpg"
        file_path = os.path.join(download_path, f"{file_name}{ext}")
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"💾 Saved: {file_name}{ext}")
    except Exception as e:
        print(f"⚠️ Skipped {url}: {e}")

# --- Step 5: Run ---
urls = get_highres_images(wd, keyword, max_images=150, delay=1)
print(f"\n📸 Ready to download {len(urls)} images...\n")

for i, url in enumerate(urls):
    download_image(download_path, url, f"{keyword.replace(' ', '_')}_{i}")

wd.quit()
print(f"\n🎉 Done! All images saved in: {download_path}")
