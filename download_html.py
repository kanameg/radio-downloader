#!/usr/bin/env python3
"""
Simple HTML downloader.

Usage:
    # NHKの番組IDだけを渡す例（BR8Z3NX7XM -> p=BR8Z3NX7XM_01 を組み立てる）
    python download_html.py BR8Z3NX7XM -o page.html

Saves to file if `-o/--output` is given, otherwise prints to stdout.
"""
import argparse
import re
import sys

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def download_with_playwright(url, timeout, headers):
    # Use Playwright to render the page (executes JS). Returns rendered HTML.
    if not sync_playwright:
        raise RuntimeError(
            "Playwright is not installed in this Python environment. Install with `pip install playwright` and run `playwright install chromium`, or run the script with the Python that has Playwright.`"
        )

    ua = headers.get("User-Agent") if headers else None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        # create context with UA when provided
        if ua:
            context = browser.new_context(user_agent=ua)
        else:
            context = browser.new_context()

        # set other headers if provided
        if headers:
            extra = {k: v for k, v in headers.items() if k.lower() != "user-agent"}
            if extra:
                context.set_extra_http_headers(extra)

        page = context.new_page()
        page.goto(url, timeout=timeout * 1000, wait_until="networkidle")
        content = page.content()
        context.close()
        browser.close()
        return content, "utf-8"


def download_with_urllib(url, timeout, headers):
    # Fallback if requests isn't available
    from urllib.request import Request, urlopen

    req = Request(url, headers=headers or {})
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        charset = resp.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace"), charset


def download(url, timeout=30, headers=None):
    # Default headers: impersonate recent Chrome to avoid simple bot blocks
    default_ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    headers = headers or {"User-Agent": default_ua}
    # Playwright is required. If it's not available in this Python, raise with instructions.
    if not sync_playwright:
        raise RuntimeError(
            "Playwright is required but not installed in this Python environment. Run `pip install playwright` and `python -m playwright install chromium`, or run the script with the Python that has Playwright installed."
        )
    return download_with_playwright(url, timeout, headers)


def main():
    parser = argparse.ArgumentParser(
        description="Download HTML source from an NHK program ID"
    )
    parser.add_argument("target", help="NHK program ID (e.g. BR8Z3NX7XM)")
    parser.add_argument(
        "-o", "--output", help="File path to save HTML. If omitted, prints to stdout"
    )
    parser.add_argument(
        "--timeout", type=int, default=30, help="Timeout in seconds (default: 30)"
    )
    args = parser.parse_args()

    # Only accept NHK program ID (alphanumeric, 6-20 chars)
    target = args.target.strip()
    if not re.fullmatch(r"[A-Za-z0-9]{6,20}", target):
        print(
            f"Invalid NHK program ID '{target}'. Provide an ID like BR8Z3NX7XM",
            file=sys.stderr,
        )
        sys.exit(2)

    url = f"https://www.nhk.or.jp/radio/ondemand/detail.html?p={target}_01"
    print(f"Downloading from {url}...")

    try:
        html, encoding = download(url, timeout=args.timeout)
    except Exception as e:
        print(f"Error downloading {url}: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        try:
            with open(args.output, "w", encoding=encoding) as f:
                f.write(html)
        except Exception as e:
            print(f"Error writing to {args.output}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Print to stdout (avoid adding extra newline)
        sys.stdout.write(html)


if __name__ == "__main__":
    main()
