import requests
import os
from pathlib import Path

def get_api_key():
    """Prompt user for Pexels API key and confirm."""
    print("=" * 50)
    print("Pexels Image Downloader")
    print("=" * 50)
    api_key = input("\nPlease enter your Pexels API key: ").strip()
    
    if not api_key:
        print("Error: API key cannot be empty!")
        return None
    
    print(f"\n✓ API key received: {api_key[:10]}...{api_key[-4:]}")
    confirm = input("Is this correct? (yes/no): ").strip().lower()
    
    if confirm in ['yes', 'y']:
        print("✓ API key confirmed!\n")
        return api_key
    else:
        print("Let's try again.\n")
        return get_api_key()

def get_search_keyword():
    """Prompt user for search keyword."""
    keyword = input("Enter a search keyword to download images: ").strip()
    
    if not keyword:
        print("Error: Search keyword cannot be empty!")
        return get_search_keyword()
    
    return keyword

def create_download_folder(keyword):
    """Create a folder with the search keyword name."""
    folder_path = Path(keyword)
    folder_path.mkdir(exist_ok=True)
    print(f"\n✓ Created/Using folder: {folder_path.absolute()}\n")
    return folder_path

def download_images(api_key, keyword, num_images=10):
    """Download images from Pexels based on search keyword."""
    base_url = "https://api.pexels.com/v1/search"
    
    headers = {
        "Authorization": api_key
    }
    
    params = {
        "query": keyword,
        "per_page": num_images,
        "orientation": "landscape"
    }
    
    print(f"Searching for '{keyword}' images...")
    
    try:
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        photos = data.get('photos', [])
        
        if not photos:
            print(f"No images found for keyword: {keyword}")
            return
        
        print(f"Found {len(photos)} images. Starting download...\n")
        
        folder_path = create_download_folder(keyword)
        
        for idx, photo in enumerate(photos, 1):
            image_url = photo['src']['large']
            image_id = photo['id']
            photographer = photo['photographer']
            
            # Download image
            img_response = requests.get(image_url)
            img_response.raise_for_status()
            
            # Save image
            file_path = folder_path / f"{keyword}_{idx}_{image_id}.jpg"
            with open(file_path, 'wb') as f:
                f.write(img_response.content)
            
            print(f"[{idx}/{len(photos)}] Downloaded: {file_path.name}")
            print(f"    Photo by: {photographer}\n")
        
        print("=" * 50)
        print(f"✓ Successfully downloaded {len(photos)} images!")
        print(f"✓ Location: {folder_path.absolute()}")
        print("=" * 50)
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            print("\n✗ Error: Invalid API key. Please check your credentials.")
        elif response.status_code == 403:
            print("\n✗ Error: Access forbidden. Please check your API key permissions.")
        elif response.status_code == 429:
            print("\n✗ Error: API rate limit exceeded. Please try again later.")
        else:
            print(f"\n✗ HTTP Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Error downloading images: {e}")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")

def main():
    """Main function to run the Pexels image downloader."""
    # Step 1: Get and confirm API key
    api_key = get_api_key()
    if not api_key:
        return
    
    # Step 2: Get search keyword
    keyword = get_search_keyword()
    
    # Step 3: Download images
    num_images = input(f"\nHow many images would you like to download? (default: 10, max: 80): ").strip()
    
    try:
        num_images = int(num_images) if num_images else 10
        num_images = min(num_images, 80)  # Pexels API limit per page
    except ValueError:
        num_images = 10
        print("Invalid number. Using default: 10 images")
    
    download_images(api_key, keyword, num_images)

if __name__ == "__main__":
    main()
