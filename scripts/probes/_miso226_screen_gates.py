"""miso-226 SCREEN GATES — committed BLIND, before the 2023 seam-alone screen solve finishes.

Scores the rule-29 screen of the SEAM ARM **ALONE** on 2023 against the
committed keeper ``miso220_nonsteamlift_B`` (rule 29(b) form 4: the keeper IS
the control — G-DRIFT ``07099620..47e306d3`` is ALL INERT, PRECOMMIT §5):

* ``miso_seam_neighbour_anchored_ladder`` — the PJM seam's bands repriced on the
  EXPORTING market's own border DA, the one admissible form of the D-2 5(i)
  object (owner ruling 2026-09-06) — armed with **both** fuel fields OFF, which
  is the whole point of this arm: with MISO's price carrying no exogenous shock,
  cheaper bands MUST raise imports and the direction reading is unconfounded.

Gate NAMES are inherited from ``_miso225_screen_gates`` wherever the
construction is identical, so nothing is renamed to dodge a comparison:

* **G-2** is miso-225's import-direction gate, threshold and hour set **frozen
  verbatim** (>= +150 MW against the keeper's 3,043 MW over the 1,230 real
  sub-$20 hours). It is this screen's PRIMARY gate.
* **G-4** is miso-225's C1 no-flip gate, construction and bands unchanged.
* **G-5** is new and belongs to this arm: footprint confinement.
* miso-225's **G-1** (fuel body price) and **G-3** (fuel dispatch response) have
  no leg in this arm — there is no fuel mechanism — so they are NOT scored. The
  price deltas are computed and REPORTED under ``price_report_only``: here a
  price move is the CONSEQUENCE of the import response being measured, not an
  exogenous driver, so gating on it would gate the screen on its own target
  residual (rule 29, which forbids exactly that).

Every band below is copied verbatim from
``PRECOMMIT-miso226-seam-alone-2026-09-06.md`` §4 and MUST NOT be edited after a
result exists (the miso-223 §2 / miso-224 §2 / miso-225 §2 discipline: a scorer
defect is DISCLOSED, never fixed after the fact).

Usage::

    python3 scripts/probes/_miso226_screen_gates.py results/calibration/miso226_seamalone_S <solve.log>
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
    FUELMIX_SHARE_PP,
    FUELMIX_VOL_CAP_TWH,
    FUELMIX_VOL_LOAD_FRAC,
    G4_INCONCLUSIVE_TWH,
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

OUT = REPO / "results/calibration/_miso226_screen_gates.json"

#: The ONE armed field.
ARM_FIELDS = ("miso_seam_neighbour_anchored_ladder",)

#: S-1's REACHABILITY leg (this PRECOMMIT's declared successor scoping, §4 S-1b,
#: written BEFORE the solve). miso-225's S-1 failed on a REAL config difference
#: that its OWN G-DRIFT had already classified inert-for-this-solve, and its
#: FINDING §2 said a successor wanting S-1 to mean "differs only in fields that
#: can REACH this solve" must declare that ex ante. This is that declaration.
#: The list is CLOSED — an explicit enumeration, not a rule that could swallow a
#: reachable field. Any other non-arm, non-year-scoped diff STOPS the arm.
S1_REACHABILITY_EXEMPT: dict[str, str] = {
    # capx D65-B on main (8.0 -> 2.95). The CCS retrofit screen is capacity
    # evolution step 2, entered only by mode="forecast", and is inert below
    # ccs_retrofit_available_year = 2028 by construction; a mode="backcast"
    # 2023 run never reaches it. G-DRIFT PRECOMMIT §5 classifies it INERT.
    "ccs_retrofit_vom_adder": (
        "capx D65-B; forecast-mode CCS retrofit screen, inert below 2028, "
        "unreachable by a backcast 2023 solve (G-DRIFT INERT)"
    ),
}

# ---- pre-registered bands (PRECOMMIT §4) -------------------------------------
#: FROZEN VERBATIM from miso-225 PRECOMMIT §5 G-2 / _miso225_screen_gates.py.
G2_MIN_CHEAP_HOUR_IMPORT_MW = 150.0
#: Phase-0 static prediction for this arm (_miso226_seam_static_remerit.json):
#: +700.7 MW over the same 1,230 hours, so the frozen bar is 0.214x the static —
#: inside the 0.27-0.39x conversion band miso-224/225 both measured. Reported,
#: never used as a threshold.
G2_STATIC_PREDICTION_MW = 700.7
G2_STATIC_ANNUAL_MW = 534.9
#: G-5 footprint: slack/dump must not absorb the change.
G5_MAX_SLACK_DUMP_TWH = 0.01


def gate_s1(arm: Path) -> dict:
    """Two legs, both reported; the REACHABILITY leg (S-1b) is the STOP gate."""
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
    unreachable_only = [d for d in substantive if d not in S1_REACHABILITY_EXEMPT]
    armed = {
        f: {
            "arm_value": a.get(f),
            "keeper_value": keeper.get(f, "<absent>"),
            "ok": bool(a.get(f)) and not bool(keeper.get(f, False)),
        }
        for f in ARM_FIELDS
    }
    armed_ok = all(v["ok"] for v in armed.values())
    return {
        # S-1b, the STOP leg
        "pass": armed_ok and not unreachable_only,
        "s1a_identity_pass_reported_only": armed_ok and not substantive,
        "armed_fields": armed,
        "other_diffs": substantive,
        "other_diffs_reachability_exempt": {
            d: S1_REACHABILITY_EXEMPT[d] for d in substantive if d in S1_REACHABILITY_EXEMPT
        },
        "other_diffs_not_exempt_STOP": unreachable_only,
        "year_scoped_diffs": year_scoped,
        "fields_absent_from_keeper": absent,
    }


def gate_s2(arm: Path, solve_log: Path | None = None) -> dict:
    """Liveness AND isolation, asserted on the SOLVE LOG (miso-224 Addendum A).

    The seam line must name the neighbour anchor, and — this arm's own
    requirement — the fuel mechanism line must be ABSENT: a seam-alone arm whose
    log carries the marginal-commodity repricing is not the arm this screen
    pre-registered. The winter-shape line is REPORTED, not gated: with the fuel
    arm off it is the keeper's own behaviour, and this session holds no keeper
    solve log to compare it against.
    """
    out: dict[str, object] = {"solve_log_checked": solve_log is not None}
    if solve_log is None:
        out["pass"] = False
        return out
    txt = Path(solve_log).read_text(errors="replace")
    seam = "PJM WESTERN-BORDER DA quantiles" in txt
    fuel = f"MISO gas marginal-commodity pricing ({YEAR})" in txt
    transport = "PLUS the derived per-plant variable transport" in txt
    winter = f"MISO winter citygate daily ({YEAR})" in txt
    out.update(
        neighbour_seam_line_in_solve_log=seam,
        fuel_marginal_commodity_line_in_solve_log_MUST_BE_ABSENT=fuel,
        transport_clause_in_solve_log_MUST_BE_ABSENT=transport,
        winter_shape_overlay_line_report_only=winter,
    )
    out["pass"] = bool(seam and not fuel and not transport)
    return out


def _imports(bundle: Path) -> np.ndarray:
    """Hourly gross import MW from the class sidecar (miso-225's construction)."""
    c = pd.read_parquet(bundle / f"hourly/class_hourly_{YEAR}.parquet")
    c = c[c["pass"] == "P1"]
    names = [k for k in c["klass"].unique() if str(k).lower().startswith("import")]
    if not names:
        return np.full(HOURS, np.nan)
    sub = c[c["klass"].isin(names)]
    return (
        sub.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    )


def _cheap_mask() -> np.ndarray:
    from _miso224_floor_anatomy_phase0 import actual_zone_price

    act = actual_zone_price(YEAR)[ZONE].to_numpy(float)
    return np.isfinite(act) & (act < 20.0)


def gate_g2(arm: Path) -> dict:
    """FROZEN VERBATIM from miso-225: every PJM import band is cheaper, so imports must RISE.

    This is the primary gate. In miso-225 it read -75 MW inside a JOINT arm
    whose fuel leg moved MISO's price down $1.92; here nothing moves the price
    exogenously, so a fall would be the mechanism doing the opposite of its own
    arithmetic with no confound available to explain it.
    """
    sel = _cheap_mask()
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
        "static_prediction_cheap_hour_mw_report_only": G2_STATIC_PREDICTION_MW,
        "realized_fraction_of_static_report_only": _r(
            d_cheap / G2_STATIC_PREDICTION_MW, 3
        ),
        "static_prediction_annual_mw_report_only": G2_STATIC_ANNUAL_MW,
        "miso225_joint_arm_cheap_hour_delta_mw": -75.0,
    }


def gate_g5(arm: Path) -> dict:
    """FOOTPRINT CONFINEMENT — the change lands where the mechanism's arithmetic put it.

    Two legs, both STOP:

    (a) The import response is CONCENTRATED in the hours a band actually changed
        merit status. The phase-0 instrument
        (``_miso226_seam_static_remerit.json``) partitions the year into hours
        where at least one PJM import band crosses from out- to in-merit at the
        keeper's own bus price and hours where none does; in the latter the
        mechanism's own arithmetic predicts no import change at all. The bar is
        DIRECTIONAL and untunable: mean import delta in the re-merit hours must
        strictly EXCEED the mean in the zero-re-merit hours.
    (b) Slack and dump absorb none of it (|delta| <= 0.01 TWh each) — the change
        is real dispatch, not an infeasibility being priced.
    """
    from market_sim.config.interchange_config import (
        MISO_SEAM_LADDER_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR,
    )

    inc = np.asarray(MISO_SEAM_LADDER_BY_YEAR[YEAR]["PJM"]["import"], float)
    neigh = np.asarray(MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR[YEAR]["PJM"]["import"], float)
    s = pd.read_parquet(KEEPER / f"hourly/system_{YEAR}.parquet")
    s = s[(s["pass"] == "P1") & (s["zone"] == "MISO_external")].sort_values("hour")
    p_bus = s["price"].to_numpy(float)
    n_remerit = (
        (p_bus[None, :] > neigh[:, None]) & ~(p_bus[None, :] > inc[:, None])
    ).sum(0)
    hit, miss = n_remerit > 0, n_remerit == 0

    ik, ia = _imports(KEEPER), _imports(arm)
    d = ia - ik
    d_hit = float(d[hit].mean()) if hit.any() else float("nan")
    d_miss = float(d[miss].mean()) if miss.any() else 0.0

    def _sd(bundle: Path) -> tuple[float, float]:
        t = pd.read_parquet(bundle / f"hourly/system_{YEAR}.parquet")
        t = t[t["pass"] == "P1"]
        return float(t["slack"].sum()) / 1e6, float(t["dump"].sum()) / 1e6

    sk, dk = _sd(KEEPER)
    sa, da = _sd(arm)
    leg_a = bool(np.isfinite(d_hit) and d_hit > d_miss)
    leg_b = bool(abs(sa - sk) <= G5_MAX_SLACK_DUMP_TWH and abs(da - dk) <= G5_MAX_SLACK_DUMP_TWH)
    return {
        "pass": leg_a and leg_b,
        "leg_a_concentration_pass": leg_a,
        "leg_b_slack_dump_pass": leg_b,
        "n_hours_with_remerit": int(hit.sum()),
        "n_hours_without_remerit": int(miss.sum()),
        "import_delta_mw_remerit_hours": _r(d_hit, 1),
        "import_delta_mw_zero_remerit_hours": _r(d_miss, 1),
        "slack_twh_keeper": _r(sk, 4),
        "slack_twh_arm": _r(sa, 4),
        "dump_twh_keeper": _r(dk, 4),
        "dump_twh_arm": _r(da, 4),
        "max_slack_dump_delta_twh": G5_MAX_SLACK_DUMP_TWH,
    }


def gate_g4(arm: Path) -> dict:
    """C1 per class, DELTA-TRANSFER — construction and bands UNCHANGED from miso-225."""
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


def price_report_only(arm: Path) -> dict:
    """The price deltas — REPORTED, never gated (PRECOMMIT §4). See the module docstring."""
    pk, lk = _sysprice(KEEPER)
    pa, la = _sysprice(arm)
    body = pk <= np.percentile(pk, 90)
    return {
        "gated": False,
        "keeper_body_mean": _r(pk[body].mean()),
        "arm_body_mean": _r(pa[body].mean()),
        "body_delta": _r(pa[body].mean() - pk[body].mean()),
        "tail_delta": _r(pa[~body].mean() - pk[~body].mean()),
        "annual_lw_delta": _r(la.mean() - lk.mean()),
        "lw_body_delta": _r(la[body].mean() - lk[body].mean()),
        "miso225_joint_arm_body_delta": -1.917,
    }


def main() -> int:
    arm = Path(sys.argv[1]).resolve()
    solve_log = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None
    rec = {
        "probe": "miso-226 screen gates (2023, blind) — the SEAM ARM ALONE",
        "arm": str(arm.relative_to(REPO)),
        "keeper": KEEPER_ID,
        "control": "form 4 — the committed keeper (G-DRIFT 07099620..47e306d3 ALL INERT)",
        "solve_log": str(solve_log) if solve_log else None,
        "gates": {},
    }
    rec["gates"]["S1"] = gate_s1(arm)
    rec["gates"]["S2"] = gate_s2(arm, solve_log)
    rec["gates"]["G2"] = gate_g2(arm)
    rec["gates"]["G4"] = gate_g4(arm)
    rec["gates"]["G5"] = gate_g5(arm)
    rec["price_report_only"] = price_report_only(arm)
    kills = [g for g in ("S1", "S2", "G2", "G4", "G5") if not rec["gates"][g]["pass"]]
    rec["verdict"] = (
        "ARM SURVIVES THE SCREEN" if not kills else f"ARM KILLED ON {', '.join(kills)}"
    )
    OUT.write_text(json.dumps(rec, indent=1))
    for g, v in rec["gates"].items():
        print(g, "PASS" if v["pass"] else "FAIL", {k: x for k, x in v.items() if k != "cells"})
    print("price (report only):", rec["price_report_only"])
    print(rec["verdict"])
    print(f"-> {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
