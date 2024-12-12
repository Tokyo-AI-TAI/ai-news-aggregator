import argparse

import newspaper


def fetch_news_metadata(url):
    # Build the source object from the URL
    source = newspaper.build(url, memoize_articles=False)

    # Extract basic metadata
    metadata = {
        "brand": source.brand,
        "description": source.description,
        "category_urls": source.category_urls()[:3],  # Limit to first three categories
    }

    # Fetch the first three articles
    articles_data = []
    for article in source.articles[:3]:
        article.download()
        article.parse()
        articles_data.append(
            {
                "title": article.title,
                "authors": article.authors,
                "publish_date": article.publish_date,
                "summary": article.summary[:150],  # Truncate summary to 150 characters
            }
        )

    return metadata, articles_data


def main():
    parser = argparse.ArgumentParser(
        description="Fetch news metadata and articles from a given URL."
    )
    parser.add_argument(
        "url", type=str, help="The URL of the news site to fetch data from"
    )
    args = parser.parse_args()

    metadata, articles = fetch_news_metadata(args.url)

    print("Source Metadata:")
    print(metadata)

    print("\nFirst Three Articles:")
    for i, article in enumerate(articles, start=1):
        print(f"Article {i}:")
        print(f"Title: {article['title']}")
        print(f"Authors: {article['authors']}")
        print(f"Publish Date: {article['publish_date']}")
        print(f"Summary: {article['summary']}")
        print("-" * 40)


if __name__ == "__main__":
    main()
