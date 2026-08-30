# FINDING — D11-R: the margin-exhaustion entry volume rule, productionized and A/B'd

_2026-08-30 · capacity-expansion (Forecast Finalization) track, lane D11-R ·
chartered by the owner's card-B signature (B-C, 2026-08-25,
`docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md` §5), re-scoped by
the director at refresh #8 on the forward-expectation A/B's evidence
(`docs/handoffs/capx-director-ledger-2026-08.md` §0e.3). Branch
`claude/capx-d11r-entry-volume-rule`._

**What this lane did:** productionized the L-1b margin-exhaustion closure —
*build until the screen's own repriced margin is exhausted, bounded by the same
caps* (`docs/FINDING-entry-signal-l1-2026-08.md` §2, probe
`scripts/probes/entry_signal_l1b_allocator_counterfactual.py`) — behind the NEW
default-OFF `ScenarioConfig.entry_margin_exhaustion`, applying to BOTH entry
allocators (thermal/VRE and storage; one mechanism, one field, rule 19
`[R-ONE-MECH]`), and measured it arm-vs-control on the ERCOT
`ercot-2021-2025-realized` T1-H leg at the registered posture, same HEAD.
No signal construction was built (the shipped `entry_lookahead_reprice=True`
default HOLDS; its cell and `entry_forward_expectation_signal`'s are
untouched); the pro-forma/scarcity-basis question stays the separate
owner-gated D12 rung.

---

## 1. Phase 0 — the probe reconciled to the live allocators (zero-DOF CONFIRMED)

### 1.1 What the offline counterfactual did, exactly

| element | probe construction |
|---|---|
| tranche | 250 MW fixed tranches (`TRANCHE_MW`), a resolution constant — halving it measured to move no reported GW by more than one tranche (finding §2.1) |
| repricing step | after each tranche, the ENTERING-year signal rebuilt from the committed dump's own stack construction: base merit price (`mc_sorted`/`cap_sorted` searchsorted) **delta-anchored to the dump's base price**, plus the model's own `ercot_lookahead_expected_ordc_adder` on the amended reserve state; 0.0 max abs error reproduction of all four dumps at zero delta |
| thermal increment | stack append at the entrant's variable cost, capacity × (1 − `EFORD[tech]`); capacity reaches reserves in the (measured 100 %) headroom-bound top-adder hours |
| storage increment | merchant share `(1 − ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC)` through the model's own `_storage_peak_shave_net_load`; AS share into reserves |
| cap interaction | the SAME caps — per-tech queue caps + growth ladder + shared ISO budget (thermal); `STORAGE_ANNUAL_BUILD_CAP_MW` / share cap / deployment ceiling (storage, its own budget) |
| screens | both, INTERLEAVED in one walk: candidates {gas_cc, gas_ct} + all six storage techs, best margin per tranche |
| margin construction | thermal: energy leg only, `Σ max(sig − vc, 0) − fixed` (the reserve-leg bound reported separately, not walked); storage: `estimate_storage_revenue(sig) − cost` at ERCOT zeros for capacity/AS |
| VRE | held at shipped in both arms (offline-harness artifact: ELCC deltas cancel in the RM comparison) |
| stop rule | no candidate's repriced margin > 0, or every cap binds |

### 1.2 What the live equivalent must do — the six reconciliation items

1. **The repricing instrument exists in the live code as
   `runner._lookahead_reprice_signal`** — so the live walk re-invokes the SAME
   function, never a model of it. The walk's additions enter through the
   model's own seams: a new `extra_stack=(mc_1d, cap_1d)` argument (the exact
   append pattern the FFR-5C pipeline rows use), a new `extra_vre` (T,) term
   (the `pipeline_vre` pattern), and the EXISTING `storage_shave` +
   `scarcity_restoration["storage_as_mw"]` parameters for storage. At zero
   additions the closure reproduces the seam's own signal call bitwise, which
   anchors the delta construction exactly — the probe's own trick, carried
   verbatim.
2. **Delta anchoring through the blend and the composition.** The signal the
   screens consume is affine in S_entering through both the EWMA blend
   (`entry_price_signal_alpha`) and the forward-expectation composition, so
   the walk signal is `consumed + α × (S(state) − S(0))` — exact arithmetic,
   α = 1.0 at the registered posture.
3. **Sequential screens, one shared state.** The live architecture decides
   thermal/VRE (`evolve_fleet` step 5) BEFORE storage
   (`apply_storage_new_entry`); the probe interleaved them. The walk carries
   ONE repricer state (`_EntryRepriceWalk`) across both calls — the storage
   walk starts from the thermal-amended signal. The interleaving never
   determined an outcome in any measured L-1b step (storage cleared only in
   2023, where the caps bound under both rules), so
   sequential-with-shared-state reproduces every measured probe decision.
4. **The reserve leg — the one construction Phase 0 had to add, and why it is
   zero-DOF.** The live thermal margin is `Σ max(price − vc, r)` with `r` the
   prior year's REALIZED post-solve ORDC adder (`screen_reserve_value_enabled`,
   the registered posture). The probe's walk had no reserve leg. Held frozen,
   the leg is an inexhaustible floor: the walk could never exhaust in
   reserve-carried years and would reproduce bang-bang exactly where the probe
   measured the largest damping (entering-2024, the FFR-9B "reserve-leg-
   carried" decision). The closure: shift the leg by the SAME within-walk
   delta of the signal's own expected-ORDC adder, floored at zero (reserve
   prices are non-negative — the curve's own range, not a parameter):
   `r_walk = max(0, r + Δadder)`. This is a within-instrument, WITHIN-YEAR
   difference — zero at walk start, so the screen's bang-bang margins are
   reproduced exactly before any tranche — and is NOT the cross-basis
   two-scarcity-objects subtraction the forward-expectation finding §4
   measured as a defect (only the delta crosses, and it is zero at anchor).
5. **Candidates beyond the probe's set.** Every live candidate class gets the
   increment the screen's own representation implies: wind/solar at their
   screened CF basis (the build zone's hourly profile, or the scalar base-CF
   fallback) into the net-load VRE term; must-run and emerging candidates
   (screened as flat-CF output at the mean price) as flat CF-shaped net-load
   reduction. Saturating annual credits that are functions of fleet MW — the
   storage AS rate and the storage capacity value — are evaluated at
   (existing + walk-built) MW: the model's own response curves, walked, not
   new coefficients. Two stated bounds, both inactive in the ERCOT A/B
   posture: the thermal capacity payment / `reserve_position` is not repriced
   within the walk (ERCOT prices capacity at zero), and the endogenous
   storage-AS scalar (`ercot_storage_as_endogenous`, off at the posture) has
   no response function to walk.
6. **Cap identity and the partial final tranche.** The walk consumes the same
   trackers (group caps, ladder, ISO budget, procured + pending netting)
   tranche by tranche, and the FINAL tranche may be partial so a cap binds
   exactly where the bang-bang build would (removing the probe's
   1,500-vs-1,571 quantization note); totals then route through the SAME
   commissioning code (COD-lag pipeline rows / in-year units / VRE pools).

### 1.3 The zero-DOF audit (the Phase-0 stop condition, not hit)

Every quantity in the exhaustion condition already exists in the screen: the
signal and its repricing instrument, the variable costs, EFORD, the caps, the
shave/AS split constant, the saturation curves. The two candidate free
parameters were examined and neither moves the answer:

- **Tranche size** — carried verbatim from the probe as
  `entry_config.ENTRY_EXHAUSTION_TRANCHE_MW = 250.0`, a resolution constant:
  the probe measured half-step invariance offline, and
  `tests/unit/model/test_entry_margin_exhaustion.py::test_tranche_resolution_invariance`
  re-asserts the property on the live walk (halving moves no tech's build by
  more than one tranche).
- **Step count** — the iteration bound derives from the budgets (ISO budget in
  whole tranches + one partial per candidate), never a chosen count.

**Phase 0 verdict: zero-DOF CONFIRMED — proceed.** (The honourable-exit stop
was not needed.)

## 2. The implementation

`entry_margin_exhaustion: bool = False` (GATED default-OFF; cache-key
registered at its default per the nyiso-119 discipline — the default key
`603c2498bf71d21d` is unchanged, an armed run hashes distinctly; requires
`entry_lookahead_reprice`, refused otherwise in `__post_init__` — the FFR-8A
pattern; coerced off in a plain backcast alongside the reprice). In
`run_config.json` via the standard serialization (rule 24), `FromConfig` in
the hindcast harness record (FFR-3R), CLI `--entry-margin-exhaustion` /
`--no-entry-margin-exhaustion` on `scripts/run_capacity_hindcast.py`.

| piece | where |
|---|---|
| walk state (one per priced entering year) | `runner._EntryRepriceWalk`; built at the `_screen_signal_for` seam over a closure re-invoking `_lookahead_reprice_signal`; threaded via `prior_results.entry_reprice`, rebound per entering year (the unified-signal swap pattern) |
| instrument seams | `_lookahead_reprice_signal(extra_stack=, extra_vre=)` — both default `None`, byte-identical |
| thermal/VRE walk | `new_entry.apply_economic_new_entry(entry_reprice=)` — per-candidate re-evaluation records captured during the ordinary screening pass (no non-price term recomputed); the bang-bang loop is untouched when unarmed |
| storage walk | `storage.apply_storage_new_entry(entry_reprice=)` — the shared `_stack_margin` construction re-called per tranche at the repriced signal and walk-grown fleet MW; the winner-take-share split untouched when unarmed |
| tranche constant | `entry_config.ENTRY_EXHAUSTION_TRANCHE_MW = 250.0` (citation in place) |
| tests | `tests/unit/model/test_entry_margin_exhaustion.py` — 14 tests: config registration/refusal/coercion; INERT-repricer walk ≡ bang-bang totals exactly (both allocators — the walk changes volumes only through repricing feedback); depressing repricer exhausts below the caps (both); tranche invariance; the reserve-leg floor path; the real walk object over the real instrument (bitwise zero anchor, downward pricing, α scaling) |
| regression | 200 entry/storage/signal-suite tests + 834 model/config tests pass; `check_mechanism_matrix.py` clean |

## 3. The A/B — ERCOT T1-H, arm vs control, same HEAD

### 3.1 Posture, verified

Both invocations solved by this session on one HEAD (branch
`claude/capx-d11r-entry-volume-rule`, base `origin/main` @ `4c13fa2` + this
lane's mechanism commit), concurrently (rule 12), years sequential within
each; solved [2021, 2023, 2024, 2025], bridged [2022]. **The control (bare
invocation) reproduces the committed registered posture EXACTLY**: cache key
`28cef3500ec1fd9e` (the t1h-refresh / fwd-exp bracket key), RM path
19.00 → 8.54 → 14.65 → 25.19 to the basis point, and the committed additions
table verbatim (0.350 / 17.987 / 9.000 / 7.571 / 5.000 GW) — zero HEAD drift
on the fleet side, so every committed bracket is a valid anchor. The arm
differs in EXACTLY one `run_config` field (`entry_margin_exhaustion:
False → True`, key `cc7bbe1170db65c2`); the probe
(`scripts/probes/entry_volume_rule_compare.py`,
artifact `results/calibration/entry_volume_rule_ab_ercot.json`) hard-fails
unless that single-delta condition holds. Both arms registered on the
FORECAST namespace with `run_config.json` committed (FC-7):
`ercot-2021-2025-realized-t1h-d11r-{control,exhaustion}`; the backcast
registry untouched (rule 15).

### 3.2 Per-step decisions

| ledger year | control (bang-bang, = the committed bracket) | margin-exhaustion arm |
|---|---|---|
| 2022 (bridge) | gas_cc 3,000 · gas_ct 1,571 · solar 4,946.6 | gas_cc 3,000 · gas_ct 1,571 · **solar 1,250** |
| 2023 | gas 3,000/3,000 · solar 5,550 · iron_air 3,000 + flow 2,000 | gas 3,000/3,000 · solar 4,946.6 · **wind 603.4** · **iron_air 3,000 only** |
| 2024 | gas 3,000/3,000 · solar 6,000 | gas 3,000/3,000 · **no solar** |
| 2025 | — (nothing clears) | **gas_cc 3,000 · gas_ct 3,000** (COD 2027, outside the ledger window) |
| RM path | 19.00 → 8.54 → 14.65 → **25.19** | 19.00 → **6.35** → 11.55 → **22.02** |
| swings (pp) | −10.46 / +6.11 / +10.54 | **−12.65 / +5.20 / +10.47** |

### 3.3 The four anchors, and where the live closure lands

| construction | terminal RM % |
|---|--:|
| shipped bang-bang (control, committed + reproduced) | 25.19 |
| disarm raw duals (committed) | 40.24 |
| forward-expectation (committed) | 40.38 |
| **L-1b offline margin-exhaustion (open-loop reconstruction)** | **18.7** |
| **margin-exhaustion, LIVE (this A/B)** | **22.02** |

**B-2 SURVIVES** — the oscillation's sign pattern and amplitude persist
(−12.65 / +5.20 / +10.47 vs the registered −10.46 / +6.11 / +10.54); the
implementation does not kill the cobweb, which per the charter is the
implementation-sanity test, passed. Terminal damping is **−3.17 pp** (25.19 →
22.02) vs the offline probe's −6.5 pp, and the difference decomposes into two
things the offline probe could not carry, both named in advance:

1. **The reserve leg is live, and it is what keeps GAS cap-bound.** In every
   clearing year the arm's gas builds to the same caps as bang-bang — the
   exhaustion never binds gas, because the screen's hourly reserve leg (the
   prior year's realized post-solve ORDC adder, largest exactly after tight
   years) carries the margin past the caps even as the energy signal
   reprices. This is the probe's own pre-registered degradation (its 2024
   "reserve-leg-carried" note) measured from the live side: the offline
   walk's 2022 (1.0 GW) and 2024 (3 GW) gas damping came from a margin with
   NO reserve leg. Live, the damping instead comes from **VRE and storage
   exhaustion**: solar 4,946.6 → 1,250 (2022), 5,550 → 4,946.6 (2023),
   6,000 → 0 (2024, exhausted at zero after 6 GW of gas tranches repriced
   the signal); storage 5,000 → 3,000 (2023, the second slot exhausts).
2. **The closed loop feeds back.** Less 2022/2023 build ⇒ a deeper 2023
   trough (8.54 → 6.35 %) and higher mid-window prices ⇒ more entry support
   in later steps — including 6 GW of gas clearing in 2025 (control: nothing)
   whose COD (2027) lies outside the ledger window but inside the scored
   decision basis. The offline probe was open-loop by construction (its §2.1
   honesty note); the live A/B is the real object.

### 3.4 Secondary observations (the charter's storage-mix question)

- **The second storage slot exhausts instead of flipping.** Offline, under
  repricing the second slot flipped flow_battery → compressed_air; live, the
  walk's repriced signal (which also carries 6 GW of same-year gas tranches)
  clears **iron_air only, at its 3,000 MW share cap** — flow_battery's margin
  no longer clears at all. **Li-ion still never builds** (consistent with
  L-1: signal/volume work does not restore li-ion; that remains L-3/D-3).
- **Wind enters (603.4 MW, 2023)** — the first wind entry in any measured
  construction other than the locational-signal arms, produced here by
  VOLUME logic alone: solar exhausting below its cap leaves the repriced
  margin surface where wind still clears, where bang-bang solar had consumed
  the shared budget's headroom at a manufactured margin.

### 3.5 Addition bands (attached evidence, never the verdict — rule 1)

2023–2025 decision basis, actual vs model GW:

| tech | actual | control | arm | note |
|---|--:|--:|--:|---|
| wind | 12.663 | 0.350 | **0.954** | improves |
| solar | 25.080 | 17.987 | **7.687** | worsens (solar exhausts on its own capture) |
| gas_cc | 0.244 | 9.000 | **12.000** | worsens (2025 clears at caps on the thinner fleet) |
| gas_ct | 3.692 | 7.571 | **10.571** | worsens (same) |
| storage | 13.691 | 5.000 | **3.000** | worsens |

Every band FAILs in both arms; the arm is worse on four of five and better
on one. Reported at full magnitude and NOT the adjudication basis: the gas
worsening is the reserve-leg interaction (§3.3 item 1) plus real equilibrium
feedback (higher prices on the thinner fleet), not a defect of the volume
rule's own arithmetic; the solar/storage worsening is the exhaustion doing
exactly what it claims against a signal whose LEVEL problems are the
adjudicated signal-lane objects (D-8 zone-flat dispersion; the D12 pro-forma
scarcity-basis rung).

## 4. Matrix cell verdict — ERCOT `entry_margin_exhaustion`: **O** (measured, owner escalation)

Cell `O` / `fc O` with this finding as evidence. Not `R`: the mechanism does
what the closure claims — volumes become margin-bounded where the margin can
exhaust (VRE, storage), the cobweb survives as real dynamics, wind entry
appears, and the terminal overshoot damps 3.17 pp with zero fitted
parameters. Not `K`: not armed anywhere, and the A/B surfaces a real
structural finding — **the reserve leg is now the binding volume driver for
gas**: under a repriced energy signal, whether gas entry is cap-bound or
margin-bounded is decided almost entirely by the prior year's realized ORDC
adder entering the screen as an inexhaustible-within-year floor. That is a
statement about the SCREEN's margin construction (the D12 pro-forma/
scarcity-basis rung and the two-scarcity-objects question), not about the
volume rule, and it is exactly the seam D12 is chartered to examine.
`entry_lookahead_reprice` and `entry_forward_expectation_signal` cells:
untouched, as chartered.

## 5. Arming recommendation (the OWNER decides; this lane only recommends)

**Recommend: HOLD arming until D12 adjudicates the screen's scarcity basis;
adopt the mechanism as the standing volume rule if/when the margin it
exhausts is the one the owner accepts as the screen's margin.** The
structural case FOR the rule is strong and construction-independent: a
developer builds until the expected margin no longer clears cost, the
implementation is zero-DOF, byte-identical off, and its damping comes from
real feedback. The case for waiting is §4's finding: with the reserve leg as
currently constructed, the rule's gas half is inert, so arming it now would
bake in "margin-exhaustion for VRE/storage, bang-bang for gas" — a posture
whose gas behaviour is decided by a leg D12 may re-found. If the owner
prefers to arm now, the honest description of what arms is exactly that
split, with the A/B here as its measured record.

## 6. Rule compliance

- **Rule 1 `[R-STRUCT]`** — adjudicated on whether exhaustion-bounded volume
  is the real allocator object, never on the bands (four of five worsen and
  are reported at full magnitude); nothing is armed on fit.
- **Rule 12 `[R-PARALLEL]`** — the two invocations ran concurrently, years
  sequential within each; in-flight backcast branches
  (`claude/ercot-p0-bit-identity-o7`, `claude/miso-190`) checked before
  launch, and the pair fills the ~2-heavy cap in this session's container.
- **Rule 13 `[R-MEASURED]`** — no measured outcome enters any model path;
  every walk input is a model-produced object.
- **Rule 19 `[R-ONE-MECH]`** — one field, one walk state, both allocators;
  the bang-bang paths are replaced when armed, never stacked on.
- **Rule 21 `[R-DOF]`** — zero elasticity/damping coefficients; the tranche
  is the probe's resolution constant with the invariance property re-tested
  live; the Phase-0 free-parameter stop was checked and not hit (§1.3).
- **Rule 22 `[R-HOLDOUT]`** — solves span the registered window only (2021
  seed + 2023–2025, 2022 bridged); freeze untouched; `--holdout-authorized`
  never needed or passed; forecast-mode machinery only.
- **Rule 15/24** — both arms on the FORECAST namespace with committed
  `run_config.json`; the new field serializes into `run_config.json` and the
  hindcast meta (`FromConfig`); backcast registry, keeper shards,
  `calibration-complete.json`, offer curves, commitment bridges and
  ORDC/scarcity mechanisms untouched (deconfliction honoured).
- **Rule 25 `[R-ISO-SCOPE]`** — every measured number is ERCOT's; the five
  sister-ISO cells enter as `U`.
- **Rule 26/28 `[R-MECH-MATRIX]`** — the row + all-ISO cells landed with the
  mechanism (duty c); the ERCOT cell verdict updated in this session (duty
  b); no other cell moves.
- **Rule 27 `[R-PUSH]`** — every ≥300-line file edited locally and pushed as
  on-disk bytes with post-push blob verification; no CI workflows added; all
  solves ran in-session.

## 7. Reproduction

```
# the two arms (bare invocation = the registered posture; one flag differs)
uv run python scripts/run_capacity_hindcast.py --iso ERCOT --start-year 2021 --end-year 2025 \
    --out-dir results/hindcast/ercot-2021-2025-realized-t1h-d11r-control
uv run python scripts/run_capacity_hindcast.py --iso ERCOT --start-year 2021 --end-year 2025 \
    --entry-margin-exhaustion \
    --out-dir results/hindcast/ercot-2021-2025-realized-t1h-d11r-exhaustion

# score each, then the A/B probe (posture-gated: exactly one field may differ)
uv run python scripts/score_capacity_hindcast.py --bundle <each bundle>
uv run python scripts/probes/entry_volume_rule_compare.py \
    --arm results/hindcast/ercot-2021-2025-realized-t1h-d11r-exhaustion \
    --control results/hindcast/ercot-2021-2025-realized-t1h-d11r-control \
    --out results/calibration/entry_volume_rule_ab_ercot.json

uv run python -m pytest tests/unit/model/test_entry_margin_exhaustion.py -q
```

`data/clean` is derived and gitignored: run
`PYTHONPATH=. uv run python scripts/regenerate_clean.py` first (50/51
datatypes succeed on this tree; the one failure is a MISO raw mirror absent
from the profile and irrelevant here). Evolution ledgers stay uncommitted per
repo policy; the probe artifact carries both arms' per-step rows and the
committed dumps carry the screen-signal internals.
