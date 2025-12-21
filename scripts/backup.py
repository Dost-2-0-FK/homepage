import os
import sys
import shutil
from datetime import date

DATA_DIR = sys.argv[1]
BACKUP_LOCATION = sys.argv[2]

print(DATA_DIR)
print(BACKUP_LOCATION)

today = date.today() 
date_format = today.strftime("%Y_%b_%d_")

shutil.make_archive(os.path.join(BACKUP_LOCATION, date_format), 'zip', DATA_DIR)
