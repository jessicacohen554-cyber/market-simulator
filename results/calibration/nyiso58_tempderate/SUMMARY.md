# nyiso-58-tempderate — temp-derate full-keeper rerun (PROBE)

Byte-faithful replay of the `2026-07-07-nyiso-56-measured-zonal` keeper's
recorded solve kwargs (`replay_keeper.build_kwargs` on the keeper's own
`meta.json`) with `temp_dependent_derate=True` added — nothing else changed.
All three train years (2023-2025) in one bundle per CLAUDE.md rule 16.
Registered as a dashboard PROBE, never a keeper promotion
(`docs/handoffs/temp-derate-keeper-rerun-playbook-2026-07.md`).

## hoursGt300 (DA-expressible, NYISO/NEISO $300 threshold)

| year | keeper | this probe | ablation twin | actual (DA) |
|---|---|---|---|---|
| 2023 | 21 | 39 | 49 | 1 |
| 2024 | 0  | 2  | 2  | 0 |
| 2025 | 14 | 36 | 44 | 12 |

Scarcity tail gets WORSE in every year vs the keeper (moves further from
actual), unlike the single-year ERCOT/PJM validation probes where the
mechanism closed an undershoot. NYISO's keeper was not undershooting scarcity
hours to begin with (2023 already 21h model vs 1h actual; 2025 was close at
14h vs 12h) — the added hot-hour capacity tightening pushes both years further
into overshoot.

## Other structural deltas vs keeper

- C1 fuel-mix / C2 system volume / C4 dispatch correlation / C5a CO2:
  essentially unchanged (confirms the CC/CT reshape is capacity-neutral as
  designed; NYISO has no coal fleet for the additive COAL/ST_GAS channel to
  matter at scale).
- C3a mean LMP: mixed — 2023 regresses (31.59→37.21 vs actual 30.29, now
  overshoots), 2024/2025 improve (closes real undershoot: 2024 33.18→34.88 vs
  actual 35.95; 2025 56.21→61.71 vs actual 60.74).
- C3b price shape: 2023 regresses sharply (0.188→0.421 stat), 2024/2025
  roughly unchanged.
- C8 forced-energy share (ST_GAS at the reliability floor): improves
  slightly in all three years (30.5/44.6/38.2% → 27.8/41.2/34.4%) — the
  probe's raw FAIL label is an artifact of no governance attestation/ledger
  on an unattested probe bundle, not a magnitude regression.

Recommendation: HOLD for investigation, not immediate promotion or rejection.
The mechanism is physically grounded (CLAUDE.md rule 1) and the C8/C3a
2024-2025 deltas are genuine improvements, but the broad-based 2023
degradation (C3a, C3b, C3c) suggests an interaction with an existing NYISO
capacity-tightening mechanism (import caps / reliability floor) calibrated
against the flat net-summer derate — worth isolating before considering
promotion.
