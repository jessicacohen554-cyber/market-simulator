"""miso-175 scope 1 — INDEPENDENT re-verification of the seam-envelope hour-key rotation.

READ-ONLY. **No LP is solved and nothing here re-enters a solve** (rule 13
``[R-MEASURED]``). The miso-175 charter orders the miso-174 §4 finding
re-verified before anything is built ("do not take miso-174 on trust"):

  V-1  the hour-key SOLVE — sweep shift ∈ [-3, +3] applied to the DIBA file's
       ``local_time`` and correlate the DIBA-sum net import against the
       independently-keyed BALANCE ``TI`` series (``MISO_region.parquet``,
       ``period`` UTC → CST). miso-174 solved shift = −1 h at r = 1.0000 in
       2023 AND 2025 (2024 r = 0.8286, the disclosed EIA-930 internal
       inconsistency). The verification REPRODUCES the whole sweep, not just
       the winner.
  V-2  the ROTATION IDENTITY — the production envelope
       (``measured_seam_import_envelope``, raw hour-ENDING key) vs the
       correctly keyed (−1 h) p90 (month × hour-of-day) table evaluated at
       roll 0 and at roll +1 (model hour h reads the aligned table's hod
       (h−1) % 24). miso-174: PJM mean |Δ| 241 MW at roll 0 → 2.9 / 3.2 MW
       (2023 / 2025) at roll +1, annual mean cap level unchanged
       (6.232 vs 6.231 GW) — an exact rotation, not a level error.
  V-3  the MISO-ONLY gate (rule 25) — ``measured_seam_import_envelope``
       returns ``None`` for every other registered ISO (the
       ``{"MISO": MISO_SEAM_DIBA}.get(iso)`` gate), so no other ISO's bundle
       can move under any fix to this function.
  V-4  record CROSS-CHECK — the re-derived roll-0 mean |Δ| per seam matches
       the COMMITTED ``_miso174_import_limit_precheck.json``
       ``reported_envelope_rotation`` numbers.

Both directions (import + export) are measured in V-2: the armed keeper
carries ``miso_seam_flow_limit`` AND ``miso_seam_export_limit``, and both
route through the same mis-keyed bucketing.

Run:  python3 scripts/probes/_miso175_rotation_verify.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.config.constants import MISO_SEAM_FLOW_PERCENTILE  # noqa: E402
from market_sim.config.interchange_config import MISO_SEAM_DIBA  # noqa: E402
from market_sim.data.eia930 import measured_seam_import_envelope  # noqa: E402
from market_sim.data.fleet import _hour_to_month_index  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _miso174_seam_overimport_decomposition import (  # noqa: E402
    HOURS,
    YEARS,
    diba_wide,
    e930_balance,
)

CAL = ROOT / "results" / "calibration"
E930_DIBA = ROOT / "data" / "raw" / "eia-930-interchange" / "MISO interchange hourly.parquet"
MISO174_RECORD = CAL / "_miso174_import_limit_precheck.json"
OUT = CAL / "_miso175_rotation_verify.json"

OTHER_ISOS = ("ERCOT", "CAISO", "PJM", "NYISO", "NEISO")


def bucket_table(year: int, pct: float, shift_h: int, direction: str) -> dict[str, np.ndarray]:
    """Per-seam (12 × 24) percentile table of measured net flow, keyed at ``shift_h``.

    The same construction as the production loader's bucketing — including the
    month-row / global NaN fills and the year filter applied AFTER the shift —
    but returning the table itself so V-2 can evaluate it at any hod roll.
    ``direction="export"`` negates the net import exactly as the production
    loader does before taking the percentile.
    """
    diba_to_seam = {d: s for s, dibas in MISO_SEAM_DIBA.items() for d in dibas}
    frame = pd.read_parquet(E930_DIBA)
    local = pd.DatetimeIndex(frame["local_time"]) + pd.Timedelta(hours=shift_h)
    keep = local.year == year
    frame, local = frame[keep], local[keep]
    seam = frame["diba"].astype(str).map(diba_to_seam)
    work = pd.DataFrame(
        {"seam": seam.to_numpy(), "month": local.month.to_numpy(),
         "hod": local.hour.to_numpy(), "ts": local.to_numpy(),
         "mw": pd.to_numeric(frame["mw"], errors="coerce").to_numpy()}
    ).dropna(subset=["seam", "mw"])
    per_ts = work.groupby(["seam", "ts", "month", "hod"], observed=True)["mw"].sum()
    per_ts = (-per_ts).reset_index(name="net_import")
    out: dict[str, np.ndarray] = {}
    for name in MISO_SEAM_DIBA:
        sub = per_ts[per_ts["seam"] == name]
        if sub.empty:
            continue
        tab = np.full((12, 24), np.nan)
        for (m, h), g in sub.groupby(["month", "hod"], observed=True):
            vals = g["net_import"].to_numpy()
            if direction == "export":
                vals = -vals
            tab[m - 1, h] = np.percentile(vals, pct)
        for m in range(12):
            row = tab[m]
            if not np.all(np.isnan(row)):
                tab[m] = np.where(np.isnan(row), np.nanmax(row), row)
        if np.any(np.isnan(tab)):
            tab = np.where(np.isnan(tab), np.nanmax(tab), tab)
        out[name] = tab
    return out


def main() -> None:
    """Run V-1..V-4, write the JSON record, print verdicts, exit non-zero on refutation."""
    rec: dict = {"session": "miso-175", "charter_expectations": {
        "V1_shift": -1, "V1_r_2023_2025": 1.0, "V1_r_2024": 0.8286,
        "V2_pjm_roll0_mean_mw": 241.0, "V2_pjm_roll1_mean_mw": (2.9, 3.2),
    }}
    failures: list[str] = []

    # ---------------- V-1 : the hour-key solve ----------------
    v1: dict = {}
    per_shift_r: dict[int, list[float]] = {}
    for shift in range(-3, 4):
        rs = []
        for y in YEARS:
            w = diba_wide(y, shift)
            tot = w.sum(axis=1, min_count=1).to_numpy()
            bal = e930_balance(y)
            ref = np.full(HOURS, np.nan)
            n = min(len(bal), HOURS)
            ref[:n] = -bal["TI"].to_numpy()[:n]
            ok = np.isfinite(tot) & np.isfinite(ref)
            rs.append(float(np.corrcoef(tot[ok], ref[ok])[0, 1]) if ok.sum() > 1000 else float("nan"))
        per_shift_r[shift] = rs
        v1[str(shift)] = {"per_year_r": rs, "mean_r": float(np.nanmean(rs))}
    best = max(per_shift_r, key=lambda s: np.nanmean(per_shift_r[s]))
    v1["solved_shift_h"] = best
    rec["v1_alignment"] = v1
    r23, r24, r25 = per_shift_r[-1]
    if best != -1:
        failures.append(f"V-1: solved shift {best:+d} != -1")
    if not (r23 > 0.9999 and r25 > 0.9999):
        failures.append(f"V-1: r at -1h = {r23:.4f}/{r25:.4f}, expected 1.0000 in 2023/2025")

    # ---------------- V-2 : the rotation identity ----------------
    v2: dict = {}
    pct = float(MISO_SEAM_FLOW_PERCENTILE)
    rm = _hour_to_month_index(HOURS)  # 0-based month per model hour
    rh = np.arange(HOURS) % 24
    for direction in ("import", "export"):
        v2[direction] = {}
        for y in YEARS:
            prod = measured_seam_import_envelope("MISO", y, HOURS, None, direction) or {}
            tabs = bucket_table(y, pct, -1, direction)
            row: dict = {}
            for seam, cap in prod.items():
                if seam not in tabs:
                    continue
                tab = tabs[seam]
                roll0 = np.clip(tab[rm, rh], 0.0, None)
                roll1 = np.clip(tab[rm, (rh - 1) % 24], 0.0, None)
                row[seam] = {
                    "prod_annual_mean_gw": float(np.mean(cap)) / 1000,
                    "aligned_annual_mean_gw": float(np.mean(roll0)) / 1000,
                    "roll0_mean_abs_mw": float(np.mean(np.abs(cap - roll0))),
                    "roll0_max_abs_mw": float(np.max(np.abs(cap - roll0))),
                    "roll1_mean_abs_mw": float(np.mean(np.abs(cap - roll1))),
                    "roll1_max_abs_mw": float(np.max(np.abs(cap - roll1))),
                }
            v2[direction][str(y)] = row
    rec["v2_rotation"] = v2
    p23 = v2["import"]["2023"].get("PJM", {})
    p25 = v2["import"]["2025"].get("PJM", {})
    if not (p23 and p25):
        failures.append("V-2: PJM seam missing from envelopes")
    else:
        if not (p23["roll1_mean_abs_mw"] < 25.0 and p25["roll1_mean_abs_mw"] < 25.0):
            failures.append(
                f"V-2: roll+1 does NOT reproduce production (PJM mean|Δ| "
                f"{p23['roll1_mean_abs_mw']:.1f} / {p25['roll1_mean_abs_mw']:.1f} MW)"
            )
        if not (p23["roll0_mean_abs_mw"] > 10 * p23["roll1_mean_abs_mw"]):
            failures.append("V-2: roll 0 not an order of magnitude worse than roll +1")

    # ---------------- V-3 : the MISO-only gate ----------------
    v3 = {}
    for iso in OTHER_ISOS:
        env = measured_seam_import_envelope(iso, 2024, HOURS)
        v3[iso] = "None" if env is None else f"NON-NONE ({sorted(env)})"
        if env is not None:
            failures.append(f"V-3: {iso} returns a non-None envelope — NOT MISO-only")
    rec["v3_miso_only"] = v3

    # ---------------- V-4 : committed-record cross-check ----------------
    v4: dict = {}
    if MISO174_RECORD.exists():
        committed = json.loads(MISO174_RECORD.read_text())["reported_envelope_rotation"]
        for y in YEARS:
            for seam, mine in v2["import"][str(y)].items():
                theirs = committed.get(str(y), {}).get(seam)
                if theirs is None:
                    continue
                d = abs(mine["roll0_mean_abs_mw"] - theirs["mean_abs_diff_mw"])
                v4[f"{y}/{seam}"] = {
                    "rederived_roll0_mean_mw": mine["roll0_mean_abs_mw"],
                    "committed_mean_abs_diff_mw": theirs["mean_abs_diff_mw"],
                    "abs_delta_mw": d,
                }
                if d > 1.0:
                    failures.append(
                        f"V-4: {y}/{seam} roll-0 mean |Δ| {mine['roll0_mean_abs_mw']:.1f} "
                        f"!= committed {theirs['mean_abs_diff_mw']:.1f}"
                    )
    else:
        failures.append("V-4: committed miso-174 record missing")
    rec["v4_record_crosscheck"] = v4

    rec["failures"] = failures
    rec["verdict"] = "ROTATION CONFIRMED" if not failures else "REFUTED / CHECK FAILURES"
    OUT.write_text(json.dumps(rec, indent=1))
    print(f"wrote {OUT}\n")

    print("== V-1: hour-key solve (r vs BALANCE -TI, per shift) ==")
    for shift in range(-3, 4):
        rs = per_shift_r[shift]
        mark = " <== SOLVED" if shift == best else ""
        print(f"  {shift:+d} h  r = " + " / ".join(f"{r:.4f}" for r in rs) + mark)

    print("\n== V-2: rotation identity (production vs -1h-keyed table) ==")
    for direction in ("import", "export"):
        for y in YEARS:
            for seam, r in v2[direction][str(y)].items():
                print(f"  {direction:6s} {y} {seam:9s} roll0 mean|Δ| {r['roll0_mean_abs_mw']:7.1f} MW"
                      f" (max {r['roll0_max_abs_mw']:6.0f})   roll+1 {r['roll1_mean_abs_mw']:5.1f} MW"
                      f" (max {r['roll1_max_abs_mw']:5.0f})   level {r['prod_annual_mean_gw']:.3f}"
                      f" vs {r['aligned_annual_mean_gw']:.3f} GW")

    print("\n== V-3: MISO-only gate ==")
    for iso, res in v3.items():
        print(f"  {iso:6s} -> {res}")

    print(f"\nVERDICT: {rec['verdict']}")
    for f in failures:
        print(f"  FAIL: {f}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
