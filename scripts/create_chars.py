from pathlib import Path
import json
import os
import random
import re
import unicodedata
from typing import Any, Dict, List

from src.communicator import Comm
from src.seafiler import Seafile
from src.user_manager import UManager

TAG_HIDDEN = "hidden: "
TAG_PRESIDENT = "Präsident"
TAG_SECU = "Security"
TAG_INACTIVE = "inactive"

TXTAD_PATH = "/srv/txtad-data/"
# TXTAD_PATH = "/home/fux/homepage/test/"
DOST_PATH = "/usr/bin/dost/homepage/"

PATH_TO_TXTAD_CHARS = Path(TXTAD_PATH, "dost/game_files/Characters/")
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

comm = Comm()
seafiler = Seafile(os.getenv("USE_SEAFILE", "False") == "True")
umanger = UManager(seafiler)

key_bloc_mapping = {}

def create_username(name, surname, max_length=30, separator='_'):
    # Convert to lowercase
    name = name.lower().strip()
    surname = surname.lower().strip()
    
    # Remove diacritics (umlauts, accents, etc.)
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')
    surname = unicodedata.normalize('NFKD', surname).encode('ASCII', 'ignore').decode('utf-8')
    
    # Remove any remaining non-allowed characters
    # Allowed: a-z, 0-9, underscore (_)
    name = re.sub(r'[^a-z0-9_]', '', name)
    surname = re.sub(r'[^a-z0-9_]', '', surname)
    
    # Remove leading/trailing underscores
    name = name.strip('_')
    surname = surname.strip('_')
    
    # Combine name and surname
    if separator == '_':
        username = f"{name}_{surname}"
    elif separator == '-':
        username = f"{name}-{surname}"
    else:  # no separator
        username = f"{name}{surname}"
    
    # Remove multiple consecutive separators
    username = re.sub(r'[_\-]+', separator, username)
    
    # Truncate to max length
    if len(username) > max_length:
        username = username[:max_length]
        # Remove trailing separator if exists
        username = username.rstrip('_-')
    
    # Ensure username isn't empty
    if not username:
        username = "user"
    
    return username

def create_public_key(key: str) -> str: 
    return "pub_" + reorder_key(key)

def create_priv_key(key: str) -> str: 
    base = reorder_key(key)
    return base.split("-")[0]

def reorder_key(key: str) -> str: 
    blocks = key.split("-")
    shuffled_blocks = [
        ''.join(random.sample(block, len(block)))
        for block in blocks
    ]
    return "-".join(shuffled_blocks)

def __calc_aitropie(data) -> int: 
    violence = data["violence_potential"] 
    illnesses = len(data["illnesses"])
    cbis = len(data["computer_brain_interfaces"])
    return __calc_entropie(violence, illnesses, cbis)

def __calc_gen_diff(data) -> int: 
    wealth = -1 * (data["violence_potential"]-5)
    illnesses = len(data["illnesses"])
    gms = len(data["genetic_augmentations"])
    return __calc_entropie(wealth, illnesses, gms)

def __calc_entropie(pos_a: int, pos_b: int, neg: int) -> int:
    return min(max(-3, pos_a + pos_b - neg - random.randint(0,2)), 3)

def __bloc_from_tags_or_creator(tags: List[str], key: str) -> str: 
    if "west" in tags: 
        return "west" 
    if "parca" in tags: 
        return "parca" 
    if "ikac" in tags: 
        return "ikac" 
    if key in key_bloc_mapping: 
        return key_bloc_mapping[key]
    print(f"{key}: missing block tag!")
    user = umanger.get_user(key) 
    if user: 
        comm_user = comm.get_user(user.email)
        if comm_user: 
            collective = comm_user.collective 
            block = collective.split("-")[1] if "-" in collective else collective
            block = "schweiz" if block == "orga" else block
            key_bloc_mapping[key] = block
            return block
        else: 
            exit(f"GET BLOC: no comm-user found for key: {key}, user: {user.email}")
    else: 
        exit(f"GET BLOC: no user found for key: {key}")

def __tags(data: Dict[str, Any]) -> List[str]: 
    if "_tags" in data: 
        return data["_tags"] 
    return []

def transform(data): 
    ctx = JSON_CTX_TEMPLATE 
    key = data["key"]
    ctx["id"] = key
    ctx["name"] = data["sirname"] + ", " + data["name"]
    print("transform: ", ctx["name"])
    ctx["attributes"] = {
        "name": ctx["name"],
        "username": create_username(data["name"], data["sirname"]),
        "key": key,
        "pub_key": create_public_key(key),
        "priv": create_priv_key(key),
        "entropie": str(__calc_aitropie(data)),
        "gen_diff": str(__calc_gen_diff(data)),
        "zone": data["zone"],
        "bloc": __bloc_from_tags_or_creator(data["_tags"], data["_creator"]),
        "president": str(TAG_PRESIDENT in __tags(data)),
        "secu": str(TAG_SECU in __tags(data)),
        "amc_online": "0",
        "amc_bloc": "[]",
        "amc_private": "[]",
        "amc_zone": "[]",
        "inactive": str(TAG_INACTIVE in __tags(data)),
    }
    for tag in __tags(data): 
        if TAG_HIDDEN in tag: 
            ctx["attributes"]["inactive"] = "True"
    return ctx.copy()

def add_contacts(chars: List[Dict[str, Any]]) -> None: 
    for char in chars: 
        print(
            "add_contacts (zone): ", 
            char["name"], 
            f"[{char["attributes"]["president"]}, {char["attributes"]["secu"]}]"
        )
        char["attributes"]["amc_zone"] = str(
            [c["attributes"]["key"] for c in chars 
            if c["attributes"]["zone"] == char["attributes"]["zone"]]
        )

        if char["attributes"]["president"] == "True" or char["attributes"]["secu"] == "True": 
            print("add_contacts (bloc): ", char["name"])
            char["attributes"]["amc_bloc"] = str(
                [c["attributes"]["key"] for c in chars 
                if c["attributes"]["bloc"] == char["attributes"]["bloc"]]
            )
        

def safe_all(chars: List[Dict[str, Any]]) -> None: 
    for char in chars: 
        with open(PATH_TO_TXTAD_CHARS.joinpath(f"{char['id']}.ctx"), 'w') as f:
            json.dump(char, f)

if __name__ == "__main__": 
    chars = []
    for file in PATH_TO_DOST_CHARS.glob("*.json"):
        with open(file, "r") as f:
            chars.append(transform(json.load(f)))
    add_contacts(chars) 
    safe_all(chars)
