# Turnout App

To build run `make build`

To run locally run `make up` then (while the server is up) in another shell run `make migrate`

To clean python files run `make lint` (while the server is running)

To enter a running docker container, run `make shell`

To enter a psql shell of the staging RDS database, run `make dbshell`

`make dbshell` connects to the database using [IAM Authentication](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.Connecting.AWSCLI.PostgreSQL.html)
and requires the `awscli` and `jq` libraries. If you're running the command locally, ensure that
you've run `aws configure` and provided the credentials to an IAM user with permission to perform
IAM auth to your turnout database. If you're running the command on EC2, ensure that the IAM Role
that your instance is running under has proper permissions. If your RDS instance is on a private
subnet, you'll likely need to connect via a VPN or from a shell that is on that same subnet.
