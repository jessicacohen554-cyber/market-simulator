"""SPP-57b PRECOMMIT §3.3: the two link ratings under the RE-DECLARED sets — N<->OK from the
`n_s_corridor` group ALONE, OK<->S from the `sps_tie` group ALONE; `oklahoma_internal` (and the CSWS-only
`other` rows) EXCLUDED from both. Reads SPP-57's committed per-constituent tables (hours, psi, t, L_f, T*)
and LOYO psi columns verbatim (rule 23: no regression re-fitted, no limit re-read); prints per link and
per direction n, pooled hours, the binding-hours-weighted median -> nearest-100 TTC, weighted p25/p75,
LOYO, and R1-R4 at the measured w_OK. Writes tstar_n_ok_57b.csv / tstar_ok_s_57b.csv beside this file.

usage: uv run python docs/handoffs/spp57b/aggregate_ttc_57b.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
S57 = HERE.parent / "spp57"
pd.set_option("display.width", 300)

# PRECOMMIT-spp-57b §3.4 residual-blind bounds at the measured w_OK (2023 min loads, EIA-860 2025 ER)
B_PLAUS = {"SPP-North": 23_300.0, "SPP-Oklahoma": 11_085.0, "SPP-South": 3_481.0}
B_HARD = {"SPP-North": 37_400.0, "SPP-Oklahoma": 24_383.0, "SPP-South": 13_119.0}


def wq(frame: pd.DataFrame, q: float) -> float:
    """Binding-hours-weighted quantile of T_star (SPP-53 §2.1 / spp57/aggregate_ttc.py::wq)."""
    frame = frame.sort_values("T_star")
    w = frame.hours.values
    cw = np.cumsum(w) / w.sum()
    return float(frame.T_star.values[np.searchsorted(cw, q)])


LINKS = (
    ("N<->OK (+ = N->OK)", "tstar_n_ok.csv", "psi_n_ok.csv", ("n_s_corridor",), "n_ok", ("SPP-North", "SPP-Oklahoma")),
    ("OK<->S (+ = OK->S)", "tstar_ok_s.csv", "psi_ok_s.csv", ("sps_tie",), "ok_s", ("SPP-Oklahoma", "SPP-South")),
)

for label, tfile, pfile, groups, tag, zones in LINKS:
    T = pd.read_csv(S57 / tfile)
    P = pd.read_csv(S57 / pfile).set_index("Constraint Name")
    excluded = T[~T.group.isin(groups)]
    both = excluded[(excluded.t.abs() >= 2.0)]
    M = T[T.group.isin(groups) & (T.hours >= 263)].copy()
    M.to_csv(HERE / f"tstar_{tag}_57b.csv", index=False)
    print(f"\n================ {label}: set = {groups}; {len(M)} members >= 263 h "
          f"(excluded groups: {sorted(excluded.group.unique().tolist())}, {len(excluded)} rows, "
          f"{len(both)} of them |t| >= 2 on this spread)")
    print(M[["Constraint Name", "Monitored Facility", "group", "hours", "psi", "t", "fwd", "rev", "L_f", "T_star"]]
          .to_string(index=False, max_colwidth=30))
    F = M[M.fwd & M.T_star.notna()]
    R = M[M.rev & M.T_star.notna()]
    hf, hr = int(F.hours.sum()), int(R.hours.sum())
    named = "forward" if hf >= hr else "reverse"
    ttc = None
    for lab, I in (("forward", F), ("reverse", R)):
        if len(I) == 0:
            print(f"  {lab}: no identified constituent with an L_f (R1 FAILS in this direction: 0 < 3)")
            continue
        med, p25, p75 = wq(I, 0.5), wq(I, 0.25), wq(I, 0.75)
        rnd = round(med, -2)
        print(f"  {lab}: n={len(I)} hours={int(I.hours.sum())} weighted median T* = {med:,.0f} -> {rnd:,.0f} MW"
              f" | p25 {p25:,.0f} p75 {p75:,.0f} ratio {p75 / max(p25, 1e-9):.2f}"
              f" | unweighted median {I.T_star.median():,.0f} min {I.T_star.min():,.0f} max {I.T_star.max():,.0f}")
        for yr in (2023, 2024, 2025):
            ps = P[f"psi_drop{yr}"].reindex(I["Constraint Name"]).abs().values
            J = I.assign(T_star=I.L_f.values / ps)
            J = J[np.isfinite(J.T_star) & (J.T_star > 0)]
            print(f"     LOYO drop {yr}: n={len(J)} weighted median T* = {wq(J, 0.5):,.0f}")
        if lab == named:
            ttc = rnd
            r1 = len(I) >= 3
            r4 = (p75 / max(p25, 1e-9)) <= 10.0
    print(f"  NAMED DIRECTION = {named} (forward {hf} h vs reverse {hr} h)")
    bp = max(B_PLAUS[z] for z in zones)
    bh = max(B_HARD[z] for z in zones)
    print(f"  TTC (named) = {ttc:,.0f} MW | R1 (>=3 identified w/ L_f) {'pass' if r1 else 'FAIL'}"
          f" | R2 (TTC < max B_plaus {bp:,.0f}) {'pass' if ttc < bp else 'FAIL'}"
          f" | R3 (TTC < max B_hard {bh:,.0f}) {'pass' if ttc < bh else 'FAIL'}"
          f" | R4 (p75/p25 <= 10) {'pass' if r4 else 'FAIL'}")
