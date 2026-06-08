import json
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

JOBS_FILE = Path(__file__).parent.parent / "jobs.json"


def _make_id(company: str, title: str, url: str) -> str:
    key = f"{company.lower().strip()}|{title.lower().strip()}|{url.strip()}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def load_jobs() -> List[Dict[str, Any]]:
    if JOBS_FILE.exists():
        with JOBS_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_jobs(jobs: List[Dict[str, Any]]) -> None:
    with JOBS_FILE.open("w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)


def append_jobs(new_jobs: List[Dict[str, Any]]) -> int:
    """Merge new_jobs into jobs.json, deduplicating by id. Returns count added."""
    existing = load_jobs()
    seen_ids = {j["id"] for j in existing}

    added = 0
    for job in new_jobs:
        jid = job.get("id") or _make_id(
            job.get("company", ""),
            job.get("job_title", ""),
            job.get("job_url", ""),
        )
        job["id"] = jid
        if jid not in seen_ids:
            job.setdefault("date_scraped", datetime.now(timezone.utc).isoformat())
            job.setdefault("status", "pending_analysis")
            existing.append(job)
            seen_ids.add(jid)
            added += 1

    save_jobs(existing)
    return added
