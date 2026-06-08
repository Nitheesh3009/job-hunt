from typing import List, Dict, Any
from .base import BaseScraper
from scraper.utils import build_search_url, clean_url, random_delay, get_domain
from scraper.config import BOARD_QUERY_PARAMS


class ConsultingBoardScraper(BaseScraper):
    """Generic scraper for consulting/staffing job boards listed in job_boards."""

    def __init__(self, page, config, board_url: str):
        super().__init__(page, config)
        self.board_url = board_url
        self.domain = get_domain(board_url)

    async def search(self, role: str, location: str) -> List[Dict[str, Any]]:
        param = BOARD_QUERY_PARAMS.get(self.domain, "q")
        url = build_search_url(self.board_url, param, role)
        jobs: List[Dict[str, Any]] = []

        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=40000)
            await random_delay(self.config.min_delay_s, self.config.max_delay_s)

            # scroll to load dynamic content
            for _ in range(4):
                await self.page.evaluate("window.scrollBy(0, 700)")
                await random_delay(1.0, 2.0)

            # Try common job card selectors used across different ATS platforms
            selectors = [
                "a[href*='job']",       # generic job links
                "a[href*='career']",
                "div[class*='job'] a",
                "li[class*='job'] a",
                "tr[class*='job'] a",
                ".job-title a",
                ".jobTitle a",
                "[data-job-id] a",
            ]
            links: list = []
            for sel in selectors:
                links = await self.page.query_selector_all(sel)
                if links:
                    break

            seen_urls: set = set()
            for link_el in links[: self.config.max_results_per_site]:
                try:
                    href = await link_el.get_attribute("href") or ""
                    text = (await link_el.inner_text()).strip()

                    # resolve relative URLs
                    if href.startswith("/"):
                        from urllib.parse import urlparse
                        base = urlparse(self.board_url)
                        href = f"{base.scheme}://{base.netloc}{href}"

                    if not href or href in seen_urls:
                        continue
                    seen_urls.add(href)

                    job = self._job_template()
                    job["source_platform"] = self.domain
                    job["job_title"] = text[:200]
                    job["job_url"] = clean_url(href)
                    job["location"] = location

                    # best-effort company name from domain
                    job["company"] = self.domain.split(".")[0].title()

                    if job["job_title"] and job["job_url"]:
                        jobs.append(job)
                except Exception:
                    continue

        except Exception as exc:
            print(f"[{self.domain}] Error scraping '{role}': {exc}")

        return jobs
