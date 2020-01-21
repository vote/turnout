up:
	docker-compose up

build:
	docker-compose build

makemigrations:
	docker-compose exec server python manage.py makemigrations

migrate:
	docker-compose exec server python manage.py migrate

createsuperuser:
	docker-compose exec server python manage.py createsuperuser

shell:
	docker-compose exec server /bin/bash

clientshell:
	docker-compose exec client /bin/bash


testpy:
	docker-compose exec server pytest /app/

lint:
	docker-compose exec server bash -c "autoflake \
		--remove-unused-variables --remove-all-unused-imports --ignore-init-module-imports --in-place --recursive --exclude /*/migrations/* /app/ && \
		isort --recursive --skip migrations /app/ && black --exclude /*/migrations/* /app/"

dbshell:
	bash scripts/rds_psql.sh

shellprod:
	ENVIRONMENT=prod bash scripts/remote_run.sh ${TAG}

shellstaging:
	ENVIRONMENT=staging bash scripts/remote_run.sh ${TAG}

ecrpush:
	scripts/local_ecr_push.sh
