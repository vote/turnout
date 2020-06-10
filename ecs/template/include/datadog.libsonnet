{
  for_service(service, env)::
    [
      {
        name: 'DD_TRACE_ANALYTICS_ENABLED',
        value: 'true',
      },
      {
        name: 'DATADOG_SERVICE_NAME',
        value: service,
      },
      {
        name: 'DATADOG_ENV',
        value: env,
      },
      {
        name: 'DD_LOGS_INJECTION',
        value: 'true',
      },
    ],
}
