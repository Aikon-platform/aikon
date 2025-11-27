.PHONY: dev-services dev-front dev-full

dev-services:
	docker-compose up db redis cantaloupe api

dev-front:
	cd front/app/webpack && npm run watch & \
	cd front && ./venv/bin/python app/manage.py runserver

dev-full: dev-services
	sleep 3
	$(MAKE) dev-front
