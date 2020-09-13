#!/bin/sh

export PGUSER=postgres
export PGHOST=localhost
export PGPASSWORD=turnout
export PGPORT=5432

psql -d turnout -c 'DROP SCHEMA public CASCADE;CREATE SCHEMA public;'

make migrate
make importfromprod
make syncusvf
make importgisdata
