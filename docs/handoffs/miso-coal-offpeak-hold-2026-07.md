# MISO COAL_BIT under-generation lane — diagnosis, two refutations, pricing re-diagnosis

**Date:** 2026-07-13. **Lane:** miso-60 handoff sanctioned lane 1
("commitment-posture window rows"). **Status: both commitment candidates
REFUTED; residual re-diagnosed as coal-BIT take-or-pay BID-PRICING; owner chose
the grounded contract-share fix; mechanism BUILT + unit-tested; throwaway 2024
probe GREEN (COAL_BIT +15.78 onto measured); full 2023-25 keeper build in
flight.** Companion to `docs/multi-iso/miso-scarcity-posture-design-2026-07.md`
(§A pooled-U lever, REJECTED as miso-43).

## RESOLUTION — grounded bituminous committed take-or-pay bid discount (miso-62)

Mechanism `coal_bit_committed_takeorpay` (`ScenarioConfig`; `fleet.py`
`campd_tranche_fuel_frac`): the `_committed` tranche of a **bituminous** coal
plant in the measured take-or-pay map passes ``1 − contract_share`` of its fuel
— the same sunk-contract rule already on `_mustrun`. MISO coal is ~100%
contracted (`coal_takeorpay_MISO.csv`), so contracted BIT baseload bids down to
hold against cheap gas; econ*/peak keep full delivered cost (`coal_econ_srmc_bound`,
already on) so BIT price-follows above the committed band. **Zero fitted
parameters** — the discount is each plant's own EIA-923 Schedule-5 share
(rule 1/13). Default off; scoped to bituminous (PRB/lignite carry their own
levers). Unit-tested (`tests/test_coal_sync_tranche.py`, 5 new cases).

**Throwaway 2024 A/B (rule 16, vs scored miso-60):**

| class | miso-60 | probe | Δ | actual |
|---|---|---|---|---|
| **COAL_BIT** | 37.66 | **53.44** | **+15.78** | **~53.4 ✓** |
| CT_PEAKER | 30.45 | 26.36 | −4.09 | lower ✓ |
| COAL_PRB | 108.56 | 103.08 | −5.48 | (redistribution to watch) |
| total coal | 150.5 | 160.5 | +10.0 | 167.1 |

COAL_BIT lands **almost exactly on the measured ~53.4** with no residual tuning
— right structure → right number (rule 1 ideal). The BIT→PRB redistribution
(some PRB econ displaced by cheap BIT committed) is the item the full 2023-25
build must clear (COAL_PRB staying in C1 tolerance). The apparent ST_GAS +5.6
is the OTHER_FOSSIL→0 raw-klass relabel artifact (OTHER_FOSSIL raw = 0 vs
gmModel 8.95), not a real rise. Twin: the discount is a PRICING input (forces no
energy) so it stays ARMED in the zero-forcing twin (like the passthrough
sigmoids / miso_rpe_pricing).

## The residual (recorded before any build, per the diagnosis discipline)

The dominant free-C1 MISO residual under the keeper `miso-60-stgas-vlr`:

- **COAL_BIT under-generates ~15.7 TWh in BOTH 2023 and 2024** (2024: model
  37.66 vs actual ~53.4 TWh). Aggregate coal: model 150.5 vs actual 167.1
  (2024), 165.8 vs 175.0 (2023). In 2025 coal *over*-generates (+16.9, high gas
  $3.52) — a **separate** South-gas/RDT problem (lane 3), not this lane's target.
- **CT_PEAKER over-generates +11.2 TWh in 2024** — displaced energy.
- COAL_BIT D-1 diurnal cv_ratio is 2.50 (2023) but **UNGATED** — D-1 gates only
  CT_PEAKER and ST_GAS (`D1_GATED_CLASSES`), and COAL_BIT already scores
  `verdict: pass`. The scored residual is purely the **C1 fuel-mix LEVEL**.

## Refutation 1 — min-down gap-bridge (the handoff's "min-run/min-down on U")

Fresh CAMPD measurement (2023-2025 unit-level hourly `grossLoad`, MISO coal fleet):

| stat | 2023 | 2024 | 2025 |
|---|---|---|---|
| coal on-fraction | 0.575 | 0.563 | 0.590 |
| RUN length median / mean (h) | 264 / 511 | 236 / 509 | 239 / 497 |
| OFF window p10 / median (h) | 6 / 94 | 5 / 94 | 4 / 76 |
| off-blocks <16h (unit-hours/yr) | 796 | 820 | 1149 |
| off-blocks <48h (unit-hours/yr) | 5731 | 4942 | 6300 |

Coal's physical min-DOWN is short (p10 off-window ~5 h — real coal *does* cycle
with short breaks); total bridgeable short-gap volume is ~0.2 TWh (<16 h) to
~1 TWh (<48 h) — **an order of magnitude below the 15.7 TWh deficit.** A
min-down gap-bridge (CAISO RA / ERCOT gas-CC pattern) cannot supply it.

## Refutation 2 — coal_sync_srmc_tranche (the min-load HOLD; rule-20 candidate)

`coal_sync_srmc_tranche` + `coal_mustrun_online_pmin` + `coal_takeorpay_from_data`
is the existing (never-MISO-tried) mechanism whose docstring names *"the step-2
residual: 2024 coal under"* — coal HOLDS volume at min-load instead of
price-following down. Rule 20 required testing it before any parallel floor.

**THROWAWAY 2024 A/B probe** (`scripts/probes/_miso_coalsync_probe.py`, rule 16,
never registered; 2024-only vs the scored miso-60 baseline):

| class | miso-60 | probe | Δ | target |
|---|---|---|---|---|
| COAL_BIT | 37.66 | 39.25 | **+1.60** | +15.7 needed |
| COAL_PRB | 108.56 | 110.18 | +1.62 | — |
| total coal | 150.5 | 154.6 | +4.15 | +16.6 needed |
| CT_PEAKER | 30.45 | 28.54 | −1.91 | direction OK |

- COAL_BIT rose only **+1.6 of the +15.7 needed** — the dominant residual is
  essentially unmoved; COAL_BIT stays a clear C1 FAIL (~−14).
- On the correct D-1 off-peak window (h0-14), COAL_BIT off-peak CV went
  **0.104 → 0.102 — unchanged** (coal_sync did not flatten the shape; and the
  shape is ungated regardless).
- Most of the small coal rise landed in PRB/lignite, not BIT — because the
  online-Pmin forcing is capacity-proportional, while the deficit is
  BIT-specific.

**Verdict: REFUTED for the COAL_BIT residual** — mirrors the ERCOT coal_sync
rejection exactly ("the gap is committed-band PRICING, not min-load quantity").

## Re-diagnosis — COAL_BIT is a take-or-pay BID-DISCOUNT (pricing) phenomenon

- In the probe, COAL_BIT is synchronized ~all hours at LMP ≈ $30, right at its
  delivered bituminous SRMC (~$2.5-3.5/MMBtu × ~10 HR ≈ $25-35/MWh). Its
  dispatchable (econ/peak) tranches back down whenever cheap gas ($2.19 in 2024)
  sets a lower LMP → BIT under-generates on **price**, not commitment.
- MISO coal fuel is **~100% contracted** (`coal_takeorpay_MISO.csv`: contract
  share mostly 1.0, a few 0.82-0.96). Contracted/sunk fuel gives BIT a real
  economic basis to bid **below** delivered spot cost to hold baseload against
  cheap gas — exactly the `coal_lignite_passthrough_sigmoid` docstring logic
  ("take-or-pay fixed costs are sunk → discount the BID, not the cost").
- The model omits this for bituminous: `coal_bit_passthrough_sigmoid` is **OFF**
  and `coal_econ_srmc_bound` is **OFF**, so BIT bids full delivered cost and is
  priced out by cheap gas.

**Candidate fix (a DIFFERENT lane — coal-BIT pricing, not commitment):** a
BIT bid discount **grounded in the measured take-or-pay contract share** (not a
residual-tuned sigmoid — rule 1). The take-or-pay data already exists; the open
design question is whether to drive the discount off the measured contract share
(grounded, preferred) vs the gas-keyed `coal_bit_passthrough_sigmoid`
(fitted floor/ceil/mid/slope — rule-1 risk unless anchored).

## BIT-only vs all-contracted-coal (the scope fork discovered in the build)

The full BIT-only 2023-25 build fixes COAL_BIT (both years) + CT_PEAKER-2024 but
flips COAL_PRB PASS→FAIL (2023/2024): cheap fuel-free BIT committed steals PRB's
merit slot (PRB is equally ~100% contracted but got no discount). Net +1
free-class (≈10/12). Generalized to `coal_committed_takeorpay_all` (discount all
contracted coal); throwaway 2024 A/B (8 TWh C1 band):

| class | actual 2024 | miso-60 | BIT-only | all-coal |
|---|---|---|---|---|
| COAL_BIT | 53.33 | 37.66 FAIL | 53.44 PASS | 52.82 PASS |
| COAL_PRB | 116.46 | 108.56 PASS | 103.08 FAIL | 124.25 PASS (+7.79, marginal) |
| CT_PEAKER | 19.22 | 30.45 FAIL | 26.36 PASS | 19.87 PASS |
| total coal | 176.3 | 150.5 | 160.5 | **182.6 (+6.3 over)** |

- **BIT-only:** surgical (fixes the genuinely priced-out class), no overshoot,
  clean 2025 (all coal/CT PASS); leaves a PRB redistribution break (the exposed
  total-coal deficit — a rule-11 root-cause item, not a mechanism flaw).
- **all-coal:** sweeps 2024 clean, but **overshoots** — PRB +7.79 (was −7.9;
  a big swing that only just passes) and total coal +6.3 over actual, a rule-1
  over-forcing signal; and it risks the already-high 2025 PRB (146 vs 139
  actual) since a blanket fuel-free committed floor raises PRB in every year.
  Needs a full 3-year build to know the 2025 PRB verdict.

Both mechanisms are built, tested, backward-compatible, and pushed. Owner steer
pending on which to register as miso-62 (recommendation: BIT-only — the
owner-chosen scope, surgical, no overshoot; PRB break ledgered as the total-coal
root-cause item).

## Refutations / settled (do not revisit without new evidence)
- min-DOWN gap-bridge on coal: REFUTED (bridgeable volume ~1 TWh ≪ 15.7).
- coal_sync_srmc_tranche for the COAL_BIT residual: REFUTED (probe +1.6, shape
  unchanged, ungated). It remains a legitimate min-load-HOLD mechanism for a
  *shape* problem, but this residual is a LEVEL/pricing problem.
- miso-43 pooled-U posture lever: REJECTED (honesty gate, 3.7-4.2× cleared reserve).
- 2025 coal over-generation is NOT this lane's target (lane 3); do not worsen it.

## Artifacts
- `scripts/probes/_miso_coalsync_probe.py` — throwaway 2024 coal_sync A/B (rule 16).
- `scripts/probes/_miso62_coalsync.py` — full 2023-25 coal_sync keeper+twin driver,
  built but **NOT to be run as a keeper** given the refutation (kept for the record /
  a future shape-lane if wanted).
