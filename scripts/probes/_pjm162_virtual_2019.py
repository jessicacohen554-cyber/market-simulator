"""pjm-162 Task B(b): the annual net DA virtual position for 2019 — no LP.

WHY. pjm-161 §2 established that the DA-virtual layer's contribution to PJM's C1
`CC_REGULAR` error IS the **annual net Day-Ahead virtual position**: the model
carries one price and one energy balance, so a financial position that closes out
in real time and contributes zero physical energy is served as physical MWh. That
position is a REAL MARKET QUANTITY, and it is not stable across price regimes —
it is ≈ 0 in 2023-2025 (−0.76 / −1.62 / +0.20 TWh at actual DA) and **+12.25 TWh
in 2022**.

**Nobody has measured it for 2019.** That matters for exactly one live decision:
whether PJM's `final` (locked-test) one-shot on 2019 can be spent while the
DA-virtual architecture escalation is open. If 2019's position is ≈ 0 like the
training years, the layer contributes ~nothing there and the escalation does not
bear on the spend. If it is large like 2022, the one-shot would be scored on a
run whose largest single C1 term is a known architectural artifact — and a
locked-test result is TOUCH-ONCE and cannot be re-run once seen (rule 22).

WHAT THIS IS, AND WHY IT SPENDS NOTHING. This measures an **INPUT**, not a model
output. It evaluates PJM's own submitted DA bid curves at PJM's own published
2019 DA prices — the rule-13 admissibility anchor — with **no LP, no fleet build,
no bundle, no determination, no registry entry**. No model result for 2019 is
produced, so 2019's power to surprise is untouched. This is the posture pjm-160's
seam-ladder derivation took for 2019/2021/2022 ("ungated prep: no year solved,
scored or registered"), and it is what rule 22's 2026-08-06 clarification makes
explicit: *what is held out is the SCORE, never the DATA* — data intake and input
characterisation need no marker; only solving, scoring or registering does.

Reuses the pjm-158 helper chain unchanged (`load_curve` / `build_hour_arrays` /
`eval_net_fast` / `actual_da_price`), so the 2019 number is computed by exactly
the code that produced the 2022-2025 column. Only the year set differs.

Sign convention (pjm-158's): **+ = net virtual DEMAND** (phantom load).

Run:  uv run python scripts/probes/_pjm162_virtual_2019.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import _pjm158_virtual_gain as G  # noqa: E402

OUT_PATH = REPO / "results/calibration/_pjm162_virtual_2019.json"
TWH = 1e6

#: 2019 is the locked-test year under assessment; the rest are the already
#: measured context column (pjm-158 in-sample, pjm-161 for 2022).
YEARS = (2019, 2022, 2023, 2024, 2025)


def main() -> None:
    pd.set_option("display.width", 190)
    rows = []
    for year in YEARS:
        try:
            bids = G.load_curve(year)
        except FileNotFoundError as exc:
            print(f"[{year}] SKIPPED — {exc}")
            continue
        hours = G.build_hour_arrays(bids)
        da = G.actual_da_price(year)  # PJM's own published DA, RTO hub mean

        anchor = float(G.eval_net_fast(hours, da).sum()) / TWH
        # Sensitivity: the same curves cleared +/- $5 around the actual DA level,
        # so the anchor's steepness is visible and a reader can see whether the
        # number is a knife-edge or a robust property of the curve.
        lo = float(G.eval_net_fast(hours, da - 5.0).sum()) / TWH
        hi = float(G.eval_net_fast(hours, da + 5.0).sum()) / TWH

        rows.append(
            dict(
                year=year,
                anchor_at_actual_DA_TWh=anchor,
                anchor_at_DA_minus5_TWh=lo,
                anchor_at_DA_plus5_TWh=hi,
                mean_actual_DA=float(np.mean(da)),
                n_hours=len(da),
            )
        )

    df = pd.DataFrame(rows).set_index("year")
    OUT_PATH.write_text(json.dumps(rows, indent=2))

    print()
    print("=" * 88)
    print("pjm-162 — annual NET DA virtual position at PJM's own published DA prices")
    print("  TWh; + = net virtual DEMAND (the term served as phantom physical energy)")
    print("=" * 88)
    print(df.T.round(3).to_string())
    print()
    if 2019 in df.index:
        a19 = df.loc[2019, "anchor_at_actual_DA_TWh"]
        print("READING")
        print(f"  2019 net DA virtual position at actual DA prices: {a19:+.2f} TWh")
        ctx = df.drop(index=2019)["anchor_at_actual_DA_TWh"]
        print(f"  context — 2022 {ctx.get(2022, float('nan')):+.2f}, "
              f"2023 {ctx.get(2023, float('nan')):+.2f}, "
              f"2024 {ctx.get(2024, float('nan')):+.2f}, "
              f"2025 {ctx.get(2025, float('nan')):+.2f}")
    print()
    print(f"written: {OUT_PATH}")


if __name__ == "__main__":
    main()
