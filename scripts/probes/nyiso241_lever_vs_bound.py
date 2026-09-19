"""nyiso-241 phase 0 (ZERO LP): size the recommended lever against the reachability bound.

Two measurements already exist, and this probe joins them:

  * ``nyiso241_reachability_bound.py`` — against the keeper's OWN hourly prices, the CT_PEAKER
    fleet would need its posted offer cut to roughly x0.70-0.80 (2023-2025) before even a
    GENEROUS upper bound (run flat out in every zone-hour that clears, no min-run, no ramp, no
    competition) covers the 1.9-2.8 TWh/yr actual.
  * ``nyiso241_ct_offer_anatomy.py`` — ``ct_peaker_committed_measured`` (``committed`` 1.35 ->
    NYISO's own measured ``phys_committed`` 0.843) is perfectly confined: 22 rows move, none
    outside CT_PEAKER, none outside the ``committed`` band. That band is 346.7 MW of the class's
    3,034.0 MW (11.4 %).

The joined question — the one the PRECOMMIT turns on — is what the lever does to the BOUND, not
to one band's offer. This probe rebuilds the fleet control and arm (``run_year(...,
fleet_only=True)`` on the keeper's own recipe), takes the EXACT per-row base-offer delta, applies
it to the committed P1 offers, and re-reads the bound.

The P0->P1 startup markup is reported at two bookends rather than guessed at, because
``model/commitment.compute_monthly_markup`` recomputes it from each row's own P0 run length and
this probe solves nothing:

  * FROZEN — the keeper's markup carried over unchanged (conservative: a row that runs more would
    amortize its start over more hours, so this understates the arm);
  * RELAXED — the committed rows' markup dropped to their own class's ``econ`` band level, which
    is what a row that starts running like the econ band would amortize to (optimistic).

The truth is between them, and if BOTH bookends leave the bound short of the actual then no LP is
needed to know the lever is not sized to the object.

Nothing here is swept: the arm value is NYISO's own registered ``phys_committed``, quoted, and
the bookends are stated before the numbers rather than chosen after (rule 1 `[R-STRUCT]` (c)).

Run: ``python3 scripts/probes/nyiso241_lever_vs_bound.py <year> [<year> ...]``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.probes.nyiso241_ct_offer_anatomy import (  # noqa: E402
    MER_LEG,
    band_of,
    rows_of,
)

# The two candidate arms, both quoted from `_NYISO_OFFER_CURVE`'s OWN registered `phys_*`
# measurements (nyiso_campd_marginal_hr_summary.csv p50s, n = 70) — nothing is chosen and
# nothing is swept (rules 1 `[R-STRUCT]` (c) / 21 `[R-DOF]`):
#
#   committed_only  — the matrix's `ct_peaker_committed_measured`, cell U, the handoff's
#                     recommendation. Moves ONE band.
#   three_band      — the matrix's `nyiso_ct_peaker_bands_measured`, cell R with a SHARPENED
#                     re-test condition (nyiso-200). Moves all three FUEL-SCALED bands; `peak`
#                     is deliberately excluded because NYISO's 4.0 is the $1,000-offer-cap
#                     scarcity wall, not a physics claim (rule 19 `[R-ONE-MECH]`).
#
# Measuring both on the SAME bound is what lets the two be compared before an LP is spent; it
# is not a sweep, because neither value is selectable and no gate is being read.
ARMS = {
    "committed_only": {"committed": 0.843},
    "three_band": {"committed": 0.843, "econ_low": 0.661, "econ_high": 0.658},
}


def build(year: int, arm):
    """Fleet-only rebuild of the keeper's own recipe, optionally with a candidate band set."""
    import importlib

    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year
    from scripts.probes.nyiso241_ct_offer_anatomy import BUNDLE

    meta = json.loads((Path(BUNDLE) / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))
    _bc = importlib.import_module("market_sim.pipeline.backcast_config")
    saved = dict(_bc._NYISO_OFFER_CURVE["CT_PEAKER"])
    try:
        if arm:
            _bc._NYISO_OFFER_CURVE["CT_PEAKER"].update(arm)
        return run_year(
            year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
        )
    finally:
        _bc._NYISO_OFFER_CURVE["CT_PEAKER"].clear()
        _bc._NYISO_OFFER_CURVE["CT_PEAKER"].update(saved)


# CT_PEAKER energy actually metered, from the committed benchmark the keeper is scored on.
ACTUAL_TWH = {2022: 2.829, 2023: 2.114, 2024: 1.911, 2025: 2.812}

# The bands whose markup level the RELAXED bookend borrows for the committed rows.
ECON_BANDS = ("econlo", "econhi")


def per_row_base(state: dict) -> pd.Series:
    """Annual-mean base (P0) offer per LP row."""
    mc = state["mc_base"]
    values = mc.mean(axis=1) if mc.ndim == 2 else mc
    return pd.Series(values, index=state["ids"])


def measure(year: int, arm_name: str) -> dict:
    """Re-read the reachability bound under the control and under one candidate band set."""
    ctl = rows_of(build(year, None))
    arm = rows_of(build(year, ARMS[arm_name]))
    base_ctl, base_arm = per_row_base(ctl), per_row_base(arm)
    delta = (
        (base_arm - base_ctl).reindex(base_ctl.index).fillna(0.0)
    )  # <= 0 on moved rows

    leg = Path(MER_LEG.format(year=year))
    unit = pd.read_parquet(
        leg / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "unit_id", "plant_group", "zone", "hour", "cap_mw", "mc"],
    )
    unit = unit[unit["pass"] == "P1"].copy()
    unit["band"] = [band_of(u) for u in unit["unit_id"]]
    system = pd.read_parquet(leg / "hourly" / f"system_{year}.parquet")
    price_col = "price" if "price" in system.columns else "lmp"
    prices = system[["zone", "hour", price_col]].rename(columns={price_col: "price"})

    ct = unit[unit["plant_group"] == "CT_PEAKER"].merge(
        prices, on=["zone", "hour"], how="left"
    )
    ct = ct[ct["price"].notna()].copy()
    ct["delta"] = ct["unit_id"].map(delta).fillna(0.0)

    # The startup markup each band carries in the keeper, so the RELAXED bookend can borrow the
    # econ level for the committed rows rather than invent one.
    anat = json.loads(
        Path("results/calibration/_nyiso241_ct_offer_anatomy.json").read_text()
    )
    bands = (
        anat.get(str(year), {}).get("anatomy", {}).get("CT_PEAKER", {}).get("bands", {})
    )
    econ_markup = (
        float(np.mean([bands[b]["startup_markup"] for b in ECON_BANDS if b in bands]))
        if bands
        else 0.0
    )
    committed_markup = float(
        bands.get("committed", {}).get("startup_markup", econ_markup)
    )

    def bound(offer: pd.Series) -> dict:
        """Generous upper bound: full available capacity wherever the offer clears its zone."""
        clears = ct["price"] >= offer
        twh = float(ct.loc[clears, "cap_mw"].sum() / 1e6)
        return {
            "energy_twh_upper_bound": twh,
            "row_hours_clearing": int(clears.sum()),
            "share_of_actual": twh / ACTUAL_TWH[year],
        }

    # RELAXED bookend applies only where the band actually moved.
    moved_band = (ct["delta"].abs() > 1e-9).to_numpy()
    is_committed = ((ct["band"] == "committed") & moved_band).to_numpy()
    offer_ctl = ct["mc"]
    offer_frozen = ct["mc"] + ct["delta"]
    offer_relaxed = offer_frozen - np.where(
        is_committed, committed_markup - econ_markup, 0.0
    )

    ct_committed = ct[is_committed]
    return {
        "actual_twh": ACTUAL_TWH[year],
        "arm_name": arm_name,
        "arm": ARMS[arm_name],
        "committed_band_markup_usd_mwh": committed_markup,
        "econ_band_markup_usd_mwh": econ_markup,
        "committed_rows_moved": int((ct_committed["delta"].abs() > 1e-9).sum() > 0)
        and int(ct_committed["unit_id"].nunique()),
        "committed_mean_offer_ctl": float(ct_committed["mc"].mean()),
        "committed_mean_offer_frozen": float(
            (ct_committed["mc"] + ct_committed["delta"]).mean()
        ),
        "committed_offer_scale": float(
            (ct_committed["mc"] + ct_committed["delta"]).mean()
            / ct_committed["mc"].mean()
        ),
        "class_offer_scale_capwt": float(
            ((ct["mc"] + ct["delta"]) * ct["cap_mw"]).sum()
            / (ct["mc"] * ct["cap_mw"]).sum()
        ),
        "bound_control": bound(offer_ctl),
        "bound_arm_frozen_markup": bound(offer_frozen),
        "bound_arm_relaxed_markup": bound(pd.Series(offer_relaxed, index=ct.index)),
    }


def main() -> None:
    """Report the lever's effect on the reachability bound for each requested year."""
    argv = [a for a in sys.argv[1:]]
    arm_names = [a for a in argv if a in ARMS] or list(ARMS)
    years = [int(a) for a in argv if a.isdigit()] or [2022, 2023, 2024, 2025]
    out: dict[str, dict] = {}
    for arm_name in arm_names:
        print(f"\n########## ARM {arm_name}: {ARMS[arm_name]} ##########")
        for year in years:
            res = measure(year, arm_name)
            out.setdefault(arm_name, {})[str(year)] = res
            print(f"\n===== {year}  actual {res['actual_twh']:.3f} TWh =====")
            print(
                f"  committed band offer {res['committed_mean_offer_ctl']:.2f} -> "
                f"{res['committed_mean_offer_frozen']:.2f} $/MWh (x{res['committed_offer_scale']:.3f}); "
                f"CLASS cap-weighted offer x{res['class_offer_scale_capwt']:.3f}"
            )
            print(
                f"  startup markup carried: committed {res['committed_band_markup_usd_mwh']:.2f} vs "
                f"econ {res['econ_band_markup_usd_mwh']:.2f} $/MWh"
            )
            for tag in (
                "bound_control",
                "bound_arm_frozen_markup",
                "bound_arm_relaxed_markup",
            ):
                b = res[tag]
                print(
                    f"  {tag:<26} {b['energy_twh_upper_bound']:>7.3f} TWh upper bound "
                    f"({b['share_of_actual'] * 100:>6.1f} % of actual)"
                )

    dest = Path("results/calibration/_nyiso241_lever_vs_bound.json")
    dest.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
