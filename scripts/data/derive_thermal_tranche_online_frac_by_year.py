"""Derive the PER-YEAR synchronization fraction behind the per-plant must-run window.

``scripts/data/derive_thermal_tranches.py`` publishes one ``online_frac`` per
``(plant_code, plant_group)``, measured over the POOLED multi-year CEMS window it
is invoked with (MISO's committed artifact: 2023-2025). The runtime consumes it
as the *window* of the per-plant must-run commitment floor — the top
``online_frac`` fraction of the SOLVE YEAR's hours, ranked by system load, in
which the plant's floor is held on (``data/fleet/arrays.py::_compose_min_gen_floors``,
``config.cc_mustrun_per_plant`` / ``st_gas_mustrun_per_plant`` /
``st_gas_mustrun_p25_level``).

The two grains do not match. A plant whose synchronization share MOVES across
the pooled window is committed in every solve year at its pooled average, so a
year it barely ran is over-committed and a year it ran hard is under-committed.
The live case is MISO plant 1402 (Little Gypsy): pooled 0.508 against per-year
0.2495 / 0.6134 / 0.6548, a ~2.3x over-commitment in 2023 that the C8 D-4
per-unit conduct rider convicts (the meter is dark in ~71 % of the hours the
floor asserts the plant must be online — rule 17 ``[R-FLOOR-WINDOW]`` verbatim).

This script publishes the SAME measurement at the grain the runtime applies it:
one row per ``(plant_code, plant_group, year)``.

Rule 23 ``[R-FROZEN-DERIVE]``: the frozen deriver is **NOT TOUCHED** — not one
byte, and its pooled artifact is not regenerated. The estimator here is
*imported* from it (``_SYNC_MW_NAMEPLATE_FRAC``, ``_THERMAL_GROUPS``,
``_ONLINE_FRAC_GROUPS``, ``_fleet_nameplate_and_group``,
``_parasitic_factor_map``) so it is provably the same statistic, not a
re-implementation: an hour counts when the plant's facility-summed CAMPD net MW
clears 1 % of nameplate, against the whole year as denominator. What changes is
the reporting GRAIN, not any value: summing this file's ``sync_hours`` and
``total_hours`` over the pooled years reproduces the committed ``online_frac``
exactly (asserted by ``--verify-pooled``). Nothing here responds to a price or
volume residual; the trigger is a measured window/driver mismatch.

Usage:
    python3 scripts/data/derive_thermal_tranche_online_frac_by_year.py \
        --iso MISO --years 2023 2024 2025 [--verify-pooled] [--out PATH]

Output: ``data/raw/_processed-legacy/thermal_tranches_online_frac_by_year_<ISO>.csv``
with columns ``plant_code, plant_group, year, nameplate_mw, sync_hours,
total_hours, online_frac`` (``online_frac`` rounded to 3 dp, exactly as the
pooled column is).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import PROCESSED_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402

# Package import, not a spec_from_file_location file-load (refactor plan §6-E):
# a private copy of the deriver could drift from the canonical one, which would
# defeat the whole point of importing the estimator rather than restating it.
from scripts.data import derive_thermal_tranches as dtt  # noqa: E402


def per_year_online_frac(iso: str, years: list[int]) -> pd.DataFrame:
    """Return the per-year synchronization fraction for ``iso``'s thermal plants.

    One row per ``(plant_code, plant_group, year)`` for every group the frozen
    deriver publishes ``online_frac`` for (:data:`derive_thermal_tranches.
    _ONLINE_FRAC_GROUPS`). The plant's facility-summed CAMPD net is attributed to
    its PRIMARY group only, exactly as the pooled deriver does — a secondary-group
    row at a multi-group plant has no separable CEMS series and is left out.
    """
    cap, primary = dtt._fleet_nameplate_and_group(iso)
    factors = dtt._parasitic_factor_map()
    states = campd.states_for_iso(iso)
    if not states:
        raise SystemExit(f"no CAMPD states registered for ISO {iso!r}")

    rows: list[dict] = []
    for year in years:
        df = campd.load_campd_hourly(states, [year])
        if df.empty:
            print(f"  (no CAMPD for {iso} {year})")
            continue
        net = campd.plant_hourly_net(df, factors, year)  # {code: (8760,) net MW}
        for (code, group), nameplate in sorted(cap.items()):
            if group not in dtt._THERMAL_GROUPS or nameplate <= 0:
                continue
            if group not in dtt._ONLINE_FRAC_GROUPS:
                continue
            if primary.get(code) != group:
                continue
            series = net.get(code)
            if series is None:
                continue
            # THE FROZEN ESTIMATOR, imported: any unit synchronized == the
            # facility net clears 1 % of nameplate; denominator is the whole
            # year (the net series carries zeros for offline hours, so a plant
            # dark for a stretch genuinely scores below 1.0).
            sync = series > dtt._SYNC_MW_NAMEPLATE_FRAC * nameplate
            n_sync, n_tot = int(sync.sum()), int(len(series))
            rows.append(
                {
                    "plant_code": int(code),
                    "plant_group": str(group),
                    "year": int(year),
                    "nameplate_mw": round(float(nameplate), 1),
                    "sync_hours": n_sync,
                    "total_hours": n_tot,
                    "online_frac": round(min(1.0, n_sync / n_tot), 3)
                    if n_tot > 0
                    else "",
                }
            )
    return pd.DataFrame(rows)


def verify_against_pooled(iso: str, by_year: pd.DataFrame) -> int:
    """Check that pooling this file's counts reproduces the committed artifact.

    Returns the number of MISMATCHED rows (0 = the grain refinement is exact).
    Rows absent from either side are reported but not counted as mismatches —
    the committed artifact may predate a group joining ``_ONLINE_FRAC_GROUPS``,
    and a ``rarely_online`` row publishes no fraction at all.
    """
    path = PROCESSED_DIR / f"thermal_tranches_{iso.upper()}.csv"
    if not path.exists():
        print(f"  (no pooled artifact at {path} — nothing to verify against)")
        return 0
    pooled = pd.read_csv(path)
    if "online_frac" not in pooled.columns:
        print("  (pooled artifact predates the online_frac column)")
        return 0
    agg = by_year.groupby(["plant_code", "plant_group"], as_index=False)[
        ["sync_hours", "total_hours"]
    ].sum()
    agg["pooled_from_by_year"] = (agg.sync_hours / agg.total_hours).clip(upper=1.0)
    ref = {
        (int(r.plant_code), str(r.plant_group)): r.online_frac
        for r in pooled.itertuples(index=False)
        if str(getattr(r, "status", "ok")) == "ok"
    }
    bad = 0
    missing = 0
    for r in agg.itertuples(index=False):
        want = ref.get((int(r.plant_code), str(r.plant_group)))
        try:
            want_f = float(want)
        except (TypeError, ValueError):
            missing += 1
            continue
        if not want_f == want_f:  # NaN
            missing += 1
            continue
        got = round(float(r.pooled_from_by_year), 3)
        if abs(got - want_f) > 5e-4:
            bad += 1
            print(
                f"  MISMATCH {int(r.plant_code)} {r.plant_group}: "
                f"pooled-from-by-year {got} vs committed {want_f}"
            )
    print(
        f"  verify-pooled: {len(agg) - bad - missing} exact, {bad} mismatched, "
        f"{missing} absent from the committed artifact"
    )
    return bad


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="MISO")
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--out", default=None)
    ap.add_argument(
        "--verify-pooled",
        action="store_true",
        help="assert that pooling the derived counts reproduces the committed "
        "thermal_tranches_<ISO>.csv online_frac column (grain refinement, not "
        "a value change)",
    )
    args = ap.parse_args()

    iso = args.iso.upper()
    print(f"Deriving per-year online_frac for {iso}, years {args.years}")
    df = per_year_online_frac(iso, sorted(args.years))
    if df.empty:
        raise SystemExit("no rows derived")

    if args.verify_pooled:
        bad = verify_against_pooled(iso, df)
        if bad:
            raise SystemExit(
                f"{bad} row(s) do not reproduce the committed pooled fraction — "
                "the grain refinement is NOT exact; do not ship this artifact"
            )

    out = (
        Path(args.out)
        if args.out
        else (PROCESSED_DIR / f"thermal_tranches_online_frac_by_year_{iso}.csv")
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    df.sort_values(["plant_code", "plant_group", "year"]).to_csv(out, index=False)
    n_moved = 0
    for _, g in df.groupby(["plant_code", "plant_group"]):
        vals = pd.to_numeric(g.online_frac, errors="coerce").dropna()
        if len(vals) > 1 and float(np.ptp(vals.to_numpy())) >= 0.10:
            n_moved += 1
    print(
        f"Wrote {out} — {len(df)} rows, "
        f"{df[['plant_code', 'plant_group']].drop_duplicates().shape[0]} plants, "
        f"{n_moved} with a >=0.10 spread across years"
    )


if __name__ == "__main__":
    main()
