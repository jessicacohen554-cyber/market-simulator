"""nyiso-143 A/B gate evaluation — K1-K5 as nyiso-130 wrote them, plus **K6'**.

Scores the pre-registered gates of
``results/calibration/PREREG-nyiso143-zone-k-transfer-bound-2026-08-18.md``
from the two arms' committed bundles only. **No solve, no re-run.**

K1-K5 are carried over VERBATIM from ``_nyiso130_ab_gates.py`` (config
isolation / feasibility / liveness / scope / seam); all five passed there and a
regression on any of them kills the arm.

**K6 is REPLACED by K6'** (owner-adopted, ``FINDING-nyiso140-li-st-floor-
membership-2026-08-16.md`` §5/§6.3). A rise in a D-2 mechanism's forced share
is **not itself a kill**: an import-relief lever moves both terms of
``forced_twh / class_twh`` the wrong way by construction. It escalates to
provenance + shape and fails only on a miss:

  (a) **provenance** — every binding mechanism still clears **D-4**, which
      since nyiso-143 means the window test AND the per-unit conduct rider;
  (b) **shape** — the class's **D-1** ``profile_r`` / ``cv_ratio`` still clear.

The energy-normalised ``dforced = forced_arm - forced_ctrl * (energy_arm /
energy_ctrl)`` is reported at full magnitude and is **not gated**.

**Leg (a) is scored ARM-vs-CONTROL**, per the pre-registration's §3 declared
reading: a mechanism failing D-4 in BOTH arms is a pre-existing defect (here,
plant 2480 Danskammer under ``Capital_Hudson x ST_GAS``) and does not kill the
arm; only a mechanism that NEWLY fails in the arm does. Both the absolute and
the delta verdicts are recorded so an owner who overturns the reading can see
what the other one says without a re-run.

Run: ``python scripts/probes/_nyiso143_ab_gates.py``
Writes ``results/calibration/_nyiso143_ab_gates.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

CONTROL = REPO / "results/calibration/nyiso143_control"
TREATMENT = REPO / "results/calibration/nyiso143_n11tsl_arm"
YEARS = (2023, 2024, 2025)

LI_AC_LINK = "NYC>Long_Island"
WINDOW_HOURS = tuple(range(14, 22))
EXPECTED_N11_MW = 940.0
TAIL_THRESHOLD_USD = 300.0
TAIL_LO, TAIL_HI = 0.5, 2.0
# frontend/data/backcast/tail/actual_tail.json at HEAD — the nyiso-139
# clock repair moved 2024 from 12 to 13.
RT_ACTUAL_TAIL = {2023: 10, 2024: 13, 2025: 42}
# The one field the arms are allowed to differ in.
ARMED_FIELD = "nyiso_li_tsl_n11_security"
# The priced seam band the arm must not exploit (prereg K5).
SEAM_BAND = 0.02


def _cfg(bundle: Path) -> dict:
    doc = json.loads((bundle / "run_config.json").read_text())
    return doc.get("scenario_config", doc)


def _links(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"network_{year}.parquet")
    return df[(df["kind"] == "link") & (df["pass"] == "P1")]


def _system(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[df["pass"] == "P1"]


def k1_config_isolation() -> dict:
    """Exactly one differing scenario_config field, and it is the armed one."""
    c, t = _cfg(CONTROL), _cfg(TREATMENT)
    keys = set(c) | set(t)
    diff = {
        k: [c.get(k, "<absent>"), t.get(k, "<absent>")]
        for k in sorted(keys)
        if c.get(k, "<absent>") != t.get(k, "<absent>")
    }
    ok = list(diff) == [ARMED_FIELD]
    return {
        "gate": "K1 config isolation",
        "passed": bool(ok),
        "n_fields_compared": len(keys),
        "differing": diff,
    }


def k2_feasibility() -> dict:
    """Zero unserved energy and zero dump, both arms, every year."""
    rows = {}
    ok = True
    for name, b in (("control", CONTROL), ("treatment", TREATMENT)):
        for year in YEARS:
            s = _system(b, year)
            slack = float(s["slack"].sum())
            dump = float(s["dump"].sum())
            rows[f"{name}_{year}"] = {"slack_mwh": slack, "dump_mwh": dump}
            ok = ok and slack == 0.0 and dump == 0.0
    return {"gate": "K2 feasibility", "passed": bool(ok), "rows": rows}


def k3_liveness() -> dict:
    """In-window bound reads 940 in the treatment and the published net in control."""
    rows, ok = {}, True
    for name, b in (("control", CONTROL), ("treatment", TREATMENT)):
        for year in YEARS:
            g = _links(b, year)
            g = g[g["name"] == LI_AC_LINK].sort_values("hour")
            hod = g["hour"].to_numpy(int) % 24
            inw = np.isin(hod, WINDOW_HOURS)
            lim_in = sorted({round(float(x), 1) for x in g["limit_up"].to_numpy()[inw]})
            lim_out = sorted(
                {round(float(x), 1) for x in g["limit_up"].to_numpy()[~inw]}
            )
            rows[f"{name}_{year}"] = {"in_window_mw": lim_in, "off_window_mw": lim_out}
            if name == "treatment":
                ok = ok and lim_in == [EXPECTED_N11_MW]
            else:
                ok = ok and lim_in != [EXPECTED_N11_MW]
    return {"gate": "K3 liveness", "passed": bool(ok), "rows": rows}


def k4_scope() -> dict:
    """No link but NYC>Long_Island changes its bound."""
    changed, ok = {}, True
    for year in YEARS:
        c, t = _links(CONTROL, year), _links(TREATMENT, year)
        for link in sorted(set(c["name"]) | set(t["name"])):
            cl = c[c["name"] == link].sort_values("hour")["limit_up"].to_numpy(float)
            tl = t[t["name"] == link].sort_values("hour")["limit_up"].to_numpy(float)
            if cl.shape != tl.shape or not np.allclose(cl, tl):
                changed.setdefault(str(year), []).append(link)
                if link != LI_AC_LINK:
                    ok = False
    return {
        "gate": "K4 scope",
        "passed": bool(ok),
        "links_with_changed_bounds": changed,
    }


def k5_seam() -> dict:
    """The arm must not import its way out through the priced external seam."""
    rows, ok = {}, True
    for year in YEARS:
        c, t = _links(CONTROL, year), _links(TREATMENT, year)
        ext = [n for n in sorted(set(c["name"])) if n.startswith("NYISO_external>")]
        ce = float(sum(c[c["name"] == n]["mw"].sum() for n in ext))
        te = float(sum(t[t["name"] == n]["mw"].sum() for n in ext))
        rel = (te - ce) / ce if ce else 0.0
        rows[str(year)] = {
            "control_import_twh": round(ce / 1e6, 4),
            "treatment_import_twh": round(te / 1e6, 4),
            "relative_change": round(rel, 5),
        }
        ok = ok and abs(rel) <= SEAM_BAND
    return {"gate": "K5 seam", "passed": bool(ok), "band": SEAM_BAND, "rows": rows}


def _legit(bundle: Path) -> dict:
    return json.loads((bundle / "legitimacy_diagnostics.json").read_text())


def _d2_rows(doc: dict) -> dict:
    return {
        (r["year"], r["mechanism"], r.get("class", "")): r
        for r in doc["diagnostics"]["D2"]["rows"]
    }


def _d4_failures(doc: dict) -> set:
    """(year, floor label, check, plant) of every FAILing D-4 row."""
    return {
        (
            int(r.get("year", -1)),
            str(r.get("floor", "")),
            str(r.get("check", "window")),
            str(r.get("plant", "")),
        )
        for r in doc["diagnostics"]["D4"]["rows"]
        if str(r.get("verdict")) == "FAIL"
    }


def _d1_misses(doc: dict) -> dict:
    """Classes whose D-1 shape gates miss, per year."""
    gates = doc.get("gates", {})
    min_r = float(gates.get("d1_min_profile_r", 0.8))
    min_cv = float(gates.get("d1_min_cv_ratio", 0.5))
    out = {}
    for r in doc["diagnostics"]["D1"]["rows"]:
        pr, cv = r.get("profile_r"), r.get("cv_ratio")
        bad = (pr is None or float(pr) < min_r) or (
            cv is not None and float(cv) < min_cv
        )
        if bad:
            out[f"{r.get('year')} {r.get('class')}"] = {
                "profile_r": pr,
                "cv_ratio": cv,
                "min_profile_r": min_r,
                "min_cv_ratio": min_cv,
            }
    return out


def k6prime_forcing() -> dict:
    """K6' — a forced-share rise escalates to provenance + shape, not a kill."""
    cd, td = _legit(CONTROL), _legit(TREATMENT)
    c, t = _d2_rows(cd), _d2_rows(td)

    risen, normalised = {}, {}
    for k, tr in t.items():
        cr = c.get(k)
        c_share = float(cr["share_of_class"]) if cr else 0.0
        t_share = float(tr["share_of_class"])
        if t_share <= c_share + 1e-6:
            continue
        label = f"{k[0]} {k[1]} {k[2]}".strip()
        risen[label] = [round(c_share, 4), round(t_share, 4)]
        # Energy-normalised delta: strip the mechanical part of the move.
        # REPORTED, never gated.
        c_forced = float(cr.get("forced_twh", 0.0)) if cr else 0.0
        t_forced = float(tr.get("forced_twh", 0.0))
        c_energy = float(cr.get("class_total_twh", 0.0)) if cr else 0.0
        t_energy = float(tr.get("class_total_twh", 0.0))
        scale = (t_energy / c_energy) if c_energy else 1.0
        normalised[label] = {
            "forced_twh": [round(c_forced, 4), round(t_forced, 4)],
            "class_twh": [round(c_energy, 4), round(t_energy, 4)],
            "delta_forced_energy_normalised_twh": round(t_forced - c_forced * scale, 4),
        }

    # (a) provenance — D-4, scored ARM-vs-CONTROL per the prereg §3 reading.
    cf, tf = _d4_failures(cd), _d4_failures(td)
    new_d4 = sorted(
        f"{y} {lab} [{chk}{' ' + pl if pl else ''}]" for y, lab, chk, pl in tf - cf
    )
    pre_d4 = sorted(
        f"{y} {lab} [{chk}{' ' + pl if pl else ''}]" for y, lab, chk, pl in tf & cf
    )
    # (b) shape — D-1.
    cm, tm = _d1_misses(cd), _d1_misses(td)
    new_d1 = {k: v for k, v in tm.items() if k not in cm}

    escalated = bool(risen)
    fails_a = bool(new_d4)
    fails_b = bool(new_d1)
    passed = (not escalated) or (not fails_a and not fails_b)
    return {
        "gate": "K6' forcing provenance + shape",
        "passed": bool(passed),
        "escalated": escalated,
        "mechanisms_whose_forced_share_rose": risen,
        "energy_normalised_delta_reported_not_gated": normalised,
        "leg_a_provenance_new_d4_failures_in_arm": new_d4,
        "leg_a_provenance_preexisting_d4_failures_both_arms": pre_d4,
        "leg_a_absolute_reading_would_fire": bool(tf),
        "leg_b_shape_new_d1_misses_in_arm": new_d1,
        "selfsupply_mechanisms_present_in_treatment_d2": sorted(
            {k[1] for k in t if "selfsupply" in k[1]}
        ),
        "reading": (
            "leg (a) scored ARM-vs-CONTROL per PREREG-nyiso143 section 3: a "
            "mechanism failing D-4 in BOTH arms is pre-existing and does not "
            "kill the arm. The absolute verdict is recorded alongside so an "
            "owner overturning that reading needs no re-run."
        ),
    }


def predictions() -> dict:
    """P2-P5: bound occupancy, substitution, the C3c tail and mean LMP."""
    out: dict[str, dict] = {}
    for year in YEARS:
        rec: dict = {}
        for name, b in (("control", CONTROL), ("treatment", TREATMENT)):
            g = _links(b, year)
            g = g[g["name"] == LI_AC_LINK].sort_values("hour")
            mw = g["mw"].to_numpy(float)
            lim = g["limit_up"].to_numpy(float)
            hod = g["hour"].to_numpy(int) % 24
            inw = np.isin(hod, WINDOW_HOURS)
            s = _system(b, year)
            wide = s.pivot_table(index="hour", columns="zone", values="price")
            mx = wide.max(axis=1)
            tail = mx[mx > TAIL_THRESHOLD_USD]
            cls = pd.read_parquet(b / "hourly" / f"class_hourly_{year}.parquet")
            cls = cls[cls["pass"] == "P1"]
            rec[name] = {
                "at_bound_share_in_window": round(
                    float((mw[inw] >= 0.999 * lim[inw]).mean()), 4
                ),
                "li_ac_import_in_window_p50_mw": round(
                    float(np.percentile(mw[inw], 50)), 1
                ),
                "li_ac_import_twh": round(float(mw.sum() / 1e6), 4),
                "tail_hours": int(len(tail)),
                "tail_zones": tail.index.map(wide.idxmax(axis=1))
                .value_counts()
                .to_dict()
                if len(tail)
                else {},
                "mean_lmp": round(float(s["price"].mean()), 3),
                "class_twh": {
                    k: round(float(v / 1e6), 4)
                    for k, v in cls.groupby("klass")["mw"].sum().items()
                },
            }
        actual = RT_ACTUAL_TAIL[year]
        rec["tail_gate_band_hours"] = [TAIL_LO * actual, TAIL_HI * actual]
        rec["rt_actual_tail_hours"] = actual
        rec["class_twh_delta"] = {
            k: round(
                rec["treatment"]["class_twh"].get(k, 0.0)
                - rec["control"]["class_twh"].get(k, 0.0),
                4,
            )
            for k in sorted(
                set(rec["treatment"]["class_twh"]) | set(rec["control"]["class_twh"])
            )
        }
        out[str(year)] = rec
    return out


def main() -> int:
    """Score every gate and prediction, write the record, print the verdict."""
    gates = [
        k1_config_isolation(),
        k2_feasibility(),
        k3_liveness(),
        k4_scope(),
        k5_seam(),
        k6prime_forcing(),
    ]
    record = {
        "session": "nyiso-143",
        "prereg": "results/calibration/PREREG-nyiso143-zone-k-transfer-bound-2026-08-18.md",
        "arms": {
            "control": str(CONTROL.relative_to(REPO)),
            "treatment": str(TREATMENT.relative_to(REPO)),
        },
        "kill_gates": gates,
        "all_gates_silent": all(g["passed"] for g in gates),
        "predictions": predictions(),
    }
    dest = REPO / "results/calibration/_nyiso143_ab_gates.json"
    dest.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")

    for g in gates:
        print(f"  [{'PASS' if g['passed'] else 'FIRED'}] {g['gate']}")
    print(f"\nALL KILL GATES SILENT: {record['all_gates_silent']}\n")
    for year, rec in record["predictions"].items():
        c, t = rec["control"], rec["treatment"]
        band = rec["tail_gate_band_hours"]
        print(
            f"  {year}: C3c {c['tail_hours']} -> {t['tail_hours']} h "
            f"(actual {rec['rt_actual_tail_hours']}, band [{band[0]:.0f},{band[1]:.0f}]) | "
            f"mean LMP {c['mean_lmp']} -> {t['mean_lmp']} | "
            f"LI AC in-window p50 {c['li_ac_import_in_window_p50_mw']} -> "
            f"{t['li_ac_import_in_window_p50_mw']} MW | at-bound "
            f"{c['at_bound_share_in_window']:.3f} -> {t['at_bound_share_in_window']:.3f}"
        )
    print(f"\nwrote {dest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
