import json
import os
import os
from scripts.pdf_gen import render_pdf
from dataclasses import dataclass
from typing import Any, Dict, List
from pathlib import Path

from src.communicator import Comm
from src.seafiler import Seafile
from src.user_manager import UManager
from src.mailer import Mailer

TXTAD_PATH = "/srv/txtad-data/"
DOST_PATH = "/usr/bin/dost/homepage/"

PATH_TO_TXTAD_CHARS = Path(TXTAD_PATH, "dost/game_files/Characters/")
PATH_TO_DOST_CHARS = Path(DOST_PATH, "data/file/")
PATH_TO_DOST_PLAYERS = Path(DOST_PATH, "data/")

PATH_TO_DISTRIBUTION = Path("resources/character_zuteilung.json")

comm = Comm()
seafiler = Seafile(os.getenv("USE_SEAFILE", "False") == "True")
umanger = UManager(seafiler)
mailer = Mailer()

@dataclass 
class Fraction: 
    primary: str 
    secondary: str|None

def get_player(key: str) -> Dict[str, str]: 
    with open(PATH_TO_DOST_PLAYERS.joinpath(f"{key}.json"), "r") as f:
        player = json.load(f)

    if not player: 
        exit(f"Failed getting player with key: {key}")

    return {
        "key": key, 
        "email": player["email"],
        "name": player["name"] 
    }


def get_fraktion_from_tags(username: str, block: str, tags: List[str]) -> Fraction: 
    if block == "NEUTRAL": 
        if username == "paul_nierendorf":
            return Fraction("", "gräber") 
        primary = "lilie" 
        if "gräber" in tags:
            return Fraction(primary, "gräber") 
        return Fraction(primary, "") 

    if block == "WEST": 
        if "West:Fundamentalisten" in tags: 
            return Fraction("fundamentalisten", "")
        if "West:Gemäßigte" in tags: 
            return Fraction("gemäßigte", "")
        if "West:Atheisten" in tags: 
            return Fraction("atheisten", "")
        print(f"{key} ist part of WEST but has no fraction: {tags}")
        return Fraction("", "")

    if block == "PARCA": 
        if "Parca:Dogmatiker" in tags: 
            return Fraction("dogmatiker", "")
        if "Parca:Pragmatiker" in tags: 
            primary = "pragmatiker"
            if "Parca:Pragmatiker-ULTRAS" in tags:
                return Fraction(primary, "ultras")
            return Fraction(primary, "")
        print(f"{key} ist part of PARCA but has no fraction: {tags}")

    print(f"{key} has no block!")
    return Fraction("", "")

def get_char_and_creator(key: str) -> Tuple[Dict[str, str], Dict[str, str]]: 
    with open(PATH_TO_DOST_CHARS.joinpath(f"{key}.json"), "r") as f:
        char_json = json.load(f)
    with open(PATH_TO_TXTAD_CHARS.joinpath(f"{key}.ctx"), "r") as f:
        ctx_json = json.load(f)

    if not char_json: 
        exit(f"Failed getting char-json with key: {key}")
    if not ctx_json: 
        exit(f"Failed getting ctx-json with key: {key}")

    # Build char
    username = ctx_json["attributes"]["username"]
    block = ctx_json["attributes"]["block"]
    tags = char_json["_tags"] if "_tags" in char_json else []
    char = {
        "key": key, 
        "pub_key": ctx_json["attributes"]["pub_key"], 
        "name": ctx_json["attributes"]["name"], 
        "username": username, 
        "block": block, 
        "fraction": get_fraktion_from_tags(username, block, tags)
    }

    # Build creator
    creator_key = char_json["_creator"]
    creator_user = umanger.get_user(creator_key)
    creator_comm = comm.get_user(creator_user.email)

    mail = f"{creator_comm.mail}@dost-2-0-fk.art"
    alias = creator_comm.alias 
    if "." in creator_comm.alias: 
        alias = alias[:alias.find(".")]

    creator = {
        "key": creator_key, 
        "email": mail, 
        "alias": alias
    }

    return (char, creator)

def do_distribution(distribution: List[Dict[str, str]]) -> None: 
    for dist in distribution: 
        player_key = dist["player"]
        char_key = dist["character"]
        player = get_player(player_key) 
        char, creator = get_char_and_creator(char_key)
        print("PLAYER:  ", player)
        print("CHAR:    ", char)
        print("CREATOR: ", creator)
        data = {
            "player": player, 
            "char": char, 
            "creator": creator
        }

        render_pdf(
            "dost.tex", 
            data, 
            f"{player_key}.pdf",
            mailer=mailer,
            to_addr=player["email"], 
            subject="[DOST 2.0 FK] Dein Charakter!",
            text_body=(
                f"Liebe*r {player['name']}, \n"
                "\n"
                "mit großer Freude senden wir dir mit einiger Verzögerung deinen Charakter! \n"
                "Die angehängte PDF enthält einen Tagebucheintrag von unbekannt, der als grobe Beschreibung des Settings dient, die Pleroma-Zugangsdaten deines Charakters (mit diesen erhälst du auf Pleroma deine weitere Charakterbeschreibung) und eine kleine Einordnung der Weltanschauung!\n"
                "Weitere Spielmaterialien werden dich IT über Pleroma erreichen.\n"
                "Die finalen Spielregeln senden wir dir in den nächsten Wochen per Mail zu.\n"
                "\n\n"
                "Liebe Grüße\n"
                "Alex, fux, Hauptmann und das gesammte Dost 2.0 FK Team <3 \n"
            )
        )

if __name__ == "__main__": 
    chars = []
    with open(PATH_TO_DISTRIBUTION, "r") as f:
        do_distribution(json.load(f))
