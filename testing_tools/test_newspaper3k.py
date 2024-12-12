# /// script
# dependencies = [
#  "newspaper3k",
#  "lxml[html-clean]",
#  "nltk",
# ]
# ///

import argparse
import sys

import nltk
from newspaper import build


def test_news_site(url, language=None):
    """Test news website parsing capabilities."""
    try:
        # Initialize news source
        print(f"\nAnalyzing news site: {url}")
        news_site = build(url, memoize_articles=False)

        # Site metadata
        print("\n=== Site Information ===")
        print(f"Brand: {news_site.brand}")
        print(f"Description: {news_site.description}")
        print(f"Total articles detected: {len(news_site.articles)}")

        # Site-wide configuration
        print("\n=== Site Configuration ===")
        print(f"Categories URLs: {news_site.category_urls()}")
        print(f"Feed URLs: {news_site.feed_urls()}")

        # Sample articles
        print("\n=== First 3 Articles ===")
        for i, article in enumerate(news_site.articles[:3], 1):
            print(f"\nArticle {i}:")
            article.download()
            article.parse()
            print(f"Title: {article.title}")
            print(f"URL: {article.url}")
            print(f"Authors: {article.authors}")
            print(f"Publish Date: {article.publish_date}")
            print(
                f"Text preview: {article.text[:150]}..."
                if article.text
                else "No text available"
            )

    except Exception as e:
        print(f"Error processing news site: {e!s}", file=sys.stderr)
        sys.exit(1)


def main():
    nltk.download("punkt")
    parser = argparse.ArgumentParser(
        description="Test newspaper3k site parsing functionality"
    )
    parser.add_argument("url", help="URL of the news site to analyze")

    args = parser.parse_args()
    test_news_site(args.url)


if __name__ == "__main__":
    main()
