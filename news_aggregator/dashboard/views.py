from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.core.paginator import Paginator

from news_aggregator.feed_service.models import Feed
from news_aggregator.feed_service.models import FeedEntry
from news_aggregator.feed_service.models import UserFeedSubscription


@login_required
def feed_list(request):
    """Display list of all feeds that the user has subscribed to."""
    # Get feeds with active subscriptions
    subscribed_feeds = (
        Feed.objects.filter(subscribers__user=request.user, subscribers__is_active=True)
        .prefetch_related("entries")
        .distinct()
    )

    # Get feeds that either have no subscription or only inactive subscriptions
    available_feeds = (
        Feed.objects.filter(is_active=True)
        .exclude(id__in=subscribed_feeds.values("id"))
        .distinct()
    )

    return render(
        request,
        "dashboard/feed_list.html",
        {
            "subscribed_feeds": subscribed_feeds,
            "available_feeds": available_feeds,
        },
    )


@login_required
def feed_detail(request, feed_id):
    """Display a single feed and all its entries if the user is subscribed."""
    feed = get_object_or_404(
        Feed.objects.prefetch_related("entries"),
        id=feed_id,
        subscribers__user=request.user,
        subscribers__is_active=True,
    )
    return render(request, "dashboard/feed_detail.html", {"feed": feed})


@login_required
def subscribe_feed(request, feed_id):
    """Subscribe to a feed."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    feed = get_object_or_404(Feed, id=feed_id)
    subscription, created = UserFeedSubscription.objects.get_or_create(
        user=request.user, feed=feed, defaults={"is_active": True}
    )

    # If subscription exists but was inactive, reactivate it
    if not created and not subscription.is_active:
        subscription.is_active = True
        subscription.save()

    return redirect("dashboard:feed_list")


@login_required
def unsubscribe_feed(request, feed_id):
    """Unsubscribe from a feed."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    subscription = get_object_or_404(
        UserFeedSubscription, user=request.user, feed_id=feed_id, is_active=True
    )
    subscription.is_active = False
    subscription.save()
    return redirect("dashboard:feed_list")


@login_required
def home(request):
    """Display a consolidated list of news entries from all subscribed feeds."""
    # Get all entries from active subscriptions, ordered by publication date
    entry_list = (
        FeedEntry.objects.filter(
            feed__subscribers__user=request.user,
            feed__subscribers__is_active=True,
        )
        .select_related("feed")
        .prefetch_related("user_interactions")
        .order_by("-published_at")
    )

    # Add pagination with 20 items per page
    paginator = Paginator(entry_list, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    return render(request, "pages/home.html", {"page_obj": page_obj})
