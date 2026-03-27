import dataclasses
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

SECRET_FILE_PATH = "data/file"
LIST_PATH = "data/lists/"
CBI_PATH = os.path.join(LIST_PATH, "cbis.json")
GM_PATH = os.path.join(LIST_PATH, "gms.json")

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

@dataclass 
class Abbr: 
    abbr: str
    name: str
    desc: str 
    _creator: str 

class Secretor: 
    def __init__(self, comm, umanager):
        if not os.path.exists(SECRET_FILE_PATH):
            os.makedirs(SECRET_FILE_PATH)
        if not os.path.exists(LIST_PATH):
            os.makedirs(LIST_PATH)
        self.secret_file = self.__load_secret_file()
        self.gms = self.__load_list(GM_PATH)
        self.cbis = self.__load_list(CBI_PATH)
        self.comm = comm 
        self.umanager = umanager

    def users_secret_file_entries(self, creator: str) -> List[SecretFileEntry]: 
        users_entries = []
        for _, entry in self.secret_file.items():
            if entry._creator == creator: 
                users_entries.append(entry) 
        return users_entries 

    def secret_files_in_review(self, collective: str) -> List[SecretFileEntry]: 
        print("review: collective", collective)
        block = collective.split("-")[1] if "-" in collective else collective
        print("review: block", collective)
        entries = []
        for _, entry in self.secret_file.items():
            user = self.umanager.get_user(entry._creator)
            if user is None: 
                print("Warn: creator not found: ", entry._creator)
                continue
            comm_user = self.comm.get_user(user.email.lower())
            print("review: ", block, "in", entry._creator, "?", comm_user.collective)
            if entry._review and (block in comm_user.collective or collective == "orga"): 
                entries.append(entry) 
        return entries

    def secret_files(self) -> List[SecretFileEntry]: 
        entries = [] 
        for _, entry in self.secret_file.items(): 
            if entry._published: 
                entries.append(entry) 
        return entries

    def get_chars_by_name(self) -> Dict[str, Tuple[str, str]]:
        chars = {}
        for _, entry in self.secret_file.items(): 
            chars[f"{entry.sirname}, {entry.name}"] = (entry.key, f"zone: {entry.zone}")
        return chars

    def get_chars_by_key(self) -> Dict[str, Tuple[str, str]]:
        chars = {}
        for _, entry in self.secret_file.items(): 
            chars[entry.key] = (f"{entry.sirname}, {entry.name}", f"zone: {entry.zone}")
        return chars

    def replace_connection_names_with_keys(
        self, connections: List[str]
    ) -> List[str]:
        chars = self.get_chars_by_name()
        keys = []
        for connection in connections: 
            if connection in chars: 
                key, _ = chars[connection]
                keys.append(key) 
            else:
                keys.append(connection) 
        return keys

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

    def delete_secret_file_entry(self, key: str) -> bool:
        if key in self.secret_file: 
            os.remove(f"{os.path.join(SECRET_FILE_PATH, key)}.json")
            del self.secret_file[key]
            return True 
        return False

    def add_gm(self, gm: Abbr): 
        self.gms[gm.abbr] = gm 
        self.__save_list(GM_PATH, self.gms)

    def add_cbi(self, cbi: Abbr): 
        self.cbis[cbi.abbr] = cbi
        self.__save_list(CBI_PATH, self.cbis)

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

    def __load_list(self, path: str) -> Dict[str, Abbr]: 
        """ Loads secret service files """
        if not os.path.exists(path):
            with open(path,'w') as f:
                f.write("{}")
        lst = {}
        with open(path, "r") as f: 
            for abbr, j_lst in json.load(f).items():
                print(j_lst)
                lst[abbr] = Abbr(**j_lst)
        return lst

    def __save_list(self, path, lst): 
        json_ready = {k: dataclasses.asdict(v) for k, v in lst.items()}
        with open(path, "w") as f: 
            json.dump(json_ready, f)
