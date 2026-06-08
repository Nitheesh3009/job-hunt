# Job Search & URL Aggregator Instructions

This document provides detailed instructions and specifications for searching multiple job websites, targeting specific roles, and saving the job URLs and metadata to a structured file. This file will serve as the reference blueprint for building the automated job hunt and profile matcher application.

---

## 📋 Table of Contents
1. [Target Roles & Search Scope](#1-target-roles--search-scope)
2. [Target Job Platforms](#2-target-job-platforms)
3. [Search Strategies & Methods](#3-search-strategies--methods)
4. [Output Data Structure](#4-output-data-structure)
5. [Anti-Scraping & Operational Safety](#5-anti-scraping--operational-safety)
6. [Next Steps: The Profile Matching Project](#6-next-steps-the-profile-matching-project)

---

## 1. Target Roles & Search Scope

Before initiating any searches, define the primary search parameters. 

### Target Roles (Examples)
*   **Role A**: Full Stack Developer / Engineer (React, Node.js)
*   **Role B**: Python Developer / Backend Engineer (Django, FastAPI, PostgreSQL)
*   **Role C**: Frontend Engineer (React, TypeScript, CSS)
*   **Role D**: AI / Machine Learning Engineer

### Search Filters & Criteria
*   **Locations**: Remote (US/Worldwide), Hybrid (Specific City), or Onsite.
*   **Experience Level**: Entry-level, Mid-level, Senior.
*   **Date Posted**: Last 24 hours, last 3 days, or last week (to target active postings).
*   **Job Type**: Full-time, Contract.

---

## 2. Target Job Platforms

Our system checks two categories of targets: **Primary Job Aggregators** and **Consulting & Staffing Boards**.

### 2.1 Primary Job Aggregators

These platforms have high volume and require specialized scraper setups:

| Platform | Query URL Pattern / Search Query | Method | Notes |
| :--- | :--- | :--- | :--- |
| **LinkedIn** | `https://www.linkedin.com/jobs/search/?keywords={role}&location={location}&f_TPR=r2592000` | Playwright / API | Requires cookie session state or API proxy due to strict rate limits. |
| **Indeed** | `https://www.indeed.com/jobs?q={role}&l={location}&fromage=14` | Playwright / Puppeteer | Uses Cloudflare protection; requires browser emulation. |
| **Glassdoor** | `https://www.glassdoor.com/Job/jobs.htm?sc.keyword={role}` | Playwright / API | Best accessed via third-party APIs or automated scroll-scrapers. |
| **ZipRecruiter** | `https://www.ziprecruiter.com/candidate/search?search={role}&location={location}` | API / Scrape | Relatively scraper-friendly layout. |

### 2.2 Consulting & Staffing Job Boards (Loaded from `job_boards`)

In addition to major aggregators, the system must ingest the custom consulting search pages listed in the [job_boards](file:///e:/projects/job-hunt/job_boards) file. These agencies post direct, high-intent roles that are often not aggregated immediately.

Since these boards use a variety of third-party applicant tracking systems (ATS) or custom layouts, here is the mapping guide for parsing them:

| Consulting Site Example | Common Search Structure / URL Pattern | Common ATS Backend / Selector |
| :--- | :--- | :--- |
| **Trident Consulting** | `https://tridentconsultinginc.com/Jobs/?search={role}` | WordPress / Custom table elements |
| **Experis** | `https://www.experis.com/en/search?query={role}` | Custom React app |
| **TEKsystems** | `https://www.teksystems.com/en/careers/all-jobs?search={role}` | Custom search client |
| **Apex Systems** | `https://www.apexsystems.com/search-results-usa?q={role}` | Custom layout / Search API |
| **Dexian** | `https://dexian.com/jobs/?search={role}` | Custom / WordPress |
| **BCforward** | `https://bcforward.jobs.net/jobs?q={role}` | CareerBuilder / Jobs.net framework |

---

## 3. Search Strategies & Methods

Depending on the complexity and constraints of the project, use one of the following two methods:

### Method A: Automated Scraper (Recommended)
Build a Node.js or Python automation script using **Playwright** or **Selenium** to perform searches and scrape URLs automatically.

> [!TIP]
> **Why Playwright?** Playwright is excellent for bypassing browser detection, allows running in headful or headless mode, and supports stealth plugins to emulate human behavior.

#### High-Level Flow for Aggregators & Consulting Boards:
1.  **Load Job Board Inputs**:
    *   Read the URLs list from [job_boards](file:///e:/projects/job-hunt/job_boards).
2.  **Initialize Browser & Config**:
    *   Initialize a browser context with human-like viewport dimensions and user-agent strings.
    *   Define query parameter rules for each domain (e.g., mapping `teksystems.com` to use `?search={role}`, `bcforward.jobs.net` to use `?q={role}`, etc.).
3.  **Search Formulation**:
    *   For each role (e.g., *Frontend Developer*, *Python Developer*):
        *   Formulate search URLs for aggregators (LinkedIn, Indeed, etc.).
        *   Formulate search URLs for each consulting site loaded from [job_boards](file:///e:/projects/job-hunt/job_boards) using their query rules. If a site doesn't support query parameters, navigate to the base jobs directory and use the search bar element to type the role, or download the full list of jobs and filter locally.
4.  **Navigation & Scraping**:
    *   Navigate to each search results page.
    *   Auto-scroll or handle pagination to trigger loading of search result elements.
5.  **Extract & Filter (Roles Match)**:
    *   Extract job listing card data (Title, Company, URL, Posting Date).
    *   **Keyword Filtering**: Filter out any listings whose titles do not contain matching terms for the target role (e.g., if searching for "Frontend", verify the title contains "Frontend", "React", "UI", etc., to ignore unrelated roles).
6.  **Resolve Links**:
    *   Clean and resolve redirected links (especially tracker or ATS redirection URLs) to get the direct application URLs.
7.  **Save Results**:
    *   Append new listings to `jobs.json` ensuring no duplicates (using a hash of `company` + `job_title` or the unique `job_url`).

---

### Method B: Semi-Automated Search Link Generator
If full automation is restricted by logins/CAPTCHAs, use a script to generate a list of pre-configured search query URLs. 

#### High-Level Flow:
1. Run a local utility script that reads inputs: `roles`, `location` and the URLs from [job_boards](file:///e:/projects/job-hunt/job_boards).
2. Generate a custom index HTML page containing clickable, pre-formatted search links for all platforms, consulting boards, and roles.
3. Open the webpage, click each link to review the open roles, and use a browser extension (like Link Klipper or Simple Mass Downloader) to capture URLs from search results.
4. Save the captured URLs into the `jobs.json` file.


---

## 4. Output Data Structure

All gathered job details must be saved in a structured format in a file named `jobs.json`. This format ensures that the downstream profile matcher can read, parse, and score each role easily.

### Target Schema (`jobs.json`)
```json
[
  {
    "id": "unique-uuid-or-hash",
    "job_title": "Senior Frontend Engineer",
    "company": "Tech Corp Inc.",
    "location": "Remote, USA",
    "source_platform": "LinkedIn",
    "job_url": "https://www.linkedin.com/jobs/view/1234567890/",
    "date_posted": "2026-06-08",
    "date_scraped": "2026-06-08T10:50:00Z",
    "raw_description_text": "We are looking for a Senior React Developer...",
    "status": "pending_analysis"
  }
]
```

> [!IMPORTANT]
> **Why raw_description_text?** Keeping the raw text of the job description is critical for matching algorithms (TF-IDF, LLM-based parsing, or keyword checking) to compute the match percentage with your profile.

---

## 5. Anti-Scraping & Operational Safety

When automation scrapes multiple job sites, strict rate limiting or IP blocks can occur. Follow these safety rules:

*   **Request Intervals**: Insert random delays (between 3 to 8 seconds) between actions to mimic human reading and scrolling speeds.
*   **User-Agent Rotation**: Use standard browser headers matching realistic desktop operating systems.
*   **Session Persistence**: Save browser sessions/cookies locally to avoid repeatedly performing logins that trigger verification challenges.
*   **Target Scope Limit**: Limit each scraper run to the top 20–30 search results per site to minimize request footprints.

---

## 6. Next Steps: The Profile Matching Project

Once the URL scraping tool saves job details to `jobs.json`, the matching phase can proceed. The next project component should:

1.  **Read Candidate Profile**: Parse the user's resume, skill lists, and career objectives from a markdown or JSON file.
2.  **Compare & Match**:
    *   **Keyword Scoring**: Check for key technologies, frameworks, and methodologies.
    *   **Semantic Matching (Optional)**: Send the resume and job description to an LLM API to evaluate the alignment score.
3.  **Produce Recommendations**: Generate a reports dashboard indicating match percentage, key missing skills, and direct application links sorted by match quality.
