"""nyiso-130 A/B gate evaluation — the six pre-registered kill gates + predictions.

Scores the pre-registered kill gates K1-K6 and the ex-ante predictions P1-P5 of
``results/calibration/PREREG-nyiso130-li-transfer-security-limit-2026-08-06.md``
from the two arms' committed bundles only. No solve, no re-run.

The gates, verbatim from the prereg:

======  ========================================================================
K1      config isolation — more than ONE differing ``scenario_config`` field
K2      feasibility — any new unserved energy (slack) or dump, either arm
K3      liveness — in-window ``limit_up`` != 940.0 on ``NYC>Long_Island``
K4      scope — any OTHER link's ``limit_up`` changes
K5      seam — the arm must not import its way out through the priced seam
K6      forcing — any D-2 mechanism's forced share RISES, or the LI self-supply
        floor reappears for Long_Island (rule 19 ``[R-ONE-MECH]``)
======  ========================================================================

Run: ``python scripts/probes/_nyiso130_ab_gates.py``
Writes ``results/calibration/_nyiso130_ab_gates.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

CONTROL = REPO / "results/calibration/nyiso130_control"
TREATMENT = REPO / "results/calibration/nyiso130_n11tsl"
YEARS = (2023, 2024, 2025)

LI_AC_LINK = "NYC>Long_Island"
WINDOW_HOURS = tuple(range(14, 22))
EXPECTED_N11_MW = 940.0
TAIL_THRESHOLD_USD = 300.0
TAIL_LO, TAIL_HI = 0.5, 2.0
RT_ACTUAL_TAIL = {2023: 10, 2024: 12, 2025: 42}
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
    diff = {k: [c.get(k, "<absent>"), t.get(k, "<absent>")] for k in sorted(keys)
            if c.get(k, "<absent>") != t.get(k, "<absent>")}
    ok = list(diff) == [ARMED_FIELD]
    return {"gate": "K1 config isolation", "passed": bool(ok),
            "n_fields_compared": len(keys), "differing": diff}


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
            lim_out = sorted({round(float(x), 1) for x in g["limit_up"].to_numpy()[~inw]})
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
    return {"gate": "K4 scope", "passed": bool(ok), "links_with_changed_bounds": changed}


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


def k6_forcing() -> dict:
    """No D-2 mechanism's forced share rises; the LI self-supply floor stays off."""
    def d2(bundle: Path) -> dict:
        doc = json.loads((bundle / "legitimacy_diagnostics.json").read_text())
        return {
            (r["year"], r["mechanism"], r.get("class", "")): float(r["share_of_class"])
            for r in doc["diagnostics"]["D2"]["rows"]
        }

    c, t = d2(CONTROL), d2(TREATMENT)
    risen = {
        f"{k[0]} {k[1]} {k[2]}".strip(): [c.get(k, 0.0), v]
        for k, v in t.items()
        if v > c.get(k, 0.0) + 1e-6
    }
    selfsupply = sorted({k[1] for k in t if "selfsupply" in k[1]})
    return {
        "gate": "K6 forcing",
        "passed": bool(not risen and not selfsupply),
        "mechanisms_whose_forced_share_rose": risen,
        "selfsupply_mechanisms_present_in_treatment_d2": selfsupply,
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
                "li_ac_import_in_window_p50_mw": round(float(np.percentile(mw[inw], 50)), 1),
                "li_ac_import_twh": round(float(mw.sum() / 1e6), 4),
                "tail_hours": int(len(tail)),
                "tail_zones": tail.index.map(wide.idxmax(axis=1)).value_counts().to_dict()
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
            k: round(rec["treatment"]["class_twh"].get(k, 0.0)
                     - rec["control"]["class_twh"].get(k, 0.0), 4)
            for k in sorted(
                set(rec["treatment"]["class_twh"]) | set(rec["control"]["class_twh"])
            )
        }
        out[str(year)] = rec
    return out


def main() -> int:
    """Score every gate and prediction, write the record, print the verdict."""
    gates = [k1_config_isolation(), k2_feasibility(), k3_liveness(), k4_scope(),
             k5_seam(), k6_forcing()]
    record = {
        "session": "nyiso-130",
        "prereg": "results/calibration/PREREG-nyiso130-li-transfer-security-limit-2026-08-06.md",
        "arms": {"control": str(CONTROL.relative_to(REPO)),
                 "treatment": str(TREATMENT.relative_to(REPO))},
        "kill_gates": gates,
        "all_gates_silent": all(g["passed"] for g in gates),
        "predictions": predictions(),
    }
    dest = REPO / "results/calibration/_nyiso130_ab_gates.json"
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
