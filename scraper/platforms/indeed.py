import urllib.parse
from typing import List, Dict, Any
from .base import BaseScraper
from scraper.utils import clean_url, random_delay


class IndeedScraper(BaseScraper):
    SOURCE = "Indeed"

    async def search(self, role: str, location: str) -> List[Dict[str, Any]]:
        url = (
            f"https://www.indeed.com/jobs?"
            f"q={urllib.parse.quote(role)}"
            f"&l={urllib.parse.quote(location)}"
            f"&fromage={self.config.date_range_days}"
        )
        jobs: List[Dict[str, Any]] = []

        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await random_delay(self.config.min_delay_s, self.config.max_delay_s)

            for _ in range(3):
                await self.page.evaluate("window.scrollBy(0, 800)")
                await random_delay(1, 2)

            cards = await self.page.query_selector_all("div.job_seen_beacon")
            for card in cards[: self.config.max_results_per_site]:
                job = self._job_template()
                job["source_platform"] = self.SOURCE

                title_el = await card.query_selector("h2.jobTitle span[title]")
                job["job_title"] = (await title_el.get_attribute("title") or "").strip() if title_el else ""

                company_el = await card.query_selector("span.companyName")
                job["company"] = (await company_el.inner_text()).strip() if company_el else ""

                location_el = await card.query_selector("div.companyLocation")
                job["location"] = (await location_el.inner_text()).strip() if location_el else ""

                date_el = await card.query_selector("span.date")
                job["date_posted"] = (await date_el.inner_text()).strip() if date_el else ""

                link_el = await card.query_selector("a[data-jk]")
                jk = (await link_el.get_attribute("data-jk") or "") if link_el else ""
                job["job_url"] = clean_url(f"https://www.indeed.com/viewjob?jk={jk}") if jk else ""

                if job["job_title"] and job["job_url"]:
                    jobs.append(job)

        except Exception as exc:
            print(f"[Indeed] Error scraping '{role}': {exc}")

        return jobs
