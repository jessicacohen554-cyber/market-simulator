"""neiso-81 Phase 0 — pre-arm screen for the ``measured_chp_heat_rates`` re-adjudication.

**No LP, no solve.** Everything here is measured from committed artifacts and one
fleet-loader rebuild, and every number it prints is fixed into the
pre-registration BEFORE either arm is launched.

It answers the four questions the prereg's numbered properties rest on:

* **W — WIRING (grain 1 of the miso-126(a) two-grain firing proof).** Rebuild the
  runner's own fleet chain (``load_or_synthesize_bins`` -> ``build_base_fleet``)
  at the DESIGNATED KEEPER's ScenarioConfig — never the loader defaults, which
  ship ``measured_chp_heat_rates=False`` (the miso-116 measurement trap) — with
  the flag off and on, and diff the heat rates the LP would actually charge.
  A zero diff is verdict ``I`` with no solve spent (the ERCOT-146 outcome);
  grain 2 is the post-arm per-class ENERGY delta and lives in the A/B scorer.

* **R — RESOLVABILITY.** C1's per-class volume band is
  ``min(2 % of ISO load, 8 TWh)``. Compare the repriced class's ENTIRE annual
  grid-delivered actual against that band. A class whose whole annual output is
  smaller than its own tolerance cannot be discriminated by its C1 row in either
  direction, which decides whether a degraded CC_CHP number is a *resolvable*
  fit regression or an unresolvable one.

* **B — BOUNDARY.** Is the CC_CHP / CC_REGULAR split keyed on the SAME plant set
  on both sides of the comparison? ``classFull[k] = e923_bench[k] - btm[k]``
  buckets EIA-923 per-plant net generation through the same
  ``plant_taxonomy.classify_plant`` registry the model's fleet uses, so this
  checks the shared-boundary claim empirically instead of asserting it, and
  reports the combined CC aggregate that the substitution hypothesis is about.

* **S — SUBSTITUTION HEADROOM.** Where does the repriced CC_CHP population land
  in the combined-cycle merit order before and after the swap, and how much
  CC_REGULAR capacity sits inside the band it moves across? This is the ex-ante
  structural basis for predicting near-1:1 displacement; the miso-121 discipline
  applies — this is *headroom*, an upper bound, never a magnitude.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_neiso81_chp_phase0.py \
        --json-out results/calibration/_neiso81_chp_phase0.json
"""

from __future__ import annotations

import argparse
import dataclasses
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fleet import build_base_fleet, load_or_synthesize_bins  # noqa: E402

ISO = "NEISO"
#: The DESIGNATED keeper this session replays. Its run_config is the model side
#: of every probe (miso-116: never the loader defaults).
KEEPER = REPO / "results/calibration/neiso_c156_meter_screen_B"
ARTIFACT = REPO / "data/raw/_processed-legacy/chp_power_only_heat_rates_NEISO.csv"
BENCH = REPO / "frontend/data/backcast/bench" / ISO
YEARS = (2023, 2024, 2025)
FLAG = "measured_chp_heat_rates"
REPRICED = ("CC_CHP", "CT_CHP")
CC_PAIR = ("CC_CHP", "CC_REGULAR")

#: scripts/calibration_verdict.py — the C1 per-class volume tolerance.
FUELMIX_VOL_LOAD_FRAC = 0.02
FUELMIX_VOL_CAP_TWH = 8.0


# --------------------------------------------------------------------------- #
# keeper config
# --------------------------------------------------------------------------- #
def keeper_config(**overrides) -> ScenarioConfig:
    """Rebuild the designated keeper's ScenarioConfig with ``overrides`` on top.

    Only fields the shipped ScenarioConfig still declares are carried, so a key
    that has since been renamed away cannot break the probe.
    """
    snap = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    valid = {f.name for f in dataclasses.fields(ScenarioConfig)}
    kw = {k: v for k, v in snap.items() if k in valid}
    kw.update(overrides)
    return ScenarioConfig(**kw)


def build_fleet_table(year: int, **overrides) -> pd.DataFrame:
    """Build the base fleet through the runner's own chain; return a unit table."""
    cfg = keeper_config(**overrides)
    iso_config = get_iso_config(ISO)
    zone_names = [z.name for z in iso_config.zones]
    bins = load_or_synthesize_bins(cfg, ISO, iso_config, [])
    fleet = build_base_fleet(
        bins, ISO, iso_config, zone_names, cfg, [], [], year, confirmed_exits=[]
    )
    return pd.DataFrame(
        [
            {
                "plant_code": int(g.plant_code or 0),
                "name": g.name,
                "plant_group": g.plant_group,
                "pmax_mw": float(g.pmax_mw),
                "heat_rate": float(g.heat_rate),
            }
            for g in fleet
        ]
    )


def _capwt(frame: pd.DataFrame, col: str = "heat_rate") -> float:
    w = frame["pmax_mw"].to_numpy(dtype=float)
    if w.sum() <= 0:
        return float("nan")
    return float(np.average(frame[col].to_numpy(dtype=float), weights=w))


# --------------------------------------------------------------------------- #
# W — wiring at the LP seam
# --------------------------------------------------------------------------- #
def screen_wiring(year: int) -> dict:
    off = build_fleet_table(year, **{FLAG: False})
    on = build_fleet_table(year, **{FLAG: True})
    key = ["plant_code", "name", "plant_group"]
    merged = off.merge(on, on=key, suffixes=("_off", "_on"), how="outer")
    moved = merged[
        ~np.isclose(
            merged["heat_rate_off"].fillna(-1.0),
            merged["heat_rate_on"].fillna(-1.0),
            rtol=0.0,
            atol=1e-9,
        )
    ]
    out = {
        "year": year,
        "generators_total": int(len(off)),
        "generators_moved": int(len(moved)),
        "mw_moved": round(float(moved["pmax_mw_on"].fillna(0.0).sum()), 4),
        "classes": {},
        "moved_rows": [],
    }
    for klass in (*REPRICED, "CC_REGULAR"):
        a = off[off["plant_group"] == klass]
        b = on[on["plant_group"] == klass]
        if a.empty and b.empty:
            continue
        hr_off, hr_on = _capwt(a), _capwt(b)
        out["classes"][klass] = {
            "n_units_off": int(len(a)),
            "cap_mw": round(float(b["pmax_mw"].sum()), 3),
            "capwt_hr_off": round(hr_off, 4),
            "capwt_hr_on": round(hr_on, 4),
            "pct_dearer": (
                round(100.0 * (hr_on / hr_off - 1.0), 4) if hr_off > 0 else None
            ),
        }
    for _, r in moved.sort_values("pmax_mw_on", ascending=False).iterrows():
        out["moved_rows"].append(
            {
                "plant_code": int(r["plant_code"]),
                "name": str(r["name"]),
                "plant_group": str(r["plant_group"]),
                "pmax_mw": round(float(r["pmax_mw_on"]), 3),
                "hr_off": round(float(r["heat_rate_off"]), 4),
                "hr_on": round(float(r["heat_rate_on"]), 4),
            }
        )
    return out


# --------------------------------------------------------------------------- #
# R / B — resolvability and the class boundary, from the committed bench
# --------------------------------------------------------------------------- #
def _bench(year: int) -> dict:
    return json.loads(gzip.open(BENCH / f"{year}.json.gz").read())["bench"]


def screen_resolvability() -> dict:
    rows = {}
    for year in YEARS:
        b = _bench(year)
        cf = {k: float(v) for k, v in (b.get("classFull") or {}).items()}
        # C1's own denominator: total load, from the bench's load series when it
        # carries one, else the summed grid-delivered class actual (the
        # calibration_verdict._total_load fallback).
        total_load = float(b.get("loadTwh") or 0.0) or sum(cf.values())
        band = min(FUELMIX_VOL_LOAD_FRAC * total_load, FUELMIX_VOL_CAP_TWH)
        cc_chp, cc_reg = cf.get("CC_CHP", 0.0), cf.get("CC_REGULAR", 0.0)
        rows[year] = {
            "total_load_twh_basis": round(total_load, 4),
            "c1_vol_band_twh": round(band, 4),
            "actual_CC_CHP_twh": round(cc_chp, 4),
            "actual_CT_CHP_twh": round(cf.get("CT_CHP", 0.0), 4),
            "actual_CC_REGULAR_twh": round(cc_reg, 4),
            "actual_CC_COMBINED_twh": round(cc_chp + cc_reg, 4),
            # The decisive ratio: a class whose ENTIRE annual actual is below
            # its own C1 band cannot be discriminated by that row either way.
            "CC_CHP_actual_over_band": round(cc_chp / band, 4) if band else None,
            "CC_CHP_resolvable": bool(band and cc_chp >= band),
            "CT_CHP_resolvable": bool(band and cf.get("CT_CHP", 0.0) >= band),
            "CC_CHP_share_of_combined_pct": (
                round(100.0 * cc_chp / (cc_chp + cc_reg), 3) if (cc_chp + cc_reg) else None
            ),
        }
    return rows


def screen_boundary(year: int) -> dict:
    """Are model and benchmark keyed on the SAME plant->class registry?

    ``classFull`` is built from the bundle's own ``eia923.parquet`` /
    ``btm.parquet``, both bucketed by ``plant_group``. This checks the model
    fleet's CC_CHP / CC_REGULAR plant sets are disjoint and that the CC_CHP
    members are exactly the EIA-860 CHP-flagged combined-cycle plants — i.e.
    that the split is one registry applied twice, not two independent
    attributions.
    """
    fleet = build_fleet_table(year)
    art = pd.read_csv(ARTIFACT)
    ok = art[art["flag"] == "ok"]
    out = {"year": year, "classes": {}}
    seen: dict[int, set[str]] = {}
    for klass in CC_PAIR:
        sub = fleet[fleet["plant_group"] == klass]
        plants = sorted({int(p) for p in sub["plant_code"] if p})
        out["classes"][klass] = {
            "n_units": int(len(sub)),
            "n_plants": len(plants),
            "cap_mw": round(float(sub["pmax_mw"].sum()), 3),
            "plants": plants,
        }
        for p in plants:
            seen.setdefault(p, set()).add(klass)
    out["plants_in_both_classes"] = sorted(p for p, k in seen.items() if len(k) > 1)
    art_cc = sorted({int(p) for p in ok[ok["plant_group"] == "CC_CHP"]["plant_code"]})
    model_cc = set(out["classes"].get("CC_CHP", {}).get("plants", []))
    out["artifact_CC_CHP_plants"] = art_cc
    out["artifact_CC_CHP_plants_absent_from_model_class"] = sorted(
        set(art_cc) - model_cc
    )
    return out


# --------------------------------------------------------------------------- #
# S — substitution headroom in the combined-cycle merit order
# --------------------------------------------------------------------------- #
def screen_substitution(year: int) -> dict:
    """CC_REGULAR capacity inside the heat-rate band CC_CHP moves across.

    UPPER BOUND ONLY (the miso-119 / miso-121 discipline): capacity sitting in
    the traversed band is what *could* absorb the displaced energy, never a
    prediction of how much does. Marginality, not headroom, is the predictive
    statistic and it is only observable post-solve.
    """
    off = build_fleet_table(year, **{FLAG: False})
    on = build_fleet_table(year, **{FLAG: True})
    chp_off = off[off["plant_group"] == "CC_CHP"]
    chp_on = on[on["plant_group"] == "CC_CHP"]
    reg = on[on["plant_group"] == "CC_REGULAR"]
    lo, hi = _capwt(chp_off), _capwt(chp_on)
    band = reg[(reg["heat_rate"] >= min(lo, hi)) & (reg["heat_rate"] <= max(lo, hi))]
    # The share of CC_REGULAR that is unambiguously CHEAPER than the repriced
    # CC_CHP population is the capacity that can displace it outright.
    cheaper = reg[reg["heat_rate"] < hi]
    return {
        "year": year,
        "CC_CHP_capwt_hr_off": round(lo, 4),
        "CC_CHP_capwt_hr_on": round(hi, 4),
        "CC_REGULAR_capwt_hr": round(_capwt(reg), 4),
        "CC_REGULAR_cap_mw": round(float(reg["pmax_mw"].sum()), 3),
        "CC_REGULAR_cap_mw_in_traversed_band": round(float(band["pmax_mw"].sum()), 3),
        "CC_REGULAR_cap_mw_cheaper_than_repriced_CHP": round(
            float(cheaper["pmax_mw"].sum()), 3
        ),
        "CC_REGULAR_cheaper_share_pct": (
            round(100.0 * cheaper["pmax_mw"].sum() / reg["pmax_mw"].sum(), 3)
            if reg["pmax_mw"].sum()
            else None
        ),
        "CC_CHP_cap_mw": round(float(chp_on["pmax_mw"].sum()), 3),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    report = {
        "session": "neiso-81",
        "iso": ISO,
        "keeper_bundle": str(KEEPER.relative_to(REPO)),
        "keeper_flag_state": json.loads((KEEPER / "run_config.json").read_text())[
            "scenario_config"
        ][FLAG],
        "artifact": str(ARTIFACT.relative_to(REPO)),
        "wiring": screen_wiring(2023),
        "resolvability": screen_resolvability(),
        "boundary": screen_boundary(2023),
        "substitution": screen_substitution(2023),
    }

    w = report["wiring"]
    print(f"=== W wiring (keeper config, {FLAG} off -> on, {w['year']}) ===")
    print(f"  keeper records {FLAG} = {report['keeper_flag_state']}")
    print(f"  generators moved {w['generators_moved']} / {w['generators_total']}"
          f"  ({w['mw_moved']} MW)")
    for k, v in w["classes"].items():
        print(f"    {k:<11} cap {v['cap_mw']:>9.1f} MW  HR "
              f"{v['capwt_hr_off']:.4f} -> {v['capwt_hr_on']:.4f}"
              f"  ({v['pct_dearer']:+.2f} %)")

    print("\n=== R resolvability (C1 volume band vs the class's whole actual) ===")
    for y, v in report["resolvability"].items():
        print(f"  {y}: band +/-{v['c1_vol_band_twh']:.3f} TWh | CC_CHP actual "
              f"{v['actual_CC_CHP_twh']:.3f} ({v['CC_CHP_actual_over_band']:.3f}x band)"
              f" | resolvable={v['CC_CHP_resolvable']}"
              f" | CC combined {v['actual_CC_COMBINED_twh']:.3f}")

    b = report["boundary"]
    print("\n=== B boundary (one registry applied twice?) ===")
    for k, v in b["classes"].items():
        print(f"  {k:<11} {v['n_units']:>4} units / {v['n_plants']:>3} plants / "
              f"{v['cap_mw']:.1f} MW")
    print(f"  plants in BOTH classes: {b['plants_in_both_classes'] or 'none'}")
    print(f"  artifact CC_CHP plants absent from the model class: "
          f"{b['artifact_CC_CHP_plants_absent_from_model_class'] or 'none'}")

    s = report["substitution"]
    print("\n=== S substitution headroom (UPPER BOUND, never a magnitude) ===")
    print(f"  CC_CHP {s['CC_CHP_cap_mw']:.1f} MW, HR {s['CC_CHP_capwt_hr_off']:.4f}"
          f" -> {s['CC_CHP_capwt_hr_on']:.4f}")
    print(f"  CC_REGULAR {s['CC_REGULAR_cap_mw']:.1f} MW @ "
          f"{s['CC_REGULAR_capwt_hr']:.4f}; "
          f"{s['CC_REGULAR_cap_mw_cheaper_than_repriced_CHP']:.1f} MW "
          f"({s['CC_REGULAR_cheaper_share_pct']:.1f} %) cheaper than the repriced CHP; "
          f"{s['CC_REGULAR_cap_mw_in_traversed_band']:.1f} MW inside the traversed band")

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n")
        print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
