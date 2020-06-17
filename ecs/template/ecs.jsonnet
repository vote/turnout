local datadog = import 'include/datadog.libsonnet';
local secrets = import 'include/secrets.libsonnet';

local env = std.extVar('env');
local capitalEnv = std.asciiUpper(env[0]) + env[1:];
local migrations = std.extVar('migrations');

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
          'curl --fail http://localhost:8000/-/health/ || exit 1',
        ],
        interval: 30,
        timeout: 5,
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
      environment: datadog.for_service('turnoutweb', env),
      secrets: secrets.for_env(env),
    },

    {
      image: 'nginx/nginx:latest',
      name: 'worker',
      command: [
        'ddtrace-run',
        'celery',
        '-A',
        'turnout.celery_app',
        'worker',
        '-Q',
        'default',
        '--without-heartbeat',
      ],
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
      environment: datadog.for_service('turnoutworker', env),
      secrets: secrets.for_env(env),
    },

    {
      image: 'nginx/nginx:latest',
      name: 'beat',
      command: [
        'ddtrace-run',
        'celery',
        '-A',
        'turnout.celery_app',
        'beat',
        '--scheduler',
        'redbeat.RedBeatScheduler',
      ],
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
      environment: datadog.for_service('turnoutbeat', env),
      secrets: secrets.for_env(env),
    },

    {
      environment: [
        {
          name: 'ECS_FARGATE',
          value: 'true',
        },
        {
          name: 'DD_DOCKER_LABELS_AS_TAGS',
          value: '{"spinnaker.stack":"spinnaker_stack", "spinnaker.servergroup":"spinnaker_servergroup", "spinnaker.detail":"spinnaker_detail", "spinnaker.stack":"env"}',
        },
        {
          name: 'DD_APM_ENABLED',
          value: 'true',
        },
        {
          name: 'DD_DOGSTATSD_NON_LOCAL_TRAFFIC',
          value: 'true',
        },
      ],
      secrets: [
        {
          valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/general.datadogkey',
          name: 'DD_API_KEY',
        },
      ],
      image: 'datadog/agent:latest',
      name: 'datadog-agent',
      essential: true,
      dependsOn: [
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
          dd_service: 'turnout-datadog',
          dd_source: 'datadog',
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
    },

    {
      essential: true,
      image: 'amazon/aws-for-fluent-bit:latest',
      name: 'log_router',
      firelensConfiguration: {
        type: 'fluentbit',
        options: { 'enable-ecs-log-metadata': 'true' },
      },
      logConfiguration: {
        logDriver: 'awslogs',
        options: {
          'awslogs-group': '/voteamerica/ecs/turnout/' + env,
          'awslogs-region': 'us-west-2',
          'awslogs-stream-prefix': 'turnout-fluentbit',
        },
      },
    },
  ] + (
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
            dd_tags: 'env:prod',
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
        environment: datadog.for_service('turnoutmigrate', env),
        secrets: secrets.for_env(env),
      },
    ]
  ),
  memory: '8192',
  requiresCompatibilities: ['FARGATE'],
  networkMode: 'awsvpc',
  cpu: '4096',
}
