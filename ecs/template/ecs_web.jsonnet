local datadogContainers = import 'include/datadog_containers.libsonnet';
local datadogEnv = import 'include/datadog_env.libsonnet';
local secrets = import 'include/secrets.libsonnet';
local turnoutContainer = import 'include/turnout_container.libsonnet';
local env = std.extVar('env');
local capitalEnv = std.asciiUpper(env[0]) + env[1:];
local migrations = std.extVar('migrations');
local cpu = std.extVar('cpu');
local memory = std.extVar('memory');

{
  executionRoleArn: 'arn:aws:iam::719108811834:role/Turnout-ECS-' + capitalEnv,
  taskRoleArn: 'arn:aws:iam::719108811834:role/Turnout-ECS-' + capitalEnv + '-TaskRole',
  containerDefinitions: [
    turnoutContainer.essential_secrets('turnoutweb', 'django', '/app/ops/web_health.sh || exit 1') + {
      name: 'web',
      portMappings: [
        {
          hostPort: 8000,
          protocol: 'tcp',
          containerPort: 8000,
        },
      ],
    },

    turnoutContainer.essential_secrets('turnoutworker', 'celery', '/app/ops/worker_health.sh || exit 1') + {
      name: 'worker',
      command: ['/app/ops/worker_launch.sh', 'default,uptime'],
    },

    turnoutContainer.essential_base_secrets('turnoutbeat', 'celerybeat', '/app/ops/beat_health.sh || exit 1') + {
      name: 'beat',
      command: ['/app/ops/beat_launch.sh'],
    },
  ] + datadogContainers.for_env(env) + (
    if !migrations then [] else [
      {
        name: 'migration',
        command: ['ddtrace-run', 'python', 'manage.py', 'migrate'],
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
        essential: false,
      } + turnoutContainer.common_secrets('turnoutmigrate', 'djangomigrate'),
    ]
  ),
  memory: '8192',
  requiresCompatibilities: ['FARGATE'],
  networkMode: 'awsvpc',
  cpu: '4096',
}
