"""miso-132(b) §2 — PRE-CHECK for the CC committed-band measured re-grounding.

Pre-registration
``results/calibration/PREREG-miso132b-cc-committed-band-regrounding-2026-08-05.md``,
pushed BEFORE this probe ran. Everything reported here is DESCRIPTIVE except the
single INERTNESS bar ``P-0`` (combined committed capacity >= 200 MW in at least one
year) — a worth-the-compute bar, never a lever screen: the swap's admissibility is
settled by rule 14 ``[R-ACCURATE]`` alone.

NO LP IS SOLVED. The dispatch fleet is assembled TWICE at HEAD under the keeper's
own committed config — once as registered (``CC_REGULAR`` committed 1.20 /
``CC_INTERMEDIATE`` 0.92) and once with both bands at the measured
``avg_committed_p50`` 1.005 — and each cohort's committed tranches are priced at the
ISO's published gas-offer anchor, then compared with the keeper's OWN solved July
night prices.

Anchor convention: prices are evaluated at
``GAS_OFFER_MARGIN_ANCHOR_BY_ISO['MISO']``. That is the identification point at which
``apply_gas_offer_margin`` reduces EXACTLY to the registered band multiplier, so
``heat_rate x anchor + vom`` is the armed margin path's own offer there — no
approximation at the anchor, and the disclosed caveat is only that a hour whose
delivered gas differs from the anchor moves the marked-up band (pre-swap
``CC_REGULAR`` only) proportionally less than the multiplier form would.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only; the probe hard-errors on any other year.

Writes ``results/calibration/_miso132b_cc_committed_precheck.json``.
"""

from __future__ import annotations

import copy
import dataclasses
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from market_sim.config.constants import (  # noqa: E402
    GAS_OFFER_MARGIN_ANCHOR_BY_ISO,
)
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    build_base_fleet,
    build_dispatch_fleet,
    fleet_to_bins,
    load_fleet_from_csv,
)

BUNDLE = REPO / "results/calibration/miso127_onlinepmin_B"
OUT = REPO / "results/calibration/_miso132b_cc_committed_precheck.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760

#: The measurand (data/raw/reference/miso_campd_marginal_hr_summary.csv,
#: CC_REGULAR avg_committed_p50, n=103 units, cap-weighted, 2023-2025 pooled).
MEASURED_COMMITTED = 1.005
REGROUND_CLASSES = ("CC_REGULAR", "CC_INTERMEDIATE")

#: Pre-registered inertness bar (PREREG §2 P-0).
P0_MIN_COMMITTED_MW = 200.0

MONTH_LEN = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
             7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
MONTH_OF_HOUR = np.concatenate(
    [np.full(MONTH_LEN[m] * 24, m) for m in range(1, 13)]
)
HOD = np.tile(np.arange(24), 365)
JULY_NIGHT = (MONTH_OF_HOUR == 7) & (HOD <= 5)


def _guard(year: int) -> None:
    if year not in YEARS:
        raise ValueError(
            f"rule 22 [R-HOLDOUT]: MISO holds no calibration-complete marker; "
            f"year {year} must not be read"
        )


def _keeper_config():
    from market_sim.config.scenarios import ScenarioConfig

    raw = json.loads((BUNDLE / "run_config.json").read_text())
    names = {f.name for f in dataclasses.fields(ScenarioConfig)}
    return ScenarioConfig(
        **{k: v for k, v in raw["scenario_config"].items() if k in names}
    )


def _regrounded_config(cfg):
    """The keeper config with both CC committed bands at the measured value."""
    curve = copy.deepcopy(cfg.offer_curve_by_group)
    for cls in REGROUND_CLASSES:
        if cls not in curve:
            raise ValueError(f"{cls} absent from the keeper's offer_curve_by_group")
        curve[cls]["committed"] = MEASURED_COMMITTED
    return dataclasses.replace(cfg, offer_curve_by_group=curve)


def _committed_tranches(year: int, cfg) -> dict[str, dict]:
    """Per plant_group: committed-tranche capacity and cap-weighted heat rate."""
    _guard(year)
    iso_config = get_iso_config("MISO")
    zone_names = [z.name for z in iso_config.zones]
    raw = load_fleet_from_csv(
        "MISO", iso_config, year=year,
        measured_ct_heat_rates=cfg.measured_ct_heat_rates,
        measured_chp_heat_rates=cfg.measured_chp_heat_rates,
        cc_steam_part_capacity=cfg.cc_steam_part_capacity,
    )
    bins = fleet_to_bins(raw, "MISO", cfg)
    base = build_base_fleet(
        bins, "MISO", iso_config, zone_names, cfg, [], [], year, None,
        vintage_year=year, legacy_n_bins=0,
    )
    generators, _ff, _a, _b = build_dispatch_fleet(
        base, bins, [], "MISO", year, zone_names, cfg
    )
    out: dict[str, dict] = {}
    for g in generators:
        uid = str(g.unit_id)
        m = re.search(r"_p(\d+)_([a-z0-9_]+)$", uid)
        if not m or not m.group(2).startswith("committed"):
            continue
        grp = str(getattr(g, "plant_group", "") or "")
        cap = float(g.pmax_mw)
        rec = out.setdefault(grp, {"cap_mw": 0.0, "hr_cap_wtd": 0.0,
                                   "vom_cap_wtd": 0.0, "n": 0})
        rec["cap_mw"] += cap
        rec["hr_cap_wtd"] += cap * float(g.heat_rate)
        rec["vom_cap_wtd"] += cap * float(
            getattr(g, "vom_cost", getattr(g, "vom", 0.0)) or 0.0
        )
        rec["n"] += 1
    for rec in out.values():
        if rec["cap_mw"] > 0:
            rec["hr_cap_wtd"] /= rec["cap_mw"]
            rec["vom_cap_wtd"] /= rec["cap_mw"]
    return out


def _july_night_prices(year: int) -> dict[str, float]:
    """The keeper's own demand-weighted July-night price percentiles."""
    _guard(year)
    df = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    # Zone-mean hourly price (the frame miso-130 §3 used for the night floor).
    p = df.groupby("hour")["price"].mean().sort_index().to_numpy()[:HOURS]
    night = p[JULY_NIGHT]
    return {
        "july_night_p10": float(np.percentile(night, 10)),
        "july_night_p50": float(np.percentile(night, 50)),
        "july_night_mean": float(night.mean()),
    }


def main() -> None:
    cfg = _keeper_config()
    cfg_b = _regrounded_config(cfg)
    anchor = float(GAS_OFFER_MARGIN_ANCHOR_BY_ISO["MISO"])

    rec: dict = {
        "prereg": (
            "results/calibration/"
            "PREREG-miso132b-cc-committed-band-regrounding-2026-08-05.md"
        ),
        "keeper": "2026-08-04-miso-127-onlinepmin",
        "measured_committed": MEASURED_COMMITTED,
        "measurand_source": (
            "data/raw/reference/miso_campd_marginal_hr_summary.csv "
            "CC_REGULAR avg_committed_p50 (n=103, cap-weighted, 2023-2025)"
        ),
        "registered_before": {
            cls: float(cfg.offer_curve_by_group[cls]["committed"])
            for cls in REGROUND_CLASSES
        },
        "gas_offer_anchor_usd_per_mmbtu": anchor,
        "P0_min_committed_mw": P0_MIN_COMMITTED_MW,
        "years": {},
    }

    for year in YEARS:
        before = _committed_tranches(year, cfg)
        after = _committed_tranches(year, cfg_b)
        prices = _july_night_prices(year)
        per_class: dict[str, dict] = {}
        cap_total = 0.0
        for cls in REGROUND_CLASSES:
            b = before.get(cls)
            a = after.get(cls)
            if b is None or b["cap_mw"] <= 0:
                per_class[cls] = {"cap_mw": 0.0, "note": "no committed tranches"}
                continue
            mc_b = b["hr_cap_wtd"] * anchor + b["vom_cap_wtd"]
            mc_a = a["hr_cap_wtd"] * anchor + a["vom_cap_wtd"]
            cap_total += b["cap_mw"]
            per_class[cls] = {
                "cap_mw": b["cap_mw"],
                "n_tranches": b["n"],
                "hr_before": b["hr_cap_wtd"],
                "hr_after": a["hr_cap_wtd"],
                "offer_before_usd_mwh": mc_b,
                "offer_after_usd_mwh": mc_a,
                "d_offer_usd_mwh": mc_a - mc_b,
                "vs_july_night_p50_before": mc_b - prices["july_night_p50"],
                "vs_july_night_p50_after": mc_a - prices["july_night_p50"],
            }
        # Capacity-weighted net direction of the swap on the CC committed block.
        num = sum(
            v["cap_mw"] * v["d_offer_usd_mwh"]
            for v in per_class.values()
            if "d_offer_usd_mwh" in v
        )
        rec["years"][str(year)] = {
            "july_night_prices": prices,
            "by_class": per_class,
            "combined_committed_cap_mw": cap_total,
            "cap_weighted_d_offer_usd_mwh": (num / cap_total) if cap_total else 0.0,
            "net_direction": (
                "DEARER" if num > 0 else ("CHEAPER" if num < 0 else "NEUTRAL")
            ),
        }

    rec["P0_inertness_pass"] = bool(
        any(
            rec["years"][str(y)]["combined_committed_cap_mw"] >= P0_MIN_COMMITTED_MW
            for y in YEARS
        )
    )
    OUT.write_text(json.dumps(rec, indent=1))
    print(json.dumps({"P0_inertness_pass": rec["P0_inertness_pass"]}, indent=1))
    for y in YEARS:
        print(y, json.dumps(rec["years"][str(y)], indent=1))


if __name__ == "__main__":
    main()
