# PRE-REGISTRATION — pjm-134 `pjm_apsouth_interface_cut` (single delta)

**Written and committed BEFORE either arm was solved.** No arm result existed
when this document was frozen. Gates below are final — a gate this document
does not contain cannot be quoted as a pass. Format follows
`PREREG-pjm133-hydro-budget-nameplate-aware-2026-07-27.md`, **mirrored, not
copied**.

Chartered by `FINDING-pjm134-dominion-zonal-inversion-2026-07-27.md`, which ran
both ASK-pjm134 §4 no-LP tests: **C1 (zonal gas basis) is REFUTED** — the model's
basis is measured-faithful on its own zone boundary and if anything *understates*
Dominion's premium — and **C2 (transfer capability) FIRES**: the keeper's PJM
clears as a copper-plate, Dominion sitting at its neighbours' dual in **100.0 %
of 26,280 hours**, while PJM's own DA congestion separates DOM from AEP-DAYTON
by >$1 in ~50–63 % of hours.

**Promotion is NOT pre-granted** and is not requested by this session. It remains
a separate owner act, and (rule 22 `[R-HOLDOUT]`) a structural mechanism change
is scored leave-one-year-out within 2023–2025 before any promotion.

---

## §1 — the delta (ONE switch, one mechanism, ZERO new free parameters)

**Arm B** = the keeper recipe replayed at this session's HEAD **plus the single
flag**:

```
scripts/replay_keeper.py results/calibration/pjm121_ccbelt \
    --out-dir results/calibration/pjm134_apsouth_B \
    --set pjm_apsouth_interface_cut=true \
    --note "pjm-134 measured AP-South joint western->MAD interface cut (single delta)"
```

- **Arm A** `results/calibration/pjm134_control_A` — keeper recipe, no delta,
  same HEAD, same container, same regenerated `clean` tree (regenerated before
  either solve). NOT a keeper candidate; registered as the run explorer's
  control arm per rule 15.
- Both arms `--year 2023 2024 2025` in ONE invocation (rule 16), years
  **sequential** within each run, arms **sequential** to each other (rule 12 +
  the pjm-133 §9 memory fact: a PJM per-plant year-solve peaks at 14.8–15.2 GB).
- Nothing else is bundled with this delta (ASK-pjm134 §5).

**Base-recipe note, stated up front.** The designated PJM keeper is
`2026-07-27-pjm-133-nameplate`, which carries one further flag
(`hydro_budget_nameplate_aware`). This A/B is deliberately run on the **pjm-121
recipe** per the session charter, so arm A is byte-comparable to the
pjm-129/pjm-132 control lineage. The delta is orthogonal to the hydro flag
(a transfer-interface constraint vs a hydro budget allocation); re-basing onto
the pjm-133 recipe is a promotion-time step, not a validity condition for this
comparison.

**What the flag does** (`model/interchange/pjm.py::build_pjm_apsouth_interface_cut_groups`,
`data/transfer_interface_limits.py::pjm_apsouth_interface_hourly`): ONE
one-sided aggregate interface-group row per hour caps the summed eastward flow

```
Flow(West_APS -> SWMAAC) + Flow(West_APS -> Dominion)  <=  AP-South(t)
```

at the hour's measured AP-South published transfer limit — the elementwise MIN
of the pre- and post-contingency postings, both simultaneously-enforced security
limits. It is the **exact construction, and the same Manual-03 provenance**, as
the already-shipped and already-keeper-resident `pjm_east_interface_cut`
(`build_pjm_east_interface_cut_groups`), which FINDING-pjm134 §2 measures as the
**only** internal PJM cut that ever binds today.

- **DRIVER (rule 14 `[R-ACCURATE]`)**: `constants.PJM_INTERFACE_LINK_MAP`'s own
  note already flags the misalignment — *"AP-South is the aggregate western→MAD
  500 kV flowgate, one of several parallel paths this 8-zone mesh splits across
  West_APS→SWMAAC and West_APS→Dominion"* — yet the per-link overlay applies it
  to West_APS→SWMAAC alone while the parallel West_APS→Dominion path rides a
  3,000 MW static. The LP's west→MAD capability is therefore
  `AP-South(t) + 3,000 MW ≈ 6,900` against a published ~3,900 flowgate, and
  every megawatt of the excess is Dominion-facing.
- **DOF added: zero** (rule 24 `[R-DOF]`). The cap is the published hourly
  series verbatim. There is no scale, percentile, haircut or blend anywhere in
  the mechanism.
- **Rule 13 `[R-MEASURED]`**: no outcome is pinned. A published operating-security
  transfer limit regenerates every year from the same Data Miner 2 feed and
  responds to changed grid conditions; forecast years keep the static seeds
  (the two-track construction `pjm_measured_interface_limits` already uses).
- **Rule 19 `[R-ONE-MECH]`**: this **REPLACES** the flagged misalignment, it does
  not stack. The joint cap dominates the surviving per-link AP-South bound (a
  sum below the limit implies each term is), so that overlay becomes redundant
  rather than additive. No new floor is added to any class.
- **Rule 25 `[R-ISO-SCOPE]`**: gated on `config.iso == "PJM"`; every other ISO
  and all forecasts are byte-identical.
- **Rule 1 `[R-STRUCT]`**: this is chartered because it is structurally correct,
  **not** because it is predicted to close the Dominion residual. §4's INERT
  outcome is a publishable result, not a failure to be re-tuned away.

## §2 — the baseline this is measured against (arm A, pre-declared)

| quantity, arm A expectation | 2023 | 2024 | 2025 |
|---|---|---|---|
| Dominion price-separated from ≥1 neighbour | 0.0 % | 0.0 % | 0.0 % |
| ISO-wide single-price hours | 95.5 % | 97.3 % | 96.2 % |
| slack / dump | 0 / 0 MWh | 0 / 0 | 0 / 0 |
| Dominion fossil Δ (model − EIA-923) | −20.0 TWh | −19.8 | −12.1 |
| Dominion CT_PEAKER (model / actual TWh) | 0.70 / 7.38 | 1.28 / 8.68 | 2.62 / 9.64 |
| Dominion CC_REGULAR (model / actual TWh) | 29.33 / 41.70 | 38.46 / 49.27 | 45.67 / 49.23 |

**Arm-A identity check (pre-declared, K5 below):** arm A must reproduce
`pjm132_control_A` — and therefore `pjm129_meritguard_a1` — to **0.000000 MW on
every class, every hour, all three years**. Arm A is NOT compared to the
committed `pjm121_ccbelt` bundle (FINDING-pjm133 §2: that bundle sits on the
pre-guard outage envelope).

**Envelope expectation, pre-declared so it cannot be mistaken for the delta:**
both arms are expected to score **NOT-YET** with **C1 / C3a / C3c FAIL** on the
corrected outage envelope. That is the pre-existing pjm-129 determination, not
this delta's doing.

## §3 — PRIMARY (structural, sign-based, not a fit target)

The PRIMARY is that **the mechanism engages and engages in the measured
direction**. It is deliberately NOT a volume or price target: rule 1 forbids
judging a structurally-correct mechanism by the residual.

**P1 — engagement.** In every year, the joint cut binds: Dominion price-separates
from at least one of its three neighbours in **> 0 %** of hours (arm A: exactly
0.0 %, 0 of 26,280).

**P2 — measured direction.** In every year, conditional on Dominion separating
from AEP_Ohio, Dominion is the **dearer** side in **≥ 2/3** of those hours.
Grounding, not fitting: PJM's published DA congestion has DOM dearer in
55.9 / 42.8 / 49.9 % of all hours against cheaper in 3.3 / 6.7 / 12.8 %, i.e.
dearer in **94 / 86 / 80 %** of separated hours. The 2/3 floor sits well under
the measured value in every year and tests the *sign asymmetry*, not its size.

**P3 — no counterflow forcing.** The hourly cap array is ≥ 0 in every hour
(non-positive postings clamp to 0, never negative), and westward flow keeps the
per-link TTCs. Verified from the limit array and the group's one-sided
(`bidirectional=False`) construction.

**Reported, NOT gated (rule 1):** Dominion CT_PEAKER / CC_REGULAR volume gaps,
the zonal displacement table, the ISO-wide fossil balance, and every rubric
criterion. These are the *interesting* numbers and they are published whatever
they say — they are not the delta's pass condition.

## §4 — the INERT outcome is pre-registered

If P1 fails — the joint cut never binds — the delta is **INERT** and is written
up and registered as such (the pjm-132 precedent). An inert result means the
model's west→MAD flows sit below ~3,900 MW even unconstrained, i.e. Dominion's
excess imports arrive by a different path, and the next ASK is *which* path.

**No-feedback ceiling (binding on this session and any follow-up):** there is
nothing in this mechanism to re-parameterise, and nothing may be added. In
particular, **no multiplier, percentile, haircut, blend, or scale factor may be
applied to the published AP-South series**, in this session or a successor,
whatever the result. A cut that does not fire is a discovered fact about the
flow pattern, not a knob set too loose. Extending the joint-cut construction to
a *different* published interface is a new charter with its own prereg, never a
retune of this one.

## §5 — pre-registered kills (structural failure modes, not residual movement)

| id | test | threshold | fires ⇒ |
|---|---|---|---|
| **K1** | **C3a guard** — the standard house no-feedback ceiling | C3a degrades by more than **+0.75 pp** in any year | report the degradation prominently; delta is not promotable without root-cause |
| **K2** | **load shedding** — a mis-specified cut starves the east | arm B `slack` > 0 or `dump` > 0 MWh in any year (arm A: exactly 0 / 0) | **KILL.** A published security limit must never make the reduced network infeasible; this means the cut is wrong for this topology |
| **K3** | **counterflow forcing** | any hour's cap < 0, or any westward flow bound changed | **KILL.** Violates P3 and the mechanism's own contract |
| **K4** | **determination regression** | arm B's rubric determination class is worse than arm A's | report; not an automatic kill (rule 1), but blocks promotion pending root-cause |
| **K5** | **arm-A identity** | arm A differs from `pjm132_control_A` by more than 0.000000 MW on any class-hour | **KILL the comparison** — the A/B is not single-delta and must be re-solved |

**K1's asymmetry is deliberate.** C3a is a *guard*, not a target: it exists so a
structural change cannot buy its structure by wrecking the price tail. It is
reported in both directions and is never optimised toward.

## §6 — instruments, committed with this prereg

- `scripts/probes/_pjm134_c1_zonal_gas_basis.py` — C1, no LP.
- `scripts/probes/_pjm134_c2_dominion_interface.py` — C2, no LP; also the
  arm-A baseline in §2 and the P1/P2 scorer's separation machinery.
- `scripts/probes/_pjm134_apsouth_ab.py` — the A/B scorer (committed before the
  arms solve; reads both bundles' `hourly/` sidecars, no replay). Machine
  output: `results/probes/pjm134_apsouth_ab.json`.
- `legitimacy_diagnostics.json` generated for **BOTH** arms before scoring.

## §7 — what this prereg does NOT authorise

- Any change to the AEP/DOM crosswalk or its limit (FINDING-pjm134 §3: measured
  at 41–51 % median utilisation, ≤ 1.4 % of hours past 90 % — it is not the
  constraint that separates Dominion).
- Any use of DOM LDA CETL as an hourly energy cap (wrong construct; published
  only as a lower bound for two of the three scored years).
- Any re-opening of C1 / the zonal gas basis (refuted, FINDING-pjm134 §1/§5).
- Any bundling with the hydro nameplate flag or anything else.
- Any solve, scoring or registration outside 2023–2025 (rule 22 `[R-HOLDOUT]`).
