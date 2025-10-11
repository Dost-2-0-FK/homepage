# Dost 2.0 FK - Homepage 

## Installation 
```
python3 -m venv .venv 
source .venv/bin/activate 
pip install -r requirements.txt 
```

Create `.env` 
```
cp env.example .env 
```
And fill out the fields accordingly 

### Local setup  
In the `.env` use something similar to this: 
```
MODE=local
LOCAL_FROM=userk@jpberlin.de
LOCAL_SMTP_HOST=smtp.jpberlin.de
LOCAL_SMTP_PORT=587
LOCAL_SMTP_USER=user@jpberlin.de
LOCAL_SMTP_PASS=supersafepassword
LOCAL_SMTP_SECURITY=starttls
```

Start app, through `python3`: 
```
source .venv/bin/activate 
python3 app.py
```

### Server setup 
In the `.env` use something similar to this: 
```
MODE=server 
SERVER_FROM=registration@dost-2-0-fk.art 
```

To install, run: 
``` 
sudo make install 
``` 

To update, run: 
```
sudo make update 
```
