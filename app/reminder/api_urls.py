from rest_framework import routers

from .api_views import ReminderRequestViewSet

router = routers.SimpleRouter()
router.register(r"signup", ReminderRequestViewSet)

app_name = "api_reminders"
urlpatterns = router.urls
