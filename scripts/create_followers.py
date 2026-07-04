from pathlib import Path
import json
import os
import random
import re
import unicodedata
from typing import Any, Dict, List

TXTAD_PATH = "/srv/txtad-data/"
DOST_PATH = "/usr/bin/dost/homepage/"

PATH_TO_TXTAD_CHARS = Path(TXTAD_PATH, "dost/game_files/Characters/")
PATH_TO_DOST_CHARS = Path(DOST_PATH, "data/file/")

PATH_TO_FOLLOWER_JSONS = "pleroma/followers.json"

def __tags(data: Dict[str, Any]) -> List[str]: 
    if "_tags" in data: 
        return data["_tags"] 
    return []

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

def get_connection_username(connection: str) -> str: 
    try: 
        with open(PATH_TO_TXTAD_CHARS.joinpath(f"{connection}.ctx"), 'r') as f:
            ctx = json.load(f)
            return ctx["attributes"]["username"]
    except: 
        return None

def create_followers(char, ctx): 
    followers = [] 
    followers.append("parca")
    followers.append("ikac")
    followers.append("west_aeterna")
    followers.append("ai_leaks")

    if ctx["attributes"]["block"] == "NEUTRAL": 
        followers.append("IKAC")
        followers.append("FSB")
        if ctx["attributes"]["username"] not in ["kim_sokolow", "anja_markova", "mara_kessler", "mika_sorin"]:
            followers.append("metabolic_infrastructure")

    if ctx["attributes"]["block"] == "PARCA": 
        followers.append("free_gazette")
        followers.append("morgenlinie")
        followers.append("erscheinungsbilder_ost")
        followers.append("parca")
        followers.append("zone00e")

    if ctx["attributes"]["block"] == "WEST": 
        followers.append("transatlantic_genetic_meritocratic_society_tgms")
        followers.append("stiftung_wissenschaft_politik_swp")
        followers.append("ODeM")

    if ctx["attributes"]["block"] == "PARCA" and ctx["attributes"]["zone"].startswith("1.A."): 
        followers.append("secondarydamage")

    if "Parca:Dogmatiker" in __tags(char): 
        followers.append("huaxia")
    if "Parca:Pragmatiker" in __tags(char): 
        followers.append("synergie")

    if "West:Fundamentalisten" in __tags(char): 
        followers.append("soldatendesherren")
    if "West:Gemäßigte" in __tags(char): 
        followers.append("marienotriemere")
    if "West:Atheisten" in __tags(char): 
        followers.append("theCOLDroom")
    if "West:Paradisten" in __tags(char): 
        followers.append("aiinparadise")

    zone_infos = create_zone(ctx["attributes"]["zone"])
    if zone_infos["valid"]: 
        followers.append(zone_infos["username"])

    for connection in char["connections"]: 
        connection_username = get_connection_username(connection)
        if connection_username:
            followers.append(connection_username)

    return {
        "username": ctx["attributes"]["username"],
        "follows": followers 
    }

if __name__ == "__main__": 
    chars = []
    for file in PATH_TO_DOST_CHARS.glob("*.json"):
        char = None 
        with open(file, "r") as f:
            char = json.load(f)
        with open(PATH_TO_TXTAD_CHARS.joinpath(f"{char['key']}.ctx"), 'r') as f:
            ctx = json.load(f)
        chars.append(create_followers(char, ctx))
    
    with open(PATH_TO_FOLLOWER_JSONS, 'w') as f:
        json.dump(chars, f)
