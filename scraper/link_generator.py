"""
Method B: Generate a static HTML page with all pre-formatted search links.
Output filename includes the generation timestamp.
"""
import urllib.parse
from datetime import datetime
from pathlib import Path

from scraper.config import SearchConfig, AGGREGATOR_TEMPLATES, BOARD_QUERY_PARAMS, load_config
from scraper.utils import load_job_boards, get_domain, build_search_url

BOARDS_FILE = Path(__file__).parent.parent / "job_boards"
OUTPUT_DIR  = Path(__file__).parent.parent / "output"


def generate(config: SearchConfig | None = None) -> Path:
    if config is None:
        config = load_config()

    OUTPUT_DIR.mkdir(exist_ok=True)

    board_urls = load_job_boards(BOARDS_FILE)
    days    = config.date_range_days
    seconds = days * 86400
    now     = datetime.now()
    ts_file = now.strftime("%Y-%m-%d_%H-%M-%S")      # used in filename
    ts_display = now.strftime("%B %d, %Y at %I:%M %p")  # used in HTML header

    sections: list[str] = []

    for role in config.roles:
        role_enc = urllib.parse.quote(role)
        loc_enc  = urllib.parse.quote(config.location)
        rows: list[str] = []

        # Aggregator links
        agg_links = {
            "LinkedIn": AGGREGATOR_TEMPLATES["LinkedIn"].format(
                role=role_enc, location=loc_enc, seconds=seconds, days=days
            ),
            "Indeed": AGGREGATOR_TEMPLATES["Indeed"].format(
                role=role_enc, location=loc_enc, seconds=seconds, days=days
            ),
            "Glassdoor": AGGREGATOR_TEMPLATES["Glassdoor"].format(
                role=role_enc, location=loc_enc
            ),
            "ZipRecruiter": AGGREGATOR_TEMPLATES["ZipRecruiter"].format(
                role=role_enc, location=loc_enc
            ),
        }
        for name, url in agg_links.items():
            rows.append(
                f'<tr><td class="platform agg">{name}</td>'
                f'<td><a href="{url}" target="_blank" rel="noopener">{url}</a></td></tr>'
            )

        # Consulting / staffing board links
        for board_url in board_urls:
            domain = get_domain(board_url)
            param  = BOARD_QUERY_PARAMS.get(domain, "q")
            url    = build_search_url(board_url, param, role)
            rows.append(
                f'<tr><td class="platform board">{domain}</td>'
                f'<td><a href="{url}" target="_blank" rel="noopener">{url}</a></td></tr>'
            )

        sections.append(
            f'<h2>{role}</h2>'
            f'<table><thead><tr><th>Platform</th><th>Search URL</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
        )

    total_links = len(config.roles) * (4 + len(board_urls))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Job Search Links — {ts_display}</title>
<style>
  body  {{ font-family: system-ui, sans-serif; max-width: 1400px; margin: 2rem auto; padding: 0 1rem; }}
  h1   {{ color: #1a1a2e; margin-bottom: .25rem; }}
  h2   {{ color: #16213e; margin-top: 2.5rem; border-bottom: 2px solid #0f3460; padding-bottom: .4rem; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 1rem; font-size: .85rem; }}
  th, td {{ text-align: left; padding: .5rem .75rem; border: 1px solid #ddd; }}
  th   {{ background: #0f3460; color: #fff; }}
  tr:nth-child(even) {{ background: #f8f8f8; }}
  .agg  {{ font-weight: 700; color: #0f3460; }}
  .board {{ color: #444; }}
  a    {{ color: #e94560; word-break: break-all; }}
  a:hover {{ text-decoration: underline; }}
  .meta {{ color: #555; font-size: .85rem; margin: .25rem 0 2rem; }}
  .badge {{ display: inline-block; background: #0f3460; color: #fff; border-radius: 4px;
            font-size: .75rem; padding: .15rem .5rem; margin-left: .5rem; vertical-align: middle; }}
</style>
</head>
<body>
<h1>Job Search Links <span class="badge">{total_links} links</span></h1>
<p class="meta">
  Generated: {ts_display} &nbsp;|&nbsp;
  Roles: {len(config.roles)} &nbsp;|&nbsp;
  Location: {config.location} &nbsp;|&nbsp;
  Date range: last {config.date_range_days} days
</p>
{''.join(sections)}
</body>
</html>"""

    out_path = OUTPUT_DIR / f"search_links_{ts_file}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Search links written to: {out_path}")
    return out_path


if __name__ == "__main__":
    generate()
