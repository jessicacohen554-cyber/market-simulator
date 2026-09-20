"""Phase-0 census: which CAISO plants carry a MECH_CHP_STEAM floor, and what
does their own meter say they were doing in the floored hours.

ZERO LP (rule 32 ``[R-SHARD]`` (a) — the parent never solves). Two halves:

1. **The model side** — rebuild the keeper's fleet for each solved year through
   the SANCTIONED :func:`scripts.lib.bundle_fleet.reconstruct_bundle_fleet`
   (which carries ``replay_keeper.DERIVED_RUN_YEAR_INPUTS``, caiso-292) and read
   ``chp_grid_pmin_mw`` per LP unit. That attribute is the sole source of
   ``MECH_CHP_STEAM`` (``fleet/arrays.py`` -- ``min_gen[g, :] = pmin_mw`` flat
   across all 8760 hours), so the census is exact rather than inferred.

2. **The meter side** — the same plants' CAMPD hourly gross load for the same
   year: on-frequency (share of hours with output > 0) and the p50 capacity
   factor conditional on being online.

The two halves answer the rule 17 ``[R-FLOOR-WINDOW]`` question the keeper's
committed D-4 rows raise: the floor asserts the unit is online in every hour of
the year, and for seven plants the meter reads zero in 76-99 % of the hours it
actually binds.

Run: ``PYTHONPATH=.:src python scripts/probes/caiso293_chp_steam_floor_census.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.lib.bundle_fleet import ensure_probe_path, reconstruct_bundle_fleet  # noqa: E402

ensure_probe_path()

BUNDLE = REPO / "results/calibration/xiso8_leftedge_span"
YEARS = (2022, 2023, 2024, 2025)
OUT = REPO / "results/calibration/_caiso293_chp_floor_census.json"

#: The seven plants the keeper's committed ``legitimacy_diagnostics.json``
#: fails D-4 on (all ``chp_steam``, all four years).
D4_FAIL_PLANTS: frozenset[int] = frozenset(
    {10034, 10294, 10649, 10650, 50612, 54749, 54768}
)


def model_side(year: int) -> tuple[pd.DataFrame, dict]:
    """Return one row per LP unit carrying a CHP steam floor, plus the config."""
    state, _meta = reconstruct_bundle_fleet(BUNDLE, year, verbose=False)
    generators = state["fleet"]
    generators = getattr(generators, "generators", generators)
    arrays = state["fleet_arrays"]
    rows = []
    for idx, gen in enumerate(generators):
        floor = float(getattr(gen, "chp_grid_pmin_mw", 0.0) or 0.0)
        if floor <= 0.0:
            continue
        rows.append(
            {
                "year": year,
                "g_idx": idx,
                "unit_id": str(gen.unit_id),
                "plant_code": int(getattr(gen, "plant_code", 0) or 0),
                "plant_group": str(getattr(gen, "plant_group", "") or ""),
                "name": str(getattr(gen, "name", "") or ""),
                "zone": str(getattr(gen, "zone", "") or ""),
                "pmax": float(gen.pmax_mw),
                "floor_mw": floor,
            }
        )
    df = pd.DataFrame(rows)
    # Availability clip: fleet/arrays.py line ~3429 applies
    # np.minimum(min_gen, pmax * availability), so the floor's realised
    # unit-hours are the clipped product, not floor x 8760.
    avail = np.asarray(arrays.availability, dtype=float)
    pmax = np.asarray(arrays.pmax, dtype=float)
    clipped = []
    for r in rows:
        g = r["g_idx"]
        cap = pmax[g] * avail[g, :]
        clipped.append(float(np.minimum(r["floor_mw"], cap).sum()))
    if not df.empty:
        df["forced_mwh_clipped"] = clipped
        df["forced_mwh_flat"] = df["floor_mw"] * avail.shape[1]
    return df, state["config"]


def meter_side(year: int, plants: set[int]) -> pd.DataFrame:
    """CAMPD hourly conduct for ``plants`` in ``year`` (on-frequency, CF-on).

    Uses the same gap-free clock (:func:`campd.plant_hourly_grid`) the derive
    reads, so an omitted off-hour counts as a zero rather than vanishing from
    the denominator — which is the whole question here.
    """
    from market_sim.data import campd

    if not plants:
        return pd.DataFrame()
    raw = campd.load_campd_hourly(["CA"], [year], prefer_unit_level=True)
    if raw is None or raw.empty:
        print(f"  [meter] no CAMPD rows for CA {year}")
        return pd.DataFrame()
    out = []
    for code in sorted(plants):
        grid = campd.plant_hourly_grid(raw, code, year)
        if grid.empty:
            out.append({"year": year, "plant_code": int(code), "campd_rows": 0})
            continue
        mw = grid["gross_mw"].to_numpy(dtype=float)
        on = mw > 0.0
        out.append(
            {
                "year": year,
                "plant_code": int(code),
                "campd_rows": int(mw.size),
                "on_hours": int(on.sum()),
                "on_frac": float(on.mean()),
                "p50_mw_on": float(np.median(mw[on])) if on.any() else 0.0,
                "max_mw": float(mw.max()),
                "mean_mw_allhr": float(mw.mean()),
                "measured_mwh": float(mw.sum()),
            }
        )
    return pd.DataFrame(out)


def main() -> None:
    model_frames, meter_frames = [], []
    cfg_echo: dict = {}
    for year in YEARS:
        print(f"== {year} ==")
        mdf, cfg = model_side(year)
        if not cfg_echo:
            cfg_echo = {
                k: getattr(cfg, k, None)
                for k in (
                    "chp_steam_following",
                    "chp_steam_floor_p25",
                    "chp_export_floor_measured",
                    "chp_layup_duty_curve",
                    "chp_btm_floor_pct",
                    "campd_per_unit_attribution",
                    "campd_outage_merit_order_guard",
                )
            }
            print("  recipe:", cfg_echo)
        print(
            f"  model: {len(mdf)} LP units carry a CHP steam floor "
            f"across {mdf['plant_code'].nunique() if not mdf.empty else 0} plants; "
            f"floor sum {mdf['floor_mw'].sum():.3f} MW; "
            f"forced {mdf['forced_mwh_clipped'].sum() / 1e6:.4f} TWh (clipped)"
        )
        model_frames.append(mdf)
        meter_frames.append(
            meter_side(year, set(mdf["plant_code"].tolist()) if not mdf.empty else set())
        )

    model = pd.concat(model_frames, ignore_index=True)
    meter = (
        pd.concat(meter_frames, ignore_index=True)
        if any(not f.empty for f in meter_frames)
        else pd.DataFrame()
    )

    per_plant = (
        model.groupby(["year", "plant_code", "plant_group", "name"], as_index=False)
        .agg(
            units=("unit_id", "size"),
            pmax=("pmax", "sum"),
            floor_mw=("floor_mw", "sum"),
            forced_mwh=("forced_mwh_clipped", "sum"),
        )
        .sort_values(["year", "forced_mwh"], ascending=[True, False])
    )
    if not meter.empty:
        per_plant = per_plant.merge(meter, on=["year", "plant_code"], how="left")
    per_plant["d4_fail"] = per_plant["plant_code"].isin(D4_FAIL_PLANTS)

    pd.set_option("display.width", 220, "display.max_columns", 40)
    cols = [
        "year",
        "plant_code",
        "plant_group",
        "name",
        "pmax",
        "floor_mw",
        "forced_mwh",
        "on_frac",
        "p50_mw_on",
        "measured_mwh",
        "d4_fail",
    ]
    print("\n===== PER-PLANT CHP STEAM FLOOR CENSUS =====")
    print(per_plant[[c for c in cols if c in per_plant.columns]].to_string(index=False))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "bundle": str(BUNDLE.relative_to(REPO)),
                "years": list(YEARS),
                "recipe": cfg_echo,
                "per_plant": json.loads(per_plant.to_json(orient="records")),
                "per_unit": json.loads(model.to_json(orient="records")),
            },
            indent=1,
        )
    )
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
