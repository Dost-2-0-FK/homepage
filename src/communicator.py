import copy 
import json
from typing import Dict, List

class CommUser: 
    def __init__(self, mail: str, collective: str, hidden: List[str]) -> None:
        self.mail = mail 
        self.collective = collective
        self.hidden = hidden

class Comm: 
    def __init__(self) -> None:
        with open("resources/communicate.json", "r") as f: 
            j = json.load(f)
            collectives = j["collectives"]
            self.users = j["users"]
        self.collectives = {}
        for mail, collective in collectives.items(): 
            if [v for v in self.users.values() if mail in v]:
                self.collectives[mail] = copy.deepcopy(collective)
                self.collectives[mail]["members"] = []
            else: 
                continue
            if "members" in collective: 
                for member in collective["members"]: 
                    if [v for v in self.users.values() if member in v]:
                        self.collectives[mail]["members"].append(member)

    def get_user(self, email: str) -> CommUser | None: 
        if email not in self.users: 
            return None
        alias = self.users[email]
        if "." in alias: 
            collective = alias[alias.find(".")+1:]
            mail = alias
        else: 
            collective = alias 
            mail = alias
        print(alias, collective, mail)
        hidden = self.collectives[collective].get("hide") or []
        return CommUser(mail, collective, hidden)
