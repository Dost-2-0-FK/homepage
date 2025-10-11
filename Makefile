install: 
	mkdir -p /usr/bin/dost/homepage
	cp -f dost-homepage.service /etc/systemd/system/ 
	systemctl daemon-reload 
	cp -f requirements.txt /usr/bin/dost/homepage
	cp -f app.py /usr/bin/dost/homepage
	cp -f .env /usr/bin/dost/homepage
	cp -f -r .venv /usr/bin/dost/homepage
	cp -f -r src/ /usr/bin/dost/homepage
	cp -f -r static/ /usr/bin/dost/homepage
	cp -f -r templates/ /usr/bin/dost/homepage
	cp -f -r data/ /usr/bin/dost/homepage
	cd /usr/bin/dost/homepage && source .venv/bin/activate && pip install -r requirements.txt 

update:  
	cp -f requirements.txt /usr/bin/dost/homepage
	cp -f app.py /usr/bin/dost/homepage
	cp -f .env /usr/bin/dost/homepage
	cp -f -r src/ /usr/bin/dost/homepage
	cp -f -r static /usr/bin/dost/homepage
	cp -f -r templates/ /usr/bin/dost/homepage
	cd /usr/bin/dost/homepage && source .venv/bin/activate && pip install -r requirements.txt 
	systemctl restart dost-homepage.service
