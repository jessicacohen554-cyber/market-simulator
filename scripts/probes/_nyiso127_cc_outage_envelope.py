"""nyiso-127 ITEM 2 / Q3 — how much of NYISO's CC capacity-year is booked as outage?

Scorer-side, **no LP solve**, committed artifacts and ``data/raw`` only. Answers the
question the holdout spend freeze (``frontend/data/backcast/holdout-freeze.json``)
poses per ISO: the freeze's stated reason is that the CAMPD unit-outage detector
books sustained economic layup as mechanical outage in all six ISO extracts,
"23-46 % of its CC capacity-year as outage against a real EFOR + planned norm of
~10-15 %" (``results/calibration/FINDING-neiso63-campd-economic-layup-2026-07.md``).
The merit-order guard was ADOPTED-AS-IMPROVEMENT 2026-07-26 and the freeze was
HELD because a residual over-count survived it, measured on NEISO. **This probe
measures the residual for NYISO specifically, on the CURRENT (post-guard)
extract.**

Two metrics, both reported:

* **neiso-63's own unit-year metric**, reproduced exactly so the 46 % baseline is
  comparable like-for-like: per unit-year, mean days out / 365, full-year windows
  excluded, over the units that appear in the extract.
* **A capacity-weighted envelope share** — MW-days booked out over installed
  CC MW-days — which is the quantity the availability envelope actually carries
  into the LP. Denominator is the model's own NYISO fleet
  (``data/raw/_processed-legacy/bin_assignments_NYISO.csv``).

Three populations are scored: BASELINE (mechanical + layup companion = the
pre-guard extract), CURRENT (``campd-unit-outages-NYISO.csv``, what every keeper
since the guard is calibrated against), and VETOED (the layup companion the guard
removed).

Rule 22 [R-HOLDOUT]: 2023-2025 only. No out-of-training year is read, scored or
registered here, and nothing in this probe lifts or edits the freeze.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from market_sim.config.paths import RAW_DIR

YEARS = (2023, 2024, 2025)
CC_CLASSES = ("CC_REGULAR", "CC_CHP")


def _load(path) -> pd.DataFrame:
    """Read an outage extract and parse its window bounds."""
    df = pd.read_csv(path, parse_dates=["outage_start", "outage_end"])
    return df


def _overlap_days(df: pd.DataFrame, year: int) -> pd.Series:
    """Days of each window that fall inside ``year`` (clipped at both ends)."""
    lo = pd.Timestamp(year, 1, 1)
    hi = pd.Timestamp(year + 1, 1, 1)
    start = df["outage_start"].clip(lower=lo, upper=hi)
    end = df["outage_end"].clip(lower=lo, upper=hi)
    return (end - start).dt.total_seconds().clip(lower=0.0) / 86400.0


def _panel_cc_mw(base: pd.DataFrame) -> dict[str, float]:
    """Installed CC MW of the detector's own unit panel, on the EXTRACT's basis.

    The denominator must be the same capacity basis as the numerator. The
    extract's ``unit_capacity_mw`` is CAMPD/EIA unit capacity and does NOT equal
    the model fleet's ``Nameplate_MW`` (CC_REGULAR: 8,949.8 MW of extract units
    across 23 plants against 6,856.5 MW of fleet nameplate across the same 23
    plants — a different basis, not a different fleet). Mixing them would inflate
    every share by ~1.31x, so the panel's own capacity is used throughout and the
    model fleet is only cross-checked for coverage.

    Panel = every unit appearing in the union of the mechanical and layup
    extracts. A CC unit that never had a single window in 2018-2026 would be
    missing (biasing the share up); coverage is checked in ``main``.
    """
    units = base.drop_duplicates(subset=["facility_id", "unit_id"])
    by_class = units.groupby("plant_group")["unit_capacity_mw"].sum().to_dict()
    out = {k: float(v) for k, v in by_class.items() if k in CC_CLASSES}
    out["CC_ALL"] = float(sum(out.get(k, 0.0) for k in CC_CLASSES))
    return out


def _capacity_weighted(df: pd.DataFrame, year: int, classes: tuple[str, ...]) -> float:
    """MW-days booked out in ``year`` for ``classes``."""
    sub = df[df["plant_group"].isin(classes)].copy()
    if sub.empty:
        return 0.0
    sub["days"] = _overlap_days(sub, year)
    return float((sub["days"] * sub["unit_capacity_mw"]).sum())


def _unit_year_metric(df: pd.DataFrame, year: int, klass: str) -> tuple[float, int]:
    """neiso-63's metric: mean days out per unit-year, full-year windows excluded."""
    sub = df[df["plant_group"] == klass].copy()
    if sub.empty:
        return float("nan"), 0
    sub["days"] = _overlap_days(sub, year)
    sub = sub[sub["days"] > 0.0]
    # neiso-63 excluded full-year windows (a unit out the whole year is a
    # mothball, not an outage-rate observation).
    sub = sub[sub["days"] < 364.0]
    if sub.empty:
        return float("nan"), 0
    per_unit = sub.groupby(["facility_id", "unit_id"])["days"].sum()
    return float(per_unit.mean()), int(per_unit.size)


def _headroom() -> dict:
    """How pinned is the keeper's CC_REGULAR fleet against its own ceiling?

    Read straight off the keeper bundle's committed ``class_hourly_<year>``
    sidecar, so no capacity basis is mixed in: the ceiling is the model's own
    annual maximum CC_REGULAR output, and the question is what fraction of hours
    sit within 5 % of it. A fleet with a realistic availability envelope has
    headroom in most hours; a fleet whose envelope is too tight runs pinned, and
    then CC cannot be the marginal unit and something dearer sets the price.

    Indicative only — this measures the consequence, it does not attribute it.
    """
    bundle = "results/calibration/nyiso125_seam_A/hourly"
    out: dict = {}
    print("=== KEEPER CC_REGULAR HEADROOM (committed class_hourly sidecar, P1) ===")
    print(f"{'year':6s} {'annual max MW':>14s} {'mean MW':>9s} {'mean/max':>9s} {'h >=95% of max':>15s}")
    for year in YEARS:
        df = pd.read_parquet(f"{bundle}/class_hourly_{year}.parquet")
        cc = df[(df["klass"] == "CC_REGULAR") & (df["pass"] == "P1")]["mw"].to_numpy()
        top = float(cc.max())
        pinned = int((cc >= 0.95 * top).sum())
        print(
            f"{year:<6d} {top:14,.0f} {cc.mean():9,.0f} {cc.mean() / top:8.1%} "
            f"{pinned:8d} ({pinned / cc.size:5.1%})"
        )
        out[str(year)] = {
            "annual_max_mw": round(top, 1),
            "mean_mw": round(float(cc.mean()), 1),
            "mean_over_max": round(float(cc.mean()) / top, 4),
            "hours_within_5pct_of_max": pinned,
            "share_of_hours": round(pinned / cc.size, 4),
        }
    print()
    return out


def _dof_symbol_check() -> list[tuple[str, str]]:
    """Every ALL-CAPS symbol the keeper's DOF ledger cites, checked against the code.

    Rule 20 [R-DOF]: the ledger lists each free parameter with its identification
    source. An entry citing a module symbol that does not exist at HEAD cannot
    bind a solve and cannot be verified, so it is a ledger defect. Reported, not
    edited (the ledger is generated by ``scripts/gen_nyiso125_attestation.py``).
    """
    attest = json.loads(
        Path("results/calibration/nyiso125_seam_A/calibration_attestation.json").read_text()
    )
    pairs: set[tuple[str, str]] = set()
    for entry in attest["free_parameters"]["entries"]:
        for sym in re.findall(r"\b([A-Z][A-Z0-9_]{5,})\b", entry.get("where", "")):
            pairs.add((entry["name"][:60], sym))
    src = Path("src/market_sim")
    missing: list[tuple[str, str]] = []
    for name, sym in sorted(pairs):
        found = any(sym in p.read_text(errors="ignore") for p in src.rglob("*.py"))
        if not found:
            missing.append((name, sym))
    print("=== DOF LEDGER SYMBOL CHECK (rule 20) ===")
    print(f"   ALL-CAPS symbols cited by the ledger's `where` fields: {len(pairs)}")
    if missing:
        for name, sym in missing:
            print(f"   NOT FOUND in src/market_sim/: {sym}  <- ledger entry '{name}'")
    else:
        print("   all cited symbols resolve at HEAD")
    print()
    return missing


def main() -> None:
    """Print the NYISO CC outage-envelope decomposition for 2023-2025."""
    mech = _load(RAW_DIR / "campd-unit-outages-NYISO.csv")
    layup = _load(RAW_DIR / "campd-unit-outages-layup-NYISO.csv")
    base = pd.concat([mech, layup.drop(columns=["out_of_merit_share"])], ignore_index=True)

    fleet = _panel_cc_mw(base)
    print("NYISO CC panel capacity (detector's own basis, unit_capacity_mw):")
    for k in sorted(fleet):
        print(f"   {k:12s} {fleet[k]:9,.1f} MW")

    # Coverage cross-check against the model fleet: plants, not MW (different basis).
    model_fleet = pd.read_csv(RAW_DIR / "_processed-legacy" / "bin_assignments_NYISO.csv")
    for klass in CC_CLASSES:
        in_fleet = set(model_fleet.loc[model_fleet["Plant_Group"] == klass, "Plant_Code"])
        in_panel = set(base.loc[base["plant_group"] == klass, "facility_id"])
        print(
            f"   coverage {klass:10s} fleet plants {len(in_fleet):3d} · panel plants "
            f"{len(in_panel):3d} · fleet plants with no window ever: "
            f"{sorted(in_fleet - in_panel)}"
        )
    print()

    pops = {"BASELINE (pre-guard)": base, "CURRENT (post-guard)": mech, "VETOED (layup)": layup}
    record: dict = {
        "probe": "_nyiso127_cc_outage_envelope",
        "question": "ITEM 2 / Q3 — does the holdout freeze's stated reason still bind for NYISO?",
        "keeper": "2026-08-04-nyiso-125-seam-envelope",
        "years": list(YEARS),
        "panel_capacity_mw": fleet,
        "capacity_weighted_pct": {},
        "unit_year_pct": {},
        "headroom": {},
    }

    print("=== CAPACITY-WEIGHTED: MW-days booked out / installed CC MW-days ===")
    print(f"{'population':24s} {'class':12s} " + "  ".join(f"{y:>8d}" for y in YEARS))
    for label, df in pops.items():
        for klass, denom_key in (
            (("CC_REGULAR",), "CC_REGULAR"),
            (("CC_CHP",), "CC_CHP"),
            (CC_CLASSES, "CC_ALL"),
        ):
            shares = []
            for year in YEARS:
                mwd = _capacity_weighted(df, year, klass)
                denom = fleet[denom_key] * 365.0
                shares.append(100.0 * mwd / denom)
            name = klass[0] if len(klass) == 1 else "CC_ALL"
            print(f"{label:24s} {name:12s} " + "  ".join(f"{s:7.1f}%" for s in shares))
            record["capacity_weighted_pct"][f"{label}|{name}"] = [round(s, 2) for s in shares]
    print()

    print("=== neiso-63 UNIT-YEAR METRIC (mean days out / 365, full-year excluded) ===")
    print(f"{'population':24s} {'class':12s} " + "  ".join(f"{y:>14d}" for y in YEARS))
    for label, df in pops.items():
        for klass in CC_CLASSES:
            cells, vals = [], []
            for year in YEARS:
                mean_days, n = _unit_year_metric(df, year, klass)
                vals.append([round(100.0 * mean_days / 365.0, 1) if n else None, n])
                cells.append(f"{100.0 * mean_days / 365.0:5.0f}% (n={n:2d})" if n else "     -      ")
            print(f"{label:24s} {klass:12s} " + "  ".join(f"{c:>14s}" for c in cells))
            record["unit_year_pct"][f"{label}|{klass}"] = vals
    print()

    record["headroom"] = _headroom()
    record["dof_ledger_symbols_missing_at_head"] = _dof_symbol_check()

    print("Reference: neiso-63 measured NYISO CC_REGULAR at 46 % of the year on the")
    print("PRE-GUARD extract (2023-2025 pooled, unit-year metric); the real CC")
    print("EFOR + planned-maintenance norm the freeze cites is ~10-15 %.")

    out = Path("results/calibration/_nyiso127_cc_outage_envelope.json")
    out.write_text(json.dumps(record, indent=2) + "\n")
    print(f"\nrecord -> {out}")


if __name__ == "__main__":
    main()
