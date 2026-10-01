# RESULT — PJM-NEXT card 1: year-correct plant membership and zoning, 2019–2025 (2026-09-25)

**PROMOTED.** `2026-09-25-pjm-r-pjm-2` → **`2026-09-25-pjm-next-c1`** (bundle `results/calibration/pjmnext_c1_span`,
2019–2025 in ONE bundle). Promoted on the owner's ruling, verbatim: *"Is this a recommended keeper candidate? If so plz
promote. If structural integrity improves but gates regress that may still be a keeper.."*. The ruling is applied on
structure (rule 1). The recommendation is yes: three rule-14 repairs and zero criterion flips.

Charter: `docs/PRECOMMIT-pjm-next-c1-year-correct-membership-2026-09-25.md` + `docs/PRECOMMIT-pjm-next-c1-ADDENDUM-g1-2026-09-25.md`.

## 1. What changed (recipe = R-PJM-2 keeper + three flags, zero free parameters)

| flag | what it repairs (phase 0, zero LP) |
|---|---|
| `mid_vintage_exit_carry` | Plants that retired **during** their own vintage year were in neither EIA-860 sheet, so the keeper dropped their real operating months. Injected rows: 47 / 34 / 24 / 77 / 49 / 60 in 2019–2024 (Bruce Mansfield, TMI, Conesville, Zimmer, Avon Lake, Cheswick, Will County, Sammis, Joliet 29, Yorktown, Homer City …). 2025: 0 by construction. The fleet census removes or changes 0 keeper units (no double carry). |
| `fleet_zone_vintage_coords` (**new**, this lane) | PJM plants eGRID 2023 lacks fell to the `PJM_AEP_Ohio` fallback. The keeper's own 2019 / 2020 / 2021 fleets had 3,824 / 3,561 / 2,900 MW mis-zoned (Will County → ComEd, Cheswick → West_APS, Avon Lake → ATSI, Chambers / Logan → EMAAC). With the flag, **0 MW** is mis-zoned in every year. Fallback branch only; membership is untouched. |
| `benchmark_membership_vintage_union` (SPP-49) | The PJM EIA-923 actuals left out the same plants. The union adds COAL_BIT +8.80 / +8.27 / +7.84 / +4.47 TWh (2019–22), nuclear +5.21 (2019) and solar +2.31 (2024). Rebuilt totals: 820.811 / 805.898 / 827.088 / 833.192 / 823.024 / 852.252 / 871.628 TWh, **exactly as pre-registered**. The rebuild seam also had to learn to find the flag, and that fix is in this lane. |

## 2. Controls and G-DRIFT

Pin `7f0953845350089732892f83248726d4b04fb84f`. G-DRIFT from the keeper's `651fac08` found **one LIVE change set**: COAL-SUB
(`8eaf34b5` + `05437cc0`), which eliminated the bare `COAL` class. It re-prices the keeper's formerly unresolved coal
cohort in 2019–2022 (18.2 / 7.3 / 17.0 / 3.7 TWh of keeper dispatch). A control solve at the same pin was therefore
spent for 2019–2022 (rule 29(b)). 2023–25 use form 4 against the committed keeper.

## 3. Result on the SAME (union) benchmark — `scripts/calibration_verdict.py`

**Zero criterion flips in any year.**

| year(s) | prior keeper | new keeper |
|---|---|---|
| 2023–25 | NOT-YET — C1 only | NOT-YET — C1 only (CC_REGULAR 2024 −14.68 TWh; prior −14.36) |
| 2019 | C1 FAIL, C3c caveat | same |
| 2020 | C1 FAIL, C3a FAIL | same (C3a +17.4 % vs +17.8 %) |
| 2021 | C1 FAIL, C3c caveat | same |
| 2022 | C1 FAIL, C3b FAIL, C3c caveat | same |

**This card's own effect on the COAL_BIT C1 error**, measured against the same-pin control:
**−4.94 / −8.55 / −9.83 / +0.28 TWh** in 2019 / 2020 / 2021 / 2022. It moves toward actual in three of four years. The
model adds the real plant-months (2019 +3.86, 2022 +4.75), and the actuals add the plants the model always dispatched.

**Reported at full magnitude.** Row-level against the *committed* prior keeper, the COAL_BIT rows rise: 2019 +8.25 →
+28.42, 2020 +13.18 → +19.40, 2021 +23.31 → +32.57, and 2022 +2.40 → **+10.33, now a FAIL**. The cause is **COAL-SUB, not
this card**. The control shows the same shift: bare COAL −18.2 → COAL_BIT +16.3 / PRB +3.8 in 2019. Any re-solve of the prior
keeper at today's `main` carries it too. In the arm, CC_REGULAR 2021 improves (−7.47 → −5.40) and 2022 improves
(+12.83 → +10.91).

**Stated, not absorbed:** TMI (8011) is now injected and zoned to Central_PA, but it **dispatches 0 MWh in 2019**.
Nuclear is not a scored C1 class, but a successor should check the nuclear must-run / availability path for mid-year
retirees.

## 4. Governance

- DOF ledger carried verbatim; zero entries added (`scripts/gen_pjmnext_c1_attestation.py`).
- `authorized_price_tuning.used = false`. Offers are the keeper's, modulo the COAL-SUB fold.
- Rule 35 order: register → `keepers/PJM.json` → `calibration-complete.json` → `build_status` → `audit_keepers` →
  prune `2026-09-25-pjm-r-pjm-2` (sidecar, payload, `rpjm2_span`) → `audit_keepers --iso PJM` reads **0 failures**. The
  year set 2019–2025 is fully covered.
- Matrix: all three cells are **K**; the PJM shard and §5.3 are re-stamped.

## 5. Retrievability (rule 34(e))

The keeper bundle is **on `main`** in rule-15 shape: attestation, diagnostics, per-year configs and hourly sidecars
(47 files). Per-plant `dispatch/` follows the repo-wide `.gitignore`, as for every PJM keeper. A question that needs it
costs a 7-shard re-solve (~12 min per year).

Shard commits (provenance only; the branches are transport):

| leg | commit |
|---|---|
| arm 2019 | `f5e305a58345` |
| arm 2020 | `64e6a16e3617` |
| arm 2021 | `aacc957040e8` |
| arm 2022 | `3c0fd248e1a1` |
| arm 2023 | `657e50c23fd2` |
| arm 2024 | `da596ccd0fb4` |
| arm 2025 | `8d5ebd63fa35` |
| control 2019 | `dcfa736934ba` |
| control 2020 | `966841c2d8b8` |
| control 2021 | `062aaf2c2f5e` |
| control 2022 | `fb29bae51387` |

The first launch lost 9 of 11 legs to two G1 wording defects in the parent's prompt and to OOM kills: a full clean regen
starved the swapfile. The blocker records are in `docs/handoffs/pjm-next-c1-r1-blockers/`. All shards are archived.

Leftover shard branches the owner must clear (sessions cannot delete refs, rule 33(f)):
`claude/pjmnext-{c1,ctl}-*` and `claude/pjmnext-{c1,ctl}-*-r2`.

## 6. Still open

- **Card 2 (F2 outage-extract drift)** needs the owner's OK to overwrite the committed `data/raw` outage extracts.
- **Card 3 (unit partial derate)** is deprioritized on magnitude: ≤ 0.27 TWh/yr
  (`docs/FINDING-pjm-next-c3-partial-derate-bound-2026-09-25.md`).
- **The rubric failures:** C1 CC_REGULAR 2024 (−14.7) on the training span. Coal over-dispatch in 2019–2022 is now larger
  row-level because of COAL-SUB (the coal-vs-gas offer ordering, card 4). C3a 2020, and C3b 2022.
