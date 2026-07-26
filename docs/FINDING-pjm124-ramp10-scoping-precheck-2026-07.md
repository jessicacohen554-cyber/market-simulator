# FINDING — pjm-124: `ramp10` deliverability scoping cannot tighten PJM's reserve balance (2026-07-26)

**Verdict: framing 2 is REFUTED — NO SOLVE SPENT.** The candidate named in
`docs/FINDING-pjm120-c3a-extreme-tail-depth-2026-07.md` §7 ("scope `ramp10`
deliverability to genuinely committed-and-online capacity rather than the
availability-scaled fleet") fails its own pre-registered K1 magnitude gate in
**all three keeper years, unanimously**, by roughly a factor of three.

Adjudicated entirely no-LP, on the pjm-121 §5 / pjm-123 pattern. The kill
criteria were written into
`scripts/probes/pjm124_ramp10_scope_precheck.py`'s module docstring and
**committed before the probe was run** (commit `84288c3`); the numbers below
come from the run that followed.

---

## 1. The one-line reason

**45 % of the keeper's deliverable ramp belongs to iron the mechanism is not
allowed to remove**, and the remainder is still ~5× the requirement.

The keeper's balance families are **Primary** Reserve (RTO + Mid-Atlantic/
Dominion subzone). Under Manual 11 §4.2, Primary = Synchronized **+
Non-Synchronized**, and Non-Synchronized reserve *is by definition offline
capacity that can start and deliver within 10 minutes* — a fast-start CT. A
commitment-state scoping of a Primary balance may therefore remove offline
**non**-fast-start iron (a cold CC/ST backs nothing) but may **not** remove
offline fast-start iron: it counts in either commitment state.

That makes the fast-start term a hard floor on the scoped supply, computable
with **no P0 dispatch and no LP at all**:

```
F(t) = Σ over FAST-START members of ramp10 × availability(t)   ≤   S_scoped(t)
```

Measured on the reconstructed keeper fleet: **1,411 fast-start members,
30.6 GW nameplate, F = 17.6 GW mean — 45 % of the 38.9 GW keeper cap and
already 5.2× the 3.35 GW Primary requirement, by itself.**

## 2. The measured table (all three keeper years, `pjm121_ccbelt`)

Two further dispatch-free terms tighten the bound: `MG` (non-fast members
carrying a positive `min_gen` floor are online by construction — P0 solves the
same floors) and `DISP` (a greedy lower bound on non-fast online capacity
implied by the keeper's own committed P1 class-hourly dispatch: a class
producing D MW must have ≥ D MW of iron synchronized, and the ramp-minimal way
to supply it is to load the lowest ramp-ratio plants first).

| GW, annual mean | 2023 | 2024 | 2025 |
|---|---|---|---|
| measured Primary requirement **R** (RTO) | 3.09 | 3.42 | 3.35 |
| **A** keeper cap (all availability-scaled members) | 38.74 | 38.67 | 38.95 |
| **F** fast-start floor (untouchable) | 17.54 | 17.57 | 17.57 |
| **MG** min-gen-floored online | 9.44 | 9.42 | 9.56 |
| **DISP** dispatch-implied online | 15.02 | 15.59 | 16.07 |
| **S_lower = F + max(MG, DISP)** | **32.56** | **33.17** | **33.64** |
| S_lower ÷ R | **10.5×** | **9.7×** | **10.0×** |
| reduction vs the keeper cap | 15.9 % | 14.2 % | 13.6 % |
| tight-bin hours with S_lower ≤ 2×R | **0 of 2,191** | **0 of 2,190** | **0 of 2,190** |

`S_lower` is a **rigorous lower bound** — the most generous possible accounting
of what the mechanism can remove. The realistic (P0-derived) value is larger.
That is what makes the verdict valid without ever solving for the true online
pattern: if the best case leaves the balance 10× slack, the real case cannot do
better.

## 3. Verdict against the pre-registered criteria

| criterion | 2023 | 2024 | 2025 |
|---|---|---|---|
| **K1 MAGNITUDE** (PASS needs mean ≤ 3×R **and** ≥ 50 tight-bin hours ≤ 2×R) | **KILL** 10.5× | **KILL** 9.7× | **KILL** 10.0× |
| **K2 STATE-DEPENDENCE** (≥ 10 pp slack-vs-tight spread) | PASS 10.8 pp | PASS 10.6 pp | KILL 9.8 pp |
| **K3 ADMISSIBILITY** (rule 13) | PASS | PASS | PASS |
| verdict | NO SOLVE | NO SOLVE | NO SOLVE |

**K1 is the decisive gate and it kills unanimously**, by ~3× the PASS band. The
mechanism does not even reach the PARTIAL band (which required a ≥ 50 %
reduction; the measured reduction is 13.6–15.9 %).

**K2 is reported honestly as split and marginal** — 10.8 / 10.6 / 9.8 pp against
a 10 pp threshold — and it does not matter, because K1 already kills. What *is*
substantive in the K2 row is the **sign**: the reduction runs 18–21 % in the
slackest net-load quartile and only 8–10 % in the tightest.

| reduction fraction by net-load quartile | bin0 (slack) | bin1 | bin2 | bin3 (tight) |
|---|---|---|---|---|
| 2023 | 21.0 % | 17.5 % | 15.9 % | 10.1 % |
| 2024 | 18.8 % | 16.0 % | 14.6 % | 8.3 % |
| 2025 | 18.4 % | 14.6 % | 13.7 % | 8.6 % |

This is physically correct and diagnostically fatal: in tight hours nearly
everything is already committed, so a commitment-state scoping has almost
nothing left to remove **exactly where PJM's residual lives**. The mechanism
shaves hardest in the hours that were never the problem.

**K3 passes** — the scoping is derivable from fleet physics (the rule-18
capacity-weighted fast-start flags) plus the model's own dispatch. No measured
reserve clearing, price, or other measured outcome enters; the measured PJM
series is read only for the *requirement*, a published Manual 13 reliability
quantity already in the keeper. Framing 2 was never inadmissible — it is simply
**inert**.

## 4. The strict variant is closed too — and it was never admissible

The obvious next move is to scope strictly to *online* iron, deleting the
offline fast-start ramp. Two independent reasons close it:

* **It is a product mismatch, not a repair.** Deleting non-synchronized supply
  from a **Primary** balance prices Synchronized reserve while calling it
  Primary. That is making reserve artificially scarce by mislabelling the
  product — the exact rule-1 failure the charter warns against. (The *legitimate*
  way to price the two products separately is `pjm_reserve_pergen_sync`, which
  partitions the same supply into SYNC and NON-SYNC columns without deleting
  any of it — already closed on the keeper's own persisted dual, pjm-120 §6.1,
  and memory-infeasible besides.)
* **It would not work anyway.** Its own lower bound is `max(MG, DISP)`:
  **15.0 / 15.6 / 16.1 GW = 4.9× / 4.6× / 4.8× the requirement** in 2023 /
  2024 / 2025. Even after deleting all 17.6 GW of fast-start ramp, the balance
  still carries nearly five times the reserve it needs.

**The whole framing-2 family is therefore closed — in its admissible form and
in its inadmissible one.**

## 5. The corroborating number the charter asked for

The single most diagnostic quantity in the lane, read from the keeper's own
committed `hourly/system_<year>.parquet::reserve_price` with **no re-solve** —
and now extended from pjm-120's 2025-only reading to all three keeper years:

| model reserve dual (max across zones per hour) | 2023 | 2024 | 2025 |
|---|---|---|---|
| hours with any nonzero dual | **0** | **0** | 22 |
| hours ≥ $300 (ORDC step 2) | **0** | **0** | **0** |
| hours ≥ $850 (ORDC step 1) | **0** | **0** | **0** |
| max / mean | $0.00 / $0.000 | $0.00 / $0.000 | $210.99 / $0.151 |

**Zero hours reach $300 in 26,280 hours.** In 2023 and 2024 the reserve balance
is *never* even marginally binding — the dual is identically zero all year. The
sub-shortage regime pjm-120 measured in 2025 is the *tightest* of the three
years, not a representative one.

## 6. What this means for the frontier ledger

**This is the "partial/negative" outcome the charter said would advance the
declaration as much as a positive one — and it lands harder than partial.**
Framing 2 is not merely insufficient; the pre-check identifies *why* the supply
side cannot be closed by any commitment-state scoping:

1. **~45 % of the deliverable ramp is tariff-protected.** Offline fast-start
   capacity is non-synchronized Primary reserve by Manual 11 §4.2. No
   commitment mechanism can remove it without modelling a different product.
2. **The remaining ~55 % is mostly online anyway in the hours that matter.**
   `MG + DISP` alone is 4.6–4.9× the requirement, and the scoping's bite falls
   off precisely as net load tightens.
3. **So the slack is not a commitment artifact.** It is the *size of PJM's
   reserve-eligible fast-ramping fleet relative to a ~3.4 GW requirement.* That
   is a real property of the fleet, not a modelling error — which is why no
   admissible mechanism removes it.

Point 3 is the substantive addition to the ledger. pjm-82 attributed the
headroom to the LP-vs-MIP boundary (a continuous `U` holding fractional online
capacity at near-zero cost). This pre-check shows that attribution is
**incomplete in the model's favour**: even with commitment state read exactly,
and even counting only iron the tariff lets us count, the balance stays ~10×
slack. **A MIP would not close this gate either.** The requirement is simply
small relative to the fleet that can serve it.

That relocates the remaining >$200 residual off the reserve *supply* side
entirely. What PJM actually prints in those hours ($1,722 at h4193 against a
model dual of $210.99 and a model any-zone energy price of $675.3) is being set
by something other than a Primary-reserve shortage the model could reproduce by
tightening supply.

**Frontier readiness is flagged, not declared** (frontier is owner-declared).
Lane 1's framing 2 is now on record as tried and closed. Framing 1 (constrain
perfect-foresight all-online commitment before the reserve bound is read,
pjm-125) remains open as a named admissible mechanism — but §6 point 3 above is
a strong prior that it will land the same way, since it addresses the same
online/offline distinction that this pre-check just measured to be worth
13.6–15.9 % of a 10× surplus.

## 7. Guardrail review

* **Rule 1** — no mechanism was promoted or rejected on whether a residual
  moved; framing 2 is rejected because the capacity it can remove is not the
  capacity that creates the slack, and the strict variant is rejected on
  product-definition grounds *before* its (also failing) magnitude was read.
* **Rule 13** — every quantity is a fleet-physics or published-tariff input
  with a forward analogue. No measured outcome is pinned; the measured PJM
  series enters only as the requirement, which the keeper already consumes.
* **Rule 16** — all three keeper years (2023 / 2024 / 2025) were measured, not
  one. No dashboard registration is claimed: **no solve was run**, so there is
  no bundle to register (the pjm-123 precedent).
* **Rule 19** — the closed `pjm_reserve_pergen_sync` product split is
  distinguished from this scoping rather than conflated with it; neither is
  stacked on the other.
* **Rule 22** — 2023–2025 only. PJM has no calibration-complete marker; no
  out-of-training year was touched.
* **Falsifiability** — K1/K2/K3 and their bands were committed to git before
  the probe ran. K2's split verdict is reported as split rather than rounded
  into agreement.

## 8. Reproduction

Container starts empty; ~4 min per year, no LP:

```
uv sync
python scripts/regenerate_clean.py transfer-interface-limits ramp-capability lmp
python scripts/data/fetch_pjm_da_virtuals.py --years 2023 2024 2025 --feeds hrl_da_incs_decs
for y in 2023 2024 2025; do
  python scripts/probes/pjm124_ramp10_scope_precheck.py \
    results/calibration/pjm121_ccbelt --year $y \
    --json-out results/calibration/pjm124_precheck_$y.json
done
```

The reserve-dual table (§5) needs no reconstruction at all — it reads the
committed keeper sidecars directly.

## Pointers

* Charter and ledger: `docs/handoffs/pjm-frontier-path-2026-07.md` §2–§4.
* The framing this closes: `docs/FINDING-pjm120-c3a-extreme-tail-depth-2026-07.md`
  §7, framing 2 (framing 1 stays open as pjm-125).
* The LP-vs-MIP attribution this qualifies: pjm-82, and
  `docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md` §B.3–B.4.
* Wiring precedent the framing would have used:
  `market_sim.pipeline.commitment.build_pjm_reserve_p1_prep` (path B) and
  `pjm_pergen_sync_reserve_caps`.
* Shared reconstruction helper promoted by this session:
  `scripts/lib/bundle_fleet.py` (frontier handoff §5 housekeeping).
