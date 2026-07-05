from src.communicator import Comm
from src.seafiler import Seafile
from src.user_manager import UManager


for filename in os.listdir(SECRET_FILE_PATH): 
    with open(os.path.join(SECRET_FILE_PATH, filename), "r") as f: 
        json_data = json.load(f)
        entries[os.path.splitext(filename)[0]] = SecretFileEntry(**json_data)


