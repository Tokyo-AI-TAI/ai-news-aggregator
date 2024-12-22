import logging
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import feedparser
from django.conf import settings
from django.utils import timezone
from feedparser import FeedParserDict
from newspaper import Article
from openai import OpenAI
from parsera import Parsera
from pydantic import BaseModel

from news_aggregator.feed_service.models import FeedEntry
from news_aggregator.feed_service.models import UserFeedSubscription
from news_aggregator.feed_service.models import Feed
from news_aggregator.feed_service.models import UserArticleInteraction

logger = logging.getLogger(__name__)


@dataclass
class FeedParseResult:
    """Result of parsing a feed, whether RSS or website"""

    title: str
    description: str
    entries: list[dict]
    is_website: bool


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
    feed_type: str = "RSS Feed"  # Default to RSS Feed


class FeedService:
    @staticmethod
    def parse_rss_feed(url: str) -> FeedParseResult:
        """
        Parse a URL as an RSS feed using feedparser.
        Returns a FeedParseResult with normalized feed data.
        Raises ValueError if parsing fails or feed is invalid.
        """
        parsed = feedparser.parse(url)
        if parsed.bozo and not parsed.entries:
            raise ValueError(
                "Invalid RSS feed format. If this is a regular website, try unchecking 'This is an RSS feed'"
            )

        feed_data = parsed.feed
        if not feed_data:
            raise ValueError("No feed data found")

        entries = []
        for entry in parsed.entries:
            if not entry.get("title") or not entry.get("link"):
                continue

            entries.append(
                {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "description": entry.get("description", ""),
                    "author": entry.get("author", ""),
                    "published_parsed": entry.get("published_parsed")
                    or entry.get("updated_parsed"),
                }
            )

        if not entries:
            raise ValueError(
                "No valid entries found in the RSS feed. If this is a regular website, try unchecking 'This is an RSS feed'"
            )

        return FeedParseResult(
            title=feed_data.get("title") or urlparse(url).netloc,
            description=feed_data.get("description", ""),
            entries=entries,
            is_website=False,
        )

    @staticmethod
    def parse_website(url: str) -> FeedParseResult:
        """
        Parse a regular website using Parsera.
        Returns a FeedParseResult with normalized feed data.
        Raises ValueError if parsing fails or no valid content is found.
        """
        elements = {
            "site_title": "Main website title or brand name from the header/banner area",
            "site_description": "Website's description, tagline, or about text if available",
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
            # logger.debug("Parsera raw output for %s: %s", url, parsed_data)

            if not isinstance(parsed_data, dict):
                raise ValueError(
                    "Failed to parse website content. If this is an RSS feed, try checking 'This is an RSS feed'"
                )

            domain = urlparse(url).netloc
            site_title = (parsed_data.get("site_title") or "").strip() or domain
            site_description = (
                parsed_data.get("site_description") or ""
            ).strip() or f"News from {domain}"

            news_items = parsed_data.get("news", [])
            if not isinstance(news_items, list):
                news_items = [news_items] if isinstance(news_items, dict) else []

            entries = []
            for entry in news_items:
                if not isinstance(entry, dict):
                    continue

                title = (entry.get("title") or "").strip()
                link = (entry.get("link") or "").strip()

                if not (title and link):
                    continue

                entries.append(
                    {
                        "title": title,
                        "link": link,
                        "description": (entry.get("subtitle") or "").strip(),
                        "author": (entry.get("author") or "").strip(),
                        "published": (entry.get("publish_date") or "").strip(),
                    }
                )

            if not entries:
                raise ValueError(
                    "No news entries found on this website. If this is an RSS feed, try checking 'This is an RSS feed'"
                )

            return FeedParseResult(
                title=site_title,
                description=site_description,
                entries=entries,
                is_website=True,
            )

        except Exception as e:
            logger.error("Failed to parse website %s: %s", url, str(e))
            raise ValueError(str(e))

    @staticmethod
    def parse_feed(url: str, is_rss: bool = True) -> FeedParseResult:
        """
        Parse a URL as either an RSS feed or website based on is_rss parameter.
        This is the main entry point for feed parsing.
        """
        if is_rss:
            return FeedService.parse_rss_feed(url)
        return FeedService.parse_website(url)

    @staticmethod
    def validate_feed_data(parsed: FeedParserDict | dict) -> None:
        """
        Validate parsed feed or website data.
        Raises ValueError with a descriptive message if the data is invalid.
        """
        if not isinstance(parsed, (dict, FeedParserDict)) or not parsed.get("feed"):
            raise ValueError("Failed to parse content structure")

        entries = (
            parsed.get("entries", []) if isinstance(parsed, dict) else parsed.entries
        )

        if not entries:
            raise ValueError("No content entries found")

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
    def create_feed_entry(feed: Feed, entry_data: dict) -> FeedEntry:
        """
        Create a new FeedEntry from parsed entry data.
        Handles both RSS and website entry formats.
        """
        # Handle the published date based on entry format
        if "published_parsed" in entry_data:
            # RSS format
            published = entry_data["published_parsed"]
            published_at = (
                timezone.datetime(*published[:6]) if published else timezone.now()
            )
        else:
            # Website format
            published_str = entry_data.get("published")
            published_at = (
                timezone.datetime.fromisoformat(published_str)
                if published_str
                else timezone.now()
            )

        return FeedEntry.objects.create(
            feed=feed,
            title=entry_data.get("title", ""),
            url=entry_data.get("link", ""),
            full_content=entry_data.get("description", ""),
            author=entry_data.get("author") or "",
            published_at=published_at,
        )

    @staticmethod
    def preview_feed(feed_url: str, is_rss: bool = True) -> FeedPreview:
        """
        Fetch feed information without saving to database.
        Works with both RSS feeds and regular websites based on is_rss parameter.
        """
        try:
            parsed = FeedService.parse_feed(feed_url, is_rss=is_rss)
            FeedService.validate_feed_data(
                {"feed": {"title": parsed.title}, "entries": parsed.entries}
            )
        except Exception as e:
            raise ValueError(f"Failed to parse feed: {e!s}") from e

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
            title=parsed.title,
            description=parsed.description,
            entry_count=len(parsed.entries),
            latest_entries=latest_entries,
            is_already_in_db=existing_feed is not None,
            feed_id=existing_feed.pk if existing_feed else None,
            feed_type="RSS Feed" if is_rss else "Website",
        )

    @staticmethod
    def create_feed_from_url(feed_url: str, is_rss: bool = True) -> Feed:
        """
        Create a new feed and its initial entries from a feed URL.
        The is_rss parameter determines whether to parse as RSS or website.
        Returns the created Feed object.
        Raises ValueError if parsing fails.
        """
        try:
            parsed = FeedService.parse_feed(feed_url, is_rss=is_rss)
            FeedService.validate_feed_data(
                {"feed": {"title": parsed.title}, "entries": parsed.entries}
            )
        except Exception as e:
            raise ValueError(f"Failed to parse feed: {e!s}") from e

        feed = Feed.objects.create(
            title=parsed.title,
            url=feed_url,
            description=parsed.description,
            last_updated=timezone.now(),
            feed_type=Feed.FEED_TYPE_RSS if is_rss else Feed.FEED_TYPE_WEBSITE,
        )

        # Add up to 10 most recent entries
        for entry in parsed.entries[:10]:
            FeedService.create_feed_entry(feed, entry)

        return feed

    @staticmethod
    def update_feed(feed: Feed) -> tuple[int, list[str]]:
        """
        Update a feed with new entries.
        Returns a tuple of (number of new entries added, list of errors if any)
        """
        errors = []
        new_entries_count = 0

        try:
            # Use the feed's stored type to determine parsing method
            is_rss = feed.feed_type == Feed.FEED_TYPE_RSS
            parsed = FeedService.parse_feed(feed.url, is_rss=is_rss)
            FeedService.validate_feed_data(
                {"feed": {"title": parsed.title}, "entries": parsed.entries}
            )

            for entry in parsed.entries:
                url = entry.get("link", "").strip()
                if not url or feed.entries.filter(url=url).exists():
                    continue

                try:
                    FeedService.create_feed_entry(feed, entry)
                    new_entries_count += 1
                except Exception as entry_error:
                    errors.append(f"Error adding entry {url}: {str(entry_error)}")

            feed.last_updated = timezone.now()
            feed.save()

        except Exception as e:
            errors.append(f"Error updating feed: {str(e)}")

        return new_entries_count, errors

    @staticmethod
    def load_article_content(entry: FeedEntry) -> tuple[bool, str]:
        """
        Load the full article content for a feed entry using newspaper3k.
        Returns a tuple of (success, error_message).
        """
        if entry.article_loaded_at:
            return True, ""

        try:
            article = Article(entry.url)
            article.download()
            article.parse()

            if not article.text:
                return False, "No article text could be extracted"

            entry.full_content = article.text
            entry.article_loaded_at = timezone.now()
            entry.article_load_error = ""  # Clear the error message on success
            entry.save()
            return True, ""

        except Exception as e:
            error_msg = f"Failed to load article: {str(e)}"
            entry.article_load_error = error_msg
            entry.save()
            return False, error_msg


class ArticleAnalysis(BaseModel):
    """Structured output format for article analysis."""

    summary: str
    relevance_score: int
    error: Optional[str] = None


class AIService:
    def __init__(self):
        self.client = OpenAI()

    def process_article_for_user(
        self, entry: FeedEntry, user: "User"
    ) -> ArticleAnalysis:
        """Summarize (and possibly translate) an article for a specific user, generating a custom summary and relevance score."""
        try:
            # Create system message with clear instructions
            system_message = """You are a precise article summarizer that processes content
            and provides summaries focused on user interests."""

            # Create user message with article content
            user_message = f"""Consider the user's interests: "{user.interests}"

Article Title: {entry.title}
Article Content: {entry.full_content}

Please provide a very short summary (TLDR, no more than two sentences) of this content, translate to English if needed, and focus on aspects matching user interests.
Do not narrate about the article contents or discuss its relevancy in the summary, just directly summarize the content.
If the content is not relevant to the user, simply provide a general summary. Adapting to the user's interests is only secondary.
"""

            # Use the parse method with structured outputs
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                response_format=ArticleAnalysis,
            )

            # Get the parsed response
            result = completion.choices[0].message.parsed

            # Check for refusal
            if completion.choices[0].message.refusal:
                return ArticleAnalysis(
                    summary="",
                    relevance_score=0,
                    error=f"AI refused to process: {completion.choices[0].message.refusal}",
                )

            return result

        except Exception as e:
            error_msg = f"Error processing article {entry.pk}: {str(e)}"
            logger.error(error_msg)
            return ArticleAnalysis(summary="", relevance_score=0, error=error_msg)

    @classmethod
    def process_entry_for_all_users(cls, entry: FeedEntry) -> None:
        """Process a feed entry for all subscribed users."""
        ai_service = cls()

        # Get all active subscribers for this feed
        subscriptions = UserFeedSubscription.objects.filter(
            feed=entry.feed, is_active=True
        ).select_related("user")

        for subscription in subscriptions:
            result = ai_service.process_article_for_user(entry, subscription.user)

            if not result.error:
                # Create or update the user's interaction with this article
                UserArticleInteraction.objects.update_or_create(
                    user=subscription.user,
                    entry=entry,
                    defaults={
                        "custom_summary": result.summary,
                        "relevance_score": result.relevance_score,
                    },
                )
            else:
                logger.error(
                    f"Failed to process entry {entry.pk} for user {subscription.user.pk}: {result.error}"
                )
