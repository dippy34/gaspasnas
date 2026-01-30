"""
Scrape multiple games from a Lagged.com category page
Example: python scrape-lagged-category.py "https://lagged.com/en/funny" --max-games 20
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
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
                # Normalize game name for comparison
                name = game.get('name', '').lower().strip()
                if name:
                    existing_games['names'].add(name)
                
                # Check directory
                directory = game.get('directory', '').lower().strip()
                if directory:
                    existing_games['directories'].add(directory)
                
                # Check gameUrl for external games
                game_url = game.get('gameUrl', '')
                if game_url:
                    # Extract slug from URL
                    if 'lagged.com' in game_url:
                        slug = game_url.split('/')[-1].lower().strip()
                        if slug:
                            existing_games['urls'].add(slug)
                
        print(f"📚 Loaded {len(existing_games['names'])} existing games from games.json")
        return existing_games
    except Exception as e:
        print(f"⚠️  Warning: Could not load existing games: {e}")
        return existing_games

def game_already_exists(game_slug, game_name, existing_games):
    """Check if a game already exists in games.json"""
    slug_lower = game_slug.lower().strip()
    name_lower = game_name.lower().strip() if game_name else ''
    
    # Check by slug/directory
    if slug_lower in existing_games['directories']:
        return True
    
    # Check by URL slug
    if slug_lower in existing_games['urls']:
        return True
    
    # Check by name (normalized)
    if name_lower and name_lower in existing_games['names']:
        return True
    
    return False

def find_lagged_games(category_url, max_games=20):
    """Find game links from a Lagged category page"""
    print(f"🔍 Finding games on {category_url}...")
    
    try:
        response = requests.get(category_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        game_links = []
        
        # Lagged uses /en/g/ for game pages
        for link in soup.find_all('a', href=re.compile(r'/en/g/')):
            href = link.get('href', '')
            if href and '/en/g/' in href:
                full_url = urljoin(category_url, href)
                if full_url not in game_links:
                    game_links.append(full_url)
        
        # Also check for game thumbnails which link to games
        for thumb in soup.find_all(['div', 'a'], class_=re.compile('thumb|game', re.I)):
            link = thumb.find('a', href=True)
            if link:
                href = link.get('href', '')
                if '/en/g/' in href:
                    full_url = urljoin(category_url, href)
                    if full_url not in game_links:
                        game_links.append(full_url)
        
        unique_links = list(set(game_links))[:max_games]
        print(f"✓ Found {len(unique_links)} game links")
        return unique_links
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def scrape_lagged_game(game_url, existing_games):
    """Scrape a single Lagged game"""
    try:
        game_slug = game_url.split('/')[-1]
        
        response = requests.get(game_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract game name from page
        game_name = None
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text()
            # Remove " - Play on Lagged.com" or similar
            game_name = re.sub(r'\s*[-–—]\s*.*$', '', title_text).strip()
        
        # Check if game already exists
        if game_already_exists(game_slug, game_name, existing_games):
            return {
                'url': game_url,
                'slug': game_slug,
                'name': game_name,
                'status': 'skipped',
                'reason': 'already exists'
            }
        
        print(f"  📥 {game_slug}")
        
        # Find the actual game URL (usually in /games/ruffle/ or similar)
        game_play_url = None
        
        # Look for play button or game iframe
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/games/' in href or '/play/' in href:
                game_play_url = urljoin(game_url, href)
                break
        
        # Look in scripts for game URLs
        if not game_play_url:
            for script in soup.find_all('script'):
                if script.string:
                    matches = re.findall(r'["\']([^"\']*games/[^"\']*)["\']', script.string)
                    if matches:
                        game_play_url = urljoin(game_url, matches[0])
                        break
        
        return {
            'url': game_url,
            'slug': game_slug,
            'name': game_name,
            'play_url': game_play_url,
            'status': 'success'
        }
        
    except Exception as e:
        return {
            'url': game_url,
            'status': 'error',
            'error': str(e)
        }

def scrape_category(category_url, max_games=20, max_workers=5, games_json_path='data/games.json'):
    """Scrape all games from a category"""
    print("🎮 Lagged Category Scraper\n" + "="*50 + "\n")
    
    # Load existing games to avoid duplicates
    existing_games = load_existing_games(games_json_path)
    
    # Find games
    game_links = find_lagged_games(category_url, max_games * 2)  # Get more to account for duplicates
    
    if not game_links:
        print("❌ No games found")
        return
    
    # Filter out games that already exist
    new_game_links = []
    skipped_count = 0
    
    print(f"\n🔍 Checking {len(game_links)} games against existing list...")
    for url in game_links:
        slug = url.split('/')[-1]
        if not game_already_exists(slug, None, existing_games):
            new_game_links.append(url)
        else:
            skipped_count += 1
    
    if skipped_count > 0:
        print(f"⏭️  Skipped {skipped_count} games that already exist")
    
    if not new_game_links:
        print("✅ All games already exist in your collection!")
        return
    
    print(f"\n📋 Scraping {len(new_game_links)} new games...\n")
    
    # Scrape in parallel
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_lagged_game, url, existing_games): url for url in new_game_links}
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if result['status'] == 'success':
                print(f"  ✓ {result['slug']}")
            elif result['status'] == 'skipped':
                print(f"  ⏭️  {result['slug']} (already exists)")
            else:
                print(f"  ✗ Error: {result.get('error', 'unknown')}")
    
    # Save results
    output_file = Path('lagged-games-list.json')
    output_file.write_text(json.dumps(results, indent=2), encoding='utf-8')
    
    successful = [r for r in results if r['status'] == 'success']
    skipped = [r for r in results if r['status'] == 'skipped']
    print(f"\n✅ Complete!")
    print(f"📊 New games found: {len(successful)}")
    print(f"⏭️  Skipped (duplicates): {len(skipped)}")
    print(f"📁 Saved to: {output_file.resolve()}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python scrape-lagged-category.py <category_url> [--max-games N] [--workers N]")
        print("Example: python scrape-lagged-category.py 'https://lagged.com/en/funny' --max-games 20")
        sys.exit(1)
    
    category_url = sys.argv[1]
    max_games = 20
    max_workers = 5
    
    # Parse optional arguments
    if '--max-games' in sys.argv:
        idx = sys.argv.index('--max-games')
        if idx + 1 < len(sys.argv):
            max_games = int(sys.argv[idx + 1])
    
    if '--workers' in sys.argv:
        idx = sys.argv.index('--workers')
        if idx + 1 < len(sys.argv):
            max_workers = int(sys.argv[idx + 1])
    
    # Try to find games.json relative to script location
    script_dir = Path(__file__).parent.parent
    games_json = script_dir / 'data' / 'games.json'
    
    scrape_category(category_url, max_games, max_workers, str(games_json))

