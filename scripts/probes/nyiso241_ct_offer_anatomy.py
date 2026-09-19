"""nyiso-241 phase 0 (ZERO LP): the exact anatomy of the CT_PEAKER offer, and the lever's reach.

Rebuilds the designated keeper's fleet on its own recipe via the SANCTIONED
``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs`` path
(``run_year(..., fleet_only=True)``) — the same instrument nyiso-232 used — so the base (P0)
marginal-cost array and each row's DELIVERED fuel price are read rather than inferred.

WHY. The object handed to this lane is CT_PEAKER's merit collapse from 2023: 2.43 -> 0.25 / 0.30 /
0.77 TWh against a flat ~2.1-2.8 TWh actual, capacity intact
(docs/FINDING-nyiso240-c1-margin-bench-attribution-2026-09-19.md §7). The recommended lever is
``ct_peaker_committed_measured`` — grounding ``_NYISO_OFFER_CURVE["CT_PEAKER"]["committed"]`` on
NYISO's OWN measured ``phys_committed`` 0.843 in place of the transferred 1.35.

Two things must be measured BEFORE that lever is proposed, and neither needs a solve:

  A. WHAT THE OFFER IS MADE OF. A band multiplier scales fuel, so on its own it cannot reorder a
     merit stack when gas falls (2022 $6.86 -> 2023 $1.98/MMBtu at Transco Z6 NY) — every gas
     offer would fall together. The committed sidecars show CT_PEAKER's cheapest offer falling
     only to 0.53 of its 2022 level while CC_REGULAR's falls to 0.43, so a component of the CT
     offer does NOT scale with fuel. This probe separates the offer into
     ``heat_rate x band x delivered_fuel`` (read from ``mc_base`` and ``fuel_prices``) and the
     residual flat part, and — against the committed P1 ``unit_hourly`` — isolates the P0->P1
     startup amortization, which ``model/commitment.compute_monthly_markup`` computes PER LP ROW
     from THAT ROW'S OWN P0 run length.

  B. WHAT THE LEVER ACTUALLY REACHES. The lever moves ONE band. The committed sidecars put
     0.08 / 0.02 / 0.04 / 0.19 TWh of CT_PEAKER's 2.43 / 0.25 / 0.30 / 0.77 TWh in the
     ``committed`` band, with the rest in ``econlo``/``econhi``, which are ALREADY at the neutral
     1.0 multiplier and which the lever does not touch. This probe reports the exact offer-array
     delta — which rows move, by how much, and what the class's CHEAPEST offer becomes — so the
     lever is sized against the object before any LP is spent.

NOTHING HERE IS SWEPT. The arm value is NYISO's own registered ``phys_committed`` 0.843, quoted
from ``_NYISO_OFFER_CURVE``, not selected by any gate or residual (rule 1 `[R-STRUCT]` (c)).

Run: ``python3 scripts/probes/nyiso241_ct_offer_anatomy.py <year> [<year> ...]``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# The designated keeper (rule 15 `[R-DASHBOARD]`), whose committed `hourly/class_hourly_<yr>`
# sidecars `derived_run_year_inputs` reads and whose recipe `run_year_kwargs` replays.
BUNDLE = Path("results/calibration/nyiso240_benchfix_span")

# The nyiso-240 MER legs carry the per-plant layer the keeper bundle does not, and their
# `dispatch/<yr>_P1.parquet` are sha256-identical to the keeper's (RESULT §A.4). Used ONLY to
# read the realised P1 offer, so the P0->P1 startup markup can be differenced out.
MER_LEG = "results/calibration/nyiso_mer_2026-09-19_{year}"

# THE CANDIDATE, declared here so the probe cannot be re-pointed silently: CT_PEAKER's
# `committed` band := its OWN measured `phys_committed`, which `_NYISO_OFFER_CURVE` already
# carries beside it (avg_committed_p50, data/raw/reference/nyiso_campd_marginal_hr_summary.csv,
# n = 70). ZERO new literals and ZERO values to pick — the strictest available form of a rule-14
# `[R-ACCURATE]` substitution, and a rule-25 `[R-ISO-SCOPE]` repair rather than a transfer
# (CAISO's 0.991 is never carried across).
ARM_CT_PEAKER = {"committed": 0.843}

FOSSIL_CLASSES = ("CT_PEAKER", "ST_GAS", "CC_REGULAR", "CC_CHP")


def _is_plant_token(tok: str) -> bool:
    """True for the ``p<digits>`` plant segment of an LP row id.

    Tested on the digits, not the leading ``p`` alone: the band name ``peak`` also starts with
    ``p``, and reading it as a plant token silently drops the entire peak band.
    """
    return len(tok) > 1 and tok[0] == "p" and tok[1:].isdigit()


def band_of(unit_id: str) -> str:
    """Return the band segment of an LP row id ``<CLASS>_<ZONE>_p<plant>_<band>``."""
    tail = str(unit_id).rsplit("_", 1)[-1]
    return "" if _is_plant_token(tail) else tail


def build(year: int, arm: bool):
    """Fleet-only rebuild of the keeper's own recipe, optionally with the candidate band."""
    import importlib

    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))

    # `_NYISO_OFFER_CURVE` is deep-merged ON TOP of `config.offer_curve_by_group` inside
    # `backcast_config`, so a recipe kwarg cannot carry the arm — the registry entry is what a
    # gated field would edit, and it is what the probe edits here, restoring it afterwards.
    _bc = importlib.import_module("market_sim.pipeline.backcast_config")
    saved = dict(_bc._NYISO_OFFER_CURVE["CT_PEAKER"])
    try:
        if arm:
            _bc._NYISO_OFFER_CURVE["CT_PEAKER"].update(ARM_CT_PEAKER)
        return run_year(
            year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
        )
    finally:
        _bc._NYISO_OFFER_CURVE["CT_PEAKER"].clear()
        _bc._NYISO_OFFER_CURVE["CT_PEAKER"].update(saved)


def rows_of(state):
    """Unpack a fleet-only state into aligned id / class / band / pmax / mc_base / fuel arrays."""
    fa = state["fleet_arrays"]
    ids = [str(u) for u in fa.unit_ids]
    return {
        "ids": ids,
        "klass": [str(k) for k in fa.plant_group],
        "band": [band_of(u) for u in ids],
        "pmax": np.asarray(fa.pmax, dtype=float),
        "heat_rate": np.asarray(fa.heat_rate, dtype=float),
        "mc_base": np.asarray(state["mc_base"], dtype=float),
        "fuel": np.asarray(state["fuel_prices"], dtype=float),
    }


def anatomy(ctl: dict, year: int) -> dict:
    """Split each class's base offer into fuel-proportional and flat, and add the P1 markup."""
    import pandas as pd

    mc = ctl["mc_base"]
    fuel = ctl["fuel"]
    # `mc_base` and `fuel_prices` may be (n_gen, T) or (n_gen,) depending on the year's build;
    # reduce to a per-row annual mean either way so the two are comparable.
    mc_row = mc.mean(axis=1) if mc.ndim == 2 else mc
    fuel_row = fuel.mean(axis=1) if fuel.ndim == 2 else fuel
    hr = ctl["heat_rate"]

    frame = pd.DataFrame(
        {
            "unit_id": ctl["ids"],
            "klass": ctl["klass"],
            "band": ctl["band"],
            "pmax": ctl["pmax"],
            "hr": hr,
            "mc_base": mc_row,
            "fuel": fuel_row,
        }
    )
    frame["fuel_component"] = frame["hr"] * frame["fuel"]
    frame["flat_component"] = frame["mc_base"] - frame["fuel_component"]

    # The realised P1 offer, from the MER leg. The difference against `mc_base` is precisely the
    # monthly startup amortization `compute_monthly_markup` adds at the P0->P1 seam.
    leg = Path(MER_LEG.format(year=year))
    p1 = pd.read_parquet(
        leg / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "unit_id", "hour", "mc"],
    )
    p1 = p1[p1["pass"] == "P1"].groupby("unit_id")["mc"].mean().rename("mc_p1")
    frame = frame.join(p1, on="unit_id")
    frame["startup_markup"] = frame["mc_p1"] - frame["mc_base"]

    out: dict[str, dict] = {"year": year}
    for klass in FOSSIL_CLASSES:
        sub = frame[frame["klass"] == klass]
        if sub.empty:
            continue
        w = sub["pmax"].to_numpy()
        wsum = w.sum()

        def cw(col: str, sub=sub, w=w, wsum=wsum) -> float:
            """Capacity-weighted mean of a column, NaN-safe."""
            v = sub[col].to_numpy(dtype=float)
            ok = np.isfinite(v)
            return (
                float((v[ok] * w[ok]).sum() / w[ok].sum())
                if ok.any() and w[ok].sum()
                else float("nan")
            )

        bands: dict[str, dict] = {}
        for band, grp in sub.groupby("band"):
            bw = grp["pmax"].to_numpy()
            bands[band or "_none"] = {
                "rows": int(len(grp)),
                "pmax_mw": float(bw.sum()),
                "mc_base": float((grp["mc_base"].to_numpy() * bw).sum() / bw.sum())
                if bw.sum()
                else float("nan"),
                "startup_markup": float(
                    np.nansum(grp["startup_markup"].to_numpy() * bw) / bw.sum()
                )
                if bw.sum()
                else float("nan"),
            }
        out[klass] = {
            "rows": int(len(sub)),
            "pmax_mw": float(wsum),
            "delivered_fuel_usd_mmbtu": cw("fuel"),
            "heat_rate_mmbtu_mwh": cw("hr"),
            "mc_base_usd_mwh": cw("mc_base"),
            "fuel_component_usd_mwh": cw("fuel_component"),
            "flat_component_usd_mwh": cw("flat_component"),
            "startup_markup_usd_mwh": cw("startup_markup"),
            "mc_p1_usd_mwh": cw("mc_p1"),
            "cheapest_row_mc_base": float(sub["mc_base"].min()),
            "cheapest_row_mc_p1": float(np.nanmin(sub["mc_p1"].to_numpy())),
            "bands": bands,
        }
    return out


def lever_reach(ctl: dict, arm: dict) -> dict:
    """Exact offer-array delta of the candidate band substitution, and its merit consequence."""
    import pandas as pd

    def flat(state: dict, tag: str):
        """Per-row annual-mean base offer, labelled."""
        mc = state["mc_base"]
        return pd.DataFrame(
            {
                "unit_id": state["ids"],
                "klass": state["klass"],
                "band": state["band"],
                "pmax": state["pmax"],
                f"mc_{tag}": mc.mean(axis=1) if mc.ndim == 2 else mc,
            }
        ).set_index("unit_id")

    c = flat(ctl, "ctl")
    a = flat(arm, "arm")[["mc_arm"]]
    joined = c.join(a, how="outer")
    joined["delta"] = joined["mc_arm"] - joined["mc_ctl"]
    moved = joined[joined["delta"].abs() > 1e-9]

    ct = joined[joined["klass"] == "CT_PEAKER"]
    other = joined[joined["klass"] != "CT_PEAKER"]
    ct_committed = ct[ct["band"] == "committed"]
    return {
        "rows_total": int(len(joined)),
        "rows_moved": int(len(moved)),
        "rows_moved_outside_ct_peaker": int((moved["klass"] != "CT_PEAKER").sum()),
        "rows_moved_outside_committed_band": int((moved["band"] != "committed").sum()),
        "confinement_max_abs_delta_elsewhere": float(other["delta"].abs().max())
        if len(other)
        else 0.0,
        "ct_committed_rows": int(len(ct_committed)),
        "ct_committed_pmax_mw": float(ct_committed["pmax"].sum()),
        "ct_total_pmax_mw": float(ct["pmax"].sum()),
        "ct_committed_pmax_share": float(ct_committed["pmax"].sum() / ct["pmax"].sum())
        if ct["pmax"].sum()
        else float("nan"),
        "ct_committed_offer_ctl": float(
            (ct_committed["mc_ctl"] * ct_committed["pmax"]).sum()
            / ct_committed["pmax"].sum()
        )
        if ct_committed["pmax"].sum()
        else float("nan"),
        "ct_committed_offer_arm": float(
            (ct_committed["mc_arm"] * ct_committed["pmax"]).sum()
            / ct_committed["pmax"].sum()
        )
        if ct_committed["pmax"].sum()
        else float("nan"),
        "ct_cheapest_offer_ctl": float(ct["mc_ctl"].min()),
        "ct_cheapest_offer_arm": float(ct["mc_arm"].min()),
    }


def main() -> None:
    """Run the anatomy and the lever-reach delta for each requested year."""
    years = [int(a) for a in sys.argv[1:]] or [2022, 2023]
    out: dict[str, dict] = {}
    for year in years:
        ctl_state = build(year, arm=False)
        arm_state = build(year, arm=True)
        ctl, arm = rows_of(ctl_state), rows_of(arm_state)
        res = {"anatomy": anatomy(ctl, year), "lever": lever_reach(ctl, arm)}
        out[str(year)] = res

        print(f"\n===== {year} =====")
        for klass in FOSSIL_CLASSES:
            row = res["anatomy"].get(klass)
            if not row:
                continue
            print(
                f"  {klass:<12} fuel {row['delivered_fuel_usd_mmbtu']:>6.3f} $/MMBtu x HR "
                f"{row['heat_rate_mmbtu_mwh']:>6.2f} = {row['fuel_component_usd_mwh']:>7.2f}  "
                f"+ flat {row['flat_component_usd_mwh']:>7.2f}  = base {row['mc_base_usd_mwh']:>7.2f}"
                f"  + startup {row['startup_markup_usd_mwh']:>6.2f}  = P1 {row['mc_p1_usd_mwh']:>7.2f}"
            )
            for band, b in sorted(row["bands"].items()):
                print(
                    f"        {band:<10} {b['pmax_mw']:>8.1f} MW  base {b['mc_base']:>7.2f}"
                    f"  startup {b['startup_markup']:>7.2f}"
                )
        lv = res["lever"]
        print(
            f"  LEVER committed 1.35 -> 0.843: {lv['rows_moved']} rows move, "
            f"{lv['rows_moved_outside_ct_peaker']} outside CT_PEAKER, "
            f"{lv['rows_moved_outside_committed_band']} outside the committed band "
            f"(max |d| elsewhere ${lv['confinement_max_abs_delta_elsewhere']:.2e})"
        )
        print(
            f"        CT committed band {lv['ct_committed_pmax_mw']:.1f} MW of "
            f"{lv['ct_total_pmax_mw']:.1f} MW ({lv['ct_committed_pmax_share'] * 100:.1f} %); offer "
            f"{lv['ct_committed_offer_ctl']:.2f} -> {lv['ct_committed_offer_arm']:.2f} $/MWh"
        )
        print(
            f"        class CHEAPEST offer {lv['ct_cheapest_offer_ctl']:.2f} -> "
            f"{lv['ct_cheapest_offer_arm']:.2f} $/MWh"
        )

    # Merge rather than overwrite: the probe is routinely run a couple of years at a time, and a
    # plain write silently drops the years a previous invocation measured.
    dest = Path("results/calibration/_nyiso241_ct_offer_anatomy.json")
    merged = json.loads(dest.read_text()) if dest.exists() else {}
    merged.update(out)
    dest.write_text(json.dumps(merged, indent=1))
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
