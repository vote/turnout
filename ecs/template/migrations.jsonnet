local datadog = import 'include/datadog.libsonnet';
local secrets = import 'include/secrets.libsonnet';

local env = std.extVar('env');
local capitalEnv = std.asciiUpper(env[0]) + env[1:];

{
  executionRoleArn: 'arn:aws:iam::719108811834:role/Turnout-ECS-' + capitalEnv,
  taskRoleArn: 'arn:aws:iam::719108811834:role/Turnout-ECS-' + capitalEnv + '-TaskRole',
  containerDefinitions: [
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

    {
      image: 'nginx/nginx:latest',
      name: 'migration',
      command: ['./manage.py', 'migrate'],
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
      environment: datadog.for_service('turnoutmigrate', env),
      secrets: secrets.for_env(env),
    },

    {
      image: 'nginx/nginx:latest',
      name: 'health',
      command: ['true'],
      dependsOn: [
        {
          containerName: 'migration',
          condition: 'SUCCESS',
        },
      ],
      essential: true,
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
      environment: datadog.for_service('turnoutmigratehealth', env),
      secrets: secrets.for_env(env),
    },
  ],
  memory: '1024',
  requiresCompatibilities: ['FARGATE'],
  networkMode: 'awsvpc',
  cpu: '512',
}
