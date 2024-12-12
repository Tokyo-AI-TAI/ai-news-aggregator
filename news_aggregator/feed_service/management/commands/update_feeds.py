from django.core.management.base import BaseCommand
from django.utils import timezone
import logging
from news_aggregator.feed_service.models import Feed
from news_aggregator.feed_service.services import FeedService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Updates all feeds in the database with new entries"

    def handle(self, *args, **options):
        feeds = Feed.objects.filter(is_active=True)
        self.stdout.write(f"Found {feeds.count()} active feeds to update")

        # Track results for each feed
        feed_results = []
        total_entries = 0

        for feed in feeds:
            result = {
                "feed": feed.title,
                "status": "success",
                "entries_added": 0,
                "errors": [],
            }

            try:
                self.stdout.write(f"Updating feed: {feed.title}")
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

        for result in feed_results:
            status_style = (
                self.style.SUCCESS
                if result["status"] == "success"
                else self.style.ERROR
            )
            status_text = "✓ SUCCESS" if result["status"] == "success" else "✗ ERROR"

            self.stdout.write(f"\n{status_style(status_text)} - {result['feed']}")
            self.stdout.write(f"  Entries added: {result['entries_added']}")
            if result["errors"]:
                self.stdout.write("  Errors:")
                for error in result["errors"]:
                    self.stdout.write(f"   - {error}")

        self.stdout.write("\n=== Summary ===")
        self.stdout.write(
            f"Total feeds processed: {len(feed_results)}\n"
            f"Successful updates: {success_count}\n"
            f"Failed updates: {error_count}\n"
            f"Total new entries added: {total_entries}"
        )
