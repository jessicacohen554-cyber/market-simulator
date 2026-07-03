# NYISO 42 — reconciled Iroquois winter spread (registered probe, NOT promoted)

nyiso-41 keeper config + `--nyiso-iroquois-winter-spread` (rule-#13
reconciliation: measured SOM annual Iroquois−Transco spread re-allocated across
months by the measured Algonquin monthly basis; zonal monthly hub ratios — NYC
resolves to its own measured Transco monthly exactly).

**Winter physics validate:** Dec-2024 monthly LMP residual −$25 → −$10,
Feb-2023 −$14 → +$4, Jan/Feb-2025 −$19/−$24 → −$12/−$14; C3b 2024 0.236 →
0.190; C3a 2024 −13.4 → −12.6%, 2025 −9.5 → −9.1%.

**Why not promoted:** the mechanism exposes two compensations the flat spread
was providing — (1) the flat construction over-priced eastern zones
~$1.3/MMBtu in every *unconstrained* month, propping shoulder LMPs: with the
correct near-zero shoulder premium the broad energy-only undershoot deepens
(2023 C3a −13.3 → −15.8%); (2) dearer winter eastern gas suppresses 2025
in-state gas burn through the **HARD C2 band (−2.5% vs EIA-930) → FAIL**. Also
Jan-2024 +$6 / Dec-2025 +$16 winter overshoots to re-check.

**Carry-forward:** keep the measured reconciliation (default-off flag); fix
the exposed root causes rather than re-burying them (rules #1/#13): the
shoulder undershoot is the reserve/uplift frontier now cleanly isolated; the
C2-2025 interaction and the December-2025 over-concentration of the AGT
weights need a targeted look. Keeper stays `2026-07-03-nyiso-41-hub-prices`.

Reproduce: the nyiso-41 command + `--nyiso-iroquois-winter-spread`.
