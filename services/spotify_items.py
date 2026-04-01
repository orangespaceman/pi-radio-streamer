import os
import json
import logging
import re

# File path for storing Spotify items
SPOTIFY_ITEMS_FILE = "config/spotify_items.json"

def ensure_dir_exists():
    """Ensure the config directory exists"""
    os.makedirs(os.path.dirname(SPOTIFY_ITEMS_FILE), exist_ok=True)

def normalize_spotify_uri(uri):
    """Convert various Spotify URI formats to a consistent format"""
    # Already a Spotify URI
    if uri.startswith('spotify:'):
        return uri

    # Web URL format: https://open.spotify.com/playlist/37i9dQZF1DX4sWSpwq3LiO
    match = re.search(r'open\.spotify\.com/(playlist|album|track)/([a-zA-Z0-9]+)', uri)
    if match:
        item_type, item_id = match.groups()
        return f"spotify:{item_type}:{item_id}"

    # Plain ID - assume it's a playlist if no prefix
    if re.match(r'^[a-zA-Z0-9]+$', uri):
        return f"spotify:playlist:{uri}"

    # Invalid format
    return None

def get_items():
    """Load Spotify items from the JSON file"""
    ensure_dir_exists()

    try:
        if os.path.exists(SPOTIFY_ITEMS_FILE):
            with open(SPOTIFY_ITEMS_FILE, 'r') as f:
                return json.load(f)
        else:
            # Return empty list if file doesn't exist
            return []
    except Exception as e:
        logging.error(f"Error loading Spotify items: {e}")
        return []

def save_items(items):
    """Save Spotify items to the JSON file"""
    ensure_dir_exists()

    try:
        with open(SPOTIFY_ITEMS_FILE, 'w') as f:
            json.dump(items, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error saving Spotify items: {e}")
        return False

def add_item(name, uri):
    """Add a new Spotify item"""
    # Normalize the URI
    normalized_uri = normalize_spotify_uri(uri)
    if not normalized_uri:
        return False, "Invalid Spotify URI format"

    items = get_items()

    # Check if an item with this URI already exists
    for item in items:
        if item.get('uri') == normalized_uri:
            return False, "An item with this URI already exists"

    # Add the new item
    items.append({
        'name': name,
        'uri': normalized_uri
    })

    if save_items(items):
        return True, "Item added successfully"
    else:
        return False, "Failed to save item"

def update_item(item_id, name, uri):
    """Update an existing Spotify item"""
    # Normalize the URI
    normalized_uri = normalize_spotify_uri(uri)
    if not normalized_uri:
        return False, "Invalid Spotify URI format"

    items = get_items()

    # Check if the index is valid
    if item_id < 0 or item_id >= len(items):
        return False, "Invalid item ID"

    # Update the item
    items[item_id] = {
        'name': name,
        'uri': normalized_uri
    }

    if save_items(items):
        return True, "Item updated successfully"
    else:
        return False, "Failed to save changes"

def delete_item(item_id):
    """Delete a Spotify item"""
    items = get_items()

    # Check if the index is valid
    if item_id < 0 or item_id >= len(items):
        return False, "Invalid item ID"

    # Remove the item
    items.pop(item_id)

    if save_items(items):
        return True, "Item deleted successfully"
    else:
        return False, "Failed to delete item"

def get_item_uris():
    """Get a list of all Spotify URIs for use in random playback"""
    return [item.get('uri') for item in get_items() if item.get('uri')]