import urllib.parse
from typing import List, Dict, Any
from .base import BaseScraper
from scraper.utils import clean_url, random_delay


class LinkedInScraper(BaseScraper):
    SOURCE = "LinkedIn"

    async def search(self, role: str, location: str) -> List[Dict[str, Any]]:
        days = self.config.date_range_days
        seconds = days * 86400
        url = (
            f"https://www.linkedin.com/jobs/search/?"
            f"keywords={urllib.parse.quote(role)}"
            f"&location={urllib.parse.quote(location)}"
            f"&f_TPR=r{seconds}"
            f"&position=1&pageNum=0"
        )
        jobs: List[Dict[str, Any]] = []

        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await random_delay(self.config.min_delay_s, self.config.max_delay_s)

            # scroll to trigger lazy loading
            for _ in range(3):
                await self.page.evaluate("window.scrollBy(0, 800)")
                await random_delay(1, 2)

            cards = await self.page.query_selector_all("div.job-search-card")
            for card in cards[: self.config.max_results_per_site]:
                job = self._job_template()
                job["source_platform"] = self.SOURCE

                title_el = await card.query_selector("h3.base-search-card__title")
                job["job_title"] = (await title_el.inner_text()).strip() if title_el else ""

                company_el = await card.query_selector("h4.base-search-card__subtitle")
                job["company"] = (await company_el.inner_text()).strip() if company_el else ""

                location_el = await card.query_selector("span.job-search-card__location")
                job["location"] = (await location_el.inner_text()).strip() if location_el else ""

                date_el = await card.query_selector("time")
                job["date_posted"] = (await date_el.get_attribute("datetime") or "") if date_el else ""

                link_el = await card.query_selector("a.base-card__full-link")
                href = (await link_el.get_attribute("href") or "") if link_el else ""
                job["job_url"] = clean_url(href)

                if job["job_title"] and job["job_url"]:
                    jobs.append(job)

        except Exception as exc:
            print(f"[LinkedIn] Error scraping '{role}': {exc}")

        return jobs
