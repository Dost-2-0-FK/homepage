import json
import os
from threading import Lock
from typing import Dict

from src.seafiler import SeafBytes, Seafile

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


class User: 
    def __init__(self, ujson: Dict[str, str]) -> None:
        # Get mandotory fields (key/email):
        if "key" not in ujson: 
            raise Exception("FATAL! Corrupted JSON: missing \"key\"")
        self.key = ujson["key"]
        if "email" not in ujson: 
            raise Exception("FATAL! Corrupted JSON: missing \"email\"")
        self.email = ujson["email"]

        # Get Optional fields:
        self.name = ujson.get("name", "") 
        self.pdream = ujson.get("pdream", "") 
        self.ndream = ujson.get("ndream", "") 
        self.pnature = ujson.get("pnature", "") 
        self.nnature = ujson.get("nnature", "") 
        self.pspirit = ujson.get("pspirit", "") 
        self.nspirit = ujson.get("nspirit", "") 

    def update_field(self, field: str, value: str) -> None: 
        if field == "name": 
            self.name = value 
        if field == "pnature": 
            self.pnature = value 
        if field == "nnature": 
            self.nnature = value 
        if field == "pspirit": 
            self.pspirit = value 
        if field == "nspirit": 
            self.nspirit = value 
        if field == "pdream": 
            self.pdream = value 
        if field == "ndream": 
            self.ndream = value 

class UManager: 
    def __init__(self):
        if "SEAFILE_CSV" not in os.environ: 
            exit("Missing SEAFILE_CSV!")
        self.SEAF_CSV_DIR = os.getenv("SEAFILE_CSV", "")
        self.mutex = Lock()
        self.seaf = Seafile(os.getenv("USE_SEAFILE", "False") == "True")

    def email_exists(self, email: str) -> bool: 
        with self.mutex: 
            for row in self.__get_csv():
                if row[1].strip().lower() == email.lower(): 
                    return True 
            return False 

    def key_exists(self, key: str) -> bool: 
        print("Checking path: ",self.__make_user_path(key))
        return os.path.exists(self.__make_user_path(key))

    def get_user(self, key: str) -> User | None: 
        if self.key_exists(key): 
            with open(self.__make_user_path(key), "r") as f: 
                return User(json.load(f)) 
        return None

    def save_user(self, user: User): 
        with open(self.__make_user_path(user.key), "w") as fp: 
            json.dump(vars(user), fp)
        # Update CSV fields: 
        with self.mutex: 
            changed = False
            csv = self.__get_csv()
            for row in csv: 
                if row[1].strip().lower() == user.email.lower(): 
                    if row[2].strip() != user.name: 
                        row[2] = user.name 
                        changed = True
            if changed: 
                self.__upload_csv(csv)
                print("Saved CSV!")


    def add_user(self, email: str, key: str): 
        with self.mutex: 
            # Add E-Mail to User-CSV 
            csv = self.__get_csv()
            csv.append([str(len(csv)), email, "", "", "", ""]) 
            self.__upload_csv(csv)
            # Create new User-Json 
            with open(self.__make_user_path(key), "w") as fp: 
                json.dump({"key": key, "email": email}, fp)

    # Function to write data to CSV
    def __upload_csv(self, csv):
        if self.seaf.use_seafile:
            self.seaf.upload_data(SeafBytes.from_csv(csv).bytes, self.SEAF_CSV_DIR)
        else:
            raise Exception("Using local CSV file not implemented")

    # Function to read data from CSV
    def __get_csv(self):
        if self.seaf.use_seafile:
            return self.seaf.download_data(self.SEAF_CSV_DIR).csv()
        raise Exception("Using local CSV file not implemented")

    def __make_user_path(self, key: str) -> str: 
        return f"data/{key}.json"
