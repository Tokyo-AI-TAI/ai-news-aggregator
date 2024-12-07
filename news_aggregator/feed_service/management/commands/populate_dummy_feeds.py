from django.core.management.base import BaseCommand
from django.utils import timezone

from news_aggregator.feed_service.models import Feed
from news_aggregator.feed_service.models import FeedEntry

DUMMY_FEEDS = [
    {
        "title": "Tech News Daily",
        "url": "https://example.com/tech-news",
        "description": "Latest technology news and updates",
        "entries": [
            {
                "title": "New AI Breakthrough in Natural Language Processing",
                "content": (
                    "Researchers have achieved a significant breakthrough in NLP..."
                ),
                "author": "John Doe",
                "url": "https://example.com/tech-news/ai-breakthrough",
            },
            {
                "title": "The Future of Quantum Computing",
                "content": (
                    "Quantum computers are getting closer to practical applications..."
                ),
                "author": "Jane Smith",
                "url": "https://example.com/tech-news/quantum-computing",
            },
        ],
    },
    {
        "title": "Science Today",
        "url": "https://example.com/science-today",
        "description": "Breaking science news and research",
        "entries": [
            {
                "title": "Mars Mission Update",
                "content": (
                    "NASA's latest Mars rover has discovered traces of ancient water..."
                ),
                "author": "Sarah Johnson",
                "url": "https://example.com/science-today/mars-mission",
            },
            {
                "title": "Climate Change Report",
                "content": "New study shows accelerating ice melt in Antarctica...",
                "author": "Mike Wilson",
                "url": "https://example.com/science-today/climate-change",
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Populates the database with dummy RSS feeds and entries"

    def handle(self, *args, **kwargs):
        self.stdout.write("Creating dummy feeds...")

        for feed_data in DUMMY_FEEDS:
            feed = Feed.objects.create(
                title=feed_data["title"],
                url=feed_data["url"],
                description=feed_data["description"],
            )

            for entry_data in feed_data["entries"]:
                FeedEntry.objects.create(
                    feed=feed,
                    title=entry_data["title"],
                    content=entry_data["content"],
                    author=entry_data["author"],
                    url=entry_data["url"],
                    published_at=timezone.now(),
                )

            self.stdout.write(
                f'Created feed: {feed.title} with {len(feed_data["entries"])} entries',
            )

        self.stdout.write(self.style.SUCCESS("Successfully populated dummy feeds"))
