"""
Comprehensive Lagged game downloader - downloads ALL game assets
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}

def download_file(url, filepath):
    """Download a file from URL"""
    try:
        response = requests.get(url, headers=HEADERS, stream=True, timeout=30)
        response.raise_for_status()
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True, filepath.stat().st_size
    except Exception as e:
        return False, str(e)

def extract_all_assets(html_content, base_url, game_dir):
    """Extract and download all assets from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    assets = {
        'scripts': [],
        'stylesheets': [],
        'images': [],
        'fonts': [],
        'data': [],
        'other': []
    }
    
    # Scripts
    for script in soup.find_all('script', src=True):
        src = script.get('src', '')
        if src:
            full_url = urljoin(base_url, src)
            assets['scripts'].append(full_url)
    
    # Inline scripts - look for URLs
    for script in soup.find_all('script'):
        if script.string:
            # Find URLs in script content
            url_patterns = [
                r'["\']([^"\']*\.(js|wasm|data|json)[^"\']*)["\']',
                r'src\s*[:=]\s*["\']([^"\']+)["\']',
                r'url\(["\']?([^"\'()]+)["\']?\)',
            ]
            for pattern in url_patterns:
                matches = re.findall(pattern, script.string, re.I)
                for match in matches:
                    url = match if isinstance(match, str) else match[0]
                    if url and not url.startswith('javascript:'):
                        full_url = urljoin(base_url, url)
                        if full_url not in assets['scripts']:
                            assets['scripts'].append(full_url)
    
    # Stylesheets
    for link in soup.find_all('link', rel='stylesheet', href=True):
        href = link.get('href', '')
        if href:
            full_url = urljoin(base_url, href)
            assets['stylesheets'].append(full_url)
    
    # Images
    for img in soup.find_all('img', src=True):
        src = img.get('src', '')
        if src:
            full_url = urljoin(base_url, src)
            assets['images'].append(full_url)
    
    # Fonts
    for link in soup.find_all('link', rel=re.compile('font', re.I), href=True):
        href = link.get('href', '')
        if href:
            full_url = urljoin(base_url, href)
            assets['fonts'].append(full_url)
    
    # Look for data files (WASM, data, etc.)
    for tag in soup.find_all(['link', 'script', 'source']):
        href = tag.get('href') or tag.get('src') or tag.get('data-src')
        if href:
            full_url = urljoin(base_url, href)
            ext = Path(urlparse(full_url).path).suffix.lower()
            if ext in ['.wasm', '.data', '.br', '.gz']:
                assets['data'].append(full_url)
    
    return assets

def download_game_assets(game_url, game_dir):
    """Download all assets for a game"""
    print(f"  📥 Downloading: {game_url.split('/')[-1]}")
    
    try:
        # Get main game page
        response = requests.get(game_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the actual game play URL
        play_url = None
        
        # Look for iframe with game
        iframe = soup.find('iframe', src=True)
        if iframe:
            play_url = urljoin(game_url, iframe.get('src'))
        
        # Look for game links
        if not play_url:
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '/games/' in href or '/play/' in href:
                    play_url = urljoin(game_url, href)
                    break
        
        # Look in scripts
        if not play_url:
            for script in soup.find_all('script'):
                if script.string:
                    matches = re.findall(r'["\']([^"\']*games/[^"\']*)["\']', script.string)
                    if matches:
                        play_url = urljoin(game_url, matches[0])
                        break
        
        if not play_url:
            print(f"    ⚠️  No play URL found, using game page")
            play_url = game_url
        
        # Get the game play page
        print(f"    🔍 Fetching game page: {play_url}")
        game_response = requests.get(play_url, headers=HEADERS, timeout=30)
        game_response.raise_for_status()
        game_html = game_response.text
        
        # Save main HTML
        (game_dir / 'index.html').write_text(game_html, encoding='utf-8')
        
        # Extract all assets
        print(f"    🔍 Extracting assets...")
        assets = extract_all_assets(game_html, play_url, game_dir)
        
        total_assets = sum(len(v) for v in assets.values())
        print(f"    📦 Found {total_assets} assets to download")
        
        # Download all assets
        downloaded = 0
        failed = 0
        
        # Create subdirectories
        (game_dir / 'js').mkdir(exist_ok=True)
        (game_dir / 'css').mkdir(exist_ok=True)
        (game_dir / 'images').mkdir(exist_ok=True)
        (game_dir / 'data').mkdir(exist_ok=True)
        
        # Download scripts
        for url in assets['scripts']:
            filename = Path(urlparse(url).path).name
            if not filename:
                continue
            filepath = game_dir / 'js' / filename
            success, result = download_file(url, filepath)
            if success:
                downloaded += 1
            else:
                failed += 1
        
        # Download stylesheets
        for url in assets['stylesheets']:
            filename = Path(urlparse(url).path).name
            if not filename:
                continue
            filepath = game_dir / 'css' / filename
            success, result = download_file(url, filepath)
            if success:
                downloaded += 1
            else:
                failed += 1
        
        # Download images
        for url in assets['images']:
            filename = Path(urlparse(url).path).name
            if not filename:
                continue
            filepath = game_dir / 'images' / filename
            success, result = download_file(url, filepath)
            if success:
                downloaded += 1
            else:
                failed += 1
        
        # Download data files
        for url in assets['data']:
            filename = Path(urlparse(url).path).name
            if not filename:
                continue
            filepath = game_dir / 'data' / filename
            success, result = download_file(url, filepath)
            if success:
                downloaded += 1
            else:
                failed += 1
        
        # Update HTML to use local paths
        update_html_paths(game_dir / 'index.html', play_url)
        
        # Get cover image
        try:
            response = requests.get(game_url, headers=HEADERS, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                img_url = urljoin(game_url, og_image['content'])
                cover_path = game_dir / 'cover.png'
                download_file(img_url, cover_path)
        except:
            pass
        
        print(f"    ✅ Downloaded {downloaded} assets ({failed} failed)")
        return True, downloaded
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False, 0

def update_html_paths(html_path, base_url):
    """Update HTML to use local asset paths"""
    try:
        html_content = html_path.read_text(encoding='utf-8')
        
        # Replace external URLs with local paths
        # This is a simplified version - you might need more sophisticated path rewriting
        base_domain = urlparse(base_url).netloc
        
        # Replace script src
        html_content = re.sub(
            rf'https?://[^/]*{re.escape(base_domain)}[^"\']*/([^/]+\.js)',
            r'js/\1',
            html_content
        )
        
        # Replace stylesheet href
        html_content = re.sub(
            rf'https?://[^/]*{re.escape(base_domain)}[^"\']*/([^/]+\.css)',
            r'css/\1',
            html_content
        )
        
        html_path.write_text(html_content, encoding='utf-8')
    except Exception as e:
        print(f"    ⚠️  Could not update HTML paths: {e}")

def main():
    import sys
    
    games_list_file = Path('lagged-games-list.json')
    non_semag_dir = Path('non-semag')
    
    if not games_list_file.exists():
        print(f"❌ {games_list_file} not found. Run scrape-lagged-category.py first.")
        return
    
    print("🎮 Full Lagged Game Downloader\n" + "="*50 + "\n")
    
    # Load games list
    with open(games_list_file, 'r', encoding='utf-8') as f:
        games_list = json.load(f)
    
    successful_games = [g for g in games_list if g.get('status') == 'success']
    
    if not successful_games:
        print("❌ No games to download")
        return
    
    print(f"📋 Downloading {len(successful_games)} games with all assets...\n")
    
    # Download games
    results = []
    for game in successful_games:
        slug = game.get('slug', '')
        game_url = game.get('url', '')
        play_url = game.get('play_url', '')
        
        if not slug or not game_url:
            continue
        
        game_dir = non_semag_dir / slug
        game_dir.mkdir(exist_ok=True)
        
        # Use play_url if available, otherwise game_url
        url_to_download = play_url if play_url else game_url
        
        success, count = download_game_assets(url_to_download, game_dir)
        results.append({
            'slug': slug,
            'success': success,
            'assets_downloaded': count
        })
        
        time.sleep(0.5)  # Be polite
    
    successful = [r for r in results if r['success']]
    print(f"\n✅ Complete! Successfully downloaded {len(successful)}/{len(successful_games)} games")
    print(f"📊 Total assets downloaded: {sum(r['assets_downloaded'] for r in successful)}")

if __name__ == "__main__":
    main()

