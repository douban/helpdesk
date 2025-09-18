SHELL := /bin/bash
git:
	source /usr/share/bash-completion/completions/git

venv: git
	test -d /home/project/venv || virtualenv /home/project/venv/

env:
	@echo "install deb for helpdesk dev ..."
	dpi -p requirements.txt -v /home/project/venv/bin/python

initdb:
	mkdir -p /var/lib/mysql
	ln -sf /var/run/mysqld/mysqld.sock /var/lib/mysql/mysql.sock
	/home/project/venv/bin/python -c 'from helpdesk.libs.db import init_db; init_db()'

dev: venv env initdb

backend-run: git
	source /home/project/venv/bin/activate
	/home/project/venv/bin/python -m uvicorn helpdesk:app --host 0.0.0.0 --port 8123 --log-level debug --log-config .doubanpde/logging_config.json

.PHONY: frontend
frontend: git
	npm config set registry https://registry.npmmirror.com
	npm --prefix /home/project/frontend/ install

frontend-run: git
	npm --prefix /home/project/frontend/ run dev
