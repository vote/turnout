{
  for_env(env)::
    [
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.database_url',
        name: 'DATABASE_URL',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.database_max_connections',
        name: 'DATABASE_MAX_CONNECTIONS',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.redis_url',
        name: 'REDIS_URL',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.secret_key',
        name: 'SECRET_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.sentry_dsn',
        name: 'SENTRY_DSN',
      },
    ],
}
