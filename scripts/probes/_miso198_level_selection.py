"""miso-198 — SELECT the re-identified ST_GAS must-run floor LEVEL, on a frozen rule.

ZERO-SOLVE. **The selection criterion below is frozen in this docstring and the
file is pushed + blob-verified BEFORE any candidate's level or assertion is
computed.** The criterion is mechanical: it enumerates the candidate level
statistics, admits them on STRUCTURAL properties alone, and breaks ties by the
census's own published diagnosis — so the level is never chosen by looking at
which number lands where. No price residual enters anywhere (rule 1
``[R-STRUCT]``); C3a is stated as a pre-registered DIRECTION only.

===============================================================================
WHAT THE CENSUS ALREADY ESTABLISHED (frozen, published, not re-litigated here)
===============================================================================
``_miso198_stgas_oom_conduct_phase0.json`` (rule frozen at ``33facea4``, basis
repaired and re-frozen at ``9ad6b25c``, both blob-verified) measured the ST_GAS
out-of-merit conduct object under the miso-197 W3b conditioning set and
partitioned the gap between it and the keeper's own armed floor EXACTLY:

    year  measured_oom  armed   gap    P(pop)  W(window)  L(level)
    2023     16.059     8.213   7.846  0.162     0.197      0.640
    2024     19.294     8.674  10.620  0.138     0.163      0.699
    2025     17.814     8.902   8.912  0.183     0.153      0.665

**L-3a verdict: DOMINANT = L (level), 3 of 3 years over the 0.45 line.** The
population channel did NOT clear L-3b (5 of its 10 plants fail the operating
test, so the lay-up exclusion census is not a clean identification defect) and
the window channel never reaches the dominance line. The repair is therefore a
LEVEL re-identification of the mechanism that already owns the phenomenon
(rule 19 ``[R-ONE-MECH]``) — never a stacked floor, never a membership change,
never a window change.

===============================================================================
THE FROZEN SELECTION CRITERION
===============================================================================

**CANDIDATES.** Four level statistics, every one MEASURED, every one produced
by the SAME frozen estimator machinery (rule 23 ``[R-FROZEN-DERIVE]``: the
frozen deriver is imported, never restated and never re-tuned), differing ONLY
in the sample the percentile is taken over and the percentile itself:

  * ``C0`` INCUMBENT -- p25 over ALL online hours. This is literally what the
    keeper runs (``thermal_tranches_p25_level_mw_MISO.csv``).
  * ``C1`` -- p25 over (online AND CC-HEADROOM).
  * ``C2`` -- p50 over (online AND CC-HEADROOM).
  * ``C3`` -- p50 over ALL online hours (the incumbent artifact's own published
    ``p50_level_mw`` column).

CC-HEADROOM is the census's inherited miso-197 W3b set: hours in which the
measured MISO CC_REGULAR fleet ran below 0.90 of its own p99.5 that year, i.e.
hours in which cheaper CC capability was demonstrably idle and a strict-merit
stack says the 10-HR steamer should be OFF. Every candidate pools 2023-2025,
the incumbent's own window.

**ADMISSIBILITY.** A candidate is ADMISSIBLE iff all three hold:

  * **S-i CONDUCT-GROUNDED** -- its conditioning set is the CC-HEADROOM hours,
    so the statistic measures THE PHENOMENON BEING REPRESENTED (out-of-merit
    operation) rather than "all hours the plant happened to be on". This is
    what the census proved defective about the incumbent: not the percentile
    but the sample.
  * **S-ii NON-PINNING** -- the level is at or below the plant's own MEDIAN
    measured output over its conditioning set, so at least half the conduct
    sample sits at or above the floor and dispatch above it stays free. This is
    the incumbent field's OWN stated rule-13 property ("dispatch above the
    floor stays free"), applied to the re-identified sample.
  * **S-iii NO WORSE OVER-ASSERTION** -- the candidate's fleet over-assertion
    share (``O / raw_assertion``: the energy the floor asserts in hours the
    plant's own meter did not make it, which is the D-4 per-unit conduct
    direction and rule 17 ``[R-FLOOR-WINDOW]``'s test) is <= **1.25 x** the
    INCUMBENT's own share, in EVERY year. The incumbent sets the bar; the 1.25
    tolerance is declared once, here, and is tuned to nothing.

**SELECTION.** Among ADMISSIBLE candidates take the one with the HIGHEST raw
assertion -- because the census's published L-3a verdict is that the LEVEL
channel is 64-70 % of the gap, so the admissible statistic that recovers the
most measured conduct while staying inside S-ii and S-iii is the correct
re-identification. If NO candidate is admissible the level family is REFUSED
and the session escalates WITHOUT SOLVING rather than tuning a percentile.

**MATERIALITY IS REPORTED, NEVER A SELECTOR** (rule 1): the 2024 increment is
computed on the BASIS-CONSISTENT footing (candidate raw assertion minus the
INCUMBENT's raw assertion, both through the runtime's own floor block) and
printed beside the inherited >= 4.00 TWh CC-2024 requirement -- after the
selection is already decided.

**BASIS-CONSISTENCY NOTE (why raw assertion, not D-2).** The census's M-4/M-5
compared a raw floor assertion against a D-2 *realised at-floor dispatch*
baseline (4.78/5.15/6.60 TWh) -- two different instruments, so those projected
forced shares are inflated and are superseded by the numbers here. Every
quantity in this script is a RAW ASSERTION on both sides, computed by
rebuilding the FleetArrays through ``run_year``'s own chain with ONLY the level
map swapped, so window, membership, availability clip and lay-up mask are the
runtime's own and the comparison is single-delta by construction.

===============================================================================
Usage
===============================================================================
    python3 scripts/probes/_miso198_level_selection.py --satisfiability
    python3 scripts/probes/_miso198_level_selection.py [--emit]

``--emit`` writes the SELECTED candidate to
``data/raw/_processed-legacy/thermal_tranches_oom_level_mw_MISO.csv``.
Record: ``results/calibration/_miso198_level_selection.json``.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

import numpy as np  # noqa: E402

import market_sim.data.fleet as fleet_pkg  # noqa: E402
from market_sim.data.floor_mechanisms import (  # noqa: E402
    MECH_ST_GAS_MUSTRUN_PER_PLANT,
)
from scripts.probes import _miso198_stgas_oom_conduct_phase0 as ph0  # noqa: E402

ISO = "MISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
GROUP = "ST_GAS"
OUT = _REPO / "results" / "calibration" / "_miso198_level_selection.json"
EMIT = (
    _REPO / "data" / "raw" / "_processed-legacy"
    / f"thermal_tranches_oom_level_mw_{ISO}.csv"
)
INCUMBENT_CSV = (
    _REPO / "data" / "raw" / "_processed-legacy"
    / f"thermal_tranches_p25_level_mw_{ISO}.csv"
)

# ---- frozen ex-ante lines (the docstring is the authority) ------------------
S_III_TOLERANCE = 1.25       # over-assertion share vs the INCUMBENT's own
CC24_REQUIREMENT = 4.00      # reported only (FINDING-miso197 §8)
CANDIDATE_SPECS = {
    # key: (percentile, conditioning set, S-i conduct-grounded?)
    "C0": (25, "all-online", False),
    "C1": (25, "oom-online", True),
    "C2": (50, "oom-online", True),
    "C3": (50, "all-online", False),
}


def measured_samples() -> tuple[dict[int, np.ndarray], dict[int, np.ndarray]]:
    """Pooled 2023-2025 measured net-MW samples per ST_GAS plant.

    Returns ``({plant: all-online sample}, {plant: oom-online sample})`` — the
    two conditioning sets the candidates differ over. Both use the census's
    own B2 machinery (the frozen deriver's online mask, net construction and
    derate source) and its inherited CC-headroom set.
    """
    allon: dict[int, list[np.ndarray]] = {}
    oomon: dict[int, list[np.ndarray]] = {}
    for year in YEARS:
        fleet, _fa, _cfg = ph0.build_run_year_fleet(year)
        klass = ph0.model_classes(fleet)
        net, online = ph0.measured_year(year)
        mask, _meta = ph0.cc_headroom_mask(net, klass)
        for code, k in klass.items():
            if k != GROUP:
                continue
            series = net.get(code)
            if series is None:
                continue
            on = online[code]
            if on.any():
                allon.setdefault(code, []).append(series[on])
            oom = on & mask
            if oom.any():
                oomon.setdefault(code, []).append(series[oom])
    return (
        {c: np.concatenate(v) for c, v in allon.items()},
        {c: np.concatenate(v) for c, v in oomon.items()},
    )


def incumbent_levels() -> dict[int, dict[str, float]]:
    """The published incumbent artifact, keyed by plant (ST_GAS rows)."""
    out: dict[int, dict[str, float]] = {}
    with INCUMBENT_CSV.open(newline="") as fh:
        for r in csv.DictReader(fh):
            if r["plant_group"] != GROUP:
                continue
            out[int(r["plant_code"])] = {
                "p25_level_mw": float(r["p25_level_mw"]),
                "p50_level_mw": float(r["p50_level_mw"]),
                "nameplate_mw": float(r["nameplate_mw"]),
            }
    return out


def candidate_levels(
    allon: dict[int, np.ndarray], oomon: dict[int, np.ndarray]
) -> dict[str, dict[int, float]]:
    """{candidate: {plant: level MW}} for the four frozen candidates."""
    inc = incumbent_levels()
    out: dict[str, dict[int, float]] = {}
    for name, (pct, cond, _cg) in CANDIDATE_SPECS.items():
        lv: dict[int, float] = {}
        if cond == "all-online":
            # The PUBLISHED artifact is used verbatim for the all-online
            # candidates so C0 is literally what the keeper runs (rule 23: the
            # frozen deriver's own output, not a restatement of it).
            key = "p25_level_mw" if pct == 25 else "p50_level_mw"
            lv = {c: d[key] for c, d in inc.items()}
        else:
            for code, sample in oomon.items():
                if sample.size < 24:  # dtt._MIN_ONLINE_HOURS
                    continue
                npl = inc.get(code, {}).get("nameplate_mw")
                v = float(np.percentile(sample, pct))
                lv[code] = min(v, npl) if npl else v
        out[name] = lv
    return out


def assert_and_overassert(
    levels: dict[int, float] | None,
) -> dict[int, dict[str, float]]:
    """Rebuild the runtime floor with ``levels`` swapped in; measure it.

    Returns ``{year: {raw_assertion_twh, over_assertion_twh, over_share,
    floored_plants}}``. ``None`` leaves the shipped artifact in place (the
    incumbent, C0). ONLY the level map is swapped, so window, membership, the
    ``pmax*availability`` clip and the lay-up mask are the runtime's own — the
    comparison is single-delta by construction.
    """
    orig = fleet_pkg.thermal_tranche_p25_measured_level
    if levels is not None:
        patched = {(int(c), GROUP): float(v) for c, v in levels.items()}

        def _patched(iso: str):  # noqa: ANN202 - runtime accessor shim
            base = dict(orig(iso))
            base.update(patched)
            return base

        fleet_pkg.thermal_tranche_p25_measured_level = _patched
    try:
        out: dict[int, dict[str, float]] = {}
        for year in YEARS:
            f, fa, _ = ph0.build_run_year_fleet(year)
            floors = ph0.plant_floor_series(f, fa)
            net, _online = ph0.measured_year(year)
            raw = over = 0.0
            for code, flr in floors.items():
                raw += float(flr.sum())
                meas = net.get(code)
                if meas is None:
                    over += float(flr.sum())
                    continue
                over += float(np.maximum(0.0, flr - meas).sum())
            out[year] = {
                "raw_assertion_twh": round(raw / 1e6, 4),
                "over_assertion_twh": round(over / 1e6, 4),
                "over_share": round(over / raw, 4) if raw > 0 else None,
                "floored_plants": sorted(floors),
            }
    finally:
        fleet_pkg.thermal_tranche_p25_measured_level = orig
    return out


def select() -> dict:
    """Run the frozen selection and return the record."""
    print("  pooling measured samples (B2) …")
    allon, oomon = measured_samples()
    cands = candidate_levels(allon, oomon)
    inc = incumbent_levels()
    rec: dict = {
        "probe": Path(__file__).name,
        "iso": ISO,
        "group": GROUP,
        "frozen": {
            "S_III_TOLERANCE": S_III_TOLERANCE,
            "candidates": {k: {"pctile": v[0], "conditioning": v[1],
                               "S_i_conduct_grounded": v[2]}
                           for k, v in CANDIDATE_SPECS.items()},
            "selection": "highest raw assertion among ADMISSIBLE candidates",
        },
        "levels": {},
        "assertion": {},
        "admissibility": {},
    }
    # per-plant level table
    plant_rows = []
    for code in sorted(set(inc) | set(oomon)):
        row = {"plant_code": code,
               "nameplate_mw": inc.get(code, {}).get("nameplate_mw")}
        for name in CANDIDATE_SPECS:
            row[name] = round(cands[name].get(code, float("nan")), 2) \
                if code in cands[name] else None
        row["oom_median_mw"] = (
            round(float(np.median(oomon[code])), 2) if code in oomon else None
        )
        row["oom_sample_hours"] = int(oomon[code].size) if code in oomon else 0
        plant_rows.append(row)
    rec["levels"]["rows"] = plant_rows

    for name in CANDIDATE_SPECS:
        print(f"  measuring candidate {name} through the runtime floor block …")
        rec["assertion"][name] = assert_and_overassert(
            None if name == "C0" else cands[name]
        )

    inc_share = {y: rec["assertion"]["C0"][y]["over_share"] for y in YEARS}
    for name, (pct, cond, cg) in CANDIDATE_SPECS.items():
        s_i = bool(cg)
        # S-ii: level <= the plant's own median over ITS conditioning set.
        viol = []
        for code, lvl in cands[name].items():
            base = oomon.get(code) if cond == "oom-online" else allon.get(code)
            if base is None or base.size == 0:
                continue
            if lvl > float(np.median(base)) + 1e-9:
                viol.append(code)
        s_ii = not viol
        s_iii_years = {}
        for y in YEARS:
            cs = rec["assertion"][name][y]["over_share"]
            bar = (inc_share[y] or 0.0) * S_III_TOLERANCE
            s_iii_years[y] = bool(cs is not None and cs <= bar + 1e-12)
        s_iii = all(s_iii_years.values())
        rec["admissibility"][name] = {
            "S_i_conduct_grounded": s_i,
            "S_ii_non_pinning": s_ii,
            "S_ii_violating_plants": sorted(viol),
            "S_iii_no_worse_over_assertion": s_iii,
            "S_iii_by_year": s_iii_years,
            "S_iii_bar_by_year": {y: round((inc_share[y] or 0.0) * S_III_TOLERANCE, 4)
                                  for y in YEARS},
            "admissible": bool(s_i and s_ii and s_iii),
        }
    adm = [n for n, v in rec["admissibility"].items() if v["admissible"]]
    if adm:
        pick = max(
            adm,
            key=lambda n: sum(rec["assertion"][n][y]["raw_assertion_twh"] for y in YEARS),
        )
    else:
        pick = None
    rec["selected"] = pick
    rec["verdict"] = (
        f"SELECTED {pick}" if pick else
        "REFUSED — no candidate is admissible; escalate without solving"
    )
    if pick:
        rec["selected_levels"] = {str(c): round(v, 2) for c, v in sorted(cands[pick].items())}
        rec["materiality_reported"] = {
            y: {
                "incumbent_raw_twh": rec["assertion"]["C0"][y]["raw_assertion_twh"],
                "selected_raw_twh": rec["assertion"][pick][y]["raw_assertion_twh"],
                "increment_twh": round(
                    rec["assertion"][pick][y]["raw_assertion_twh"]
                    - rec["assertion"]["C0"][y]["raw_assertion_twh"],
                    4,
                ),
            }
            for y in YEARS
        }
        rec["materiality_reported"]["cc24_requirement_twh"] = CC24_REQUIREMENT
        rec["materiality_reported"]["note"] = (
            "REPORTED AFTER SELECTION, never a selector (rule 1). A raw "
            "assertion is an upper bound on the class increment: the LP "
            "re-optimizes and displaced classes give energy back."
        )
    return rec


def satisfiability() -> None:
    """Verify the machinery — NO candidate level or assertion is computed."""
    print("SATISFIABILITY (no candidate level or assertion computed)")
    assert INCUMBENT_CSV.exists(), INCUMBENT_CSV
    inc = incumbent_levels()
    print(f"  incumbent artifact: {len(inc)} ST_GAS rows")
    assert inc, "premise: the incumbent level artifact has ST_GAS rows"
    orig = fleet_pkg.thermal_tranche_p25_measured_level
    base = orig(ISO)
    keys = [k for k in base if k[1] == GROUP]
    print(f"  runtime accessor resolves {len(keys)} ST_GAS level key(s)")
    assert keys, "premise: the runtime accessor is reachable and populated"
    probe_key = keys[0]

    def _shim(iso: str):  # noqa: ANN202
        d = dict(orig(iso))
        d[probe_key] = d[probe_key]
        return d

    fleet_pkg.thermal_tranche_p25_measured_level = _shim
    try:
        f, fa, _ = ph0.build_run_year_fleet(2024)
        fl = ph0.plant_floor_series(f, fa)
        print(f"  patched-accessor rebuild OK; floored plants {sorted(fl)}")
        assert fl, "premise: the swapped accessor still builds the floor"
    finally:
        fleet_pkg.thermal_tranche_p25_measured_level = orig
    print("SATISFIABLE — the level swap is reachable and single-delta.")


def main() -> None:
    ap = argparse.ArgumentParser(description="miso-198 level selection")
    ap.add_argument("--satisfiability", action="store_true")
    ap.add_argument("--emit", action="store_true")
    args = ap.parse_args()
    if args.satisfiability:
        satisfiability()
        return
    rec = select()
    OUT.write_text(json.dumps(rec, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(_REPO)}")
    print("\n== assertion (raw, TWh) ==")
    for name in CANDIDATE_SPECS:
        a = rec["assertion"][name]
        print(
            f"  {name}: " + "  ".join(
                f"{y} raw {a[y]['raw_assertion_twh']:6.3f} over {a[y]['over_assertion_twh']:5.3f} "
                f"({a[y]['over_share']:.3f})" for y in YEARS
            )
        )
    print("\n== admissibility ==")
    for name, v in rec["admissibility"].items():
        print(
            f"  {name}: S-i {v['S_i_conduct_grounded']!s:5s} S-ii {v['S_ii_non_pinning']!s:5s} "
            f"S-iii {v['S_iii_no_worse_over_assertion']!s:5s} -> {'ADMISSIBLE' if v['admissible'] else 'no'}"
        )
    print(f"\n{rec['verdict']}")
    if rec.get("selected") and args.emit:
        with EMIT.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["plant_code", "plant_group", "oom_level_mw"])
            for c, v in sorted(rec["selected_levels"].items(), key=lambda kv: int(kv[0])):
                w.writerow([c, GROUP, v])
        print(f"emitted {EMIT.relative_to(_REPO)}")


if __name__ == "__main__":
    main()
