"""Derive the ERCOT measured COMMITMENT-LOADING state weight for the cleared-share wall.

The ERCOT-73 commitment-STATE artifact
(``ScenarioConfig.ercot_offer_surface_cleared_share_state``). One number per
gas class per hour::

    w_c(t) = clip( (online_cap_c(t) - gross_c(t))
                   / (online_cap_c(t) - cleared_c(t)), 0, 1 )

— the measured fraction of the class's ABOVE-DA-POSITION online capability
that the real-time commitment regime left UNLOADED:

* ``online_cap_c(t)``  CAMPD CEMS on-line (gross > 1 MW) unit capacity
  envelope per model class — the measured commitment envelope
  (``derive_ercot_rtolcap_forward._class_hourly``, the ERCOT-58/68 measured
  basis: physical quantities, never prices, never the LP's own dispatch).
* ``gross_c(t)``       the same units' CEMS gross output (the loading point).
* ``cleared_c(t)``     the class's DAM energy award (60-Day DAM disclosure,
  config-collapsed site-hours — the ERCOT-72 cleared-share artifact's basis),
  rebased onto the CEMS-capacity axis via the measured live-HSL share.

Why this quantity: ERCOT has no DAM must-offer, and ERCOT-72 measured the
participation cliff (8.6 GW of CC live HSL carried no DA offer on the May-2024
shoulders) and proved the composition lever — but the static wall was REJECTED
on its tight-regime arm: reality RUC/self-commits the un-offered capacity
online NEAR COST in tight regimes (Aug-2024 h14-19: RT CC 23.8 GW vs 18.0 DA-
offered). The ERCOT-73 scouting measurement (2026-07-16 calibration-log entry)
adjudicated the candidate state series:

* online-share and online-minus-cleared (RUC/self-commit increment): REFUTED
  as discriminators — the un-offered capacity is largely ONLINE in BOTH
  regimes (May-24 target 0.269 vs Jan-24 damage 0.269 increment).
* published system RTOLCAP: REFUTED — dominated by non-gas headroom (May-24
  target 11.4 GW vs Jan-24 damage 16.3 GW).
* the class's unloaded online headroom (this artifact): separates every
  ERCOT-72 damage window from every target window AT HOUR GRAIN — Aug-23
  0.02 / Sep-23 0.09 / Jun-23 0.21 / Aug-24 0.16 and Jan-24 tight hours
  (net-load >= p90) 0.25, vs May-24 shoulders 0.55 / Apr-24 0.79 /
  Nov-24 0.68 — with strong persistence (lag-1 autocorr 0.98) the static
  net-load bins cannot carry (bin-vs-state corr 0.75).

Regime meaning: w ~ 1 -> the belt/wall IS the marginal supply (moderate
regime, the DA participation cliff governs); w -> 0 -> the class runs at its
committed envelope and the same capacity is inframarginal near cost
(RUC/self-commitment regime, the wall must stand down).

Provenance / admissibility (CLAUDE.md rules 13/14/26): every term is a
measured physical/market quantity (CEMS unit operation — the same source
family as the campd-unit-outages overlay; DAM awards — ex-ante market
positions); the weight enters formulaically with zero fitted scalars and
never pins a MW (it scopes WHICH REGIME prices the un-offered capacity,
composing multiplicatively with the frozen cleared-share wall). Backcast
years read the year's own hourly series (a measured state-event overlay,
the G4 mode-aware seam — exactly the outage-overlay pattern); a year absent
from the artifact (forecast, holdout) falls back to the pooled CLIMATOLOGY
below, which regenerates from the target year's own net-load percentile and
hour-of-day and responds to changed conditions (the rule-13 forward test).

Climatology fallback: pooled mean w per (net-load-percentile bin x 4-hour
block), the cleared-share artifact's own bin edges x the ORDC's six daily
blocks — both existing structural partitions, nothing tuned.

FROZEN AGAINST RESIDUALS (rule 23): re-derive only when the CAMPD extracts or
the DAM disclosure source files update; never because a residual moved.
Re-derivation commits must cite the data change.

Usage::

    python scripts/derive_ercot_commitment_loading_state.py \
        [--years 2023 2024 2025] \
        [--out data/raw/_validation-source/ercot_commitment_loading_state.json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
import sys  # noqa: E402

sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from derive_ercot_dam_cleared_share import (  # noqa: E402
    NETLOAD_PCT_EDGES,
    _collapse_and_segment,
    _gas_day_series,
    _load_year,
    _netload_pct,
)
from derive_ercot_rtolcap_forward import _class_hourly  # noqa: E402

HOURS = 8760
DEFAULT_OUT = (
    REPO / "data" / "raw" / "_validation-source" / "ercot_commitment_loading_state.json"
)

#: Model class -> artifact class key (the cleared-share wall's own scope).
CLASS_OF_MODEL = {"CC_REGULAR": "CC", "CT_PEAKER": "CT"}

#: Hour-of-day blocks for the climatology: the ORDC LOLP's six 4-hour blocks
#: (an existing ERCOT market-design partition, results/scarcity.py) — not a
#: tuned quantity.
HOUR_BLOCKS = 6
BLOCK_HOURS = 4


def derive_year(year: int, gas_day) -> dict[str, np.ndarray]:
    """Return ``{cls: w (8760,)}`` for one delivery year."""
    df = _load_year(year)
    site_hours, _segments = _collapse_and_segment(df, gas_day)
    _res, _off, class_cap, online_cap, online_gross = _class_hourly(year)
    out: dict[str, np.ndarray] = {}
    for mcls, cls in CLASS_OF_MODEL.items():
        sh = site_hours[site_hours["cls"] == cls]
        g = sh.groupby("hoy")[["live", "cleared"]].sum()
        live = g["live"].reindex(range(HOURS)).to_numpy(float)
        cleared = g["cleared"].reindex(range(HOURS)).to_numpy(float)
        on = np.asarray(online_cap[mcls], dtype=float)[:HOURS]
        gross = np.asarray(online_gross[mcls], dtype=float)[:HOURS]
        cap = float(class_cap[mcls])
        # DAM award onto the CEMS-capacity axis: award share of live HSL,
        # applied to min(live, cap) so disclosure/CEMS coverage mismatches
        # (the non-CAMPD plants) cannot push the DA position past the envelope.
        clr_share = np.where(live > 0, cleared / np.where(live > 0, live, 1.0), 0.0)
        clr_cap = clr_share * np.minimum(np.nan_to_num(live), cap)
        num = on - gross
        den = on - clr_cap
        w = np.where(
            num <= 0, 0.0, np.where(den <= num, 1.0, num / np.where(den > 0, den, 1.0))
        )
        out[cls] = np.clip(np.nan_to_num(w, nan=1.0), 0.0, 1.0)
    return out


def climatology(per_year: dict[int, dict[str, np.ndarray]]) -> dict:
    """Pooled mean w per (net-load-percentile bin x 4-hour block), per class.

    The forward/holdout fallback: a target year's bins regenerate from its own
    net load, its blocks from the clock — the rule-13 forward story.
    """
    edges = np.asarray(NETLOAD_PCT_EDGES)
    n_bins = len(edges) + 1
    hod_block = (np.arange(HOURS) % 24) // BLOCK_HOURS  # (HOURS,)
    out: dict[str, list[list[float]]] = {}
    classes = sorted({c for d in per_year.values() for c in d})
    for cls in classes:
        acc = np.zeros((n_bins, HOUR_BLOCKS))
        cnt = np.zeros((n_bins, HOUR_BLOCKS))
        for year, tables in per_year.items():
            if cls not in tables:
                continue
            pct = _netload_pct(year)
            hour_bin = np.searchsorted(edges, pct, side="right")
            w = tables[cls]
            np.add.at(acc, (hour_bin, hod_block), w)
            np.add.at(cnt, (hour_bin, hod_block), 1.0)
        table = np.where(cnt > 0, acc / np.where(cnt > 0, cnt, 1.0), np.nan)
        out[cls] = [[round(float(v), 3) for v in row] for row in table]
    return out


def main() -> None:
    """Derive and write the commitment-loading state JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    gas_day = _gas_day_series()
    per_year: dict[int, dict[str, np.ndarray]] = {}
    for y in args.years:
        per_year[y] = derive_year(y, gas_day)
        for cls, w in per_year[y].items():
            print(
                f"{y} {cls}: mean w = {w.mean():.3f}; "
                f"share of hours w<0.25 = {(w < 0.25).mean():.3f}, "
                f"w>0.75 = {(w > 0.75).mean():.3f}"
            )

    clim = climatology(per_year)
    result: dict = {
        "_provenance": {
            "source": (
                "CAMPD CEMS hourly unit operation (online envelope + gross, "
                "derive_ercot_rtolcap_forward._class_hourly) x ERCOT 60-Day "
                "DAM Disclosure Gen Resource Data energy awards, delivery "
                "years " + "-".join(str(y) for y in args.years)
            ),
            "method": (
                "w = clip((online_cap - gross) / (online_cap - cleared), 0, 1) "
                "per class-hour: the measured unloaded fraction of the class's "
                "above-DA-position online capability (moderate regime -> 1, "
                "RUC/self-commitment envelope-loading regime -> 0)"
            ),
            "driver": (
                "measured commitment-loading state (CEMS operation, the "
                "campd-unit-outages source family; DAM awards). Forward/"
                "holdout years fall back to the pooled climatology below, "
                "which regenerates from the target year's own net-load "
                "percentile x hour-of-day block"
            ),
            "netload_pct_edges": list(NETLOAD_PCT_EDGES),
            "hour_block_hours": BLOCK_HOURS,
            "iso": "ERCOT",
            "classes": {"CC": ["CC_REGULAR"], "CT": ["CT_PEAKER"]},
            "frozen": (
                "rule 23 — re-derive only on a CAMPD / DAM-disclosure "
                "source-data update, never because a residual moved"
            ),
        },
        "climatology": clim,
    }
    classes = sorted({c for d in per_year.values() for c in d})
    for cls in classes:
        result[cls] = {
            "years": {
                str(y): [round(float(v), 3) for v in per_year[y][cls]]
                for y in args.years
                if cls in per_year[y]
            }
        }

    args.out.write_text(json.dumps(result))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
