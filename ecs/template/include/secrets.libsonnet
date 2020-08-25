local base_secrets = import './base_secrets.libsonnet';

{
  for_env(env)::
    base_secrets.for_env(env) + [
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
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.actionnetwork_form_prefix',
        name: 'ACTIONNETWORK_FORM_PREFIX',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.optimizely_sdk_key',
        name: 'OPTIMIZELY_SDK_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.pa_ovr_key',
        name: 'PA_OVR_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.pa_ovr_staging',
        name: 'PA_OVR_STAGING',
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
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.uptime_twitter_consumer_key',
        name: 'UPTIME_TWITTER_CONSUMER_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.uptime_twitter_consumer_secret',
        name: 'UPTIME_TWITTER_CONSUMER_SECRET',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.uptime_twitter_access_token',
        name: 'UPTIME_TWITTER_ACCESS_TOKEN',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.uptime_twitter_access_token_secret',
        name: 'UPTIME_TWITTER_ACCESS_TOKEN_SECRET',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.slack_uptime_webhook',
        name: 'SLACK_UPTIME_WEBHOOK',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.proxy_ssh_key',
        name: 'PROXY_SSH_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.proxy_ssh_pub',
        name: 'PROXY_SSH_PUB',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.proxy_ssh_key_id',
        name: 'PROXY_SSH_KEY_ID',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.proxy_tag',
        name: 'PROXY_TAG',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.selenium_url',
        name: 'SELENIUM_URL',
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
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.verifier_upsell_url',
        name: 'VERIFIER_UPSELL_URL',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.lob_key',
        name: 'LOB_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.lob_letter_webhook_secret',
        name: 'LOB_LETTER_WEBHOOK_SECRET',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/turnout.' + env + '.return_address',
        name: 'RETURN_ADDRESS',
      },
    ],
}
