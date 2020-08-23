from psycogreen.gevent import patch_psycopg

timeout = 75
keepalive = 75
accesslog = "-"
errorlog = "-"
num_proc = 1
worker_class = "gevent"
workers = 2
access_log_format = "%(t)s '%(r)s' %(s)s %(b)s %(a)s"


def post_fork(server, worker):
    patch_psycopg()
