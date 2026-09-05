"""nyiso-190 — WHOSE energy the nyiso-189 promotion moved into the 2024 ``CC_REGULAR`` cell.

A ZERO-SOLVE provenance decomposition on committed artifacts only, executing
the bars of ``results/calibration/PREREG-nyiso190-cc2024-displacement-provenance.md``
(pushed before the first number was read; rule 1 ``[R-STRUCT]``).

The object: the nyiso-189 promotion took C1-2024 ``CC_REGULAR`` from +2.05 to
+3.33 TWh (+1.8 → +2.8 pp against a 3.0 pp band), and the FINDING justifies
that in one unmeasured clause — *"the NYC steam it displaces is what the market
committed anyway"*. This probe measures that clause.

Instrument (PREREG §2): the registered arm payload
(``2026-09-05-nyiso-189-steam-identity``) against the registered
``2026-09-04-nyiso-188-combined`` payload — established BIT-IDENTICAL to the
nyiso-189 same-HEAD control (0 of 52,560 prices differ in every year) — and the
bench's per-plant CAMPD / EIA-923 record. Annual levels come from the exact
floats; the per-plant b64 blobs (``round(100·mw/npl)``, uint8, 8760) are used
only to classify hours and apportion removed MWh.

Bars (PREREG §3), 2024 gated, 2023/2025 reported as context:
  V1  payload class totals reproduce the FINDING's control/arm columns
  B1  share of removed MWh falling in measured-online hours      (H1 iff ≥ 0.50)
  B2  share of displaced TWh moved AWAY from actual              (H1 iff ≥ 0.50)
  B3  gas-family pinning (band + arm-vs-control family movement)
  B4  the displaced set's zone/class composition (descriptive, fixes the naming)

Stop S2 (PREREG §5): this is observed unit conduct and can therefore NEVER
identify the cell-G mechanism (nyiso-97 §5 re-open bar). It characterizes the
cell and sizes the owner's choice; it supplies no parameter, unit set, MW
requirement or window.
"""

from __future__ import annotations

import base64
import gzip
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.backcast_artifacts import decode_run_js  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "frontend/data/backcast/runs"
BENCH = ROOT / "frontend/data/backcast/bench/NYISO"

ARM_ID = "2026-09-05-nyiso-189-steam-identity"
CTL_ID = "2026-09-04-nyiso-188-combined"
YEARS = ("2023", "2024", "2025")
GATED_YEAR = "2024"

# PREREG §3: the displaced set's membership threshold (1 GWh — above the 4-dp
# rounding of the payload's own annual TWh).
DISPLACED_EPS_TWH = 0.001
# PREREG §3 B1: measured-online bar = 2 % of nameplate (two codec bytes, twice
# the quantum; the nyiso-175 online-bar convention). 1 % and 5 % are the
# pre-registered sensitivities; the 2 % bar decides.
ONLINE_BARS_PCT = (1.0, 2.0, 5.0)
DECIDING_BAR_PCT = 2.0
# PREREG §3 B3: the gas fossil family, and the C1-2024 volume band.
GAS_FAMILY = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
C1_VOL_BAND_TWH = 3.82
FAMILY_MOVE_TOL_TWH = 0.25
# PREREG §3 B4: the pre-committed naming rule's cell set.
DOWNSTATE_ZONES = ("NYC", "Long_Island", "Lower_Hudson")
STEAM_COGEN_CLASSES = ("ST_GAS", "ST_CHP", "CC_CHP", "CT_CHP")
NAMING_RULE_SHARE = 0.50
# PREREG §2 V1: the FINDING §3.1 control → arm 2024 class columns, verbatim.
V1_EXPECTED_2024 = {
    "CC_REGULAR": (36.11, 37.39),
    "CC_CHP": (19.56, 18.84),
}
V1_TOL_TWH = 0.01


def _dec(blob: str) -> np.ndarray:
    """Decode a per-plant b64 uint8 series to its raw byte values (0-250)."""
    return np.frombuffer(base64.b64decode(blob), dtype=np.uint8).astype(float)


def _load():
    """Load the two registered payloads and the three bench years."""
    arm = decode_run_js((RUNS / f"{ARM_ID}.js").read_text())
    ctl = decode_run_js((RUNS / f"{CTL_ID}.js").read_text())
    bench = {
        y: json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"] for y in YEARS
    }
    return arm, ctl, bench


def run_v1(arm: dict, ctl: dict) -> dict:
    """V1 — the payloads must be the runs the FINDING describes."""
    rows, ok = [], True
    for klass, (c_exp, a_exp) in V1_EXPECTED_2024.items():
        c_got = float(ctl["years"][GATED_YEAR]["gmModel"].get(klass, 0.0))
        a_got = float(arm["years"][GATED_YEAR]["gmModel"].get(klass, 0.0))
        row_ok = abs(c_got - c_exp) <= V1_TOL_TWH and abs(a_got - a_exp) <= V1_TOL_TWH
        ok &= row_ok
        rows.append(
            {
                "class": klass,
                "control_expected": c_exp,
                "control_got": round(c_got, 4),
                "arm_expected": a_exp,
                "arm_got": round(a_got, 4),
                "ok": bool(row_ok),
            }
        )
    return {"passed": bool(ok), "tol_twh": V1_TOL_TWH, "rows": rows}


def displaced_set(arm: dict, ctl: dict, year: str) -> tuple[dict, dict]:
    """Split every plant-class key by the sign of its annual model movement."""
    ap, cp = arm["years"][year]["plants"], ctl["years"][year]["plants"]
    down, up = {}, {}
    for key in sorted(set(ap) | set(cp)):
        d = float(ap.get(key, {}).get("m_ann", 0.0)) - float(
            cp.get(key, {}).get("m_ann", 0.0)
        )
        if d < -DISPLACED_EPS_TWH:
            down[key] = d
        elif d > DISPLACED_EPS_TWH:
            up[key] = d
    return down, up


def run_b1(arm: dict, ctl: dict, bench: dict, year: str, down: dict) -> dict:
    """B1 — what share of the removed MWh fell in measured-online hours."""
    ap, cp, bp = arm["years"][year]["plants"], ctl["years"][year]["plants"], bench["plants"]
    tot = {b: 0.0 for b in ONLINE_BARS_PCT}
    removed_total = 0.0
    no_bench, nodata = [], []
    per_plant = []
    for key in down:
        if key not in bp:
            no_bench.append(key)
            continue
        if bp[key].get("nodata"):
            nodata.append(key)
            continue
        npl = float(bp[key]["npl"]) or 1.0
        a = _dec(ap[key]["m"]) / 100.0 * npl
        c = _dec(cp[key]["m"]) / 100.0 * npl
        meas = _dec(bp[key]["campd"]) / 100.0 * npl
        n = min(len(a), len(c), len(meas))
        rho = np.maximum(0.0, c[:n] - a[:n])
        r_sum = float(rho.sum())
        if r_sum <= 0.0:
            continue
        removed_total += r_sum
        shares = {}
        for barpct in ONLINE_BARS_PCT:
            online = meas[:n] >= (barpct / 100.0) * npl
            got = float(rho[online].sum())
            tot[barpct] += got
            shares[barpct] = got / r_sum
        per_plant.append(
            {
                "key": key,
                "name": bp[key]["name"],
                "zone": bp[key]["zone"],
                "group": bp[key]["group"],
                "npl_mw": round(npl),
                "d_m_ann_twh": round(down[key], 4),
                "removed_gwh": round(r_sum / 1e3, 2),
                "s_online": {f"{b:g}%": round(shares[b], 4) for b in ONLINE_BARS_PCT},
            }
        )
    per_plant.sort(key=lambda r: r["d_m_ann_twh"])
    s = {f"{b:g}%": (round(tot[b] / removed_total, 4) if removed_total else None)
         for b in ONLINE_BARS_PCT}
    deciding = tot[DECIDING_BAR_PCT] / removed_total if removed_total else None
    return {
        "bar": ">= 0.50 at the 2% online bar",
        "s_online": s,
        "deciding_bar_pct": DECIDING_BAR_PCT,
        "s_online_deciding": (round(deciding, 4) if deciding is not None else None),
        "verdict": (
            "SUPPORTED" if deciding is not None and deciding >= 0.50
            else ("REFUTED" if deciding is not None else "UNEVALUABLE")
        ),
        "removed_twh_scored": round(removed_total / 1e6, 4),
        "excluded_no_bench_record": no_bench,
        "excluded_nodata": nodata,
        "per_plant": per_plant,
    }


def run_b2(arm: dict, ctl: dict, bench: dict, year: str, down: dict) -> dict:
    """B2 — did the displacement move those plants away from their actuals."""
    ap, cp, bp = arm["years"][year]["plants"], ctl["years"][year]["plants"], bench["plants"]
    out = {}
    for basis in ("c_ann", "e_ann"):
        away = same = toward = 0.0
        rows, unscored = [], 0.0
        for key, d in down.items():
            if key not in bp:
                unscored += abs(d)
                continue
            actual = float(bp[key].get(basis) or 0.0)
            if basis == "c_ann" and bp[key].get("nodata"):
                unscored += abs(d)
                continue
            e_c = float(cp[key]["m_ann"]) - actual
            e_a = float(ap[key]["m_ann"]) - actual
            w = abs(d)
            if abs(e_a) > abs(e_c):
                away += w
                verdict = "away"
            elif abs(e_a) < abs(e_c):
                toward += w
                verdict = "toward"
            else:
                same += w
                verdict = "same"
            rows.append(
                {
                    "key": key,
                    "name": bp[key]["name"],
                    "zone": bp[key]["zone"],
                    "group": bp[key]["group"],
                    "d_m_ann_twh": round(d, 4),
                    "control_twh": round(float(cp[key]["m_ann"]), 4),
                    "arm_twh": round(float(ap[key]["m_ann"]), 4),
                    "actual_twh": round(actual, 4),
                    "err_control": round(e_c, 4),
                    "err_arm": round(e_a, 4),
                    "moves": verdict,
                    "ct_only_flag": bool(bp[key].get("ctOnly") or bp[key].get("ct_only")),
                }
            )
        scored = away + same + toward
        rows.sort(key=lambda r: r["d_m_ann_twh"])
        out[basis] = {
            "w_away": round(away / scored, 4) if scored else None,
            "w_toward": round(toward / scored, 4) if scored else None,
            "w_same": round(same / scored, 4) if scored else None,
            "scored_twh": round(scored, 4),
            "unscored_twh": round(unscored, 4),
            "rows": rows,
        }
    dec = out["c_ann"]["w_away"]
    return {
        "bar": ">= 0.50 on the CAMPD (c_ann) basis",
        "primary_basis": "c_ann",
        "w_away_deciding": dec,
        "verdict": (
            "SUPPORTED" if dec is not None and dec >= 0.50
            else ("REFUTED" if dec is not None else "UNEVALUABLE")
        ),
        "bases_agree": (out["c_ann"]["w_away"] is not None
                        and out["e_ann"]["w_away"] is not None
                        and (out["c_ann"]["w_away"] >= 0.50)
                        == (out["e_ann"]["w_away"] >= 0.50)),
        "by_basis": out,
    }


def run_b3(arm: dict, ctl: dict, bench: dict, year: str) -> dict:
    """B3 — is the gas family still pinned, and did the arm move its total."""
    gm_a, gm_c = arm["years"][year]["gmModel"], ctl["years"][year]["gmModel"]
    cf = bench["classFull"]

    def _tot(d):
        return sum(float(d.get(k) or 0.0) for k in GAS_FAMILY)

    def _actual(k):
        v = cf.get(k)
        if isinstance(v, dict):
            return float(v.get("ann") or v.get("a_ann") or 0.0)
        if isinstance(v, list):
            return float(v[0]) if v else 0.0
        return float(v or 0.0)

    fam_a, fam_c = _tot(gm_a), _tot(gm_c)
    fam_act = sum(_actual(k) for k in GAS_FAMILY)
    move = abs(fam_a - fam_c)
    in_band = abs(fam_a - fam_act) <= C1_VOL_BAND_TWH
    return {
        "family": list(GAS_FAMILY),
        "family_model_control_twh": round(fam_c, 4),
        "family_model_arm_twh": round(fam_a, 4),
        "family_actual_twh": round(fam_act, 4),
        "arm_minus_actual_twh": round(fam_a - fam_act, 4),
        "band_twh": C1_VOL_BAND_TWH,
        "a_in_band": bool(in_band),
        "arm_minus_control_twh": round(fam_a - fam_c, 4),
        "b_move_tol_twh": FAMILY_MOVE_TOL_TWH,
        "b_move_ok": bool(move <= FAMILY_MOVE_TOL_TWH),
        "verdict": "HOLDS" if (in_band and move <= FAMILY_MOVE_TOL_TWH) else "BREAKS",
        "per_class": {
            k: {
                "control": round(float(gm_c.get(k) or 0.0), 4),
                "arm": round(float(gm_a.get(k) or 0.0), 4),
                "actual": round(_actual(k), 4),
            }
            for k in GAS_FAMILY
        },
    }


def run_b4(bench: dict, down: dict) -> dict:
    """B4 — the displaced set's real zone/class composition (fixes the naming)."""
    bp = bench["plants"]
    by_zone, by_group, by_cell = {}, {}, {}
    tot = unmapped = 0.0
    for key, d in down.items():
        w = abs(d)
        tot += w
        if key not in bp:
            unmapped += w
            by_zone["(no bench record)"] = by_zone.get("(no bench record)", 0.0) + w
            by_group["(no bench record)"] = by_group.get("(no bench record)", 0.0) + w
            continue
        z, g = bp[key]["zone"], bp[key]["group"]
        by_zone[z] = by_zone.get(z, 0.0) + w
        by_group[g] = by_group.get(g, 0.0) + w
        by_cell[f"{z}|{g}"] = by_cell.get(f"{z}|{g}", 0.0) + w
    named = sum(
        v for k, v in by_cell.items()
        if k.split("|")[0] in DOWNSTATE_ZONES and k.split("|")[1] in STEAM_COGEN_CLASSES
    )
    share = named / tot if tot else 0.0
    return {
        "displaced_total_twh": round(tot, 4),
        "unmapped_twh": round(unmapped, 4),
        "by_zone_twh": {k: round(v, 4) for k, v in sorted(by_zone.items(), key=lambda x: -x[1])},
        "by_group_twh": {k: round(v, 4) for k, v in sorted(by_group.items(), key=lambda x: -x[1])},
        "by_cell_twh": {k: round(v, 4) for k, v in sorted(by_cell.items(), key=lambda x: -x[1])},
        "downstate_steam_cogen_share": round(share, 4),
        "naming_rule_share": NAMING_RULE_SHARE,
        "may_call_it_nyc_steam_cogen": bool(share >= NAMING_RULE_SHARE),
    }


def main() -> int:
    arm, ctl, bench = _load()
    rec: dict = {
        "session": "nyiso-190",
        "prereg": "results/calibration/PREREG-nyiso190-cc2024-displacement-provenance.md",
        "arm_run": ARM_ID,
        "control_run": CTL_ID,
        "control_basis": (
            "the nyiso-189 same-HEAD control was BIT-IDENTICAL to this run "
            "(0 of 52,560 prices differ in every year, FINDING-nyiso189 §3)"
        ),
        "solves": 0,
        "V1": run_v1(arm, ctl),
    }
    if not rec["V1"]["passed"]:
        rec["bars"] = "UNEVALUABLE — V1 failed (PREREG §2)"
        print(json.dumps(rec, indent=2))
        return 1
    rec["by_year"] = {}
    for year in YEARS:
        down, up = displaced_set(arm, ctl, year)
        entry = {
            "gated": year == GATED_YEAR,
            "displaced_keys": len(down),
            "gaining_keys": len(up),
            "displaced_twh": round(sum(abs(v) for v in down.values()), 4),
            "gained_twh": round(sum(up.values()), 4),
            "B4": run_b4(bench[year], down),
            "B1": run_b1(arm, ctl, bench[year], year, down),
            "B2": run_b2(arm, ctl, bench[year], year, down),
            "B3": run_b3(arm, ctl, bench[year], year),
            "top_gainers_twh": {
                k: round(v, 4)
                for k, v in sorted(up.items(), key=lambda x: -x[1])[:8]
            },
        }
        rec["by_year"][year] = entry
    g = rec["by_year"][GATED_YEAR]
    rec["verdict"] = {
        "year": GATED_YEAR,
        "B1": g["B1"]["verdict"],
        "B2": g["B2"]["verdict"],
        "B3": g["B3"]["verdict"],
        "H1_supported": bool(
            g["B1"]["verdict"] == "SUPPORTED"
            and g["B2"]["verdict"] == "SUPPORTED"
            and g["B3"]["verdict"] == "HOLDS"
        ),
    }
    out = ROOT / "results/calibration/_nyiso190_displacement_provenance.json"
    out.write_text(json.dumps(rec, indent=2))
    print(json.dumps(rec["verdict"], indent=2))
    print(f"\nwrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
