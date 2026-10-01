"""PJM-NEXT-9 card 1 zero-LP phase 0: which binding constraints price the NJ hub
below Western, and Dominion above it?

Joins PJM's own day-ahead binding-constraint record
(``data/raw/pjm-binding-constraints/da_marginal_value_<y>_<m>.parquet``, gitignored,
re-fetch with ``scripts/data/fetch_pjm_binding_constraints.py``) to the DA hub
congestion components (``data/clean/lmp/PJM/DAM``). A hub's congestion component
is a linear combination of the binding constraints' shadow prices,
``MCC_hub,t = sum_k beta_k,hub * mu_k,t`` with ``beta`` the (negated) shift
factor. Shift factors are not published, so ``beta`` is recovered per year by
least squares over the top constraints by absolute rent, and each constraint's
contribution to a hub SPREAD is ``beta_k * mean_t(mu_k,t)``.

Outputs: fit R^2 per spread, the top-N constraints by contribution to the
NJ-Western and Dominion-Western DA congestion spreads, and the same aggregated
by monitored facility. Zero LP, no model input read.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BC = REPO / "data/raw/pjm-binding-constraints"
DAM = REPO / "data/clean/lmp/PJM/DAM"
OUT = REPO / "results/phase0/pjm/_pjmnext9_congestion_boundary.json"
N_TOP = 250  # constraints kept in the regression (by sum |mu|); ~>95 % of rent
# The Peach Bottom / Conastone (PECO+PPL -> BGE) corridor facilities named by the 2023 ranking.
CORRIDOR = r"NOTTINGH|GRACETON|CONASTON|Yorkana|PEACHBOT|SAFEHARB"
SPREADS = {
    "NJ-Western": ("NEW JERSEY HUB", "WESTERN HUB"),
    "Eastern-Western": ("EASTERN HUB", "WESTERN HUB"),
    "Dominion-Western": ("DOMINION HUB", "WESTERN HUB"),
    "NJ-Dominion": ("NEW JERSEY HUB", "DOMINION HUB"),
}


def load_mu(y: int) -> pd.DataFrame:
    """Hour x constraint shadow-price matrix (0 where not binding), UTC index."""
    fs = sorted(BC.glob(f"da_marginal_value_{y}_*.parquet"))
    d = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    d["t"] = pd.to_datetime(
        d.datetime_beginning_utc, format="%m/%d/%Y %I:%M:%S %p", utc=True
    )
    d["k"] = (
        d.monitored_facility.str.strip()
        + " | "
        + d.contingency_facility.fillna("").str.strip()
    )
    return d.pivot_table(
        index="t", columns="k", values="shadow_price", aggfunc="sum"
    ).fillna(0.0)


def load_hubs(y: int) -> pd.DataFrame:
    """Hour x hub DA congestion component, UTC index."""
    lm = pd.read_parquet(DAM / f"lmp_{y}.parquet")
    lm = lm[lm.interval_start_utc.dt.year == y]
    return lm.pivot_table(
        index="interval_start_utc", columns="node", values="congestion_usd_per_mwh"
    )


def main() -> None:
    """Fit per-year constraint loadings on each hub spread and rank contributions."""
    R: dict = {}
    for y in range(2019, 2026):
        mu = load_mu(y)
        hub = load_hubs(y)
        idx = hub.index
        mu = mu.reindex(idx).fillna(0.0)
        rent = mu.abs().sum().sort_values(ascending=False)
        keep = rent.index[:N_TOP]
        X = mu[keep].to_numpy()
        yr: dict = {
            "hours": int(len(idx)),
            "constraints_total": int(mu.shape[1]),
            "rent_share_kept": round(float(rent.iloc[:N_TOP].sum() / rent.sum()), 4),
            "spreads": {},
        }
        for name, (a, b) in SPREADS.items():
            s = (hub[a] - hub[b]).to_numpy()
            ok = np.isfinite(s)
            beta, *_ = np.linalg.lstsq(X[ok], s[ok], rcond=None)
            fit = X[ok] @ beta
            r2 = 1 - ((s[ok] - fit) ** 2).sum() / ((s[ok] - s[ok].mean()) ** 2).sum()
            contrib = pd.Series(beta * X[ok].mean(axis=0), index=keep)
            fac = contrib.groupby(keep.str.split(" | ", regex=False).str[0]).sum()
            yr["spreads"][name] = {
                "mean_spread": round(float(s[ok].mean()), 3),
                "fit_mean": round(float(fit.mean()), 3),
                "r2": round(float(r2), 3),
                "top_constraints": [
                    {
                        "k": k,
                        "contrib": round(float(v), 3),
                        "beta": round(float(beta[keep.get_loc(k)]), 3),
                        "bind_h": int((mu[k] != 0).sum()),
                        "mean_mu": round(float(mu[k].mean()), 3),
                    }
                    for k, v in contrib.reindex(
                        contrib.abs().sort_values(ascending=False).index
                    )[:15].items()
                ],
                "corridor_share": round(
                    float(
                        contrib[keep.str.contains(CORRIDOR, regex=True)].sum()
                        / s[ok].mean()
                    ),
                    3,
                ),
                "top_facilities": {
                    k: round(float(v), 3)
                    for k, v in fac.reindex(
                        fac.abs().sort_values(ascending=False).index
                    )[:15].items()
                },
            }
        R[y] = yr
    OUT.write_text(json.dumps(R, indent=1))
    for y, yr in R.items():
        print(
            f"== {y}: {yr['hours']} h, {yr['constraints_total']} constraints, kept rent share {yr['rent_share_kept']}"
        )
        for name, sp in yr["spreads"].items():
            print(
                f"  {name}: mean {sp['mean_spread']} fit {sp['fit_mean']} R2 {sp['r2']} corridor {sp['corridor_share']}"
            )
            for f, v in list(sp["top_facilities"].items())[:5]:
                print(f"     {v:+7.3f}  {f}")


if __name__ == "__main__":
    sys.exit(main())
