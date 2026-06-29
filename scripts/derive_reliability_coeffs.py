"""Derive honest per-(zone x class) temperature reliability-floor coefficients.

Part B of ``docs/multi-iso/reliability-floor-rebuild-plan.md``. For one ISO, for
every (model zone, fossil class), this script measures the temperature->commitment
relationship from CAMPD unit-level ``grossLoad`` and emits a transparent
coefficient row. The floor is **structural**, never tuned to a price/volume
residual (CLAUDE.md #9/#11):

    floor_pct = commit_frac x min_stable_pct

where
  * ``min_stable_pct`` = the class's physical min-stable level (Pmin/Pmax),
    taken from the model bins' ``Pct_Must_Run`` share (the must-run tranche the
    LP already enforces), and
  * ``commit_frac`` = the share of the class's nameplate that is *online*
    (``grossLoad > 0``) on temperature-flagged days — a commitment count, NOT a
    measured-CF ceiling.

Per (zone, class) two limbs are evaluated: a **hot** limb gated on the zone's
daily TMAX and a **cold** limb gated on daily TMIN. For each limb we report:
``threshold`` (the °C onset), ``floor_pct``, ``commit_frac``, ``min_stable_pct``,
plus diagnostics ``rho`` (Spearman of the temperature drive vs daily CF), ``n``
(flagged-day count), ``slope`` and ``baseline`` (mild-day mean CF).

A limb ships ``enabled=True`` ONLY when the response is real:
``rho >= RHO_MIN`` AND ``n >= N_MIN`` AND ``floor_pct > baseline``. Otherwise it
ships ``enabled=False`` and is visible (with its weak fit) in the markdown report
so nothing is invented to plug a residual.

Outputs:
  * ``data/raw/reference/reliability_floor_coeffs_<ISO>.csv`` — the coefficient
    table (one row per zone x class x limb that has data).
  * ``docs/multi-iso/reliability-floor-coefficients.md`` — a human-readable
    per-ISO section.

Usage:
    python scripts/derive_reliability_coeffs.py --iso ERCOT
"""

from __future__ import annotations

import argparse
import logging

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DIR, REFERENCE_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("derive_reliability_coeffs")

# --- Enable/disable gate (plan B.3); diagnostics only, never residual-tuned. ---
RHO_MIN = 0.3  # min Spearman temperature->CF correlation to ship a limb on
N_MIN = 30  # min flagged-day sample size to trust a limb
# Default temperature onsets (°C) when not over-ridden per class. Hot = AC-ramp
# commitment onset; cold = gas-electric cold-snap commitment onset.
HOT_THRESHOLD_C = 25.0
COLD_THRESHOLD_C = 0.0
HOURS_PER_DAY = 24  # CF denominator: nameplate x 24 hours

# Fossil classes the engine can floor (plan B.1). Renewables/nuclear/hydro never.
FOSSIL_CLASSES = (
    "COAL",
    "COAL_PRB",
    "COAL_BIT",
    "COAL_LIGNITE",
    "COAL_WC",
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
    "oil",
)

# CAMPD is filed by state; these are each ISO's footprint states (a superset is
# fine — the bin-map join restricts to the ISO's own plants by facilityId).
ISO_CAMPD_STATES: dict[str, tuple[str, ...]] = {
    "ERCOT": ("TX",),
    "CAISO": ("CA",),
    "PJM": (
        "IL",
        "IN",
        "MI",
        "OH",
        "PA",
        "WV",
        "VA",
        "MD",
        "DC",
        "DE",
        "NJ",
        "NC",
        "TN",
        "KY",
    ),
    "MISO": (
        "MN",
        "ND",
        "SD",
        "IA",
        "MO",
        "WI",
        "IL",
        "IN",
        "MI",
        "AR",
        "LA",
        "MS",
        "TX",
    ),
    "NYISO": ("NY",),
    "NEISO": ("CT", "MA", "ME", "NH", "RI", "VT"),
}

# Per-ISO model-fleet bin source + its (zone, class, nameplate, must-run) columns.
# ERCOT uses the curated CAMPD per-plant bins (custom-bin-assignments.csv); the
# other multi-zone ISOs use bin_assignments_<ISO>.csv. PJM has no bin file, so it
# maps plant->zone via data.zone_assignment + class via classify_plant (below).
_LEGACY_BINS = RAW_DIR / "_processed-legacy"


def _zone_temps(iso: str) -> pd.DataFrame:
    """Load the per-zone daily ``date,zone,tmax_c,tmin_c`` series for an ISO."""
    path = RAW_DIR / f"{iso.lower()}-weather" / f"{iso.lower()}_zone_temp_daily.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"zone temp file missing for {iso}: {path} "
            f"(run scripts/fetch_zone_temperature.py --iso {iso})"
        )
    df = pd.read_csv(path, parse_dates=["date"])
    return df


def _plant_map(iso: str) -> pd.DataFrame:
    """Return ``plant_code,zone,plant_class,nameplate_mw,must_run_pct`` for an ISO.

    ERCOT: curated ``custom-bin-assignments.csv`` (groups summed per plant).
    CAISO/MISO/NEISO/NYISO: ``bin_assignments_<ISO>.csv``.
    PJM: model zone from :func:`data.zone_assignment.build_zone_lookup`, class
    from :func:`config.plant_taxonomy.classify_plant` over the EIA-860 fleet.
    """
    iso = iso.upper()
    if iso == "ERCOT":
        b = pd.read_csv(REFERENCE_DIR / "custom-bin-assignments.csv")
        b = b.rename(columns={"ERCOT_Zone": "Zone", "Plant_Group": "plant_class"})
        grp = b.groupby(["Plant_Code", "Zone", "plant_class"], as_index=False).agg(
            nameplate_mw=("Nameplate_MW", "sum"),
            must_run_pct=("Pct_Must_Run", "mean"),
        )
        grp = grp.rename(columns={"Plant_Code": "plant_code", "Zone": "zone"})
        return grp

    legacy = _LEGACY_BINS / f"bin_assignments_{iso}.csv"
    if legacy.exists():
        b = pd.read_csv(legacy)
        grp = b.groupby(["Plant_Code", "Zone", "Plant_Group"], as_index=False).agg(
            nameplate_mw=("Nameplate_MW", "sum"),
            must_run_pct=("Pct_Must_Run", "mean"),
        )
        return grp.rename(
            columns={
                "Plant_Code": "plant_code",
                "Zone": "zone",
                "Plant_Group": "plant_class",
            }
        )

    if iso == "PJM":
        return _pjm_plant_map()

    raise FileNotFoundError(f"no bin/zone source for ISO {iso}")


def _pjm_plant_map() -> pd.DataFrame:
    """Build the PJM ``plant_code,zone,plant_class,nameplate_mw,must_run_pct`` map.

    Zone from eGRID/EIA-860 geography (``build_zone_lookup``), class from the
    canonical :func:`classify_plant`. Nameplate comes from the model's EIA-860
    fleet loader so the CF denominator matches the LP capacity basis. Falls back
    to an empty frame (handled gracefully by the caller) if the fleet loader is
    unavailable.
    """
    from market_sim.config.plant_taxonomy import classify_plant
    from market_sim.data.zone_assignment import build_zone_lookup

    zone_lookup = build_zone_lookup("PJM")
    try:
        from market_sim.data.fleet import load_eia860_fleet

        fleet = load_eia860_fleet("PJM")
    except Exception as exc:  # pragma: no cover - Phase-2 fleet wiring
        log.warning("PJM fleet load unavailable (%s); PJM map empty", exc)
        return pd.DataFrame(
            columns=[
                "plant_code",
                "zone",
                "plant_class",
                "nameplate_mw",
                "must_run_pct",
            ]
        )

    rows = []
    for rec in fleet.itertuples(index=False):
        oris = int(getattr(rec, "plant_code", getattr(rec, "Plant_Code", 0)) or 0)
        if oris not in zone_lookup:
            continue
        klass = classify_plant(
            getattr(rec, "fuel", ""),
            getattr(rec, "prime_mover", ""),
            bool(getattr(rec, "chp_flag", False)),
            oris,
        )
        rows.append(
            {
                "plant_code": oris,
                "zone": zone_lookup[oris],
                "plant_class": klass,
                "nameplate_mw": float(getattr(rec, "nameplate_mw", 0.0) or 0.0),
                "must_run_pct": float(getattr(rec, "must_run_pct", 0.0) or 0.0),
            }
        )
    return pd.DataFrame(rows)


def _load_campd(iso: str, plant_codes: set[int]) -> pd.DataFrame:
    """Concatenate the ISO's state CAMPD unit-level frames, kept to its plants.

    Aggregates each unit row to a per-(facilityId, date, hour) ``grossLoad`` is
    not needed — we keep the unit rows and sum per group/day downstream. Raises a
    clear error when no CAMPD parquet is present for the ISO.
    """
    states = ISO_CAMPD_STATES.get(iso.upper(), ())
    frames: list[pd.DataFrame] = []
    for st in states:
        for yr in (2023, 2024, 2025):
            p = RAW_DIR / "campd-unit-level" / f"{st}_{yr}.parquet"
            if p.exists():
                frames.append(
                    pd.read_parquet(p, columns=["facilityId", "date", "grossLoad"])
                )
    if not frames:
        raise FileNotFoundError(
            f"no CAMPD unit-level parquet found for {iso} states {states}"
        )
    c = pd.concat(frames, ignore_index=True)
    c["facilityId"] = c["facilityId"].astype(int)
    c = c[c["facilityId"].isin(plant_codes)].copy()
    c["date"] = pd.to_datetime(c["date"])
    return c


def _group_daily_cf(
    campd: pd.DataFrame, plant_npl: dict[int, float], nameplate: float
) -> pd.DataFrame:
    """Daily ``cf`` and ``online_frac`` for a (zone, class) plant group.

    * ``cf`` = group daily MWh / (group nameplate x 24), clipped to [0, 1].
    * ``online_frac`` = nameplate-weighted share of the group's capacity that is
      online (any unit ``grossLoad > 0``) that day — the commitment count, on the
      same model nameplate basis as the CF denominator. CAMPD carries no
      nameplate, so each plant's online presence is weighted by its bin nameplate
      (``plant_npl``).
    """
    codes = set(plant_npl)
    if nameplate <= 0.0 or not codes:
        return pd.DataFrame(columns=["cf", "online_frac"])
    sub = campd[campd["facilityId"].isin(codes)].copy()
    if sub.empty:
        return pd.DataFrame(columns=["cf", "online_frac"])
    daily_mwh = sub.groupby("date")["grossLoad"].sum(min_count=1)
    cf = (daily_mwh / (nameplate * HOURS_PER_DAY)).clip(0.0, 1.0)
    # Per-plant online nameplate: a plant counts as online on any day it reports
    # positive gross load; sum its bin nameplate, normalise by group nameplate.
    online = sub[sub["grossLoad"].fillna(0.0) > 0.0]
    online_plants = online.groupby("date")["facilityId"].agg(lambda s: set(s))
    online_share = online_plants.apply(
        lambda s: sum(plant_npl.get(int(p), 0.0) for p in s) / nameplate
    ).clip(0.0, 1.0)
    return pd.DataFrame({"cf": cf, "online_frac": online_share})


def _fit_limb(
    df: pd.DataFrame, temp: pd.Series, threshold: float, cold: bool
) -> dict | None:
    """Fit one temperature limb; return its coefficient dict or ``None``.

    ``drive`` rises with severity (TMAX above the hot onset, or coldness below the
    cold onset). Flagged days are those past the threshold. ``commit_frac`` is the
    mean online share on flagged days; ``baseline`` is the mild-day mean CF.
    """
    d = df.join(temp.rename("t"), how="inner").dropna(subset=["cf", "t"])
    if d.empty:
        return None
    if cold:
        flagged = d[d["t"] < threshold]
        drive = threshold - flagged["t"]
        mild = d[d["t"] >= threshold]
    else:
        flagged = d[d["t"] >= threshold]
        drive = flagged["t"] - threshold
        mild = d[d["t"] < threshold]
    n = int(len(flagged))
    if n < 2:
        return None
    commit_frac = float(flagged["online_frac"].mean())
    baseline = float(mild["cf"].mean()) if len(mild) else 0.0
    slope = float(np.polyfit(drive, flagged["cf"], 1)[0]) if n >= 2 else 0.0
    rho = (
        float(drive.corr(flagged["cf"], method="spearman"))
        if n >= 2 and drive.nunique() > 1
        else float("nan")
    )
    return {
        "commit_frac": commit_frac,
        "baseline": baseline,
        "slope": slope,
        "rho": rho,
        "n": n,
    }


def derive_iso(iso: str) -> pd.DataFrame:
    """Derive the full per-(zone, class, limb) coefficient table for one ISO."""
    iso = iso.upper()
    temps = _zone_temps(iso)
    pmap = _plant_map(iso)
    if pmap.empty:
        log.warning("%s: empty plant map; no coefficients derived", iso)
        return pd.DataFrame()

    pmap = pmap[pmap["plant_class"].isin(FOSSIL_CLASSES)].copy()
    all_codes = set(pmap["plant_code"].astype(int))
    campd = _load_campd(iso, all_codes)

    rows: list[dict] = []
    for (zone, klass), grp in pmap.groupby(["zone", "plant_class"], sort=False):
        plant_npl = dict(
            zip(grp["plant_code"].astype(int), grp["nameplate_mw"].astype(float))
        )
        nameplate = float(grp["nameplate_mw"].sum())
        # min-stable level = the must-run tranche share (Pmin/Pmax proxy), [0,1].
        min_stable_pct = float(np.clip(grp["must_run_pct"].mean() / 100.0, 0.0, 1.0))
        cf = _group_daily_cf(campd, plant_npl, nameplate)
        if cf.empty:
            continue
        zt = temps[temps["zone"] == zone].set_index("date")
        if zt.empty:
            continue
        for driver, threshold, cold in (
            ("tmax", HOT_THRESHOLD_C, False),
            ("tmin", COLD_THRESHOLD_C, True),
        ):
            fit = _fit_limb(cf, zt[f"{driver}_c"], threshold, cold)
            if fit is None:
                continue
            floor_pct = float(fit["commit_frac"] * min_stable_pct)
            enabled = bool(
                (not np.isnan(fit["rho"]))
                and fit["rho"] >= RHO_MIN
                and fit["n"] >= N_MIN
                and floor_pct > fit["baseline"]
            )
            rows.append(
                {
                    "iso": iso,
                    "zone": zone,
                    "plant_class": klass,
                    "driver": driver,
                    "threshold": round(threshold, 2),
                    "floor_pct": round(floor_pct, 4),
                    "enabled": enabled,
                    "commit_frac": round(fit["commit_frac"], 4),
                    "min_stable_pct": round(min_stable_pct, 4),
                    "rho": round(fit["rho"], 4) if not np.isnan(fit["rho"]) else "",
                    "n": fit["n"],
                    "baseline": round(fit["baseline"], 4),
                }
            )
    return pd.DataFrame(rows)


def _write_markdown(iso: str, table: pd.DataFrame) -> None:
    """Append a human-readable per-ISO section to the coefficient markdown."""
    md_path = RAW_DIR.parent / "multi-iso" / "reliability-floor-coefficients.md"
    # docs path: repo docs/multi-iso/ (RAW_DIR is data/raw, so go to repo root).
    repo_root = RAW_DIR.parent.parent
    md_path = repo_root / "docs" / "multi-iso" / "reliability-floor-coefficients.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)

    header = (
        "# Temperature reliability-floor coefficients\n\n"
        "Derived by `scripts/derive_reliability_coeffs.py`. `floor_pct = "
        "commit_frac x min_stable_pct` (never residual-tuned, CLAUDE.md #9/#11). "
        "A limb is `enabled` only when `rho >= 0.3`, `n >= 30`, and `floor_pct > "
        "baseline`; weak limbs ship OFF but stay visible below.\n"
    )
    existing = ""
    if md_path.exists():
        existing = md_path.read_text()
    if not existing.startswith("# Temperature reliability-floor coefficients"):
        existing = header

    # Strip any prior section for this ISO so re-runs are idempotent.
    marker = f"\n## {iso}\n"
    if marker in existing:
        existing = existing.split(marker)[0]
    if not existing.endswith("\n"):
        existing += "\n"

    lines = [f"\n## {iso}\n"]
    if table.empty:
        lines.append("\n_No coefficients derived (no data)._\n")
    else:
        cols = [
            "zone",
            "plant_class",
            "driver",
            "threshold",
            "floor_pct",
            "enabled",
            "commit_frac",
            "min_stable_pct",
            "rho",
            "n",
            "baseline",
        ]
        lines.append("\n| " + " | ".join(cols) + " |\n")
        lines.append("|" + "|".join(["---"] * len(cols)) + "|\n")
        for r in table.itertuples(index=False):
            lines.append("| " + " | ".join(str(getattr(r, c)) for c in cols) + " |\n")
    md_path.write_text(existing + "".join(lines))
    log.info("wrote markdown section -> %s", md_path)


def main() -> None:
    """CLI: derive + write the coefficient CSV and markdown for one ISO."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True, help="ISO to derive (e.g. ERCOT).")
    args = ap.parse_args()
    iso = args.iso.upper()

    try:
        table = derive_iso(iso)
    except FileNotFoundError as exc:
        log.error("%s: %s", iso, exc)
        return

    out_csv = REFERENCE_DIR / f"reliability_floor_coeffs_{iso}.csv"
    if table.empty:
        log.warning("%s: no coefficient rows produced; CSV not written", iso)
    else:
        table.to_csv(out_csv, index=False)
        n_on = int(table["enabled"].sum())
        log.info("%s: %d limbs (%d enabled) -> %s", iso, len(table), n_on, out_csv)
    _write_markdown(iso, table)


if __name__ == "__main__":
    main()
