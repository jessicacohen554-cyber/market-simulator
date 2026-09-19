#!/usr/bin/env python3
"""nyiso-240 phase 0: is the C1 `CC_REGULAR` Feb/Nov over-run the MODEL or the RULER?

Zero LP. Every number in
``docs/FINDING-nyiso240-c1-margin-bench-attribution-2026-09-19.md`` regenerates from
committed artifacts (bench parts, run payloads, keeper hourlies) plus the immutable
``data/raw`` EIA-923 and NYISO fuel-mix extracts.

Five sections:

1. **The ISO's own meter.** Model total fossil vs NYISO's published hourly fuel mix
   (``Natural Gas + Dual Fuel + Other Fossil Fuels``), by month. This is the arbiter that
   decides whether the object is a fossil-level miss at all.
2. **R1 — EIA-923 missing months.** A month every EIA-923 row of a (plant, year) reports as
   NaN, while CAMPD meters generation in it. ``netgen_annual_mwh`` is EIA's own published
   annual and is the sum of the *reported* months, so the class benchmark is short by the
   whole missing block. Includes the cross-ISO census over every committed bench part.
3. **R2 — dual-fuel class attribution.** ``_classify_f923`` routes 100 % of DFO/RFO/JF/KER/
   WO/PC to the ``oil`` class; the model books those units wholly in their own gas class.
4. **The margin.** Both repairs scored through ``calibration_verdict`` for NYISO.
5. **The cross-ISO verdict census.** Every ISO's designated keeper re-scored against a
   repaired copy of its own bench — the measurement nyiso-239 §7 said needed a cross-lane job.

Usage::

    python3 scripts/probes/nyiso240_c1_margin_bench_phase0.py [--json-out PATH]
"""

from __future__ import annotations

import argparse
import base64
import copy
import gzip
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

import calibration_verdict as cv  # noqa: E402
from market_sim.data.eia923 import load_monthly_generation  # noqa: E402

BENCH = REPO / "frontend" / "data" / "backcast" / "bench"
RUNS = REPO / "frontend" / "data" / "backcast" / "runs"
KEEPERS = REPO / "frontend" / "data" / "backcast" / "keepers"
KEEPER = "2026-09-17-nyiso239-bench-oil-basis"
KEEPER_BUNDLE = REPO / "results" / "calibration" / "nyiso239_bench_span"

# EIA-923 liquid-petroleum fuel codes. `_classify_f923` routes every one to `oil`.
OIL_FUELS = ("DFO", "RFO", "JF", "KER", "WO", "PC")
# NYISO publishes no `oil` category; an oil-capable unit files under `Dual Fuel`.
NYISO_FOSSIL_CATEGORIES = ("Natural Gas", "Dual Fuel", "Other Fossil Fuels")
# The classes `_backfill_eia923_with_campd` already considers eligible (non-CHP grid).
BACKFILL_ELIGIBLE = frozenset(
    {"CC_REGULAR", "CT_PEAKER", "ST_GAS", "COAL_BIT", "COAL_PRB", "COAL"}
)
FOSSIL_KLASSES = (
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
    "OTHER_FOSSIL",
    "COAL_BIT",
    "COAL_PRB",
)
ISO_TO_BA = {
    "CAISO": "CISO",
    "ERCOT": "ERCO",
    "MISO": "MISO",
    "NEISO": "ISNE",
    "NYISO": "NYIS",
    "PJM": "PJM",
    "SOCO": "SOCO",
    "SPP": "SWPP",
    "NWPP": "NWPP",
}


def _bench(iso: str, year: int) -> dict | None:
    """Return one committed bench part's ``bench`` block, or ``None``."""
    p = BENCH / iso / f"{year}.json.gz"
    return json.load(gzip.open(p))["bench"] if p.exists() else None


def _payload(run_id: str) -> dict:
    """Decode a committed run payload (``window.BC.runGz[...] = "<b64 gzip>"``)."""
    m = re.search(r'="([A-Za-z0-9+/=]+)";?\s*$', (RUNS / f"{run_id}.js").read_text().strip())
    if m is None:  # pragma: no cover - wire format change
        raise SystemExit(f"cannot decode payload for {run_id}")
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def _keepers() -> dict[str, str]:
    """Return ``{iso: designated keeper run id}`` from the per-ISO keeper shards."""
    out: dict[str, str] = {}
    for f in sorted(KEEPERS.glob("*.json")):
        d = json.load(open(f))
        if d.get("iso") and d.get("keeper"):
            out[d["iso"]] = d["keeper"]
    return out


def _nan_month_mask(gen: pd.DataFrame) -> pd.DataFrame:
    """``(year, plant_id) -> [bool]*12``: month *m* is NaN in EVERY row of that plant-year.

    A single reported row is enough to make the month present, so this is the conservative
    reading of "EIA-923 has no data for this plant in this month".
    """
    mon = [c for c in gen.columns if c.startswith("netgen_") and c != "netgen_annual_mwh"]
    flags = gen[["year", "plant_id"]].copy()
    vals = gen[mon].astype(float)
    for i, c in enumerate(mon):
        flags[i] = vals[c].isna()
    return flags.groupby(["year", "plant_id"])[list(range(12))].all()


# --------------------------------------------------------------------------
# Section 1 — the ISO's own meter
# --------------------------------------------------------------------------
def section1_iso_meter(year: int = 2022) -> dict:
    """Model total fossil vs NYISO's published hourly fuel mix, by month."""
    print(f"\n=== 1. NYISO's OWN published hourly fuel mix vs the model's TOTAL FOSSIL ({year})")
    src = REPO / "data/raw/NYISO/fuel-mix" / f"NYISO_fuelmix_hourly_{year}.csv.gz"
    d = pd.read_csv(src)
    d["utc"] = pd.to_datetime(d["interval_start_utc"], utc=True)
    piv = d.pivot_table(
        index="utc", columns="fuel_category", values="gen_mw", aggfunc="sum"
    ).fillna(0.0)
    months = piv.index.tz_convert("America/New_York").month
    published = sum(
        (piv[c] for c in NYISO_FOSSIL_CATEGORIES if c in piv.columns),
        pd.Series(0.0, index=piv.index),
    )
    act = np.array([published[months == m].sum() / 1e3 for m in range(1, 13)])

    hourly = pd.read_parquet(KEEPER_BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    hourly = hourly[hourly["pass"] == "P1"]
    tot = (
        hourly[hourly["klass"].isin(FOSSIL_KLASSES)]
        .groupby("hour")["mw"]
        .sum()
        .reindex(range(8760), fill_value=0.0)
        .to_numpy()
    )
    mo = pd.date_range(f"{year}-01-01", periods=8760, freq="h").month
    mod = np.array([tot[mo == m].sum() / 1e3 for m in range(1, 13)])

    print(f"{'mo':>3} {'model':>11} {'published':>11} {'delta':>9} {'pct':>8}")
    for i in range(12):
        print(f"{i + 1:>3} {mod[i]:11.1f} {act[i]:11.1f} {mod[i] - act[i]:+9.1f} "
              f"{100 * (mod[i] - act[i]) / act[i]:+7.1f}%")
    print(f"{'SUM':>3} {mod.sum():11.1f} {act.sum():11.1f} {mod.sum() - act.sum():+9.1f} "
          f"{100 * (mod.sum() - act.sum()) / act.sum():+7.1f}%")
    print("  February +2.0 % and November +0.8 % are two of the model's MOST ACCURATE months.")
    print("  The real outliers are January -7.6 % and December -10.6 %, both UNDER-runs.")
    return {
        "model_gwh": [round(float(x), 1) for x in mod],
        "published_gwh": [round(float(x), 1) for x in act],
        "pct": [round(float(100 * (mod[i] - act[i]) / act[i]), 2) for i in range(12)],
    }


# --------------------------------------------------------------------------
# Section 2 — R1, EIA-923 missing months
# --------------------------------------------------------------------------
def r1_gaps(iso: str, year: int, bench: dict, nanmask: pd.DataFrame) -> dict[str, float]:
    """Implied ``classFull`` shortfall (TWh) per class from EIA-923 missing months.

    A plant's missing-month CAMPD net is scaled by that plant's OWN measured
    ``sum(e_mon) / sum(c_mon)`` over the months EIA-923 DOES report — zero free parameters,
    and the same "scale CAMPD's shape to a measured target" arithmetic ``_book`` performs.
    CEMS meters only the stacked units of a combined cycle, so the raw CAMPD number is known
    to be short (Bethlehem: 0.677, i.e. a 1.476 ratio).
    """
    out: dict[str, float] = {}
    for pid, rec in bench["plants"].items():
        group = rec.get("group")
        if group not in BACKFILL_ELIGIBLE:
            continue
        plant = int(str(pid).split(":")[0])
        try:
            mask = nanmask.loc[(year, plant)].to_numpy()
        except KeyError:
            continue
        missing = [i for i in range(12) if mask[i]]
        if not missing:
            continue
        c_mon = rec.get("c_mon") or [0.0] * 12
        e_mon = rec.get("e_mon") or [0.0] * 12
        gap = sum(c_mon[i] or 0.0 for i in missing)
        if gap <= 1.0:  # CAMPD says the plant was genuinely idle — nothing to repair
            continue
        reported = [i for i in range(12) if not mask[i]]
        c_rep = sum(c_mon[i] or 0.0 for i in reported)
        e_rep = sum(e_mon[i] or 0.0 for i in reported)
        ratio = (e_rep / c_rep) if c_rep > 0 else 1.0
        out[group] = out.get(group, 0.0) + gap * ratio / 1e3
    return out


def section2_r1(gen: pd.DataFrame, nanmask: pd.DataFrame) -> dict:
    """The Bethlehem instance, then the cross-ISO census."""
    print("\n=== 2a. R1 — the instance: Bethlehem Energy Center (2539), NYISO 2022")
    mon = [c for c in gen.columns if c.startswith("netgen_") and c != "netgen_annual_mwh"]
    d = gen[(gen.plant_id == 2539) & (gen.year == 2022)]
    for _, r in d.iterrows():
        m = r[mon].astype(float).to_numpy()
        print(f"  pm={r.prime_mover:<3} fuel={r.fuel_type:<4} annual={r.netgen_annual_mwh:>12,.0f} "
              f"sum(reported months)={np.nansum(m):>12,.0f} "
              f"NaN months={[i + 1 for i, v in enumerate(m) if np.isnan(v)]}")
    print("  EIA's OWN published annual equals the sum of the TEN reported months:")
    print("  February and November are absent from the annual benchmark, not merely from the shape.")
    b22 = _bench("NYISO", 2022)
    rec = b22["plants"]["2539"]
    print(f"  bench e_mon (EIA-923) GWh: {[round(x or 0, 1) for x in rec['e_mon']]}")
    print(f"  bench c_mon (CAMPD)   GWh: {[round(x or 0, 1) for x in rec['c_mon']]}")

    print("\n=== 2b. R1 — the cross-ISO census over every committed bench part")
    rows = []
    for part in sorted(BENCH.glob("*/*.json.gz")):
        iso, year = part.parent.name, int(part.stem.split(".")[0])
        gaps = r1_gaps(iso, year, json.load(gzip.open(part))["bench"], nanmask)
        for klass, twh in gaps.items():
            rows.append({"iso": iso, "year": year, "class": klass, "twh": round(twh, 4)})
    rows.sort(key=lambda r: -r["twh"])
    print(f"{'ISO':<7}{'yr':<6}{'class':<13}{'GWh':>9}")
    for r in rows[:16]:
        print(f"{r['iso']:<7}{r['year']:<6}{r['class']:<13}{r['twh'] * 1e3:9.1f}")
    print(f"  ... {len(rows)} (ISO, year, class) cells in total, across "
          f"{len({r['iso'] for r in rows})} BAs.")
    return {"census": rows}


# --------------------------------------------------------------------------
# Section 3 — R2, dual-fuel class attribution
# --------------------------------------------------------------------------
def r2_deltas(iso: str, year: int, bench: dict, gen: pd.DataFrame) -> dict[str, float]:
    """EIA-923 oil-fuel MWh (TWh) re-attributed to the burning plant's own bench class.

    A plant carrying several bench classes (Ravenswood: CC_REGULAR + ST_GAS) splits by its
    own measured EIA-923 class energy. A plant absent from the model fleet keeps its MWh in
    the `oil` class, which is the right place for it.
    """
    groups: dict[int, dict[str, float]] = {}
    for pid, rec in bench["plants"].items():
        plant = int(str(pid).split(":")[0])
        groups.setdefault(plant, {})[rec["group"]] = sum(
            x or 0.0 for x in (rec.get("e_mon") or [0.0] * 12)
        )
    d = gen[
        (gen.year == year)
        & (gen.ba_code == ISO_TO_BA.get(iso, iso))
        & (gen.fuel_type.isin(OIL_FUELS))
    ]
    out: dict[str, float] = {}
    for plant, g in d.groupby("plant_id"):
        mwh = float(g.netgen_annual_mwh.sum())
        if mwh <= 0:
            continue
        gs = groups.get(int(plant))
        if not gs:
            continue
        total = sum(gs.values()) or 1.0
        for klass, weight in gs.items():
            out[klass] = out.get(klass, 0.0) + mwh / 1e6 * (weight / total)
    return out


def section3_r2(gen: pd.DataFrame) -> dict:
    """The model books a dual-fuel CC wholly in its gas class; EIA-923 does not."""
    print("\n=== 3. R2 — the dual-fuel class boundary, verified at the UNIT layer")
    leg = REPO / "results/calibration/nyiso239_bench_2022/hourly/unit_hourly_2022.parquet"
    if leg.exists():
        u = pd.read_parquet(leg)
        u = u[u["pass"] == "P1"]
        by = u.groupby(["plant_code", "plant_group", "fuel"])["mw"].sum() / 1e3
        for plant in ("55375", "57664", "56196", "2500", "2516"):
            sel = by[by.index.get_level_values(0).astype(str) == plant]
            if len(sel):
                print(f"  plant {plant}: "
                      + ", ".join(f"{i[1] or '-'}/{i[2]} {v:.1f} GWh" for i, v in sel.items()))
        oil = u[u.fuel == "oil"]["mw"].sum() / 1e3
        print(f"  model `oil`-FUEL fleet, ALL plants, whole year: {oil:.1f} GWh "
              f"(bench classFull.oil = {_bench('NYISO', 2022)['classFull']['oil'] * 1e3:.1f} GWh)")
    else:
        print("  (unit layer not on disk — recover the nyiso-239 legs per .gitignore:2400)")

    print("\n  EIA-923 oil-fuel MWh by the plant's own bench class (GWh):")
    out = {}
    for year in (2022, 2023, 2024, 2025):
        b = _bench("NYISO", year)
        dd = r2_deltas("NYISO", year, b, gen)
        out[year] = {k: round(v * 1e3, 1) for k, v in dd.items()}
        print(f"   {year}: "
              + ", ".join(f"{k} +{v * 1e3:.1f}" for k, v in sorted(dd.items(), key=lambda x: -x[1]))
              + f"   | oil class {b['classFull']['oil'] * 1e3:.1f} -> "
                f"{b['classFull']['oil'] * 1e3 - sum(dd.values()) * 1e3:.1f}")
    return out


# --------------------------------------------------------------------------
# Sections 4 & 5 — the margin, and the cross-ISO verdict census
# --------------------------------------------------------------------------
def _repaired_bench_root(iso: str, use_r1: bool, use_r2: bool,
                         gen: pd.DataFrame, nanmask: pd.DataFrame, tmp: Path) -> Path:
    """Copy the committed bench tree and apply the requested repairs to ``iso``'s parts."""
    root = tmp / f"bench_{iso}_{int(use_r1)}{int(use_r2)}"
    if root.exists():
        shutil.rmtree(root)
    shutil.copytree(BENCH, root)
    for p in sorted((root / iso).glob("*.json.gz")):
        year = int(p.stem.split(".")[0])
        full = json.load(gzip.open(p))
        b = full["bench"]
        if use_r1:
            for klass, twh in r1_gaps(iso, year, b, nanmask).items():
                b["classFull"][klass] = b["classFull"].get(klass, 0.0) + twh
        if use_r2:
            dd = r2_deltas(iso, year, b, gen)
            for klass, twh in dd.items():
                b["classFull"][klass] = b["classFull"].get(klass, 0.0) + twh
            if dd:
                b["classFull"]["oil"] = max(
                    0.0, b["classFull"].get("oil", 0.0) - sum(dd.values())
                )
        with gzip.open(p, "wt") as fh:
            json.dump(full, fh)
    return root


def section4_margin(gen: pd.DataFrame, nanmask: pd.DataFrame, tmp: Path) -> dict:
    """NYISO's C1 rows under each repair, scored with the real scorer."""
    print("\n=== 4. THE MARGIN — NYISO C1 share pp (band +-3.0), by repair")
    pay = _payload(KEEPER)
    out: dict = {}
    print(f"{'yr':<6}{'variant':<24}" + "".join(f"{k:>13}" for k in
          ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "ST_GAS")))
    for year in (2022, 2023, 2024, 2025):
        base = _bench("NYISO", year)
        for tag, u1, u2 in (("committed", False, False), ("R1", True, False),
                            ("R2", False, True), ("R1+R2", True, True)):
            b = copy.deepcopy(base)
            if u1:
                for klass, twh in r1_gaps("NYISO", year, base, nanmask).items():
                    b["classFull"][klass] = b["classFull"].get(klass, 0.0) + twh
            if u2:
                dd = r2_deltas("NYISO", year, base, gen)
                for klass, twh in dd.items():
                    b["classFull"][klass] = b["classFull"].get(klass, 0.0) + twh
                if dd:
                    b["classFull"]["oil"] = max(
                        0.0, b["classFull"].get("oil", 0.0) - sum(dd.values())
                    )
            recs = {r["key"]: r for r in cv.score_fuelmix(year, pay["years"][str(year)], b, "NYISO")}
            out.setdefault(str(year), {})[tag] = {
                k: recs[k]["share_pp"] for k in recs if recs[k].get("share_pp") is not None
            }
            cells = "".join(
                f"{recs[k]['share_pp']:+13.2f}" if k in recs and recs[k].get("share_pp") is not None
                else f"{'-':>13}"
                for k in ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "ST_GAS")
            )
            print(f"{year:<6}{tag:<24}{cells}")
        print()
    return out


def section5_cross_iso(gen: pd.DataFrame, nanmask: pd.DataFrame, tmp: Path) -> dict:
    """Every ISO's designated keeper re-scored against a repaired copy of its own bench."""
    print("=== 5. CROSS-ISO VERDICT CENSUS (rule 25) — determination under each repair")
    print(f"{'ISO':<7}{'variant':<9}{'determination':<28}{'grade':<7}{'fails':<6}FAIL criteria")
    out: dict = {}
    for iso, run_id in _keepers().items():
        for tag, u1, u2 in (("base", False, False), ("R1", True, False), ("R1+R2", True, True)):
            cv.BENCH_DIR = (
                BENCH if tag == "base"
                else _repaired_bench_root(iso, u1, u2, gen, nanmask, tmp)
            )
            v = cv.determine(run_id)
            crit = {k: x.get("status") for k, x in v["criteria"].items()}
            fails = [k for k, s in crit.items() if s == "FAIL"]
            out.setdefault(iso, {})[tag] = {
                "determination": v.get("determination"),
                "grade": v.get("grade_summary", {}).get("target_grade"),
                "fails": fails,
            }
            print(f"{iso:<7}{tag:<9}{v.get('determination'):<28}"
                  f"{v.get('grade_summary', {}).get('target_grade')!s:<7}{len(fails):<6}"
                  f"{fails or 'none'}")
        print()
    cv.BENCH_DIR = BENCH
    flips = [iso for iso, d in out.items()
             if len({d[t]["determination"] for t in d}) > 1]
    print(f"  DETERMINATION FLIPS across all {len(out)} ISOs: {flips or 'ZERO'}")
    return out


def main() -> int:
    """Run every section and optionally write the machine record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    gen = load_monthly_generation()
    nanmask = _nan_month_mask(gen)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        res = {
            "keeper": KEEPER,
            "iso_meter": section1_iso_meter(),
            "r1": section2_r1(gen, nanmask),
            "r2": section3_r2(gen),
            "margin": section4_margin(gen, nanmask, tmp),
            "cross_iso": section5_cross_iso(gen, nanmask, tmp),
        }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(res, indent=1))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
