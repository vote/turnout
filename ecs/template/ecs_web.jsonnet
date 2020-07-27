local datadogContainers = import 'include/datadog_containers.libsonnet';
local datadogEnv = import 'include/datadog_env.libsonnet';
local secrets = import 'include/secrets.libsonnet';

local env = std.extVar('env');
local capitalEnv = std.asciiUpper(env[0]) + env[1:];
local migrations = std.extVar('migrations');
local cpu = std.extVar('cpu');
local memory = std.extVar('memory');

{
  executionRoleArn: 'arn:aws:iam::719108811834:role/Turnout-ECS-' + capitalEnv,
  taskRoleArn: 'arn:aws:iam::719108811834:role/Turnout-ECS-' + capitalEnv + '-TaskRole',
  containerDefinitions: [
    {
      portMappings: [
        {
          hostPort: 8000,
          protocol: 'tcp',
          containerPort: 8000,
        },
      ],
      healthCheck: {
        command: [
          'CMD-SHELL',
          '/app/ops/web_health.sh || exit 1',
        ],
        interval: 120,
        timeout: 15,
        retries: 3,
      },
      image: 'nginx/nginx:latest',
      name: 'web',
      essential: true,
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
      logConfiguration: {
        logDriver: 'awsfirelens',
        options: {
          Name: 'datadog',
          host: 'http-intake.logs.datadoghq.com',
          dd_service: 'turnoutweb',
          dd_source: 'django',
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
      environment: datadogEnv.for_service('turnoutweb', env),
      secrets: secrets.for_env(env),
    },

    {
      image: 'nginx/nginx:latest',
      name: 'worker',
      command: [
        '/app/ops/worker_launch.sh',
        'default',
      ],
      healthCheck: {
        command: [
          'CMD-SHELL',
          '/app/ops/worker_health.sh || exit 1',
        ],
        interval: 120,
        timeout: 15,
        retries: 3,
      },
      essential: true,
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
      logConfiguration: {
        logDriver: 'awsfirelens',
        options: {
          Name: 'datadog',
          host: 'http-intake.logs.datadoghq.com',
          dd_service: 'turnoutworker',
          dd_source: 'celery',
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
      environment: datadogEnv.for_service('turnoutworker', env),
      secrets: secrets.for_env(env),
    },

    {
      image: 'nginx/nginx:latest',
      name: 'beat',
      command: [
        '/app/ops/beat_launch.sh',
      ],
      healthCheck: {
        command: [
          'CMD-SHELL',
          '/app/ops/beat_health.sh || exit 1',
        ],
        interval: 120,
        timeout: 15,
        retries: 3,
      },
      essential: true,
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
      logConfiguration: {
        logDriver: 'awsfirelens',
        options: {
          Name: 'datadog',
          host: 'http-intake.logs.datadoghq.com',
          dd_service: 'turnoutbeat',
          dd_source: 'celerybeat',
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
      environment: datadogEnv.for_service('turnoutbeat', env),
      secrets: secrets.for_env(env),
    },
  ] + datadogContainers.for_env(env) + (
    if !migrations then [] else [
      {
        image: 'nginx/nginx:latest',
        name: 'migration',
        command: ['ddtrace-run', 'python', 'manage.py', 'migrate'],
        essential: false,
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
        logConfiguration: {
          logDriver: 'awsfirelens',
          options: {
            Name: 'datadog',
            host: 'http-intake.logs.datadoghq.com',
            dd_service: 'turnoutmigrate',
            dd_source: 'djangomigrate',
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
        environment: datadogEnv.for_service('turnoutmigrate', env),
        secrets: secrets.for_env(env),
      },
    ]
  ),
  memory: '8192',
  requiresCompatibilities: ['FARGATE'],
  networkMode: 'awsvpc',
  cpu: '4096',
}
