import logging
from dataclasses import dataclass
from urllib.parse import urlparse

import feedparser
from django.utils import timezone
from feedparser import FeedParserDict
from parsera import Parsera

from .models import Feed
from .models import FeedEntry

logger = logging.getLogger(__name__)


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
    def _validate_feed(parsed: FeedParserDict | dict, url: str) -> None:
        """
        Validate a parsed feed or website data.
        Raises ValueError with a descriptive message if the data is invalid.
        """
        # Check for basic structure (both RSS and website parsing should provide this)
        if not isinstance(parsed, (dict, FeedParserDict)) or not parsed.get("feed"):
            raise ValueError("Failed to parse content structure")

        # Get entries consistently for both types
        entries = (
            parsed.get("entries", []) if isinstance(parsed, dict) else parsed.entries
        )

        if not entries:
            raise ValueError("No content entries found")

        # Validate first entry has minimum required fields
        required_entry_fields = ["title", "link"]
        first_entry = entries[0]
        missing_fields = [
            field for field in required_entry_fields if not first_entry.get(field)
        ]
        if missing_fields:
            missing_fields_str = ", ".join(missing_fields)
            raise ValueError(
                f"Content entries are missing required fields: {missing_fields_str}"
            )

    @staticmethod
    def _parse_website(url: str) -> dict:
        """
        Parse a regular website using Parsera.
        Returns a dict with feed-like structure including site metadata and article details.
        Raises ValueError if the parsed data is invalid or missing required fields.
        """
        elements = {
            # Site metadata
            "site_title": "Main website title or brand name from the header/banner area",
            "site_description": "Website's description, tagline, or about text if available",
            # News articles list - simplified structure
            "news": [
                {
                    "title": "News article title. Only include actual news entries, ignore page metadata.",
                    "subtitle": "News article subtitle or summary. Leave empty if not available.",
                    "link": "The full, clean link to the news article entry",
                    "publish_date": "Article publication date in ISO format",
                    "author": "Article author name if available",
                }
            ],
        }

        try:
            scraper = Parsera()
            parsed_data = scraper.run(url=url, elements=elements)

            logger.debug("Parsera raw output for %s: %s", url, parsed_data)

            if not isinstance(parsed_data, dict):
                raise ValueError("Parsera returned invalid data structure")

            # Get site metadata with fallbacks
            domain = urlparse(url).netloc
            site_title = (parsed_data.get("site_title") or "").strip() or domain
            site_description = (
                parsed_data.get("site_description") or ""
            ).strip() or f"News from {domain}"

            # Safely get news items - simplified access
            news_items = parsed_data.get("news", [])
            if not isinstance(news_items, list):
                news_items = [news_items] if isinstance(news_items, dict) else []

            # Initialize feed structure
            feed_structure = {
                "feed": {
                    "title": site_title,
                    "description": site_description,
                },
                "entries": [],
            }

            # Process entries with careful validation
            for entry in news_items:
                if not isinstance(entry, dict):
                    continue

                title = (entry.get("title") or "").strip()
                link = (entry.get("link") or "").strip()

                if not (title and link):  # Skip entries without required fields
                    continue

                feed_structure["entries"].append(
                    {
                        "title": title,
                        "link": link,
                        "description": (entry.get("subtitle") or "").strip(),
                        "author": (entry.get("author") or "").strip(),
                        "published": (entry.get("publish_date") or "").strip(),
                    }
                )

            if not feed_structure["entries"]:
                raise ValueError("No valid entries found in parsed website content")

            logger.debug("Transformed feed structure for %s: %s", url, feed_structure)

            return feed_structure

        except Exception as e:
            logger.error("Failed to parse website %s: %s", url, str(e))
            raise ValueError(f"Failed to parse website content: {e!s}")

    @staticmethod
    def _parse_feed(url: str) -> FeedParserDict:
        """Try parsing as RSS first, if fails try as website."""
        parsed = feedparser.parse(url)

        if parsed.bozo and not parsed.entries:
            # Not a valid RSS feed, try parsing as website
            try:
                return FeedService._parse_website(url)  # type: ignore
            except Exception as e:
                raise ValueError(f"Failed to parse as RSS or website: {e}")

        return parsed

    @staticmethod
    def preview_feed(feed_url: str) -> FeedPreview:
        """
        Fetch feed information without saving to database.
        Works with both RSS feeds and regular websites.
        """
        try:
            parsed = FeedService._parse_feed(feed_url)
            FeedService._validate_feed(parsed, feed_url)
        except Exception as e:
            raise ValueError(f"Failed to parse feed: {e!s}") from e

        # Check if feed already exists
        existing_feed = Feed.objects.filter(url=feed_url).first()

        # Use get() to safely access entries
        entries = (
            parsed.get("entries", []) if isinstance(parsed, dict) else parsed.entries
        )

        latest_entries = [
            {
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "author": entry.get("author", ""),
                "summary": entry.get("description", "")[:200] + "..."
                if entry.get("description")
                else "",
            }
            for entry in entries[:5]  # Preview only 5 latest entries
        ]

        # Handle both dict and FeedParserDict cases
        feed_data = parsed.get("feed", {}) if isinstance(parsed, dict) else parsed.feed

        return FeedPreview(
            url=feed_url,
            title=feed_data.get("title") or urlparse(feed_url).netloc,
            description=feed_data.get("description", ""),
            entry_count=len(entries),
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
            parsed = FeedService._parse_feed(feed_url)
            FeedService._validate_feed(parsed, feed_url)
        except Exception as e:
            raise ValueError(f"Failed to parse feed: {e!s}") from e

        # Handle both dict (website) and FeedParserDict (RSS) cases
        feed_data = parsed.get("feed", {}) if isinstance(parsed, dict) else parsed.feed

        feed = Feed.objects.create(
            title=feed_data.get("title") or urlparse(feed_url).netloc,
            url=feed_url,
            description=feed_data.get("description", ""),
            last_updated=timezone.now(),
        )

        # Get entries consistently for both types
        entries = (
            parsed.get("entries", []) if isinstance(parsed, dict) else parsed.entries
        )

        # Add up to 10 most recent entries
        for entry in entries[:10]:
            # For website parsing, published_parsed won't exist, so we'll use the raw date
            published = None
            if isinstance(parsed, dict):
                # Handle website date format
                published_str = entry.get("published")
                published_at = (
                    timezone.datetime.fromisoformat(published_str)
                    if published_str
                    else timezone.now()
                )
            else:
                # Handle RSS date format
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                published_at = (
                    timezone.datetime(*published[:6]) if published else timezone.now()
                )

            FeedEntry.objects.create(
                feed=feed,
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                content=entry.get("description", ""),
                author=entry.get("author") or "",
                published_at=published_at,
            )

        return feed
