#!/usr/bin/env python3
"""
Scraper for Veck.io - Only game files, no website assets
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import re
import time

GAME_URL = "https://games.crazygames.com/en_US/veck-io/index.html"
OUTPUT_DIR = Path("scraped-veck-io")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.crazygames.com/'
}

def setup_directories():
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "scripts").mkdir(exist_ok=True)
    (OUTPUT_DIR / "stylesheets").mkdir(exist_ok=True)
    (OUTPUT_DIR / "images").mkdir(exist_ok=True)
    (OUTPUT_DIR / "other").mkdir(exist_ok=True)

def download_file(url, filepath):
    try:
        response = requests.get(url, stream=True, timeout=30, headers=HEADERS)
        response.raise_for_status()
        
        total_size = 0
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)
        
        print(f"✓ Downloaded: {filepath.name} ({total_size:,} bytes)")
        return True
    except Exception as e:
        print(f"✗ Failed to download {url}: {e}")
        return False

def scrape_game():
    setup_directories()
    print("🎮 Veck.io Game Scraper")
    print("=" * 60)
    print("⚠️  Only downloading game files, NOT website assets")
    print()
    
    # Get base URL
    parsed = urlparse(GAME_URL)
    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rsplit('/', 1)[0]}/"
    
    print(f"📄 Fetching {GAME_URL}...")
    try:
        response = requests.get(GAME_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        html_content = response.text
        (OUTPUT_DIR / "index.html").write_text(html_content, encoding='utf-8')
        print("✓ Saved index.html")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract asset URLs
    print("\n🔍 Extracting assets from HTML...")
    assets_to_download = []
    
    # Scripts
    for script in soup.find_all('script', src=True):
        src = urljoin(base_url, script['src'])
        if urlparse(src).netloc == urlparse(base_url).netloc:
            assets_to_download.append({'url': src, 'type': 'script'})
    
    # Stylesheets
    for link in soup.find_all('link', rel="stylesheet", href=True):
        href = urljoin(base_url, link['href'])
        if urlparse(href).netloc == urlparse(base_url).netloc:
            assets_to_download.append({'url': href, 'type': 'stylesheet'})
    
    # Images
    for img in soup.find_all('img', src=True):
        src = urljoin(base_url, img['src'])
        if urlparse(src).netloc == urlparse(base_url).netloc:
            assets_to_download.append({'url': src, 'type': 'image'})
    
    # Favicon
    for link in soup.find_all('link', rel=re.compile("icon", re.I), href=True):
        href = urljoin(base_url, link['href'])
        if urlparse(href).netloc == urlparse(base_url).netloc:
            assets_to_download.append({'url': href, 'type': 'favicon'})
    
    # Filter out duplicates and external scripts
    unique_assets = []
    seen_urls = set()
    for asset in assets_to_download:
        if asset['url'] not in seen_urls and not any(x in asset['url'] for x in ['googlesyndication', 'doubleclick', 'crazygames.com/portal', 'crazygames.com/images']):
            unique_assets.append(asset)
            seen_urls.add(asset['url'])
    
    print(f"  Found {len([a for a in unique_assets if a['type'] == 'script'])} scripts")
    print(f"  Found {len([a for a in unique_assets if a['type'] == 'stylesheet'])} stylesheets")
    print(f"  Found {len([a for a in unique_assets if a['type'] == 'image'])} images")
    
    # Download assets
    print(f"\n📥 Downloading {len(unique_assets)} assets...")
    downloaded_count = 0
    for asset in unique_assets:
        parsed_url = urlparse(asset['url'])
        filename = Path(parsed_url.path).name
        
        target_dir = OUTPUT_DIR / "other"
        if asset['type'] == 'script':
            target_dir = OUTPUT_DIR / "scripts"
        elif asset['type'] == 'stylesheet':
            target_dir = OUTPUT_DIR / "stylesheets"
        elif asset['type'] == 'image' or asset['type'] == 'favicon':
            target_dir = OUTPUT_DIR / "images"
        
        if download_file(asset['url'], target_dir / filename):
            downloaded_count += 1
        time.sleep(0.1)  # Be polite
    
    print(f"\n✅ Complete! Downloaded {downloaded_count}/{len(unique_assets)} assets")
    print(f"📁 Assets saved to: {OUTPUT_DIR.resolve()}")

if __name__ == "__main__":
    scrape_game()


