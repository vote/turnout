import multiprocessing

access_log_format = (
    '%(h)s %({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
)
timeout = 75
keepalive = 75
num_proc = multiprocessing.cpu_count()
workers = (num_proc * 2) + 1
accesslog = "-"
errorlog = "-"
