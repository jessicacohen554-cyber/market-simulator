"""Derive measured gas commitment parameters (min-load fraction, run lengths) from CAMPD.

The measured-conduct basis for the P1-native gas commitment bridge
(``ScenarioConfig.nyiso_gas_commitment_bridge`` and the ISO-neutral detector
:func:`market_sim.model.commitment.caiso_ra_mustoffer_min_gen`). The bridge needs
two per-class numbers, and both must be MEASURED operating statistics rather
than fitted values (CLAUDE.md rules 5 [R-NO-MAGIC] / 13 [R-MEASURED] / 21
[R-DOF]):

1. ``min_load_frac`` — minimum stable load as a fraction of maximum sustained
   load. ERCOT identifies this from the 60-Day DAM disclosure's published
   LSL/HSL pairs (capacity-weighted p50 = 0.574,
   ``ScenarioConfig.ercot_gas_bridge_min_load_frac``). **NYISO publishes no
   equivalent unit-level offer disclosure**, so this script reconstructs the
   same ratio from unit CONDUCT in the EPA CAMPD/CEMS hourly record — the
   WP-3 "loading-when-on" construction (``scripts/data/derive_thermal_tranches.py``
   ``_CHP_STEAM_LEVEL_ON_PCTILE``): condition on the unit being online, then
   take a percentile of its own loading distribution. Per unit::

       HSL_proxy = p99.5 of grossLoad over the pooled window
       online    = grossLoad >= max(_ONLINE_MW, _ONLINE_FRAC x HSL_proxy)
       LSL_proxy = p5 of grossLoad over ONLINE hours
       lsl_frac  = LSL_proxy / HSL_proxy

   The p5-of-online-hours statistic is the ``derive_cc_committed_pct.py``
   construction verbatim ("the minimum stable load the plant holds at when
   backed down, excluding brief ramp transients"). Taking BOTH the numerator
   and the denominator from the same meter makes the ratio independent of the
   nameplate/outage crosswalk: a derated or partly-out unit still reports its
   own sustained floor, and a fully-out unit simply contributes no online
   hours. The class value is the capacity-weighted p50 of ``lsl_frac`` across
   units — the population statistic ERCOT's cap-weighted LSL/HSL p50 is.

2. ``min_run_hours`` — the run-length distribution. A real unit commitment
   holds a started unit online for a minimum duration; the class tables
   (``constants.CC_COMMITMENT_PARAMS`` / ``ST_GAS_COMMITMENT_PARAMS``, NREL/
   SR-5500-55433) carry engineering values, and this script measures what the
   ISO's own fleet actually does. A *run* is a maximal block of consecutive
   online hours (the ``derive_campd_ct_run_lengths.py`` convention), computed
   WITHIN a year so runs never stitch across a vintage boundary. The class
   p50/p75 of the pooled run-length distribution are the identification source
   for a keeper ``min_run_hours``; a value may be probed above them, but a
   keeper value must come from this artifact, never from a residual moving
   (rule 23 [R-FROZEN-DERIVE]).

Scope: units at plants the ISO's own model fleet assigns to one of
:data:`TARGET_CLASSES`, which is what keeps a shared state extract (NJ is read
for both NYISO and PJM) from leaking another ISO's plants in. A plant whose
model fleet rows span more than one target class is AMBIGUOUS at the CAMPD
facility level (CEMS unit ids do not carry the model's class) and is dropped
with a printed note rather than silently attributed.

Output: ``data/raw/_processed-legacy/campd_gas_commitment_params_{ISO}.csv``
(one row per class plus the per-unit detail under ``--detail``).

Governance (CLAUDE.md rules 13 [R-MEASURED] / 23 [R-FROZEN-DERIVE]): a measured
market-behaviour parameter in the same admissibility class as the CAMPD
committed shares, min-stable loads and CT run horizons — it regenerates from
the CAMPD pipeline for any new vintage and re-derives ONLY when its source data
updates. Rule 13 admissibility: both statistics are unit-conduct properties that
would be produced identically for a forward year and respond to changed
conditions (a fleet that cycles more shortens its measured runs); neither is a
measured OUTCOME fed back to close a residual.

BASIS (``--plant-basis``): the per-unit ratio above is one TURBINE's turndown.
A consumer whose floor is multiplied by PLANT capacity needs the PLANT's
minimum stable CONFIGURATION instead, which on a multi-train combined cycle is
roughly half the per-unit value. See :data:`PLANT_BASIS_NOTE` for the
adjudication and the CAISO measurement that forced it.

Usage::

    python scripts/data/derive_campd_gas_commitment_params.py --iso NYISO
    python scripts/data/derive_campd_gas_commitment_params.py --iso CAISO --plant-basis
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data.campd import _ONLINE_MW, states_for_iso  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"

# Model classes the gas commitment bridge can floor: the merchant slow-start
# gas fleet. Cogens (*_CHP) follow their steam host and are never bridged;
# fast-start CT classes fail the bridge's own physics gate (min-down 1 h,
# $12-25/MW starts) and are excluded here too so the artifact cannot be
# mis-wired onto them later (CLAUDE.md rule 18 [R-PHYSICS]).
TARGET_CLASSES: tuple[str, ...] = ("CC_REGULAR", "ST_GAS")

# ``--ct`` target: the fast-start peaker class. Kept OUT of the default
# :data:`TARGET_CLASSES` above for two independent reasons, only one of which
# the original exclusion note stated:
#
# 1. *Byte-safety.* Adding CT_PEAKER to the default set would make every mixed
#    steam/turbine plant (E F Barrett, Gowanus, Narrows) span two target
#    classes, so ``class_plant_codes`` would drop them as AMBIGUOUS — silently
#    changing the committed CC_REGULAR/ST_GAS rows the keeper's bridge already
#    reads. The ``--ct`` path therefore targets CT alone and writes its own
#    artifact; the default invocation stays byte-identical.
# 2. *Physics scoping.* The original note said CT classes "fail the bridge's
#    own physics gate (min-down 1 h, $12-25/MW starts)". That is true of the
#    ECONOMIC gap bridge and remains true: ``RA_BRIDGE_ECON_MIN_DOWN_HOURS``
#    (4 h) is untouched, so a fast-start CT is still never HELD ACROSS an idle
#    gap (rule 18 [R-PHYSICS], nyiso-87). It is NOT true of the ``min_run_hours``
#    extension leg, which is gated on minimum-RUN physics — a distinct property.
#    Minimum-down governs how fast a unit can come back; minimum-run governs how
#    long a started unit must stay on. The NREL class tables already carry the
#    two independently for every other fuel. Measuring the CT class's run
#    horizon does not re-arm economic bridging on it.
CT_TARGET_CLASSES: tuple[str, ...] = ("CT_PEAKER",)

# CAMPD ``unitType`` the ``--ct`` path restricts to (casefolded compare). The
# same device ``derive_campd_ct_heat_rates.py`` uses: CEMS unit ids carry no
# model class, but CAMPD's own ``unitType`` says which units are simple-cycle
# turbines, so a mixed facility contributes ONLY its turbines instead of being
# dropped as unattributable. Without it the CT artifact would lose Barrett,
# Gowanus and Narrows — 832 MW, the whole 1970s barge fleet.
CT_UNIT_TYPE: str = "combustion turbine"

# Robust maximum-sustained-load percentile: the HSL proxy. p99.5 rather than
# the raw max so a single over-range meter sample cannot inflate the
# denominator and depress every unit's measured lsl_frac.
_HSL_PCTILE: float = 99.5

# Online threshold as a fraction of the unit's own HSL proxy, floored at the
# CAMPD online convention (:data:`market_sim.data.campd._ONLINE_MW`). The same
# "low bar that admits a single unit at part load while rejecting sensor noise
# and ramp-through-zero" as derive_cc_committed_pct.py's ``_ONLINE_FRAC``.
_ONLINE_FRAC: float = 0.05

# Percentile of the ONLINE-hours loading distribution taken as the unit's
# minimum stable load (derive_cc_committed_pct.py: "the committed-tranche % is
# the P5 of that distribution ... excluding brief ramp transients").
_LSL_PCTILE: float = 5.0

# Percentile taken ACROSS units for the class value. ERCOT's published
# LSL/HSL identification is a capacity-weighted p50 over the unit population;
# this reproduces that aggregation on the conduct-derived ratios.
_CLASS_PCTILE: float = 50.0

# ``--plant-basis``: WHICH minimum-load fraction a consumer actually needs.
#
# The two statistics are different physical quantities and differ by ~2x on a
# multi-train combined-cycle fleet:
#
# * PER-UNIT (the default) — one CEMS unit's own turndown against its own
#   maximum sustained load. This is what ERCOT's published 60-Day-DAM LSL/HSL
#   pairs measure (per RESOURCE/train), which is why the two agree there
#   (CAISO per-unit 0.566-0.572 vs ERCOT 0.574).
# * PER-PLANT (this flag) — the facility's whole metered output against its own
#   full capability. A 2x1 or 3x1 CC plant's minimum stable CONFIGURATION is
#   one train at minimum, so the plant fraction is roughly the per-train
#   fraction divided by the train count.
#
# A consumer must use the basis its own denominator is on. The CAISO RA
# must-offer bridge (``market_sim.model.commitment.caiso_ra_mustoffer_min_gen``)
# floors ``min_load_frac x PLANT pmax`` — "the floor is the PLANT's minimum
# stable load ... never a per-tranche fraction" — and CAISO runs
# ``plant_level_fleet=True``, so the PLANT statistic is the admissible one
# there. Measured on CAISO CC_REGULAR 2023-25 the two bases are 0.566-0.572
# (unit) against 0.289-0.304 (plant): applying the per-unit value to plant
# capacity asserts a minimum CAISO's own plants sit below in ~2 of every 5
# online hours. Evidence and adjudication: ``FINDING-caiso135`` §A / §R.
#
# Writes its own ``*_plant.csv`` artifact so the default per-unit invocation
# (the NYISO/ERCOT identification the shipped bridge parameters cite) stays
# byte-identical.
PLANT_BASIS_NOTE: str = (
    "PLANT basis: facility units summed to one series before measuring, so "
    "min_load_frac is the plant's minimum stable CONFIGURATION over its full "
    "capability (the basis a floor multiplied by PLANT pmax requires)"
)


def unit_run_lengths(on: np.ndarray) -> list[int]:
    """Return the lengths (hours) of maximal True-blocks in ``on``."""
    if not on.any():
        return []
    d = np.diff(np.concatenate([[0], on.astype(np.int8), [0]]))
    starts = np.where(d == 1)[0]
    ends = np.where(d == -1)[0]
    return (ends - starts).tolist()


def weighted_percentile(values: np.ndarray, weights: np.ndarray, pct: float) -> float:
    """Return the ``pct`` weighted percentile of *values* (weights >= 0).

    The capacity-weighted order statistic: sort by value, walk the cumulative
    weight, and return the first value at or past ``pct``% of the total. Used
    for the class-level aggregation so a 1,000 MW block and a 20 MW block do
    not count equally toward the fleet's minimum-load fraction.

    Args:
        values: The per-unit statistic.
        weights: Per-unit capacity weights, same shape.
        pct: Percentile in ``[0, 100]``.

    Returns:
        The weighted percentile, or ``nan`` when the total weight is zero.
    """
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    keep = np.isfinite(v) & np.isfinite(w) & (w > 0)
    if not keep.any():
        return float("nan")
    v, w = v[keep], w[keep]
    order = np.argsort(v)
    v, w = v[order], w[order]
    cum = np.cumsum(w) / w.sum()
    return float(v[np.searchsorted(cum, pct / 100.0, side="left").clip(0, v.size - 1)])


def class_plant_codes(
    iso: str, classes: tuple[str, ...] = TARGET_CLASSES
) -> tuple[dict[int, str], list[int]]:
    """Return ``({plant_code: class}, ambiguous_codes)`` for the ISO's fleet.

    A CAMPD facility carries no model class, so the mapping is by plant code.
    A plant whose model rows span more than one *classes* entry cannot be
    attributed at facility level and is returned as ambiguous (and excluded)
    rather than folded into whichever class happened to appear first.

    Args:
        iso: The ISO name.
        classes: The model classes to target. Defaults to
            :data:`TARGET_CLASSES`; the ``--ct`` path passes
            :data:`CT_TARGET_CLASSES`.
    """
    fleet = load_fleet_from_csv(iso, get_iso_config(iso))
    by_code: dict[int, set[str]] = {}
    for gen in fleet:
        if gen.plant_group not in classes:
            continue
        code = int(gen.plant_code or 0)
        if code:
            by_code.setdefault(code, set()).add(gen.plant_group)
    mapping = {c: next(iter(k)) for c, k in by_code.items() if len(k) == 1}
    ambiguous = sorted(c for c, k in by_code.items() if len(k) > 1)
    return mapping, ambiguous


def unit_statistics(
    iso: str,
    years: list[int],
    classes: tuple[str, ...] = TARGET_CLASSES,
    unit_type: str | None = None,
    plant_basis: bool = False,
) -> pd.DataFrame:
    """Return one row per CAMPD unit with its measured LSL fraction and runs.

    Loads each state-year extract once, restricts to the ISO's own target-class
    plants, and reduces each ``(facilityId, unitId)`` to the conduct statistics
    described in the module docstring. Run lengths are pooled across years but
    computed WITHIN each year, so a unit online at both year boundaries does not
    report one spurious multi-year run.

    Args:
        iso: The ISO name.
        years: CAMPD vintages to pool.
        classes: Model classes to target (default :data:`TARGET_CLASSES`).
        unit_type: When given, keep only CAMPD rows whose ``unitType`` matches
            (casefolded). The ``--ct`` path passes :data:`CT_UNIT_TYPE` so a
            mixed steam/turbine facility contributes only its turbines.
        plant_basis: Sum each facility's units to one PLANT series before
            measuring, so ``lsl_frac`` is the plant's minimum stable
            CONFIGURATION over its full capability rather than one turbine's
            own turndown. See :data:`PLANT_BASIS_NOTE`.
    """
    mapping, ambiguous = class_plant_codes(iso, classes)
    if not mapping:
        raise SystemExit(f"{iso}: model fleet has no {classes} plants")
    if ambiguous:
        print(
            f"  (dropping {len(ambiguous)} mixed-class plant code(s), "
            f"unattributable at CAMPD facility level: {ambiguous})"
        )
    codes = set(mapping)

    # {(facility, unit): [per-year load arrays]} — pooled for the percentile
    # statistics, kept per year so runs never stitch across a vintage boundary.
    loads: dict[tuple[int, str], list[np.ndarray]] = {}
    names: dict[tuple[int, str], str] = {}
    for state in states_for_iso(iso):
        for year in years:
            path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                print(f"  (skip {path.name}: not on disk)")
                continue
            cols = [
                "facilityId",
                "facilityName",
                "unitId",
                "date",
                "hour",
                "grossLoad",
            ]
            if unit_type is not None:
                cols.append("unitType")
            df = pd.read_parquet(path, columns=cols)
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df[df["facilityId"].isin(codes)]
            if unit_type is not None and not df.empty:
                df = df[
                    df["unitType"].astype(str).str.strip().str.casefold()
                    == unit_type.casefold()
                ]
            if df.empty:
                continue
            if plant_basis:
                # Collapse the facility's units to one PLANT series BEFORE any
                # statistic is taken, so the p99.5/p5 pair describes the plant's
                # own configuration ladder (2x1 -> 1x1 -> off) instead of a
                # single turbine's turndown (caiso-135 §A).
                df = df.groupby(["facilityId", "date", "hour"], as_index=False).agg(
                    grossLoad=("grossLoad", "sum"),
                    facilityName=("facilityName", "first"),
                )
                df["unitId"] = "PLANT"
            df = df.sort_values(["facilityId", "unitId", "date", "hour"])
            for (fid, uid), g in df.groupby(["facilityId", "unitId"], sort=False):
                key = (int(fid), str(uid))
                load = g["grossLoad"].fillna(0.0).to_numpy(dtype=float)
                loads.setdefault(key, []).append(load)
                names[key] = str(g["facilityName"].iloc[0])

    if not loads:
        raise SystemExit(f"{iso}: no CAMPD hours found for {classes}")

    rows = []
    # Every individual run, kept per class so the class summary can report the
    # EXACT pooled distribution rather than a reconstruction from per-unit
    # medians. Each entry is (run_hours, unit HSL) so the same array serves the
    # unweighted and capacity-weighted percentiles.
    class_runs: dict[str, list[tuple[float, float]]] = {k: [] for k in classes}
    for key, chunks in loads.items():
        fid, uid = key
        pooled = np.concatenate(chunks)
        hsl = float(np.percentile(pooled, _HSL_PCTILE))
        if hsl <= _ONLINE_MW:
            continue  # never meaningfully online in the window
        thresh = max(_ONLINE_MW, _ONLINE_FRAC * hsl)
        on_pooled = pooled >= thresh
        if not on_pooled.any():
            continue
        lsl = float(np.percentile(pooled[on_pooled], _LSL_PCTILE))
        # Runs within each year, using the pooled-window threshold.
        run_lengths: list[int] = []
        for chunk in chunks:
            run_lengths.extend(unit_run_lengths(chunk >= thresh))
        arr = np.asarray(run_lengths, dtype=float)
        class_runs[mapping[fid]].extend((float(r), hsl) for r in run_lengths)
        rows.append(
            {
                "plant_code": fid,
                "unit_id": uid,
                "plant_name": names[key],
                "plant_class": mapping[fid],
                "hsl_mw": hsl,
                "lsl_mw": lsl,
                "lsl_frac": lsl / hsl,
                "online_hours": int(on_pooled.sum()),
                "total_hours": int(pooled.size),
                "online_frac": float(on_pooled.mean()),
                "n_runs": int(arr.size),
                "median_run_hours": float(np.median(arr)) if arr.size else float("nan"),
                "p75_run_hours": (
                    float(np.percentile(arr, 75)) if arr.size else float("nan")
                ),
            }
        )
    runs_out = {
        k: np.asarray(v, dtype=float).reshape(-1, 2) for k, v in class_runs.items()
    }
    return pd.DataFrame(rows), runs_out


def class_summary(
    units: pd.DataFrame,
    class_runs: dict[str, np.ndarray],
    iso: str,
    years: list[int],
    classes: tuple[str, ...] = TARGET_CLASSES,
    unit_type: str | None = None,
    plant_basis: bool = False,
) -> pd.DataFrame:
    """Aggregate the per-unit conduct table to one row per class.

    ``min_load_frac`` is the HSL-weighted p50 of the units' ``lsl_frac`` — the
    ERCOT cap-weighted-LSL/HSL-p50 aggregation, applied to the conduct-derived
    ratios.

    The run-length columns are reported BOTH ways, because the two answer
    different questions and differ by more than an order of magnitude on a
    class whose small units cycle hard:

    - ``run_hours_p*`` — the EQUALLY-WEIGHTED pooled distribution over every
      individual run. Dominated by the highest-cycling units: NYISO's ST_GAS
      class carries E F Barrett's 16-21 MW fast units (the model classes them
      ST_GAS at plant level), which contribute ~5,000 runs of 2-3 h and pull
      the pooled p50 to 3 h against a 585 MW Bowline unit's 38 h.
    - ``run_hours_p*_capwtd`` — the CAPACITY-weighted distribution (each run
      carries its unit's HSL). This is the population the bridge parameter is
      actually applied to (a min-run constraint floors committed MW, not
      committed unit-count), and it is the same weighting ``min_load_frac``
      uses, so it is the identification column.

    Both are written; neither is chosen here. Choosing a keeper value is the
    calibration lane's job and must cite this artifact (rule 23
    [R-FROZEN-DERIVE]). Note also that an OBSERVED run length is an upper-ish
    bound on a minimum-run CONSTRAINT — a unit that ran 60 h because it was
    economic does not prove a 60 h commitment floor — so the low percentiles
    (p10/p25) bound the constraint from the side the constraint lives on.
    """
    years_tag = "-".join(str(y) for y in years)
    out = []
    for klass in classes:
        sel = units[units["plant_class"] == klass]
        if sel.empty:
            continue
        w = sel["hsl_mw"].to_numpy(dtype=float)
        runs = class_runs.get(klass)
        rh = runs[:, 0] if runs is not None and runs.size else np.array([np.nan])
        rw = runs[:, 1] if runs is not None and runs.size else np.array([1.0])
        row = {
            "iso": iso,
            "plant_class": klass,
            "n_units": int(len(sel)),
            "n_plants": int(sel["plant_code"].nunique()),
            "capacity_mw": float(w.sum()),
            "min_load_frac": weighted_percentile(
                sel["lsl_frac"].to_numpy(), w, _CLASS_PCTILE
            ),
            "min_load_frac_p25": weighted_percentile(
                sel["lsl_frac"].to_numpy(), w, 25.0
            ),
            "min_load_frac_p75": weighted_percentile(
                sel["lsl_frac"].to_numpy(), w, 75.0
            ),
            "online_frac": float(sel["online_hours"].sum() / sel["total_hours"].sum()),
            "n_runs": int(rh.size),
        }
        for pct in (10, 25, 50, 75, 90):
            row[f"run_hours_p{pct}"] = float(np.percentile(rh, pct))
            row[f"run_hours_p{pct}_capwtd"] = weighted_percentile(rh, rw, float(pct))
        row["years"] = years_tag
        row["source"] = (
            "EPA CAMPD unit-level hourly grossLoad "
            f"(data/raw/campd-unit-level); HSL=p{_HSL_PCTILE} of pooled "
            f"load, online>=max({_ONLINE_MW} MW, {_ONLINE_FRAC}xHSL), "
            f"LSL=p{_LSL_PCTILE} of online-hour load, class min_load_frac = "
            f"capacity-weighted p{_CLASS_PCTILE} across units; run hours "
            "reported equally-weighted and capacity-weighted (see docstring)"
        )
        if unit_type is not None:
            row["source"] += f"; restricted to CAMPD unitType == '{unit_type}'"
        if plant_basis:
            row["source"] += f"; {PLANT_BASIS_NOTE}"
        out.append(row)
    return pd.DataFrame(out)


def main() -> None:
    """Derive and write the measured gas commitment-parameter artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, help="ISO name, e.g. NYISO")
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2023, 2024, 2025],
        help="CAMPD vintages to pool (default 2023 2024 2025)",
    )
    parser.add_argument("--out", default=None, help="Output CSV path override")
    parser.add_argument(
        "--detail",
        action="store_true",
        help="ALSO write the per-unit conduct table alongside the class summary",
    )
    parser.add_argument(
        "--ct",
        action="store_true",
        help="measure the fast-start CT_PEAKER class instead of the slow-start "
        "gas classes, restricted to CAMPD unitType 'Combustion turbine' so a "
        "mixed steam/turbine facility contributes only its turbines. Writes "
        "campd_ct_commitment_params_<ISO>.csv; the default invocation is "
        "unaffected and byte-identical.",
    )
    parser.add_argument(
        "--plant-basis",
        action="store_true",
        help="sum each facility's units to ONE plant series before measuring, so "
        "min_load_frac is the plant's minimum stable CONFIGURATION rather than a "
        "single turbine's turndown. Required by any consumer whose floor is "
        "multiplied by PLANT capacity (the CAISO RA must-offer bridge). Writes "
        "campd_gas_commitment_params_plant_<ISO>.csv; the default per-unit "
        "invocation is unaffected and byte-identical.",
    )
    args = parser.parse_args()
    iso = args.iso.upper()

    classes = CT_TARGET_CLASSES if args.ct else TARGET_CLASSES
    unit_type = CT_UNIT_TYPE if args.ct else None
    stem = "campd_ct_commitment_params" if args.ct else "campd_gas_commitment_params"
    if args.plant_basis:
        stem += "_plant"

    units, class_runs = unit_statistics(
        iso, args.years, classes, unit_type, args.plant_basis
    )
    summary = class_summary(
        units, class_runs, iso, args.years, classes, unit_type, args.plant_basis
    )
    if summary.empty:
        raise SystemExit(f"{iso}: no target-class units measured — nothing to write")

    out_path = Path(args.out) if args.out else (PROCESSED_DIR / f"{stem}_{iso}.csv")
    summary.to_csv(out_path, index=False)
    print(f"wrote {out_path} ({len(summary)} rows)")
    print(
        summary[
            [
                "plant_class",
                "n_units",
                "capacity_mw",
                "min_load_frac",
                "min_load_frac_p25",
                "min_load_frac_p75",
                "n_runs",
                "run_hours_p25",
                "run_hours_p50",
                "run_hours_p75",
                "run_hours_p25_capwtd",
                "run_hours_p50_capwtd",
                "run_hours_p75_capwtd",
            ]
        ].to_string(index=False)
    )
    if args.detail:
        detail_path = out_path.with_name(out_path.stem + "_units.csv")
        units.sort_values(["plant_class", "plant_code", "unit_id"]).to_csv(
            detail_path, index=False
        )
        print(f"wrote {detail_path} ({len(units)} unit rows)")


if __name__ == "__main__":
    main()
