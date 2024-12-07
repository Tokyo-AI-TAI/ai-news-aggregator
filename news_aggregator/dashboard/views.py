from django.shortcuts import get_object_or_404
from django.shortcuts import render

from news_aggregator.feed_service.models import Feed


def feed_list(request):
    """Display list of all feeds with their latest entries."""
    feeds = Feed.objects.prefetch_related("entries").all()
    return render(request, "dashboard/feed_list.html", {"feeds": feeds})


def feed_detail(request, feed_id):
    """Display a single feed and all its entries."""
    feed = get_object_or_404(Feed.objects.prefetch_related("entries"), id=feed_id)
    return render(request, "dashboard/feed_detail.html", {"feed": feed})
