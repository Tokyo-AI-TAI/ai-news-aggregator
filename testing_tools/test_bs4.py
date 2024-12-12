# /// script
# dependencies = [
#  "beautifulsoup4",
#  "requests",
# ]
# ///

import argparse
import json
import re
import sys

import bs4
import requests
from bs4 import BeautifulSoup
from bs4.element import Comment


class WebTextExtractor:
    """Extract clean, structured text content from web pages"""

    # Elements that should be ignored
    INVISIBLE_ELEMENTS = {
        "style",
        "script",
        "head",
        "title",
        "meta",
        "[document]",
        "header",
        "footer",
        "nav",
        "iframe",
        "noscript",
    }

    def __init__(self):
        # Compile regex for cleaning whitespace
        self.whitespace_re = re.compile(r"\s{2,}")

    def _is_visible(self, element: bs4.element.NavigableString) -> bool:
        """Check if element should be included in output"""
        if isinstance(element, Comment):
            return False

        if element.parent.name in self.INVISIBLE_ELEMENTS:
            return False

        # Skip empty strings and pure whitespace
        if not element.strip():
            return False

        return True

    def extract_text(self, url, structured=True):
        """Extract clean text from URL"""
        # Fetch page content
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            return f"Error fetching URL: {e!s}"

        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        if structured:
            # Extract text while preserving some structure
            output = []

            # Get main content area if possible
            main = soup.find("main") or soup.find("article") or soup.body

            # Process headings
            for heading in main.find_all(["h1", "h2", "h3"]):
                if heading.get_text(strip=True):
                    output.append(f"\n# {heading.get_text(strip=True)}")

            # Process paragraphs
            for p in main.find_all("p"):
                if p.get_text(strip=True):
                    output.append(p.get_text(strip=True))

            # Join with double newlines to ensure spacing
            text = "\n\n".join(output)

        else:
            # Extract all visible text
            texts = soup.findAll(text=True)
            visible_texts = filter(self._is_visible, texts)
            # Preserve line breaks by checking parent tags
            processed_texts = []
            for t in visible_texts:
                text = t.strip()
                if text:
                    processed_texts.append(text)
                    # Add double newline after block-level elements
                    if t.parent.name in [
                        "p",
                        "div",
                        "br",
                        "li",
                        "h1",
                        "h2",
                        "h3",
                        "h4",
                        "h5",
                        "h6",
                    ]:
                        processed_texts.append("\n\n")
            # Join with single space but preserve our intentional newlines
            text = " ".join(processed_texts)

        # Modified whitespace cleanup to preserve intentional newlines
        text = re.sub(r"[ \t]+", " ", text)  # Clean horizontal whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)  # Limit consecutive newlines
        text = text.strip()

        return text

    def extract_html(self, url):
        """Extract cleaned HTML content while preserving structure"""
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            return f"Error fetching URL: {e!s}"

        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Define elements that should actually be removed
        remove_elements = {
            "style",
            "script",
            "meta",
            "iframe",
            "noscript",
        }

        # Define attributes to preserve (all others will be removed)
        preserve_attributes = {
            "href",
            "src",
            "title",
            "alt",
            "type",
            "rel",
            "target",
            "datetime",  # for time elements
            "lang",  # language information
            "name",  # for forms and inputs
            "value",  # for inputs
            "action",  # for forms
            "method",  # for forms
        }

        # Remove invisible elements
        for elem in soup.find_all(remove_elements):
            elem.decompose()

        # Remove comments and empty elements
        for element in soup.find_all():
            if isinstance(element, Comment) or (
                element.name not in ["br", "img"]  # preserve empty formatting elements
                and not element.get_text(strip=True)
                and not element.find_all(["img", "video", "audio"])
            ):
                element.decompose()

        # Clean attributes from all elements
        for tag in soup.find_all(True):
            # Get all attributes of the tag
            attrs = dict(tag.attrs)
            for attr in attrs:
                if attr not in preserve_attributes:
                    del tag[attr]

        # Clean whitespace while preserving structure
        return str(soup.prettify())


def main():
    """Command line interface for WebTextExtractor"""
    parser = argparse.ArgumentParser(
        description="Extract clean text content from websites.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://example.com
  %(prog)s https://example.com --plain
  %(prog)s https://example.com --output result.txt
  %(prog)s --urls urls.txt --output-dir ./results
        """,
    )

    # Add arguments
    parser.add_argument("url", nargs="?", help="URL to extract text from")
    parser.add_argument("--urls", help="File containing URLs (one per line)")
    parser.add_argument(
        "--plain", action="store_true", help="Extract plain text without structure"
    )
    parser.add_argument("--output", help="Output file for single URL")
    parser.add_argument("--output-dir", help="Output directory for multiple URLs")
    parser.add_argument(
        "--json", action="store_true", help="Output results in JSON format"
    )
    parser.add_argument(
        "--html", action="store_true", help="Extract cleaned HTML structure"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.url and not args.urls:
        parser.error("Either URL or --urls file must be provided")
    if args.url and args.urls:
        parser.error("Cannot use both URL and --urls file")
    if args.output and args.output_dir:
        parser.error("Cannot use both --output and --output-dir")
    if args.output_dir and not args.urls:
        parser.error("--output-dir requires --urls")
    if sum([args.plain, args.html]) > 1:
        parser.error("Cannot use multiple format options (--plain, --html)")

    extractor = WebTextExtractor()

    # Process single URL
    if args.url:
        if args.html:
            text = extractor.extract_html(args.url)
        else:
            text = extractor.extract_text(args.url, structured=not args.plain)

        if args.json:
            result = {"url": args.url, "text": text}
            text = json.dumps(result, indent=2)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(text)
        else:
            print(text)

    # Process multiple URLs from file
    else:
        try:
            with open(args.urls) as f:
                urls = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error reading URLs file: {e!s}", file=sys.stderr)
            sys.exit(1)

        results = []
        for url in urls:
            if args.html:
                text = extractor.extract_html(url)
            else:
                text = extractor.extract_text(url, structured=not args.plain)

            if args.json:
                results.append({"url": url, "text": text})
            else:
                results.append(f"=== {url} ===\n{text}\n")

        if args.output_dir:
            import os

            os.makedirs(args.output_dir, exist_ok=True)

            if args.json:
                output_file = os.path.join(args.output_dir, "results.json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2)
            else:
                for i, result in enumerate(results):
                    output_file = os.path.join(args.output_dir, f"result_{i+1}.txt")
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(result)
        elif args.json:
            print(json.dumps(results, indent=2))
        else:
            print("\n".join(results))


if __name__ == "__main__":
    main()
