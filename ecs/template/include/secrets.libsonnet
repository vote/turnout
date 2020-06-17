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
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.targetsmart_key',
        name: 'TARGETSMART_KEY',
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
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.allowed_hosts',
        name: 'ALLOWED_HOSTS',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.sentry_dsn',
        name: 'SENTRY_DSN',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.multifactor_issuer',
        name: 'MULTIFACTOR_ISSUER',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.use_s3',
        name: 'ATTACHMENT_USE_S3',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.public_storage_bucket',
        name: 'AWS_STORAGE_BUCKET_NAME',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.private_storage_bucket',
        name: 'AWS_STORAGE_PRIVATE_BUCKET_NAME',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.sendgrid_api_key',
        name: 'SENDGRID_API_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.file_token_reset_url',
        name: 'FILE_TOKEN_RESET_URL',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.primary_origin',
        name: 'PRIMARY_ORIGIN',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.usvf_key',
        name: 'USVOTEFOUNDATION_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.alloy_key',
        name: 'ALLOY_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.alloy_secret',
        name: 'ALLOY_SECRET',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.cloudflare_zone',
        name: 'CLOUDFLARE_ZONE',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.cloudflare_token',
        name: 'CLOUDFLARE_TOKEN',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.cloudflare_enabled',
        name: 'CLOUDFLARE_ENABLED',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.leo_email_disable',
        name: 'ABSENTEE_LEO_EMAIL_DISABLE',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.leo_email_override_address',
        name: 'ABSENTEE_LEO_EMAIL_OVERRIDE_ADDRESS',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.leo_email_from',
        name: 'ABSENTEE_LEO_EMAIL_FROM',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.twilio_account_sid',
        name: 'TWILIO_ACCOUNT_SID',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.twilio_auth_token',
        name: 'TWILIO_AUTH_TOKEN',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.twilio_messaging_service_sid',
        name: 'TWILIO_MESSAGING_SERVICE_SID',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.multifactor_enabled',
        name: 'MULTIFACTOR_ENABLED',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.geocodio_key',
        name: 'GEOCODIO_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.fax_disable',
        name: 'FAX_DISABLE',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.fax_override_dest',
        name: 'FAX_OVERRIDE_DEST',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.fax_gateway_callback_url',
        name: 'FAX_GATEWAY_CALLBACK_URL',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.fax_gateway_sqs_queue',
        name: 'FAX_GATEWAY_SQS_QUEUE',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.slack_data_error_enabled',
        name: 'SLACK_DATA_ERROR_ENABLED',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.slack_data_error_webhook',
        name: 'SLACK_DATA_ERROR_WEBHOOK',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.usvf_sync',
        name: 'USVF_SYNC',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.usvf_sync_hour',
        name: 'USVF_SYNC_HOUR',
      },
    ],
}
