"""pjm-h21 phase 0 — Card D: locate the PJM CC_REGULAR volume defect. ZERO LP.

Rule 32 ``[R-SHARD]`` (a): the parent runs no LP. Every number is read from
artifacts that already exist:

* ACTUAL — the committed PJM bench (``frontend/data/backcast/bench/PJM/<y>.json.gz``):
  per-plant CAMPD hourly profile (``campd``, CF-percent bytes) rescaled to the
  plant's EIA-923 NET annual (``e_ann``; ``c_ann`` if absent), so levels sit on the
  scorer's basis and the CAMPD profile supplies only the hourly SHAPE.
* KEEPER — the registered keeper payloads (``runs/2026-09-23-pjm-h19-dbs-*.js``):
  per-plant hourly model profile (``m``) rescaled to ``m_ann``.
* ARM (level form) — pjm-h20's per-year shard bundles, pulled read-only to a
  scratch dir from their shard SHAs (rule 33(d) provenance): ``unit_hourly`` gives
  per-tranche MW, available capacity ``cap_mw`` and bid ``mc`` per hour, and
  ``floors/<y>_P1.npz`` gives each tranche's hourly ``min_gen`` floor.

Per plant (CC_REGULAR bench plants) the model-minus-actual energy is split
exactly into
  ON-HOURS effect = (H_mod - H_act) x L_act      and
  LOADING effect  = H_mod x (L_mod - L_act),
where H = hours with output > ``ON_FRAC`` x nameplate and L = mean MW when on.
The model's EXTRA on-hours (model on, actual off) are then bucketed by the
length of the ACTUAL off-run containing them: short (< 24 h: a unit PJM cycled
off overnight/weekend), medium (1-7 d), long (>= 7 d: an outage, maintenance or
lay-up window the model's availability does not carry).

STATED LIMITS:
1. ``ON_FRAC`` = 5 % of nameplate is the CAMPD-byte resolution floor (a byte is
   1 % CF) plus margin; the split is re-run at 2 % and 10 % to show it is not
   threshold-driven.
2. Plant level, not unit level: a 3x1 CC running one CT counts as "on" in both.
3. Bench coverage is the bench-matched CC_REGULAR plant set; its coverage of
   the class total is reported, not assumed.

Run: ``python scripts/probes/pjm_h21_cardd_phase0.py <scratch legs dir>``
Writes ``results/calibration/_pjm_h21_cardd_phase0.json``.
"""

from __future__ import annotations

import base64
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BENCH = REPO / "frontend/data/backcast/bench/PJM"
RUNS = {
    "span": REPO / "frontend/data/backcast/runs/2026-09-23-pjm-h19-dbs-span.js",
    "touchpoint": REPO
    / "frontend/data/backcast/runs/2026-09-23-pjm-h19-dbs-touchpoint.js",
}
YEARS = (2020, 2021, 2022, 2023, 2024, 2025)
KLASS = "CC_REGULAR"
ON_FRACS = (0.02, 0.05, 0.10)
ON_FRAC = 0.05
SHORT_H, LONG_H = 24, 24 * 7


def _payload(path: Path) -> dict:
    """Decode a registered run payload (``runs/<id>.js``)."""
    t = path.read_text()
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', t)
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def _dec(b64: str, ann_twh: float | None) -> np.ndarray:
    """Decode CF-percent bytes and rescale to the annual TWh total."""
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)
    tot = raw.sum()
    if ann_twh and tot > 0:
        return raw * (float(ann_twh) * 1e6 / tot)
    return raw


def _run_lengths(off: np.ndarray) -> np.ndarray:
    """Return, per hour, the length of the contiguous True run containing it (0 if False)."""
    out = np.zeros(off.size, dtype=int)
    idx = np.flatnonzero(np.diff(np.r_[0, off.astype(int), 0]))
    for s, e in zip(idx[::2], idx[1::2]):
        out[s:e] = e - s
    return out


def _split(mod: np.ndarray, act: np.ndarray, npl: float, frac: float) -> dict:
    """On-hours / loading decomposition and extra-on-hour bucketing for one plant."""
    thr = frac * npl
    on_m, on_a = mod > thr, act > thr
    hm, ha = int(on_m.sum()), int(on_a.sum())
    lm = float(mod[on_m].mean()) if hm else 0.0
    la = float(act[on_a].mean()) if ha else 0.0
    runlen = _run_lengths(~on_a)
    extra = on_m & ~on_a
    missing = on_a & ~on_m
    return dict(
        h_mod=hm,
        h_act=ha,
        l_mod=lm,
        l_act=la,
        e_mod=float(mod.sum()) / 1e6,
        e_act=float(act.sum()) / 1e6,
        on_eff=(hm - ha) * la / 1e6,
        load_eff=hm * (lm - la) / 1e6,
        extra_h=int(extra.sum()),
        missing_h=int(missing.sum()),
        extra_mwh_short=float(mod[extra & (runlen < SHORT_H)].sum()) / 1e6,
        extra_mwh_med=float(mod[extra & (runlen >= SHORT_H) & (runlen < LONG_H)].sum())
        / 1e6,
        extra_mwh_long=float(mod[extra & (runlen >= LONG_H)].sum()) / 1e6,
        extra_h_long=int((extra & (runlen >= LONG_H)).sum()),
        both_on_excess=float(np.clip(mod - act, 0, None)[on_m & on_a].sum()) / 1e6,
        both_on_short=float(np.clip(act - mod, 0, None)[on_m & on_a].sum()) / 1e6,
        missing_mwh=float(act[missing].sum()) / 1e6,
    )


def _arm_plants(legs: Path, y: int) -> tuple[dict, dict]:
    """Per-plant hourly MW / available cap / floor for the arm's CC_REGULAR tranches."""
    b = legs / f"pjm_h20_cardc_{y}"
    uh = pd.read_parquet(
        b / f"hourly/unit_hourly_{y}.parquet",
        columns=["unit_id", "plant_code", "plant_group", "hour", "mw", "cap_mw", "mc"],
    )
    uh = uh[uh["unit_id"].astype(str).str.startswith(KLASS + "_")]
    fl = np.load(b / f"floors/{y}_P1.npz")
    uid = list(fl["unit_ids"])
    keep = [i for i, u in enumerate(uid) if u.startswith(KLASS + "_")]
    floor = pd.DataFrame({"plant_code": fl["plant_code"][keep]})
    fl_mw = fl["min_gen"][keep]
    out_mw, out_cap, out_fl = {}, {}, {}
    for pc, g in uh.groupby("plant_code", observed=True):
        piv = (
            g.groupby("hour", observed=True)[["mw", "cap_mw"]]
            .sum()
            .reindex(range(8760), fill_value=0.0)
        )
        out_mw[str(pc)] = piv["mw"].to_numpy(float)
        out_cap[str(pc)] = piv["cap_mw"].to_numpy(float)
    for pc, idx in floor.groupby("plant_code").groups.items():
        out_fl[str(pc)] = fl_mw[np.asarray(list(idx))].sum(axis=0).astype(float)
    return {"mw": out_mw, "cap": out_cap, "floor": out_fl}, {}


def main(legs: Path) -> None:
    """Run the census for every year and write the JSON artifact."""
    pay = {}
    for p in RUNS.values():
        for y, rec in _payload(p)["years"].items():
            pay[int(y)] = rec["plants"]
    res = {
        "what": "pjm-h21 Card D phase 0 — CC_REGULAR volume census. ZERO LP.",
        "on_frac": ON_FRAC,
        "years": {},
    }
    for y in YEARS:
        bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]
        class_act = float(bench["classFull"].get(KLASS, 0.0))
        arm, _ = _arm_plants(legs, y)
        rows = []
        for pid, bp in bench["plants"].items():
            if bp.get("group") != KLASS or bp.get("nodata") or not bp.get("campd"):
                continue
            npl = float(bp.get("npl") or 0.0)
            act = _dec(bp["campd"], bp.get("e_ann") or bp.get("c_ann"))
            kp = pay[y].get(pid, {})
            keep = _dec(kp["m"], kp.get("m_ann")) if kp.get("m") else np.zeros(8760)
            pc = pid.split("|")[0].split(":")[0]
            a_mw = arm["mw"].get(pc, np.zeros(8760))
            a_cap = arm["cap"].get(pc, np.zeros(8760))
            a_fl = arm["floor"].get(pc, np.zeros(8760))
            r = dict(
                pid=pid,
                name=bp.get("name", "?")[:26],
                zone=bp.get("zone", "").replace("PJM_", ""),
                npl=npl,
            )
            for tag, mod in (("keeper", keep), ("arm", a_mw)):
                for f in ON_FRACS:
                    s = _split(mod, act, npl, f)
                    for k, v in s.items():
                        r[f"{tag}_{k}" if f == ON_FRAC else f"{tag}_{k}@{f}"] = v
            # availability: model available MWh vs what the plant actually used; hours the model
            # had the plant available while PJM's plant sat in a >=7-day off-run
            off_long = _run_lengths(~(act > ON_FRAC * npl)) >= LONG_H
            r["cap_avail_twh"] = float(a_cap.sum()) / 1e6
            r["cap_avail_h_in_long_off"] = int(
                ((a_cap > ON_FRAC * npl) & off_long).sum()
            )
            r["act_long_off_h"] = int(off_long.sum())
            r["arm_floor_twh"] = float(np.minimum(a_fl, a_mw).sum()) / 1e6
            r["act_p99"] = (
                float(np.quantile(act[act > 0], 0.99)) if (act > 0).any() else 0.0
            )
            r["arm_max"] = float(a_mw.max())
            rows.append(r)
        t = pd.DataFrame(rows)
        tot = lambda c: float(t[c].sum())  # noqa: E731
        yr = dict(
            n_plants=len(t),
            class_act_twh=class_act,
            bench_act_twh=tot("keeper_e_act"),
            npl_gw=tot("npl") / 1e3,
        )
        for tag in ("keeper", "arm"):
            yr[tag] = dict(
                e_mod=tot(f"{tag}_e_mod"),
                e_act=tot(f"{tag}_e_act"),
                delta=tot(f"{tag}_e_mod") - tot(f"{tag}_e_act"),
                on_eff=tot(f"{tag}_on_eff"),
                load_eff=tot(f"{tag}_load_eff"),
                h_mod_capwtd=float((t[f"{tag}_h_mod"] * t.npl).sum() / t.npl.sum()),
                h_act_capwtd=float((t[f"{tag}_h_act"] * t.npl).sum() / t.npl.sum()),
                loadfrac_mod=float((t[f"{tag}_l_mod"]).sum() / t.npl.sum()),
                loadfrac_act=float((t[f"{tag}_l_act"]).sum() / t.npl.sum()),
                extra_short=tot(f"{tag}_extra_mwh_short"),
                extra_med=tot(f"{tag}_extra_mwh_med"),
                extra_long=tot(f"{tag}_extra_mwh_long"),
                both_on_excess=tot(f"{tag}_both_on_excess"),
                both_on_short=tot(f"{tag}_both_on_short"),
                missing=tot(f"{tag}_missing_mwh"),
                sens={
                    str(f): dict(
                        on_eff=tot(f"{tag}_on_eff@{f}"),
                        load_eff=tot(f"{tag}_load_eff@{f}"),
                    )
                    for f in ON_FRACS
                    if f != ON_FRAC
                },
            )
        # Within-class split: plants ranked by their ACTUAL capacity factor (EIA-923 net),
        # equal-count terciles. Shows WHICH CCs carry the model-minus-actual energy.
        t["act_cf"] = t["keeper_e_act"] * 1e6 / (t["npl"] * 8760)
        t["terc"] = pd.qcut(
            t["act_cf"].rank(method="first"), 3, labels=["lowCF", "midCF", "highCF"]
        ).astype(str)
        yr["terciles"] = {}
        for k, g in t.groupby("terc"):
            yr["terciles"][k] = dict(
                n=len(g),
                gw=float(g.npl.sum() / 1e3),
                act_cf=float(g.keeper_e_act.sum() * 1e6 / (g.npl.sum() * 8760)),
                act_twh=float(g.keeper_e_act.sum()),
                **{
                    f"{tag}_{m}": float(g[f"{tag}_{m}"].sum())
                    for tag in ("keeper", "arm")
                    for m in (
                        "e_mod",
                        "on_eff",
                        "load_eff",
                        "extra_mwh_short",
                        "extra_mwh_med",
                        "extra_mwh_long",
                    )
                },
                avail_h_in_long_off_capwtd=float(
                    (g.cap_avail_h_in_long_off * g.npl).sum() / g.npl.sum()
                ),
                act_long_off_h_capwtd=float(
                    (g.act_long_off_h * g.npl).sum() / g.npl.sum()
                ),
                floor_twh=float(g.arm_floor_twh.sum()),
            )
        yr["arm_avail_twh"] = tot("cap_avail_twh")
        yr["arm_avail_h_in_long_off_capwtd"] = float(
            (t.cap_avail_h_in_long_off * t.npl).sum() / t.npl.sum()
        )
        yr["act_long_off_h_capwtd"] = float(
            (t.act_long_off_h * t.npl).sum() / t.npl.sum()
        )
        yr["arm_floor_twh"] = tot("arm_floor_twh")
        yr["top_plants_arm_delta"] = (
            t.assign(d=t.arm_e_mod - t.arm_e_act)
            .sort_values("d", ascending=False)
            .head(12)[
                [
                    "pid",
                    "name",
                    "zone",
                    "npl",
                    "arm_e_act",
                    "keeper_e_mod",
                    "arm_e_mod",
                    "arm_h_act",
                    "keeper_h_mod",
                    "arm_h_mod",
                    "arm_extra_mwh_long",
                ]
            ]
            .round(3)
            .to_dict("records")
        )
        res["years"][str(y)] = yr
        print(
            y,
            json.dumps(
                {
                    k: (round(v, 2) if isinstance(v, float) else v)
                    for k, v in yr.items()
                    if k not in ("keeper", "arm", "top_plants_arm_delta")
                }
            ),
        )
        for tag in ("keeper", "arm"):
            print(
                "  ",
                tag,
                {
                    k: (round(v, 2) if isinstance(v, float) else v)
                    for k, v in yr[tag].items()
                },
            )
    out = REPO / "results/calibration/_pjm_h21_cardd_phase0.json"
    out.write_text(json.dumps(res, indent=1, default=float))
    print("wrote", out)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
