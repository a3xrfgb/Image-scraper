import os
import time
import requests
import json
import hashlib
import base64
import uuid
from PIL import Image
from io import BytesIO
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
import pandas as pd
from openai import OpenAI

# Ask user for search keyword
search_keyword = input("Enter the search keyword to scrape from Google Images: ").strip()

# Ask for minimum pixels (configurable)
min_pixels_input = input("Enter minimum total pixels for hi-res images (e.g., 500000, or 0 to disable check): ").strip()
MIN_PIXELS = int(min_pixels_input) if min_pixels_input.isdigit() else 500000

print(f"Using minimum pixels: {MIN_PIXELS}. Images below this will be skipped.")

# Ask for OpenAI API key
api_key = input("Enter your OpenAI API key for image captioning: ").strip()
if not api_key:
    print("Error: OpenAI API key is required for captioning!")
    exit(1)

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Create a folder with the same name
folder_name = search_keyword.replace(" ", "_")
if not os.path.isdir(folder_name):
    os.makedirs(folder_name)

downloaded_urls = set()
metadata_list = []

def calculate_md5(file_path):
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_mime_type(file_path):
    """Get MIME type of an image file"""
    try:
        img = Image.open(file_path)
        format_to_mime = {
            'JPEG': 'image/jpeg',
            'PNG': 'image/png',
            'GIF': 'image/gif',
            'BMP': 'image/bmp',
            'WEBP': 'image/webp'
        }
        return format_to_mime.get(img.format, 'image/jpeg')
    except:
        return 'image/jpeg'

def caption_image(file_path):
    """Generate detailed caption using OpenAI GPT-4 Vision API"""
    try:
        with open(file_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        response = client.chat.completions.create(
            model="gpt-4o",  # Using GPT-4o (the latest vision model)
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Provide an extremely detailed caption for this image. Describe the main subjects, their appearance, actions, setting, colors, mood, composition, and any notable details. Be thorough and specific."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        caption = response.choices[0].message.content
        print(f"   ✓ Caption generated: {caption[:80]}...")
        return caption
    
    except Exception as e:
        print(f"   ✗ Error generating caption: {e}")
        return "Caption generation failed"

def download_image(url, folder_name, num):
    """Download image and return metadata if successful"""
    if url in downloaded_urls:
        print(f"Skipping duplicate image: {num}")
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'image' in content_type:
                # Create file name
                file_name = f"{num}.jpg"
                file_path = os.path.join(folder_name, file_name)
                
                # Check resolution before saving
                if MIN_PIXELS == 0:
                    with open(file_path, "wb") as file:
                        file.write(response.content)
                    downloaded_urls.add(url)
                    
                    # Get image dimensions
                    img = Image.open(file_path)
                    width, height = img.size
                    
                    print(f"Downloaded image {num} (pixel check disabled)")
                    print(f"   Captioning image {num}...")
                    
                    # Generate caption
                    caption = caption_image(file_path)
                    
                    # Create metadata with new format
                    metadata = {
                        'url': url,
                        'file_name': file_name,
                        'id': f"E{num:03d}",  # Format as E001, E002, E003, etc.
                        'title': f"{search_keyword} - Image {num}",
                        'caption': caption,
                        'width': width,
                        'height': height,
                        'mime_type': get_mime_type(file_path),
                        'hash': calculate_md5(file_path),
                        'license': 'Creative Commons License',
                        'source': 'Google Images'
                    }
                    return metadata
                else:
                    try:
                        img = Image.open(BytesIO(response.content))
                        width, height = img.size
                        total_pixels = width * height
                        
                        if total_pixels >= MIN_PIXELS:
                            with open(file_path, "wb") as file:
                                file.write(response.content)
                            downloaded_urls.add(url)
                            
                            print(f"Downloaded hi-res image {num} ({width}x{height}, {total_pixels} pixels)")
                            print(f"   Captioning image {num}...")
                            
                            # Generate caption
                            caption = caption_image(file_path)
                            
                            # Create metadata with new format
                            metadata = {
                                'url': url,
                                'file_name': file_name,
                                'id': f"E{num:03d}",  # Format as E001, E002, E003, etc.
                                'title': f"{search_keyword} - Image {num}",
                                'caption': caption,
                                'width': width,
                                'height': height,
                                'mime_type': get_mime_type(file_path),
                                'hash': calculate_md5(file_path),
                                'license': 'Creative Commons License',
                                'source': 'Google Images'
                            }
                            return metadata
                        else:
                            print(f"Skipping low-res image {num} ({width}x{height}, {total_pixels} pixels) - below {MIN_PIXELS} pixels")
                            return None
                    except Exception as e:
                        print(f"Error checking resolution for image {num}: {e}")
                        return None
    except Exception as e:
        print(f"Error downloading image {num}: {e}")
    return None

def save_metadata_files():
    """Save metadata to JSONL and Parquet files"""
    print("\n📝 Saving metadata...")
    
    # Save metadata to JSONL
    jsonl_path = os.path.join(folder_name, "metadata.jsonl")
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for metadata in metadata_list:
            f.write(json.dumps(metadata) + '\n')
    print(f"✅ Saved metadata.jsonl with {len(metadata_list)} entries")
    
    # Save metadata to Parquet
    try:
        df = pd.DataFrame(metadata_list)
        parquet_path = os.path.join(folder_name, "metadata.parquet")
        df.to_parquet(parquet_path, index=False)
        print(f"✅ Saved metadata.parquet with {len(metadata_list)} entries")
    except Exception as e:
        print(f"⚠️ Error saving Parquet file: {e}")
        print("   (Make sure pyarrow or fastparquet is installed: pip install pyarrow)")

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
    while True:
        try:
            # Make sure we're on the main window
            if driver.current_window_handle != main_window:
                driver.switch_to.window(main_window)
            
            # Close any extra tabs
            if len(driver.window_handles) > 1:
                for handle in driver.window_handles:
                    if handle != main_window:
                        driver.switch_to.window(handle)
                        driver.close()
                driver.switch_to.window(main_window)
            
            # Re-find thumbnails
            thumbnails = driver.find_elements(By.CSS_SELECTOR, "img.rg_i")
            if not thumbnails:
                thumbnails = driver.find_elements(By.CSS_SELECTOR, "img.YQ4gaf")
            
            # Check if we need more images
            if idx >= len(thumbnails):
                print("\nReached end of available images. Scrolling for more...")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                try:
                    show_more = driver.find_element(By.CSS_SELECTOR, "input.mye4qd")
                    show_more.click()
                    time.sleep(3)
                    print("Loaded more images...")
                except:
                    pass
                
                idx = len(thumbnails) - 10 if len(thumbnails) > 10 else 0
                continue
            
            thumbnail = thumbnails[idx]
            idx += 1
            
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thumbnail)
                time.sleep(0.5)
                thumbnail.click()
                time.sleep(2)
            except (ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException):
                continue
            
            # Method 1: Try preview panel image
            try:
                full_image = driver.find_element(By.CSS_SELECTOR, "img.sFlh5c.pT0Scc.iPVvYb")
                src = full_image.get_attribute("src")
                
                if src and src.startswith("http") and "encrypted-tbn0" not in src:
                    metadata = download_image(src, folder_name, count + 1)
                    if metadata:
                        metadata_list.append(metadata)
                        count += 1
                        continue
            except (NoSuchElementException, StaleElementReferenceException):
                pass
            
            # Method 2: Alternative selectors
            try:
                images = driver.find_elements(By.CSS_SELECTOR, "img[src^='http']")
                for img in images:
                    try:
                        src = img.get_attribute("src")
                        if (src and src.startswith("http") and 
                            "encrypted-tbn0" not in src and 
                            "gstatic" not in src and
                            "google.com/images" not in src):
                            
                            metadata = download_image(src, folder_name, count + 1)
                            if metadata:
                                metadata_list.append(metadata)
                                count += 1
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
    # Save metadata files when user interrupts
    save_metadata_files()

# Final cleanup
if len(driver.window_handles) > 1:
    for handle in driver.window_handles:
        if handle != main_window:
            driver.switch_to.window(handle)
            driver.close()
    driver.switch_to.window(main_window)

driver.quit()

# Save metadata files (for normal completion)
if metadata_list:
    save_metadata_files()

print(f"\n✅ Done! {count} full-resolution images downloaded into '{folder_name}'")
print(f"📊 Processed {idx} thumbnails total")
print(f"📁 Metadata files saved in '{folder_name}' folder")