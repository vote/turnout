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

importfromprod:
	docker-compose exec server python manage.py importfromprod

shell:
	docker-compose exec server /bin/bash

clientshell:
	docker-compose exec client /bin/bash

testpy:
	docker-compose exec server pytest /app/

mypy:
	docker-compose exec server mypy /app/

test:
	docker-compose exec server bash -c "pytest /app/ && mypy /app/"

lint:
	docker-compose exec server bash -c "autoflake \
		--remove-unused-variables --remove-all-unused-imports --ignore-init-module-imports --in-place --recursive --exclude /*/migrations/* /app/ && \
		isort --recursive --skip migrations /app/ && black --exclude /*/migrations/* /app/"

openapi:
	docker-compose exec server python manage.py generateschema --format openapi openapi.yaml


dbshell:
	bash scripts/rds_psql.sh

dblocalrestore:
	bash scripts/rds_localrestore.sh

shellprod:
	ENVIRONMENT=prod bash scripts/remote_run.sh ${TAG}

shellstaging:
	ENVIRONMENT=staging bash scripts/remote_run.sh ${TAG}

shelldev:
	ENVIRONMENT=dev DOCKER_REPO_NAME=turnoutdev bash scripts/remote_run.sh ${TAG}

localtodev:
	bash scripts/local_to_dev.sh

ecrpush:
	scripts/local_ecr_push.sh
