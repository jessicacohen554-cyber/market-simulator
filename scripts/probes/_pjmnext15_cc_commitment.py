"""PJM-NEXT-15 card 2 (zero LP): is the keeper's CC over-run a COMMITMENT defect?

For every CC_REGULAR bench plant and every year 2019-2025, compares the keeper's hourly
model profile (registered payload ``runs/2026-09-28-pjm-next8-exitfix.js``, ``m`` rescaled
to ``m_ann``) with CAMPD hourly (bench ``campd`` rescaled to the EIA-923 net annual,
``e_ann``; ``c_ann`` if absent), the same basis pjm-h21 used.

Per plant: on-hours (output > ``ON_FRAC`` x nameplate), starts (off->on transitions after an
off-run of at least ``MIN_OFF_H`` hours, so byte noise is not a start), mean run length,
mean loading when on, and the model-minus-actual energy split exactly into
  ON-HOURS  = (H_mod - H_act) x L_act     and     LOADING = H_mod x (L_mod - L_act).
The model's extra on-hours (model on, actual off) are bucketed by the length of the ACTUAL
off-run that contains them: < 24 h (cycled off overnight/weekend), 1-7 d, >= 7 d.

Aggregated per year by actual-CF third (plant-weighted by nameplate, ranked by actual CF
within the year) and by zone. Writes ``results/phase0/pjm/_pjmnext15_cc_commitment.json``.

Stated limits: plant level, not unit level (a 2x1 CC running one CT is "on"); CAMPD bytes
are 1 % CF, so ``ON_FRAC`` is re-run at 2 % and 10 %.
"""

from __future__ import annotations

import base64
import gzip
import json
import re
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
BENCH = REPO / "frontend/data/backcast/bench/PJM"
RUN = REPO / "frontend/data/backcast/runs/2026-09-28-pjm-next8-exitfix.js"
OUT = REPO / "results/phase0/pjm/_pjmnext15_cc_commitment.json"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
KLASS = "CC_REGULAR"
ON_FRACS = (0.02, 0.05, 0.10)
ON_FRAC = 0.05
MIN_OFF_H = 3
SHORT_H, LONG_H = 24, 24 * 7


def _payload(path: Path) -> dict:
    """Decode a registered run payload."""
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', path.read_text())
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def _dec(b64: str, ann_twh: float | None) -> np.ndarray:
    """Decode CF-percent bytes and rescale to the annual TWh total (MW per hour)."""
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)
    tot = raw.sum()
    return raw * (float(ann_twh) * 1e6 / tot) if ann_twh and tot > 0 else raw * 0.0


def _runs(on: np.ndarray) -> list[tuple[int, int]]:
    """(start, end) of contiguous True runs."""
    idx = np.flatnonzero(np.diff(np.r_[0, on.astype(int), 0]))
    return list(zip(idx[::2], idx[1::2]))


def _offrun_len(on: np.ndarray) -> np.ndarray:
    """Per hour, the length of the contiguous OFF run containing it (0 if on)."""
    out = np.zeros(on.size, dtype=int)
    for s, e in _runs(~on):
        out[s:e] = e - s
    return out


def _starts(on: np.ndarray) -> tuple[int, float]:
    """Starts after an off-run >= MIN_OFF_H, and mean on-run length (h)."""
    on = on.copy()
    for s, e in _runs(~on):  # fill short off gaps so byte noise is not a start
        if e - s < MIN_OFF_H and s > 0 and e < on.size:
            on[s:e] = True
    r = _runs(on)
    n = len(r) - (1 if r and r[0][0] == 0 else 0)
    return n, float(np.mean([e - s for s, e in r])) if r else 0.0


def _plant(mod: np.ndarray, act: np.ndarray, npl: float, frac: float) -> dict:
    """Commitment statistics for one plant-year."""
    thr = frac * npl
    on_m, on_a = mod > thr, act > thr
    hm, ha = int(on_m.sum()), int(on_a.sum())
    lm = float(mod[on_m].mean()) if hm else 0.0
    la = float(act[on_a].mean()) if ha else 0.0
    offlen = _offrun_len(on_a)
    extra = on_m & ~on_a
    sm, rm = _starts(on_m)
    sa, ra = _starts(on_a)
    return dict(
        e_mod=float(mod.sum()) / 1e6,
        e_act=float(act.sum()) / 1e6,
        h_mod=hm,
        h_act=ha,
        l_mod_frac=lm / npl if npl else 0.0,
        l_act_frac=la / npl if npl else 0.0,
        on_eff=(hm - ha) * la / 1e6,
        load_eff=hm * (lm - la) / 1e6,
        starts_mod=sm,
        starts_act=sa,
        run_mod=rm,
        run_act=ra,
        extra_short=float(mod[extra & (offlen < SHORT_H)].sum()) / 1e6,
        extra_med=float(mod[extra & (offlen >= SHORT_H) & (offlen < LONG_H)].sum())
        / 1e6,
        extra_long=float(mod[extra & (offlen >= LONG_H)].sum()) / 1e6,
        missing=float(act[on_a & ~on_m].sum()) / 1e6,
    )


SUMS = (
    "npl",
    "e_mod",
    "e_act",
    "on_eff",
    "load_eff",
    "extra_short",
    "extra_med",
    "extra_long",
    "missing",
    "starts_mod",
    "starts_act",
)


def _agg(rows: list[dict]) -> dict:
    """Sum energy/starts; nameplate-weight hours, loading and run length."""
    if not rows:
        return {}
    w = np.array([r["npl"] for r in rows])
    out = {k: round(float(sum(r[k] for r in rows)), 2) for k in SUMS}
    for k in (
        "h_mod",
        "h_act",
        "l_mod_frac",
        "l_act_frac",
        "run_mod",
        "run_act",
    ):
        out[k] = round(float(np.average([r[k] for r in rows], weights=w)), 3)
    out["n"] = len(rows)
    out["gap"] = round(out["e_mod"] - out["e_act"], 2)
    return out


def main() -> None:
    """Census every year; write the JSON artifact."""
    pay = {int(y): rec["plants"] for y, rec in _payload(RUN)["years"].items()}
    res = {
        "what": "PJM-NEXT-15 card 2 - CC_REGULAR commitment census vs CAMPD. ZERO LP.",
        "keeper": "2026-09-28-pjm-next8-exitfix",
        "on_frac": ON_FRAC,
        "min_off_h": MIN_OFF_H,
        "years": {},
    }
    for y in YEARS:
        bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]
        rows = {f: [] for f in ON_FRACS}
        for pid, bp in bench["plants"].items():
            if bp.get("group") != KLASS or bp.get("nodata") or not bp.get("campd"):
                continue
            npl = float(bp.get("npl") or 0.0)
            kp = pay[y].get(pid, {})
            if npl <= 0 or not kp.get("m"):
                continue
            act = _dec(bp["campd"], bp.get("e_ann") or bp.get("c_ann"))
            mod = _dec(kp["m"], kp.get("m_ann"))
            for f in ON_FRACS:
                r = _plant(mod, act, npl, f)
                r.update(pid=pid, zone=bp.get("zone", "").replace("PJM_", ""), npl=npl)
                r["cf_act"] = r["e_act"] * 1e6 / (npl * 8760)
                rows[f].append(r)
        base = rows[ON_FRAC]
        order = sorted(base, key=lambda r: r["cf_act"])
        cw = np.cumsum([r["npl"] for r in order]) / sum(r["npl"] for r in order)
        third = {r["pid"]: min(int(c * 3 - 1e-9), 2) for r, c in zip(order, cw)}
        rec = {
            "class_actual_twh": float(bench["classFull"].get(KLASS, 0.0)),
            "all": _agg(base),
            "all_by_on_frac": {str(f): _agg(rows[f]) for f in ON_FRACS},
            "cf_third": {
                t: _agg([r for r in base if third[r["pid"]] == i])
                for i, t in enumerate(("low", "mid", "high"))
            },
            "zone": {
                z: _agg([r for r in base if r["zone"] == z])
                for z in sorted({r["zone"] for r in base})
            },
            "low_third_by_zone": {
                z: _agg([r for r in base if r["zone"] == z and third[r["pid"]] == 0])
                for z in sorted({r["zone"] for r in base})
            },
            "top_plants_gap": sorted(
                (
                    {
                        k: (round(v, 3) if isinstance(v, float) else v)
                        for k, v in r.items()
                    }
                    for r in base
                ),
                key=lambda r: -(r["e_mod"] - r["e_act"]),
            )[:15],
        }
        res["years"][str(y)] = rec
        a = rec["all"]
        print(
            y,
            f"gap {a['gap']:+.1f} on {a['on_eff']:+.1f} load {a['load_eff']:+.1f}",
            f"starts mod/act {a['starts_mod']:.0f}/{a['starts_act']:.0f}",
            f"h {a['h_mod']:.0f}/{a['h_act']:.0f}",
            f"L {a['l_mod_frac']:.2f}/{a['l_act_frac']:.2f}",
            f"extra s/m/l {a['extra_short']:.1f}/{a['extra_med']:.1f}/{a['extra_long']:.1f}",
            flush=True,
        )
        for t, v in rec["cf_third"].items():
            print(
                f"   {t:4s} gap {v['gap']:+.1f} on {v['on_eff']:+.1f} load {v['load_eff']:+.1f}"
                f" h {v['h_mod']:.0f}/{v['h_act']:.0f} st {v['starts_mod']:.0f}/{v['starts_act']:.0f}"
                f" run {v['run_mod']:.0f}/{v['run_act']:.0f} L {v['l_mod_frac']:.2f}/{v['l_act_frac']:.2f}"
                f" xl {v['extra_short']:.1f}/{v['extra_med']:.1f}/{v['extra_long']:.1f}"
            )
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
