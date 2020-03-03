# Turnout

Turnout is a multi-tenant voter notification, verification, registration, and Get Out The Vote app
built to get as many people as possible to the polls.

Turnout was created in-house at [Turnout2020](https://www.turnout2020.us), who is the primary user.

Turnout's code is publicly available under the
[Business Source License v1.1](https://github.com/vote/turnout/blob/master/LICENSE).

## Architecture

Turnout is written entirely in Python using the Django and Celery frameworks and relies on Postgres
as a data backend and Redis as a cache and message broker.

API views are written entirely using Django Rest Framework, while the administrative interface is
built using Django generic views and static assets compiled using webpack.

Local development is done entirely inside docker using docker-compose, orchestrated on the command
line using gnumake, and deployment is done by creating Docker images and deploying them using a
container orchestration system such as Kubernetes or (in the case of Turnout2020) Elastic Container
Service.

For production deployments, Turnout's web interface assumes it's behind a caching and web firewall
layer, such as Cloudflare, and is configured respond to health checks sent from a load balancer
such as an AWS Application Load Balancer.

This repository contains utilities specific to Turnout2020's deployment of Turnout on AWS. Commits
to master as well as new git tags trigger [Travis](https://travis-ci.com/vote/turnout) to build
docker images and upload those images to container repositories within the Turnout2020 AWS account.
A Turnout2020-hosted version of Spinnakerlaunches ECS tasks with this new image (using the Fargate
launch type) using a Red/Black deployment strategy. Turnout2020 uses Postgres on RDS and Redis on
ElastiCache.

## General Development

The commands generally require `gnumake` and `docker` to be installed locally.

To launch you'll need a `.env` file in your project root. Review `.env.example` for examples of
variables you can include in your file.

To build run `make build`

To run locally run `make up` then (while the server is up) in another shell run `make migrate`

To create a new superuser run `make createsuperuser` (while server is running)

To run python tests, run `make testpy` (while server is running)

To clean python files run `make lint` (while the server is running)

To bootstrap the database with state information fields and data from our production API,
run `make importfromprod` (while server is running) 


### Shell Access

To enter a running bash shell on your running docker container, i.e. when `make up` has been run in
another prompt, run `make shell`

To enter a bash shell of your local version, with prod environment variables (such as DATABASE_URL)
run `make shellprod`. To use staging environment variables, run `make shellstaging`. For dev,
`make shelldev`

To run a specific docker tag on staging or prod, `make shellprod TAG=tagid` or
`make shellstaging TAG=tagid`. So, for example, to enter a bash shell of version `0.0.25` with
staging environment variables, run `make shellstaging TAG=0.0.25`.

It is also possible to launch commits to `master` in the dev environment, using `make shelldev`.
Just enter `make shelldev TAG=a130efea6f124a2deb455be81ab30ecf72325a18` to enter a shell with the
commit `a130efea6f124a2deb455be81ab30ecf72325a18`.

These remote shell commands will only work if you have the `awscli` and `jq` libraries installed,
and with your locally configured user or (if running on EC2) system's IAM role having permission to
access the relevant parameters in the Systems Manager parameter store. You'll also need permission
to decrypt the permissions, as they're stored as SecureStrings. You'll also likely need to be on a
VPN, as services such as redis and RDS are likely on a private subnet.

By default Django's DEBUG mode is set to True. To run without DEBUG, `make shellprod DEBUG=false`
can be run. This will likely result in some external calls being sent, such as those to Datadog
and Sentry. Port `8000` is also forwarded to the host, so the command
`./manage.py runserver 0.0.0.0:8000` would allow you to visit a version of the app locally at
`http://localhost:8000/`.


### On-Demand Dev Deployment

To deploy the version of code currently in your `app/` directory to the dev cluster, run
`make localtodev`. Migrations will be automatically run prior to the cluster launching with your
new code.


3 Notes:

1) The dev cluster is a shared asset, and commits to `master` automatically deploy to it. This
means that it's possible your version will be overwritten without your knowledge. Keep an eye on
what version is being deployed, and communicate in Slack when you're deploying to dev.

2) The dev cluster's database is not wiped on new deploys, and deployments automatically run any
pending django migrations. This means that the dev database may have tables or columns that you
may not be expecting, or migrations may be applied in an order that may not reflect the order
they appear in your local deployment (or staging or prod deployments.)

3) Dev is not currently behind a CDN, and is not accessible by the public internet.


This means one thing: **Dev is a playground to test code, not an adequite reflection of how turnout
will function on prod**


### Remote Database Access

To enter a psql shell of the staging RDS database, run `make dbshell`

To wipe your local database and replace it with the staging database, run `make dblocalrestore`.
**THIS IS AN IRREVERSABLE DESTRUCTIVE ACTION.** Your local database will be wiped and replaced with
the content on the remote database.

To further spell out why `make dblocalrestore` may be a bad idea, if the staging database is large
this can take a long time and use substantial amounts of disk space. If the staging database
contains PII, it will be cloned to your local machine. Only perform this action if you know what
you're doing. There is no going back.

`make dbshell` and `make dblocalrestore` connects to the database using [IAM Authentication](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.Connecting.AWSCLI.PostgreSQL.html)
and requires the `awscli` and `jq` libraries, as well as postgres client tools. If you're running
the commands locally, ensure that you've run `aws configure` and provided the credentials to an
IAM user with permission to perform IAM auth to your turnout database. If you're running the
commands on EC2, ensure that the IAM Role that your instance is running under has proper
permissions. If your RDS instance is on a private subnet, you'll likely need to connect via a VPN
or from a shell that is on that same subnet.
