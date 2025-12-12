import dataclasses
import json
import os
from dataclasses import dataclass
from typing import Dict, List

SECRET_FILE_PATH = "data/file"

@dataclass 
class SecretFileEntry: 
    key: str
    # Name
    name: str
    sirname: str
    maidenname: str
    # Gender, birth, zone
    gender: str
    dob: str 
    zone: str 
    # Mods
    genetic_augmentations: list[str]
    computer_brain_interfaces: list[str]
    # Violence
    violence_potential: int
    estimated_wealth: int
    # Background
    crimes: list[str]
    employers: list[str]
    background: str
    connections: list[str]
    illnesses: list[str]
    notes: str
    _creator: str
    _published: bool 
    _review: bool

class Secretor: 
    def __init__(self):
        self.secret_file = self.__load_secret_file()

    def users_secret_file_entries(self, creator: str) -> List[SecretFileEntry]: 
        users_entries = []
        for _, entry in self.secret_file.items():
            if entry._creator == creator: 
                users_entries.append(entry) 
        return users_entries 

    def secret_files_in_review(self, collective: str) -> List[SecretFileEntry]: 
        block = collective.split("-")[0] if "-" in collective else collective
        entries = []
        for _, entry in self.secret_file.items():
            if entry._review and (not block or block in entry._creator): 
                entries.append(entry) 
        return entries

    def secret_files(self) -> List[SecretFileEntry]: 
        entries = [] 
        for _, entry in self.secret_file.items(): 
            if entry._published: 
                entries.append(entry) 
        return entries

    def add_secret_file_entry(self, json_str: str): 
        entry = SecretFileEntry(**json.loads(json_str)) 
        self.secret_file[entry.key] = entry 
        self.__save_entry(entry)

    def __save_entry(self, entry: SecretFileEntry): 
        with open(os.path.join(SECRET_FILE_PATH, entry.key), "w") as f: 
            json.dump(dataclasses.asdict(entry), f)

    def __load_secret_file(self) -> Dict[str, SecretFileEntry]: 
        """ Loads secret service files """
        entries = {}
        for filename in os.listdir(SECRET_FILE_PATH): 
            with open(os.path.join(SECRET_FILE_PATH, filename), "r") as f: 
                json_data = json.load(f)
                entries[filename] = SecretFileEntry(**json_data)
        return entries
