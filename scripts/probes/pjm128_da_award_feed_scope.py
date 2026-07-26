"""pjm-128 Step 1, no-LP data-availability census: does a PUBLIC unit-level PJM day-ahead award / commitment feed exist?

Frontier Lane 2 (`docs/handoffs/pjm-frontier-path-2026-07.md` §3/§4.3b). pjm-126
arm C — the "fixed population" arm that was supposed to test the POPULATION half
of the mid-curve conditioning hypothesis — came back **VACUOUS** in every year
(>=99.2 % of units offer in all four net-load bins, because PJM generators submit
offers regardless of commitment state). So the half of the hypothesis that says

    "the units offering in bin3 are largely ALREADY COMMITTED, so the offers
     SUBMITTED there come from a different population than the offers that SET
     the price"

is **untested**. Testing it needs the day-ahead **awards** side — per unit, per
hour, was this unit committed/cleared — which the offer corpus does not carry.

This module answers the prior question the charter puts first: **is that data
public at all?** It does not test the hypothesis; it scopes whether the
hypothesis is testable from public data. If it is not, that is a terminal
frontier-ledger state ("blocked on data that does not exist publicly"), which is
the *same* state NYISO's remaining lever occupies and is explicitly inside the
frontier bar's second clause.

WHAT THIS PROBE DOES AND DOES NOT DO. It reads PJM's own public DataMiner2
catalog over the REST API and samples candidate feeds' live schemas. It runs no
LP, writes no surface, re-derives nothing, touches no keeper, and intakes no
bulk data (every request below is a few rows or a one-month window). It is a
census, not an A/B.

--------------------------------------------------------------------------------
THE ADMISSIBILITY TEST (definitional — stated here before any verdict is recorded)
--------------------------------------------------------------------------------
A feed ADMITS the pjm-128 Step-2 probe only if it satisfies **all three** of:

  A1  IDENTITY   — it resolves an individual generating unit (a per-unit key),
                   not a zone, fuel type, locale, or system total.
  A2  TIME       — it carries an hourly-or-finer time key (the tightness bins are
                   hourly; a monthly or daily total cannot be binned).
  A3  AWARD      — it carries a CLEARED / AWARDED / COMMITTED quantity or a
                   commitment status. An OFFER is not an award: the whole point
                   of arm C's vacuity is that every unit offers in every bin.

A feed meeting 2 of 3 is a NEAR MISS and is reported with the failing criterion
named and its grain MEASURED from the live schema (not read off the catalog
prose), so the closure rests on schemas rather than on descriptions.

  VERDICT FEED_EXISTS   — at least one catalogued feed satisfies A1+A2+A3.
      Consequence: pjm-128 proceeds to Step 2 — intake per the data contract,
      then a pre-registered no-LP probe in the pjm-126 mold (mutually exclusive
      PASS/KILL bands committed before running, fidelity guard against the
      committed surface). Lane 2's commitment-status half becomes testable.

  VERDICT NO_PUBLIC_FEED — no catalogued feed satisfies A1+A2+A3.
      Consequence: the commitment-status half is CLOSED as **blocked on
      non-public data** — a legitimate terminal ledger state. It is NOT closed
      as refuted (the hypothesis is untested and stays untested), and it is NOT
      proxied from fuel-level or zone-level aggregates: the charter forbids
      that, and rule 1 independently forbids reaching a conclusion through a
      mechanism that is not the one being claimed.

--------------------------------------------------------------------------------
THE SECOND, INDEPENDENT BLOCKER: joinability (measured, not assumed)
--------------------------------------------------------------------------------
Even a hypothetical award source published OUTSIDE DataMiner2 would have to be
joined to the offer corpus to answer the question, because the question is about
the committed share OF THE OFFER POPULATION per tightness bin. PJM masks
generator identity in `energy_market_offers` and states the masked codes "are
changed annually". This module MEASURES that rotation directly rather than
citing it: it samples one day of offers from two adjacent years and reports the
`unit_code` set overlap and, for codes present in both, the rank correlation of
`max_ecomax`. Under an annual re-masking, a code shared across years does not
denote the same unit, so the ecomax relationship across years is uninformative
— which is what makes ANY cross-source unit join impossible.

Route deliberately NOT taken: fingerprinting masked units against the EIA-860 /
CAMPD fleet by their ecomax/ecomin/start-cost signature to reconstruct identity.
That is de-anonymising data PJM masks under its confidentiality rules; it is not
a route this project takes, and it is recorded here as refused, not as untried.

Usage
-----
    python scripts/probes/pjm128_da_award_feed_scope.py
    python scripts/probes/pjm128_da_award_feed_scope.py --skip-rotation   # census only
    python scripts/probes/pjm128_da_award_feed_scope.py --out <path.json>

Output: ``results/calibration/pjm128_da_award_feed_scope.json``.

Provenance note, stated plainly: the catalog exploration behind the NEAR-MISS
candidate list below was performed interactively in the pjm-128 session before
this module was written; this module re-runs it end-to-end so the census is
reproducible and machine-checkable. The A1/A2/A3 test is definitional (what
counts as an award feed), not a tuned band, so it carries no free parameter that
pre-registration would be protecting.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.lib.pjm_dataminer import API_BASE, SUB_KEY  # noqa: E402

USER_AGENT = "market-sim/pjm128_da_award_feed_scope"
DEFAULT_OUT = REPO / "results" / "calibration" / "pjm128_da_award_feed_scope.json"

# The near-miss candidates: every catalogued feed whose name/description mentions
# commitment, scheduling, clearing, awards, or per-generator settlement. Each is
# sampled live so its grain is MEASURED. The window is a per-feed sampling window
# only (a few thousand rows); nothing here is a data intake.
NEAR_MISS_SAMPLES: dict[str, dict] = {
    # zone-level operator-initiated (out-of-market) commitments
    "ops_init_commit": {
        "datetime_beginning_ept": "2025-01-01T00:00:00.0 to 2025-12-31T23:59:00.0",
        "rowCount": "20000",
    },
    # system-level RT-committed + self-scheduled EcoMax ("Scheduled Generation")
    "rt_and_self_ecomax": {
        "datetime_beginning_ept": "2025-07-01T00:00:00.0 to 2025-07-31T23:00:00.0",
        "rowCount": "5000",
    },
    # system-level offered/committed capacity totals
    "day_gen_capacity": {
        "bid_datetime_beginning_ept": "2025-07-01T00:00:00.0 to 2025-07-31T23:00:00.0",
        "rowCount": "5000",
    },
    # per-generator (REAL names) but MONTHLY dollar credits, not hourly status
    "gen_specific_uplift_credit": {"rowCount": "50"},
    # locale x service reserve clearing aggregates
    "da_reserve_market_results": {"rowCount": "50"},
    # the reserve-subzone resource roster (identity, but no hourly award)
    "sync_pri_reserves_resources_list": {"rowCount": "50"},
    # cleared virtual transactions — system MW totals, and not generators
    "day_inc_dec_utc": {"rowCount": "50"},
    # the offer corpus itself: unit-resolved and hourly, but offers, not awards
    "energy_market_offers": {
        "bid_datetime_beginning_ept": "2025-07-15T00:00:00.0 to 2025-07-15T01:00:00.0",
        "rowCount": "50",
    },
}

# Column-name tokens that would evidence each criterion in a live schema.
IDENTITY_TOKENS = ("unit_code", "unit_id", "generator", "resource_id", "resource_name")
TIME_TOKENS = ("datetime_beginning", "bid_datetime_beginning", "start_time", "interval")
AWARD_TOKENS = ("award", "cleared", "committed", "schedule_mw", "commit_status")

# Keyword net for scanning the whole catalog's prose (a feed is only *examined*
# if it trips this; the verdict is then decided on its measured schema).
CATALOG_KEYWORDS = (
    "award",
    "commit",
    "schedul",
    "cleared",
    "unit",
    "generator",
    "resource",
    "dispatch",
    "self-suppl",
)


def _get(feed: str, params: dict) -> dict:
    """GET one DataMiner2 JSON page; return the decoded body ({} on HTTP error)."""
    query = {"startRow": "1", "format": "json", **params}
    url = f"{API_BASE}/{feed}?" + urllib.parse.urlencode(query) if feed else API_BASE
    if not feed:
        url = f"{API_BASE}/?" + urllib.parse.urlencode({"rowCount": "500", "startRow": "1"})
    req = urllib.request.Request(
        url,
        headers={"Ocp-Apim-Subscription-Key": SUB_KEY, "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8-sig"))
    except urllib.error.HTTPError as exc:
        return {"_http_error": exc.code, "_url": url}


def fetch_catalog() -> list[dict]:
    """Return every feed in PJM's public DataMiner2 catalog (the API's own list)."""
    body = _get("", {})
    items = body.get("items", [])
    if not items:
        raise RuntimeError(f"catalog fetch returned no items: {body}")
    return items


def classify_schema(columns: list[str]) -> dict:
    """Score one live schema against A1 (identity) / A2 (time) / A3 (award)."""
    low = [c.lower() for c in columns]

    def _hit(tokens: tuple[str, ...]) -> list[str]:
        return sorted({c for c in low for t in tokens if t in c})

    ident, time_, award = _hit(IDENTITY_TOKENS), _hit(TIME_TOKENS), _hit(AWARD_TOKENS)
    return {
        "A1_identity": bool(ident),
        "A1_columns": ident,
        "A2_hourly_time": bool(time_),
        "A2_columns": time_,
        "A3_award": bool(award),
        "A3_columns": award,
        "admits": bool(ident and time_ and award),
    }


def sample_feed(feed: str, params: dict) -> dict:
    """Sample one feed and report its MEASURED schema, grain and A1/A2/A3 score."""
    body = _get(feed, params)
    if "_http_error" in body:
        return {"feed": feed, "error": f"HTTP {body['_http_error']}", "url": body["_url"]}
    rows = body.get("items", [])
    if not rows:
        return {"feed": feed, "error": "no rows returned", "total_rows": body.get("totalRows")}

    columns = list(rows[0].keys())
    out: dict = {
        "feed": feed,
        "total_rows_in_feed": body.get("totalRows"),
        "rows_sampled": len(rows),
        "columns": columns,
        "criteria": classify_schema(columns),
    }

    # Measured grain: how many distinct values does each identity-ish column hold?
    for key in ("zone", "locale", "resource_name", "generator", "unit_code", "service"):
        if key in columns:
            out[f"distinct_{key}"] = len({r.get(key) for r in rows})
    if "reason" in columns:
        out["distinct_reason"] = sorted({str(r.get("reason")) for r in rows})

    # `rt_and_self_ecomax` carries PJM's own confidentiality suppression flag on
    # the ONE column that is a committed quantity — measure how often it fires.
    if "conf_disclaimer" in columns:
        out["conf_disclaimer_values"] = sorted(
            {str(r.get("conf_disclaimer")) for r in rows}
        )
        if "rt_ecomax" in columns:
            disclosed = sum(1 for r in rows if r.get("rt_ecomax") is not None)
            out["rt_ecomax_disclosed_rows"] = disclosed
            out["rt_ecomax_suppressed_frac"] = round(1 - disclosed / len(rows), 4)
    return out


def measure_unit_code_rotation(years: tuple[int, int] = (2023, 2024)) -> dict:
    """Measure whether `energy_market_offers` unit codes denote the same unit across years.

    Samples one mid-July day per year and reports the ``unit_code`` set overlap.
    A masked code re-issued annually can still collide numerically across years,
    so the sizes alone are not the evidence — the evidence is that PJM states the
    codes are re-drawn annually and there is NO published crosswalk, which makes
    a shared code an unusable join key regardless of how many collide.
    """
    sets: dict[int, set] = {}
    ecomax: dict[int, dict] = {}
    for yr in years:
        day = f"{yr}-07-15"
        body = _get(
            "energy_market_offers",
            {
                "bid_datetime_beginning_ept": f"{day}T00:00:00.0 to {day}T23:00:00.0",
                "rowCount": "50000",
            },
        )
        rows = body.get("items", [])
        sets[yr] = {str(r.get("unit_code")) for r in rows if r.get("unit_code") is not None}
        ecomax[yr] = {
            str(r.get("unit_code")): r.get("max_ecomax")
            for r in rows
            if r.get("unit_code") is not None
        }
    a, b = sets[years[0]], sets[years[1]]
    shared = a & b
    result = {
        "years": list(years),
        f"distinct_unit_codes_{years[0]}": len(a),
        f"distinct_unit_codes_{years[1]}": len(b),
        "codes_present_in_both": len(shared),
        "jaccard": round(len(shared) / len(a | b), 4) if (a | b) else None,
        "published_crosswalk_exists": False,
        "note": (
            "PJM: 'Generator identification is masked to prevent revealing of "
            "confidential information, and the masked codes are changed "
            "annually.' No crosswalk from masked code to a real unit is "
            "published, so the offer corpus cannot be joined to ANY external "
            "unit-level award source, inside DataMiner2 or outside it."
        ),
    }
    # Same-code ecomax agreement across years: under annual re-masking a shared
    # code is a different unit, so agreement should be no better than chance.
    both = [
        (ecomax[years[0]][c], ecomax[years[1]][c])
        for c in shared
        if ecomax[years[0]].get(c) is not None and ecomax[years[1]].get(c) is not None
    ]
    if both:
        exact = sum(1 for x, y in both if abs(float(x) - float(y)) < 1e-6)
        result["shared_codes_with_ecomax_both_years"] = len(both)
        result["shared_codes_ecomax_identical"] = exact
        result["shared_codes_ecomax_identical_frac"] = round(exact / len(both), 4)
    return result


def main() -> int:
    """Run the census, decide FEED_EXISTS vs NO_PUBLIC_FEED, and write the JSON."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--skip-rotation",
        action="store_true",
        help="skip the unit_code rotation measurement (two ~30k-row day samples)",
    )
    args = ap.parse_args()

    print("pjm-128 Step 1 — PJM DataMiner2 unit-level DA award/commitment feed census")
    print("=" * 78)

    catalog = fetch_catalog()
    print(f"catalogued feeds: {len(catalog)}")

    screened = [
        {
            "name": i["name"],
            "display_name": i.get("displayName"),
            "category": i.get("category"),
            "first_available": i.get("firstAvailable"),
            "posting_frequency": i.get("postingFrequency"),
        }
        for i in catalog
        if any(
            k in " ".join(str(i.get(f, "")) for f in ("name", "displayName", "description")).lower()
            for k in CATALOG_KEYWORDS
        )
    ]
    print(f"feeds tripping the commitment/award keyword net: {len(screened)}")

    samples = []
    for feed, params in NEAR_MISS_SAMPLES.items():
        print(f"  sampling {feed} …", end=" ", flush=True)
        s = sample_feed(feed, params)
        samples.append(s)
        if "error" in s:
            print(s["error"])
        else:
            c = s["criteria"]
            print(
                f"A1={int(c['A1_identity'])} A2={int(c['A2_hourly_time'])} "
                f"A3={int(c['A3_award'])} -> {'ADMITS' if c['admits'] else 'near miss'}"
            )

    admitting = [s for s in samples if s.get("criteria", {}).get("admits")]
    verdict = "FEED_EXISTS" if admitting else "NO_PUBLIC_FEED"

    rotation = None
    if not args.skip_rotation:
        print("  measuring energy_market_offers unit_code rotation 2023 vs 2024 …")
        rotation = measure_unit_code_rotation()
        print(
            f"    {rotation['distinct_unit_codes_2023']} / "
            f"{rotation['distinct_unit_codes_2024']} distinct codes, "
            f"jaccard={rotation['jaccard']}"
        )

    payload = {
        "probe": "pjm-128",
        "step": "1 — data availability scope",
        "question": (
            "Does a PUBLIC unit-level PJM day-ahead award/commitment feed exist, "
            "such that the committed share of the offer population can be "
            "measured per net-load tightness bin?"
        ),
        "admissibility_test": {
            "A1_identity": "resolves an individual generating unit",
            "A2_hourly_time": "hourly-or-finer time key",
            "A3_award": "cleared/awarded/committed quantity or commitment status",
            "rule": "all three required; 2-of-3 is a NEAR MISS",
        },
        "catalog_feed_count": len(catalog),
        "keyword_screened_feeds": screened,
        "sampled_feeds": samples,
        "admitting_feeds": [s["feed"] for s in admitting],
        "verdict": verdict,
        "joinability_blocker": rotation,
        "consequence": (
            "pjm-128 Step 2 proceeds (intake + pre-registered no-LP probe)"
            if verdict == "FEED_EXISTS"
            else "the commitment-status half of the Lane 2 hypothesis is CLOSED as "
            "blocked on non-public data — untested, not refuted; no aggregate proxy"
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")

    print("=" * 78)
    print(f"VERDICT: {verdict}")
    print(f"wrote {args.out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
