# nyiso 51 floor rederive — PROBE (floors-alone; keeper stays nyiso-41 STALE-VS-HEAD)

The CT/ST reliability-floor re-derivation (rule 17/18/23) named as the remaining
structural work in PR #1427, **floors-alone** (no delivered-fuel basis). Companion
config with the PR #1427 gas basis: `nyiso 52 floor rederive ctgas`. One-delta
baseline: `nyiso 48 head regate`. See the `nyiso 52` bundle SUMMARY.md for the
full audit, gate table, and disposition — this bundle isolates the floor changes
alone.

## Floor changes (rule 17/18/23, source-grounded narrowings)

1. NYC CT_PEAKER 24h hot step (tmax 31.7 / 0.1833) DISABLED (r1_disabled) — the
   D-4 off-window binder, double-floored NYC CT over the windowed NYC_CT_ev ramp,
   bound overnight where measured NYC CT CF ~= 0.018.
2. LI local self-supply floor NARROWED to the HB14-21 peak window
   (NYISO_SELFSUPPLY_FLOOR_HOURS); 0.45 level UNCHANGED (issue #1345).

## Gate (one-delta vs nyiso-48, 2023/2024/2025)

- CT_PEAKER 4.46/4.51/4.73 -> **3.70/2.84/3.86 TWh** (actual 2.26/2.13/2.84);
  C1 CT_PEAKER FAIL->in band; free-class 9/10 (remaining = 2024 ST_GAS -3.48).
- **C7 (D-1) FAIL->PASS all years** (2024 CT off-peak cv_ratio 0.454 -> 2.393).
- self-supply CT forcing HALVED (1.84/2.87/1.86 -> 0.90/1.23/0.89 TWh);
  reliability-floor CT overnight energy = **0.000** (was ~0.18 from the NYC step).
- NOT a keeper: rule-20 D-2 CT forced-share still >10% (reliability alone
  25.6/34.1/25.1%); C3a -16.2/-15.5/-13.6% / C3c 0/0/7h still FAIL — both cleanly
  the missing **#1344** peaker-scarcity/reserve price structure.
- D-4 residual (~35%) is entirely hour 14 (0 overnight) — the D-4 h15-21 vs NYISO
  HB14-21 window-boundary artifact.

Keeper stays `nyiso-41` STALE-VS-HEAD; `keepers.json` unchanged. The gas premium
(nyiso 52) is what pulls CT volume to near-exact; this floors-alone config leaves
CT modestly high (3.7/2.8/3.9). Rules 1/17/18/23.
