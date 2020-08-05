local base_secrets = import './base_secrets.libsonnet';
local datadogEnv = import './datadog_env.libsonnet';
local secrets = import './secrets.libsonnet';
local migrations = std.extVar('migrations');
local env = std.extVar('env');

local common(ddname, ddsource) =
  {
    image: 'nginx/nginx:latest',
    essential: false,
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
  };

local common_secrets(ddname, ddsource) =
  common(ddname, ddsource) +
  {
    secrets: secrets.for_env(env),
  };

local common_base_secrets(ddname, ddsource) =
  common(ddname, ddsource) +
  {
    secrets: base_secrets.for_env(env),
  };

local essential(ddname, ddsource, health_command) =
  common(ddname, ddsource) + {
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
    ] + (
      if !migrations then [] else [
        {
          containerName: 'migration',
          condition: 'COMPLETE',
        },
      ]
    ),
    essential: true,
  };

local essential_secrets(ddname, ddsource, health_command) =
  essential(ddname, ddsource, health_command) +
  {
    secrets: secrets.for_env(env),
  };
local essential_base_secrets(ddname, ddsource, health_command) =
  essential(ddname, ddsource, health_command) +
  {
    secrets: base_secrets.for_env(env),
  };

{
  common(ddname, ddsource)::
    common(ddname, ddsource),

  common_secrets(ddname, ddsource)::
    common_secrets(ddname, ddsource),

  essential(ddname, ddsource, health_command)::
    essential(ddname, ddsource, health_command),

  essential_secrets(ddname, ddsource, health_command)::
    essential_secrets(ddname, ddsource, health_command),

  essential_base_secrets(ddname, ddsource, health_command)::
    essential_base_secrets(ddname, ddsource, health_command),
}
