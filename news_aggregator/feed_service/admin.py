from django.contrib import admin

from .models import Feed
from .models import FeedEntry
from .models import UserFeedSubscription


class FeedEntryInline(admin.TabularInline):
    model = FeedEntry
    extra = 0
    fields = ("title", "author", "published_at", "has_translation", "has_summary")
    readonly_fields = (
        "title",
        "author",
        "published_at",
        "has_translation",
        "has_summary",
    )
    can_delete = False
    max_num = 0
    show_change_link = True
    ordering = ("-published_at",)

    @admin.display(boolean=True)
    def has_translation(self, obj):
        return bool(obj.title_translated and obj.content_translated)

    @admin.display(boolean=True)
    def has_summary(self, obj):
        return bool(obj.summary)


@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "url",
        "feed_type",
        "last_updated",
        "is_active",
        "subscriber_count",
    )
    list_filter = ("is_active", "created_at", "feed_type")
    search_fields = ("title", "description")
    list_editable = ("feed_type", "is_active")
    actions = ["set_as_rss", "set_as_website"]
    inlines = [FeedEntryInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "url",
                    "description",
                    "feed_type",
                    "is_active",
                ),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("last_updated", "created_at"),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ("last_updated", "created_at")

    @admin.display(description="Active Subscribers")
    def subscriber_count(self, obj):
        return obj.subscribers.filter(is_active=True).count()

    @admin.action(description="Set selected feeds as RSS feeds")
    def set_as_rss(self, request, queryset):
        updated = queryset.update(feed_type=Feed.FEED_TYPE_RSS)
        self.message_user(request, f"Changed {updated} feeds to RSS type.")

    @admin.action(description="Set selected feeds as website feeds")
    def set_as_website(self, request, queryset):
        updated = queryset.update(feed_type=Feed.FEED_TYPE_WEBSITE)
        self.message_user(request, f"Changed {updated} feeds to website type.")


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
        "full_content",
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
                "fields": (
                    "feed",
                    "title",
                    "url",
                    "full_content",
                    "author",
                    "published_at",
                    "article_load_error",
                    "article_loaded_at",
                ),
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
