from django.urls import path

from .api_views import test_optimizely

urlpatterns = [
    path("test-optimizely/", test_optimizely),
]
