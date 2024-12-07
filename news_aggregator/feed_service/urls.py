from django.urls import path

from . import views

app_name = "feed_service"

urlpatterns = [
    path("add/", views.add_feed, name="add_feed"),
]
