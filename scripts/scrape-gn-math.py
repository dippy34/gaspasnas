#!/usr/bin/env python3
"""
Scrape games from gn-math.dev
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path
import time

BASE_URL = "https://gn-math.dev/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def load_existing_games():
    """Load existing games from games.json to avoid duplicates"""
    games_file = Path(__file__).parent.parent / "data" / "games.json"
    if games_file.exists():
        with open(games_file, 'r', encoding='utf-8') as f:
            games = json.load(f)
            # Create sets of existing names, directories, and URL slugs
            existing_names = {g.get('name', '').lower() for g in games}
            existing_dirs = {g.get('directory', '') for g in games}
            return existing_names, existing_dirs
    return set(), set()

def scrape_games():
    """Scrape games from gn-math.dev"""
    print(f"Fetching games from gn-math.dev API...")
    
    # The site loads games from a JSON API
    zones_url = "https://cdn.jsdelivr.net/gh/gn-math/assets@main/zones.json"
    
    try:
        r = requests.get(zones_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        zones_data = r.json()
    except Exception as e:
        print(f"Error fetching zones.json: {e}")
        return []
    
    existing_names, existing_dirs = load_existing_games()
    games = []
    
    # zones.json is a dictionary where keys are zone IDs and values are zone data
    if isinstance(zones_data, dict):
        zones = zones_data
    elif isinstance(zones_data, list):
        zones = {str(i): zone for i, zone in enumerate(zones_data)}
    else:
        print("Unexpected zones.json format")
        return []
    
    print(f"Found {len(zones)} zones/games in API")
    
    # Process each zone
    for zone_id, zone_data in zones.items():
        # Extract zone information
        if isinstance(zone_data, dict):
            name = zone_data.get('name') or zone_data.get('title') or zone_data.get('zone') or f"Zone {zone_id}"
            author = zone_data.get('author') or zone_data.get('by') or 'Unknown'
            tag = zone_data.get('tag') or zone_data.get('type') or ''
            url_path = zone_data.get('url') or zone_data.get('path') or zone_id
        else:
            name = str(zone_data) if zone_data else f"Zone {zone_id}"
            author = 'Unknown'
            tag = ''
            url_path = zone_id
        
        # Create directory name
        dir_name = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        if not dir_name or len(dir_name) < 2:
            dir_name = f"zone-{zone_id}"
        
        # Check if already exists
        if name.lower() in existing_names or dir_name in existing_dirs:
            print(f"  ⏭ Skipping {name} (already exists)")
            continue
        
        # Construct game URL
        game_url = f"{BASE_URL}#{zone_id}" if zone_id else BASE_URL
        
        # Try to get cover image from covers repository
        cover_url = f"https://cdn.jsdelivr.net/gh/gn-math/covers@main/{zone_id}.png"
        
        game_info = {
            'name': name,
            'directory': dir_name,
            'image': 'cover.png',
            'source': 'non-semag',
            'gameUrl': game_url
        }
        
        # Check if cover image exists
        try:
            cover_check = requests.head(cover_url, headers=HEADERS, timeout=5)
            if cover_check.status_code == 200:
                game_info['imagePath'] = cover_url
        except:
            pass
        
        games.append(game_info)
        print(f"  ✓ Added: {name} (by {author})")
    
    return games

def main():
    print("GN-Math.dev Game Scraper")
    print("=" * 50)
    
    games = scrape_games()
    
    if not games:
        print("\n⚠ No new games found or page structure is different than expected")
        print("You may need to inspect the page structure manually")
        return
    
    # Save to JSON file
    output_file = Path(__file__).parent.parent / "data" / "gn-math-games.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(games, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Found {len(games)} new games")
    print(f"✓ Saved to {output_file}")
    print("\nNext step: Review the games and add them to games.json")

if __name__ == "__main__":
    main()

