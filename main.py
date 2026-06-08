#!/usr/bin/env python3
"""
Job Hunt — main entry point.

Usage:
  python main.py scrape    # Method A: Playwright automated scraper → jobs.json
  python main.py links     # Method B: generate timestamped search_links HTML
  python main.py list      # Show jobs saved in jobs.json
"""
import argparse
import asyncio
import json
import webbrowser
from pathlib import Path


def cmd_scrape(_args):
    from scraper.runner import run
    asyncio.run(run())


def cmd_links(args):
    from scraper.link_generator import generate
    output = asyncio.run(generate())
    if args.open:
        webbrowser.open(output.as_uri())


def cmd_list(args):
    jobs_file = Path(__file__).parent / "jobs.json"
    if not jobs_file.exists():
        print("jobs.json not found — run 'python main.py scrape' first.")
        return

    jobs = json.loads(jobs_file.read_text(encoding="utf-8"))
    filtered = [j for j in jobs if not args.status or j.get("status") == args.status]

    print(f"\nTotal: {len(filtered)} job(s)"
          + (f" with status='{args.status}'" if args.status else ""))
    print("-" * 80)
    for j in filtered:
        print(f"  [{j.get('source_platform', '?'):18}] {j.get('job_title', '')}")
        print(f"   Company : {j.get('company', 'N/A')}")
        print(f"   Location: {j.get('location', 'N/A')}")
        print(f"   URL     : {j.get('job_url', '')}")
        print(f"   Posted  : {j.get('date_posted', 'N/A')}  |  Scraped: {j.get('date_scraped', 'N/A')}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Job Hunt Aggregator")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scrape", help="Run Playwright scraper (Method A)").set_defaults(func=cmd_scrape)

    p_links = sub.add_parser("links", help="Generate timestamped search links HTML (Method B)")
    p_links.add_argument("--open", action="store_true", help="Open the HTML file in browser after generating")
    p_links.set_defaults(func=cmd_links)

    p_list = sub.add_parser("list", help="List scraped jobs from jobs.json")
    p_list.add_argument("--status", help="Filter by status (e.g. pending_analysis)")
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
