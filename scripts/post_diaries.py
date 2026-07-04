import json
import os
import os
from scripts.pdf_gen import render_pdf
from dataclasses import dataclass
from typing import Any, Dict, List
from pathlib import Path

from src.communicator import Comm
from src.seafiler import Seafile
from src.secretor import Secretor
from src.user_manager import UManager
from src.diaryer import Diaryer

comm = Comm()
seafiler = Seafile(os.getenv("USE_SEAFILE", "False") == "True")
umanger = UManager(seafiler)
secretor = Secretor(comm, umanger)
diaryer = Diaryer(comm, umanger, secretor)

TXTAD_PATH = "/srv/txtad-data/"
DOST_PATH = "/usr/bin/dost/homepage/"

PATH_TO_TXTAD_CHARS = Path(TXTAD_PATH, "dost/game_files/Characters/")

PATH_TO_PLEROMA_POSTS_JSON = Path("/home/fux/homepage/pleroma/chats.json")

MSG_FORMAT_JSON = {
    "username": "diarybot",
    "text": "",
    "recipients": [ ],
    "media": [],
    "posted": False
}

def get_username(key: str) -> str:
    with open(PATH_TO_TXTAD_CHARS.joinpath(f"{key}.ctx"), "r") as f:
        ctx = json.load(f)
    return ctx["attributes"]["username"]

if __name__ == "__main__": 
    for name, conf in diaryer.config.items(): 
        found = False
        for diary in diaryer.diaries:
            if name == diary.name: 
                print("Handlling: ", name, type(diary))
                diaryer.run_config(diary)
                found = True
        if not found: 
            print("diaries have missing name: ", name)
    print("CONFIG APPLIED SUCCESSFULLY", name)
    
    messages = []
    for diary in diaryer.diaries:
        username = get_username(diary.key)
        if "nierendorf" in username: 
            print("SKIPPED NIERENDORF")
            continue
        else:
            for entry in diary.entries: 
                new_msg = MSG_FORMAT_JSON.copy() 
                new_msg["recipients"] = [username]
                new_msg["text"] = entry.entry
                messages.append(new_msg)

    # Store prepared messages
    with open(PATH_TO_PLEROMA_POSTS_JSON, 'w') as f:
        json.dump(messages, f)
