"""NYISO-NEXT-12 G-2 (a) / (c) and G-4 (ZERO LP): each arm leg vs the keeper's committed hourlies.

``docs/records/nyiso/PRECOMMIT-nyiso-next11-ne-ac-node-2026-09-28.md`` sec. 6:

G-2 (a): in P1 the NE AC node exports (sum of its ``_exp#`` rows < 0) in >= 1 h AND
     imports (sum of its ``_imp#`` rows > 0) in >= 1 h, every year.
G-2 (c): |annual import-class TWh (arm - keeper)| <= 4 % of the keeper's, every year.
G-4 (reported, not a criterion): per-zone load-weighted P1 price move; class TWh moves;
     the node's net TWh vs the measured tie; hours the node sits at a posted bound.
G-2 (b) is ``nyisonext12_g2b.py``. Record: ``results/phase0/nyiso/_nyisonext12_gates.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO / "src", REPO):
    sys.path.insert(0, str(p))

KEEP = {
    2021: "nyisonext9_2021",
    **{y: "nyisonext9_span" for y in (2022, 2023, 2024, 2025)},
}
G2C_FRAC = 0.04
#: measured NE AC net tie, TWh (PRECOMMIT sec. 4; + = import into NYISO)
MEASURED_NE_TWH = {2021: -5.17, 2022: -3.51, 2023: -4.47, 2024: -5.84, 2025: -5.76}
NODE = "NYISO_NE_AC_"


def _sys(b: str, y: int) -> pd.DataFrame:
    s = pd.read_parquet(REPO / f"results/calibration/{b}/hourly/system_{y}.parquet")
    return s[s["pass"] == "P1"]


def _cls(b: str, y: int) -> pd.DataFrame:
    c = pd.read_parquet(
        REPO / f"results/calibration/{b}/hourly/class_hourly_{y}.parquet"
    )
    c["klass"] = c["klass"].astype(str)
    return c[c["pass"].astype(str) == "P1"]


def _posted(y: int) -> tuple[np.ndarray, np.ndarray]:
    """Hourly posted import / export limit (MW, both positive) on the node link."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.model.interchange.nyiso import nyiso_ne_ac_posted_ttc_hourly
    from market_sim.model.interchange.spec import (
        NYISO_NE_AC_ZONE,
        apply_interchange_topology,
        get_interchange_spec,
    )

    cfg = ScenarioConfig(iso="NYISO", mode="backcast", nyiso_ne_ac_node=True)
    spec = get_interchange_spec(cfg, "NYISO", year=y)
    topo = apply_interchange_topology(get_iso_config("NYISO"), spec, cfg, year=y)
    ttc = np.array([float(link.ttc_mw) for link in topo.links])
    base = np.broadcast_to(ttc, (8760, ttc.size)).copy()
    fwd, rev = nyiso_ne_ac_posted_ttc_hourly(base, base.copy(), topo, y, 8760)
    i = next(
        k
        for k, link in enumerate(topo.links)
        if NYISO_NE_AC_ZONE in (link.from_zone, link.to_zone)
    )
    return fwd[:, i], rev[:, i]


def year(y: int, arm_bundle: str) -> dict:
    """Gate values for one year."""
    k, a = _sys(KEEP[y], y), _sys(arm_bundle, y)
    out: dict = {"lw_price_delta": {}}
    for z in sorted(set(k.zone.astype(str)) | set(a.zone.astype(str))) + ["system"]:

        def lw(d: pd.DataFrame) -> float | None:
            d = d if z == "system" else d[d.zone.astype(str) == z]
            if d.empty:
                return None
            w = d.demand.sum()
            return float((d.price * d.demand).sum() / w if w else d.price.mean())

        lk, la = lw(k), lw(a)
        out["lw_price_delta"][z] = (
            round(la - lk, 3)
            if lk is not None and la is not None
            else {"arm": la, "keeper": lk}
        )
    ck, ca = _cls(KEEP[y], y), _cls(arm_bundle, y)
    tk, ta = ck.groupby("klass").mw.sum() / 1e6, ca.groupby("klass").mw.sum() / 1e6
    idx = tk.index.union(ta.index)
    d = ta.reindex(idx, fill_value=0) - tk.reindex(idx, fill_value=0)
    out["class_twh_delta"] = {
        i: round(float(v), 4) for i, v in d.items() if abs(v) >= 0.001
    }
    ik = float(ck[ck.klass == "import"].mw.sum())
    ia = float(ca[ca.klass == "import"].mw.sum())
    out["import_twh"] = {
        "keeper": round(ik / 1e6, 4),
        "arm": round(ia / 1e6, 4),
        "delta": round((ia - ik) / 1e6, 4),
    }
    out["G2c_pass"] = bool(abs(ia - ik) <= G2C_FRAC * abs(ik))

    dp = pd.read_parquet(
        REPO / f"results/calibration/{arm_bundle}/dispatch/{y}_P1.parquet",
        columns=["unit_id", "hour", "mw"],
    )
    dp["unit_id"] = dp["unit_id"].astype(str)
    node = dp[dp.unit_id.str.startswith(NODE)]
    exp = (
        node[node.unit_id.str.contains("_exp#")]
        .groupby("hour")
        .mw.sum()
        .reindex(range(8760), fill_value=0.0)
    )
    imp = (
        node[node.unit_id.str.contains("_imp#")]
        .groupby("hour")
        .mw.sum()
        .reindex(range(8760), fill_value=0.0)
    )
    net = imp + exp
    out["node"] = {
        "n_units": int(node.unit_id.nunique()),
        "hours_exporting": int((exp < -1e-6).sum()),
        "hours_importing": int((imp > 1e-6).sum()),
        "export_twh": round(float(exp.sum()) / 1e6, 4),
        "import_twh": round(float(imp.sum()) / 1e6, 4),
        "net_twh": round(float(net.sum()) / 1e6, 4),
        "measured_net_twh": MEASURED_NE_TWH[y],
    }
    try:
        fwd, rev = _posted(y)
        n = net.to_numpy()
        out["node"]["hours_at_posted_import"] = int((n >= fwd - 0.5).sum())
        out["node"]["hours_at_posted_export"] = int((n <= -rev + 0.5).sum())
    except Exception as exc:  # noqa: BLE001 -- reported-only diagnostic
        out["node"]["posted_bound_error"] = str(exc)[:200]
    out["G2a_pass"] = bool(
        out["node"]["hours_exporting"] >= 1 and out["node"]["hours_importing"] >= 1
    )
    return out


if __name__ == "__main__":
    ys = [int(x) for x in sys.argv[1:]] or [2021, 2022, 2023, 2024, 2025]
    res = {y: year(y, f"nyisonext12_{y}") for y in ys}
    p = REPO / "results/phase0/nyiso/_nyisonext12_gates.json"
    old = json.loads(p.read_text()) if p.exists() else {}
    old.update({str(y): v for y, v in res.items()})
    p.write_text(json.dumps(old, indent=1))
    print(json.dumps(res, indent=1))
