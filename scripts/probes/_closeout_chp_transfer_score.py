#!/usr/bin/env python3
"""closeout-chp-transfer (ZERO LP): static C1 record moves of the three CHP arms per ISO.

Reads the census (``_closeout_chp_transfer_census.json``) and each keeper's
committed C1 fuel-mix records (``frontend/data/backcast/status/<ISO>.js``) and
walks four cumulative static arms, per class-year:

* ``M``  bench only: the measured Schedules 6/7 share pinned on the bench
  subtrahend (the nyiso-149 principle -- lands as soon as the ISO's artifact
  exists, flag or not): CHP actual + dE, then the family reconcile re-checked.
* ``A1`` + the run's measured carve (``<iso>_chp_btm_measured``): model CHP
  + reach, displaced classes down.
* ``A2`` + ``chp_startup_covered``: model CHP + release, displaced down,
  scaled by the w3f realised/static ratio for that lever (MISO arm A, 0.40).
* ``A3`` + ``mustrun_chp_btm_holdout``: model + take-up of the removed host
  injection, by class (the up-walk).

Status = |miss| <= the record's volume band AND |share| <= 3 pp, the share
moved by dmiss / generation (generation from the record set's own
miss/share ratio). Static: the LP response differs (see the FINDING).

Output: results/phase0/governance/_closeout_chp_transfer_score.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "src"), str(REPO), str(REPO / "scripts")]
from scripts.lib import benchmark_semantics as bs  # noqa: E402

CENSUS = REPO / "results/phase0/governance/_closeout_chp_transfer_census.json"
OUT = REPO / "results/phase0/governance/_closeout_chp_transfer_score.json"
STARTUP_REALISED = 0.40  # MISO w3f arm A: realised CC_CHP gain / static gain
SHARE_PP = 3.0
FAMILY = set(bs.GAS_GROUPS) | set(bs.COAL_GROUPS) | set(bs.OIL_GROUPS)


def records(iso: str) -> list[dict]:
    """The keeper's scored C1 fuel-mix records."""
    s = (REPO / f"frontend/data/backcast/status/{iso}.js").read_text()
    i = s.find(f'["{iso}"]=') + len(f'["{iso}"]=')
    d = json.JSONDecoder().raw_decode(s[i:])[0]
    out = []
    for r in d["keeper"]["criteria"]["fuelmix"]["records"]:
        m = re.search(r"= ±([\d.]+) TWh", r.get("tol") or "")
        if r.get("status") not in ("PASS", "FAIL") or not m or r.get("model") is None:
            continue
        out.append({**r, "tol_twh": float(m.group(1))})
    return out


def _gen(recs: list[dict]) -> float:
    """Total generation implied by miss / share (median over material records)."""
    v = [
        (r["model"] - r["actual"]) * 100.0 / r["share_pp"]
        for r in recs
        if abs(r["model"] - r["actual"]) > 1.0 and abs(r.get("share_pp") or 0) > 0.2
    ]
    if len(v) >= 3:
        return float(np.median(v))
    # few material records: the volume band's own 3 %-of-generation leg
    return float(np.median([r["tol_twh"] for r in recs])) / 0.03


def _status(miss: float, share: float, tol: float) -> str:
    return "PASS" if abs(miss) <= tol + 1e-9 and abs(share) <= SHARE_PP + 1e-9 else "FAIL"


def arms(c: dict) -> tuple[dict[str, dict[str, float]], object]:
    """Per arm, per class: cumulative d_model TWh; plus the bench actual shift.

    The bench shift is the same in every arm (the measured share is pinned on
    the bench whenever the artifact exists): a family class rescales from the
    committed reconcile factor to the new one, a CHP class gains dE first.
    """
    rc = c["reconcile"]
    s_old = rc["target"] / rc["family_pre_est"] if rc["fired_committed"] else 1.0
    s_new = rc["scale_new"]

    def actual_shift(cls: str, committed: float) -> float:
        if cls not in FAMILY:
            return 0.0
        return (committed / s_old + c["dE_by_group"].get(cls, 0.0)) * s_new - committed

    def add(base: dict, src: dict, sign: float, k: float = 1.0) -> dict:
        out = dict(base)
        for g, v in src.items():
            out[g] = out.get(g, 0.0) + sign * k * v
        return out

    ar = c.get("arm_reach", {})
    rel = c.get("commitment", {}).get("release", {})
    a1 = add(add({}, ar.get("model_add_by_group", {}), 1), ar.get("displaced_twh_by_class", {}), -1)
    a2 = add(add(a1, rel.get("gain_by_group", {}), 1, STARTUP_REALISED),
             rel.get("displaced_twh_by_class", {}), -1, STARTUP_REALISED)
    a3 = add(a2, c.get("holdout_reach", {}).get("taken_twh_by_class", {}), 1)
    return {"M": {}, "A1": a1, "A2": a2, "A3": a3}, actual_shift


def main() -> None:
    cen = json.loads(CENSUS.read_text())
    res: dict = {}
    for iso, yrs in cen.items():
        recs = records(iso)
        res[iso] = {"records": [], "summary": {}}
        gen_by_year = {
            y: _gen([r for r in recs if r["year"] == y]) for y in {r["year"] for r in recs}
        }
        for r in recs:
            c = yrs.get(str(r["year"]))
            if c is None:
                continue
            a, shift = arms(c)
            miss0 = r["model"] - r["actual"]
            gen = gen_by_year.get(r["year"]) or float("nan")
            row = {
                "year": r["year"], "key": r["key"], "tol": r["tol_twh"],
                "miss": round(miss0, 2), "share": r.get("share_pp"), "status": r["status"],
            }
            d_actual = shift(r["key"], r["actual"])
            for arm in ("M", "A1", "A2", "A3"):
                dm = a[arm].get(r["key"], 0.0)
                miss = miss0 + dm - d_actual
                share = (r.get("share_pp") or 0.0) + (
                    (miss - miss0) * 100.0 / gen if gen == gen and gen else 0.0
                )
                row[arm] = {"miss": round(miss, 2), "share": round(share, 2),
                            "status": _status(miss, share, r["tol_twh"])}
            res[iso]["records"].append(row)
        for arm in ("M", "A1", "A2", "A3"):
            rr = res[iso]["records"]
            res[iso]["summary"][arm] = {
                "fail": sum(x[arm]["status"] == "FAIL" for x in rr),
                "fail_to_pass": [f'{x["key"]} {x["year"]}' for x in rr
                                 if x["status"] == "FAIL" and x[arm]["status"] == "PASS"],
                "pass_to_fail": [f'{x["key"]} {x["year"]}' for x in rr
                                 if x["status"] == "PASS" and x[arm]["status"] == "FAIL"],
            }
        res[iso]["summary"]["keeper_fail"] = sum(x["status"] == "FAIL" for x in res[iso]["records"])
        print(iso, json.dumps(res[iso]["summary"]))
    OUT.write_text(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
