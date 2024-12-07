from django.contrib import admin

from .models import Feed
from .models import FeedEntry
from .models import UserFeedSubscription


@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    list_display = ("title", "url", "last_updated", "is_active", "subscriber_count")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "description")

    @admin.display(description="Active Subscribers")
    def subscriber_count(self, obj):
        return obj.subscribers.filter(is_active=True).count()


@admin.register(FeedEntry)
class FeedEntryAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "feed",
        "author",
        "published_at",
        "has_translation",
        "has_summary",
    )
    list_filter = ("feed", "published_at", "last_processed")
    search_fields = (
        "title",
        "content",
        "author",
        "title_translated",
        "content_translated",
        "summary",
    )
    raw_id_fields = ("feed",)
    readonly_fields = ("last_processed",)
    fieldsets = (
        (
            None,
            {
                "fields": ("feed", "title", "url", "content", "author", "published_at"),
            },
        ),
        (
            "AI Generated Content",
            {
                "fields": (
                    "title_translated",
                    "content_translated",
                    "summary",
                    "translation_language",
                    "last_processed",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(boolean=True)
    def has_translation(self, obj):
        return bool(obj.title_translated and obj.content_translated)

    @admin.display(boolean=True)
    def has_summary(self, obj):
        return bool(obj.summary)


@admin.register(UserFeedSubscription)
class UserFeedSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "feed", "subscribed_at", "is_active")
    list_filter = ("is_active", "subscribed_at", "feed")
    search_fields = ("user__username", "user__email", "feed__title")
    raw_id_fields = ("user", "feed")
    date_hierarchy = "subscribed_at"
    actions = ["activate_subscriptions", "deactivate_subscriptions"]

    @admin.display(description="Activate selected subscriptions")
    def activate_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} subscriptions.")

    @admin.display(description="Deactivate selected subscriptions")
    def deactivate_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} subscriptions.")
