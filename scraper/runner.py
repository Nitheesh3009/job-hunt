"""
Method A: Playwright-based automated scraper.
Launches a browser, iterates over all roles x platforms, writes jobs.json.
"""
import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright, BrowserContext

from scraper.config import SearchConfig, load_config
from scraper.storage import append_jobs
from scraper.utils import load_job_boards, title_matches_role
from scraper.platforms import (
    LinkedInScraper,
    IndeedScraper,
    ZipRecruiterScraper,
    ConsultingBoardScraper,
)

BOARDS_FILE = Path(__file__).parent.parent / "job_boards"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


async def _new_page(context: BrowserContext):
    page = await context.new_page()
    await page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
    return page


async def run(config: SearchConfig | None = None) -> None:
    if config is None:
        config = load_config()

    board_urls = load_job_boards(BOARDS_FILE)
    total_added = 0

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1440, "height": 900},
            locale="en-US",
        )

        for role in config.roles:
            role_kw = config.role_keywords.get(role, [role.lower()])
            print(f"\n{'='*60}")
            print(f"Role: {role}")
            print(f"{'='*60}")

            # ── Aggregators ──────────────────────────────────────────
            aggregator_scrapers = [
                ("LinkedIn",     LinkedInScraper),
                ("Indeed",       IndeedScraper),
                ("ZipRecruiter", ZipRecruiterScraper),
            ]
            for name, ScraperCls in aggregator_scrapers:
                print(f"  [{name}] Scraping…", end=" ", flush=True)
                page = await _new_page(context)
                try:
                    scraper = ScraperCls(page, config)
                    results = await scraper.search(role, config.location)
                    filtered = [j for j in results if title_matches_role(j["job_title"], role_kw)]
                    added = append_jobs(filtered)
                    total_added += added
                    print(f"{len(results)} found → {len(filtered)} matched → {added} new")
                finally:
                    await page.close()

            # ── Consulting boards ─────────────────────────────────────
            for board_url in board_urls:
                from scraper.utils import get_domain
                domain = get_domain(board_url)
                print(f"  [{domain}] Scraping…", end=" ", flush=True)
                page = await _new_page(context)
                try:
                    scraper = ConsultingBoardScraper(page, config, board_url)
                    results = await scraper.search(role, config.location)
                    filtered = [j for j in results if title_matches_role(j["job_title"], role_kw)]
                    added = append_jobs(filtered)
                    total_added += added
                    print(f"{len(results)} found → {len(filtered)} matched → {added} new")
                finally:
                    await page.close()

        await context.close()
        await browser.close()

    print(f"\nDone. Total new jobs added to jobs.json: {total_added}")


if __name__ == "__main__":
    asyncio.run(run())
