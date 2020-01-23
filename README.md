# Turnout App

The commands generally require `gnumake` and `docker` to be installed locally.


### General Development

To launch you'll need a `.env` file in your project root. Review `.env.example` for examples of
variables you can include in your file.

To build run `make build`

To run locally run `make up` then (while the server is up) in another shell run `make migrate`

To create a new superuser run `make createsuperuser` (while server is running)

To run python tests, run `make testpy` (while server is running)

To clean python files run `make lint` (while the server is running)


### Shell Access

To enter a running bash shell on your running docker container, i.e. when `make up` has been run in
another prompt, run `make shell`

To enter a bash shell of your local version, with prod environment variables (such as DATABASE_URL)
run `make shellprod`. To use staging environment variables, run `make shellstaging`. To run a
specific docker tag, `make shellprod TAG=tagid` or `make shellstaging TAG=tagid`. So, for example,
to enter a bash shell of version `0.0.25` with staging environment variables, run
`make shellstaging TAG=0.0.25`.

These remote shell commands will only work if you have the `awscli` and `jq` libraries installed,
and with your locally configured user or (if running on EC2) system's IAM role having permission to
access the relevant parameters in the Systems Manager parameter store. You'll also need permission
to decrypt the permissions, as they're stored as SecureStrings. You'll also likely need to be on a
VPN, as services such as redis and RDS are likely on a private subnet.

By default Django's DEBUG mode is set to True. To run without DEBUG, `DEBUG=false make shellprod`
can be run. This will likely result in some external calls being sent, such as those to Datadog
and Sentry. Port `8000` is also forwarded to the host, so the command
`./manage.py runserver 0.0.0.0:8000` would allow you to visit a version of the app locally at
`http://localhost:8000/`.


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
