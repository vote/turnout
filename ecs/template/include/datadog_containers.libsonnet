{
  for_env(env)::
    [
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
    ],
}
