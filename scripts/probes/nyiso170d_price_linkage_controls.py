"""nyiso-170d — third-factor controls on the ONE surviving positive finding.

ZERO SOLVE. Imports its instruments from ``nyiso170_merit_order_coincidence``.

Rule 22 ``[R-HOLDOUT]``: every year read is 2023, 2024 or 2025.
Rule 13 ``[R-MEASURED]``: CAMPD enters as conduct identification only.

Why this exists
---------------
nyiso-170 / 170b / 170c falsified the DISPLACEMENT hypothesis: the CC over-run
and the CT/ST under-run are not the same hours, on the raw test (J1 at or below
its own circular-shift null in all three years) or the load-controlled test
(J4 mean within-decile r -0.153 in 2025, 1 of 10 deciles positive). Exactly ONE
positive finding survives: nyiso-170 G3, upheld by nyiso-170b H2 against the
load channel — inside narrow load slices, the hours the model runs a higher CC
share of its gas are the hours it under-prices, partial r|load
-0.243 / -0.316 / -0.257.

**A finding handed to a successor as a named object must survive more than the
one confounder its author happened to think of.** Load was the obvious channel.
It is not the only one: within a load decile, an hour's gas price, its net
import level and its renewable output all move BOTH the model's gas
composition AND its price. This probe attacks the surviving finding with those,
and with a within-decile permutation null. It can only weaken the finding.

PRE-REGISTERED GATES
--------------------
**K1 — FULL PARTIAL CORRELATION.** Residualise ds_CC and the model-minus-actual
DA gap on the full design [1, load, load^2, load^3, gas, gas^2, load*gas,
net_import, renewables] by OLS, then correlate the residuals. SURVIVES iff the
partial correlation is negative in all three years and retains at least half the
magnitude of the load-only partial (nyiso-170b H2).

**K2 — RANK ROBUSTNESS.** Spearman rho of the same residual pair, so a handful
of extreme hours cannot carry the result. SURVIVES iff negative in all three.

**K3 — WITHIN-DECILE PERMUTATION NULL.** Inside each load decile, permute ds_CC
199 times and recompute nyiso-170b H2's top-minus-bottom-quartile gap spread.
SURVIVES iff the observed spread is below the null's 5th percentile in at least
6 of 10 deciles, in all three years.

If K1-K3 fail, the surviving finding is withdrawn too and nyiso-170 hands
forward a pure null. If they hold, the object handed forward is a MEASURED
composition-price association, explicitly NOT a demonstrated causal mechanism.

Run: ``PYTHONPATH=.:src python scripts/probes/nyiso170d_price_linkage_controls.py``
Writes: ``results/calibration/_nyiso170d_price_linkage_controls.json``
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

from scripts.probes.nyiso170_merit_order_coincidence import (  # noqa: E402
    ACTUAL_HOURLY,
    GAS_CLASSES,
    KEEPER,
    YEARS,
    build_series,
    chp_plants,
    hourly_gas,
    keeper_system,
)

OUT = REPO / "results/calibration/_nyiso170d_price_linkage_controls.json"

N_PERM = 199
PERM_SEED = 1704
K3_MIN_DECILES = 6
#: nyiso-170b H2's load-only partial, the magnitude K1 must half-retain.
H2_PARTIAL = {2023: -0.243, 2024: -0.316, 2025: -0.257}


def other_classes(year: int) -> tuple[np.ndarray, np.ndarray]:
    """Model hourly net imports and total renewables from the keeper sidecar."""
    c = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
    c = c[c["pass"] == "P1"]
    p = c.pivot_table(index="hour", columns="klass", values="mw", observed=True)
    p = p.reindex(range(8760)).fillna(0.0)
    imp = p["import"].to_numpy(float) if "import" in p else np.zeros(8760)
    ren = np.zeros(8760)
    for k in ("hydro", "wind", "solar"):
        if k in p:
            ren = ren + p[k].to_numpy(float)
    return imp, ren


def _resid(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return y - X @ beta


def ds_and_gap(model, meas, mprice, da):
    """Hourly CC-share excess and the model-minus-actual DA price gap."""
    gm = np.sum([model[k] for k in GAS_CLASSES], axis=0)
    gx = np.sum([meas[k] for k in GAS_CLASSES], axis=0)
    cm = np.divide(model["CC_CHP"] + model["CC_REGULAR"], gm, out=np.zeros(8760), where=gm > 0)
    cx = np.divide(meas["CC_CHP"] + meas["CC_REGULAR"], gx, out=np.zeros(8760), where=gx > 0)
    return cm - cx, mprice - da


def main() -> None:
    chpset = chp_plants()
    act = pd.read_parquet(ACTUAL_HOURLY)
    rec: dict = {
        "probe": "nyiso170d_price_linkage_controls",
        "keeper": "2026-08-30-nyiso-159-loss-surface",
        "years": list(YEARS),
        "note": (
            "Zero solve. Third-factor controls on the ONE positive finding that "
            "survived nyiso-170/170b/170c: the within-load association between "
            "the model's gas-composition error and its price deficit. Gates "
            "pre-registered in the module docstring, committed before running. "
            "These can only weaken the finding."
        ),
        "gate_thresholds": dict(
            n_perm=N_PERM, perm_seed=PERM_SEED, K3_min_deciles=K3_MIN_DECILES,
            h2_load_only_partial=H2_PARTIAL,
        ),
        "by_year": {},
    }

    for year in YEARS:
        model, meas, _ = build_series(year, chpset)
        load, mprice = keeper_system(year)
        a = act[act["year"] == year].sort_values("hour")
        da = a["da"].to_numpy(float)
        gas = hourly_gas(year)
        imp, ren = other_classes(year)

        ds, gap = ds_and_gap(model, meas, mprice, da)
        ok = np.isfinite(ds) & np.isfinite(gap) & np.isfinite(gas)
        L, G = load[ok], gas[ok]
        X = np.column_stack(
            [np.ones(L.size), L, L**2, L**3, G, G**2, L * G, imp[ok], ren[ok]]
        )
        rs, rg = _resid(ds[ok], X), _resid(gap[ok], X)
        k1 = float(np.corrcoef(rs, rg)[0, 1])
        k2 = float(
            np.corrcoef(
                pd.Series(rs).rank().to_numpy(), pd.Series(rg).rank().to_numpy()
            )[0, 1]
        )

        rng = np.random.default_rng(PERM_SEED)
        order = np.argsort(load)
        dec_rows, n_beat = [], 0
        for k in range(10):
            idx = order[int(8760 * k / 10) : int(8760 * (k + 1) / 10)]
            idx = idx[ok[idx]]
            if len(idx) < 40:
                dec_rows.append(dict(decile=k, n=len(idx), observed=None))
                continue
            d_, g_ = ds[idx], gap[idx]
            q = max(len(idx) // 4, 1)

            def spread(v: np.ndarray) -> float:
                o = np.argsort(v)
                return float(np.mean(g_[o[-q:]]) - np.mean(g_[o[:q]]))

            obs = spread(d_)
            null = np.array([spread(rng.permutation(d_)) for _ in range(N_PERM)])
            p5 = float(np.percentile(null, 5))
            beat = bool(obs < p5)
            n_beat += int(beat)
            dec_rows.append(
                dict(
                    decile=k,
                    n=len(idx),
                    observed=round(obs, 2),
                    null_p5=round(p5, 2),
                    null_median=round(float(np.median(null)), 2),
                    beats_null=beat,
                )
            )

        row = dict(
            K1_full_partial_corr=round(k1, 4),
            K1_load_only_partial=H2_PARTIAL[year],
            K1_magnitude_retained=round(k1 / H2_PARTIAL[year], 3),
            K1_survives=bool(k1 < 0 and abs(k1) >= 0.5 * abs(H2_PARTIAL[year])),
            K2_spearman_partial=round(k2, 4),
            K2_survives=bool(k2 < 0),
            K3_within_decile=dec_rows,
            K3_deciles_beating_null=n_beat,
            K3_survives=bool(n_beat >= K3_MIN_DECILES),
        )
        rec["by_year"][str(year)] = row
        print(f"\n{year}")
        print(
            f"  K1 full partial r {k1:+.4f} vs load-only {H2_PARTIAL[year]:+.3f}"
            f"  (retained {row['K1_magnitude_retained']:.2f}x)   SURVIVES: {row['K1_survives']}"
        )
        print(f"  K2 Spearman on residuals {k2:+.4f}   SURVIVES: {row['K2_survives']}")
        print(
            f"  K3 deciles beating permutation null {n_beat}/10   SURVIVES: {row['K3_survives']}"
        )

    ys = rec["by_year"]
    rec["verdict"] = {
        f"{g}_all_years": all(ys[str(y)][f"{g}_survives"] for y in YEARS)
        for g in ("K1", "K2", "K3")
    }
    rec["verdict"]["linkage_survives"] = all(rec["verdict"].values())
    OUT.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")
    print(f"\n  VERDICT {json.dumps(rec['verdict'])}")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    raise SystemExit(main())
