"""pjm-147 K2 — the control does NOT reproduce the keeper, and this locates why.

PREREG-pjm147 section 4 K2 requires the same-HEAD zero-delta control to
reproduce the committed keeper ``2026-07-31-pjm-143b-hy-level`` to 0.0 MW on
every class-hour. It does not. This probe is the mandated diagnosis, run
BEFORE the candidate arm is scored.

Method — three independent lines, none of which assumes the answer:

1. **Magnitude.** Keeper vs control, per year: max |delta class-hour MW| and the
   load-weighted annual price, from the committed ``hourly/`` sidecars.
2. **Attribution by class.** Which class carries the drift. A repricing of one
   class shows up as that class moving far more than any other.
3. **Attribution by commit.** The solve-relevant diff over the window in which
   the drift entered — from ``7cc95fa`` (pjm-146's control, which DID reproduce
   the keeper at 0.0 MW, FINDING-pjm146 section 3) to this HEAD. A single
   changed solve input in that window, matching the class signature, is the
   cause.

The finding this produces is SESSION-INDEPENDENT: it is a property of the
keeper at HEAD, not of this lever, and it would affect any PJM session solving
at this HEAD. It does not invalidate the A/B, because both arms solve at the
same HEAD and the arm-minus-control delta still isolates the single flag (the
neiso-69 / caiso-146 same-HEAD-drift precedent).

CORRECTION (2026-08-03, on reading ``origin/main`` after this probe first ran).
An earlier revision of this docstring, and the commit message at ``c19a385``,
framed the changed input as an UNCHARTERED cross-ISO change made in a CAISO
session against the matrix's own warning. **That framing is wrong and is
withdrawn.** The change is caiso-158 executing
``PREREG-caiso156-ct-heat-rate-meter-screen-2026-08-02.md`` — it HAS its own
charter, exactly as the matrix demanded; it pre-registered PJM's own delta
(cap-weighted applied map 11.5817 -> 11.6511, **+0.0693**) and reproduced it to
4 dp; and it DECLARED the PJM scope cut on the record (its §5: PJM's arm A was
not launched because PJM is the largest LP in the set, ~15.5 GB peak RSS
against a 15 GB box **with no swap available**, and carried the smallest
predicted effect). There is no governance breach. What remains true is narrower
and is what this probe actually measures: PJM's keeper was never RE-GATED
against the corrected artifact, so its committed dispatch no longer reproduces
at HEAD.

That makes this probe's keeper-vs-control comparison the PJM leg caiso-158
deferred — its follow-up item 2, which asked for "a successor session on a
larger box ... or the ``--years`` + ``--reuse-solved`` per-year invocation
chain". This session has 12 GB of swap and used exactly that chain. The
comparison is a clean single-delta measurement of the meter screen for PJM:
pjm-146's control reproduced this keeper at 0.0 MW from ``7cc95fa``, proving
everything before it inert, and over ``7cc95fa..HEAD`` the only PJM-solve-
relevant data change is the CT artifact.

    PYTHONPATH=.:src uv run python scripts/probes/_pjm147_k2_drift.py
"""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/pjm143_hy_level_B"
CONTROL = REPO / "results/calibration/pjm147_control_A"
OUT_PATH = REPO / "results/calibration/_pjm147_k2_drift.json"

YEARS = (2023, 2024, 2025)
#: pjm-146's control HEAD — it reproduced this keeper to 0.0 MW, so any drift
#: visible now entered after it (FINDING-pjm146-rggi-allowance-2026-08-02 §3).
PJM146_CONTROL_SHA = "7cc95fa"
CT_ARTIFACT = "data/raw/_processed-legacy/campd_ct_heat_rates_PJM.csv"
EXTERNAL_PREFIX = "PJM_external"


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return frame[frame["pass"] == "P1"] if "pass" in frame.columns else frame


def _lw_price(bundle: Path, year: int) -> float:
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    if "pass" in frame.columns:
        frame = frame[frame["pass"] == "P1"]
    pj = frame[~frame["zone"].astype(str).str.startswith(EXTERNAL_PREFIX)]
    return float((pj["price"] * pj["demand"]).sum() / pj["demand"].sum())


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True
    ).stdout


def main() -> int:
    out: dict = {
        "gate": "K2 strict byte (PREREG-pjm147 §4)",
        "correction": (
            "The changed CT artifact is caiso-158 executing PREREG-caiso156, a "
            "CHARTERED input correction that pre-registered PJM's own +0.0693 "
            "delta and declared the PJM scope cut (its §5). No governance "
            "breach; an earlier framing at commit c19a385 said otherwise and is "
            "withdrawn. What stands: PJM's keeper was never re-gated against the "
            "corrected artifact, and this comparison is the PJM leg caiso-158 "
            "deferred as its follow-up item 2."
        ),
        "keeper": str(KEEPER.relative_to(REPO)),
        "control": str(CONTROL.relative_to(REPO)),
        "keeper_git_sha": json.loads((KEEPER / "run_config.json").read_text()).get("git_sha"),
        "control_git_sha": json.loads((CONTROL / "run_config.json").read_text()).get("git_sha"),
        "years": {},
    }

    print("=" * 78)
    print("1. MAGNITUDE — keeper vs same-HEAD zero-delta control")
    print("=" * 78)
    passed = True
    for year in YEARS:
        k = _class_hourly(KEEPER, year).set_index(["klass", "hour"])["mw"].sort_index()
        c = _class_hourly(CONTROL, year).set_index(["klass", "hour"])["mw"].sort_index()
        kj, cj = k.align(c, join="outer", fill_value=0.0)
        diff = (kj - cj).abs()
        lw_k, lw_c = _lw_price(KEEPER, year), _lw_price(CONTROL, year)
        by_class = {
            str(kk): round(float(v), 4)
            for kk, v in diff.groupby(level="klass").max().items()
            if float(v) > 1e-9
        }
        twh = {
            str(kk): round(float(v) / 1e6, 4)
            for kk, v in (cj - kj).groupby(level="klass").sum().items()
            if abs(float(v)) > 5e3
        }
        passed &= float(diff.max()) <= 1e-9
        out["years"][str(year)] = {
            "max_abs_diff_mw": round(float(diff.max()), 6),
            "max_by_class_mw": by_class,
            "class_twh_control_minus_keeper": twh,
            "lw_price_keeper": round(lw_k, 4),
            "lw_price_control": round(lw_c, 4),
            "lw_price_delta": round(lw_c - lw_k, 6),
        }
        print(
            f"  {year}  max|dMW| {float(diff.max()):10.3f}   "
            f"lw ${lw_k:.4f} -> ${lw_c:.4f}  ({lw_c - lw_k:+.6f})"
        )
    out["k2_strict_byte_passed"] = bool(passed)

    print()
    print("=" * 78)
    print("2. ATTRIBUTION BY CLASS — control minus keeper, TWh")
    print("=" * 78)
    for year in YEARS:
        rec = out["years"][str(year)]["class_twh_control_minus_keeper"]
        ranked = sorted(rec.items(), key=lambda kv: -abs(kv[1]))
        print(f"  {year}  " + "  ".join(f"{k}={v:+.3f}" for k, v in ranked[:6]))

    print()
    print("=" * 78)
    print(f"3. ATTRIBUTION BY COMMIT — solve inputs changed since {PJM146_CONTROL_SHA}")
    print("=" * 78)
    data_diff = _git("diff", "--stat", PJM146_CONTROL_SHA, "HEAD", "--", "data/").strip()
    print(data_diff or "  (no data/ changes)")
    out["data_diff_since_pjm146_control"] = data_diff.splitlines()

    log = _git("log", "--oneline", f"{PJM146_CONTROL_SHA}..HEAD", "--", CT_ARTIFACT).strip()
    out["ct_artifact_commits"] = log.splitlines()
    print(f"\n  commits touching {CT_ARTIFACT}:")
    print("    " + (log.replace("\n", "\n    ") if log else "(none)"))

    print()
    print("=" * 78)
    print("4. THE CHANGED INPUT, QUANTIFIED")
    print("=" * 78)
    old = pd.read_csv(
        io.StringIO(_git("show", f"{PJM146_CONTROL_SHA}:{CT_ARTIFACT}"))
    )
    new = pd.read_csv(REPO / CT_ARTIFACT)
    m = old.merge(new, on="plant_code", suffixes=("_o", "_n"))
    ok_n = m["flag_n"] == "ok"
    moved = m[((m["heat_rate_n"] - m["heat_rate_o"]).abs() > 1e-6) & ok_n]
    w = moved["class_capacity_mw_n"].to_numpy(float)
    capw_o = float(np.average(moved["heat_rate_o"], weights=w))
    capw_n = float(np.average(moved["heat_rate_n"], weights=w))
    transitions = {
        f"{a}->{b}": int(n)
        for (a, b), n in m.groupby(["flag_o", "flag_n"]).size().items()
    }
    out["ct_artifact_delta"] = {
        "applied_rows_old": int((m["flag_o"] == "ok").sum()),
        "applied_rows_new": int(ok_n.sum()),
        "rows_with_changed_rate": int(len(moved)),
        "changed_capacity_mw": round(float(w.sum()), 1),
        "capw_heat_rate_old": round(capw_o, 4),
        "capw_heat_rate_new": round(capw_n, 4),
        "capw_pct_change": round(100.0 * (capw_n / capw_o - 1.0), 4),
        "flag_transitions": transitions,
    }
    print(
        f"  applied rows {int((m['flag_o'] == 'ok').sum())} -> {int(ok_n.sum())};  "
        f"{len(moved)} rows / {w.sum():,.1f} MW changed rate"
    )
    print(
        f"  cap-wt measured HR {capw_o:.4f} -> {capw_n:.4f} "
        f"({100 * (capw_n / capw_o - 1):+.2f} %)   flag transitions {transitions}"
    )

    OUT_PATH.write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nwrote {OUT_PATH.relative_to(REPO)}")
    print(f"  K2 strict-byte: {'PASS' if passed else 'FAIL'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
