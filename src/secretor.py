import dataclasses
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List

SECRET_FILE_PATH = "data/file"

@dataclass 
class SecretFileEntry: 
    key: str = field(default="")
    # Name
    name: str = field(default="")
    sirname: str = field(default="")
    maidenname: str = field(default="")
    # Gender, birth, zone
    gender: str = field(default="")
    dob: str = field(default="")
    dob_zr: str = field(default="")
    zone: str = field(default="")
    # Mods
    genetic_augmentations: list[str] = field(default_factory=lambda: [''])
    computer_brain_interfaces: list[str] = field(default_factory=lambda: [''])
    # Violence
    violence_potential: int = field(default=0)
    estimated_wealth: int = field(default=0)
    # Background
    crimes: list[str] = field(default_factory=lambda: [''])
    employers: list[str] = field(default_factory=lambda: [''])
    background: str = field(default="")
    connections: list[str] = field(default_factory=lambda: [''])
    illnesses: list[str] = field(default_factory=lambda: [''])
    notes: str = field(default="")
    _creator: str = field(default="")
    _published: bool = field(default=False)
    _review: bool = field(default=False)

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
            if entry._review and (not block or block in entry._creator or collective == "orga"): 
                entries.append(entry) 
        return entries

    def secret_files(self) -> List[SecretFileEntry]: 
        entries = [] 
        for _, entry in self.secret_file.items(): 
            if entry._published: 
                entries.append(entry) 
        return entries

    def get_secret_file_entry(self, key: str) -> SecretFileEntry: 
        if key in self.secret_file: 
            return self.secret_file[key]
        return SecretFileEntry()

    def add_secret_file_entry(self, entry: SecretFileEntry): 
        self.secret_file[entry.key] = entry 
        self.__save_entry(entry)

    def review_secret_file_entry(self, key: str) -> bool: 
        if key in self.secret_file: 
            self.secret_file[key]._review = True 
            self.__save_entry(self.secret_file[key]) 
            return True 
        return False

    def __save_entry(self, entry: SecretFileEntry): 
        with open(f"{os.path.join(SECRET_FILE_PATH, entry.key)}.json", "w") as f: 
            json.dump(dataclasses.asdict(entry), f)

    def __load_secret_file(self) -> Dict[str, SecretFileEntry]: 
        """ Loads secret service files """
        entries = {}
        for filename in os.listdir(SECRET_FILE_PATH): 
            with open(os.path.join(SECRET_FILE_PATH, filename), "r") as f: 
                json_data = json.load(f)
                entries[os.path.splitext(filename)[0]] = SecretFileEntry(**json_data)
        return entries
