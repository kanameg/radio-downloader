#!/usr/bin/env python3
"""
Simple HTML downloader (list output).

Usage:
    python download_radio_list.py BR8Z3NX7XM -o programs.json

Saves JSON list to file if `-o/--output` is given, otherwise prints to stdout.
"""
import argparse
import html as _html
import json
import re
import sys

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def download_with_playwright(url, timeout, headers):
    if not sync_playwright:
        raise RuntimeError(
            "Playwright is not installed in this Python environment. Install with `pip install playwright` and run `playwright install chromium`, or run the script with the Python that has Playwright.`"
        )

    ua = headers.get("User-Agent") if headers else None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        if ua:
            context = browser.new_context(user_agent=ua)
        else:
            context = browser.new_context()

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
    from urllib.request import Request, urlopen

    req = Request(url, headers=headers or {})
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        charset = resp.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace"), charset


def parse_programs_from_html(html_text):
    entries = []
    tag_pattern = re.compile(
        r"<div[^>]*class=[\'\"][^\'\"]*nol_audio_player_base[^\'\"]*[^>]*>",
        re.IGNORECASE,
    )
    for m in tag_pattern.finditer(html_text):
        tag = m.group(0)
        hls_m = re.search(r"data-hlsurl=[\"\']([^\"\']+)[\"\']", tag)
        aa_m = re.search(r"data-aa=[\"\']([^\"\']+)[\"\']", tag)
        if not hls_m:
            continue
        hls = hls_m.group(1)
        aa = aa_m.group(1) if aa_m else ""

        title = None
        broadcast_date = None
        broadcast_start = None
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
        description="Download program list (JSON) from an NHK program ID"
    )
    parser.add_argument("target", help="NHK program ID (e.g. BR8Z3NX7XM)")
    parser.add_argument("-o", "--output", help="Output JSON file path (default stdout)")
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
    except Exception as e:
        print(f"Error downloading {url}: {e}", file=sys.stderr)
        sys.exit(1)

    programs = parse_programs_from_html(html)
    if not programs:
        print("No program entries found in the page.", file=sys.stderr)
        sys.exit(1)
    # Merge with existing file named {target}.json if present (merge key: hls_url)
    existing_fname = f"{target}.json"
    existing = []
    try:
        with open(existing_fname, "r", encoding="utf-8") as ef:
            existing = json.load(ef)
            if not isinstance(existing, list):
                existing = []
    except FileNotFoundError:
        existing = []
    except Exception as e:
        print(
            f"Warning: failed to read existing file {existing_fname}: {e}",
            file=sys.stderr,
        )
        existing = []

    existing_by_hls = {
        e.get("hls_url"): e
        for e in existing
        if isinstance(e, dict) and e.get("hls_url")
    }
    parsed_by_hls = {p.get("hls_url"): p for p in programs if p.get("hls_url")}

    merged = []
    # For each parsed program, prefer existing file's values when keys overlap
    for hls, p in parsed_by_hls.items():
        if hls in existing_by_hls:
            ex = existing_by_hls[hls]
            m = p.copy()
            m.update(ex)
            merged.append(m)
        else:
            merged.append(p)

    # Also include any existing entries that are not present in newly parsed list
    for hls, ex in existing_by_hls.items():
        if hls and hls not in parsed_by_hls:
            merged.append(ex)

    # Output merged JSON
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error writing to {args.output}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        json.dump(merged, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
