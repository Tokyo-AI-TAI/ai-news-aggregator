from django.urls import path

from . import views

app_name = "dashboard"
urlpatterns = [
    path("", views.feed_list, name="feed_list"),
    path("feed/<int:feed_id>/", views.feed_detail, name="feed_detail"),
]
