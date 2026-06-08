"""
Visits every board and aggregator, searches for each role, and builds
a timestamped HTML with only the boards/platforms that returned actual job listings.
"""
import asyncio
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from playwright.async_api import async_playwright, BrowserContext

from scraper.config import (
    AGGREGATOR_TEMPLATES,
    BOARD_QUERY_PARAMS,
    SearchConfig,
    load_config,
)
from scraper.utils import (
    build_search_url,
    clean_url,
    get_domain,
    load_job_boards,
    random_delay,
    title_matches_role,
)

BOARDS_FILE = Path(__file__).parent.parent / "job_boards"
OUTPUT_DIR  = Path(__file__).parent.parent / "output"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


# ── per-platform scrapers ────────────────────────────────────────────────────

async def _scrape_linkedin(page, role: str, config: SearchConfig) -> List[Dict]:
    days    = config.date_range_days
    seconds = days * 86400
    url = (
        f"https://www.linkedin.com/jobs/search/?"
        f"keywords={urllib.parse.quote(role)}"
        f"&location={urllib.parse.quote(config.location)}"
        f"&f_TPR=r{seconds}"
    )
    jobs = []
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await random_delay(config.min_delay_s, config.max_delay_s)
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 800)")
            await random_delay(1, 2)

        cards = await page.query_selector_all("div.job-search-card")
        for card in cards[: config.max_results_per_site]:
            title_el = await card.query_selector("h3.base-search-card__title")
            title     = (await title_el.inner_text()).strip() if title_el else ""
            company_el = await card.query_selector("h4.base-search-card__subtitle")
            company    = (await company_el.inner_text()).strip() if company_el else ""
            link_el    = await card.query_selector("a.base-card__full-link")
            href       = clean_url(await link_el.get_attribute("href") or "") if link_el else ""
            if title and href:
                jobs.append({"title": title, "company": company, "url": href})
    except Exception as exc:
        print(f"  [LinkedIn] {exc}")
    return jobs


async def _scrape_indeed(page, role: str, config: SearchConfig) -> List[Dict]:
    url = (
        f"https://www.indeed.com/jobs?"
        f"q={urllib.parse.quote(role)}"
        f"&l={urllib.parse.quote(config.location)}"
        f"&fromage={config.date_range_days}"
    )
    jobs = []
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await random_delay(config.min_delay_s, config.max_delay_s)
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 800)")
            await random_delay(1, 2)

        cards = await page.query_selector_all("div.job_seen_beacon")
        for card in cards[: config.max_results_per_site]:
            title_el = await card.query_selector("h2.jobTitle span[title]")
            title     = (await title_el.get_attribute("title") or "").strip() if title_el else ""
            company_el = await card.query_selector("span.companyName")
            company    = (await company_el.inner_text()).strip() if company_el else ""
            link_el    = await card.query_selector("a[data-jk]")
            jk         = (await link_el.get_attribute("data-jk") or "") if link_el else ""
            href       = f"https://www.indeed.com/viewjob?jk={jk}" if jk else ""
            if title and href:
                jobs.append({"title": title, "company": company, "url": href})
    except Exception as exc:
        print(f"  [Indeed] {exc}")
    return jobs


async def _scrape_ziprecruiter(page, role: str, config: SearchConfig) -> List[Dict]:
    url = (
        f"https://www.ziprecruiter.com/candidate/search?"
        f"search={urllib.parse.quote(role)}"
        f"&location={urllib.parse.quote(config.location)}"
    )
    jobs = []
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await random_delay(config.min_delay_s, config.max_delay_s)
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 800)")
            await random_delay(1, 2)

        cards = await page.query_selector_all("article.job_result")
        for card in cards[: config.max_results_per_site]:
            title_el   = await card.query_selector("h2[class*='title']")
            title      = (await title_el.inner_text()).strip() if title_el else ""
            company_el = await card.query_selector("a[class*='company']")
            company    = (await company_el.inner_text()).strip() if company_el else ""
            link_el    = await card.query_selector("a[href*='/jobs/']")
            href       = clean_url(await link_el.get_attribute("href") or "") if link_el else ""
            if title and href:
                jobs.append({"title": title, "company": company, "url": href})
    except Exception as exc:
        print(f"  [ZipRecruiter] {exc}")
    return jobs


async def _scrape_board(page, board_url: str, role: str, config: SearchConfig) -> List[Dict]:
    domain = get_domain(board_url)
    param  = BOARD_QUERY_PARAMS.get(domain, "q")
    url    = build_search_url(board_url, param, role)
    jobs   = []

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=40000)
        await random_delay(config.min_delay_s, config.max_delay_s)
        for _ in range(4):
            await page.evaluate("window.scrollBy(0, 700)")
            await random_delay(1.0, 2.0)

        selectors = [
            "a[href*='job']",
            "a[href*='career']",
            "div[class*='job'] a",
            "li[class*='job'] a",
            "tr[class*='job'] a",
            ".job-title a",
            ".jobTitle a",
            "[data-job-id] a",
        ]
        links = []
        for sel in selectors:
            links = await page.query_selector_all(sel)
            if links:
                break

        seen: set = set()
        for link_el in links[: config.max_results_per_site]:
            try:
                href = await link_el.get_attribute("href") or ""
                text = (await link_el.inner_text()).strip()
                if href.startswith("/"):
                    base = urllib.parse.urlparse(board_url)
                    href = f"{base.scheme}://{base.netloc}{href}"
                href = clean_url(href)
                if not href or href in seen or not text:
                    continue
                seen.add(href)
                jobs.append({"title": text[:200], "company": domain.split(".")[0].title(), "url": href})
            except Exception:
                continue
    except Exception as exc:
        print(f"  [{domain}] {exc}")

    return jobs


# ── HTML builder ─────────────────────────────────────────────────────────────

def _build_html(
    results: Dict[str, Dict[str, List[Dict]]],
    config: SearchConfig,
    ts_display: str,
) -> str:
    """
    results = {
        "Cloud Engineer": {
            "LinkedIn":            [{"title": ..., "company": ..., "url": ...}, ...],
            "teksystems.com":      [...],
        },
        ...
    }
    Only boards with at least one result are included.
    """
    total_links = sum(
        len(board_jobs)
        for role_data in results.values()
        for board_jobs in role_data.values()
    )

    sections: List[str] = []
    for role, boards in results.items():
        if not boards:
            continue
        board_blocks: List[str] = []
        for platform, jobs in boards.items():
            rows = "".join(
                f'<tr>'
                f'<td><a href="{j["url"]}" target="_blank" rel="noopener">{j["title"]}</a></td>'
                f'<td>{j["company"]}</td>'
                f'</tr>'
                for j in jobs
            )
            badge_cls = "agg" if platform in ("LinkedIn", "Indeed", "ZipRecruiter") else "board"
            board_blocks.append(
                f'<div class="board-block">'
                f'<h3><span class="platform {badge_cls}">{platform}</span>'
                f'<span class="count">{len(jobs)} job{"s" if len(jobs) != 1 else ""}</span></h3>'
                f'<table><thead><tr><th>Job Title</th><th>Company</th></tr></thead>'
                f'<tbody>{rows}</tbody></table>'
                f'</div>'
            )

        total_role = sum(len(j) for j in boards.values())
        sections.append(
            f'<section>'
            f'<h2>{role} <span class="count">{total_role} result{"s" if total_role != 1 else ""}</span></h2>'
            + "".join(board_blocks)
            + f'</section>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Job Results — {ts_display}</title>
<style>
  body          {{ font-family: system-ui, sans-serif; max-width: 1200px; margin: 2rem auto; padding: 0 1rem; color: #222; }}
  h1            {{ color: #1a1a2e; margin-bottom: .2rem; }}
  .meta         {{ color: #555; font-size: .85rem; margin: .2rem 0 2rem; }}
  section       {{ margin-bottom: 3rem; }}
  h2            {{ color: #16213e; border-bottom: 2px solid #0f3460; padding-bottom: .4rem; display: flex; align-items: center; gap: .75rem; }}
  h3            {{ margin: 1.2rem 0 .4rem; display: flex; align-items: center; gap: .6rem; font-size: .95rem; }}
  .board-block  {{ margin-left: 1rem; margin-bottom: 1rem; }}
  table         {{ width: 100%; border-collapse: collapse; font-size: .85rem; }}
  th, td        {{ text-align: left; padding: .4rem .75rem; border: 1px solid #ddd; }}
  th            {{ background: #0f3460; color: #fff; }}
  tr:nth-child(even) {{ background: #f8f8f8; }}
  a             {{ color: #e94560; text-decoration: none; }}
  a:hover       {{ text-decoration: underline; }}
  .platform     {{ display: inline-block; border-radius: 4px; font-size: .78rem; padding: .15rem .55rem; font-weight: 700; }}
  .agg          {{ background: #0f3460; color: #fff; }}
  .board        {{ background: #e8eaf6; color: #1a237e; }}
  .count        {{ font-size: .78rem; font-weight: 400; color: #888; }}
</style>
</head>
<body>
<h1>Job Results</h1>
<p class="meta">
  Generated: {ts_display} &nbsp;|&nbsp;
  Location: {config.location} &nbsp;|&nbsp;
  Date range: last {config.date_range_days} days &nbsp;|&nbsp;
  <strong>{total_links} total listings</strong>
</p>
{"".join(sections) if sections else "<p>No matching jobs found.</p>"}
</body>
</html>"""


# ── main entry ───────────────────────────────────────────────────────────────

async def generate(config: SearchConfig | None = None) -> Path:
    if config is None:
        config = load_config()

    OUTPUT_DIR.mkdir(exist_ok=True)
    board_urls = load_job_boards(BOARDS_FILE)
    now        = datetime.now()
    ts_file    = now.strftime("%Y-%m-%d_%H-%M-%S")
    ts_display = now.strftime("%B %d, %Y at %I:%M %p")

    # results[role][platform] = [job, ...]
    results: Dict[str, Dict[str, List[Dict]]] = {role: {} for role in config.roles}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1440, "height": 900},
            locale="en-US",
        )

        for role in config.roles:
            keywords = config.role_keywords.get(role, [role.lower()])
            print(f"\n{'='*60}\nRole: {role}\n{'='*60}")

            # ── aggregators ──────────────────────────────────────────
            for name, scrape_fn in [
                ("LinkedIn",     _scrape_linkedin),
                ("Indeed",       _scrape_indeed),
                ("ZipRecruiter", _scrape_ziprecruiter),
            ]:
                print(f"  [{name}] …", end=" ", flush=True)
                page = await context.new_page()
                try:
                    jobs = await scrape_fn(page, role, config)
                    matched = [j for j in jobs if title_matches_role(j["title"], keywords)]
                    if matched:
                        results[role][name] = matched
                    print(f"{len(jobs)} found → {len(matched)} matched")
                finally:
                    await page.close()

            # ── consulting / staffing boards ─────────────────────────
            for board_url in board_urls:
                domain = get_domain(board_url)
                print(f"  [{domain}] …", end=" ", flush=True)
                page = await context.new_page()
                try:
                    jobs = await _scrape_board(page, board_url, role, config)
                    matched = [j for j in jobs if title_matches_role(j["title"], keywords)]
                    if matched:
                        results[role][domain] = matched
                    print(f"{len(jobs)} found → {len(matched)} matched")
                finally:
                    await page.close()

        await context.close()
        await browser.close()

    html     = _build_html(results, config, ts_display)
    out_path = OUTPUT_DIR / f"search_links_{ts_file}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"\nOutput: {out_path}")
    return out_path
