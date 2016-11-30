
all: install

install_deps:
	sudo -H pip3 install -r requirements.txt

help:
	@echo
	@echo "now call sudo systemctl daemon-reload"
	@echo "  sudo systemctl enable git-mirrorer.timer"
	@echo "  sudo systemctl start git-mirrorer.timer"
	@echo "  sudo systemctl status git-mirrorer.service"
	@echo "  sudo systemctl start git-mirrorer"
	@echo "  sudo systemctl list-timers --all"
	@echo "  sudo systemctl is-enabled git-mirrorer.timer"
	@echo "  sudo journalctl -xe -u git-mirrorer"

install:
	install -m 755 -T git-mirrorer.py /usr/bin/git-mirrorer
	mkdir -p /etc/git-mirrorer
ifneq ("$(wildcard $("/etc/git-mirrorer/conf.json"))","")
	@echo "installing configuration file"
	install -m 644 -T conf.json /etc/git-mirrorer/conf.json
else
	@echo "DID NOT overwrite configuration file /etc/git-mirrorer/conf.json"
endif
	install -m 644 assets/git-mirrorer.service /etc/systemd/system/
	install -m 644 assets/git-mirrorer.timer /etc/systemd/system/
	make help

uninstall:
	rm -rf /usr/bin/git-mirrorer
	rm -rf /etc/git-mirrorer
	rm -rf /etc/systemd/system/git-mirrorer.service


