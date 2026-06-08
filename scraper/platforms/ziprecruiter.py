import urllib.parse
from typing import List, Dict, Any
from .base import BaseScraper
from scraper.utils import clean_url, random_delay


class ZipRecruiterScraper(BaseScraper):
    SOURCE = "ZipRecruiter"

    async def search(self, role: str, location: str) -> List[Dict[str, Any]]:
        url = (
            f"https://www.ziprecruiter.com/candidate/search?"
            f"search={urllib.parse.quote(role)}"
            f"&location={urllib.parse.quote(location)}"
        )
        jobs: List[Dict[str, Any]] = []

        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await random_delay(self.config.min_delay_s, self.config.max_delay_s)

            for _ in range(3):
                await self.page.evaluate("window.scrollBy(0, 800)")
                await random_delay(1, 2)

            cards = await self.page.query_selector_all("article.job_result")
            for card in cards[: self.config.max_results_per_site]:
                job = self._job_template()
                job["source_platform"] = self.SOURCE

                title_el = await card.query_selector("h2[class*='title']")
                job["job_title"] = (await title_el.inner_text()).strip() if title_el else ""

                company_el = await card.query_selector("a[class*='company']")
                job["company"] = (await company_el.inner_text()).strip() if company_el else ""

                location_el = await card.query_selector("p[class*='location']")
                job["location"] = (await location_el.inner_text()).strip() if location_el else ""

                date_el = await card.query_selector("time")
                job["date_posted"] = (await date_el.get_attribute("datetime") or "") if date_el else ""

                link_el = await card.query_selector("a[href*='/jobs/']")
                href = (await link_el.get_attribute("href") or "") if link_el else ""
                job["job_url"] = clean_url(href)

                if job["job_title"] and job["job_url"]:
                    jobs.append(job)

        except Exception as exc:
            print(f"[ZipRecruiter] Error scraping '{role}': {exc}")

        return jobs
