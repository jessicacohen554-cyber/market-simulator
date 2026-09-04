"""Derive the v2 per-plant CO2-rate artifact from ``emissions-unit-annual``.

The v2 artifact (``data/raw/_processed-legacy/plant_emission_rates_v2.parquet``)
is keyed ``(iso, plant_id, unit_id, year)`` with **per-year rows only** — no
baked pooled ``year == 0`` row (the forward estimator pools at consumption time;
see ``docs/handoffs/emissions-co2-rate-plan-2026-07.md`` §2/§4) and **no
quarantined 2022/H1-2026 rows** (CLAUDE.md rule 22). Unit grain is the whole
point: it dissolves the old mixed coal/gas facility exclusion — a plant that
retires a unit (or a Parish-style coal+gas facility) gets a forward rate from the
surviving/matching units via the estimator's composition mask.

Net conversion follows the existing parasitic factors
(``compute_parasitic_factors`` / ``parasitic_load_factors.parquet``): station
service is a plant-level quantity, so each unit inherits its plant's factor and
``net_mwh_unit = gross_mwh_unit × factor``. For years the parasitic file does not
cover yet (2018-2021), extend it first with EIA-923 those years
(``scripts/data/derive_parasitic_load.py``); missing factors fall back to the plant's
pooled factor, then 1.0.

Columns: iso, plant_id, unit_id, year, primary_fuel, unit_type, gross_mwh,
net_mwh, parasitic_factor, heat_mmbtu, co2_kg, co2_kg_per_mwh_net, co2_source,
nox_kg, nox_kg_per_mwh_net, so2_kg, so2_kg_per_mwh_net, starts, op_hours,
steam_load_klbh_sum (the CEMS steam-output signature the CHP class-CF helper
keys off — EM-7 / plan §5 R5).

NOx/SO2 masses come straight from the annual datatype (``nox_kg`` / ``so2_kg``)
and their per-net-MWh intensities are derived on the same net basis as CO2 (the
NOx/SO2 full-wiring wave, plan §5 R7 / §7). NOx/SO2 are *secondary* to CO2 — the
CO2 columns and their derivation are unchanged here.

Usage:
    python scripts/data/derive_plant_emissions_v2.py                 # all ISOs, all years
    python scripts/data/derive_plant_emissions_v2.py --iso ERCOT --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from market_sim.config import paths  # noqa: E402
from market_sim.config.iso_configs import SUPPORTED_ISOS  # noqa: E402
from market_sim.data import campd  # noqa: E402
from scripts.lib import clean_io  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("derive_plant_emissions_v2")

QUARANTINED_YEARS = frozenset({2022, 2026})
PROCESSED_DIR = paths.RAW_DATA_DIR / "_processed-legacy"
PARASITIC_PATH = PROCESSED_DIR / "parasitic_load_factors.parquet"
OUT_PATH = PROCESSED_DIR / "plant_emission_rates_v2.parquet"
CSV_PATH = PROCESSED_DIR / "plant_emission_rates_v2.csv"

# Canonical registry order (iso_configs.SUPPORTED_ISOS). Output is fanned out
# over every ISO of an overlapping state and then sorted by ["iso", ...], so the
# derived artifact is invariant to this order (rule 26 preserved); the tuple only
# drives which ISOs the state map covers and the --iso default.
ALL_ISOS = SUPPORTED_ISOS

_OUT_COLUMNS = [
    "iso",
    "plant_id",
    "unit_id",
    "year",
    "primary_fuel",
    "unit_type",
    "gross_mwh",
    "net_mwh",
    "parasitic_factor",
    "heat_mmbtu",
    "co2_kg",
    "co2_kg_per_mwh_net",
    "co2_source",
    "nox_kg",
    "nox_kg_per_mwh_net",
    "so2_kg",
    "so2_kg_per_mwh_net",
    "starts",
    "op_hours",
    "steam_load_klbh_sum",
]


def _parasitic_maps() -> tuple[dict[tuple[int, int], float], dict[int, float]]:
    """Return ``({(plant,year): factor}, {plant: pooled_factor})``."""
    if not PARASITIC_PATH.exists():
        logger.warning(
            "no parasitic factors at %s; using 1.0 (gross==net)", PARASITIC_PATH
        )
        return {}, {}
    df = pd.read_parquet(PARASITIC_PATH)
    per = {
        (int(r.plant_id), int(r.year)): float(r.parasitic_factor)
        for r in df[df["year"] != 0].itertuples(index=False)
    }
    return per, campd.pooled_factor_map(df)


def _state_to_isos() -> dict[str, list[str]]:
    """Return ``{state: [iso, ...]}`` from campd.ISO_STATES (states overlap ISOs)."""
    out: dict[str, list[str]] = {}
    for iso in ALL_ISOS:
        for st in campd.states_for_iso(iso):
            out.setdefault(st, []).append(iso)
    return out


def derive(
    years: list[int], isos: list[str], allow_quarantined: bool = False
) -> pd.DataFrame:
    """Build the v2 artifact frame for ``years`` × ``isos`` from the annual data.

    ``allow_quarantined`` is set ONLY by the ``--holdout-intake`` path (the
    marker-gated one-shot holdout validation, CLAUDE.md rule 22); the default
    keeps 2022/H1-2026 out of the artifact.
    """
    per_paras, pooled_paras = _parasitic_maps()
    state_isos = _state_to_isos()
    want_states = {st for iso in isos for st in campd.states_for_iso(iso)}

    frames = []
    for year in years:
        if year in QUARANTINED_YEARS and not allow_quarantined:
            logger.warning("skipping quarantined year %d (rule 22)", year)
            continue
        if not clean_io.clean_exists("emissions-unit-annual", year=year):
            logger.warning(
                "no emissions-unit-annual for %d; curate it first "
                "(scripts/data/curate_emissions_unit_annual.py)",
                year,
            )
            continue
        a = clean_io.read_clean("emissions-unit-annual", year=year, validate=False)
        a = a[a["state"].astype(str).isin(want_states)].copy()
        frames.append(a)
    if not frames:
        return pd.DataFrame(columns=_OUT_COLUMNS)
    annual = pd.concat(frames, ignore_index=True)

    def _factor(plant_id: int, year: int) -> float:
        return per_paras.get(
            (int(plant_id), int(year)), pooled_paras.get(int(plant_id), 1.0)
        )

    annual["parasitic_factor"] = [
        _factor(p, y) for p, y in zip(annual["plant_id"], annual["year"])
    ]
    annual["net_mwh"] = annual["gross_mwh"].astype(float) * annual["parasitic_factor"]
    # NOx/SO2 masses are nullable in the annual datatype (a unit reporting no
    # pollutant monitor); treat missing as zero so the net-basis intensity is
    # well-defined and gas units keep their legitimate ~0 SO2.
    annual["nox_kg"] = annual["nox_kg"].fillna(0.0).astype(float)
    annual["so2_kg"] = annual["so2_kg"].fillna(0.0).astype(float)
    for mass in ("co2_kg", "nox_kg", "so2_kg"):
        rate = mass.replace("_kg", "_kg_per_mwh_net")
        annual[rate] = [
            (float(m) / float(n)) if n > 0 else 0.0
            for m, n in zip(annual[mass], annual["net_mwh"])
        ]

    # Fan out to one row per (iso, plant_id, unit_id, year): a plant in a state
    # shared by two ISOs appears under both; downstream each ISO's fleet build
    # filters to its own plant codes.
    rows = []
    for r in annual.itertuples(index=False):
        for iso in state_isos.get(str(r.state), []):
            if iso not in isos:
                continue
            rows.append(
                {
                    "iso": iso,
                    "plant_id": int(r.plant_id),
                    "unit_id": str(r.unit_id),
                    "year": int(r.year),
                    "primary_fuel": str(r.primary_fuel),
                    "unit_type": str(r.unit_type),
                    "gross_mwh": round(float(r.gross_mwh), 3),
                    "net_mwh": round(float(r.net_mwh), 3),
                    "parasitic_factor": round(float(r.parasitic_factor), 6),
                    "heat_mmbtu": round(float(r.heat_mmbtu), 3),
                    "co2_kg": round(float(r.co2_kg), 3),
                    "co2_kg_per_mwh_net": round(float(r.co2_kg_per_mwh_net), 6),
                    "co2_source": str(r.co2_source),
                    "nox_kg": round(float(r.nox_kg), 3),
                    "nox_kg_per_mwh_net": round(float(r.nox_kg_per_mwh_net), 6),
                    "so2_kg": round(float(r.so2_kg), 3),
                    "so2_kg_per_mwh_net": round(float(r.so2_kg_per_mwh_net), 6),
                    "starts": int(r.starts),
                    "op_hours": int(r.op_hours),
                    "steam_load_klbh_sum": round(float(r.steam_load_klbh_sum), 3),
                }
            )
    out = pd.DataFrame(rows, columns=_OUT_COLUMNS)
    return out.sort_values(["iso", "plant_id", "unit_id", "year"]).reset_index(
        drop=True
    )


def _calibration_complete_isos() -> set[str]:
    """Return ISOs marked calibration-complete (uppercased) — the rule-22 gate."""
    marker = (
        paths.REPO_ROOT / "frontend" / "data" / "backcast" / "calibration-complete.json"
    )
    try:
        import json

        data = json.loads(marker.read_text())
    except (OSError, ValueError):
        return set()
    return {str(k).upper() for k in (data.get("complete") or {})}


def _intake_authorized_isos() -> set[str]:
    """Return ISOs with a logged rule-22 data-intake authorization (uppercased).

    Rule 22 (Option 2) permits out-of-training DATA INTAKE for any ISO under
    explicit, session-logged owner authorization — a channel *separate* from the
    calibration-complete marker, which gates only solve / score / dashboard
    registration. Every ISO named in an ``intake_log`` entry has been through such
    an authorization, so ``--holdout-intake`` may extend the artifact on that
    logged authorization alone; the marker is NOT required for data readiness (it
    remains required before any out-of-training solve/score/register).
    """
    marker = (
        paths.REPO_ROOT / "frontend" / "data" / "backcast" / "calibration-complete.json"
    )
    try:
        import json

        log = json.loads(marker.read_text()).get("intake_log") or []
    except (OSError, ValueError):
        return set()
    import re

    known = {"ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"}
    authorized: set[str] = set()
    for entry in log:
        text = " ".join(str(entry.get(k, "")) for k in ("scope", "by"))
        authorized |= {iso for iso in known if re.search(rf"\b{iso}\b", text)}
    return authorized


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", nargs="+", default=list(ALL_ISOS))
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument(
        "--merge",
        action="store_true",
        help="year-scoped merge into the existing artifact: replace only the "
        "(iso, year) rows this run derives and carry every other row through "
        "byte-frozen (other ISOs, other years, the quarantined-year intakes). "
        "Default: the whole artifact is rewritten from --iso x --years, which "
        "drops any row outside that product. Use --merge to re-derive one "
        "ISO's rows after a source or routing change (rule 23) without "
        "touching the rest.",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="write the parquet here (and its .csv sibling) instead of the "
        "committed artifact path — for an A/B arm derived alongside the "
        "committed control (the merge base is still the committed artifact).",
    )
    ap.add_argument(
        "--holdout-intake",
        default=None,
        metavar="ISO",
        help="authorize extending the artifact with quarantined-year (2022/2026) "
        "rows for this ISO only (requires its calibration-complete marker OR a "
        "logged intake_log authorization; CLAUDE.md rule 22 — data intake, not "
        "solve). In this mode --years must be quarantined years only and --iso "
        "must equal the named ISO; the new rows are MERGED into the existing "
        "artifact with every pre-existing row asserted byte-frozen.",
    )
    args = ap.parse_args(argv)

    bad = [y for y in args.years if y in QUARANTINED_YEARS]
    if bad and not args.holdout_intake:
        ap.error(f"quarantined years cannot enter the artifact: {bad} (rule 22)")

    if args.holdout_intake:
        iso = args.holdout_intake.upper()
        complete = _calibration_complete_isos()
        authorized = _intake_authorized_isos()
        if iso not in complete and iso not in authorized:
            ap.error(
                f"{iso} has neither a calibration-complete marker nor a logged "
                f"intake_log authorization (complete: {sorted(complete) or 'none'}"
                f"; intake-authorized: {sorted(authorized) or 'none'}); rule 22 "
                "data intake needs one or the other"
            )
        if [i.upper() for i in args.iso] != [iso]:
            ap.error(f"--holdout-intake {iso} requires --iso {iso} (and only it)")
        if not bad or set(args.years) - QUARANTINED_YEARS:
            ap.error(
                "--holdout-intake extends the artifact with quarantined years "
                "only; run the default path for in-sample years"
            )
        new = derive(args.years, [iso], allow_quarantined=True)
        if new.empty:
            logger.error("no rows derived — curate emissions-unit-annual first")
            return 1
        existing = pd.read_parquet(OUT_PATH)
        clash = existing[(existing["iso"] == iso) & existing["year"].isin(args.years)]
        if not clash.empty:
            logger.error(
                "artifact already carries %d (%s, %s) rows — the one-shot "
                "holdout intake may only run once (rule 22)",
                len(clash),
                iso,
                sorted(set(args.years)),
            )
            return 1
        merged = (
            pd.concat([existing, new], ignore_index=True)
            .sort_values(["iso", "plant_id", "unit_id", "year"])
            .reset_index(drop=True)
        )
        # Every pre-existing row must survive byte-identically (frozen).
        refrozen = (
            merged.merge(new, how="left", indicator=True)
            .query("_merge == 'left_only'")
            .drop(columns="_merge")
            .reset_index(drop=True)
        )
        frozen_ok = refrozen.equals(
            existing.sort_values(["iso", "plant_id", "unit_id", "year"]).reset_index(
                drop=True
            )
        )
        if not frozen_ok:
            logger.error("pre-existing artifact rows changed — refusing to write")
            return 1
        out = merged
    else:
        out = derive(args.years, [i.upper() for i in args.iso])
        if out.empty:
            logger.error("no rows derived — curate emissions-unit-annual first")
            return 1
        if args.merge:
            if not OUT_PATH.exists():
                ap.error(f"--merge needs an existing artifact at {OUT_PATH}")
            existing = pd.read_parquet(OUT_PATH)
            derived_keys = set(zip(out["iso"].astype(str), out["year"].astype(int)))
            keep_mask = [
                (str(i), int(y)) not in derived_keys
                for i, y in zip(existing["iso"], existing["year"])
            ]
            kept = existing[keep_mask]
            logger.info(
                "--merge: replacing %d (iso, year) block(s) [%s]; carrying %d of "
                "%d pre-existing rows through byte-frozen",
                len(derived_keys),
                ", ".join(f"{i}:{y}" for i, y in sorted(derived_keys)),
                len(kept),
                len(existing),
            )
            out = (
                pd.concat([kept, out], ignore_index=True)
                .sort_values(["iso", "plant_id", "unit_id", "year"])
                .reset_index(drop=True)
            )
    pq_path = args.out if args.out is not None else OUT_PATH
    csv_path = pq_path.with_suffix(".csv") if args.out is not None else CSV_PATH
    pq_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(pq_path, index=False)
    out.to_csv(csv_path, index=False)
    logger.info(
        "wrote %s: %d rows, %d plants, ISOs %s, years %s",
        pq_path,
        len(out),
        out["plant_id"].nunique(),
        sorted(out["iso"].unique()),
        sorted(out["year"].unique()),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
