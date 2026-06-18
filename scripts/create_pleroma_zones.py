from pathlib import Path
import json
import os
import random
import re
import string
from typing import Any, Dict, List

TXTAD_PATH = "/srv/txtad-data/"
DOST_PATH = "/usr/bin/dost/homepage/"

PATH_TO_TXTAD_ZONES = Path(TXTAD_PATH, "dost/game_files/Zones/")
PATH_TO_USER_JSONS = "pleroma/zone_accounts.json"

JSON_ACCOUNT_TEMPLATE = {
    "username": "bob",
    "email": "bob@example.com",
    "password": "change-me-please-2",
    "fullname": "Bob Example",
    "bio": "Bob's bio"
}

def transform(data): 
    account = JSON_ACCOUNT_TEMPLATE 
    account["username"] = data["attributes"]["username"] 
    account["email"] = data["attributes"]["username"] + "@dost-2-0-fk.at"
    account["password"] = data["attributes"]["key"] 
    account["fullname"] = data["name"]
    account["bio"] = f"{data['attributes']['block']} | {data['name']}"
    return account.copy()

if __name__ == "__main__": 
    zones = [] 
    for file in PATH_TO_TXTAD_ZONES.glob("*.ctx"):
        with open(file, "r") as f:
            data = json.load(f)
            zones.append(transform(data))

    with open(PATH_TO_USER_JSONS, 'w') as f:
        json.dump(zones, f)
