local datadogContainers = import 'include/datadog_containers.libsonnet';
local turnoutContainer = import 'include/turnout_container.libsonnet';
local env = std.extVar('env');
local capitalEnv = std.asciiUpper(env[0]) + env[1:];
local cpu = std.extVar('cpu');
local memory = std.extVar('memory');

{
  executionRoleArn: 'arn:aws:iam::719108811834:role/Turnout-ECS-' + capitalEnv,
  taskRoleArn: 'arn:aws:iam::719108811834:role/Turnout-ECS-' + capitalEnv + '-TaskRole',
  containerDefinitions: [
    turnoutContainer.common('turnoutworker', 'celery', '/app/ops/worker_health.sh || exit 1') + {
      name: 'worker',
      command: ['/app/ops/worker_launch.sh', 'default,leouptime,usvf'],
    },
    turnoutContainer.common('turnoutworker', 'celery', '/app/ops/worker_health.sh || exit 1') + {
      name: 'workerbulk',
      command: ['/app/ops/worker_launch.sh', 'tokens'],
    },
    turnoutContainer.common('turnoutworker', 'celery', '/app/ops/worker_health.sh || exit 1') + {
      name: 'workerhigh',
      command: ['/app/ops/worker_launch.sh', 'high-pri'],
    },
  ] + datadogContainers.for_env(env),
  memory: '2048',
  requiresCompatibilities: ['FARGATE'],
  networkMode: 'awsvpc',
  cpu: '1024',
}
