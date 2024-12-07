from django.urls import path

from news_aggregator.dashboard import views

app_name = "dashboard"
urlpatterns = [
    path("", views.feed_list, name="feed_list"),
    path("feed/<int:feed_id>/", views.feed_detail, name="feed_detail"),
    path("feed/<int:feed_id>/subscribe/", views.subscribe_feed, name="subscribe_feed"),
    path(
        "feed/<int:feed_id>/unsubscribe/",
        views.unsubscribe_feed,
        name="unsubscribe_feed",
    ),
]
