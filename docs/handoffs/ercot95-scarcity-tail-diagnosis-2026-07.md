# ERCOT-95 diagnosis — the 2023-summer scarcity-tail miss is a SUPPLY-MIX residual on an ALREADY-ADDRESSED owner; the reserve-side / ORDC-LOLP lane is refuted three ways

**Verdict: the ERCOT-95 hand-off's reserve-side / ORDC-LOLP hypothesis does NOT
own the 2023-summer LMP under-run. It is refuted by (a) the keeper config, (b)
measure-first on measured data, and (c) the ERCOT-68/69/70 prior adjudication —
all three independently. C3c stays FAIL because the residual is the supply-mix /
CC-formation frontier whose named owner (phantom CC) and offer-belt composition
are ALREADY deployed in the ercot91 keeper. C3c is a *supporting* criterion; the
correct disposition is to LEDGER it as the documented supply-mix limitation
(NOT-YET → CALIBRATED-WITH-CAVEATS), not to re-open the reserve side.**

Measure-first only (rule 15, no keeper re-solve — the ercot91 committed 2023
sidecar + measured ERCOT reserve/AS series). The confirming 2023 A/B (the
co-opt LOLP-table swap, below) was BLOCKED by the environment: the ercot91
keeper was built on the ERCOT-74..94 codebase and this session's container
could not fetch that code (blobless partial-clone blob fetch through the agent
proxy times out). The A/B is specified below for a session with a
keeper-compatible tree; the disposition does not depend on it.

## The objective (owner, ERCOT-95)

"Restore the 2023 summer (Jul/Aug/Sep) scarcity TAIL." ercot91
(`2026-07-20-ercot91-seasonal-drag-fullspan`) is **NOT-YET**, driven by the
**C3c price_tail FAIL** (2023 model 40 h vs RT 181 h >$200, 0.22×). C3a-2023 and
C3b are already ledgered CAVEATs sharing the same root.

## Finding 1 — the hand-off's proposed knobs are DEAD CODE in this keeper

The hand-off (and ERCOT-94) pointed at `scarcity.py::ordc_adder` / `lolp` /
`load_lolp_params` / `ordc_lolp_params_path` / `ordc_as_plan_mw` — the
**post-solve ORDC overlay** (`runner.py` ~1715, gated on
`config.scarcity_pricing_enabled AND config.scarcity_price_overlay`).

The ercot91 `run_config.json` has **`scarcity_pricing_enabled = False` and
`scarcity_price_overlay = False`**. So that entire path — `scarcity_prices()`,
`ordc_adder()`, `load_lolp_params`, the AS-plan netting — **never executes**.
Wiring `ordc_lolp_params_path` to the published CSV or setting `ordc_as_plan_mw`
via that path would change NOTHING in the scored price.

The scored settlement price's scarcity component comes from a DIFFERENT
mechanism: the **energy+reserve co-optimization** (`energy_reserve_coopt=True`,
`ercot_multiproduct_as_coopt=True`, `ercot_reserve_supply_cap=True`,
`ercot_ordc_total_reserve=True`). The scored `ordc_adder` column
(`run_calibration_full.py` ~618-668) = `result.reserve_price_by_family[:, -1]`
(the ORDC total-reserve family balance dual), added to the energy price.

## Finding 2 — AS-plan netting is the WRONG lever (measured, over-fires)

Hand-off smoking-gun #2 was `ordc_as_plan_mw = 0.0` (no AS netted). Measured on
disk (`ASPLANNP433_2023`, RegUp+RRS+ECRS+NSPIN mean **7,726 MW**), netting that
off ERCOT's measured on-line reserve (RTOLCAP) drives `ordc_adder` on the
measured envelope to **4,538 h >$200** (vs the 181-h target) — a catastrophic
over-fire, because RTOLCAP already embeds AS-held capacity. The runner code
already says so verbatim (`runner.py` ~1731: "NOT netting the AS plan — ERCOT's
RTOLCAP already counts online AS-held capacity as reserve, so subtracting it
double-counts"). Measure-first confirms the code's design decision.

## Finding 3 — the 181-h tail is ENERGY scarcity, not the ORDC adder

From `ercot_2023_ordc_reserves_hourly.parquet` (measured):
- **`system_lambda` alone is >$200 for exactly 181 hours** — the C3c benchmark
  tail IS ERCOT's SCED energy-scarcity price.
- ERCOT's *actual* on-line ORDC adder `rtorpa` is >$200 in only **11 h** (max
  $651); `rtordpa` 2 h. The adders add ~8-12 h on top of the energy tail.
- On the 181 tail hours ERCOT's own RTOLCAP median is **~7,227 MW** — moderate,
  not physically short.

So even ERCOT's real ORDC did not create the tail; the model's ORDC overlay
would have to carry the whole energy-scarcity tail that its capped merit-order
offer curve cannot form.

## Finding 4 — the ONE live reserve lever (co-opt LOLP curve) is a latent correctness item, not a C3c fix

The co-opt reserve demand curve DOES read the published table:
`reserve_config.py:753` calls `resolve_lolp_params(config, hours)` (which returns
the seasonal CSV when `ordc_lolp_params_path` is set), then **collapses it to the
annual mean** (`mu_s = float(np.mean(mu))`) before `ercot_ordc_demand_steps`. So
swapping to the published table shifts the co-opt curve center from the synthetic
default **mu=0** to **mu≈915** (σ 1400→1343) — it prices moderate reserve ~890 MW
higher.

- This IS a legitimate rule-11 correctness improvement (the synthetic mu=0 is a
  placeholder; ERCOT's published net-load-error distribution is the measured
  input). It should be A/B'd and, if it does not over-fire (C7 / zero-spurious),
  adopted **on correctness grounds** independent of C3c.
- But it will NOT close C3c: measure-first shows the published table at measured
  RTOLCAP fires only **~28 h >$200** (matching ERCOT's small actual rtorpa),
  because on the tail hours the model's reserves are **loose** (RTOLCAP ~7,227),
  above even the shifted curve's steep zone. ERCOT-69 said the same ("realized
  reserves are LOOSE at those hours").

**A/B spec (for a keeper-compatible tree):** `replay_keeper.py` on the ercot91
meta with `ordc_lolp_params_path = data/raw/_validation-source/ercot_ordc_lolp_params.csv`,
2023 only (rule-16 throwaway, never registered). Predicted C3c ≈ 0.35-0.4× (not
in band); check C7 diurnal + zero-spurious for over-fire before considering the
swap on correctness grounds.

## Finding 5 — the residual is the SUPPLY-MIX frontier, owner ALREADY addressed

Incidence test on the ercot91 2023 sidecar (rule 15):
- The model's scored `ordc_adder` fires (>$20) on only **2 hours**; of the 40
  model tail hours, 38 are energy-dual scarcity (genuinely tight fleet).
- The **143 missing tail hours cluster in Aug (79) / Sep (22) / Jul (11)
  afternoons (hod 13-19)**, priced at merit-order CC **~$56** while reality was
  **~$767** — a *which-units-clear* formation gap, not a reserve-pricing gap.

This is exactly the ERCOT-68/69/70 adjudication, converging from four
independent measurements: the residual is a **SUPPLY-MIX / dispatch residual**
(ERCOT-68: "NOT reserve-side"; ERCOT-69: "SUPPLY-MIX residual, not DA-expressible
offer/AS formation"; ERCOT-70 named it: **+1.2-1.7 GW phantom CC_REGULAR from
four CAMPD-invisible plants** — Kiamichi/Hidalgo/AVR/EG178 — composing with the
measured offer belt).

Crucially, that owner is **already addressed in the ercot91 keeper**:
- `ercot_noncampd_plant_availability=True` — the CAMPD-blind per-plant
  availability caps for the four blind plants.
- `ercot_offer_surface_cleared_share(+_rt +_state)=True` — the ERCOT-72/73
  measured cleared-share offer boundary + commitment-loading-state wall (the
  successor to, and mutually exclusive with, the ERCOT-69 midcurve belt).

And the ERCOT-73 commitment-state weight **deliberately stands the offer wall
down in tight summer** (Aug-23 w=0.02, Sep-23 w=0.09), because reality
RUC/self-commits that capacity near cost — so the offer belt is *correctly*
silent on the 143 missing hours. The residual is that the model, with honest
availability, still has marginally more/cheaper capacity committed at those
afternoons than reality did, so it never climbs into the $60-100 belt reality
cleared. That is the chartered supply-mix depth (ERCOT-66 storage dead-end,
West/Panhandle topology charter, the CAMPD-invisible partial-derate tail) — none
of it reserve-side.

## Disposition

1. **Close the reserve-side lane.** The ERCOT-95 reserve-side / ORDC-LOLP
   hypothesis is refuted (Findings 1-4). Do not re-open it; the post-solve
   overlay is dead code, AS-netting over-fires, and the live co-opt curve swap is
   a correctness item worth ~28 tail hours, not a C3c fix.
2. **Optional correctness follow-up (independent of C3c):** A/B the published
   seasonal LOLP table into the co-opt curve (Finding 4). Adopt only if C7 /
   zero-spurious hold — a rule-11 measured-over-synthetic improvement, not a
   scarcity fix.
3. **C3c disposition:** it is a *supporting*-tier criterion; its miss is the
   documented supply-mix / CAMPD-blindness limitation, exhaustively adjudicated
   and with its named owner already deployed. Recommend **ledgering C3c as a
   documented measured-input caveat** (with C3a/C3b already ledgered, that is 3/3
   of `MAX_LEDGERED_CAVEATS`), which flips the determination NOT-YET →
   CALIBRATED-WITH-CAVEATS via `calibration_verdict.determine`. Owner sign-off
   required (governance action). The alternative is to keep it as the open
   chartered supply-mix lane (ERCOT-70 successor), unchanged.

## Data-integrity carry-over (from ERCOT-94, unresolved)

`data/raw/ercot/2026-02.part0001-0009.parquet` (Dec 3-9 2025 out-of-band upload)
lack the HASL column and crash the offer-wall derives on year 2025; quarantine
them until re-uploaded with HASL. Not on this lane's path (reserve/AS + LOLP
table are the primary inputs), but flagged for the owner.
