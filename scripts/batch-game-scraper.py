import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import re
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import os

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def load_existing_games(games_json_path='data/games.json'):
    """Load existing games from games.json to avoid duplicates"""
    existing_games = {
        'names': set(),
        'directories': set(),
        'urls': set()
    }
    
    try:
        if os.path.exists(games_json_path):
            with open(games_json_path, 'r', encoding='utf-8') as f:
                games = json.load(f)
                
            for game in games:
                name = game.get('name', '').lower().strip()
                if name:
                    existing_games['names'].add(name)
                
                directory = game.get('directory', '').lower().strip()
                if directory:
                    existing_games['directories'].add(directory)
                
                game_url = game.get('gameUrl', '')
                if game_url:
                    # Extract domain and path for comparison
                    parsed = urlparse(game_url)
                    if parsed.path:
                        slug = parsed.path.strip('/').split('/')[-1].lower()
                        if slug:
                            existing_games['urls'].add(slug)
                
        return existing_games
    except Exception as e:
        print(f"⚠️  Warning: Could not load existing games: {e}")
        return existing_games

def game_already_exists(game_name, game_url, existing_games):
    """Check if a game already exists"""
    name_lower = game_name.lower().strip() if game_name else ''
    url_slug = game_url.split('/')[-1].lower().strip() if game_url else ''
    
    if name_lower and name_lower in existing_games['names']:
        return True
    if url_slug and (url_slug in existing_games['directories'] or url_slug in existing_games['urls']):
        return True
    
    return False

def find_game_links(base_url, max_games=50):
    """Find all game links on a page or category page"""
    print(f"🔍 Finding game links on {base_url}...")
    
    try:
        response = requests.get(base_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        game_links = []
        
        # Common patterns for game links
        # Lagged.com pattern
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            # Look for game URLs
            if '/g/' in href or '/games/' in href or '/en/g/' in href:
                full_url = urljoin(base_url, href)
                # Avoid duplicates and non-game pages
                if full_url not in game_links and 'category' not in href.lower():
                    game_links.append(full_url)
        
        # Kongregate pattern
        for link in soup.find_all('a', href=re.compile(r'/games/|/en/games/')):
            href = link.get('href', '')
            full_url = urljoin(base_url, href)
            if full_url not in game_links:
                game_links.append(full_url)
        
        # Filter to unique games and limit
        unique_links = list(set(game_links))[:max_games]
        print(f"✓ Found {len(unique_links)} game links")
        return unique_links
        
    except Exception as e:
        print(f"❌ Error finding game links: {e}")
        return []

def scrape_single_game(game_url, output_base_dir):
    """Scrape a single game - simplified version"""
    try:
        game_name = game_url.split('/')[-1].replace('-', '_').replace(' ', '_')
        game_dir = output_base_dir / game_name
        game_dir.mkdir(exist_ok=True)
        
        print(f"  📥 Scraping: {game_name}")
        
        response = requests.get(game_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        # Save HTML
        (game_dir / "index.html").write_text(response.text, encoding='utf-8')
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find game file URLs (SWF, iframe, etc.)
        game_files = []
        
        # Look for iframes
        for iframe in soup.find_all('iframe', src=True):
            src = urljoin(game_url, iframe['src'])
            if 'game' in src.lower() or 'embed' in src.lower():
                game_files.append(src)
        
        # Look for SWF files in scripts
        for script in soup.find_all('script'):
            if script.string:
                swf_matches = re.findall(r'["\']([^"\']*\.swf[^"\']*)["\']', script.string, re.I)
                for match in swf_matches:
                    full_url = urljoin(game_url, match)
                    game_files.append(full_url)
        
        # Download game files
        downloaded = []
        for file_url in game_files[:3]:  # Limit to first 3 files
            try:
                file_response = requests.get(file_url, headers=HEADERS, timeout=30, stream=True)
                if file_response.status_code == 200:
                    filename = Path(urlparse(file_url).path).name or 'game_file'
                    filepath = game_dir / filename
                    with open(filepath, 'wb') as f:
                        for chunk in file_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    downloaded.append(filename)
            except:
                pass
        
        return {
            'url': game_url,
            'name': game_name,
            'status': 'success',
            'files': downloaded
        }
        
    except Exception as e:
        return {
            'url': game_url,
            'status': 'error',
            'error': str(e)
        }

def batch_scrape(base_url, max_games=10, max_workers=5, output_dir='scraped-games-batch', games_json_path='data/games.json'):
    """Scrape multiple games from a site"""
    print("🎮 Batch Game Scraper\n" + "="*50 + "\n")
    
    # Load existing games
    existing_games = load_existing_games(games_json_path)
    if existing_games['names']:
        print(f"📚 Loaded {len(existing_games['names'])} existing games from games.json")
    
    output_base = Path(output_dir)
    output_base.mkdir(exist_ok=True)
    
    # Step 1: Find game links
    game_links = find_game_links(base_url, max_games * 2)  # Get more to account for duplicates
    
    if not game_links:
        print("❌ No game links found")
        return
    
    # Filter out existing games
    new_game_links = []
    skipped_count = 0
    
    print(f"\n🔍 Checking {len(game_links)} games against existing list...")
    for url in game_links:
        game_slug = url.split('/')[-1]
        if not game_already_exists(None, url, existing_games):
            new_game_links.append(url)
        else:
            skipped_count += 1
    
    if skipped_count > 0:
        print(f"⏭️  Skipped {skipped_count} games that already exist")
    
    if not new_game_links:
        print("✅ All games already exist in your collection!")
        return
    
    print(f"\n📋 Found {len(new_game_links)} new games to scrape")
    print(f"⚙️  Using {max_workers} workers\n")
    
    # Step 2: Scrape games in parallel
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(scrape_single_game, url, output_base): url 
            for url in new_game_links
        }
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if result['status'] == 'success':
                print(f"  ✓ {result['name']}")
            else:
                print(f"  ✗ {result.get('url', 'unknown')}: {result.get('error', 'unknown error')}")
    
    # Step 3: Save summary
    successful = [r for r in results if r['status'] == 'success']
    summary = {
        'base_url': base_url,
        'total_found': len(game_links),
        'skipped_duplicates': skipped_count,
        'new_games_scraped': len(successful),
        'results': results
    }
    
    (output_base / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding='utf-8'
    )
    
    print(f"\n✅ Complete!")
    print(f"📊 New games scraped: {len(successful)}")
    print(f"⏭️  Skipped (duplicates): {skipped_count}")
    print(f"📁 Output directory: {output_base.resolve()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Batch scrape games from a website')
    parser.add_argument('url', help='Base URL or category page URL')
    parser.add_argument('--max-games', type=int, default=10, help='Maximum number of games to scrape (default: 10)')
    parser.add_argument('--workers', type=int, default=5, help='Number of parallel workers (default: 5)')
    parser.add_argument('--output', default='scraped-games-batch', help='Output directory (default: scraped-games-batch)')
    parser.add_argument('--games-json', default='data/games.json', help='Path to games.json (default: data/games.json)')
    
    args = parser.parse_args()
    
    # Try to find games.json relative to script location
    script_dir = Path(__file__).parent.parent
    games_json = script_dir / args.games_json
    
    batch_scrape(args.url, args.max_games, args.workers, args.output, str(games_json))

