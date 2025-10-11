import csv
import json
import os
from threading import Lock

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

class UManager: 
    def __init__(self):
        self.CSV_PATH = "data/anmeldungen.csv"
        self.mutex = Lock()
        self.csv = self.__read_from_csv() 

    def email_exists(self, email: str) -> bool: 
        for row in self.csv: 
            if row[1].strip().lower() == email.lower(): 
                return True 
        return False 

    def key_exists(self, key: str) -> bool: 
        print("Checking path: ",self.__make_user_path(key))
        return os.path.exists(self.__make_user_path(key))

    def add_user(self, email: str, key: str): 
        with self.mutex: 
            # Add E-Mail to User-CSV 
            self.csv.append([str(len(self.csv)), email, "", "", "", ""]) 
            self.__write_to_csv(self.csv)
            # Create new User-Json 
            with open(self.__make_user_path(key), "w") as fp: 
                json.dump({"key": key, "email": email}, fp)

    # Function to write data to CSV
    def __write_to_csv(self, data):
        with open(self.CSV_PATH, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerows(data)

    # Function to read data from CSV
    def __read_from_csv(self):
        with open(self.CSV_PATH, 'r') as csvfile:
            csv_reader = csv.reader(csvfile)
            data = list(csv_reader)
        return data

    def __make_user_path(self, key: str) -> str: 
        return f"data/{key}.json"
