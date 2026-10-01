"""SPP-91 stage 1 (ZERO LP): hourly per-plant series of SPP-90's FLAT on-line coal shortfall.

Record: ``docs/records/spp/FINDING-spp-91-flat-coal-headroom-2026-09-27.md``.

Reproduces, per keeper coal plant and hour, SPP-90's ``below_weekcap_flat`` component
(``_spp90_coal_inmoney_conduct.py``, identical definitions): units ON line, output flat
(|dG| <= 2 % of D per hour), below the unit's SAME-WEEK in-money capability ``Cw``. Writes
one ``flat_<year>.npz`` with the plant x hour matrices ``F`` (flat shortfall MW), ``A``
(CEMS gross MW), ``ON`` (on-line demonstrated MW) plus the plant codes, for stage 2
(``_spp91_flat_coal_tests.py``). Reads the SPP-89 stacks only for the keeper's coal plant set.

Usage: ``python scripts/probes/_spp91_flat_coal_series.py --stack-dir <dir> --out-dir <dir>``
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from scripts.probes._spp90_coal_inmoney_conduct import COAL, cems_units  # noqa: E402

YEARS = range(2019, 2026)


def year_series(y: int, sd: Path, lmp_all: pd.DataFrame) -> dict:
    """Plant x hour flat-shortfall, CEMS gross and on-line capability for one year."""
    z = np.load(sd / f"stack_{y}.npz", allow_pickle=False)
    r = np.isin(z["klass"], COAL)
    pc = sorted(set(z["codes"][r].tolist()))
    T = z["cap"].shape[1]
    lmp = lmp_all[lmp_all.year == y].set_index("hour")["rt"].reindex(range(T)).to_numpy(float)
    d = cems_units(y, set(pc))
    units = sorted(d["u"].unique())
    ui = {u: i for i, u in enumerate(units)}
    n = len(units)
    G = np.zeros((n, T))
    ON = np.zeros((n, T), bool)
    FULL = np.zeros((n, T), bool)
    iu = d["u"].map(ui).to_numpy()
    tt = d["t"].to_numpy()
    G[iu, tt] = d["grossLoad"].fillna(0).to_numpy()
    op = d["opTime"].fillna(0).to_numpy()
    ON[iu, tt] = op > 0
    FULL[iu, tt] = op >= 0.999
    D = np.array([np.percentile(G[i][FULL[i] & (G[i] > 0)], 99) if (FULL[i] & (G[i] > 0)).any() else 0.0
                  for i in range(n)])
    wk = np.arange(T) // 168
    inm = lmp >= 30
    W = np.zeros((n, T))
    for w in np.unique(wk):
        s = wk == w
        sel = ON[:, s] & inm[None, s]
        g = np.where(sel, G[:, s], -1.0)
        cap_w = np.where(sel.sum(axis=1) >= 10, g.max(axis=1), D)
        W[:, s] = np.minimum(cap_w, D)[:, None]
    dG = np.diff(G, axis=1, prepend=G[:, :1])
    onsh = np.where(ON, (D[:, None] - G).clip(min=0), 0.0)
    derate = np.minimum(np.where(ON, (D[:, None] - W).clip(min=0), 0.0), onsh)
    below_w = onsh - derate
    flat = ON & (np.abs(dG) <= 0.02 * D[:, None])
    Fu = np.where(flat, below_w, 0.0)
    ufid = np.array([int(u.split(":")[0]) for u in units])
    codes = np.array(sorted(set(ufid.tolist())))
    agg = lambda X: np.stack([X[ufid == c].sum(axis=0) for c in codes])  # noqa: E731
    return {"codes": codes, "F": agg(Fu).astype(np.float32), "A": agg(G).astype(np.float32),
            "ON": agg(np.where(ON, D[:, None], 0.0)).astype(np.float32),
            "Cw": agg(np.where(ON, W, 0.0)).astype(np.float32), "lmp": lmp}


def main() -> int:
    """Write one npz per year."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--stack-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    a = ap.parse_args()
    lmp = pd.read_parquet(RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet")
    a.out_dir.mkdir(parents=True, exist_ok=True)
    for y in a.years:
        r = year_series(y, a.stack_dir, lmp)
        np.savez_compressed(a.out_dir / f"flat_{y}.npz", **r)
        m = r["lmp"] >= 30
        print(y, "plants", len(r["codes"]), "flat GW (>=$30)", round(float(r["F"][:, m].sum(0).mean()) / 1e3, 3), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
