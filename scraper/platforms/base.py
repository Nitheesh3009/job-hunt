from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseScraper(ABC):
    """Common interface for all platform scrapers."""

    def __init__(self, page, config):
        self.page = page
        self.config = config

    @abstractmethod
    async def search(self, role: str, location: str) -> List[Dict[str, Any]]:
        """Return a list of raw job dicts for the given role/location."""
        ...

    def _job_template(self) -> Dict[str, Any]:
        return {
            "id": None,
            "job_title": "",
            "company": "",
            "location": "",
            "source_platform": "",
            "job_url": "",
            "date_posted": "",
            "date_scraped": "",
            "raw_description_text": "",
            "status": "pending_analysis",
        }
