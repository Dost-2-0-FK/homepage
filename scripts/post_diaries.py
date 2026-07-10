import json
import os
import os
import roman
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

name_username_mapping = {}
for file in PATH_TO_TXTAD_CHARS.glob("*.ctx"):
    with open(file, "r") as f:
        ctx = json.load(f)
        print(ctx["name"])
        name_username_mapping[ctx["name"]] = ctx["attributes"]["username"]


def parse_date(date: str) -> str: 
    year = int(date[:date.find("-")])
    rest = date[date.find("-")+1:]
    rest = rest.replace("-", ".")
    if year > 2043: 
        return f"[{roman.toRoman(year-2043)}.{rest} NnZ]"
    else:
        return f"[{year}.{rest} VuZ]"


def get_username(key: str) -> str:
    with open(PATH_TO_TXTAD_CHARS.joinpath(f"{key}.ctx"), "r") as f:
        ctx = json.load(f)
    return ctx["attributes"]["username"]

def get_username_from_name(name: str) -> str|None: 
    if name in name_username_mapping: 
        return name_username_mapping[name]
    if "," in name: 
        for n, un in name_username_mapping.items(): 
            if name[:name.find(",")] in n and name[name.find(",") +2:] in n: 
                print("- found ", n, " instead")
                return un

    print(f"no username for name: {name}")
    exit("Failed!")

if __name__ == "__main__": 
    for name, conf in diaryer.config.items(): 
        found = False
        for diary in diaryer.diaries:
            if name == diary.name: 
                print("Handling: ", name, type(diary))
                diaryer.run_config(diary)
                found = True
        if not found: 
            print("diaries have missing name: ", name)

    print("CONFIG APPLIED SUCCESSFULLY", name)
    
    messages = []
    for diary in diaryer.diaries:
        username = get_username(diary.key)
        new_msg = MSG_FORMAT_JSON.copy() 
        new_msg["recipients"] = [username]
        new_msg["text"] = '''ACHTUNG! Sehr geehrte Nutzerin, aufgrund eines
        sicherheitsrelevanten Vorfalls mit unautorisiertem Systemzugriff musste
        eine Wiederherstellung aus einem Backup durchgeführt werden.
        Infolgedessen kam es zu temporären Inkonsistenzen und Datenlücken
        innerhalb der Speicheradressierung.

        Die betroffenen, zuvor gelöschten Speicheradressen konnten inzwischen mittels
        algorithmischer Interpolation rekonstruiert und in die Datenstruktur
        reintegriert werden.'''
        messages.append(new_msg)

        for entry in diary.entries: 
            new_msg = MSG_FORMAT_JSON.copy() 
            new_msg["recipients"] = [username]
            new_msg["text"] = f"{parse_date(entry.date)} {entry.entry}"
            messages.append(new_msg)
            for chat in entry.chats: 
                if len(chat.people) == 2: 
                    for msg in chat.messages:
                        new_msg = MSG_FORMAT_JSON.copy() 
                        new_msg["recipients"] = [
                            get_username_from_name(u) 
                            for u in chat.people 
                            if u != msg.name
                        ]
                        new_msg["text"] = f"{parse_date(entry.date)} {msg.message}"
                        new_msg["username"] = get_username_from_name(msg.name)
                        messages.append(new_msg)
                    print(f"Adding CHAT with {len(chat.people)} people")
                else: 
                    print("Number of people not 2:", len(chat.people))

        new_msg = MSG_FORMAT_JSON.copy() 
        new_msg["recipients"] = [username]
        new_msg["text"] = '''ACHTUNG! Sehr geehrte Nutzerin, aufgrund eines
        sicherheitsrelevanten Vorfalls mit unautorisiertem Systemzugriff musste
        eine Wiederherstellung aus einem Backup durchgeführt werden.
        Infolgedessen kam es zu temporären Inkonsistenzen und Datenlücken
        innerhalb der Speicheradressierung.

        Die betroffenen, zuvor gelöschten Speicheradressen konnten inzwischen mittels
        algorithmischer Interpolation rekonstruiert und in die Datenstruktur
        reintegriert werden.'''
        messages.append(new_msg)


    # Store prepared messages
    with open(PATH_TO_PLEROMA_POSTS_JSON, 'w') as f:
        json.dump(messages, f)
