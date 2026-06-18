from pathlib import Path
import json
import os
import random
import re
import string
from typing import Any, Dict, List

TXTAD_PATH = "/srv/txtad-data/"
# TXTAD_PATH = "/home/fux/homepage/test/"
DOST_PATH = "/usr/bin/dost/homepage/"

PATH_TO_TXTAD_ZONES = Path(TXTAD_PATH, "dost/game_files/Zones/")
PATH_TO_DOST_CHARS = Path(DOST_PATH, "data/file/")

JSON_CTX_TEMPLATE = {
    "attributes": {
    },
    "description": {
        "logic": "",
        "one_time_events": "",
        "permanent_events": "",
        "shared": False,
        "txt": "."
    },
    "id": "",
    "listeners": [],
    "name": "",
    "permeable": True,
    "priority": 0,
    "re_entrycondition": "",
    "shared": True
}

def create_zone(zone_input):
    """
    Parse a zone input and return structured information.
    
    Args:
        zone_input: Zone identifier string (e.g., "1.A.X", "0.0 (W)", "1.B.17 (E)")
    
    Returns:
        dict: {
            'name': Formatted display name (e.g., "Zone 1.A.X"),
            'username': Mastodon-compatible username (e.g., "zone1ax"),
            'block': Block type ('PARCA', 'WEST', or 'neutral'),
            'valid': Boolean indicating if zone has a block identifier
        }
    """
    # Clean input
    zone = zone_input.strip()
    
    # Handle empty or invalid input
    if not zone or zone == "-":
        return { 'valid': False }
    
    # Extract direction/block from brackets
    direction = ""
    bracket_match = re.search(r'\(([^)]+)\)', zone)
    if bracket_match:
        direction = bracket_match.group(1).upper()
        # Remove bracket part for the number
        zone_number = re.sub(r'\s*\([^)]+\)', '', zone).strip()
    elif zone == "1.A.X":
        zone_number = zone.strip()
        return {
            'name': f"Zone {zone_number}",
            'zone': zone_number,
            'username': f"zone{zone_number.replace('.', '').lower()}",
            'block': "NEUTRAL",
            'valid': True
        }
    else:
        zone_number = zone.strip()
        # Zones without block identifier should be flagged
        return { 'valid': False }
    
    # Remove trailing dot if present
    if zone_number.endswith('.'):
        zone_number = zone_number[:-1]
    
    # Determine block type
    block_map = {
        'E': 'PARCA',
        'W': 'WEST',
        'O': 'PARCA',  # Assuming O is also PARCA based on your example
    }
    
    block_type = block_map.get(direction, 'neutral')
    
    # Generate username (remove dots, convert to lowercase)
    username_base = zone_number.replace('.', '').lower()
    username = f"zone{username_base}{direction.lower()}"
    
    # Clean username (remove any remaining invalid characters)
    username = re.sub(r'[^a-z0-9]', '', username)
    
    return {
        'name': f"Zone {zone_input}",
        'zone': zone_input,
        'username': username,
        'block': block_type,
        'valid': True
    }

def create_key(): 
    def id_part(n): 
        return ''.join(
            random.choices(string.ascii_letters + string.digits, k=n)
        )
    return '-'.join([id_part(4) for _ in range(4)])


def transform_to_ctx(zone_id: str): 
    ctx = JSON_CTX_TEMPLATE 
    key = create_key()
    zone = create_zone(zone_id)
    if not zone["valid"]: 
        print("Skipped zone: ", zone_id)
        return None
    ctx["id"] = key
    ctx["name"] = zone["name"]
    ctx["attributes"] = {
        "key": key,
        "name": zone["name"],
        "username": zone["username"],
        "block": zone["block"],
        "zone": zone["zone"]
    }
    return ctx.copy()

def safe_all(zones: List[Dict[str, Any]]) -> None: 
    for zone in zones: 
        with open(PATH_TO_TXTAD_ZONES.joinpath(f"{zone['id']}.ctx"), 'w') as f:
            json.dump(zone, f)


if __name__ == "__main__": 
    zones = [] 
    for file in PATH_TO_DOST_CHARS.glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)
            if data["zone"] not in zones: 
                zones.append(data["zone"])
    contexts = []
    for zone in zones: 
        print(zone)
        ctx = transform_to_ctx(zone)
        if ctx: 
            print(ctx["name"], ctx["attributes"]["username"])
            contexts.append(ctx.copy()) 
    safe_all(contexts)
