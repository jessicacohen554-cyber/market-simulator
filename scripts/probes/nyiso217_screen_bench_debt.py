#!/usr/bin/env python3
"""nyiso-217 — does ``_screen_fuel_spike_columns`` move any NYISO SCORED quantity?

Pays the C1/C4 benchmark debt nyiso-215 §7 flagged and nyiso-216 §1 passed
forward. **Zero LP**: every number is either a live EIA-930 loader call with the
screen live vs. bypassed (P2/P5), an execution of the committed scorer (P1), or
exact arithmetic on the committed bench part (P3/P4).

The five gates are pre-registered in
``results/calibration/PREREG-nyiso217-eia930-fuel-spike-screen-bench-debt.md``
and are NOT restated here.

Usage::

    uv run python scripts/probes/nyiso217_screen_bench_debt.py
"""

from __future__ import annotations

import gzip
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

YEARS = (2022, 2023, 2024, 2025)
ISO = "NYISO"
KEEPER = "2026-09-07-nyiso-213-summer-seam"
BENCH = ROOT / "frontend/data/backcast/bench/NYISO"
OUT = ROOT / "results/calibration/_nyiso217_screen_bench_debt.json"

# SPP-41's own declared NYISO effect, from the _screen_fuel_spike_columns
# docstring -- the set P2 tests against (PREREG C-4).
SPP41_DECLARED = {
    (2024, "other"): (3.3846, 3.3197, [6759]),
}


def _bench(year: int) -> dict:
    return json.load(gzip.open(BENCH / f"{year}.json.gz"))["bench"]


# ---------------------------------------------------------------------------
# P1 -- provenance, by EXECUTION: does the scorer reach the live loader at all?
# ---------------------------------------------------------------------------
_P1_CHILD = r"""
import json, sys
sys.path.insert(0, {root!r})
import market_sim.data.eia930.actuals as A

if {patch!r}:
    _orig = A._screen_fuel_spike_columns
    A._screen_fuel_spike_columns = lambda frame, *, ba_code, year: frame
    # control assertion: the patch must actually be in force
    assert A._screen_fuel_spike_columns is not _orig, "monkey-patch not in force"
    import pandas as pd
    _f = pd.DataFrame({{"NG: X": [1.0, 1e9]}})
    assert A._screen_fuel_spike_columns(_f, ba_code="X", year=2024) is _f, (
        "patched symbol is not the identity"
    )

import runpy
sys.argv = ["calibration_verdict.py", "--run-id", {keeper!r}, "--json"]
try:
    runpy.run_path({verdict!r}, run_name="__main__")
except SystemExit:
    pass
"""


def run_p1() -> dict:
    verdict = str(ROOT / "scripts/calibration_verdict.py")
    outs = {}
    for label, patch in (("unpatched", False), ("patched", True)):
        src = _P1_CHILD.format(
            root=str(ROOT), patch=patch, keeper=KEEPER, verdict=verdict
        )
        p = subprocess.run(
            [sys.executable, "-c", src], capture_output=True, text=True, cwd=str(ROOT)
        )
        outs[label] = {"rc": p.returncode, "stdout": p.stdout, "stderr": p.stderr[-4000:]}
    a, b = outs["unpatched"], outs["patched"]
    identical = a["stdout"] == b["stdout"] and a["rc"] == b["rc"]
    return {
        "identical": bool(identical),
        "rc_unpatched": a["rc"],
        "rc_patched": b["rc"],
        "stdout_len": len(a["stdout"]),
        "stdout_len_patched": len(b["stdout"]),
        "patch_in_force": "monkey-patch not in force" not in b["stderr"]
        and "patched symbol is not the identity" not in b["stderr"],
        "stderr_tail_patched": b["stderr"][-1200:],
        "stderr_tail_unpatched": a["stderr"][-1200:],
        "determination_excerpt": a["stdout"][:600],
    }


# ---------------------------------------------------------------------------
# P2 / P5(ii) -- the live loader, screen ON vs OFF, per series and per column
# ---------------------------------------------------------------------------
def run_p2() -> dict:
    import market_sim.data.eia930.actuals as A
    from market_sim.data.eia930.frames import _ISO_TO_HOURLY_BA

    orig = A._screen_fuel_spike_columns

    # A recording wrapper: same behaviour, but logs which NG: columns it flags.
    flagged: dict[tuple[int, str], int] = {}

    def _recording(frame, *, ba_code, year):
        out = orig(frame, ba_code=ba_code, year=year)
        if out is not frame:
            for col in frame.columns:
                if not str(col).startswith("NG: "):
                    continue
                a = pd.to_numeric(frame[col], errors="coerce").to_numpy(float)
                b = pd.to_numeric(out[col], errors="coerce").to_numpy(float)
                n = int(np.sum(np.isfinite(a) & ~np.isfinite(b)))
                if n:
                    flagged[(year, str(col))] = n
        return out

    res: dict[str, dict] = {}
    for year in YEARS:
        A._screen_fuel_spike_columns = _recording
        on = A.load_eia_hourly_benchmark(ISO, year)
        A._screen_fuel_spike_columns = lambda frame, *, ba_code, year: frame
        off = A.load_eia_hourly_benchmark(ISO, year)
        A._screen_fuel_spike_columns = orig

        if on is None or off is None:
            res[str(year)] = {"available": False}
            continue
        assert set(on) == set(off), (set(on) ^ set(off))
        rows = {}
        for s in sorted(on):
            a = np.asarray(off[s], dtype=float)  # screen OFF
            b = np.asarray(on[s], dtype=float)  # screen ON
            twh_off = float(np.nansum(a)) / 1e6
            twh_on = float(np.nansum(b)) / 1e6
            dmax = float(np.nanmax(np.abs(b - a))) if a.shape == b.shape else float("nan")
            rows[s] = {
                "twh_screen_off": round(twh_off, 4),
                "twh_screen_on": round(twh_on, 4),
                "delta_twh": round(twh_on - twh_off, 6),
                "max_abs_hour_delta_mw": round(dmax, 3),
                "n_hours_changed": int(np.sum(~np.isclose(a, b, rtol=0, atol=1e-9))),
                "moved": bool(abs(twh_on - twh_off) > 1e-9 or dmax > 1e-9),
            }
        res[str(year)] = {"available": True, "ba": _ISO_TO_HOURLY_BA.get(ISO), "series": rows}

    moved = {
        (int(y), s)
        for y, d in res.items()
        if d.get("available")
        for s, r in d["series"].items()
        if r["moved"]
    }
    return {
        "per_year": res,
        "moved_set": sorted(f"{y}:{s}" for y, s in moved),
        "flagged_columns": {f"{y}:{c}": n for (y, c), n in sorted(flagged.items())},
    }


# ---------------------------------------------------------------------------
# P3 / P4 -- exact arithmetic on the COMMITTED bench part
# ---------------------------------------------------------------------------
def run_p3_p4(p2: dict) -> dict:
    from scripts.lib import benchmark_semantics as bs
    from scripts.render_calibration_html import (
        _COAL_GROUPS,
        _GAS_GROUPS,
        _VINTAGE_RECONCILE_FRAC,
    )

    out: dict[str, dict] = {"_VINTAGE_RECONCILE_FRAC": _VINTAGE_RECONCILE_FRAC}
    for year in YEARS:
        p = BENCH / f"{year}.json.gz"
        if not p.exists():
            out[str(year)] = {"bench_committed": False}
            continue
        b = _bench(year)
        cf = dict(b["classFull"])
        e930 = dict(b["e930"])

        yr = p2["per_year"].get(str(year), {})
        d_other = 0.0
        if yr.get("available") and "other" in yr["series"]:
            d_other = float(yr["series"]["other"]["delta_twh"])

        x_committed = float(e930.get("other", 0.0))
        x_screened = x_committed + d_other

        def defl(x: float) -> float:
            return bs.gas_foldin_deflation(cf, {**e930, "other": x}, ISO)

        d_c, d_s = defl(x_committed), defl(x_screened)
        model_other_bio = float(cf.get("OTHER", 0.0)) + float(cf.get("biomass", 0.0))
        tgt_c = float(e930.get("gas", 0.0)) + float(e930.get("coal", 0.0)) - d_c
        tgt_s = float(e930.get("gas", 0.0)) + float(e930.get("coal", 0.0)) - d_s

        present = [g for g in (*_GAS_GROUPS, *_COAL_GROUPS) if g in cf]
        cur_post = sum(float(cf[g]) for g in present)
        # DETERMINING WHETHER THE RECONCILE FIRED, correctly.
        #
        # The PREREG's step 3 claimed the two tests below are "mutually
        # exclusive and jointly exhaustive given the code". THAT IS WRONG and
        # is corrected here rather than restated: firing forces
        # ``post == _tgt``, and ``_tgt`` is trivially inside the band around
        # itself, so ``in_band`` evaluated on the POST sum is True whenever the
        # reconcile fired. Only one direction is sound:
        #
        #   post != _tgt  =>  provably DID NOT fire (firing forces equality),
        #                     and then post == pre, so the band test on post is
        #                     the band test on pre and is meaningful.
        #   post == _tgt  =>  fired, OR did not fire and pre coincidentally
        #                     equalled _tgt. The committed part cannot separate
        #                     these: pre-reconcile classFull is not recoverable
        #                     without the bundle's inputs, which the slim keeper
        #                     bundle does not carry. Reported as UNDETERMINED.
        did_not_fire = abs(cur_post - tgt_c) > 1e-3
        fired_or_on_target = not did_not_fire
        # Meaningful only when the reconcile provably did not fire.
        in_band_pre = (
            _VINTAGE_RECONCILE_FRAC * tgt_c <= cur_post <= tgt_c / _VINTAGE_RECONCILE_FRAC
        )
        # How far the (pre == post) fossil total sits from the nearer band edge,
        # i.e. how much room there is before the reconcile would start firing.
        # Meaningful only in the did-not-fire case.
        lo, hi = _VINTAGE_RECONCILE_FRAC * tgt_c, tgt_c / _VINTAGE_RECONCILE_FRAC
        band_headroom = min(cur_post - lo, hi - cur_post) if did_not_fire else None
        # Conservative for the sensitivity question: treat "undetermined" as
        # firing, because that is the case in which classFull WOULD move.
        fired = fired_or_on_target

        scale = (tgt_s / tgt_c) if (fired and tgt_c > 0) else 1.0
        per_class = {
            g: round(float(cf[g]) * (scale - 1.0), 6) for g in present
        }

        out[str(year)] = {
            "bench_committed": True,
            "e930_other_committed": round(x_committed, 6),
            "e930_other_screened": round(x_screened, 6),
            "delta_other_twh": round(d_other, 6),
            "classFull_OTHER": round(float(cf.get("OTHER", 0.0)), 6),
            "classFull_biomass": round(float(cf.get("biomass", 0.0)), 6),
            "model_other_bio": round(model_other_bio, 6),
            "clamp_headroom_committed_twh": round(x_committed - model_other_bio, 6),
            "clamp_headroom_screened_twh": round(x_screened - model_other_bio, 6),
            "clamp_headroom_tighter_twh": round(
                min(x_committed, x_screened) - model_other_bio, 6
            ),
            "deflation_committed": round(d_c, 6),
            "deflation_screened": round(d_s, 6),
            "deflation_clamped_both": bool(d_c == 0.0 and d_s == 0.0),
            "tgt_committed": round(tgt_c, 6),
            "tgt_screened": round(tgt_s, 6),
            "d_tgt": round(tgt_s - tgt_c, 9),
            "fossil_classfull_sum_committed": round(cur_post, 6),
            "reconcile_provably_did_not_fire": bool(did_not_fire),
            "reconcile_fired_or_on_target_UNDETERMINED": bool(fired_or_on_target),
            "reconcile_fired_conservative": bool(fired),
            "reconcile_pre_in_band": bool(in_band_pre) if did_not_fire else None,
            "reconcile_band_headroom_twh": (
                round(band_headroom, 6) if band_headroom is not None else None
            ),
            "classfull_scale_screened_over_committed": round(scale, 9),
            "per_class_twh_move": per_class,
            "max_abs_per_class_move_twh": round(
                max((abs(v) for v in per_class.values()), default=0.0), 9
            ),
            # P4: C2's gas-family actual subtracts the deflation directly.
            "c2_gas_actual_delta_twh": round(-(d_s - d_c), 9),
            # VRE mirror channel (P3's other writer)
            "vre_mirror_direction": None,  # filled below
            "vre_mirror_moved": bool(
                yr.get("available")
                and any(
                    yr["series"].get(s, {}).get("moved") for s in ("wind", "solar")
                )
            ),
        }
    return out


def run_p5(p2: dict) -> dict:
    from scripts.calibration_verdict import CEMS_GAS_ANCHOR_ISOS, CEMS_GAS_ANCHOR_ONSET

    gas_coal_cols = {
        k: v
        for k, v in p2["flagged_columns"].items()
        if k.split(":", 1)[1] in ("NG: NG", "NG: COL")
    }
    return {
        "nyiso_in_cems_gas_anchor_isos": ISO in CEMS_GAS_ANCHOR_ISOS,
        "cems_gas_anchor_isos": sorted(CEMS_GAS_ANCHOR_ISOS),
        "cems_gas_anchor_onset": {k: v for k, v in sorted(CEMS_GAS_ANCHOR_ONSET.items())},
        "flagged_gas_or_coal_columns": gas_coal_cols,
        "zero_gas_coal_flags": not gas_coal_cols,
    }


def run_vre_profile() -> dict:
    """UN-PRE-REGISTERED, UN-GATED: the delivered VRE profile the LP consumes.

    ``_screen_fuel_spike_columns``'s own docstring names three consumers -- the
    C1/C4 benchmark, the ``calibration_reference.json`` builder, and the model's
    delivered wind/solar profile (``load_eia_hourly_renewable_gen`` ->
    ``renewables._eia_hourly_cf_profile`` -> the LP's wind bound). P2 covers the
    benchmark reader only. This is the third consumer, checked because the
    docstring names it -- NOT a pre-registered gate, and reported as such.
    """
    import market_sim.data.eia930.actuals as A

    orig = A._screen_fuel_spike_columns
    out: dict[str, dict] = {}
    for year in YEARS:
        A._screen_fuel_spike_columns = orig
        on = A.load_eia_hourly_renewable_gen(ISO, year)
        A._screen_fuel_spike_columns = lambda frame, *, ba_code, year: frame
        off = A.load_eia_hourly_renewable_gen(ISO, year)
        A._screen_fuel_spike_columns = orig
        if on is None or off is None:
            out[str(year)] = {"available": False}
            continue
        rows = {}
        for k in sorted(set(on) | set(off)):
            a = np.asarray(off[k], dtype=float)
            b = np.asarray(on[k], dtype=float)
            rows[k] = {
                "twh_screen_off": round(float(np.nansum(a)) / 1e6, 4),
                "twh_screen_on": round(float(np.nansum(b)) / 1e6, 4),
                "max_abs_hour_delta_mw": round(float(np.nanmax(np.abs(b - a))), 9),
                "n_hours_changed": int(np.sum(~np.isclose(a, b, rtol=0, atol=1e-9))),
            }
        out[str(year)] = {"available": True, "series": rows}
    return out


def run_ungated(p2: dict) -> dict:
    """Committed bench e930 vs what HEAD's loader produces WITH the screen live.

    Mixes the screen's effect with any other engine drift since the part was
    written -- reported, never gated (PREREG §4 'An ungated statistic').
    """
    out = {}
    for year in YEARS:
        p = BENCH / f"{year}.json.gz"
        yr = p2["per_year"].get(str(year), {})
        if not p.exists() or not yr.get("available"):
            out[str(year)] = {"comparable": False}
            continue
        e930 = _bench(year)["e930"]
        rows = {}
        for s, r in yr["series"].items():
            if s not in e930:
                continue
            c = float(e930[s])
            h = float(r["twh_screen_on"])
            rows[s] = {
                "committed": round(c, 4),
                "head_screen_on": round(h, 4),
                "delta": round(h - c, 4),
            }
        out[str(year)] = {"comparable": True, "series": rows}
    return out


def main() -> None:
    rec: dict = {"iso": ISO, "keeper": KEEPER, "years": list(YEARS)}
    print("== P1 provenance (executing the scorer twice) ==", flush=True)
    rec["P1"] = run_p1()
    print(json.dumps(rec["P1"], indent=1)[:1400], flush=True)

    print("\n== P2 live loader, screen ON vs OFF ==", flush=True)
    rec["P2"] = run_p2()
    print("moved_set:", rec["P2"]["moved_set"], flush=True)
    print("flagged_columns:", rec["P2"]["flagged_columns"], flush=True)

    print("\n== P3/P4 exact arithmetic on the committed bench part ==", flush=True)
    rec["P3_P4"] = run_p3_p4(rec["P2"])
    for y in YEARS:
        d = rec["P3_P4"].get(str(y), {})
        if d.get("bench_committed"):
            print(
                f"{y}: d_other={d['delta_other_twh']:+.6f} "
                f"clamp_head(tight)={d['clamp_headroom_tighter_twh']:+.4f} "
                f"defl {d['deflation_committed']:.6f}->{d['deflation_screened']:.6f} "
                f"d_tgt={d['d_tgt']:+.9f} not_fired={d['reconcile_provably_did_not_fire']} "
                f"bandroom={d['reconcile_band_headroom_twh']} "
                f"max_class_move={d['max_abs_per_class_move_twh']:.9f} "
                f"c2_gas_delta={d['c2_gas_actual_delta_twh']:+.9f}",
                flush=True,
            )

    print("\n== P5 C4 immunity ==", flush=True)
    rec["P5"] = run_p5(rec["P2"])
    print(json.dumps(rec["P5"], indent=1), flush=True)

    print("\n== UN-PRE-REGISTERED: delivered VRE profile (LP's wind bound) ==", flush=True)
    rec["vre_profile_unregistered"] = run_vre_profile()
    for y in YEARS:
        d = rec["vre_profile_unregistered"].get(str(y), {})
        if d.get("available"):
            print(
                f"{y}: "
                + ", ".join(
                    f"{k} d_hours={v['n_hours_changed']} maxhr={v['max_abs_hour_delta_mw']}"
                    for k, v in d["series"].items()
                ),
                flush=True,
            )

    print("\n== UNGATED: committed bench e930 vs HEAD screen-on ==", flush=True)
    rec["ungated_committed_vs_head"] = run_ungated(rec["P2"])
    for y in YEARS:
        d = rec["ungated_committed_vs_head"].get(str(y), {})
        if d.get("comparable"):
            worst = max(d["series"].items(), key=lambda kv: abs(kv[1]["delta"]))
            print(f"{y}: worst {worst[0]} {worst[1]}", flush=True)

    OUT.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")
    print(f"\nwrote {OUT.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
