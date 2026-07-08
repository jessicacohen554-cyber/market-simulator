# MISO keeper-swap memo — miso-47 → miso-48 (ST_GAS_INTERMEDIATE SRMC-floor re-ground)

**Date:** 2026-07-08 · **Decision:** OWNER — this memo presents the swap, it does not execute it
(`keepers.json` unchanged until sign-off). · **Lane:** L-14 (G-21/#1302 follow-on to the L-7 audit,
`docs/miso-caiso-srmc-floor-audit-2026-07.md` §2).

## What changed (one edit)

The generic `ST_GAS_INTERMEDIATE.committed` offer band was re-grounded **0.85 → 1.00× base_HR**
(`src/market_sim/pipeline/backcast_config.py`, merged to main in `5eff2b3`). The 0.85 was an
uncited, ISO-unscoped generic default pricing a **non-CHP, non-take-or-pay** gas tranche
~$3.3–5.2/MWh below its own average-heat-rate fuel cost at MISO 2023–2025 delivered gas — the exact
pjm-83 defect pattern, live in the miso-47 keeper via `st_gas_intermediate=True` (Harding Street,
Ames, Nine Mile Point, Lewis Creek, Sabine). 1.00× is the MISO cost-based-offer SRMC floor (Tariff
Module C / Attachment L; sanity-checked against the MISO IMM / Potomac Economics SOM), and is the
committed-band rule the class's own "mirrors CT_INTERMEDIATE" comment already claimed. A steam
boiler's part-load heat rate is monotonically worse than its average, so 1.0× is a true floor — the
CC flat-plateau exception does **not** apply, which is also why `CC_REGULAR.econ_low = 0.95` is
deliberately untouched (the audit rules it SURVIVES on MISO's own CAMPD flat-body marginal-HR
physics).

**Zero free parameters.** A tariff-cited bound replaces a residual-lineage scalar; nothing was
tuned to any residual. Leave-one-year-out therefore degenerates to per-year direction checks
(the miso-42 precedent), and the response is directionally consistent in all three years
independently (ST_GAS −0.6 TWh/yr, C3a +0.3pp/yr).

## Runs

| | run id | bundle |
|---|---|---|
| before (keeper) | `2026-07-08-miso-47-steamgas-ct` | `results/calibration/MISO/miso_47_steamgas_ct_drag` |
| after (candidate) | `2026-07-08-miso-48-stgas-srmc` | `results/calibration/MISO/miso_48_stgas_srmc` |

Recipe byte-identical to miso-47 (same 21 flags, all years 2023–2025 in one invocation, rule 16);
the only delta is the offer-band change above. Zero-forcing ablation twin registered alongside
(rule 21). Both determinations are **NOT-YET on the same four criteria** (C1 fuelmix, C2 sysvol,
C3a mean LMP, C3c tail); D-1/D-2/D-4/D-5/D-9/D-10 and C5a CO₂ / C4 / C6–C8 pass in both.

## Before → after (scored deltas, rubric v2.2)

**C1 fuel-mix by class** — headline 14/16 → **13/16** (free 10/12 → 9/12):

| year | class | miso-47 | miso-48 | note |
|---|---|---|---|---|
| 2023 | ST_GAS | −7.56 TWh (PASS) | **−8.16 TWh (FAIL)** | crosses the ±8.00 TWh band edge — the one flipped row |
| 2024 | ST_GAS | −10.08 TWh (FAIL) | −10.72 TWh (FAIL) | already failing; deepens by the same ~0.6 |
| 2023 | COAL_PRB | +8.10 TWh (FAIL) | +8.80 TWh (FAIL) | pre-existing overrun absorbs the displaced energy (#1347) |
| 2024 | COAL_PRB | +3.56 (PASS) | +4.26 (PASS) | same direction, in band |
| 2023 | CT_PEAKER | −2.52 (PASS) | −2.19 (PASS) | toward actuals |
| 2024 | CT_PEAKER | +3.62 (PASS) | +4.00 (PASS) | away, in band |
| all | CC/CHP/coal-BIT/LIG | ±≤0.25 TWh | | effectively unchanged |

**C2 system volume (2025, family fallback)** — unchanged: gas −14.7% → −14.6%, coal +16.2% → +16.4%
(both FAIL before and after; owned by #1347 sigmoid level + the 2025 import under-run).

**C3a mean LMP** — **improves in every year**: 2023 −0.4% → −0.1%, 2024 −5.0% → −4.7%,
2025 −11.0% → −10.7% (2025 still FAIL; rides the missing ELMP/RDC scarcity mechanism, as does C3c).

## The residual relocation is a discovered root cause, not a regression to revert

Per rules 1/11/14 this is a structure fix promoted on correctness. The sub-SRMC committed band was
silently buying ~0.6 TWh/yr of ST_GAS energy that the market's own cost floor says cannot clear at
that price — i.e. miso-47's ST_GAS C1 rows were flattered by an inadmissible mechanism. The true
G-25 commitment-posture wedge (steam self-commitment the perfect-foresight P1 cannot carry) is that
much larger than previously reported, and the displaced energy landing on the already-over COAL_PRB
stack re-confirms the #1347 coal-sigmoid offer-level item. Both attributions are ledgered in the
miso-48 attestation disclosures. Reverting to 0.85 to regain the 2023 C1 PASS would be tuning an
uncited sub-cost offer to a volume residual — exactly what rules 13/21/24 forbid.

## Recommendation

**Swap the MISO keeper to `2026-07-08-miso-48-stgas-srmc`.** It is strictly more structurally
faithful (rule 1: keeper = most faithful, not lowest error): same recipe, one uncited sub-SRMC
band replaced by the tariff floor, price level closer to actuals in all three years, all
protective gates passing, and the C1 flip fully attributed. The pjm-83 → pjm-90 precedent applies
verbatim (PJM's SRMC re-ground also worsened a volume metric and was promoted on structure).

On sign-off: update `keepers.json` MISO → `2026-07-08-miso-48-stgas-srmc`, run
`scripts/audit_keepers.py` / the `calibration-keeper-auditor` agent, rebuild
`scripts/build_status.py`, and commit `keepers.json` + `status.js`. Honour top-15 retention when
pruning.

## Honesty gate

1.00× is the tariff SRMC floor (measured base_HR × delivered gas + VOM), not a value tuned to a
residual. No unit pinned to observed CEMS generation; no input rescaled so model output lands on
actuals; coal sigmoids NOT re-fit (rule 23 — no source-data change).
