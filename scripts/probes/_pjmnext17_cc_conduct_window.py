"""PJM-NEXT-17 card 2 (zero LP): a plant-conduct window for ``cc_mustrun_per_plant``.

The keeper places each CC_REGULAR plant's committed floor in the top
``round(online_frac x 8760)`` hours ranked by SYSTEM load. The candidate keeps that SIZE and
level, and ranks hours instead by the plant's OWN measured online probability in the hour's
conduct cell, pooled over the OTHER bench years (leave-one-year-out: no same-year outcome
enters, rule 13), ties broken by system load.

Two cell grains are scored by held-out conduct log-loss ONLY (never by a C1/price residual):
``mh`` = month x hour-of-day (288 cells), ``mdh`` = month x weekday/weekend x hour-of-day (576).

Per year it reports, keeper window vs conduct window: floored plant-hours and committed-MW
MWh where the plant's CAMPD meter reads offline (< 1 % nameplate, the deriver's
``_SYNC_MW_NAMEPLATE_FRAC``), i.e. the rule-17 conduct rider. Sources: committed
``thermal_tranches_PJM.csv`` (online_frac, committed_pct), bench CAMPD hourly, keeper
``hourly/system_<y>.parquet`` load. Writes ``results/phase0/pjm/_pjmnext17_cc_conduct_window.json``.
"""

from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BENCH = REPO / "frontend/data/backcast/bench/PJM"
HOURLY = REPO / "results/calibration/pjmnext16_A_span/hourly"
TRANCHES = REPO / "data/raw/_processed-legacy/thermal_tranches_PJM.csv"
OUT = REPO / "results/phase0/pjm/_pjmnext17_cc_conduct_window.json"
YEARS = tuple(range(2019, 2026))
SYNC = 0.01  # derive_thermal_tranches._SYNC_MW_NAMEPLATE_FRAC
T = 8760
EPS = 1e-3


def _cells(y: int) -> dict[str, np.ndarray]:
    """Conduct-cell index per hour of year *y* for each grain."""
    ts = pd.date_range(f"{y}-01-01", periods=T, freq="h")
    m, h = ts.month.values - 1, ts.hour.values
    we = (ts.dayofweek.values >= 5).astype(int)
    return {"mh": m * 24 + h, "mdh": (m * 2 + we) * 24 + h}


def _on(y: int) -> dict[int, np.ndarray]:
    """Per CC_REGULAR plant: hourly online mask from the bench CAMPD trace."""
    b = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
    out = {}
    for pid, bp in b.items():
        if bp.get("group") != "CC_REGULAR" or bp.get("nodata") or not bp.get("campd"):
            continue
        raw = np.frombuffer(base64.b64decode(bp["campd"]), dtype=np.uint8).astype(float)
        if raw.size != T or raw.max() <= 0:
            continue
        # campd bytes are CF-percent of nameplate, so 1 % of nameplate is byte >= 1.
        # Split-plant keys read "<plant>:<group>".
        out[int(str(pid).split(":")[0])] = raw >= SYNC * 100.0
    return out


def main() -> None:
    """Score both grains and both windows for every bench year."""
    tr = pd.read_csv(TRANCHES)
    tr = tr[(tr.plant_group == "CC_REGULAR") & (tr.online_frac.fillna(0) > 0)]
    frac = dict(zip(tr.plant_code.astype(int), tr.online_frac.astype(float)))
    pmin = dict(
        zip(
            tr.plant_code.astype(int),
            tr.nameplate_mw * tr.committed_pct.fillna(0) / 100,
        )
    )
    on = {y: _on(y) for y in YEARS}
    cells = {y: _cells(y) for y in YEARS}
    prof: dict = {g: {} for g in ("mh", "mdh")}
    for g, n in (("mh", 288), ("mdh", 576)):
        for y in YEARS:
            for pid, o in on[y].items():
                c = cells[y][g]
                prof[g].setdefault(pid, {})[y] = (
                    np.bincount(c, weights=o, minlength=n),
                    np.bincount(c, minlength=n),
                )
    res: dict = {
        "what": "PJM-NEXT-17 card 2 - CC conduct window. ZERO LP.",
        "years": {},
    }
    for y in YEARS:
        sysd = pd.read_parquet(HOURLY / f"system_{y}.parquet")
        load = (
            sysd[sysd["pass"] == "P1"]
            .groupby("hour")
            .demand.sum()
            .reindex(range(T))
            .values
        )
        lrank = np.empty(T)
        lrank[np.argsort(-load, kind="stable")] = np.arange(T)
        rec: dict = {"loglik": {}, "windows": {}}
        tot = {k: [0, 0.0, 0, 0] for k in ("keeper", "mh", "mdh")}
        for g in ("mh", "mdh"):
            ll, nn = 0.0, 0
            for pid, o in on[y].items():
                oth = [v for yy, v in prof[g].get(pid, {}).items() if yy != y]
                if not oth:
                    continue
                p = sum(a for a, _ in oth) / np.maximum(sum(b for _, b in oth), 1)
                ph = np.clip(p[cells[y][g]], EPS, 1 - EPS)
                ll += float(np.sum(o * np.log(ph) + (~o) * np.log(1 - ph)))
                nn += T
            rec["loglik"][g] = round(ll / max(nn, 1), 4)
        for pid, o in on[y].items():
            if pid not in frac or pmin.get(pid, 0) <= 0:
                continue
            k = int(round(frac[pid] * T))
            if k <= 0:
                continue
            wins = {"keeper": np.argsort(lrank)[:k]}
            for g in ("mh", "mdh"):
                oth = [v for yy, v in prof[g].get(pid, {}).items() if yy != y]
                if not oth:
                    wins[g] = wins["keeper"]
                    continue
                p = sum(a for a, _ in oth) / np.maximum(sum(b for _, b in oth), 1)
                # Rank by conduct probability (desc), ties by system-load rank.
                order = np.lexsort((lrank, -p[cells[y][g]]))
                wins[g] = order[:k]
            for name, w in wins.items():
                off = ~o[w]
                t = tot[name]
                t[0] += int(off.sum())
                t[1] += float(off.sum() * pmin[pid])
                t[2] += k
                t[3] += 1
        rec["windows"] = {
            n: {
                "plants": v[3],
                "floored_h": v[2],
                "off_h": v[0],
                "off_share": round(v[0] / max(v[2], 1), 4),
                "off_floor_twh": round(v[1] / 1e6, 2),
            }
            for n, v in tot.items()
        }
        res["years"][str(y)] = rec
        w = rec["windows"]
        print(
            y,
            "loglik",
            rec["loglik"],
            "| off-share keeper/mh/mdh",
            w["keeper"]["off_share"],
            w["mh"]["off_share"],
            w["mdh"]["off_share"],
            "| off-floor TWh",
            w["keeper"]["off_floor_twh"],
            w["mh"]["off_floor_twh"],
            w["mdh"]["off_floor_twh"],
            "| plants",
            w["keeper"]["plants"],
            flush=True,
        )
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
