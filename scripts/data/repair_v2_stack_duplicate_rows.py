"""Surgically merge CAMPD stack-duplicate unit rows in ``plant_emission_rates_v2``.

**Why this exists instead of a re-derive.** The committed artifact
``data/raw/_processed-legacy/plant_emission_rates_v2.parquet`` carries
2018-2026, and ``derive_plant_emissions_v2.py``'s default path is a REPLACE,
not a merge (``out = derive(args.years, isos)``). Re-deriving it would silently
destroy two classes of row that cannot be rebuilt:

* every **2018** row — CLAUDE.md rule 22 dropped 2018 from
  ``regenerate_clean``, so ``emissions-unit-annual`` is no longer built for it; and
* the **2022 / 2026** holdout-intake rows, which ``--holdout-intake`` states
  "may only run once (rule 22)" and are therefore unrepeatable by construction.

The hazard is pre-existing and applies to any change touching this artifact
(``FINDING-nyiso141-astoria-stack-duplication-2026-08-17.md`` §4.2). This
driver takes the admissible route: it rewrites ONLY the rows of the facilities
named in :data:`campd.CAMPD_STACK_DUPLICATE_UNITS` and asserts every other row
survives byte-identically — the same discipline ``--holdout-intake`` already
applies to its own merge.

**What the merge is.** A common-generator stack pair is ONE generating unit
monitored on two flue paths: CAMPD repeats the generator's full ``grossLoad``
on both rows while splitting heat and the emission masses between them
(identification: the finding above, three independent channels). At the unit
grain ``curate_emissions_unit_annual._normalize_unit_hourly`` re-labels the
duplicate onto its primary and masks its repeated gross, so the group-by sums
the pair into the one generator it is. This driver reproduces that same
aggregation directly on the annual rows:

===================== ==========================================================
field                 merged value
===================== ==========================================================
``gross_mwh``         the PRIMARY's (the duplicate's is the same number, repeated)
``heat_mmbtu``        primary + duplicate (genuinely per-path — must keep summing)
``co2_kg`` / NOx / SO2 primary + duplicate, on the same grounds
``steam_load_klbh_sum`` primary + duplicate
``op_hours``/``starts`` the PRIMARY's — the duplicate's masked gross contributes
                      no online hour and no off->on transition
``net_mwh``/rates      re-derived from the merged mass and gross on the
                      artifact's own basis (``net = gross x parasitic_factor``)
===================== ==========================================================

Zero new degrees of freedom (rule 21 ``[R-DOF]``): no parameter, no coefficient,
no threshold — it is a row-identity correction.

Usage::

    python scripts/data/repair_v2_stack_duplicate_rows.py --check   # report only
    python scripts/data/repair_v2_stack_duplicate_rows.py           # rewrite
    python scripts/data/repair_v2_stack_duplicate_rows.py --validate-against-clean
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
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from market_sim.config import paths  # noqa: E402
from market_sim.data import campd  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("repair_v2_stack_duplicate_rows")

PROCESSED_DIR = paths.RAW_DATA_DIR / "_processed-legacy"
OUT_PATH = PROCESSED_DIR / "plant_emission_rates_v2.parquet"
CSV_PATH = PROCESSED_DIR / "plant_emission_rates_v2.csv"

_KEY = ["iso", "plant_id", "unit_id", "year"]
# Rounding grid of derive_plant_emissions_v2._OUT_COLUMNS, reproduced so a
# repaired row is indistinguishable from a re-derived one.
_ROUND = {
    "gross_mwh": 3,
    "net_mwh": 3,
    "parasitic_factor": 6,
    "heat_mmbtu": 3,
    "co2_kg": 3,
    "co2_kg_per_mwh_net": 6,
    "nox_kg": 3,
    "nox_kg_per_mwh_net": 6,
    "so2_kg": 3,
    "so2_kg_per_mwh_net": 6,
    "steam_load_klbh_sum": 3,
}
_SUMMED = ("heat_mmbtu", "co2_kg", "nox_kg", "so2_kg", "steam_load_klbh_sum")


def _merge_group(primary: pd.Series, dups: list[pd.Series]) -> pd.Series:
    """Return the merged annual row for one (iso, plant, primary unit, year)."""
    out = primary.copy()
    for col in _SUMMED:
        out[col] = round(
            float(primary[col]) + sum(float(d[col]) for d in dups), _ROUND[col]
        )
    # gross/op_hours/starts stay the primary's: the duplicate's gross is masked
    # upstream, so it contributes no MWh, no online hour and no start.
    factor = float(primary["parasitic_factor"])
    net = round(float(out["gross_mwh"]) * factor, _ROUND["net_mwh"])
    out["net_mwh"] = net
    for mass in ("co2_kg", "nox_kg", "so2_kg"):
        rate = mass.replace("_kg", "_kg_per_mwh_net")
        out[rate] = round(float(out[mass]) / net, _ROUND[rate]) if net > 0 else 0.0
    return out


def repair(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return ``(repaired_frame, audit_frame)`` for the whole artifact.

    ``audit_frame`` carries one row per merged unit-year with the before/after
    CO2 intensity, so the caller can check it against the finding's target
    table without re-reading the parquet.
    """
    pairs = campd.CAMPD_STACK_DUPLICATE_UNITS
    if not pairs:
        return df.copy(), pd.DataFrame()

    touched = df["plant_id"].isin(pairs.keys())
    frozen = df[~touched].reset_index(drop=True)
    work = df[touched].copy()

    audit_rows: list[dict] = []
    merged_rows: list[pd.Series] = []
    for (iso, plant_id, year), grp in work.groupby(
        ["iso", "plant_id", "year"], sort=True
    ):
        mapping = pairs[int(plant_id)]
        by_unit = {str(r["unit_id"]): r for _, r in grp.iterrows()}
        consumed: set[str] = set()
        for unit_id, row in by_unit.items():
            if unit_id in mapping:  # a duplicate — folded into its primary below
                continue
            dups = [
                by_unit[d]
                for d, prim in mapping.items()
                if prim == unit_id and d in by_unit
            ]
            if not dups:
                merged_rows.append(row)
                continue
            # The simple sum is only valid when every leg carries the same CO2
            # basis; a mixed basis would need _co2_annual's re-scaling, which
            # cannot be reconstructed from annual rows. Fail loudly instead.
            bases = {str(row["co2_source"]), *(str(d["co2_source"]) for d in dups)}
            if len(bases) != 1:
                raise ValueError(
                    f"mixed co2_source {sorted(bases)} for {iso} {plant_id} "
                    f"{unit_id} {year}: not reconstructible from annual rows"
                )
            new = _merge_group(row, dups)
            merged_rows.append(new)
            consumed |= {str(d["unit_id"]) for d in dups}
            audit_rows.append(
                {
                    "iso": iso,
                    "plant_id": int(plant_id),
                    "unit_id": unit_id,
                    "year": int(year),
                    "dropped": ",".join(
                        sorted(consumed & {str(d["unit_id"]) for d in dups})
                    ),
                    "gross_mwh": float(new["gross_mwh"]),
                    "co2_rate_old": float(row["co2_kg_per_mwh_net"]),
                    "co2_rate_new": float(new["co2_kg_per_mwh_net"]),
                }
            )

    out = (
        pd.concat([frozen, pd.DataFrame(merged_rows)], ignore_index=True)
        .sort_values(_KEY)
        .reset_index(drop=True)
    )
    return out[df.columns], pd.DataFrame(audit_rows)


def assert_untouched_frozen(before: pd.DataFrame, after: pd.DataFrame) -> None:
    """Raise unless every row outside the stack-duplicate facilities is identical."""
    ids = set(campd.CAMPD_STACK_DUPLICATE_UNITS)
    b = before[~before["plant_id"].isin(ids)].sort_values(_KEY).reset_index(drop=True)
    a = after[~after["plant_id"].isin(ids)].sort_values(_KEY).reset_index(drop=True)
    if not b.equals(a):
        raise AssertionError(
            f"non-stack-duplicate rows changed: {len(b)} before vs {len(a)} after"
        )
    logger.info("byte-freeze OK: %d non-stack-duplicate rows identical", len(b))


def validate_against_clean(after: pd.DataFrame) -> pd.DataFrame:
    """Re-derive the touched rows from ``emissions-unit-annual`` and compare.

    The clean tree is the ground truth this repair reproduces by arithmetic;
    where a year is still buildable, the two must agree. Years the clean tree
    cannot cover (2018, and the quarantined 2022/2026) are reported as
    ``no-clean`` — they are exactly the rows the surgical route exists for.
    """
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))
    from scripts.data.derive_plant_emissions_v2 import derive

    ids = set(campd.CAMPD_STACK_DUPLICATE_UNITS)
    rows = []
    for (iso, year), grp in after[after["plant_id"].isin(ids)].groupby(
        ["iso", "year"], sort=True
    ):
        try:
            ref = derive([int(year)], [str(iso)])
        except Exception as exc:  # noqa: BLE001
            rows.append({"iso": iso, "year": int(year), "verdict": f"ERR {exc}"})
            continue
        ref = ref[ref["plant_id"].isin(ids)]
        if ref.empty:
            rows.append({"iso": iso, "year": int(year), "verdict": "no-clean"})
            continue
        m = grp.merge(ref, on=_KEY, how="outer", suffixes=("_repaired", "_clean"))
        diffs = []
        for col in _ROUND:
            a, b = m.get(f"{col}_repaired"), m.get(f"{col}_clean")
            if a is None or b is None:
                continue
            d = (a.astype(float) - b.astype(float)).abs().max()
            if pd.notna(d) and d > 0.01:
                diffs.append(f"{col} max|d|={d:.4f}")
        for col in ("starts", "op_hours"):
            a, b = m.get(f"{col}_repaired"), m.get(f"{col}_clean")
            if a is None or b is None:
                continue
            d = (a.astype(float) - b.astype(float)).abs().max()
            if pd.notna(d) and d > 0:
                diffs.append(f"{col} max|d|={d:.0f}")
        rows.append(
            {
                "iso": iso,
                "year": int(year),
                "verdict": "MATCH" if not diffs else "; ".join(diffs),
                "rows": len(m),
            }
        )
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report only, do not write")
    ap.add_argument(
        "--validate-against-clean",
        action="store_true",
        help="re-derive the touched rows from emissions-unit-annual and compare",
    )
    args = ap.parse_args(argv)

    before = pd.read_parquet(OUT_PATH)
    after, audit = repair(before)
    assert_untouched_frozen(before, after)

    logger.info(
        "rows %d -> %d (%d duplicate rows folded onto their primaries)",
        len(before),
        len(after),
        len(before) - len(after),
    )
    if not audit.empty:
        print("\nMERGED UNIT-YEARS (co2_kg_per_mwh_net, old -> new):")
        print(audit.to_string(index=False))

    if args.validate_against_clean:
        print("\nVALIDATION vs freshly curated emissions-unit-annual:")
        print(validate_against_clean(after).to_string(index=False))

    if args.check:
        logger.info("--check: nothing written")
        return 0
    after.to_parquet(OUT_PATH, index=False)
    after.to_csv(CSV_PATH, index=False)
    logger.info("wrote %s and %s", OUT_PATH, CSV_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
