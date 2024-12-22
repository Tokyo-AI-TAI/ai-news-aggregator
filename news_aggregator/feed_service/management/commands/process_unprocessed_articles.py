from django.core.management.base import BaseCommand
from django.utils import timezone
import logging
from datetime import timedelta
from collections import defaultdict
from django.db.models import Q
from news_aggregator.feed_service.models import (
    FeedEntry,
    UserFeedSubscription,
    UserArticleInteraction,
)
from news_aggregator.feed_service.services import AIService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process articles with AI that haven't received summaries yet"
    MAX_ERRORS_TO_SHOW = 3

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours",
            type=int,
            default=48,
            help="Only process articles published within this many hours (default: 48)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of articles to process in each batch (default: 100)",
        )
        parser.add_argument(
            "--reprocess",
            action="store_true",
            help="Reprocess articles even if they were previously processed",
        )

    def handle(self, *args, **options):
        hours = options["hours"]
        batch_size = options["batch_size"]
        reprocess = options["reprocess"]
        cutoff_time = timezone.now() - timedelta(hours=hours)

        # Initialize feed-level tracking
        feed_results = defaultdict(
            lambda: {
                "title": "",
                "feed_type": "",
                "status": "success",
                "articles_processed": 0,
                "articles_skipped": 0,
                "processing_errors": 0,
                "errors": [],
            }
        )

        # Get recent articles that need processing
        entries = (
            FeedEntry.objects.filter(
                published_at__gte=cutoff_time,
                article_load_error="",
            )
            .select_related("feed")
            .order_by("feed_id")
        )

        total_entries = entries.count()
        self.stdout.write(
            f"Found {total_entries} articles within the last {hours} hours"
        )

        ai_service = AIService()
        current_feed = None

        # Process articles grouped by feed
        for entry in entries:
            if current_feed != entry.feed:
                current_feed = entry.feed
                self.stdout.write(f"\nProcessing feed: {current_feed.title}")
                feed_results[current_feed.id].update(
                    {
                        "title": current_feed.title,
                        "feed_type": current_feed.get_feed_type_display(),
                    }
                )

            # Modified subscribers query to handle reprocessing
            subscribers_query = UserFeedSubscription.objects.filter(
                feed=entry.feed,
                is_active=True,
            )
            if not reprocess:
                subscribers_query = subscribers_query.exclude(
                    user__article_interactions__entry=entry
                )
            subscribers = subscribers_query.select_related("user")

            if not subscribers.exists():
                feed_results[current_feed.id]["articles_skipped"] += 1
                continue

            result = feed_results[current_feed.id]
            for subscription in subscribers[:batch_size]:
                try:
                    ai_result = ai_service.process_article_for_user(
                        entry, subscription.user
                    )

                    if ai_result.error:
                        result["processing_errors"] += 1
                        result["errors"].append(
                            f"Error processing {entry.title}: {ai_result.error}"
                        )
                        result["status"] = "error"
                        continue

                    # Update or create the interaction
                    UserArticleInteraction.objects.update_or_create(
                        user=subscription.user,
                        entry=entry,
                        defaults={
                            "custom_summary": ai_result.summary,
                            "relevance_score": ai_result.relevance_score,
                        },
                    )
                    result["articles_processed"] += 1

                except Exception as e:
                    result["processing_errors"] += 1
                    result["errors"].append(f"Error processing {entry.title}: {str(e)}")
                    result["status"] = "error"
                    logger.error(f"Error processing article {entry.pk}: {str(e)}")

        # Print detailed report
        self.stdout.write("\n=== Processing Report ===")

        # Group results by feed type
        rss_feeds = [r for r in feed_results.values() if r["feed_type"] == "RSS Feed"]
        website_feeds = [
            r for r in feed_results.values() if r["feed_type"] == "Website"
        ]

        for result in feed_results.values():
            status_style = (
                self.style.SUCCESS
                if result["status"] == "success"
                else self.style.ERROR
            )
            status_text = "✓ SUCCESS" if result["status"] == "success" else "✗ ERROR"

            self.stdout.write(
                f"\n{status_style(status_text)} - [{result['feed_type']}] {result['title']}"
            )
            self.stdout.write(f"  Articles processed: {result['articles_processed']}")
            self.stdout.write(f"  Articles skipped: {result['articles_skipped']}")
            self.stdout.write(f"  Processing errors: {result['processing_errors']}")

            if result["errors"]:
                self.stdout.write("  Errors:")
                for error in result["errors"][: self.MAX_ERRORS_TO_SHOW]:
                    self.stdout.write(f"   - {error}")
                if len(result["errors"]) > self.MAX_ERRORS_TO_SHOW:
                    remaining = len(result["errors"]) - self.MAX_ERRORS_TO_SHOW
                    self.stdout.write(f"   ... and {remaining} more errors")

        # Print summary statistics
        self.stdout.write("\n=== Summary ===")
        success_count = sum(
            1 for r in feed_results.values() if r["status"] == "success"
        )
        error_count = sum(1 for r in feed_results.values() if r["status"] == "error")
        total_processed = sum(r["articles_processed"] for r in feed_results.values())
        total_skipped = sum(r["articles_skipped"] for r in feed_results.values())
        total_errors = sum(r["processing_errors"] for r in feed_results.values())

        self.stdout.write(
            f"Total feeds processed: {len(feed_results)}\n"
            f"  - RSS Feeds: {len(rss_feeds)}\n"
            f"  - Website Feeds: {len(website_feeds)}\n"
            f"Successful feeds: {success_count}\n"
            f"Failed feeds: {error_count}\n"
            f"Total articles processed: {total_processed}\n"
            f"Total articles skipped: {total_skipped}\n"
            f"Total processing errors: {total_errors}"
        )
