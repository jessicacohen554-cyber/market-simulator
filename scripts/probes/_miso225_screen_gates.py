"""miso-225 SCREEN GATES — committed BLIND, before the 2023 screen solve finishes.

Scores the rule-29 screen of the OWNER-RULED joint arm on 2023 against the
committed keeper ``miso220_nonsteamlift_B`` (rule 29(b) form 4: the keeper IS
the control — G-DRIFT at ``cbcd3d33..d1aa877f`` is ALL INERT, PRECOMMIT §7):

* ``miso_gas_marginal_commodity_pricing`` + ``miso_gas_variable_transport`` —
  gas at the traded hub PLUS its plant's MEASURED variable transport, the form
  the owner ruled on 2026-09-06 (the bare hub of miso-224 is superseded);
* ``miso_seam_neighbour_anchored_ladder`` — the PJM seam's bands repriced on the
  EXPORTING market's own border DA, the one admissible form of the D-2 5(i)
  object.

Every band below is copied verbatim from
``PRECOMMIT-miso225-transport-seam-joint-2026-09-06.md`` §5 and MUST NOT be
edited after a result exists (the miso-223 §2 / miso-224 §2 discipline: a scorer
defect is DISCLOSED, never fixed after the fact).

Gates are STRUCTURAL and STOP-only. None reads C3a or any target residual; none
can promote the arm.

Usage::

    python3 scripts/probes/_miso225_screen_gates.py results/calibration/miso225_ruled_S <solve.log>
"""

from __future__ import annotations

import base64
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _miso224_screen_gates import (  # noqa: E402
    C1_CLASSES,
    COAL,
    FUELMIX_SHARE_PP,
    FUELMIX_VOL_CAP_TWH,
    FUELMIX_VOL_LOAD_FRAC,
    G4_INCONCLUSIVE_TWH,
    GAS,
    HOURS,
    KEEPER,
    KEEPER_ID,
    YEAR,
    YEAR_SCOPED,
    ZONE,
    _classes,
    _r,
    _sysprice,
)

OUT = REPO / "results/calibration/_miso225_screen_gates.json"

#: The three armed fields. S-1 is scoped as miso-224 §2's successor prescribed:
#: each is True in the ARM and absent-or-False in the KEEPER.
ARM_FIELDS = (
    "miso_gas_marginal_commodity_pricing",
    "miso_gas_variable_transport",
    "miso_seam_neighbour_anchored_ladder",
)

# ---- pre-registered bands (PRECOMMIT §5), from the RULED static re-merit -----
G1_STATIC_BODY_DELTA = -2.976       # _miso225_static_remerit.json, 2023 body, Indiana
G1_BAND = (1.5 * G1_STATIC_BODY_DELTA, 0.5 * G1_STATIC_BODY_DELTA)   # [-4.464, -1.488]
G2_MIN_CHEAP_HOUR_IMPORT_MW = 150.0  # seam leg: imports RISE in the real sub-$20 hours
G3_STATIC_COAL_MW = -1470.0         # ruled static, 2023 actual-hub<$20 hours
G3_STATIC_GAS_MW = +1483.0
G3_MIN_FRACTION = 0.3
IMPORT_CLASSES = ("import", "IMPORT", "imports", "interchange", "net_import")


def gate_s1(arm: Path) -> dict:
    """Each arm field True in the arm and absent-or-False in the keeper; nothing else differs."""
    keeper = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    a = json.loads((arm / "run_config.json").read_text())["scenario_config"]
    diffs, year_scoped, absent = [], [], []
    for key in sorted(set(keeper) | set(a)):
        if key not in keeper:
            absent.append(key)
            continue
        if keeper.get(key) != a.get(key):
            (year_scoped if key in YEAR_SCOPED else diffs).append(key)
    substantive = [d for d in diffs if d not in ARM_FIELDS]
    armed = {
        f: {
            "arm_value": a.get(f),
            "keeper_value": keeper.get(f, "<absent>"),
            "ok": bool(a.get(f)) and not bool(keeper.get(f, False)),
        }
        for f in ARM_FIELDS
    }
    return {
        "pass": all(v["ok"] for v in armed.values()) and not substantive,
        "armed_fields": armed,
        "other_diffs": substantive,
        "year_scoped_diffs": year_scoped,
        "fields_absent_from_keeper": absent,
    }


def gate_s2(arm: Path, solve_log: Path | None = None) -> dict:
    """Liveness, asserted on the SOLVE LOG — the chain a backcast actually takes.

    miso-224 Addendum A's lesson, inherited rather than relearned: a
    config-rebuild is evidence about the probe path, not about the solve. The
    fuel leg must show the marginal-commodity line CARRYING the transport clause
    (the bare-hub form prints a different clause), the winter-shape line must be
    ABSENT (rule 19), and the seam leg must name the neighbour anchor.
    """
    out: dict[str, object] = {"solve_log_checked": solve_log is not None}
    if solve_log is None:
        out["pass"] = False
        return out
    txt = Path(solve_log).read_text(errors="replace")
    fuel_line = f"MISO gas marginal-commodity pricing ({YEAR})" in txt
    transport = "PLUS the derived per-plant variable transport" in txt
    winter = f"MISO winter citygate daily ({YEAR})" in txt
    seam = "PJM WESTERN-BORDER DA quantiles" in txt
    out.update(
        mechanism_line_in_solve_log=fuel_line,
        transport_clause_in_solve_log=transport,
        winter_shape_overlay_line_in_solve_log=winter,
        neighbour_seam_line_in_solve_log=seam,
        pass_=None,
    )
    out.pop("pass_")
    out["pass"] = bool(fuel_line and transport and not winter and seam)
    return out


def gate_g1(arm: Path) -> dict:
    """Fuel leg: the body falls inside 0.5x-1.5x the RULED static prediction."""
    pk, lk = _sysprice(KEEPER)
    pa, la = _sysprice(arm)
    body = pk <= np.percentile(pk, 90)  # the keeper's OWN body hours, fixed
    d = float(pa[body].mean() - pk[body].mean())
    return {
        "pass": G1_BAND[0] <= d <= G1_BAND[1],
        "band": [round(x, 3) for x in G1_BAND],
        "static_prediction": G1_STATIC_BODY_DELTA,
        "keeper_body_mean": _r(pk[body].mean()),
        "arm_body_mean": _r(pa[body].mean()),
        "delta": _r(d),
        "lw_body_delta_report_only": _r(la[body].mean() - lk[body].mean()),
        "tail_delta_report_only": _r(pa[~body].mean() - pk[~body].mean()),
        "annual_lw_delta_report_only": _r(la.mean() - lk.mean()),
    }


def _imports(bundle: Path) -> np.ndarray:
    """Hourly gross import MW from the class sidecar, whatever the class is called."""
    c = pd.read_parquet(bundle / f"hourly/class_hourly_{YEAR}.parquet")
    c = c[c["pass"] == "P1"]
    names = [k for k in c["klass"].unique() if str(k).lower().startswith("import")]
    if not names:
        names = [k for k in c["klass"].unique() if str(k) in IMPORT_CLASSES]
    if not names:
        return np.full(HOURS, np.nan)
    sub = c[c["klass"].isin(names)]
    return (
        sub.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    )


def gate_g2(arm: Path) -> dict:
    """Seam leg: every PJM import band is cheaper, so imports must RISE."""
    from _miso224_floor_anatomy_phase0 import actual_zone_price

    act = actual_zone_price(YEAR)[ZONE].to_numpy(float)
    sel = np.isfinite(act) & (act < 20.0)
    ik, ia = _imports(KEEPER), _imports(arm)
    if not np.isfinite(ik).any() or not np.isfinite(ia).any():
        return {"pass": False, "note": "no import class found in the class sidecar"}
    d_cheap = float(ia[sel].mean() - ik[sel].mean())
    d_annual = float((ia.sum() - ik.sum()) / 1e6)
    return {
        "pass": bool(d_cheap >= G2_MIN_CHEAP_HOUR_IMPORT_MW and d_annual > 0.0),
        "min_cheap_hour_delta_mw": G2_MIN_CHEAP_HOUR_IMPORT_MW,
        "n_cheap_hours": int(sel.sum()),
        "keeper_cheap_hour_import_mw": _r(ik[sel].mean(), 0),
        "arm_cheap_hour_import_mw": _r(ia[sel].mean(), 0),
        "cheap_hour_delta_mw": _r(d_cheap, 0),
        "annual_delta_twh": _r(d_annual),
        "keeper_annual_twh": _r(ik.sum() / 1e6),
        "arm_annual_twh": _r(ia.sum() / 1e6),
    }


def gate_g3(arm: Path) -> dict:
    """Fuel leg dispatch: coal DOWN and gas UP by >= 0.3x the ruled static."""
    from _miso224_floor_anatomy_phase0 import actual_zone_price

    act = actual_zone_price(YEAR)[ZONE].to_numpy(float)
    sel = np.isfinite(act) & (act < 20.0)
    ck, ca = _classes(KEEPER), _classes(arm)

    def tot(c, names):
        return c[[n for n in names if n in c.columns]].sum(1).to_numpy(float)

    dcoal = float(tot(ca, COAL)[sel].mean() - tot(ck, COAL)[sel].mean())
    dgas = float(tot(ca, GAS)[sel].mean() - tot(ck, GAS)[sel].mean())
    return {
        "pass": bool(
            dcoal <= G3_MIN_FRACTION * G3_STATIC_COAL_MW
            and dgas >= G3_MIN_FRACTION * G3_STATIC_GAS_MW
        ),
        "n_hours": int(sel.sum()),
        "coal_delta_mw": _r(dcoal, 0),
        "gas_delta_mw": _r(dgas, 0),
        "coal_required_mw": _r(G3_MIN_FRACTION * G3_STATIC_COAL_MW, 0),
        "gas_required_mw": _r(G3_MIN_FRACTION * G3_STATIC_GAS_MW, 0),
        "static_coal_mw": G3_STATIC_COAL_MW,
        "static_gas_mw": G3_STATIC_GAS_MW,
        "keeper_coal_mw": _r(tot(ck, COAL)[sel].mean(), 0),
        "arm_coal_mw": _r(tot(ca, COAL)[sel].mean(), 0),
        "keeper_gas_mw": _r(tot(ck, GAS)[sel].mean(), 0),
        "arm_gas_mw": _r(tot(ca, GAS)[sel].mean(), 0),
    }


def gate_g4(arm: Path) -> dict:
    """C1 per class, DELTA-TRANSFER: arm_gm = keeper_gm + (arm_ch - keeper_ch)."""
    s = (REPO / f"frontend/data/backcast/runs/{KEEPER_ID}.js").read_text()
    pay = json.loads(
        gzip.decompress(base64.b64decode(s[s.find('="') + 2 : s.rfind('"')]))
    )["years"][str(YEAR)]
    bench = json.loads(
        gzip.decompress(
            (REPO / f"frontend/data/backcast/bench/MISO/{YEAR}.json.gz").read_bytes()
        )
    )["bench"]
    gm, cf = pay["gmModel"], bench["classFull"]
    load = sum(float(z.get("d", 0.0)) for z in pay["lmp"].values())
    ck, ca = _classes(KEEPER), _classes(arm)
    dch = {
        c: float(ca[c].sum() - ck[c].sum()) / 1e6
        if c in ca.columns and c in ck.columns
        else 0.0
        for c in gm
    }
    gm_arm = {c: gm[c] + dch.get(c, 0.0) for c in gm}
    a_gen = sum(float(v) for v in cf.values())
    m_gen_k = sum(float(gm[c]) for c in cf if c in gm)
    m_gen_a = sum(float(gm_arm[c]) for c in cf if c in gm_arm)
    band = min(
        max(FUELMIX_VOL_LOAD_FRAC * load, FUELMIX_SHARE_PP / 100 * a_gen),
        FUELMIX_VOL_CAP_TWH,
    )
    cells, flips, inconclusive = {}, [], []
    for c in C1_CLASSES:
        if c not in cf or c not in gm:
            continue
        a = float(cf[c])

        def status(m, m_gen, actual=a):
            d = m - actual
            sp = 100 * m / m_gen - 100 * actual / a_gen
            return (abs(d) <= band and abs(sp) <= FUELMIX_SHARE_PP), d, sp

        pk, dk, _spk = status(float(gm[c]), m_gen_k)
        pa, da, spa = status(float(gm_arm[c]), m_gen_a)
        cells[c] = {
            "actual": _r(a),
            "keeper_model": _r(gm[c]),
            "keeper_err": _r(dk),
            "keeper_pass": pk,
            "arm_model_delta_transfer": _r(gm_arm[c]),
            "arm_err": _r(da),
            "arm_share_pp": _r(spa, 2),
            "arm_pass": pa,
            "class_hourly_delta_twh": _r(dch.get(c, 0.0)),
        }
        if pk and not pa:
            near = abs(abs(da) - band) <= G4_INCONCLUSIVE_TWH and abs(spa) <= FUELMIX_SHARE_PP
            (inconclusive if near else flips).append(c)
    return {
        "pass": not flips,
        "flips_pass_to_fail": flips,
        "inconclusive_within_approximation": inconclusive,
        "vol_band_twh": _r(band),
        "load_twh": _r(load),
        "a_gen_twh": _r(a_gen),
        "c2_scored": False,
        "note": "C2 (system-volume family) is UNSCORED ex ante: a single-year replay writes no metrics.json.",
        "cells": cells,
    }


def main() -> int:
    arm = Path(sys.argv[1]).resolve()
    solve_log = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None
    rec = {
        "probe": "miso-225 screen gates (2023, blind) — the OWNER-RULED joint arm",
        "arm": str(arm.relative_to(REPO)),
        "keeper": KEEPER_ID,
        "control": "form 4 — the committed keeper (G-DRIFT cbcd3d33..d1aa877f ALL INERT)",
        "solve_log": str(solve_log) if solve_log else None,
        "gates": {},
    }
    rec["gates"]["S1"] = gate_s1(arm)
    rec["gates"]["S2"] = gate_s2(arm, solve_log)
    rec["gates"]["G1"] = gate_g1(arm)
    rec["gates"]["G2"] = gate_g2(arm)
    rec["gates"]["G3"] = gate_g3(arm)
    rec["gates"]["G4"] = gate_g4(arm)
    kills = [g for g in ("S1", "S2", "G1", "G2", "G3", "G4") if not rec["gates"][g]["pass"]]
    rec["verdict"] = (
        "ARM SURVIVES THE SCREEN" if not kills else f"ARM KILLED ON {', '.join(kills)}"
    )
    OUT.write_text(json.dumps(rec, indent=1))
    for g, v in rec["gates"].items():
        print(g, "PASS" if v["pass"] else "FAIL", {k: x for k, x in v.items() if k != "cells"})
    print(rec["verdict"])
    print(f"-> {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
