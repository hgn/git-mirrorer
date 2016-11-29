
all: install

install_deps:
	sudo -H pip3 install -r requirements.txt

help:
	@echo
	@echo "now call sudo systemctl daemon-reload"
	@echo ".. enable service via: sudo systemctl enable git-mirrorer.service"
	@echo ".. start service via:  sudo systemctl start git-mirrorer.service"
	@echo ".. status via:         sudo systemctl status git-mirrorer.service"
	@echo ".. log info via:       sudo journalctl -u git-mirrorer.service"

install:
	install -m 755 -T git-mirrorer.py /usr/bin/git-mirrorer
	mkdir -p /etc/git-mirrorer
	install -m 644 -T conf.json /etc/git-mirrorer/conf.json
	install -m 644 assets/git-mirrorer.service /lib/systemd/system/
	make help

uninstall:
	rm -rf /usr/bin/git-mirrorer
	rm -rf /etc/git-mirrorer
	rm -rf /lib/systemd/system/git-mirrorer.service


