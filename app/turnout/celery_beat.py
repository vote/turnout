from .celery_app import app

print("Beat Schedule")
print(app.conf.beat_schedule)
