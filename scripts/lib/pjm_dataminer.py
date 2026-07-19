"""Shared PJM DataMiner2 REST client — paging + retry for the fetch_pjm_* scripts.

The ``fetch_pjm_*`` data scripts each pull one or more DataMiner2 feeds
(``https://api.pjm.com/api/v1/<feed>``) with the same mechanics: a public
subscription-key header, ``startRow``/``rowCount`` paging until a short page
arrives, ``format=csv`` with a UTF-8 BOM, and exponential back-off on HTTP
429/503. This module homes that once; a fetcher supplies only the feed name and
the per-request query params (date filter, sort/order, feed-specific extras).

The subscription key is PUBLIC — it is embedded verbatim in DataMiner2's own
Angular ``settings.json`` (``/config/settings.json``); it is not a secret.
"""

from __future__ import annotations

import csv
import io
import time
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://api.pjm.com/api/v1"
SUB_KEY = "6a75d9f6d933401dbb4f36f8e70b95b3"
PAGE_SIZE = 50_000  # rows per page (max the API allows)


def fetch_page(
    url: str,
    *,
    user_agent: str,
    retries: int = 4,
    sleep_s: float = 1.5,
    no_data_codes: tuple[int, ...] = (),
) -> list[dict]:
    """Fetch one CSV page from a fully-built DataMiner2 URL; return row dicts.

    Retries on HTTP 429/503 (and transient ``URLError``/``TimeoutError``) with
    exponential back-off. An empty body is a legitimate "no rows for this
    window" and returns ``[]``. Any status in ``no_data_codes`` (e.g. ``404`` /
    ``400``, which DataMiner2 returns inconsistently for a window before a
    feed's retention floor) also returns ``[]`` rather than raising. Other
    HTTP errors raise.
    """
    delay = sleep_s
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "Ocp-Apim-Subscription-Key": SUB_KEY,
                    "Accept": "text/csv",
                    "User-Agent": user_agent,
                },
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8-sig", errors="replace")  # strip BOM
            if not raw.strip():
                return []
            return list(csv.DictReader(io.StringIO(raw)))
        except urllib.error.HTTPError as exc:
            if exc.code in no_data_codes:
                print(
                    f"    HTTP {exc.code} — treating as no data for this window ({url})"
                )
                return []
            if exc.code in (429, 503) and attempt < retries:
                print(f"    HTTP {exc.code} — back-off {delay:.0f}s …")
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < retries:
                print(f"    network error ({exc}) — back-off {delay:.0f}s …")
                time.sleep(delay)
                delay *= 2
                continue
            raise
    return []


def fetch_feed(
    feed: str,
    params: dict,
    *,
    user_agent: str,
    page_size: int = PAGE_SIZE,
    sleep_s: float = 1.5,
    retries: int = 4,
    no_data_codes: tuple[int, ...] = (),
    verbose: bool = True,
) -> list[dict]:
    """Page through one DataMiner2 feed for one window; return the CSV rows.

    Args:
        feed: the DataMiner2 feed name (the URL path after ``/api/v1/``).
        params: the per-request query params EXCLUDING ``startRow``/``rowCount``
            (the date filter, ``sort``/``order``, ``format``, ``isActiveMetadata``
            and any feed-specific extras), in the order they should appear.
        user_agent: the ``User-Agent`` header the fetcher identifies itself with.
        page_size: rows per page; paging stops when a page returns fewer.
        sleep_s: seconds slept between pages (and the retry back-off base).
        retries: retries on 429/503/transient network errors.
        no_data_codes: HTTP statuses that mean "no data for this window" and
            return an empty page instead of raising.
        verbose: print per-page progress (matches the standalone fetchers).

    Returns:
        The concatenated row dicts across every page (possibly empty).
    """
    all_rows: list[dict] = []
    start_row = 1
    page = 1
    while True:
        query = {"startRow": str(start_row), "rowCount": str(page_size), **params}
        url = f"{API_BASE}/{feed}?" + urllib.parse.urlencode(query)
        if verbose:
            print(f"  page {page:3d}  startRow={start_row:>8d} … ", end="", flush=True)
        rows = fetch_page(
            url,
            user_agent=user_agent,
            retries=retries,
            sleep_s=sleep_s,
            no_data_codes=no_data_codes,
        )
        if verbose:
            print(f"{len(rows):>6d} rows")
        all_rows.extend(rows)
        if len(rows) < page_size:
            break
        start_row += page_size
        page += 1
        time.sleep(sleep_s)
    return all_rows
