import random
import asyncio
import re
import urllib.parse
from typing import List
from pathlib import Path


async def random_delay(min_s: float = 3.0, max_s: float = 8.0) -> None:
    await asyncio.sleep(random.uniform(min_s, max_s))


def load_job_boards(boards_file: Path) -> List[str]:
    lines = boards_file.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip() and not l.startswith("#")]


def build_search_url(base_url: str, query_param: str, role: str) -> str:
    parsed = urllib.parse.urlparse(base_url)
    qs = urllib.parse.parse_qs(parsed.query)
    qs[query_param] = [role]
    new_query = urllib.parse.urlencode(qs, doseq=True)
    return parsed._replace(query=new_query).geturl()


def title_matches_role(title: str, keywords: List[str]) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in keywords)


def clean_url(url: str) -> str:
    """Strip tracking parameters and common ATS redirects."""
    # Remove common tracker query params
    tracker_params = {"trk", "trackingId", "refId", "position", "pageNum", "origin",
                      "utm_source", "utm_medium", "utm_campaign", "referer"}
    parsed = urllib.parse.urlparse(url)
    qs = {k: v for k, v in urllib.parse.parse_qs(parsed.query).items()
          if k not in tracker_params}
    clean_query = urllib.parse.urlencode(qs, doseq=True)
    return parsed._replace(query=clean_query).geturl()


def get_domain(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc
    # strip www. prefix
    return re.sub(r"^www\.", "", host)
