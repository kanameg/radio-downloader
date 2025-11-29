#!/usr/bin/env python3
"""
Simple HTML downloader (list output).

Usage:
    python download_radio_list.py BR8Z3NX7XM -o programs.csv

Downloads program entries from NHK and merges with an existing
`<target>.csv` (if present) using `hls_url` as the key. The script
uses pandas for the merge when available.
"""
import argparse
import html as _html
import json
import os
import re
import sys

import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def download_with_playwright(url, timeout, headers):
    if not sync_playwright:
        raise RuntimeError(
            "Playwright is not installed in this Python environment. Install with `pip install playwright` and run `playwright install chromium`, or run the script with the Python that has Playwright.`"
        )

    ua = headers.get("User-Agent") if headers else None
    with sync_playwright() as playwright_handle:
        browser = playwright_handle.chromium.launch(
            headless=True, args=["--no-sandbox"]
        )
        if ua:
            context = browser.new_context(user_agent=ua)
        else:
            context = browser.new_context()

        if headers:
            extra = {
                header_key: header_value
                for header_key, header_value in headers.items()
                if header_key.lower() != "user-agent"
            }
            if extra:
                context.set_extra_http_headers(extra)

        page = context.new_page()
        page.goto(url, timeout=timeout * 1000, wait_until="networkidle")
        content = page.content()
        context.close()
        browser.close()
        return content, "utf-8"


def download_with_urllib(url, timeout, headers):
    from urllib.request import Request, urlopen

    req = Request(url, headers=headers or {})
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        charset = resp.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace"), charset


def parse_programs_from_html(html_text):
    # Parse using BeautifulSoup for clarity and robustness
    soup = BeautifulSoup(html_text, "lxml")
    entries = []

    # Find divs whose class attribute contains 'nol_audio_player_base'
    def class_contains_nol_audio(cls):
        if not cls:
            return False
        # bs4 may give a list for multiple classes
        if isinstance(cls, (list, tuple)):
            return any(
                "nol_audio_player_base" in class_name
                for class_name in cls
                if class_name
            )
        return "nol_audio_player_base" in cls

    for div in soup.find_all("div", class_=class_contains_nol_audio):
        hls = div.get("data-hlsurl") or ""
        aa = div.get("data-aa") or ""
        if not hls:
            continue

        title = ""
        broadcast_date = ""
        broadcast_start = ""
        try:
            parts = aa.split(";")
            if len(parts) >= 2:
                title = _html.unescape(parts[1]).strip()
            if len(parts) >= 5 and parts[4]:
                iso_range = parts[4]
                start_iso = iso_range.split("_")[0]
                broadcast_start = start_iso
                broadcast_date = start_iso.split("T")[0]
        except Exception:
            pass

        entries.append(
            {
                "title": title or "",
                "broadcast_date": broadcast_date or "",
                "broadcast_start": broadcast_start or "",
                "hls_url": hls,
                "get": 0,
            }
        )

    return entries


def download(url, timeout=30, headers=None):
    default_ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    headers = headers or {"User-Agent": default_ua}
    if not sync_playwright:
        raise RuntimeError(
            "Playwright is required but not installed in this Python environment. Run `pip install playwright` and `python -m playwright install chromium`, or run the script with the Python that has Playwright installed."
        )
    return download_with_playwright(url, timeout, headers)


def main():
    parser = argparse.ArgumentParser(
        description="Download program list (CSV) from an NHK program ID"
    )
    parser.add_argument("target", help="NHK program ID (e.g. BR8Z3NX7XM)")
    parser.add_argument("-o", "--output", help="Output CSV file path (default: stdout)")
    parser.add_argument(
        "--timeout", type=int, default=30, help="Timeout in seconds (default: 30)"
    )
    args = parser.parse_args()

    target = args.target.strip()
    if not re.fullmatch(r"[A-Za-z0-9]{6,20}", target):
        print(f"Invalid NHK program ID '{target}'", file=sys.stderr)
        sys.exit(2)

    url = f"https://www.nhk.or.jp/radio/ondemand/detail.html?p={target}_01"
    # print(f"Downloading from {url}...")

    try:
        html, encoding = download(url, timeout=args.timeout)
    except Exception as err:
        print(f"Error downloading {url}: {err}", file=sys.stderr)
        sys.exit(1)

    programs = parse_programs_from_html(html)
    if not programs:
        print("No program entries found in the page.", file=sys.stderr)
        sys.exit(1)
    # Merge with existing CSV named {target}.csv if present (merge key: hls_url)
    existing_fname = f"{target}.csv"

    # DataFrame from parsed programs
    new_df = (
        pd.DataFrame(programs)
        if programs
        else pd.DataFrame(
            columns=["title", "broadcast_date", "broadcast_start", "hls_url", "get"]
        )
    )

    # Read existing CSV if present, else create empty with standard columns
    if os.path.exists(existing_fname):
        try:
            existing_df = pd.read_csv(existing_fname, dtype=str)
        except Exception as err:
            print(
                f"Warning: failed to read existing CSV {existing_fname}: {err}",
                file=sys.stderr,
            )
            existing_df = pd.DataFrame(
                columns=["title", "broadcast_date", "broadcast_start", "hls_url", "get"]
            )
    else:
        existing_df = pd.DataFrame(
            columns=["title", "broadcast_date", "broadcast_start", "hls_url", "get"]
        )

    # Ensure union of columns
    for column_name in existing_df.columns.difference(new_df.columns):
        new_df[column_name] = ""
    for column_name in new_df.columns.difference(existing_df.columns):
        existing_df[column_name] = ""

    # Place existing first so its values take precedence when dropping duplicates
    combined = pd.concat([existing_df, new_df], ignore_index=True, sort=False)
    if "hls_url" in combined.columns:
        combined = combined.drop_duplicates(subset=["hls_url"], keep="first")

    # Normalize `get` column (use to_numeric to avoid FutureWarning about downcasting)
    if "get" in combined.columns:
        combined["get"] = (
            pd.to_numeric(combined["get"], errors="coerce").fillna(0).astype(int)
        )

    # Write CSV to output file if specified, otherwise write to stdout
    if args.output:
        out_fname = args.output
        try:
            combined.to_csv(out_fname, index=False, encoding="utf-8")
        except Exception as err:
            print(f"Error writing CSV to {out_fname}: {err}", file=sys.stderr)
            sys.exit(1)
    else:
        # print CSV to stdout
        try:
            combined.to_csv(sys.stdout, index=False)
        except Exception as err:
            print(f"Error writing CSV to stdout: {err}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
