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
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.usvf_sync',
        name: 'USVF_SYNC',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.usvf_sync_hour',
        name: 'USVF_SYNC_HOUR',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.actionnetwork_sync',
        name: 'ACTIONNETWORK_SYNC',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.actionnetwork_sync_daily',
        name: 'ACTIONNETWORK_SYNC_DAILY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.actionnetwork_sync_hour',
        name: 'ACTIONNETWORK_SYNC_HOUR',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.ovbm_sync',
        name: 'OVBM_SYNC',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.uptime_enabled',
        name: 'UPTIME_ENABLED',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.file_purge_days',
        name: 'FILE_PURGE_DAYS',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.state_tool_redirect_sync',
        name: 'STATE_TOOL_REDIRECT_SYNC',
      },
    ],
}
