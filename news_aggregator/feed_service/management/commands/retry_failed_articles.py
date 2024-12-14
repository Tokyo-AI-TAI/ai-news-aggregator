from django.core.management.base import BaseCommand
from django.utils import timezone
import logging
from datetime import timedelta
from news_aggregator.feed_service.models import FeedEntry
from news_aggregator.feed_service.services import FeedService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Retries loading full article content for entries that previously failed"
    MAX_ERRORS_TO_SHOW = 3  # Match the limit from update_feeds.py

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours",
            type=int,
            default=48,
            help="Only retry articles published within this many hours (default: 48)",
        )

    def handle(self, *args, **options):
        hours = options["hours"]
        cutoff_time = timezone.now() - timedelta(hours=hours)

        # Find entries that have an error message and were published within the time window
        failed_entries = FeedEntry.objects.filter(
            article_load_error__gt="",  # Has an error message
            article_loaded_at__isnull=True,  # Never successfully loaded
            published_at__gte=cutoff_time,  # Within time window
        ).select_related("feed")

        total_entries = failed_entries.count()
        self.stdout.write(
            f"Found {total_entries} failed entries within the last {hours} hours"
        )

        success_count = 0
        still_failed = 0
        all_errors = []

        for entry in failed_entries:
            self.stdout.write(f"\nRetrying: {entry.title}")
            self.stdout.write(f"  Feed: {entry.feed.title}")
            self.stdout.write(f"  Previous error: {entry.article_load_error}")

            success, error = FeedService.load_article_content(entry)
            if success:
                success_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Successfully loaded"))
            else:
                still_failed += 1
                error_msg = f"Failed to load {entry.url}: {error}"
                all_errors.append(error_msg)
                self.stdout.write(self.style.ERROR(f"  ✗ {error_msg}"))

        # Print summary with limited error display
        self.stdout.write("\n=== Retry Summary ===")
        self.stdout.write(f"Total entries processed: {total_entries}")
        self.stdout.write(f"Successfully loaded: {success_count}")
        self.stdout.write(f"Still failed: {still_failed}")

        if all_errors:
            self.stdout.write("\nRecent errors:")
            for error in all_errors[: self.MAX_ERRORS_TO_SHOW]:
                self.stdout.write(self.style.ERROR(f"  - {error}"))
            if len(all_errors) > self.MAX_ERRORS_TO_SHOW:
                remaining = len(all_errors) - self.MAX_ERRORS_TO_SHOW
                self.stdout.write(f"  ... and {remaining} more errors")
