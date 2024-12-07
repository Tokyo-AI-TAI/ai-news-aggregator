from dataclasses import dataclass
from urllib.parse import urlparse

import feedparser
from django.utils import timezone
from feedparser import FeedParserDict

from .models import Feed
from .models import FeedEntry


@dataclass
class FeedPreview:
    """Preview of a feed before it's added to the database"""

    url: str
    title: str
    description: str
    entry_count: int
    latest_entries: list[dict]
    is_already_in_db: bool = False
    feed_id: int | None = None


class FeedService:
    @staticmethod
    def _validate_feed(parsed: FeedParserDict, url: str) -> None:
        """
        Validate a parsed feed.
        Raises ValueError with a descriptive message if the feed is invalid.
        """
        if not parsed.feed:
            raise ValueError("URL does not contain a valid RSS/Atom feed")

        if parsed.bozo and not parsed.entries:
            bozo_exception = parsed.get("bozo_exception")
            if bozo_exception:
                raise ValueError(f"Feed error: {bozo_exception!s}")
            raise ValueError("Invalid feed format")

        if not parsed.entries:
            raise ValueError("Feed contains no entries")

        required_entry_fields = ["title", "link"]
        if parsed.entries:
            missing_fields = [
                field
                for field in required_entry_fields
                if not parsed.entries[0].get(field)
            ]
            if missing_fields:
                missing_fields_str = ", ".join(missing_fields)
                raise ValueError(
                    f"Feed entries are missing required fields: {missing_fields_str}"
                )

    @staticmethod
    def preview_feed(feed_url: str) -> FeedPreview:
        """
        Fetch feed information without saving to database.
        Returns a FeedPreview object.
        Raises ValueError if the URL is not a valid feed.
        """
        try:
            parsed = feedparser.parse(feed_url)
            FeedService._validate_feed(parsed, feed_url)
        except Exception as e:
            raise ValueError(f"Failed to parse feed: {e!s}") from e

        # Check if feed already exists
        existing_feed = Feed.objects.filter(url=feed_url).first()

        latest_entries = [
            {
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "author": entry.get("author", ""),
                "summary": entry.get("description", "")[:200] + "..."
                if entry.get("description")
                else "",
            }
            for entry in parsed.entries[:5]  # Preview only 5 latest entries
        ]

        return FeedPreview(
            url=feed_url,
            title=parsed.feed.get("title") or urlparse(feed_url).netloc,
            description=parsed.feed.get("description", ""),
            entry_count=len(parsed.entries),
            latest_entries=latest_entries,
            is_already_in_db=existing_feed is not None,
            feed_id=existing_feed.pk if existing_feed else None,
        )

    @staticmethod
    def create_feed_from_url(feed_url: str) -> Feed:
        """
        Create a new feed and its initial entries from a feed URL.
        Returns the created Feed object.
        Raises ValueError if the URL is not a valid feed.
        """
        try:
            parsed = feedparser.parse(feed_url)
            FeedService._validate_feed(parsed, feed_url)
        except Exception as e:
            raise ValueError(f"Failed to parse feed: {e!s}") from e

        feed = Feed.objects.create(
            title=parsed.feed.get("title") or urlparse(feed_url).netloc,
            url=feed_url,
            description=parsed.feed.get("description", ""),
            last_updated=timezone.now(),
        )

        # Add up to 10 most recent entries
        for entry in parsed.entries[:10]:
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            published_at = (
                timezone.datetime(*published[:6]) if published else timezone.now()
            )

            FeedEntry.objects.create(
                feed=feed,
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                content=entry.get("description", ""),
                author=entry.get("author", ""),
                published_at=published_at,
            )

        return feed
