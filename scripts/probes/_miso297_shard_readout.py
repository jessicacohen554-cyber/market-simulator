#!/usr/bin/env python3
"""miso-297 kill-rule readout (ZERO LP): K-3 and K-4 on a solved bundle.

For each year of a bundle (a composed span or a single leg):

* **K-3** — the coal marginal share: the share of hours in which a coal row is
  the marginal row of the P1 bid stack (the bundle's OWN recipe rebuilt
  ``fleet_only``, base offers + the miso-287 startup markup from the P0 clear)
  cleared at the bundle's OWN P1 thermal quantity. The miso-296 block-B /
  miso-297 census statistic, beside the IMM SOM Table 1 coal SMP share.
* **K-4** — the quintile-1-2 load-weighted price error: the bundle's P1 zonal
  prices against the zone-resolved actual, both weighted by the measured zonal
  demand (the miso-296 block-A construction); quintiles of measured load.

Run it on the keeper and on the arm span and compare; the PRECOMMIT's K-3
(toward IMM in >= 5 of 6 published years) and K-4 (shrinks in 2019 / 2020 /
2023 / 2024) read off the two JSONs.

Usage (repo root)::

    uv run python scripts/probes/_miso297_shard_readout.py \\
        --bundle results/calibration/miso_297_span --out results/phase0/miso/_miso297_readout_arm.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(REPO / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes import _miso271_cc_decomp as dec  # noqa: E402
from scripts.probes import _miso297_joint_census as J  # noqa: E402
from scripts.probes._miso296_lowload_stack import (  # noqa: E402
    IMM_SMP_SHARE,
    INTERNAL,
    NON_LP,
    T,
    family,
    zone_actual,
)


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    from scripts.data import derive_actual_lmp as dal  # noqa: E402
    from scripts.run_calibration import _load_reference  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    bundle = REPO / args.bundle
    dec.KEEPER = bundle  # the bundle's OWN recipe (meta.json + per-year overlay)
    out_path = Path(args.out)
    out = json.loads(out_path.read_text()) if out_path.exists() else {}
    famv = np.vectorize(family)
    for y in args.years:
        if not (bundle / f"hourly/class_hourly_{y}.parquet").exists():
            print(y, "no sidecar; skipped")
            continue
        hh = _henry_hub_actual(_load_reference(), y)
        b = J.rebuild(y, hh, {})
        sc = json.loads(
            (
                bundle / f"run_config_{y}.json"
                if (bundle / f"run_config_{y}.json").exists()
                else bundle / "run_config.json"
            ).read_text()
        )["scenario_config"]
        ch = pd.read_parquet(bundle / f"hourly/class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"]
        q = (
            ch[~ch.klass.astype(str).isin(NON_LP)]
            .groupby("hour")
            .mw.sum()
            .reindex(range(T))
            .fillna(0)
            .to_numpy()
        )
        p0, m0, d0 = J.clear_vec(b["mc"], b["mg"], b["flex"], q)
        mk = J.markup_for(b, d0)
        p1, m1, d1 = J.clear_vec(b["mc"] + mk, b["mg"], b["flex"], q)
        fam_row = famv(b["lab"])
        w = dal._measured_zone_demand("MISO", y)
        assert w is not None and w.shape == (6, T), w.shape
        load = w.sum(axis=0)
        q5 = pd.qcut(load, 5, labels=False)
        pa = zone_actual(y)
        ok = ~np.isnan(pa).any(axis=0)
        lw_a = (pa * w).sum(0) / w.sum(0)
        s = pd.read_parquet(bundle / f"hourly/system_{y}.parquet")
        s = s[s["pass"] == "P1"]
        pz = s.pivot(index="hour", columns="zone", values="price").sort_index()
        pm = pz[INTERNAL].to_numpy().T
        lw_m = (pm * w).sum(0) / w.sum(0)
        wt = np.where(ok, load, 0.0)

        def census(marg, mask):
            v = pd.Series(fam_row[marg[mask]]).value_counts(normalize=True)
            return {k: J._r(x) for k, x in v.items()}

        def lw_err(mask):
            mk_ = mask & ok
            return J._r(((lw_m - lw_a)[mk_] * wt[mk_]).sum() / wt[mk_].sum())

        allm = np.ones(T, bool)
        out[str(y)] = {
            "config": {
                k: sc.get(k)
                for k in (
                    "miso_gas_marginal_commodity_pricing",
                    "miso_gas_variable_transport",
                )
            },
            "coal_econ_bands": {
                g: {
                    b_: sc["offer_curve_by_group"][g][b_]
                    for b_ in ("econ_low", "econ_high")
                }
                for g in ("COAL_PRB", "COAL_BIT", "COAL_LIGNITE", "COAL_WC")
            },
            "imm_coal": (IMM_SMP_SHARE.get(y) or {}).get("coal"),
            "k3": {
                "bid_all": census(m1, allm),
                "p0_all": census(m0, allm),
                "bid_q": {f"q{i + 1}": census(m1, q5 == i) for i in range(5)},
                "bid_vs_p1_median_q12": {
                    "bid": J._r(np.median(p1[q5 <= 1])),
                    "p1": J._r(np.median(lw_m[q5 <= 1])),
                },
            },
            "k4": {
                "lw_err_q12": lw_err(q5 <= 1),
                "lw_err_q1": lw_err(q5 == 0),
                "lw_err_q2": lw_err(q5 == 1),
                "lw_err_q5": lw_err(q5 == 4),
                "lw_err_all": lw_err(allm),
                "model_lw": J._r((lw_m[ok] * wt[ok]).sum() / wt.sum()),
                "actual_lw": J._r((lw_a[ok] * wt[ok]).sum() / wt.sum()),
                "coverage_hours": int(ok.sum()),
            },
        }
        print(
            y,
            "K3 bid coal",
            out[str(y)]["k3"]["bid_all"].get("coal"),
            "imm",
            out[str(y)]["imm_coal"],
            "K4 q12 err",
            out[str(y)]["k4"]["lw_err_q12"],
            "all",
            out[str(y)]["k4"]["lw_err_all"],
            flush=True,
        )
        out_path.write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
