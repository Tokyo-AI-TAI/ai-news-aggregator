from django.db import models
from django.utils import timezone


class Feed(models.Model):
    title = models.CharField(max_length=200)
    url = models.URLField(unique=True)
    description = models.TextField(blank=True)
    last_updated = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class FeedEntry(models.Model):
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE, related_name="entries")
    title = models.CharField(max_length=200)
    url = models.URLField()
    content = models.TextField()
    author = models.CharField(max_length=100, blank=True)
    published_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    # AI-generated fields
    title_translated = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="AI-translated title",
    )
    content_translated = models.TextField(
        blank=True,
        default="",
        help_text="AI-translated content",
    )
    summary = models.TextField(
        blank=True,
        default="",
        help_text="AI-generated summary of the content",
    )
    translation_language = models.CharField(
        max_length=10,
        blank=True,
        default="",
        help_text="Language code of the translation",
    )
    last_processed = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the entry was last processed by AI",
    )

    class Meta:
        ordering = ["-published_at"]
        verbose_name_plural = "Feed entries"

    def __str__(self):
        return self.title
