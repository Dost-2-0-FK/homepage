from pathlib import Path
import json
import os
from typing import Any, Dict, List

TXTAD_PATH = "/srv/txtad-data/"
DOST_PATH = "/usr/bin/dost/homepage/"

PATH_TO_TXTAD_CHARS = Path(TXTAD_PATH, "dost/game_files/Characters/")
PATH_TO_USER_JSONS = "resources/accounts.json"

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
    account["password"] = data["attributes"]["pub_key"] 
    account["fullname"] = data["name"]
    account["bio"] = data["attributes"]["zone"]
    return account.copy()

if __name__ == "__main__": 
    chars = []
    for file in PATH_TO_TXTAD_CHARS.glob("*.ctx"):
        with open(file, "r") as f:
            data = json.load(f)
            if "attributes" not in data or "priv" not in data["attributes"]:
                print("Skipping ", data["id"])
                continue 
            chars.append(transform(data))

    with open(PATH_TO_USER_JSONS, 'w') as f:
        json.dump(chars, f)
