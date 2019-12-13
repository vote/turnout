up:
	docker-compose up

build:
	docker-compose build

migrate:
	docker-compose exec server python manage.py migrate

shell:
	docker-compose exec server /bin/bash

lint:
	docker-compose exec server bash -c "autoflake \
		--remove-unused-variables --remove-all-unused-imports --ignore-init-module-imports --in-place --recursive /app/ && \
		isort --recursive /app/ && black /app/"

ecrpush:
	scripts/local_ecr_push.sh
