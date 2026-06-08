from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import yaml

CONFIG_FILE = Path(__file__).parent.parent / "config.yaml"


@dataclass
class SearchConfig:
    roles: List[str] = field(default_factory=list)
    location: str = "Remote"
    date_range_days: int = 14
    max_results_per_site: int = 25
    min_delay_s: float = 3.0
    max_delay_s: float = 8.0
    role_keywords: Dict[str, List[str]] = field(default_factory=dict)


def load_config(path: Path = CONFIG_FILE) -> SearchConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return SearchConfig(
        roles=raw.get("roles", []),
        location=raw.get("location", "Remote"),
        date_range_days=raw.get("date_range_days", 14),
        max_results_per_site=raw.get("max_results_per_site", 25),
        min_delay_s=raw.get("min_delay_s", 3.0),
        max_delay_s=raw.get("max_delay_s", 8.0),
        role_keywords=raw.get("role_keywords", {}),
    )


# Query-parameter key for each consulting board domain
BOARD_QUERY_PARAMS: Dict[str, str] = {
    "tridentconsultinginc.com":    "search",
    "pyramidci.com":               "s",
    "experis.com":                 "query",
    "beaconhillstaffing.com":      "q",
    "mykelly.com":                 "query",
    "eliassen.com":                "keyword",
    "pinnacle1.com":               "q",
    "randstadusa.com":             "q",
    "roberthalf.com":              "q",
    "centizenapps.com":            "query",
    "teksystems.com":              "search",
    "prolianceconsult.com":        "q",
    "modis.com":                   "q",
    "apexsystems.com":             "q",
    "judge.com":                   "q",
    "insightglobal.com":           "q",
    "dexian.com":                  "search",
    "yoh.com":                     "q",
    "pipercompanies.com":          "keyword",
    "kellymitchell.com":           "query",
    "bcforward.jobs.net":          "q",
    "kforce.com":                  "q",
    "collabera.com":               "q",
    "matrixres.com":               "search",
    "vaco.com":                    "q",
    "lancesoft.com":               "s",
}

# Primary aggregator URL templates ({role} and {location} are substituted)
AGGREGATOR_TEMPLATES: Dict[str, str] = {
    "LinkedIn":     "https://www.linkedin.com/jobs/search/?keywords={role}&location={location}&f_TPR=r{seconds}",
    "Indeed":       "https://www.indeed.com/jobs?q={role}&l={location}&fromage={days}",
    "Glassdoor":    "https://www.glassdoor.com/Job/jobs.htm?sc.keyword={role}",
    "ZipRecruiter": "https://www.ziprecruiter.com/candidate/search?search={role}&location={location}",
}
