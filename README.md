# Job Hunt Aggregator

Searches multiple job platforms and consulting/staffing boards for roles that match your profile, collecting links into a browsable HTML file or saving full job details to `jobs.json`.

---

## Project Structure

```
job-hunt/
├── config.yaml          ← edit this to change roles, location, filters
├── job_boards           ← list of consulting/staffing board URLs (one per line)
├── main.py              ← entry point
├── requirements.txt
├── scraper/
│   ├── config.py        ← loads config.yaml, holds URL templates
│   ├── link_generator.py
│   ├── runner.py
│   ├── storage.py
│   ├── utils.py
│   └── platforms/
│       ├── linkedin.py
│       ├── indeed.py
│       ├── ziprecruiter.py
│       └── consulting_board.py
└── output/              ← generated HTML files land here (git-ignored)
```

---

## Setup

### 1. Prerequisites

- Python 3.11 or higher
- pip

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install the Playwright browser (only needed for Method A)

```bash
python -m playwright install chromium
```

---

## Configuration

Open **`config.yaml`** and edit it before running anything:

```yaml
roles:
  - Full Stack Developer
  - React Developer
  - Python Developer

location: Remote          # or "New York, NY", "United States", etc.
date_range_days: 14       # only show postings from the last N days
max_results_per_site: 25  # cap per site per role
```

To add or remove job boards, edit the **`job_boards`** file — one URL per line.

---

## Usage

### Method B — Generate search links HTML (recommended starting point)

Produces a timestamped HTML file in `output/` containing pre-built search links for every role × every platform. Open it in a browser and click through manually.

```bash
python main.py links
```

Add `--open` to automatically open the file in your default browser:

```bash
python main.py links --open
```

Output example: `output/search_links_2026-06-08_14-30-00.html`

---

### Method A — Automated Playwright scraper

Headlessly visits every platform, extracts job cards, filters by role keywords, and saves results to `jobs.json`. Respects random delays between requests to avoid rate limits.

```bash
python main.py scrape
```

---

### View saved jobs

```bash
python main.py list

# filter by status
python main.py list --status pending_analysis
```

---

## Output format (`jobs.json`)

```json
[
  {
    "id": "a3f1b2c4d5e6f7a8",
    "job_title": "Senior Frontend Engineer",
    "company": "Tech Corp Inc.",
    "location": "Remote, USA",
    "source_platform": "LinkedIn",
    "job_url": "https://www.linkedin.com/jobs/view/1234567890/",
    "date_posted": "2026-06-01",
    "date_scraped": "2026-06-08T14:30:00Z",
    "raw_description_text": "We are looking for...",
    "status": "pending_analysis"
  }
]
```

New runs deduplicate against existing entries using a hash of `company + job_title + job_url`.
