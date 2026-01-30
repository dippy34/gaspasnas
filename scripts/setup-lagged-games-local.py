"""
Download and set up Lagged games locally
Reads from lagged-games-list.json and sets up games in non-semag directory
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
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"    ✗ Failed to download {url}: {e}")
        return False

def setup_lagged_game(game_data, non_semag_dir):
    """Set up a single Lagged game locally"""
    slug = game_data.get('slug', '')
    game_url = game_data.get('url', '')
    play_url = game_data.get('play_url', '')
    game_name = game_data.get('name', slug)
    
    if not slug:
        return {'status': 'error', 'error': 'No slug provided'}
    
    print(f"  📦 Setting up: {slug}")
    
    # Create game directory
    game_dir = non_semag_dir / slug
    game_dir.mkdir(exist_ok=True)
    
    # Try to get the play URL if we have it
    if not play_url and game_url:
        try:
            response = requests.get(game_url, headers=HEADERS, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for game iframe or play button
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '/games/' in href:
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
        except:
            pass
    
    # If we have a play URL, fetch the game page
    if play_url:
        try:
            response = requests.get(play_url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            game_html = response.text
            soup = BeautifulSoup(game_html, 'html.parser')
            
            # Look for SWF files
            swf_files = []
            for script in soup.find_all('script'):
                if script.string:
                    swf_matches = re.findall(r'["\']([^"\']*\.swf[^"\']*)["\']', script.string, re.I)
                    for match in swf_matches:
                        full_url = urljoin(play_url, match)
                        swf_files.append(full_url)
            
            # Download SWF files
            for swf_url in swf_files[:1]:  # Download first SWF
                filename = Path(urlparse(swf_url).path).name
                if filename:
                    swf_path = game_dir / filename
                    if download_file(swf_url, swf_path):
                        print(f"    ✓ Downloaded: {filename}")
            
            # Create index.html with Ruffle
            create_ruffle_html(game_dir, swf_files, game_name)
            
        except Exception as e:
            print(f"    ⚠️  Could not fetch play URL: {e}")
            # Create a basic external game HTML
            create_external_html(game_dir, play_url or game_url, game_name)
    else:
        # No play URL, create external game HTML
        create_external_html(game_dir, game_url, game_name)
    
    # Try to get a cover image
    try:
        response = requests.get(game_url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for og:image or game thumbnail
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            img_url = urljoin(game_url, og_image['content'])
            cover_path = game_dir / 'cover.png'
            if download_file(img_url, cover_path):
                print(f"    ✓ Downloaded cover image")
    except:
        pass
    
    return {
        'status': 'success',
        'slug': slug,
        'directory': slug,
        'name': game_name
    }

def create_ruffle_html(game_dir, swf_files, game_name):
    """Create HTML file with Ruffle to play SWF"""
    swf_file = swf_files[0].split('/')[-1] if swf_files else None
    
    if not swf_file:
        create_external_html(game_dir, None, game_name)
        return
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{game_name}</title>
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            overflow: hidden;
            background: #000;
        }}
        #container {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        ruffle-player {{
            width: 100%;
            height: 100%;
            max-width: 100vw;
            max-height: 100vh;
        }}
    </style>
    <script src="https://unpkg.com/@ruffle-rs/ruffle@latest"></script>
    <script>
        window.RufflePlayer = window.RufflePlayer || {{}};
        window.RufflePlayer.config = {{
            "polyfills": true,
            "letterbox": "on",
            "autoplay": "on",
            "upgradeToHttps": true,
            "showSwfDownload": false,
            "menu": false,
            "contextMenu": "off",
            "scale": "exactfit",
            "forceScale": true,
            "openUrlMode": "deny",
            "splashScreen": false,
            "warnOnUnsupportedContent": false
        }};

        window.addEventListener("load", (event) => {{
            const ruffle = window.RufflePlayer.newest();
            const player = ruffle.createPlayer();
            const container = document.getElementById("container");
            container.appendChild(player);
            player.style.width = "100%";
            player.style.height = "100%";
            player.load({{
                url: "{swf_file}",
                allowScriptAccess: false
            }}).then(() => {{
                console.info("Game file loaded");
            }}).catch((e) => {{
                console.error("Error loading game file", e);
            }});
        }});
    </script>
</head>
<body>
    <div id="container"></div>
</body>
</html>"""
    
    (game_dir / 'index.html').write_text(html_content, encoding='utf-8')

def create_external_html(game_dir, game_url, game_name):
    """Create HTML that loads game from external URL"""
    if not game_url:
        game_url = "https://lagged.com"
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{game_name}</title>
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            overflow: hidden;
            background: #000;
        }}
        iframe {{
            width: 100%;
            height: 100vh;
            border: none;
        }}
    </style>
</head>
<body>
    <iframe src="{game_url}" allowfullscreen></iframe>
</body>
</html>"""
    
    (game_dir / 'index.html').write_text(html_content, encoding='utf-8')

def add_to_games_json(games_data, games_json_path):
    """Add games to games.json"""
    try:
        with open(games_json_path, 'r', encoding='utf-8') as f:
            existing_games = json.load(f)
        
        added_count = 0
        for game_data in games_data:
            if game_data['status'] != 'success':
                continue
            
            slug = game_data['directory']
            name = game_data['name']
            
            # Check if already exists
            exists = any(g.get('directory') == slug for g in existing_games)
            if exists:
                continue
            
            # Add new game
            new_game = {
                "name": name,
                "directory": slug,
                "image": "cover.png",
                "source": "non-semag"
            }
            existing_games.append(new_game)
            added_count += 1
        
        # Save updated games.json
        with open(games_json_path, 'w', encoding='utf-8') as f:
            json.dump(existing_games, f, indent='\t', ensure_ascii=False)
        
        print(f"\n✅ Added {added_count} games to games.json")
        return added_count
    except Exception as e:
        print(f"❌ Error updating games.json: {e}")
        return 0

def main():
    import sys
    
    games_list_file = Path('lagged-games-list.json')
    non_semag_dir = Path('non-semag')
    games_json_path = Path('data/games.json')
    
    if not games_list_file.exists():
        print(f"❌ {games_list_file} not found. Run scrape-lagged-category.py first.")
        return
    
    print("🎮 Setting up Lagged games locally\n" + "="*50 + "\n")
    
    # Load games list
    with open(games_list_file, 'r', encoding='utf-8') as f:
        games_list = json.load(f)
    
    successful_games = [g for g in games_list if g.get('status') == 'success']
    
    if not successful_games:
        print("❌ No successful games to set up")
        return
    
    print(f"📋 Setting up {len(successful_games)} games...\n")
    
    # Set up games
    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(setup_lagged_game, game, non_semag_dir): game 
            for game in successful_games
        }
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if result.get('status') == 'success':
                print(f"  ✓ {result['slug']}")
    
    # Add to games.json
    successful = [r for r in results if r.get('status') == 'success']
    if successful:
        add_to_games_json(successful, games_json_path)
    
    print(f"\n✅ Complete! Set up {len(successful)}/{len(successful_games)} games locally")

if __name__ == "__main__":
    main()

