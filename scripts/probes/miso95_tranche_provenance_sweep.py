"""Cross-ISO provenance sweep over the committed ``thermal_tranches_<ISO>.csv``.

Answers, per ISO and without re-reading a single CAMPD hour: does the committed
artifact's ``nameplate_mw`` column match the fleet the LP actually dispatches
(``apply_cc_summer_guard=True``), match only the un-guarded fleet, or neither?

Background (miso-95,
``results/calibration/FINDING-miso95-thermal-tranches-provenance-2026-07.md``):
``scripts/data/derive_thermal_tranches.py`` sources non-ERCOT nameplate from
:func:`market_sim.data.fleet.load_fleet_from_csv`, whose ``apply_cc_summer_guard``
default is ``True`` — the merchant-CC reconciliation
``fleet/eia860.py::_reconcile_cc_pmax_to_nameplate``. All five committed
artifacts predate that guard, so their tranche percentages carry an over-stated
denominator for every reconciled CC plant. Because the model applies the derived
percentage to the *guarded* (smaller) pmax, the resulting min-stable / must-run
floor is understated one-sided.

This probe is the cheap standing check for that condition: it is a pure artifact
diff, runs in seconds, touches nothing on disk, and re-answers the question after
any change to the guard or to a committed tranche artifact.

Usage:
    PYTHONPATH=$PWD python scripts/probes/miso95_tranche_provenance_sweep.py
    PYTHONPATH=$PWD python scripts/probes/miso95_tranche_provenance_sweep.py --iso MISO PJM
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import PROCESSED_DIR  # noqa: E402
from market_sim.data.fleet import load_campd_bins, load_fleet_from_csv  # noqa: E402

# ISOs holding a committed thermal_tranches_<ISO>.csv. ERCOT has none (it runs
# the CAMPD bin sheet directly), but is accepted so the sweep can report that.
_DEFAULT_ISOS = ("MISO", "PJM", "CAISO", "NYISO", "NEISO", "ERCOT")

# MW tolerance for calling a nameplate a match. The artifacts carry one decimal.
_TOL_MW = 0.05


def _capacity_map(iso: str, guard: bool) -> dict[tuple[int, str], float]:
    """Return ``{(plant_code, plant_group): nameplate_mw}`` for an ISO's fleet.

    Mirrors ``derive_thermal_tranches._fleet_nameplate_and_group`` exactly:
    ERCOT sums the CAMPD bin sheet, every other ISO sums the per-plant EIA-860
    fleet. ``guard`` selects whether the merchant-CC summer-capacity
    reconciliation is applied (it is ignored for ERCOT, which never runs it).
    """
    cap: dict[tuple[int, str], float] = collections.defaultdict(float)
    if iso == "ERCOT":
        bins = load_campd_bins("data/raw/reference/custom-bin-assignments.csv")
        for code, group, mw in zip(
            bins["Plant_Code"], bins["Plant_Group"], bins["capacity_mw"]
        ):
            if mw and float(mw) > 0:
                cap[(int(code), str(group))] += float(mw)
        return dict(cap)
    for gen in load_fleet_from_csv(
        iso, get_iso_config(iso), apply_cc_summer_guard=guard
    ):
        code = int(gen.plant_code)
        if code <= 0 or not gen.plant_group:
            continue
        cap[(code, gen.plant_group)] += float(gen.pmax_mw)
    return dict(cap)


def sweep_iso(iso: str) -> dict | None:
    """Report one ISO's tranche-artifact nameplate provenance, or ``None``.

    Returns a summary dict and prints the per-plant detail for every row whose
    nameplate matches the un-guarded fleet only — i.e. every plant whose tranche
    percentages were derived against a denominator the model no longer uses.
    """
    path = PROCESSED_DIR / f"thermal_tranches_{iso}.csv"
    if not path.exists():
        print(f"{iso:6s} no committed artifact")
        return None
    df = pd.read_csv(path)
    guarded = _capacity_map(iso, guard=True)
    unguarded = _capacity_map(iso, guard=False)

    n_guarded = n_unguarded_only = n_neither = 0
    overstated_mw = 0.0
    floor_gap_mw = 0.0
    detail: list[tuple[int, str, float, float, float]] = []
    for row in df.itertuples(index=False):
        key = (int(row.plant_code), str(row.plant_group))
        filed = float(row.nameplate_mw)
        model_mw = guarded.get(key)
        raw_mw = unguarded.get(key)
        if model_mw is not None and abs(model_mw - filed) < _TOL_MW:
            n_guarded += 1
        elif raw_mw is not None and abs(raw_mw - filed) < _TOL_MW:
            n_unguarded_only += 1
            if model_mw:
                overstated_mw += filed - model_mw
                # The tranche % was derived over `filed` but is applied to
                # `model_mw`, so the floor it sets is short by this much.
                ratio = filed / model_mw
                floor_gap_mw += (
                    (ratio - 1.0) * float(row.committed_pct) / 100.0 * model_mw
                )
                detail.append((key[0], key[1], filed, model_mw, ratio))
        else:
            n_neither += 1

    print(
        f"{iso:6s} rows={len(df):4d}  matches GUARDED(model)={n_guarded:4d}  "
        f"matches UNGUARDED only={n_unguarded_only:3d}  neither={n_neither:3d}  "
        f"overstated={overstated_mw:8,.1f} MW  understated committed floor="
        f"{floor_gap_mw:7,.0f} MW"
    )
    for code, group, filed, model_mw, ratio in detail:
        print(
            f"        {code:6d} {group:<12s} file {filed:8.1f} MW  "
            f"model fleet {model_mw:8.1f} MW  r={ratio:.3f}"
        )
    # Schema generation tells: a committed file missing a column the deriver now
    # writes predates that column, which dates the artifact without any numbers.
    return {
        "iso": iso,
        "rows": len(df),
        "guarded": n_guarded,
        "unguarded_only": n_unguarded_only,
        "neither": n_neither,
        "overstated_mw": overstated_mw,
        "floor_gap_mw": floor_gap_mw,
        "max_online_hours": int(df["online_hours"].max()),
        "columns": list(df.columns),
    }


def main() -> None:
    """Run the sweep over the requested ISOs and print the roll-up."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", nargs="+", default=list(_DEFAULT_ISOS))
    args = ap.parse_args()

    summaries = [s for s in (sweep_iso(i.upper()) for i in args.iso) if s]
    if not summaries:
        return
    print("\nschema generation (a missing column dates the artifact):")
    seen = set()
    for s in summaries:
        seen.update(s["columns"])
    for s in summaries:
        missing = sorted(seen - set(s["columns"]))
        print(
            f"  {s['iso']:6s} max online_hours={s['max_online_hours']:6d}  "
            f"missing={missing or '—'}"
        )
    print(
        f"\nTOTAL over-stated CC nameplate "
        f"{sum(s['overstated_mw'] for s in summaries):,.0f} MW; "
        f"understated committed floor "
        f"{sum(s['floor_gap_mw'] for s in summaries):,.0f} MW"
    )


if __name__ == "__main__":
    main()
