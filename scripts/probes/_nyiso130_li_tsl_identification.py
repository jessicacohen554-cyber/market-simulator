"""nyiso-130 Phase 0 — identify the Long Island (Zone K) in-window transfer cap.

Measurement-only probe for the nyiso-129-named successor lever (the ISO's
lever-queue item 1, `docs/mechanism-testing-matrix.md` §5.5): the armed
``nyiso_li_lcr_tsl`` applies the PUBLISHED Zone-K "Locality Limit"
(325/275/275 MW) as an in-window HOURLY ENERGY bound on the model's only
mainland->Long_Island AC link, and nyiso-129 measured that bound saturated in
100 % of the 22 C3c-2023 tail hours.

This probe answers, from committed artifacts and NYISO's own postings ONLY --
**no solve is spent** -- the two questions the reconciliation turns on:

1. **What IS the published number?**  Four consecutive NYISO Locality Bulk
   Power Transmission Capability / TSL reports (capability years 2023/24
   through 2026/27) are parsed for the Zone-K table.  Every edition names the
   same limiting element (Dunwoodie-Shore Road Y50 345 kV @ LTE 964 MVA) and
   carries the SAME 660 MW Neptune HVDC loss-of-source inside the number; the
   2024/25, 2025/26 and 2026/27 editions additionally state, in a footnote,
   the transfer limit itself: *"The true N-1-1 Transmission Security Limit is
   940 in this scenario, the Bulk Transfer Limit accounts for the loss-of-
   source of 660 MW."*

2. **Where does the model stand?**  The designated keeper's committed
   ``hourly/network_<year>.parquet`` and ``hourly/system_<year>.parquet``
   sidecars give the link's realised flow/bound occupancy, the C3c tail-hour
   census by zone, and the in-window Zone-K headroom -- i.e. the ex-ante
   sensitivity the A/B is pre-registered against.

Rule 13 ``[R-MEASURED]``: every quantity here is either a published planning
input (regenerates for a forward year from the same annual posting) or a
readout of an already-committed model artifact.  Nothing is identified from a
price residual.

Run: ``python scripts/probes/_nyiso130_li_tsl_identification.py``
Writes ``results/calibration/_nyiso130_li_tsl_identification.json``.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

# The designated keeper bundle (2026-08-06-nyiso-128-solar-basis).
KEEPER_BUNDLE = REPO_ROOT / "results" / "calibration" / "nyiso128_treatment"
YEARS = (2023, 2024, 2025)

# The model link that carries the whole mainland->Zone-K AC interface.
LI_AC_LINK = "NYC>Long_Island"
LI_EXTERNAL_LINK = "NYISO_external>Long_Island"

# HB14-21 — NYISO_SELFSUPPLY_FLOOR_HOURS, the design-cooling window the armed
# cap is applied in (model/interchange/nyiso.py).
WINDOW_HOURS = tuple(range(14, 22))

# C3c gate (scripts/calibration_verdict.py): NYISO tail threshold and band.
TAIL_THRESHOLD_NYISO = 300.0
TAIL_LO, TAIL_HI = 0.5, 2.0
# Committed RT actual tail counts (tail/actual_tail.json, the scorer's actual).
RT_ACTUAL_TAIL = {2023: 10, 2024: 12, 2025: 42}

# NYISO postings.  Cached under the session scratchpad by the caller (curl);
# the URLs are recorded so the extraction is reproducible.
TSL_REPORTS: dict[str, dict[str, str]] = {
    "2023/2024": {
        "url": (
            "https://www.nyiso.com/documents/20142/34388803/"
            "Summer2023_N-1-1_Analysis_FINAL_DRAFT_20221018.pdf"
        ),
        "cache": "li_tsl_2324.pdf",
    },
    "2024/2025": {
        "url": (
            "https://www.nyiso.com/documents/20142/40834869/"
            "2024-25%20Locality%20Bulk%20Power%20Transmission%20Capability%20Report.pdf"
        ),
        "cache": "li_tsl_2425.pdf",
    },
    "2025/2026": {
        "url": (
            "https://www.nyiso.com/documents/20142/47642242/"
            "2025-26%20Locality%20Bulk%20Power%20Transmission%20Capability%20Report_Final.pdf"
        ),
        "cache": "li_tsl_2526.pdf",
    },
    "2026/2027": {
        "url": (
            "https://www.nyiso.com/documents/20142/53789919/"
            "2026%20Locality%20Bulk%20Power%20Transmission%20Capability%20Report.pdf"
        ),
        "cache": "li_tsl_2627.pdf",
    },
}


def extract_zone_k_tables(cache_dir: Path) -> dict[str, dict]:
    """Parse the Zone-K table out of each cached NYISO TSL report.

    Returns one record per capability year with the published Locality Limit,
    the limiting element / contingency strings, and any stated "true N-1-1
    Transmission Security Limit".  A report that is not cached locally yields
    ``{"unavailable": ...}`` rather than a guess.
    """
    try:
        from pypdf import PdfReader
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"unavailable": f"pypdf import failed: {exc}"}

    out: dict[str, dict] = {}
    for cy, meta in TSL_REPORTS.items():
        path = cache_dir / meta["cache"]
        if not path.exists():
            out[cy] = {"unavailable": f"not cached: {path.name}", "url": meta["url"]}
            continue
        text = "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
        # The Zone-K block runs from its own table heading to the next one.
        start = text.rfind("TABLE 1")
        block = text[start : start + 1200] if start >= 0 else ""
        limit = re.search(r"(\d[\d,]*)\s*MW\s*\(1\)", block)
        true_n11 = re.search(
            r"true\s+N-1-1\s+Transmission\s+Security\s+Limit\s+is\s+([\d,]+)", block
        )
        loss_of_source = re.search(r"loss-?of-?source\s*\n?\s*of\s+([\d,]+)", block)
        rating = re.search(r"@\s*LTE\s+([\d,]+)\s*MVA", block)
        out[cy] = {
            "url": meta["url"],
            "published_locality_limit_mw": (
                float(limit.group(1).replace(",", "")) if limit else None
            ),
            "true_n11_tsl_mw": (
                float(true_n11.group(1).replace(",", "")) if true_n11 else None
            ),
            "loss_of_source_deduction_mw": (
                float(loss_of_source.group(1).replace(",", "")) if loss_of_source else None
            ),
            "limiting_element_lte_mva": (
                float(rating.group(1).replace(",", "")) if rating else None
            ),
            "limiting_element": "Dunwoodie - Shore Road (Y50) 345 kV"
            if "Shore Road" in block
            else None,
            "zone_k_table_text": " ".join(block.split())[:900],
        }
    return out


def link_occupancy(bundle: Path) -> dict[str, dict]:
    """Per-year bound occupancy and flow distribution on both Zone-K links."""
    out: dict[str, dict] = {}
    for year in YEARS:
        net = pd.read_parquet(bundle / "hourly" / f"network_{year}.parquet")
        net = net[(net["kind"] == "link") & (net["pass"] == "P1")]
        rec: dict = {}
        for link in (LI_AC_LINK, LI_EXTERNAL_LINK):
            g = net[net["name"] == link].sort_values("hour")
            if g.empty:
                continue
            mw = g["mw"].to_numpy(float)
            lim = g["limit_up"].to_numpy(float)
            hod = g["hour"].to_numpy(int) % 24
            inw = np.isin(hod, WINDOW_HOURS)
            at_bound = mw >= 0.999 * lim
            rec[link] = {
                "limit_in_window_mw": sorted(np.unique(lim[inw]).tolist()),
                "limit_off_window_mw": sorted(np.unique(lim[~inw]).tolist()),
                "flow_in_window_p50": float(np.percentile(mw[inw], 50)),
                "flow_in_window_p95": float(np.percentile(mw[inw], 95)),
                "flow_off_window_p50": float(np.percentile(mw[~inw], 50)),
                "flow_off_window_p95": float(np.percentile(mw[~inw], 95)),
                "flow_off_window_max": float(mw[~inw].max()),
                "at_bound_share_all_hours": float(at_bound.mean()),
                "at_bound_share_in_window": float(at_bound[inw].mean()),
                "off_window_hours_above_940": int((mw[~inw] > 940.0).sum()),
                "off_window_hours": int((~inw).sum()),
            }
        out[str(year)] = rec
    return out


def tail_census(bundle: Path) -> dict[str, dict]:
    """C3c tail-hour census: count, zone incidence, and Zone-K link state.

    The scorer counts hours whose MAX ZONAL dual exceeds the NYISO $300/MWh
    threshold; this reproduces that count off the committed system sidecar and
    then attributes each tail hour to the zone that set the maximum.
    """
    out: dict[str, dict] = {}
    for year in YEARS:
        sysdf = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
        sysdf = sysdf[sysdf["pass"] == "P1"]
        wide = sysdf.pivot_table(index="hour", columns="zone", values="price")
        maxp = wide.max(axis=1)
        argz = wide.idxmax(axis=1)
        tail = maxp[maxp > TAIL_THRESHOLD_NYISO]
        zones = argz.loc[tail.index]
        net = pd.read_parquet(bundle / "hourly" / f"network_{year}.parquet")
        net = net[(net["kind"] == "link") & (net["pass"] == "P1")]
        state: dict[str, float] = {}
        for link in (LI_AC_LINK, LI_EXTERNAL_LINK):
            g = net[net["name"] == link].set_index("hour")
            if g.empty:
                continue
            sub = g.loc[g.index.intersection(tail.index)]
            if sub.empty:
                state[link] = float("nan")
                continue
            state[link] = float(
                (sub["mw"].to_numpy(float) >= 0.999 * sub["limit_up"].to_numpy(float)).mean()
            )
        actual = RT_ACTUAL_TAIL[year]
        lo, hi = TAIL_LO * actual, TAIL_HI * actual
        out[str(year)] = {
            "model_tail_hours": int(len(tail)),
            "rt_actual_tail_hours": actual,
            "ratio": round(len(tail) / actual, 3) if actual else None,
            "gate_band_hours": [lo, hi],
            "gate_status": "PASS" if lo <= len(tail) <= hi else "FAIL",
            "headroom_to_lower_edge_hours": int(len(tail) - int(np.ceil(lo))),
            "tail_hours_by_zone": zones.value_counts().to_dict(),
            "tail_hours_by_hour_of_day": (
                pd.Series(tail.index % 24).value_counts().sort_index().to_dict()
            ),
            "share_of_tail_hours_in_window": float(
                np.isin(tail.index % 24, WINDOW_HOURS).mean()
            )
            if len(tail)
            else None,
            "zone_k_links_at_bound_share_in_tail": state,
        }
    return out


def in_window_zone_k_headroom(bundle: Path) -> dict[str, dict]:
    """Zone-K in-window demand and price level, the sensitivity denominator.

    A +/-1 MW change in the AC bound moves Zone-K supply 1:1 in the hours the
    bound is binding, so the pre-registered effect size is expressed against
    the zone's own in-window demand.
    """
    out: dict[str, dict] = {}
    for year in YEARS:
        sysdf = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
        sysdf = sysdf[(sysdf["pass"] == "P1") & (sysdf["zone"] == "Long_Island")]
        sysdf = sysdf.sort_values("hour")
        hod = sysdf["hour"].to_numpy(int) % 24
        inw = np.isin(hod, WINDOW_HOURS)
        dem = sysdf["demand"].to_numpy(float)
        pr = sysdf["price"].to_numpy(float)
        out[str(year)] = {
            "demand_in_window_p50_mw": float(np.percentile(dem[inw], 50)),
            "demand_in_window_p95_mw": float(np.percentile(dem[inw], 95)),
            "demand_in_window_max_mw": float(dem[inw].max()),
            "price_in_window_p50": float(np.percentile(pr[inw], 50)),
            "price_in_window_p95": float(np.percentile(pr[inw], 95)),
            "price_in_window_mean": float(pr[inw].mean()),
            "hours_price_gt_300_in_window": int((pr[inw] > 300.0).sum()),
            "relief_615mw_as_share_of_p50_demand": float(
                615.0 / np.percentile(dem[inw], 50)
            ),
        }
    return out


def main() -> int:
    """Assemble and write the nyiso-130 Phase-0 identification record."""
    cache_dir = Path(
        "/tmp/claude-0/-home-user-market-simulator/"
        "7952f3d9-7189-5c52-8b7b-e1ccb8212379/scratchpad"
    )
    record = {
        "session": "nyiso-130",
        "phase": "0 (identification, no solve)",
        "keeper_bundle": str(KEEPER_BUNDLE.relative_to(REPO_ROOT)),
        "published_zone_k_tsl": extract_zone_k_tables(cache_dir),
        "keeper_link_occupancy": link_occupancy(KEEPER_BUNDLE),
        "keeper_tail_census": tail_census(KEEPER_BUNDLE),
        "keeper_zone_k_in_window": in_window_zone_k_headroom(KEEPER_BUNDLE),
    }
    dest = REPO_ROOT / "results" / "calibration" / "_nyiso130_li_tsl_identification.json"
    dest.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps(record, indent=2, sort_keys=True))
    print(f"\nwrote {dest.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
