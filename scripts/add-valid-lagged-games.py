"""
Add valid Lagged games to games.json
Only adds games that have actual game files (not just iframes to game sites)
"""
import json
from pathlib import Path
import re

def check_game_valid(game_dir):
    """Check if a game is valid (has game files, not just iframe to game site)"""
    if not game_dir.exists():
        return False
    
    index_html = game_dir / 'index.html'
    if not index_html.exists():
        return False
    
    html_content = index_html.read_text(encoding='utf-8')
    
    # Check if it's just an iframe to a game site (bad)
    bad_iframe_patterns = [
        r'iframe.*lagged\.com',
        r'iframe.*crazygames',
        r'iframe.*kongregate',
        r'iframe.*gamejolt',
        r'iframe.*itch\.io'
    ]
    
    for pattern in bad_iframe_patterns:
        if re.search(pattern, html_content, re.I):
            return False
    
    # Check if it has game files (good)
    has_js = any(game_dir.rglob('*.js'))
    has_swf = any(game_dir.rglob('*.swf'))
    has_wasm = any(game_dir.rglob('*.wasm'))
    has_data = any(game_dir.rglob('*.data'))
    
    # Has game files = valid
    if has_js or has_swf or has_wasm or has_data:
        return True
    
    # Check if it references external CDNs (also valid per user)
    external_cdn_patterns = [
        r'gacembed\.withgoogle\.com',
        r'jsdelivr\.net',
        r'unpkg\.com',
        r'cdnjs\.cloudflare\.com'
    ]
    
    for pattern in external_cdn_patterns:
        if re.search(pattern, html_content, re.I):
            return True
    
    return False

def main():
    games_list_file = Path('lagged-games-list.json')
    games_json_path = Path('data/games.json')
    non_semag_dir = Path('non-semag')
    
    if not games_list_file.exists():
        print("❌ lagged-games-list.json not found")
        return
    
    print("🎮 Adding Valid Lagged Games\n" + "="*50 + "\n")
    
    # Load games list
    with open(games_list_file, 'r', encoding='utf-8') as f:
        games_list = json.load(f)
    
    # Load existing games
    with open(games_json_path, 'r', encoding='utf-8') as f:
        existing_games = json.load(f)
    
    existing_directories = {g.get('directory', '').lower() for g in existing_games}
    
    # Check each game
    valid_games = []
    skipped = []
    
    for game in games_list:
        if game.get('status') != 'success':
            continue
        
        slug = game.get('slug', '')
        if not slug:
            continue
        
        # Skip if already exists
        if slug.lower() in existing_directories:
            skipped.append(f"{slug} (already exists)")
            continue
        
        game_dir = non_semag_dir / slug
        
        if check_game_valid(game_dir):
            game_name = game.get('name', slug.replace('-', ' ').title())
            # Remove " Game" suffix if present
            if game_name.endswith(' Game'):
                game_name = game_name[:-5]
            
            valid_games.append({
                "name": game_name,
                "directory": slug,
                "image": "cover.png",
                "source": "non-semag"
            })
            print(f"  ✓ {slug}")
        else:
            skipped.append(f"{slug} (no game files or iframe)")
    
    # Add valid games to games.json
    if valid_games:
        existing_games.extend(valid_games)
        
        with open(games_json_path, 'w', encoding='utf-8') as f:
            json.dump(existing_games, f, indent='\t', ensure_ascii=False)
        
        print(f"\n✅ Added {len(valid_games)} games to games.json")
    else:
        print("\n⚠️  No valid games to add")
    
    if skipped:
        print(f"\n⏭️  Skipped {len(skipped)} games:")
        for item in skipped[:10]:  # Show first 10
            print(f"    - {item}")
        if len(skipped) > 10:
            print(f"    ... and {len(skipped) - 10} more")

if __name__ == "__main__":
    main()

