from django.core.management.base import BaseCommand
from django.utils import timezone
import logging
from news_aggregator.feed_service.models import Feed, FeedEntry
from news_aggregator.feed_service.services import FeedService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Updates all feeds in the database with new entries and loads full article content"
    MAX_ERRORS_TO_SHOW = 3

    def handle(self, *args, **options):
        feeds = Feed.objects.filter(is_active=True)
        self.stdout.write(f"Found {feeds.count()} active feeds to update")

        # Track results for each feed
        feed_results = []
        total_entries = 0
        total_articles_loaded = 0
        total_article_errors = 0

        for feed in feeds:
            result = {
                "feed": feed.title,
                "feed_type": feed.get_feed_type_display(),  # Get human-readable feed type
                "status": "success",
                "entries_added": 0,
                "articles_loaded": 0,
                "article_errors": 0,
                "errors": [],
            }

            try:
                self.stdout.write(
                    f"Updating {feed.get_feed_type_display()}: {feed.title} ({feed.url})"
                )
                entries_added, errors = FeedService.update_feed(feed)

                if errors:
                    result["status"] = "error"
                    result["errors"] = errors
                    for error in errors:
                        self.stdout.write(
                            self.style.ERROR(f"Error in {feed.title}: {error}")
                        )
                else:
                    if entries_added:
                        self.stdout.write(
                            f"Added {entries_added} new entries to {feed.title}"
                        )
                    else:
                        self.stdout.write("No new entries found")

                result["entries_added"] = entries_added
                total_entries += entries_added

                # Load full article content for new entries
                if entries_added > 0:
                    new_entries = feed.entries.filter(article_loaded_at__isnull=True)
                    for entry in new_entries:
                        self.stdout.write(f"Loading article content for: {entry.title}")
                        success, error = FeedService.load_article_content(entry)
                        if success:
                            result["articles_loaded"] += 1
                            total_articles_loaded += 1
                        else:
                            result["article_errors"] += 1
                            total_article_errors += 1
                            result["errors"].append(
                                f"Article load error for {entry.url}: {error}"
                            )

            except Exception as e:
                result["status"] = "error"
                result["errors"].append(str(e))
                logger.error(f"Error updating feed {feed.title}: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(f"Failed to update {feed.title}: {str(e)}")
                )

            feed_results.append(result)

        # Print detailed report
        self.stdout.write("\n=== Feed Update Report ===")
        success_count = sum(1 for r in feed_results if r["status"] == "success")
        error_count = sum(1 for r in feed_results if r["status"] == "error")

        # Group results by feed type
        rss_feeds = [r for r in feed_results if r["feed_type"] == "RSS Feed"]
        website_feeds = [r for r in feed_results if r["feed_type"] == "Website"]

        for result in feed_results:
            status_style = (
                self.style.SUCCESS
                if result["status"] == "success"
                else self.style.ERROR
            )
            status_text = "✓ SUCCESS" if result["status"] == "success" else "✗ ERROR"

            self.stdout.write(
                f"\n{status_style(status_text)} - [{result['feed_type']}] {result['feed']}"
            )
            self.stdout.write(f"  Entries added: {result['entries_added']}")
            self.stdout.write(f"  Articles loaded: {result['articles_loaded']}")
            self.stdout.write(f"  Article load errors: {result['article_errors']}")
            if result["errors"]:
                self.stdout.write("  Errors:")
                for error in result["errors"][: self.MAX_ERRORS_TO_SHOW]:
                    self.stdout.write(f"   - {error}")
                if len(result["errors"]) > self.MAX_ERRORS_TO_SHOW:
                    remaining = len(result["errors"]) - self.MAX_ERRORS_TO_SHOW
                    self.stdout.write(f"   ... and {remaining} more errors")

        self.stdout.write("\n=== Summary ===")
        self.stdout.write(
            f"Total feeds processed: {len(feed_results)}\n"
            f"  - RSS Feeds: {len(rss_feeds)}\n"
            f"  - Website Feeds: {len(website_feeds)}\n"
            f"Successful updates: {success_count}\n"
            f"Failed updates: {error_count}\n"
            f"Total new entries added: {total_entries}\n"
            f"Total articles loaded: {total_articles_loaded}\n"
            f"Total article load errors: {total_article_errors}"
        )
