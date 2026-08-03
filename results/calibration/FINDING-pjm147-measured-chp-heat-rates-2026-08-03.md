# FINDING pjm-147 — measured power-only CHP heat rates at PJM: PROMOTED, and the session also closes caiso-158's deferred PJM re-gate

**Verdict: `measured_chp_heat_rates` PJM `U → K`.** New keeper
**`2026-08-03-pjm-147b-chp-heat`**, promoted 2026-08-03 on owner instruction
in-session. Every pre-registered gate passes except K2, which fails for a
chartered keeper-side reason this promotion itself resolves. CALIBRATED 9/9,
C1 all 16/16 · free 12/12, zero fails, zero caveats — identical scorecard to
the superseded `2026-07-31-pjm-143b-hy-level`, with the target class materially
closer to its measured actual in all three years.

Charter: `docs/handoffs/pjm-matrix-column-triage-2026-08.md` §2.2 (the triage's
rank-2 live candidate). Pre-registration:
`results/calibration/PREREG-pjm147-measured-chp-heat-rates-2026-08-03.md`,
committed **and pushed** before either arm solved. Machine record:
`results/calibration/_pjm147_chp_ab.json`; drift record
`_pjm147_k2_drift.json`; pre-solve wiring record `_pjm147_flag_fidelity.json`.

Rule 25 `[R-ISO-SCOPE]`: MISO/CAISO/NYISO `K` and NEISO `O` transferred
nothing. PJM entered as `U` and was judged on PJM's own artifact, derived this
session from PJM's own eGRID + CAMPD record.

## 1. The arms

| | run id | bundle |
|---|---|---|
| control | `2026-08-03-pjm-147a-control-zerodelta` | `pjm147_control_A` |
| arm | `2026-08-03-pjm-147b-chp-heat` | `pjm147_chp_B` |

Single delta `measured_chp_heat_rates=true`. Years 2023/2024/2025 in one bundle
per arm (rule 16 `[R-ALLYEARS]`), sequential, `--reuse-solved` chain (rule 12
`[R-PARALLEL]`). Both arms record `git.dirty=false` with empty `changed_files`,
and **zero commits touched `src/` or `data/raw/` between them** — the
single-delta property is proven from the record, not assumed.

## 2. Two prerequisites, both real

**The derive suite was red at HEAD.** All 7
`tests/unit/data/test_measured_chp_heat_rates.py::TestDerive` failures were one
stale harness signature: `plant_table()` grew the `basis_hr` argument in the
caiso-147 seam fix and the tests' own call site was never updated. Repaired by
defaulting `basis` to `model` — what the two *are* outside
`CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` — so every existing case keeps its exact
semantics, plus the case that was missing: a hand-factored shipped rate whose
**seam** rate matches eGRID's credited rate must flag `ok`. 15 passed.

**The PJM artifact had never been derived.** Derived with the ISO-generic
deriver, unmodified (rule 23 `[R-FROZEN-DERIVE]`).

## 3. The artifact

65 `(plant, class)` rows, **21 applied**. Flag census: `not_unfired_topping`
27, `ok` 21, `no_chp_credit` 8, `no_egrid_row` 5, `basis_mismatch` 2,
`above_physical_band` 1, `below_physical_band` 1.

| class | plants | capacity | metered CAMPD energy | cap-wt shipped → measured |
|---|---|---|---|---|
| CC_CHP | 5/14 | 1,766/2,385 MW (74.0 %) | 24.95/30.26 TWh (**82.5 %**) | 7.422 → 7.943 (**+7.0 %**) |
| CT_CHP | 16/51 | 268/823 MW (32.6 %) | 1.17/4.64 TWh (25.1 %) | 10.701 → 11.282 (+5.4 %) |

CEMS validation: `PLHTIAN + CHPCHTI` reproduces independently metered CAMPD
annual heat input within 1 % on **11/12** covered plants, median **1.00000**.
The one miss (50463 Procter & Gamble, 0.429) has sub-Part-75 units where CEMS
undercounts and eGRID is complete — it fails toward CEMS, never toward eGRID.

**Direction is PJM's own.** CC_CHP is **one-sided dearer** (5 of 5 rows, 100 %
of covered MW) — the MISO/NEISO shape, opposite CAISO's two-sided result.
CT_CHP is two-sided with a dearer tilt (13 dearer / 191 MW, 2 cheaper / 68 MW);
both cheaper rows are ones the ×1.8 hand factor **over**-corrected (Energy
Center Dover CT 12.577 → measured 9.929) — caiso-128's "wrong in both
directions at once", measured on PJM.

**The caiso-147 seam defect in PJM is real and MEASURED SMALL, correcting the
triage's expectation.** 29 rows carry the hand factor, but 25 are excluded by
other gates regardless, so gating at the replacement seam rather than the
shipped rate buys PJM **4 applied rows / 182.2 MW** — against CAISO's 59 rows /
3,089 MW. PJM's CC_CHP credited rates all sit above 6.0, so the CC limb never
fires on the applied population. The triage predicted a CAISO-sized latent
defect; it is not one.

## 4. Gates

| gate | result |
|---|---|
| **K0** wiring liveness, PRE-SOLVE | **PASS** — the ERCOT-146 hazard checked on PJM's own fleet (rule 25; neiso-70's clearance is NEISO's). 68 generators / 1,339.9 MW / 19 pairs move, identically in all three years; CC_CHP cap-wt **7.7130 → 8.1415** at the LP seam; zero out-of-scope leak |
| **K1** dispatch liveness | **PASS** — max \|Δ class-hour\| on CC_CHP 291.7 / 252.3 / 440.7 MW |
| **K2** control integrity (strict byte) | **FAIL** — see §6; chartered cause, not this lever |
| **K3** scope integrity | **PASS** — exactly 19 `(plant, class)` pairs move, every one in the artifact, `pairs_not_in_artifact` empty, zero out-of-scope classes, all three years |
| **K4** sign | **PASS** — CC_CHP never rises |
| **K5** overshoot (the neiso-70 kill) | **PASS** — \|C1 error\| improves every year, no crossing under |
| **E1b** CC_CHP band −0.3…−2.0 TWh | **PASS** — −0.455 / −0.639 / −0.972 |
| **E1c** \|C1 error\| improves | **PASS** — all three years |
| **E1d** C1 magnitude ≤ 1.5 TWh | **PASS** — largest non-CC_CHP move CC_REGULAR **+0.366** TWh |

**E1d is the gap pjm-146 named.** That session licensed a C3a move ex ante but
registered no C1 magnitude gate, which is precisely why its C1 CC_REGULAR
regression could not be adjudicated on its pre-registration alone. E1d was
declared here before either arm solved, and it passes with a 4× margin.

## 5. Result

| year | CC_CHP model → | actual | \|C1 error\| control → arm |
|---|---|---|---|
| 2023 | 9.062 → **8.606** | 6.115 | 2.947 → **2.491** |
| 2024 | 8.710 → **8.071** | 7.283 | 1.427 → **0.788** |
| 2025 | 7.806 → **6.835** | 6.445 | 1.361 → **0.390** |

Displaced energy (TWh): CC_REGULAR +0.190/+0.221/+0.366, COAL_BIT
+0.065/+0.103/+0.144, CT_PEAKER +0.066/+0.115/+0.186, CT_CHP
+0.024/+0.051/+0.013, ST_GAS +0.017/+0.023/+0.052, imports +0.031/+0.040/+0.077.
Load-weighted price **+$0.022 / +$0.026 / +$0.053** — a 1.1 %-of-generation
class repricing barely touching the annual level, as predicted.

Determination **CALIBRATED**, 9/9 at target grade, zero fails, zero caveats,
C1 all 16/16 · free 12/12. DOF **18 → 19** entries with `n_residual`
**UNCHANGED at 6**.

**Zero fitted parameters, and a hand number retired.** The replacement value is
eGRID's own published allocation on the same denominator; the deriver's four
gates are frozen upstream and were not touched. PJM sits in
`CHP_STEAM_CREDIT_HR_CORRECTION_ISOS`, so on covered plants the incumbent was
the credited rate times an off-registry ×1.8 / ×1.15-floored-6.3 factor;
`apply_measured_chp_heat_rates` runs first and hands the hand factor a
`skip_ids` set, so a repriced plant never also takes it (rule 19
`[R-ONE-MECH]`). This is a rules-21/24 retirement, not an addition.

## 6. K2 failed, and this promotion is what fixes it

The control does not reproduce the outgoing keeper: max \|Δ\| **943 / 1031 /
1245 MW** on the class-hour, load-weighted **+$0.057 / +$0.044 / +$0.077**.

Cause, attributed on three independent lines (`_pjm147_k2_drift.py`): pjm-146's
control reproduced this keeper at **0.0 MW** from `7cc95fa`, so the change
entered after it; over `7cc95fa..HEAD` the only PJM-solve-relevant data change
is `campd_ct_heat_rates_PJM.csv`; and the class signature is CT_PEAKER
**−0.924 / −0.657 / −0.899 TWh**, dominating every other class — exactly the
class that artifact reprices. The input moved on **63 of 71 applied plants /
19,887 MW**, cap-weighted **11.4749 → 11.5556** MMBtu/MWh (+0.70 %), flag
transitions `ok→ok` 71 (a pure value change).

**A framing this session got wrong and withdrew.** An earlier revision (commit
`c19a385`) called this an unchartered CAISO-lane change that violated the
matrix's "needs its own charter" warning. **That is false and is retracted.**
It is caiso-158 executing `PREREG-caiso156`: it has its own charter, it
pre-registered PJM's own delta (+0.0693 cap-weighted, reproduced here to 4 dp
independently), and it **declared the PJM scope cut on the record** — caiso-158
§5 did not launch PJM's arm A because PJM is the largest LP in the set
(~15.5 GB peak RSS against a 15 GB box **with no swap available**) and carried
the smallest predicted effect. There is no governance breach. The narrower fact
that survives: PJM's keeper was never **re-gated** against the corrected
artifact.

**So the control arm is caiso-158's follow-up item 2.** That item asked for "a
successor session on a larger box … or the `--years` + `--reuse-solved`
per-year invocation chain". This session had 12 GB of swap and used exactly
that chain. The control measures the CT meter screen for PJM: **dispatch-live
and score-neutral** — CALIBRATED 9/9 with a scorecard identical to the outgoing
keeper's — the same shape caiso-158 measured in CAISO/NEISO/NYISO. Promoting
arm B therefore also closes PJM's missing re-gate, which is what made K2 fail.

**One adverse diagnostic row, stated not buried.** D-2 CT_PEAKER forced share
**rises** keeper → control: 15.2/15.4/15.8 % → 16.3/16.4/16.5 %. All are a
GROUNDED ABOVE BUDGET PASS (every binding mechanism clears D-4, profile r and
off-peak CV both above floor), so C8 passes throughout and no determination
moves. Arm B is marginally better than its own control (16.2/16.3/16.4 %). *An
earlier draft of the promotion note claimed the screen* improved *this row,
citing 16.3/16.9/17.1 % — that is note item (5)'s pjm-137-era figure, copied
into the wrong comparison. Caught by the `calibration-keeper-auditor`, verified
against all three bundles, corrected at commit `eafb957`.*

## 7. What this does NOT establish

- **The CT_CHP half is not identified, not scored, and nearly inert.**
  Coverage is 32.6 % of capacity and 25.1 % of the class's own metered energy
  (thin on both bases); `CT_CHP ∈ FUELMIX_EXCLUDED`, so C1 never gates it; and
  it moves **+0.36 %** at the LP seam. Declared uncitable in either direction
  before the solve, and it stays uncitable (the neiso-73 discipline).
- **CC_CHP is a PINNED class** (`PINNED_CLASSES_BY_ISO`, audit L4 — measured
  CHP export floor), excluded from the free-class score. This lever therefore
  **cannot** improve PJM's headline: `free 12/12` holds either way. Equally it
  cannot be gate-chasing — the class it targets does not gate. It is rule-1
  `[R-STRUCT]` work judged on whether the mechanism is right.
- **CC_CHP/CT_CHP are exempt from BOTH C7 and C8 by explicit class list**
  (host-steam-pinned duty), not by the 2 % materiality floor, so their D-1/D-2
  numbers are diagnostics, never a passed gate.

## 8. Successor — the named lane

**The defect is not fully closed, and what remains is a QUANTITY question, not
a price one.** 2023 still runs **+2.49 TWh** over actual. The offer is now
measured, so the residual sits in the host-steam holdout (`chp_btm_pct` /
`chp_grid_pmin_mw`) and the `chp_steam` floor's level — **nyiso-105's named
successor lane**, which reached the same conclusion from NYISO's own data. Not
chartered here.

**DO NOT re-derive the heat rate against that residual** (rule 23
`[R-FROZEN-DERIVE]`): it re-derives only when eGRID/CAMPD source data updates,
and the derive commit must cite the source change.

**Also not done here, and needing its own charter:** the caiso-147 side finding
that sub-6.0 MMBtu/MWh loaded *meter* hours drag the shared CHP derive low in
every ISO (PJM 1.55 % of loaded hours, +0.081 energy-weighted). That is the CHP
analogue of the CT screen caiso-158 just shipped, it would move several
committed keepers' inputs, and it is a cross-ISO charter, not a PJM session.

## 9. Process note

Arm B's link 3 refused `--reuse-solved` ("reusing years none") and re-solved all
three years, because this session committed probe/generator files under
`scripts/` while the chain was running and the reuse gate checks `src/`,
`scripts/` and `data/`. The refusal is **conservative** — it re-solved rather
than reusing stale results — and the single-delta property is intact (§1). Cost
was time, not correctness. **Do not commit to `scripts/` mid-chain.**
