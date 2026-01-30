import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import re
import time
import json

BASE_URL = 'https://lagged.com/en/g/whack-your-boss'
OUTPUT_DIR = Path('./scraped-lagged-whack-your-boss-assets')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://lagged.com/'
}

def setup_directories():
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "images").mkdir(exist_ok=True)
    (OUTPUT_DIR / "scripts").mkdir(exist_ok=True)
    (OUTPUT_DIR / "stylesheets").mkdir(exist_ok=True)
    (OUTPUT_DIR / "data").mkdir(exist_ok=True)
    (OUTPUT_DIR / "other").mkdir(exist_ok=True)

def download_file(url, filepath):
    try:
        response = requests.get(url, stream=True, timeout=30, headers=HEADERS)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✓ Downloaded: {filepath.name} ({filepath.stat().st_size} bytes)")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to download {url}: {e}")
        return False

def scrape_assets():
    setup_directories()
    print("🎮 Lagged Whack Your Boss Asset Scraper\n" + "="*50 + "\n")

    # 1. Fetch the main HTML page
    print(f"📄 Fetching {BASE_URL}...")
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        html_content = response.text
        (OUTPUT_DIR / "index.html").write_text(html_content, encoding='utf-8')
        print("✓ Saved index.html")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return

    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 2. Extract game embed information
    print("\n🔍 Extracting game embed information...")
    
    # Look for iframe with game embed
    game_iframe = soup.find('iframe', {'id': re.compile('game', re.I)})
    if not game_iframe:
        game_iframe = soup.find('iframe', src=re.compile('game|embed|play', re.I))
    
    # Look for game container divs
    game_containers = soup.find_all(['div', 'section'], class_=re.compile('game|play|embed', re.I))
    
    embed_urls = []
    game_urls_found = []
    
    if game_iframe and game_iframe.get('src'):
        embed_url = urljoin(BASE_URL, game_iframe['src'])
        embed_urls.append(embed_url)
        print(f"  Found iframe: {embed_url}")
    
    # Look for object/embed tags
    for obj in soup.find_all(['object', 'embed']):
        if obj.get('data') or obj.get('src'):
            url = obj.get('data') or obj.get('src')
            if url:
                full_url = urljoin(BASE_URL, url)
                embed_urls.append(full_url)
                print(f"  Found embed: {full_url}")
    
    # Look for game script tags that might contain game URLs
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            # Look for common game URL patterns
            patterns = [
                r'["\']([^"\']*game[^"\']*\.(html|js|wasm)[^"\']*)["\']',  # Game files
                r'gameUrl["\']?\s*[:=]\s*["\']([^"\']+)["\']',  # gameUrl assignments
                r'src["\']?\s*[:=]\s*["\']([^"\']+game[^"\']*)["\']',  # src with game
                r'iframe["\']?\s*[:=]\s*["\']([^"\']+)["\']',  # iframe URLs
                r'["\']([^"\']*play[^"\']*\.(html|js)[^"\']*)["\']',  # Play URLs
                r'["\'](https?://[^"\']*lagged[^"\']*game[^"\']*)["\']',  # Lagged game URLs
            ]
            for pattern in patterns:
                matches = re.findall(pattern, script.string, re.I)
                for match in matches:
                    url = match if isinstance(match, str) else match[0] if isinstance(match, tuple) else match
                    if url and not url.startswith('javascript:') and url not in game_urls_found:
                        full_url = urljoin(BASE_URL, url) if not url.startswith('http') else url
                        game_urls_found.append(full_url)
                        print(f"  Found game URL in script: {full_url}")
    
    # Look for data attributes that might contain game URLs
    for element in soup.find_all(attrs={'data-game-url': True}):
        url = element.get('data-game-url')
        if url:
            full_url = urljoin(BASE_URL, url)
            if full_url not in game_urls_found:
                game_urls_found.append(full_url)
                print(f"  Found data-game-url: {full_url}")
    
    for element in soup.find_all(attrs={'data-src': True}):
        url = element.get('data-src')
        if url and ('game' in url.lower() or 'play' in url.lower()):
            full_url = urljoin(BASE_URL, url)
            if full_url not in game_urls_found:
                game_urls_found.append(full_url)
                print(f"  Found data-src: {full_url}")

    # 3. Extract asset URLs
    print("\n🔍 Extracting assets from HTML...")
    assets_to_download = []

    # Images
    for img in soup.find_all('img', src=True):
        src = urljoin(BASE_URL, img['src'])
        parsed = urlparse(src)
        if parsed.netloc in ['lagged.com', 'www.lagged.com', 'cdn.lagged.com', '']:
            assets_to_download.append({'url': src, 'type': 'image'})
    
    # Favicon
    for link in soup.find_all('link', rel=re.compile("icon", re.I), href=True):
        href = urljoin(BASE_URL, link['href'])
        assets_to_download.append({'url': href, 'type': 'favicon'})

    # Scripts
    for script in soup.find_all('script', src=True):
        src = urljoin(BASE_URL, script['src'])
        parsed = urlparse(src)
        if parsed.netloc in ['lagged.com', 'www.lagged.com', 'cdn.lagged.com', '']:
            assets_to_download.append({'url': src, 'type': 'script'})

    # Stylesheets
    for link in soup.find_all('link', rel="stylesheet", href=True):
        href = urljoin(BASE_URL, link['href'])
        parsed = urlparse(href)
        if parsed.netloc in ['lagged.com', 'www.lagged.com', 'cdn.lagged.com', '']:
            assets_to_download.append({'url': href, 'type': 'stylesheet'})

    # Add found game URLs
    for url in embed_urls + game_urls_found:
        assets_to_download.append({'url': url, 'type': 'game'})

    # Filter out duplicates and external ad scripts
    unique_assets = []
    seen_urls = set()
    for asset in assets_to_download:
        if asset['url'] not in seen_urls:
            # Filter out external ad networks
            if not any(domain in asset['url'] for domain in ['googlesyndication', 'doubleclick', 'facebook', 'twitter', 'google-analytics', 'googletagmanager']):
                unique_assets.append(asset)
                seen_urls.add(asset['url'])

    print(f"  Found {len([a for a in unique_assets if a['type'] == 'image'])} images")
    print(f"  Found {len([a for a in unique_assets if a['type'] == 'script'])} scripts")
    print(f"  Found {len([a for a in unique_assets if a['type'] == 'stylesheet'])} stylesheets")
    print(f"  Found {len([a for a in unique_assets if a['type'] == 'game'])} game files")
    print(f"  Found {len([a for a in unique_assets if a['type'] == 'favicon'])} favicons")

    # 4. Download assets
    print(f"\n📥 Downloading {len(unique_assets)} assets...")
    downloaded_count = 0
    game_file_path = None
    
    for asset in unique_assets:
        parsed_url = urlparse(asset['url'])
        filename = Path(parsed_url.path).name or 'index.html'
        
        # Handle query parameters in filename
        if '?' in filename:
            filename = filename.split('?')[0]
        
        # Clean filename
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        if not filename or filename == '_':
            filename = 'index.html'
        
        target_dir = OUTPUT_DIR / "other"
        if asset['type'] == 'image' or asset['type'] == 'favicon':
            target_dir = OUTPUT_DIR / "images"
        elif asset['type'] == 'script':
            target_dir = OUTPUT_DIR / "scripts"
        elif asset['type'] == 'stylesheet':
            target_dir = OUTPUT_DIR / "stylesheets"
        elif asset['type'] == 'game':
            target_dir = OUTPUT_DIR / "data"
            if not game_file_path:  # Save first game file path
                game_file_path = target_dir / filename
        
        if download_file(asset['url'], target_dir / filename):
            downloaded_count += 1
        time.sleep(0.1)  # Be polite

    print(f"\n✅ Complete! Downloaded {downloaded_count}/{len(unique_assets)} assets")
    print(f"📁 Assets saved to: {OUTPUT_DIR.resolve()}")
    
    if game_file_path:
        print(f"🎮 Game file: {game_file_path}")
    
    # Save metadata
    metadata = {
        'source_url': BASE_URL,
        'game_urls': embed_urls + game_urls_found,
        'total_assets': downloaded_count
    }
    (OUTPUT_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(f"📋 Metadata saved to: {OUTPUT_DIR / 'metadata.json'}")

if __name__ == "__main__":
    scrape_assets()

