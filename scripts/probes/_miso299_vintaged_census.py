#!/usr/bin/env python3
"""miso-299 (ZERO LP): the ruled gas form with a PER-YEAR transport table, census per year.

Owner ruling 2026-10-01 (miso-298 card "Per-year transport phase 0"): derive the
2019-2022 variable-transport rows from each year's own EIA-923 receipts and
measure the static CC fuel move and the census per year BEFORE any shard.

Three legs per year, every one the miso-297 census machinery
(:mod:`scripts.probes._miso297_joint_census`: fleet-only rebuild of the keeper
recipe, P0 base stack and P1 bid stack cleared at the keeper's own P1 thermal
quantity every hour, coal econ multiplier m = 1.00 only):

* ``keeper``          -- the keeper recipe (EIA-923 average print on gas rows);
* ``joint_frozen``    -- the owner-ruled gas form with the FROZEN 2023-2025 table
                         (= the miso-298 arm, the miso-297 "joint|1.00" row);
* ``joint_vintaged``  -- the owner-ruled gas form with THAT YEAR's own table
                         (``data/raw/reference/miso_gas_variable_transport_vintaged/<Y>.csv``).

The vintaged leg points the production applier at the per-year table by
rebinding ``market_sim.data.fuel.basis.miso.MISO_GAS_VARIABLE_TRANSPORT_PATH``
for the rebuild -- a probe-only shim; a ScenarioConfig field is minted only if
the pre-stated reading (FINDING-miso299 s0) says the lane proceeds.

Reported per year and leg: fleet cap-weighted fuel by class (print / bare hub /
hub + v), the implied print-over-hub wedge and the fleet cap-weighted ``v``,
transport coverage, the bid-stack marginal census (all hours, by load quintile),
static dispatch (coal / coal econ / gas / CC_REGULAR / seam, mean GW), static
q1-q2 and all-hours load-weighted price error against the zone-resolved actual.

Output: ``results/phase0/miso/_miso299_vintaged_census.json``.

Usage (repo root)::

    uv run python scripts/probes/_miso299_vintaged_census.py [--years ...] [--out ...]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(REPO / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes import _miso271_cc_decomp as dec  # noqa: E402
from scripts.probes._miso296_lowload_stack import (  # noqa: E402
    COAL,
    GAS,
    IMM_SMP_SHARE,
    INTERNAL,
    KEEPER,
    NON_LP,
    T,
    YEARS,
    family,
    zone_actual,
)
from scripts.probes._miso297_joint_census import (  # noqa: E402
    ARM_FLIPS,
    _r,
    clear_vec,
    markup_for,
    rebuild,
    transport_coverage,
)

OUT = REPO / "results/phase0/miso/_miso299_vintaged_census.json"
VINTAGED = REPO / "data/raw/reference/miso_gas_variable_transport_vintaged"
REPORT_GROUPS = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "__ALL_GAS__")


def _mask(b, g):
    gas = np.isin(b["grp"], GAS)
    return gas if g == "__ALL_GAS__" else (b["grp"] == g)


def _cap_wtd(values, cap, mask):
    """Capacity-weighted mean of an ``(n, T)`` or ``(n,)`` array over ``mask`` rows."""
    c = cap[mask]
    if c.sum() <= 0:
        return None
    v = values[mask]
    if v.ndim == 1:
        v = v[:, None] * np.ones_like(c)
    return _r((v * c).sum() / c.sum())


def transport_vector(b):
    """The per-row variable transport the applier added (zero on non-gas rows)."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fuel.basis.miso import _miso_gas_variable_transport_vector

    zn = tuple(get_iso_config("MISO").zone_names)
    gas_idx = np.nonzero(np.isin(b["grp"], GAS))[0]
    v = np.zeros(len(b["grp"]))
    v[gas_idx] = _miso_gas_variable_transport_vector(b["fa"], gas_idx, zn)
    return v


def rebuild_with_table(y, hh, table: Path | None):
    """Fleet-only rebuild of the ruled form with the transport table at ``table``."""
    from market_sim.data.fuel.basis import miso as basis

    saved = basis.MISO_GAS_VARIABLE_TRANSPORT_PATH
    try:
        if table is not None:
            basis.MISO_GAS_VARIABLE_TRANSPORT_PATH = table
        b = rebuild(y, hh, ARM_FLIPS)
        b["transport"] = transport_vector(b)
        b["coverage"] = transport_coverage(b)
    finally:
        basis.MISO_GAS_VARIABLE_TRANSPORT_PATH = saved
    return b


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    from scripts.data import derive_actual_lmp as dal  # noqa: E402
    from scripts.run_calibration import _load_reference  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    dec.KEEPER = KEEPER
    out = json.loads(args.out.read_text()) if args.out.exists() else {}
    out["_rule"] = {
        "legs": {
            "keeper": "keeper recipe (EIA-923 average print on gas rows)",
            "joint_frozen": "ruled gas form + frozen 2023-2025 pooled table (the miso-298 arm)",
            "joint_vintaged": "ruled gas form + that year's own per-year table",
        },
        "m": 1.0,
        "quantity": "keeper P1 thermal quantity every hour (miso-296 block B)",
        "pre_stated_reading": "FINDING-miso299-peryear-transport-2026-10-02.md s0 @ a5fb67f4",
    }
    famv = np.vectorize(family)
    for y in args.years:
        t0 = time.time()
        yo: dict = {}
        hh = _henry_hub_actual(_load_reference(), y)
        legs = {
            "keeper": rebuild(y, hh, {}),
            "joint_frozen": rebuild_with_table(y, hh, None),
            "joint_vintaged": rebuild_with_table(y, hh, VINTAGED / f"{y}.csv"),
        }
        b0 = legs["keeper"]
        gas = np.isin(b0["grp"], GAS)
        cap = b0["cap"]
        # --- fuel by class and leg; the wedge the print carries over the bare hub
        fuel: dict = {}
        for g in REPORT_GROUPS:
            m = _mask(b0, g)
            row = {"print_keeper": _cap_wtd(b0["fp"], cap, m)}
            for leg in ("joint_frozen", "joint_vintaged"):
                b = legs[leg]
                hub_only = b["fp"] - b["transport"][:, None]
                row[f"hub_bare_{leg}"] = _cap_wtd(hub_only, cap, m)
                row[f"fuel_{leg}"] = _cap_wtd(b["fp"], cap, m)
                row[f"v_{leg}"] = _cap_wtd(b["transport"], cap, m)
                row[f"delta_vs_print_{leg}"] = _r(
                    row[f"fuel_{leg}"] - row["print_keeper"]
                )
            row["wedge_print_over_hub"] = _r(
                row["print_keeper"] - row["hub_bare_joint_frozen"]
            )
            row["delta_vintaged_vs_frozen"] = _r(
                row["fuel_joint_vintaged"] - row["fuel_joint_frozen"]
            )
            fuel[g] = row
        yo["fuel_cap_wtd"] = fuel
        yo["identity"] = {
            "non_gas_rows_identical_frozen": bool(
                np.allclose(b0["mc"][~gas], legs["joint_frozen"]["mc"][~gas])
            ),
            "non_gas_rows_identical_vintaged": bool(
                np.allclose(b0["mc"][~gas], legs["joint_vintaged"]["mc"][~gas])
            ),
            "hub_bare_identical_between_joint_legs": bool(
                np.allclose(
                    legs["joint_frozen"]["fp"][gas]
                    - legs["joint_frozen"]["transport"][gas][:, None],
                    legs["joint_vintaged"]["fp"][gas]
                    - legs["joint_vintaged"]["transport"][gas][:, None],
                )
            ),
            "n_rows": int(b0["mc"].shape[0]),
        }
        yo["coverage"] = {
            leg: legs[leg]["coverage"] for leg in ("joint_frozen", "joint_vintaged")
        }
        # --- quantity, demand weights, quintiles, actual (as miso-297)
        ch = pd.read_parquet(KEEPER / f"hourly/class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"]
        chl = ch[~ch.klass.astype(str).isin(NON_LP)]
        q = chl.groupby("hour").mw.sum().reindex(range(T)).fillna(0).to_numpy()
        w = dal._measured_zone_demand("MISO", y)
        assert w is not None and w.shape == (6, T), w.shape
        load = w.sum(axis=0)
        q5 = pd.qcut(load, 5, labels=False)
        pa = zone_actual(y)
        ok = ~np.isnan(pa).any(axis=0)
        lw_a = (pa * w).sum(0) / w.sum(0)
        s = pd.read_parquet(KEEPER / f"hourly/system_{y}.parquet")
        s = s[s["pass"] == "P1"]
        pz = s.pivot(index="hour", columns="zone", values="price").sort_index()
        pm = pz[INTERNAL].to_numpy().T
        lw_m = (pm * w).sum(0) / w.sum(0)
        wt = np.where(ok, load, 0.0)
        yo["reference"] = {
            "actual_lw_mean": _r((lw_a[ok] * wt[ok]).sum() / wt.sum()),
            "keeper_p1_lw_mean": _r((lw_m[ok] * wt[ok]).sum() / wt.sum()),
            "actual_q1_median": _r(np.median(lw_a[(q5 == 0) & ok])),
            "actual_q2_median": _r(np.median(lw_a[(q5 == 1) & ok])),
            "coverage_hours": int(ok.sum()),
            "imm_smp_share": IMM_SMP_SHARE.get(y),
        }
        rows = {}
        for leg, b in legs.items():
            fam_row = famv(b["lab"])
            is_coal = fam_row == "coal"
            is_gas = fam_row == "gas"
            is_seam = fam_row == "seam"
            ce = np.isin(b["grp"], COAL) & (b["fam"] == "econ")
            cc = b["grp"] == "CC_REGULAR"
            p0, m0, d0 = clear_vec(b["mc"], b["mg"], b["flex"], q)
            mk = markup_for(b, d0)
            p1, m1, d1 = clear_vec(b["mc"] + mk, b["mg"], b["flex"], q)

            def census(marg, mask):
                v = pd.Series(fam_row[marg[mask]]).value_counts(normalize=True)
                return {k: _r(x) for k, x in v.items()}

            allm = np.ones(T, bool)
            rows[leg] = {
                "p0_all": census(m0, allm),
                "bid_all": census(m1, allm),
                "bid_q": {f"q{i + 1}": census(m1, q5 == i) for i in range(5)},
                "coal_econ_dispatched_share": _r(
                    d1[ce].sum() / max(b["cap"][ce].sum(), 1.0)
                ),
                "dispatch_gw_mean": {
                    "coal": _r(d1[is_coal].sum(0).mean() / 1e3),
                    "coal_econ": _r(d1[ce].sum(0).mean() / 1e3),
                    "gas": _r(d1[is_gas].sum(0).mean() / 1e3),
                    "cc_regular": _r(d1[cc].sum(0).mean() / 1e3),
                    "seam": _r(d1[is_seam].sum(0).mean() / 1e3),
                },
                "dispatch_gw_mean_q12": {
                    "coal": _r(d1[is_coal][:, q5 <= 1].sum(0).mean() / 1e3),
                    "gas": _r(d1[is_gas][:, q5 <= 1].sum(0).mean() / 1e3),
                    "cc_regular": _r(d1[cc][:, q5 <= 1].sum(0).mean() / 1e3),
                    "seam": _r(d1[is_seam][:, q5 <= 1].sum(0).mean() / 1e3),
                },
                "price": {
                    "bid_q1_median": _r(np.median(p1[q5 == 0])),
                    "bid_q2_median": _r(np.median(p1[q5 == 1])),
                    "bid_q5_median": _r(np.median(p1[q5 == 4])),
                    "bid_lw_mean": _r((p1[ok] * wt[ok]).sum() / wt.sum()),
                    "bid_minus_actual_lw_mean": _r(
                        ((p1 - lw_a)[ok] * wt[ok]).sum() / wt.sum()
                    ),
                    "bid_minus_actual_lw_mean_q12": _r(
                        ((p1 - lw_a)[(q5 <= 1) & ok] * wt[(q5 <= 1) & ok]).sum()
                        / wt[(q5 <= 1) & ok].sum()
                    ),
                    "markup_at_margin_q12_median": _r(
                        np.median(mk[m1, np.arange(T)][q5 <= 1])
                    ),
                },
            }
            print(
                y,
                leg,
                "CC fuel",
                fuel["CC_REGULAR"].get(
                    f"fuel_{leg}", fuel["CC_REGULAR"]["print_keeper"]
                ),
                "bid coal",
                rows[leg]["bid_all"].get("coal"),
                "cc GW",
                rows[leg]["dispatch_gw_mean"]["cc_regular"],
                "q12 err",
                rows[leg]["price"]["bid_minus_actual_lw_mean_q12"],
                "all err",
                rows[leg]["price"]["bid_minus_actual_lw_mean"],
                flush=True,
            )
        yo["legs"] = rows
        yo["elapsed_s"] = round(time.time() - t0, 1)
        out[str(y)] = yo
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
