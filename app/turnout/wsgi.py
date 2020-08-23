import os

from django.core.wsgi import get_wsgi_application
from gevent import monkey

monkey.patch_all()


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "turnout.settings")

application = get_wsgi_application()
