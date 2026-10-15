"""Direct Naukri search API (JobSpy-port fast path for skills scans).

Ports the approach verified against the reference repo
(speedyapply/JobSpy, MIT — ``jobspy/naukri/{__init__,util,constant}.py``)
and validated against two HAR captures of real manual searches plus a live
``200`` probe with a fresh self-generated token:

* ``GET https://www.naukri.com/jobapi/v3/search`` with ``appid: 109`` and a
  per-request ``nkparam`` header — RSA (PKCS#1 v1.5) of
  ``v0|<epoch-ms>|121_<page>`` under Naukri's public key. Pure stdlib
  (``pow`` modular exponentiation); no browser, no login cookies.
* 20 rows per page (``noOfResults``/``pageNo``); every row already carries
  ``tagsAndSkills`` + ``companyName`` — skills need no detail visits.
* ``406`` = rate-limited or rotated key (JobSpy documents both); ``400``
  past the last page. Either way the caller falls back to the browser.

Freshness-first like the UI: ``jobAge`` + ``sort=f`` (JobSpy's pattern,
``jobAge`` user-verified in the manual HAR).
"""
from __future__ import annotations

import base64
import functools
import logging
import secrets
import time

import httpx

from ..models import Job
from ..naukri_scraper import ProgressHook, StopHook, build_skills_report, coerce_job
from ..stealth_browser import human_pause

log = logging.getLogger(__name__)

#: Search API + token inputs (JobSpy ``jobspy/naukri/constant.py``).
SEARCH_URL = "https://www.naukri.com/jobapi/v3/search"
APP_ID = "109"
JOBS_PER_API_PAGE = 20

#: Naukri's RSA public key for ``nkparam`` (JobSpy constant, MIT).
#: Breaks when Naukri rotates it — symptom: HTTP 406 everywhere.
NK_PUBLIC_KEY = (
    "MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBALrlQ+djR0RjJwBF1xuisHmdFv334MImK6LgzJhmLhN7"
    "B5yuEyaKoasgXQk3+OQglsOaBxEJ0j5PcTL3nbOvt80CAwEAAQ=="
)


def company_mode(params: dict) -> bool:
    """True unless the caller explicitly asked for per-posting counts."""
    return (params.get("count_mode") or "companies") != "postings"


class NkApiError(Exception):
    """The API fast path failed (rate-limit, rotated key, network)."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


def _read_der(data: bytes, i: int) -> tuple[bytes, int]:
    """DER value at ``data[i]`` + index after it (minimal ASN.1 reader)."""
    length = data[i + 1]
    i += 2
    if length & 0x80:
        size = length & 0x7F
        length = int.from_bytes(data[i:i + size], "big")
        i += size
    return data[i:i + length], i + length


@functools.cache
def _public_key() -> tuple[int, int]:
    """Naukri RSA (modulus, exponent) from the DER public key."""
    key, _ = _read_der(base64.b64decode(NK_PUBLIC_KEY), 0)
    _, i = _read_der(key, 0)
    bit_string, _ = _read_der(key, i)
    rsa_key, _ = _read_der(bit_string[1:], 0)
    modulus, i = _read_der(rsa_key, 0)
    exponent, _ = _read_der(rsa_key, i)
    return int.from_bytes(modulus, "big"), int.from_bytes(exponent, "big")


def generate_nkparam(page: str = "srp") -> str:
    """Fresh request token: RSA-encrypt ``v0|<ms>|121_<page>`` (JobSpy util).

    ``page`` is ``"srp"`` for search (fresh token per request — captured
    HAR values are time-bound and must NOT be replayed).
    """
    modulus, exponent = _public_key()
    size = (modulus.bit_length() + 7) // 8
    message = f"v0|{int(time.time() * 1000)}|121_{page}".encode()
    padding = bytes(secrets.randbelow(255) + 1
                    for _ in range(size - 3 - len(message)))
    block = b"\x00\x02" + padding + b"\x00" + message
    cipher = pow(int.from_bytes(block, "big"), exponent, modulus)
    return base64.b64encode(cipher.to_bytes(size, "big")).decode()


def fetch_search_page(keywords: str, location: str, experience: int,
                      days: int, page_no: int) -> tuple[list[dict], int | None]:
    """One API result page → ``(raw job rows, total or None)``.

    ``400`` means past the last page → ``([], None)``. Anything else
    non-200 (notably ``406``) raises :class:`NkApiError` for the browser
    fallback. Params mirror the manual-search HAR capture exactly.
    """
    try:
        response = httpx.get(
            SEARCH_URL,
            params={"noOfResults": JOBS_PER_API_PAGE,
                    "urlType": "search_by_key_loc", "searchType": "adv",
                    "location": location, "keyword": keywords,
                    "sort": "f", "pageNo": page_no,
                    "experience": experience, "jobAge": days},
            headers={"appid": APP_ID, "systemid": "Naukri",
                     "nkparam": generate_nkparam("srp"),
                     "Accept": "application/json",
                     "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X "
                                    "10_15_7) AppleWebKit/537.36 (KHTML, like "
                                    "Gecko) Chrome/126.0.0.0 Safari/537.36")},
            timeout=30,
        )
    except Exception as e:
        raise NkApiError(f"search API unreachable: {e}") from e
    if response.status_code == 400:
        return [], None  # past the last page — clean end, not an error
    if response.status_code != 200:
        raise NkApiError(f"search API refused: HTTP {response.status_code}",
                         status=response.status_code)
    payload = response.json()
    return payload.get("jobDetails") or [], payload.get("noOfJobs")


def api_job_to_raw(api_job: dict) -> dict:
    """Map one API job row onto the extractor dict shape (for coercion).

    Reuses the same Pydantic gate as browser cards: bad rows drop with a
    warning instead of poisoning the report.
    """
    tags = [s.strip() for s in str(api_job.get("tagsAndSkills") or "").split(",")
            if s.strip()]
    jd_url = str(api_job.get("jdURL") or "")
    url = ("https://www.naukri.com" + jd_url) if jd_url.startswith("/") else jd_url
    return {"jobId": str(api_job.get("jobId") or ""),
            "title": api_job.get("title") or "",
            "company": api_job.get("companyName") or "",
            "location": "", "experience": api_job.get("experienceText") or "",
            "salary": "", "posted": "",
            "snippet": str(api_job.get("jobDescription") or "")[:600],
            "url": url, "skills": tags}


def api_collect_jobs(params: dict, should_stop: StopHook,
                     on_progress: ProgressHook) -> list[Job]:
    """Collect postings over the API (no browser): page until cap/empty.

    Shared by skills scans (which aggregate) and collect runs (which
    persist). Polite 2–5s pauses between pages (JobSpy sleeps 3–7s).
    Stops at ``max_jobs``, an empty page, the reported total, or cancel.
    Returns ``(jobs, pages_fetched)``.
    """
    keywords = str(params.get("keywords") or "").strip()
    location = str(params.get("location") or "pune").strip().lower()
    experience = params.get("experience") or 6
    days = params.get("days") or 7
    max_jobs = params.get("max_jobs") or 100
    found: dict[str, Job] = {}
    # Bounded page range: caps API requests even when every page is fresh.
    max_pages = max_jobs // JOBS_PER_API_PAGE + 2
    total = None
    pages_fetched = 0
    for page_no in range(1, max_pages + 1):
        if should_stop():
            log.info("Skills API scan cancel requested — stopping")
            break
        rows, total = fetch_search_page(keywords, location, experience,
                                        days, page_no)
        pages_fetched = page_no
        if not rows:
            break
        for raw in rows:
            job: Job | None = coerce_job(api_job_to_raw(raw),
                                         search_location=location)
            if job is None or job.job_id in found:
                continue
            found[job.job_id] = job
            if len(found) >= max_jobs:
                break
        on_progress({"stage": "search", "location": location, "page": page_no,
                     "found": len(found), "source": "api"})
        if len(found) >= max_jobs:
            break
        if total is not None and page_no * JOBS_PER_API_PAGE >= total:
            break
        human_pause()  # politeness between API pages
    return list(found.values()), pages_fetched


def api_scan_skills(params: dict, should_stop: StopHook,
                    on_progress: ProgressHook) -> dict:
    """Full skills report over the API (no browser): collect then aggregate."""
    by_company = company_mode(params)
    jobs, _ = api_collect_jobs(params, should_stop, on_progress)
    return build_skills_report(jobs, by_company=by_company)
