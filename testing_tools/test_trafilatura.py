# /// script
# dependencies = [
#  "trafilatura",
# ]
# ///

import argparse

import trafilatura


def extract_content(url: str) -> dict[str, any]:
    downloaded = trafilatura.fetch_url(url)
    extracted = trafilatura.extract(downloaded, output_format="json", include_formatting=True)
    return extracted


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--url", type=str, required=True)
    args = args.parse_args()
    print(extract_content(args.url))
