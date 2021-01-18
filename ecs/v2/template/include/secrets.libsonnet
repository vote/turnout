{
  for_env(env)::
    [
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.database_url',
        name: 'DATABASE_URL',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.readonly_database_url',
        name: 'READONLY_DATABASE_URL',
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
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.amqp_url',
        name: 'AMQP_URL',
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
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.file_purge_days',
        name: 'FILE_PURGE_DAYS',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.state_tool_redirect_sync',
        name: 'STATE_TOOL_REDIRECT_SYNC',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.targetsmart_key',
        name: 'TARGETSMART_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.allowed_hosts',
        name: 'ALLOWED_HOSTS',
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
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.www_origin',
        name: 'WWW_ORIGIN',
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
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.sms_optin_reminder_delay',
        name: 'SMS_OPTIN_REMINDER_DELAY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.sms_post_signup_alert',
        name: 'SMS_POST_SIGNUP_ALERT',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.sms_optout_number',
        name: 'SMS_OPTOUT_NUMBER',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.sms_optout_poll',
        name: 'SMS_OPTOUT_POLL',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.multifactor_enabled',
        name: 'MULTIFACTOR_ENABLED',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.two_factor_sms_number',
        name: 'TWO_FACTOR_SMS_NUMBER',
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
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.usvf_geocode',
        name: 'USVF_GEOCODE',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/general.datadogkey',
        name: 'DD_API_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.register_co_vrd_id',
        name: 'REGISTER_CO_VRD_ID',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.register_co_vrd_enabled',
        name: 'REGISTER_CO_VRD_ENABLED',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.register_wa_vrd_id',
        name: 'REGISTER_WA_VRD_ID',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.register_wa_vrd_enabled',
        name: 'REGISTER_WA_VRD_ENABLED',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.actionnetwork_key',
        name: 'ACTIONNETWORK_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.actionnetwork_subscribers_key',
        name: 'ACTIONNETWORK_SUBSCRIBERS_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.optimizely_sdk_key',
        name: 'OPTIMIZELY_SDK_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.slack_subscriber_interest_enabled',
        name: 'SLACK_SUBSCRIBER_INTEREST_ENABLED',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.slack_subscriber_interest_webhook',
        name: 'SLACK_SUBSCRIBER_INTEREST_WEBHOOK',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.api_key_pepper',
        name: 'API_KEY_PEPPER',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.digitalocean_key',
        name: 'DIGITALOCEAN_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.register_resume_url',
        name: 'REGISTER_RESUME_URL',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.file_token_purged_url',
        name: 'FILE_TOKEN_PURGED_URL',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.pdf_generation_lambda_enabled',
        name: 'PDF_GENERATION_LAMBDA_ENABLED',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.pdf_generation_lambda_function',
        name: 'PDF_GENERATION_LAMBDA_FUNCTION',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.return_address',
        name: 'RETURN_ADDRESS',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.beat_stats_metric_namespace',
        name: 'BEAT_STATS_METRIC_NAMESPACE',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.i90_key',
        name: 'I90_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.mover_id',
        name: 'MOVER_ID',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.mover_secret',
        name: 'MOVER_SECRET',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.mover_source',
        name: 'MOVER_SOURCE',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.mover_leads_endpoint',
        name: 'MOVER_LEADS_ENDPOINT',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.slack_alloy_update_enabled',
        name: 'SLACK_ALLOY_UPDATE_ENABLED',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.slack_alloy_update_webhook',
        name: 'SLACK_ALLOY_UPDATE_WEBHOOK',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.mapbox_key',
        name: 'MAPBOX_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.mms_attachment_bucket',
        name: 'MMS_ATTACHMENT_BUCKET',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.civic_key',
        name: 'CIVIC_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.uptime_url',
        name: 'UPTIME_URL',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.uptime_user',
        name: 'UPTIME_USER',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.uptime_secret',
        name: 'UPTIME_SECRET',
      },
    ],
}
