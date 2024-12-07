from django.contrib import admin

from .models import Feed
from .models import FeedEntry


@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    list_display = ("title", "url", "last_updated", "is_active")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "description")


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
