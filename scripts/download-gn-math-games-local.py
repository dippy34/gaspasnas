#!/usr/bin/env python3
"""
Download games from gn-math.dev locally (no iframes)
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path
import time
import os

BASE_URL = "https://gn-math.dev/"
ZONES_URL = "https://cdn.jsdelivr.net/gh/gn-math/assets@main/zones.json"
COVERS_BASE = "https://cdn.jsdelivr.net/gh/gn-math/covers@main/"
HTML_BASE = "https://cdn.jsdelivr.net/gh/gn-math/html@main/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
}

GAMES_DIR = Path(__file__).parent.parent / "non-semag"
MAX_GAMES = 50

def load_existing_games():
    """Load existing games to avoid duplicates"""
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    if games_file.exists():
        with open(games_file, 'r', encoding='utf-8') as f:
            games = json.load(f)
            existing_dirs = {g.get('directory', '') for g in games}
            existing_names = {g.get('name', '').lower() for g in games}
            return existing_dirs, existing_names
    return set(), set()

def download_file(url, filepath):
    """Download a file from URL"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=HEADERS, stream=True, timeout=30)
        r.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"    ✗ Error downloading {url}: {e}")
        return False

def download_game(zone_id, zone_data, game_dir):
    """Download a single game locally"""
    print(f"\n  Downloading: {zone_data.get('name', zone_id)}")
    
    # Get game HTML URL
    html_url = f"{HTML_BASE}{zone_id}/index.html"
    
    # Try to download the HTML
    html_file = game_dir / "index.html"
    if not download_file(html_url, html_file):
        print(f"    ⚠ Could not download HTML, trying alternative...")
        # Try without /index.html
        html_url_alt = f"{HTML_BASE}{zone_id}.html"
        if not download_file(html_url_alt, html_file):
            return False
    
    # Read the HTML to find assets
    try:
        with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
    except:
        return False
    
    soup = BeautifulSoup(html_content, 'html.parser')
    base_url = f"{HTML_BASE}{zone_id}/"
    
    # Find and download all assets
    assets_downloaded = 0
    
    # Scripts
    for script in soup.find_all('script', src=True):
        src = script.get('src', '')
        if src and not src.startswith('http') and not src.startswith('//'):
            asset_url = urljoin(base_url, src)
            asset_path = game_dir / src.lstrip('/')
            if download_file(asset_url, asset_path):
                assets_downloaded += 1
                # Update HTML to use local path
                script['src'] = src.lstrip('/')
    
    # Stylesheets
    for link in soup.find_all('link', rel='stylesheet', href=True):
        href = link.get('href', '')
        if href and not href.startswith('http') and not href.startswith('//'):
            asset_url = urljoin(base_url, href)
            asset_path = game_dir / href.lstrip('/')
            if download_file(asset_url, asset_path):
                assets_downloaded += 1
                link['href'] = href.lstrip('/')
    
    # Images
    for img in soup.find_all('img', src=True):
        src = img.get('src', '')
        if src and not src.startswith('http') and not src.startswith('//') and not src.startswith('data:'):
            asset_url = urljoin(base_url, src)
            asset_path = game_dir / src.lstrip('/')
            if download_file(asset_url, asset_path):
                assets_downloaded += 1
                img['src'] = src.lstrip('/')
    
    # Look for asset references in script content
    asset_patterns = [
        r'["\']([^"\']*\.(js|css|png|jpg|jpeg|gif|webp|svg|json|wasm|data|br|woff|woff2|ttf)[^"\']*)["\']',
        r'url\(["\']?([^"\'()]+)["\']?\)',
    ]
    
    for pattern in asset_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for match in matches:
            asset_path_str = match if isinstance(match, str) else match[0]
            if asset_path_str and not asset_path_str.startswith(('http', '//', 'data:')):
                asset_url = urljoin(base_url, asset_path_str)
                asset_file = game_dir / asset_path_str.lstrip('/')
                if not asset_file.exists():
                    if download_file(asset_url, asset_file):
                        assets_downloaded += 1
    
    # Save updated HTML
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    # Download cover image
    cover_url = f"{COVERS_BASE}{zone_id}.png"
    cover_file = game_dir / "cover.png"
    download_file(cover_url, cover_file)
    
    print(f"    ✓ Downloaded {assets_downloaded} assets")
    return True

def main():
    print("GN-Math.dev Local Game Downloader")
    print("=" * 50)
    
    # Load zones
    print(f"Fetching zones from {ZONES_URL}...")
    try:
        r = requests.get(ZONES_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
        zones_data = r.json()
    except Exception as e:
        print(f"Error fetching zones: {e}")
        return
    
    if isinstance(zones_data, dict):
        zones = zones_data
    elif isinstance(zones_data, list):
        zones = {str(i): zone for i, zone in enumerate(zones_data)}
    else:
        print("Unexpected zones.json format")
        return
    
    print(f"Found {len(zones)} zones")
    
    existing_dirs, existing_names = load_existing_games()
    
    # Filter out games that already exist and skip special entries
    available_zones = []
    for zone_id, zone_data in zones.items():
        if isinstance(zone_data, dict):
            name = zone_data.get('name') or zone_data.get('title') or f"Zone {zone_id}"
        else:
            name = str(zone_data) if zone_data else f"Zone {zone_id}"
        
        # Skip suggestion/comments entries
        if name.startswith('[!]') or 'suggest' in name.lower() or 'comment' in name.lower():
            continue
        
        dir_name = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        if not dir_name or len(dir_name) < 2:
            dir_name = f"zone-{zone_id}"
        
        if name.lower() not in existing_names and dir_name not in existing_dirs:
            available_zones.append((zone_id, zone_data, name, dir_name))
    
    print(f"\nFound {len(available_zones)} available games")
    print(f"Downloading first {MAX_GAMES} games...\n")
    
    downloaded_games = []
    for i, (zone_id, zone_data, name, dir_name) in enumerate(available_zones[:MAX_GAMES]):
        game_dir = GAMES_DIR / dir_name
        
        if download_game(zone_id, zone_data, game_dir):
            game_info = {
                'name': name,
                'directory': dir_name,
                'image': 'cover.png',
                'source': 'non-semag'
            }
            downloaded_games.append(game_info)
            print(f"  ✓ Successfully downloaded: {name}")
        else:
            print(f"  ✗ Failed to download: {name}")
        
        time.sleep(0.5)  # Be polite
    
    # Add to games.json
    if downloaded_games:
        games_file = Path(__file__).parent.parent / "data" / "games.json"
        with open(games_file, 'r', encoding='utf-8') as f:
            existing_games = json.load(f)
        
        existing_games.extend(downloaded_games)
        
        with open(games_file, 'w', encoding='utf-8') as f:
            json.dump(existing_games, f, indent='\t', ensure_ascii=False)
        
        print(f"\n✓ Added {len(downloaded_games)} games to games.json")
        print(f"✓ Total games: {len(existing_games)}")
    else:
        print("\n⚠ No games were successfully downloaded")

if __name__ == "__main__":
    main()

