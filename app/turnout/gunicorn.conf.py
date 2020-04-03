timeout = 75
keepalive = 75
accesslog = "-"
errorlog = "-"
access_log_format = (
    '{"message":"%(h)s %({x-forwarded-for}i)s %(l)s %(u)s %(t)s \'%(r)s\' %(s)s %(b)s %(f)s %(a)s",'
    '"remote_ip":"%(h)s","request_id":"%({X-Request-Id}i)s","response_code":"%(s)s",'
    '"request_method":"%(m)s","request_path":"%(U)s","request_querystring":"%(q)s",'
    '"request_timetaken":"%(D)s","response_length":"%(B)s","user_agent":"%(a)s",'
    '"cf_ipaddress":"%({CF-Connecting-IP}i)s","cf_country":"%({CF-IPCountry}i)s",'
    '"cf_ray":"%({CF-Ray}i)s","forwarded_for":"%({x-forwarded-for}i)s"}'
)
