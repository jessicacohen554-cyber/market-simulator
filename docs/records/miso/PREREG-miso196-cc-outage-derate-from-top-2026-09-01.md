# PREREG miso-196 — `cc_outage_derate_from_top` in MISO: the tranche-grain outage-application A/B

**Session:** miso-196 (2026-09-01). **Keeper at session start and throughout:**
`2026-08-30-miso-191-bexit` (bundle `results/calibration/miso191_bax_B`),
**UNCHANGED by this document**. **Pushed BEFORE the arm exists** (rule: no
adjudicating solve quantity may precede its pre-registration).

Phase-0 rule frozen and pushed at `fef3dcb6` before any adjudicating quantity;
census record `results/calibration/_miso196_outage_derate_from_top_phase0.json`;
probe `scripts/probes/_miso196_outage_derate_from_top_phase0.py`.

---

## 1. The mechanism, and what is NOT being created

`cc_outage_derate_from_top` (`scenarios.py:11908`, bool, default `False`) —
**no new `ScenarioConfig` field, no new matrix row.** It is the
application-shape leg of the outage-overlay family, already registered as a
literal sub-scalar on the `campd_outage_windows` row (xiso-3 convention), and
already **armed on the CAISO and PJM designated keepers**. MISO's keeper runs
it `False`.

Seam: `data/fleet/arrays.py::_apply_outage_overlays` (:1050; the reallocation
block at :2251). For every `CC_REGULAR` plant with ≥ 2 LP tranches the plant's
hourly available MW — **unchanged in total** — is re-stacked bottom-up in
heat-rate order, so a partial outage truncates the expensive duct-fire / high-
econ end instead of scaling every tranche by one factor. CC_CHP is outside the
population by construction; single-tranche plants are a no-op.

## 2. Phase 0 CLEARS — every witness, at full magnitude

| witness | line (frozen ex ante) | result |
|---|---|---|
| **W1 liveness** | differing plant-hours ≥ 25% of P within the scarce set S, every year | **LIVE** — 96.3 / 95.9 / 86.0% (S); 83.8 / 83.5 / 79.0% full-year |
| **W2 drag / materiality** | positive band movement in S ≥ 1% of CC_REGULAR class pmax, every year | **MATERIAL** — 8.56 / 8.64 / 8.52% |
| **W3 conduct, MISO's own record** | CF ratio ≥ (1 + f)/2, the data-derived midpoint | **PASS — 0.9035 vs bar 0.8018** |
| **W4 C1 headroom** | floor-channel lower bound ≥ C1 headroom in a banded year ⇒ refute | **CLEAR** (2023, 2024); **N/A** 2025 (C1 record SKIPPED, no band) |
| **W5 single-delta identity** | 0 non-P rows move; plant total MW preserved to 1e-6 | **CLEAN** — 0 rows; 6.3e-16 (2023 on the warm basis, Amendment 1) |

**`CHARTER_AB = true`.**

**W3 is the structural case and it is MISO's own.** Over 1,264 partial-outage
CC windows (208,934 surviving-unit hours against 738,148 fully-available
hours), the surviving units run at **CF 0.6166** versus **0.6825** for the same
units when their plant is whole — a ratio of **0.9035**. Strict pro-rata
predicts that ratio should be ≈ **f = 0.6036**, the surviving share of plant
capacity. MISO's CAMPD record says a partially-out CC plant keeps ~90% of its
normal loading on the surviving train. That is the `from_top` premise measured
on this ISO's own conduct (rule 25 — no CAISO or PJM parameter or verdict is
transferred; the CAISO/PJM `K` is registration, not evidence here).

**W2, the object being moved** (mean MW, full-year / scarce set S):

| band | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `committed` | +840 / **+1,152** | +814 / **+1,171** | +809 / **+1,147** |
| `econ` | −54 / −147 | −9 / −116 | +0.3 / −117 |
| `peak` | −787 / **−1,005** | −805 / **−1,055** | −810 / **−1,031** |

**Provenance, reported and NOT gated** (the frozen rule declined to invent a
bar for it): of the 2025 mean availability shortfall on the P population
(9,105 MW against 27,747 MW of capacity), the **measured CAMPD overlay
supplies 65.0%** and the statistical WEFOR/POF base the remaining 35.0%. The
row def defends the mechanism as a partial-*outage* conduct rule; on MISO's
fleet that justification covers the majority — not the whole — of what it
reallocates, and this document says so on the record.

## 3. A DISCLOSED LIMIT ON W4 — the gate reads CLEAR for a reason that is not reassurance

**`CC_REGULAR` carries NO `min_gen` floor on this keeper** —
`cc_mustrun_per_plant=False`, and the class has no D-2 forced-energy row in
any year. Measured: the class-aggregate `min_gen` is **0.0 MW in both arms**,
so the arm's `min_gen` change is identically zero and W4's floor channel
**cannot bite**. Its `CLEAR` therefore rules out nothing.

This also corrects half of the row def's own justification as it applies to
MISO: "the committed floor keeps its level" describes a floor MISO does not
have. What the `committed` tranche is here is a cheap offer-curve *band*, not
a forced floor — so the mechanism reduces in MISO to a pure supply-curve shape
change, and its C1 exposure runs entirely through the **economic** channel,
which phase 0 cannot bound without a solve. That exposure is named as kill K-1
below with its ex-ante arithmetic, rather than left to be discovered after.

## 4. The A/B — one delta

- **Control** `miso196_control_A`: byte-faithful
  `replay_keeper.py results/calibration/miso191_bax_B`. Expected
  **bit-identical** to the committed keeper (the miso-193/194 lineage measured
  it exact, 12/12 sidecars); any drift is reported as branch IV.
- **Arm** `miso196_top_B`: the same replay `--set cc_outage_derate_from_top=true`.
- **Years 2023 2024 2025**, one invocation per leg, legs **sequential**
  (rule 12); **both legs registered in this session** (rule 15).
- Rule 22: no out-of-training year. MISO holds neither a `complete` nor a
  `final` marker and the holdout freeze is active.

## 5. DIRECTIONAL PREREG, with the adverse face declared

**C3a-2025 moves DOWN** (more negative than −12.3405%), **confidence 0.75**.
Mechanism: the arm strictly raises cheap CC capability and strictly lowers
expensive CC capability in exactly the hours it fires, softening the top of
the supply curve where 2025's scarce hours clear. The face is adverse on the
keeper's **sole failing criterion**, and it is declared here, before the solve.

Two independent reasons to expect it, both structural rather than fitted:
miso-193 measured that shrinking the expensive CC top band moves C3a-2025 down
(−12.3405 → −13.3304) — transferring as **shape evidence only**, since that
lever *removed* MW where this one *reallocates* them; and miso-178 measured
Δ₁ = **+10.50 (197%)**, i.e. the model's price-setter is already too efficient
(implied HR ~12 against the market's ~29), so a lever that makes efficient CC
capability more available pushes the marginal identity further in the
direction the diagnosis already calls wrong.

**MATERIALITY, honest to the lever's justification:** this lever's yardstick is
the marginal-unit identity, D-1 diurnal shape and the C8 legs — **not pp of
C3a**. **No pp threshold is pre-registered as a success criterion, and no C3a
improvement would be claimed as its justification** (rule 1 `[R-STRUCT]`). The
pp face is reported at full magnitude and routed by §7.

## 6. PRE-REGISTERED KILLS

- **K-1 — C1 fuelmix PASS→FAIL flip. `CC_REGULAR` 2024 is NAMED EX ANTE**, and
  the ex-ante arithmetic is stated so it cannot be re-litigated after: 2024
  CC_REGULAR sits at **+6.664 TWh against the ±8.00 TWh band — 1.336 TWh of
  headroom**, while the arm makes a year-mean **+814 MW** of extra cheap
  `committed` capability available. At 8,760 h that is **7.13 TWh** of newly
  in-merit cheap capability, so **a realised conversion above ~19% blows the
  band**. `ST_GAS` 2024 is the adjacent second (miso-193's K-1 fired on exactly
  this class pair; ST_GAS reached −8.08 there). 2023 carries 11.674 TWh of
  headroom; 2025's C1 record is SKIPPED and unbanded.
- **K-2** — C3b price-duration NRMSE through 0.20 in any year.
- **K-3** — any NEW D-4 off-window binding.
- **K-4** — any increase in the DOF ledger's `n_residual` (currently 37/2).

Any kill firing ⇒ the arm is **REJECTED on its own pre-registered kill**;
both legs are still registered and the finding reports every number.

## 7. ADJUDICATION POSTURE, PRE-COMMITTED (rule 1; the miso-193 precedent)

- Clean structural gates **and** an adverse C3a face ⇒ **OWNER ESCALATION**.
  Never self-promotion, never silent rejection on fit.
- The miso-193 standing owner posture directive ("structural-integrity gain may
  carry a keeper even where gates regress") is **NOT assumed to carry here**:
  miso-193 measured that it did not carry its own cap leg, and this session
  does not extend an owner directive on its own authority.
- **NOT this session's to decide** (restated, not reopened): the D-4 posture
  ruling; the miso-141 §11 nameplate-basis switch (MISO CC pmax **is** the
  net-summer rating, owner court — this lever is evaluated on that basis
  as-is); the D-2 seam-response 5(i) admissibility ruling; the class-resolved
  outage data ask; the C8 provenance-materiality floor; the RHO_CLIP band; the
  miso-189 §7.3 residue; the `correlated_forced_outage` backcast default.

## 8. THE INCIDENTAL DEFECT, and why it does not confound this A/B

Phase 0's W5 control check found a reproducibility defect in **shipped code**,
unrelated to the lever (probe docstring, Amendment 1): a control identity — the
**same config built twice** — differs on **58 rows / 7 plants / 7,722.8 MW**,
`CC_REGULAR` + `CT_PEAKER`, over **2,928 hours** (h3624–h6551 — exactly Jun 1 00:00 through
Sep 30 23:00), `pmax` identical, max availability delta **0.1088**, the first build carrying
**+1,544.1 GWh** (mean **+527.4 MW** across the summer window) more capability
than every later one.

Root cause: `_CC_PMAX_RECONCILED_PLANTS` (`data/fleet/eia860.py:776`, written
:875) is a **last-writer-wins module global keyed only by ISO**, written by
every fleet-record load — including narrow auxiliary loads whose record set
legitimately reconciles nothing. The traced sequence is
`_iso_plant_capacity → load_retired_within_window` writing `MISO=[]` *after*
the main `load_fleet_from_csv` wrote the correct seven plants; that call is
cached, so it clobbers on the **first** build only. `_basis_aware_suppresses`
(`arrays.py:463`) then reads the empty set under the armed
`summer_derate_basis_aware` and **suppresses the flat summer ambient derate for
the seven plants that should keep it**. Whether those plants are derated
depends on lru_cache warm-up order, not on data.

**Why the A/B is unconfounded:** control and arm are solved by the same driver
in the same order, so the state is identical on both sides and the delta
remains single. The control leg additionally *tests* the question — if the
replay reproduces the committed keeper bit-identically across all three years,
the shipped path is at least stable and reproducible in its own order.

**Not fixed here, and deliberately so:** the repair is a solve-affecting change
to core fleet code that would re-base a designated keeper's summer
availability. That needs its own charter, PREREG and A/B — not a side edit in a
lever session (rule: one lever per session). It is reported at full magnitude
and named as this session's successor. **Whether the keeper's own committed
2023 solve is affected is NOT asserted here** — it depends on the runner's call
order, which this session did not measure; the control leg is the evidence that
will speak to it.

## 9. Reproduction

```
python3 scripts/probes/_miso196_outage_derate_from_top_phase0.py
python3 scripts/replay_keeper.py results/calibration/miso191_bax_B \
    --out-dir results/calibration/miso196_control_A --years 2023 2024 2025
python3 scripts/replay_keeper.py results/calibration/miso191_bax_B \
    --out-dir results/calibration/miso196_top_B --years 2023 2024 2025 \
    --set cc_outage_derate_from_top=true
```
