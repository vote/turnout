local datadogEnv = import './datadog_env.libsonnet';
local secrets = import './secrets.libsonnet';
local env = std.extVar('env');

local common(ddname, ddsource, health_command) =
  {
    image: 'nginx/nginx:latest',
    essential: true,
    logConfiguration: {
      logDriver: 'awsfirelens',
      options: {
        Name: 'datadog',
        host: 'http-intake.logs.datadoghq.com',
        dd_service: ddname,
        dd_source: ddsource,
        dd_message_key: 'log',
        dd_tags: 'env:' + env,
        TLS: 'on',
        Host: 'http-intake.logs.datadoghq.com',
        provider: 'ecs',
      },
      secretOptions: [
        {
          valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/general.datadogkey',
          name: 'apikey',
        },
      ],
    },
    environment: datadogEnv.for_service(ddname, env),
    secrets: secrets.for_env(env),
    healthCheck: {
      command: [
        'CMD-SHELL',
        health_command,
      ],
      interval: 120,
      timeout: 15,
      retries: 3,
    },
    dependsOn: [
      {
        containerName: 'datadog-agent',
        condition: 'START',
      },
      {
        containerName: 'log_router',
        condition: 'START',
      },
    ],
  };

{
  common(ddname, ddsource, health_command)::
    common(ddname, ddsource, health_command),
}
