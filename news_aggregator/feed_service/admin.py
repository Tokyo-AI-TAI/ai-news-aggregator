from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import Feed
from .models import FeedEntry
from .models import UserFeedSubscription
from .models import UserArticleInteraction


class UserArticleInteractionInline(admin.StackedInline):
    model = UserArticleInteraction
    extra = 0
    fields = (
        ("user", "relevance_score", "processed_at"),
        "custom_summary",
    )
    readonly_fields = ("processed_at",)
    ordering = ("-processed_at",)
    can_delete = False
    max_num = 0
    show_change_link = True


class FeedEntryInline(admin.TabularInline):
    model = FeedEntry
    extra = 0
    fields = (
        "title",
        "author",
        "published_at",
        "article_status",
        "interaction_count",
    )
    readonly_fields = (
        "title",
        "author",
        "published_at",
        "article_status",
        "interaction_count",
    )
    can_delete = False
    max_num = 0
    show_change_link = True
    ordering = ("-published_at",)

    def article_status(self, obj):
        if obj.article_load_error:
            return format_html('<span style="color: red;">Error</span>')
        if obj.article_loaded_at:
            return format_html('<span style="color: green;">Loaded</span>')
        return "Pending"

    @admin.display(description="Interactions")
    def interaction_count(self, obj):
        return obj.user_interactions.count()


@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "url",
        "feed_type",
        "last_updated",
        "is_active",
        "subscriber_count",
        "entry_count",
    )
    list_filter = ("is_active", "created_at", "feed_type")
    search_fields = ("title", "description", "url")
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
        count = obj.subscribers.filter(is_active=True).count()
        url = (
            reverse("admin:feed_service_userfeedsubscription_changelist")
            + f"?feed__id__exact={obj.id}"
        )
        return format_html('<a href="{}">{}</a>', url, count)

    @admin.display(description="Entries")
    def entry_count(self, obj):
        count = obj.entries.count()
        url = (
            reverse("admin:feed_service_feedentry_changelist")
            + f"?feed__id__exact={obj.id}"
        )
        return format_html('<a href="{}">{}</a>', url, count)

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
        "feed_link",
        "author",
        "published_at",
        "article_status",
        "interaction_count",
    )
    list_filter = (
        "feed",
        "published_at",
        "last_processed",
        "article_loaded_at",
    )
    search_fields = (
        "title",
        "full_content",
        "author",
        "feed__title",
    )
    raw_id_fields = ("feed",)
    readonly_fields = ("last_processed", "article_loaded_at")
    inlines = [UserArticleInteractionInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "feed",
                    "title",
                    "url",
                    "author",
                    "published_at",
                ),
            },
        ),
        (
            "Content",
            {
                "fields": ("full_content",),
                "classes": ("collapse",),
            },
        ),
        (
            "Processing Status",
            {
                "fields": (
                    "article_load_error",
                    "article_loaded_at",
                    "last_processed",
                ),
            },
        ),
    )

    @admin.display(description="Feed")
    def feed_link(self, obj):
        url = reverse("admin:feed_service_feed_change", args=[obj.feed.id])
        return format_html('<a href="{}">{}</a>', url, obj.feed.title)

    def article_status(self, obj):
        if obj.article_load_error:
            return format_html('<span style="color: red;">Error</span>')
        if obj.article_loaded_at:
            return format_html('<span style="color: green;">Loaded</span>')
        return "Pending"

    @admin.display(description="User Interactions")
    def interaction_count(self, obj):
        count = obj.user_interactions.count()
        url = (
            reverse("admin:feed_service_userarticleinteraction_changelist")
            + f"?entry__id__exact={obj.id}"
        )
        return format_html('<a href="{}">{}</a>', url, count)


@admin.register(UserArticleInteraction)
class UserArticleInteractionAdmin(admin.ModelAdmin):
    list_display = (
        "user_link",
        "entry_link",
        "relevance_badge",
        "processed_at",
    )
    list_filter = (
        "user",
        "processed_at",
        "relevance_score",
        "entry__feed",
    )
    search_fields = (
        "user__username",
        "user__email",
        "entry__title",
        "entry__feed__title",
        "custom_summary",
    )
    raw_id_fields = ("user", "entry")
    readonly_fields = ("processed_at",)
    ordering = ("-processed_at",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("user", "entry"),
                    ("relevance_score", "processed_at"),
                ),
            },
        ),
        (
            "AI Generated Content",
            {
                "fields": ("custom_summary",),
            },
        ),
    )

    @admin.display(description="User")
    def user_link(self, obj):
        if not obj.user:
            return "No user"
        url = reverse("admin:users_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)

    @admin.display(description="Article")
    def entry_link(self, obj):
        url = reverse("admin:feed_service_feedentry_change", args=[obj.entry.id])
        return format_html('<a href="{}">{}</a>', url, obj.entry.title)

    @admin.display(description="Relevance")
    def relevance_badge(self, obj):
        if obj.relevance_score >= 80:
            color = "green"
        elif obj.relevance_score >= 50:
            color = "orange"
        else:
            color = "red"
        return format_html(
            '<span style="color: {}">{}</span>', color, obj.relevance_score
        )


@admin.register(UserFeedSubscription)
class UserFeedSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user_link",
        "feed_link",
        "subscribed_at",
        "is_active",
    )
    list_filter = ("is_active", "subscribed_at", "feed")
    search_fields = (
        "user__username",
        "user__email",
        "feed__title",
    )
    raw_id_fields = ("user", "feed")
    date_hierarchy = "subscribed_at"
    actions = ["activate_subscriptions", "deactivate_subscriptions"]

    @admin.display(description="User")
    def user_link(self, obj):
        if not obj.user:
            return "No user"
        url = reverse("admin:users_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)

    @admin.display(description="Feed")
    def feed_link(self, obj):
        url = reverse("admin:feed_service_feed_change", args=[obj.feed.id])
        return format_html('<a href="{}">{}</a>', url, obj.feed.title)

    @admin.action(description="Activate selected subscriptions")
    def activate_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} subscriptions.")

    @admin.action(description="Deactivate selected subscriptions")
    def deactivate_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} subscriptions.")
