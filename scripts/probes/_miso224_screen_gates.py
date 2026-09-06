"""miso-224 SCREEN GATES — committed BLIND, before the 2023 screen solve finishes.

Scores the rule-29 screen of the marginal-commodity gas arm
(``miso_gas_marginal_commodity_pricing``) on 2023 against the committed keeper
``miso220_nonsteamlift_B`` (rule 29(b) form 4: the keeper IS the control —
G-DRIFT at ``b3fb0edc..HEAD`` is ALL INERT, PRECOMMIT §7). Every band below is
copied verbatim from ``PRECOMMIT-miso224-gas-marginal-commodity-2026-09-06.md``
§5 and MUST NOT be edited after a result exists (miso-223 §2 discipline: a scorer
defect is disclosed, never fixed after the fact).

Gates are STRUCTURAL and STOP-only. None reads C3a or any target residual; none
can promote the arm.

Usage::

    python3 scripts/probes/_miso224_screen_gates.py results/calibration/miso224_spotgas_S
"""

from __future__ import annotations

import dataclasses
import gzip
import base64
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

KEEPER = REPO / "results/calibration/miso220_nonsteamlift_B"
KEEPER_ID = "2026-09-05-miso-220-nonsteam-lift"
OUT = REPO / "results/calibration/_miso224_screen_gates.json"
YEAR = 2023
ZONE = "MISO-Indiana"
HOURS = 8760
ARM_FIELD = "miso_gas_marginal_commodity_pricing"
#: run_config fields that are YEAR-SCOPED (differ between a 3-year keeper stamped
#: for 2023 and a 2023-only arm for that reason alone) — excluded from S-1 (the
#: miso-223 §2 lesson, scoped BEFORE the run).
YEAR_SCOPED = {"weather_year", "gas_price_override", "start_year", "end_year", "year", "years"}
COAL = ("COAL", "COAL_BIT", "COAL_LIGNITE", "COAL_PRB", "COAL_WC")
GAS = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_CHP", "ST_GAS")

# ---- pre-registered bands (PRECOMMIT §5) ----------------------------------
G1_STATIC_BODY_DELTA = -6.72        # static re-merit, 2023 body, Indiana ($/MWh)
G1_BAND = (1.5 * G1_STATIC_BODY_DELTA, 0.5 * G1_STATIC_BODY_DELTA)   # [-10.08, -3.36]
G3_STATIC_COAL_MW = -2919.0         # static, 2023 actual-hub<$20 hours
G3_STATIC_GAS_MW = +2990.0
G3_MIN_FRACTION = 0.3
# C1 band constants, verbatim from scripts/calibration_verdict.py (rubric v3.x)
FUELMIX_VOL_LOAD_FRAC, FUELMIX_SHARE_PP, FUELMIX_VOL_CAP_TWH = 0.02, 3.0, 8.0
C1_CLASSES = ("CC_CHP", "CC_REGULAR", "CT_PEAKER", "ST_CHP", "ST_GAS",
              "COAL_PRB", "COAL_LIGNITE", "COAL_BIT", "COAL_WC", "COAL")
G4_INCONCLUSIVE_TWH = 1.5           # delta-transfer approximation width (PRECOMMIT §5 G-4)


def _r(x, k=3):
    return None if x is None or not np.isfinite(x) else round(float(x), k)


def _sysprice(bundle: Path) -> tuple[np.ndarray, np.ndarray]:
    s = pd.read_parquet(bundle / f"hourly/system_{YEAR}.parquet")
    s = s[s["pass"] == "P1"]
    p = s.pivot_table(index="hour", columns="zone", values="price", aggfunc="first").reindex(range(HOURS))
    d = s.pivot_table(index="hour", columns="zone", values="demand", aggfunc="first").reindex(range(HOURS))
    carrying = [z for z in p.columns if not str(z).startswith("MISO_external")]
    lw = (p[carrying].to_numpy(float) * d[carrying].to_numpy(float)).sum(1) / d[carrying].to_numpy(float).sum(1)
    return p[ZONE].to_numpy(float), lw


def _classes(bundle: Path) -> pd.DataFrame:
    c = pd.read_parquet(bundle / f"hourly/class_hourly_{YEAR}.parquet")
    c = c[c["pass"] == "P1"]
    return c.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum", observed=True).reindex(range(HOURS)).fillna(0.0)


def gate_s1(arm: Path) -> dict:
    k = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    a = json.loads((arm / "run_config.json").read_text())["scenario_config"]
    diffs, year_scoped, absent = [], [], []
    for key in sorted(set(k) | set(a)):
        if key not in k:
            absent.append(key); continue
        if k.get(key) != a.get(key):
            (year_scoped if key in YEAR_SCOPED else diffs).append(key)
    substantive = [d for d in diffs if d != ARM_FIELD]
    return {"pass": (ARM_FIELD in diffs) and not substantive, "arm_field_differs": ARM_FIELD in diffs,
            "other_diffs": substantive, "year_scoped_diffs": year_scoped, "fields_absent_from_keeper": absent,
            "arm_value": a.get(ARM_FIELD), "keeper_value": k.get(ARM_FIELD, "<absent>")}


def gate_s2(arm: Path) -> dict:
    """Liveness: rebuilt from the ARM's recorded config, every gas row is at its hub."""
    import _miso134_ct_night_order_screen as m134
    m134.BUNDLE = arm
    from _miso134_ct_night_order_screen import build_year, keeper_config
    from market_sim.data import fuel
    cfg = keeper_config()
    _, fleet, arrays, fp, mc, _ = build_year(cfg, YEAR)
    fp = np.asarray(fp, float)
    fuel_name = np.array([str(getattr(g, "fuel_type", "")) for g in fleet])
    zone = np.array([str(g.zone) for g in fleet])
    gas = np.array([f.startswith("gas") for f in fuel_name])
    chi = np.repeat(fuel._flow_date_staircase(fuel._miso_citygate_daily_dated(None)[YEAR], YEAR), 24)
    hh = np.repeat(fuel._trade_date_staircase(fuel._henry_hub_daily_dated(None)[YEAR], YEAR), 24)
    mw, so = gas & (zone != "MISO-South"), gas & (zone == "MISO-South")
    d1 = fp[mw] - chi[None, :]; d2 = fp[so] - hh[None, :]
    # dual-fuel parity can only LOWER a gas price (min with oil), never raise it
    eq = float(((np.abs(d1) < 1e-9).mean() * mw.sum() + (np.abs(d2) < 1e-9).mean() * so.sum()) / gas.sum())
    return {"pass": bool(getattr(cfg, ARM_FIELD, False)) and d1.max() <= 1e-9 and d2.max() <= 1e-9 and eq >= 0.99,
            "armed_in_recorded_config": bool(getattr(cfg, ARM_FIELD, False)),
            "gas_rows": int(gas.sum()), "midwest_max_over_chicago": _r(d1.max(), 6),
            "south_max_over_hh": _r(d2.max(), 6), "share_exactly_at_hub": _r(eq, 4)}


def gate_g1(arm: Path) -> dict:
    pk, lk = _sysprice(KEEPER)
    pa, la = _sysprice(arm)
    body = pk <= np.percentile(pk, 90)           # the keeper's OWN body hours, fixed
    d = float(pa[body].mean() - pk[body].mean())
    return {"pass": G1_BAND[0] <= d <= G1_BAND[1], "band": list(G1_BAND), "static_prediction": G1_STATIC_BODY_DELTA,
            "keeper_body_mean": _r(pk[body].mean()), "arm_body_mean": _r(pa[body].mean()), "delta": _r(d),
            "lw_body_delta_report_only": _r(la[body].mean() - lk[body].mean()),
            "tail_delta_report_only": _r(pa[~body].mean() - pk[~body].mean()),
            "annual_lw_delta_report_only": _r(la.mean() - lk.mean())}


def gate_g3(arm: Path) -> dict:
    from _miso224_floor_anatomy_phase0 import actual_zone_price
    act = actual_zone_price(YEAR)[ZONE].to_numpy(float)
    sel = np.isfinite(act) & (act < 20.0)
    ck, ca = _classes(KEEPER), _classes(arm)
    def tot(c, names):
        return c[[n for n in names if n in c.columns]].sum(1).to_numpy(float)
    dcoal = float(tot(ca, COAL)[sel].mean() - tot(ck, COAL)[sel].mean())
    dgas = float(tot(ca, GAS)[sel].mean() - tot(ck, GAS)[sel].mean())
    ok = dcoal <= G3_MIN_FRACTION * G3_STATIC_COAL_MW and dgas >= G3_MIN_FRACTION * G3_STATIC_GAS_MW
    return {"pass": ok, "n_hours": int(sel.sum()), "coal_delta_mw": _r(dcoal, 0), "gas_delta_mw": _r(dgas, 0),
            "static_coal_mw": G3_STATIC_COAL_MW, "static_gas_mw": G3_STATIC_GAS_MW, "min_fraction": G3_MIN_FRACTION,
            "keeper_coal_mw": _r(tot(ck, COAL)[sel].mean(), 0), "keeper_gas_mw": _r(tot(ck, GAS)[sel].mean(), 0),
            "arm_coal_mw": _r(tot(ca, COAL)[sel].mean(), 0), "arm_gas_mw": _r(tot(ca, GAS)[sel].mean(), 0)}


def gate_g4(arm: Path) -> dict:
    """C1 per class, DELTA-TRANSFER: arm_gm = keeper_gm + (arm_ch - keeper_ch)."""
    s = (REPO / f"frontend/data/backcast/runs/{KEEPER_ID}.js").read_text()
    pay = json.loads(gzip.decompress(base64.b64decode(s[s.find('="') + 2:s.rfind('"')])))["years"][str(YEAR)]
    bench = json.loads(gzip.decompress((REPO / f"frontend/data/backcast/bench/MISO/{YEAR}.json.gz").read_bytes()))["bench"]
    gm, cf = pay["gmModel"], bench["classFull"]
    load = sum(float(z.get("d", 0.0)) for z in pay["lmp"].values())
    ck, ca = _classes(KEEPER), _classes(arm)
    dch = {c: float(ca[c].sum() - ck[c].sum()) / 1e6 if c in ca.columns and c in ck.columns else 0.0 for c in gm}
    gm_arm = {c: gm[c] + dch.get(c, 0.0) for c in gm}
    a_gen = sum(float(v) for v in cf.values())
    m_gen_k = sum(float(gm[c]) for c in cf if c in gm)
    m_gen_a = sum(float(gm_arm[c]) for c in cf if c in gm_arm)
    band = min(max(FUELMIX_VOL_LOAD_FRAC * load, FUELMIX_SHARE_PP / 100 * a_gen), FUELMIX_VOL_CAP_TWH)
    cells, flips, inconclusive = {}, [], []
    for c in C1_CLASSES:
        if c not in cf or c not in gm:
            continue
        a = float(cf[c])
        def status(m, m_gen):
            d = m - a; sp = 100 * m / m_gen - 100 * a / a_gen
            return (abs(d) <= band and abs(sp) <= FUELMIX_SHARE_PP), d, sp
        pk, dk, spk = status(float(gm[c]), m_gen_k)
        pa, da, spa = status(float(gm_arm[c]), m_gen_a)
        cells[c] = {"actual": _r(a), "keeper_model": _r(gm[c]), "keeper_err": _r(dk), "keeper_pass": pk,
                    "arm_model_delta_transfer": _r(gm_arm[c]), "arm_err": _r(da), "arm_share_pp": _r(spa, 2), "arm_pass": pa,
                    "class_hourly_delta_twh": _r(dch.get(c, 0.0))}
        if pk and not pa:
            (inconclusive if abs(abs(da) - band) <= G4_INCONCLUSIVE_TWH and abs(spa) <= FUELMIX_SHARE_PP else flips).append(c)
    return {"pass": not flips, "flips_pass_to_fail": flips, "inconclusive_within_approximation": inconclusive,
            "vol_band_twh": _r(band), "load_twh": _r(load), "a_gen_twh": _r(a_gen),
            "c2_scored": False, "note": "C2 (system-volume family) is UNSCORED ex ante: a single-year replay writes no metrics.json.",
            "cells": cells}


def main() -> int:
    arm = Path(sys.argv[1]).resolve()
    rec = {"probe": "miso-224 screen gates (2023, blind)", "arm": str(arm.relative_to(REPO)), "keeper": KEEPER_ID,
           "control": "form 4 — the committed keeper (G-DRIFT b3fb0edc..HEAD ALL INERT)", "gates": {}}
    rec["gates"]["S1"] = gate_s1(arm)
    rec["gates"]["S2"] = gate_s2(arm)
    rec["gates"]["G1"] = gate_g1(arm)
    rec["gates"]["G3"] = gate_g3(arm)
    rec["gates"]["G4"] = gate_g4(arm)
    kills = [g for g in ("S1", "S2", "G1", "G3", "G4") if not rec["gates"][g]["pass"]]
    rec["verdict"] = "ARM SURVIVES THE SCREEN" if not kills else f"ARM KILLED ON {', '.join(kills)}"
    OUT.write_text(json.dumps(rec, indent=1))
    for g, v in rec["gates"].items():
        print(g, "PASS" if v["pass"] else "FAIL", {k: x for k, x in v.items() if k not in ("cells",)})
    print(rec["verdict"]); print(f"-> {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
