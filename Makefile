
# Running too many tests is parallel exhausts shared memory on some
# machines (recent Ubuntu and Fedora in my case).
MAXPROC ?= 16

up:
	docker-compose up --build

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

importgisdata:
	docker-compose exec server python manage.py importgisdata

syncusvf:
	docker-compose exec server python manage.py syncusvf

shell:
	docker-compose exec server /bin/bash

clientshell:
	docker-compose exec client /bin/bash

testpy:
	docker-compose exec server bash -c "TEST=1 ATTACHMENT_USE_S3=False pytest -n `scripts/nproc-max ${MAXPROC}` /app/"

mypy:
	docker-compose exec server mypy /app/

test:
	docker-compose exec server bash -c "TEST=1 ATTACHMENT_USE_S3=False pytest -n `scripts/nproc-max ${MAXPROC}` /app/ && mypy /app/"

testpdf:
	docker-compose exec server bash -c "TEST=1 ATTACHMENT_USE_S3=False ABSENTEE_TEST_ONLY=${STATE} pytest /app/absentee/tests/test_pdf.py /app/absentee/tests/test_metadata.py"

testpdfsigbox:
	docker-compose exec server bash -c "mkdir -p absentee/management/commands/out && python manage.py sig_sample ${STATE} --box"

testpdfsig:
	docker-compose exec server bash -c "mkdir -p absentee/management/commands/out && python manage.py sig_sample ${STATE}"

cacheofficials:
	docker-compose exec server python manage.py cacheofficials

lint:
	docker-compose exec server bash -c "autoflake \
		--remove-unused-variables --remove-all-unused-imports --ignore-init-module-imports --in-place --recursive --exclude /*/migrations/* /app/ && \
		isort --recursive -m 3 -tc -w 88 --skip migrations /app/ && \
		black --exclude /*/migrations/* /app/"

openapi:
	docker-compose exec server python manage.py generateschema --format openapi openapi.yaml

make psql:
	PGPASSWORD=turnout psql turnout -h localhost -U postgres

dbshell:
	bash scripts/rds_psql.sh

dblocalrestore:
	bash scripts/rds_localrestore.sh

shellprod:
	ENVIRONMENT=prod bash scripts/remote_run.sh ${TAG} "${CMD}"

shellstaging:
	ENVIRONMENT=staging bash scripts/remote_run.sh ${TAG} "${CMD}"

shelldev:
	ENVIRONMENT=dev DOCKER_REPO_NAME=turnoutdev bash scripts/remote_run.sh ${TAG} "${CMD}"

localtodev:
	bash scripts/local_to_dev.sh

ecrpush:
	scripts/local_ecr_push.sh

resetlocaldb:
	scripts/reset_local_db.sh
