PREFIX=/usr/bin/dost/homepage
PYTHON=/usr/bin/python3

install:
	mkdir -p $(PREFIX)
	# code & assets
	cp -f requirements.txt $(PREFIX)/
	cp -f app.py $(PREFIX)/
	cp -f .env $(PREFIX)/
	rsync -a --delete src/ $(PREFIX)/src/
	rsync -a --delete static/ $(PREFIX)/static/
	rsync -a --delete templates/ $(PREFIX)/templates/
	rsync -a --delete data/ $(PREFIX)/data/

	# create venv IN PLACE (do not copy an existing one)
	$(PYTHON) -m venv $(PREFIX)/.venv
	$(PREFIX)/.venv/bin/python -m pip install --upgrade pip
	$(PREFIX)/.venv/bin/pip install -r $(PREFIX)/requirements.txt

	# install service
	cp -f dost-homepage.service /etc/systemd/system/
	systemctl daemon-reload
	systemctl enable --now dost-homepage.service

update:
	cp -f requirements.txt $(PREFIX)/
	cp -f app.py $(PREFIX)/
	cp -f .env $(PREFIX)/
	rsync -a --delete src/ $(PREFIX)/src/
	rsync -a --delete static/ $(PREFIX)/static/
	rsync -a --delete templates/ $(PREFIX)/templates/
	$(PREFIX)/.venv/bin/pip install -r $(PREFIX)/requirements.txt
	systemctl restart dost-homepage.service

