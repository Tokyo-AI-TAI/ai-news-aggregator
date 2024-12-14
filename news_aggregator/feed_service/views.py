from urllib.error import HTTPError
from urllib.error import URLError
from xml.etree.ElementTree import ParseError

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .forms import AddFeedForm
from .models import Feed
from .models import UserFeedSubscription
from .services import FeedService


@login_required
@require_http_methods(["GET", "POST"])
def add_feed(request):
    """
    GET: Show the feed URL input form
    POST: Preview feed or subscribe to it
    """
    form = AddFeedForm(request.POST or None)
    context = {"form": form, "preview_data": None, "error": None}

    if request.method == "POST":
        action = request.POST.get("action")
        is_rss = request.POST.get("is_rss") == "on"

        if action == "subscribe" and request.POST.get("url"):
            return handle_feed_subscription(request, request.POST["url"], is_rss)

        if form.is_valid():
            try:
                preview_data = FeedService.preview_feed(
                    form.cleaned_data["url"], is_rss=is_rss
                )
                context["preview_data"] = preview_data
            except (URLError, HTTPError) as e:
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse(
                        {"status": "error", "message": f"Failed to fetch feed: {e}"}
                    )
                context["error"] = f"Failed to fetch feed: {e}"
            except (ParseError, ValueError) as e:
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse(
                        {"status": "error", "message": f"Invalid feed format: {e}"}
                    )
                context["error"] = f"Invalid feed format: {e}"

    return render(request, "feed_service/add_feed.html", context)


def handle_feed_subscription(request, url, is_rss=True):
    """Handle the actual feed subscription after preview."""
    try:
        preview_data = FeedService.preview_feed(url, is_rss=is_rss)

        if preview_data.is_already_in_db:
            feed = Feed.objects.get(url=url)
            if UserFeedSubscription.objects.filter(
                user=request.user, feed=feed, is_active=True
            ).exists():
                messages.error(request, "You are already subscribed to this feed")
                return redirect("feed_service:add_feed")
        else:
            feed = FeedService.create_feed_from_url(url, is_rss=is_rss)

        UserFeedSubscription.objects.create(user=request.user, feed=feed)
        messages.success(request, "Successfully subscribed to feed")
        return redirect("dashboard:feed_list")

    except IntegrityError as e:
        messages.error(request, f"Failed to subscribe to feed: {e}")
    except (URLError, HTTPError, ParseError, ValueError) as e:
        messages.error(request, f"Failed to process feed: {e}")

    return redirect("feed_service:add_feed")
