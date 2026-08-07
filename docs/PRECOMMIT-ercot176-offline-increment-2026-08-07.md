# PRECOMMIT — ercot-176: the offline-increment start-inclusive re-pricing, SLOW-START tier (`ercot_offline_commit_offer`)

**Session ercot-176, 2026-08-07. Pushed BEFORE any derive, any measurement and
any solve.** Charter: the ERCOT-151 §3 design round, owner-authorized in-session
2026-08-07 (the ercot-175 decision card), discharging that document's §4 ask (2);
ask (1) was discharged at ercot-157 (the delivery-2023 NP3-965 corpus, 315
shards / 897 MB, is on disk).

Object: **C3a-2023** (−29.9 % lw-hub, −32.2 % scorer), fail set {C3a, C3b}, on
keeper `2026-08-05-run168b-year-curves`.

Everything below — mechanism, class scope, composition rule, guards, kill gates,
falsifiers and predictions — is fixed HERE and is not renegotiated after the
solve.

---

## 0. A correction to the charter's own premise, stated before anything is built

The handoff prompt for this session cites, as THE CHARTER, the ERCOT-151 §0.2
headline: *"18.1 GW of startable-but-OFF CC+CT at the missed hours, ~13.5 GW of
it submitted-DAM ≤ $200."* **That number is REFUTED and this session does not
rest on it.** `DIAGNOSIS-ercot151-offline-increment-phase0-2026-08-02.md` carries
an ERCOT-163 correction banner at its head saying so
(`FINDING-ercot163-cc-commitment-state-refuted-2026-08-04.md`): the CC half is a
60-Day-DAM day-ahead-status artifact — measured on the delivery-2023 SCED corpus
at the committed top-100 gap hours, ERCOT's CC fleet was **96.4 % committed and
98.0 % loaded**, with **0.020 GW** of offline-startable (OFFQS/OFFNS) capability.
ercot-175 §2 corroborates at SCED grain from the other side: OFF-startable
resources carry only **~0.9 GW** of sub-$200 offers at these hours.

**What survives, and is the whole of this session's justification (rule 1):**

1. **The model prices its own uncommitted increment at base cost with no start
   economics.** The availability basis is only-OUT-is-out (correct — startability
   is physical, rule 13), so every non-outaged unit is offered to the LP at its
   base/wall-basis curve whether or not serving the next MW would require a
   **start**. P1's startup amortization is the only start term and it is the
   wrong identification by ~30× (physical startup $/MW over min-run at LSL ≈
   **$20–30/MWh**; ERCOT-151 §0.3).
2. **Reality prices that same capability at start-inclusive opportunity cost, and
   the magnitude is measured.** The ERCOT-88 pool artifact carries the CT tier's
   own SCED2 ladder at p50 **$271–707** / p90 **$641–1,010** — scarcity
   magnitudes, from the fleet's own conduct. ercot-175's ~0.9 GW sub-$200
   startable figure is the same fact seen from below: real OFF capability is
   **not** cheap in RT.
3. **The residual is a marginal-price phenomenon, which is exactly what an offer
   mechanism can reach.** ercot-175 §2: reality delivered 51.95 GW of sub-$200
   energy against the model's dispatched ~51.9 GW — *the quantities agree*. At
   the same ~52 GW, reality's next deliverable MW priced $462 (p50) and the
   model's prices <$200. The model's sub-$200 margin above dispatch is M = 3.30
   GW mean / **2.21 GW p50**.

So the defect this session addresses is **not** "the model has a phantom 13.5 GW
of cheap offline depth" (refuted). It is: **the model's marginal MW at the missed
hours is priced as if no start were required.** That is a genuine structural
absence, it is rule-1 correct to close whatever it does to the residual, and its
price is measured conduct rather than a fitted scalar.

**The magnitude claim in ERCOT-151 §3's "expected magnitude" paragraph is
withdrawn with the premise it rests on.** No magnitude is promised here; §8
states predictions that can fail.

## 1. The mechanism — ONE default-off gate, zero fitted scalars

`ScenarioConfig.ercot_offline_commit_offer: bool = False` (+
`ercot_offline_commit_offer_path: str | None = None`, the artifact override —
the ERCOT-88 field pair, same shape).

**Construction: the ERCOT-88 static conditional-conduct surface, new physics
tier.** Not a new seam and not a P0-conditioned mechanism — the accepted
precedent, a second class block in the same artifact:

```
boundary(bin) = 1 - pool_frac_SLOW(bin)        # measured offline-startable share
rel           = (share_g - boundary) / (1 - boundary)
target[g, t]  = interp(rel, ladder_q, ladder_SLOW(bin)) x gas_day(t)
markup[g, t]  = max(0, min(target, cap_frac x VOLL) - mc_base[g, t])
```

applied on the rows whose WITHIN-PLANT cumulative-capacity midpoint sits above
the hour-bin's measured boundary.

* **Eligibility is unit physics (rule 18 `[R-PHYSICS]`), never a class tuple:**
  `4.0 <= min_down_hours <= 8.0` **and** `min_run_hours <= 12.0`. Both bounds are
  physical and both are needed. The lower bound is `constants.
  RA_BRIDGE_ECON_MIN_DOWN_HOURS = 4.0`, already documented at the CC table's own
  floor ("every CC row qualifies, every CT row is excluded"); the min-run bound
  is the **within-day start-and-run** line — a unit whose minimum run is 24–48 h
  is not making a within-day start decision at all, its commitment is a
  multi-day choice. Against `constants.*_COMMITMENT_PARAMS` this band admits all
  three CC classes (min-down 4/6/8, min-run 5/8/10) and excludes CT (min-down 1 →
  the ERCOT-88 tier already owns it), ST_GAS (min-run 24/48) and coal (min-run
  48). New constant `OFFLINE_COMMIT_MIN_DOWN_HOURS_MAX = 8.0` /
  `OFFLINE_COMMIT_MIN_RUN_HOURS_MAX = 12.0` in `constants.py` with this citation
  — **structural bounds read off the committed physics tables, not fitted
  scalars** (§6 G-DOF).
* **ST is EXCLUDED, by the charter's own condition.** ERCOT-151 §3 admits ST only
  "if its row survives the ERCOT-90/91 steam-lane reconciliation". It does not:
  ERCOT-91 REJECTED the band-hour steam-wall arm on the zero-spurious/C3a guards
  in both years, alone and composed, and found the trip *intrinsic to the
  DAM-basis ST ladder in cold-snap hours*. That cell is `R`; re-testing it here
  without new evidence would breach DO-NOT-REDO. The physics band excludes ST by
  construction, so this is enforced by the gate, not by discipline.
* **An offer-availability, NEVER a floor.** No `min_gen` is touched; the markup
  can only RAISE a bid (`max(0, ...)`), and where the measured target sits below
  the row's base cost the markup is 0 and the row bids cost. **D-2 forced energy
  and D-4 off-window binding are vacuous by construction** — the rule-17
  `[R-FLOOR-WINDOW]` hazard is structurally impossible, exactly as for ERCOT-88.
* **Above-LSL basis:** the ladder derives from the startable increment's
  above-LSL segments only; below-LSL min-gen curve bottoms (negative prices)
  never enter.
* **Year-scoped (rule 13):** no pooled fallback. A year absent from the artifact
  gets **no** tier and every surface stays byte-identical.
* **P1-only**, via the shared `mc_bid_adjust` seam: P0 run lengths and the
  startup-amortization coupling are untouched.
* **Forward story (rule 13):** the surface is conditional conduct — net-load
  percentile bin × physics tier. It regenerates for a forward year from forward
  net load exactly as the DAM/RT walls and the CT pool already do, and it
  responds to changed conditions (a tighter forward year lands in a higher bin
  and prices higher). It is **not** an overlay and carries no measured outcome.

## 2. Rule 19 `[R-ONE-MECH]` reconciliation — enumerated exactly as ERCOT-151 §3.2 requires

One owner per row-hour, enforced at the composition site (`scripts/
run_calibration.py`, the ERCOT-88 `np.where(mask, ...)` pattern):

| incumbent | overlap with the new tier | resolution |
|---|---|---|
| `ercot_gas_commitment_bridge` | owns the **ON committed CC min-gen state** | **DISJOINT by object** — the bridge sets a `min_gen` floor on committed rows; this tier sets a **bid price** and touches no bound. No row-hour is floored *by this tier*, and the bridge's floors are unchanged. |
| **P1 startup amortization** | prices started runs on the same rows | **REPLACED, never stacked**, on the tier's own row-hours. The measured start-inclusive ladder already contains the start; adding the amortized markup on top would double-count the start term. Enforced by mask, and it is the seam-proof's SP-4 assertion. |
| `ercot_faststart_pool_offer` (ERCOT-88, CT) | same construction, same artifact | **DISJOINT by physics** — min-down ≤ 2 h vs ≥ 4 h; the eligibility bands cannot both admit a row. Asserted in the seam proof (SP-3). |
| cleared-share wall + RT leg (`ercot_offer_surface_cleared_share[_rt]`) | own the **ON** fleet's ladder | **DISJOINT by status, REPLACE-BY-MASK where they touch** — an online/DA-basis price is refuted for capability that must start. Same precedence the CT pool already takes. |
| `ercot_offer_surface_conditional` (peak surface) | peak rungs | **REPLACE-BY-MASK** in the tier's row-hours, ERCOT-88 precedent. |
| steam wall / coal offer lanes | ST_GAS, coal rows | **DISJOINT** — excluded by the physics band (§1). |

The tier **requires `ercot_offer_surface_cleared_share` armed** (hard error
otherwise), the same precondition ERCOT-88 carries: this enumeration was
performed against that recipe context.

## 3. The ERCOT-89 zero-spurious / C3a guards

The guards that killed the shoulder-span arms, carried verbatim as
**falsifiers**:

* **G-SPUR (primary falsifier, see §6)** — the tier must not reprice sub-$150
  same-cell hours into the tail. The net-load-bin scoping is the protection: a
  loose hour sits in a low bin whose measured ladder is low. If the spurious
  mid-band tail-hour count rises in **any** year, the arm is REJECTED-AS-ARMED.
* **C3a directional guard** — a C3a that overshoots (2024 or 2025 crossing from
  PASS/near-PASS into a positive-side miss) is a failure, not a success. The arm
  must move 2023 toward zero without inverting the sign elsewhere.

## 4. Seam proof — BEFORE any solve (the ercot-173/174 SP pattern)

Executed and committed as a probe + its JSON record before the LP pair starts.
Any assertion failing stops the session at that point.

* **SP-1 — out-of-scope byte-identity.** With the gate ON, every row failing the
  physics band has a byte-identical `mc_bid_adjust` to the gate-OFF build
  (sha256 over the array). Non-ERCOT ISOs: the builder returns `None`.
* **SP-2 — gate-off no-op.** `ercot_offline_commit_offer=False` reproduces the
  control's `mc_bid_adjust` sha256 exactly; and with the gate ON for a year
  absent from the artifact, likewise (year-scoping, rule 13).
* **SP-3 — tier disjointness.** The new tier's `own_mask` and the ERCOT-88 CT
  pool's `own_mask` have **zero** overlapping row-hours.
* **SP-4 — composed arm equals the independent construction on every scoped
  row.** On the tier's own row-hours the composed `mc_bid_adjust` equals the
  tier's markup alone (proving REPLACE, not stack — including against the P1
  startup amortization).
* **SP-5 — monotone/no-markdown.** `markup >= 0` everywhere; no row's bid is ever
  lowered by the tier.
* **SP-6 — artifact integrity.** Re-deriving the artifact reproduces the
  **existing CT blocks for all three years byte-identically** (the ERCOT-105
  precedent, applied strictly: the whole CT sub-tree, not just absent years); the
  bin edges and ladder quantiles equal the wall artifact's.

## 5. The derive

`scripts/data/derive_ercot_faststart_pool.py` gains the slow-start class block
alongside `CT`, from the same corpus rows, by the **same construction**
(above-LSL SCED2 segments of OFF-status resources; MW-weighted quantile ladder as
effective-HR multiplier; `pool_frac` = interval-mean offline-startable MW over
class live capability, only-OUT-is-out). No new statistic, no new estimator, no
tuned bin. Coverage disclosed per (year × bin), never silently capped.

**Data notes, stated pre-derive:** delivery-2023 is full-span on disk (315
shards). **2024/2025 carry sample days only** (`60_DAY_SCED_DISCLOSURE_*_
ercot74/75/86_*`) — the pool's existing 2024/2025 CT blocks were identified on
those probe-day subsets (the ERCOT-88 precedent), and any new-tier 2024/2025
identification inherits exactly that basis and its disclosed thinness. Rule 22
LOYO within 2023–2025 before any promotion. Rule 23 `[R-FROZEN-DERIVE]`: this
re-derive is licensed by a **source-data change** (the ercot-157 corpus arrival)
plus a **new class scope**, never by a residual.

## 6. Kill gates

Inherited from `PRECOMMIT-ercot172` §5. Two of the eight were written against
ercot-172's **2024-scoped** object and cannot be applied verbatim to a
**year-agnostic** rule without killing any correct mechanism by construction.
Both are re-stated here **pre-solve**, preserving the protective intent and never
loosening it; the deviation and its reason are declared now, not after.

* **G-BIT — declared N/A pre-solve, with reason.** ercot-172 §3c(a) forbids a
  year-scoped rule; this tier applies in every year the artifact covers, so no
  year is expected byte-identical. Replaced by **G-SPAN′** below, exactly as
  PRECOMMIT-ercot172 §5 instructs.
* **G-SPAN′ (replaces G-SPAN).** G-SPAN's energy clause ("in 2023 and 2025 no
  class's annual energy moves > 0.5 %") protected the years ercot-172's
  correction was *not* aimed at. **2023 is this arm's object**, so that clause is
  not applicable there. Protective intent preserved as: **the out-of-object years
  must not degrade** — 2024 keeps its **C3a PASS**, 2025's C3a does not worsen
  beyond its current −9.1 %, and in **2024 and 2025** no class's annual energy
  moves more than **0.5 %**. The tail-count and shed clauses are kept verbatim
  and apply to all three years.
* **G-SHED — protective half kept verbatim, success half N/A.** "**No year's shed
  count may rise**" is kept exactly. ercot-172's "the 2024 shed count must
  **fall**" was that object's *success criterion*, not a protection, and this arm
  does not address the 2024 shed; declared N/A pre-solve.
* **G-SPUR — verbatim.** The C3c spurious mid-band tail-hour count must not
  increase in any year. *(This is the primary falsifier for this object.)*
* **G-C3c — verbatim.** The three ledgered tail counts (2023 61/181, 2024 25/53,
  2025 3/31) must not degrade.
* **G-COAL148 — verbatim.** Coal dispatch above the measured-window ceiling may
  not rise more than **0.5 TWh** in any year. The ERCOT-148 adjudication is
  reconciled, never repealed as a side effect.
* **G-DOF — verbatim.** **Zero** new fitted scalars. Every number is a measured MW,
  a measured duration, or a physics-table bound read off `constants.py`
  (rule 20 `[R-DOF]`). A residual that can only be closed by a tuned value is an
  open root-cause issue, not a parameter.
* **G-D2 — verbatim.** No class's forced share may cross its rule-20
  `[R-FORCED-BUDGET]` cap as a result of the arm. *(Expected trivially satisfied:
  the tier touches no bound.)*
* **Rule 22 LOYO — verbatim.** Leave-one-year-out within 2023–2025 before any
  promotion.

**Failing any live gate ⇒ REJECTED-AS-ARMED, reported as such and registered
anyway (rules 15/16).** The gates are not renegotiated after the solve.

## 7. The LP pair

ONE pair, `--year 2023 2024 2025` in a single invocation each, **years sequential**
(rule 12 `[R-PARALLEL]`), **SAME-HEAD** (no rebase between the two solves),
detached under `nohup`, via `scripts/replay_keeper.py --out-dir --set`:

* **CONTROL** — the run168b keeper recipe replayed at HEAD, single delta: none.
* **ARM** — control **+ `ercot_offline_commit_offer=true`**. Single delta.

**BOTH are registered whatever the outcome** (rules 15/16 `[R-DASHBOARD]` /
`[R-ALLYEARS]`).

**Owner ruling folded in (2026-08-07, ercot-175 decision card):** the control
replay at HEAD **doubles as the keeper re-solve**. Whatever the arm does, the
control is registered and the ERCOT keeper is **re-keyed to it**
(`frontend/data/backcast/keepers/ERCOT.json` + `build_status.py --iso ERCOT` +
the `calibration-keeper-auditor` agent), retiring the run168b non-reproduction
item (ercot-173 §5). ERCOT holds **no `complete` marker**, so no
`calibration-complete.json` re-key applies (rule 22 D-5(b) does not fire).

## 8. Predictions — pre-registered, adjudicated at full magnitude whatever they read

* **P-1 (C3a-2023 direction).** C3a-2023 improves from −29.9 % lw-hub. **No
  magnitude is claimed** — ERCOT-151's arithmetic is withdrawn with its premise
  (§0). A null result is a real possibility and is the honest test of whether the
  model's marginal MW at the missed hours is in fact a would-be start.
* **P-2 (the inertness risk, stated as the likeliest failure).** Reality's CC
  fleet was 96.4 % committed at the gap hours (ERCOT-163), so the measured
  `pool_frac_SLOW` in the tight bins may be **small**, and the tier may be
  **measured-inert** — repricing capacity the model was not marginal on. If the
  derived slow-start `pool_frac` in the top net-load bin is < 0.02, that is
  recorded as a measured-inert tier and reported as the finding; the arm still
  solves and still registers.
* **P-3 (C3c formation must be MATCHED, not invented).** Any 2023 tail-hour gain
  must land in hours that are **actual** tail hours — the ercot148/149 anatomy
  discipline. The honest formation story is: at the missed hours the model's
  marginal MW is a CC start priced at measured start-inclusive conduct instead of
  base cost, so the **energy dual** rises in **those same hours**. Tail mass
  manufactured on quiet days is a **G-SPUR failure**, not a success, and is
  reported as such. C3c stays a ledgered CAVEAT ×3 either way — no C3c claim is
  made.
* **P-4 (C3b).** C3b-2023 (0.604) is expected to improve *if* P-1 does, since the
  2023 fail set is one residual (ERCOT-101/103); C3b-2024 (0.206) has a separate
  maintenance-season spike-day root and is **not** expected to move. If C3b-2024
  degrades, G-SPAN′ fires.
* **P-5 (D-2/D-4).** Zero forced energy attributable to the tier, in every year —
  it touches no bound. A non-zero D-2 attribution would mean the mechanism was
  mis-implemented as a floor and is a stop-the-line event.

## 9. Scope fences — DO-NOT-REDO honoured in full

Not entered, not re-litigated, not re-tested: the **event-cap ceiling lane**
(FROZEN — `docs/handoffs/DECISION-MEMO-ercot-148149-doublecount-2026-08-07.md` is
filed and its ruling is **PENDING**; this session does **not** act on its
recommendation); blanket `min()` (`R`); unit-scoped (`R`); the 2023
depth/excess-cheap-depth premise (**REFUTED**, sharpened at ercot-175 — and §0
above declines to lean on it); the reserve-side family (**CLOSED** and
corroborated: the model over-holds vs reality's thermal sub-$200 AS wedge by
2.87 GW p50); **no ramp mechanism** (`ramp_envelopes` ERCOT `R`, re-affirmed at
ercot-175, w_ramp/M 0.26); `ercot_storage_rt_offer_surface` (`R`);
`energy_online_capability_cap` (`R`); the CC-headroom crosswalk
(**FILED-UNLICENSED**); all coal offer lanes (**CLOSED**); per-year CT
re-identification (**REFUSED**); West/Panhandle (**CLOSED**); ercot-172's C3
(**REFUSED**, rule 13); no per-hour telemetered-HSL cap; no aggregate capability
cap.

## 10. Governance

* **Rule 22 `[R-HOLDOUT]`:** `--year 2023 2024 2025` only. ERCOT holds no
  `complete` and no `final` marker; 2022 / 2019 / H1-2026 are quarantined and are
  not solved, scored, read or registered.
* **Rule 24 `[R-REGISTRY]`:** the mechanism is ONE `ScenarioConfig` field (+ its
  path override), present in `run_config.json`. No env-var knob, no per-plant
  dict, no `getattr` fallback literal in the offer path.
* **Rule 25 `[R-ISO-SCOPE]`:** ERCOT-gated in the builder; every other ISO
  byte-identical (SP-1).
* **Rule 26 `[R-DELETE]`:** nothing deprecated, nothing zeroed.
* **Rule 27 `[R-PUSH]`:** every push touching a ≥300-line file is blob-verified
  (line count + sha256 vs local) before the next commit. `offer_surfaces.py`,
  `scenarios.py`, `constants.py`, `run_calibration.py` and the deriver all
  qualify; all are edited locally and pushed as exact on-disk bytes.
* **Rule 28 `[R-MECH-MATRIX]`:** matrix §5.1 gains **item 19**; the
  `ercot_offline_commit_offer` row is added in the SAME PR as the
  `ScenarioConfig` field (duty c), and its cell + the `ercot_faststart_pool_offer`
  cell are updated with this session's outcome — **rejection included** (duty b).
* **Rules 15/16:** both runs registered, all three years, in one bundle each.
* **GitHub Actions:** no workflow is added; both solves run in-session.

---

## AMENDMENT 1 — 2026-08-07, pre-derive and PRE-SOLVE: the composition seam is corrected from ADDITIVE replace-by-mask to a bid-LEVEL `max()` reconciliation

**Status when written: no year solved, no measurement of the arm taken, the CC
ladder not yet derived.** Recorded here rather than discovered afterwards, in the
same manner PRECOMMIT-ercot172 §5 requires of its own G-BIT/G-SPAN election
("whichever applies is stated before the solve, never after").

**What was wrong.** §1 and §2 above specified the ERCOT-88 form: an additive
markup `max(0, target - mc_base)` delivered through the `mc_bid_adjust` seam and
composed REPLACE-BY-MASK. Implementation against the solve core shows that seam
is additive against a bid that **already carries P1's monthly startup
amortization**:

```
mc_bid = mc_base + compute_monthly_markup(...) + mc_bid_adjust     # solve.py
```

So an additive form of this tier prices its rows at **`ladder + startup`**. The
measured ladder is **start-INCLUSIVE by construction** — that is the entire
identification (§0.2) — so the additive form **double-counts the start**. §2 of
this precommit already forbids exactly that ("P1 startup amortization … must be
REPLACED, not stacked"); what §1 could not know is that the seam it named cannot
deliver it, because the startup markup is computed *inside* `run_energy_solve`,
after `mc_bid_adjust` has been passed in. The two clauses were in conflict and
the anti-double-count clause is the one that governs.

**The correction.** The tier returns a bid **LEVEL** and goes to the
purpose-built `p1_bid_max_target` seam
(`pipeline.solve.apply_bid_max_target`), which applies `max(bid, target)` **after**
the startup amortization. Builder renamed accordingly
(`build_ercot_offline_commit_target`).

This seam exists for precisely this failure: its own docstring records that the
additive form of the analogous PJM CT_FAST reprice over-expressed at **CT −12
TWh** (pjm-101/102) and was replaced by the `max()` reconciliation (pjm-103).
Using it here is precedent-following, not novelty.

**Why the correction is strictly safer, not a loosening:**

* **The start is counted once.** Whichever of {model bid incl. amortization,
  measured start-inclusive ladder} is higher sets the row — never their sum.
* **It cannot LOWER any price.** `max()` can only raise a bid, so the tier can
  never undercut a level another measured surface set. §4 SP-5 becomes
  structural rather than an assertion to check.
* **Rule 19 `[R-ONE-MECH]` is satisfied by reconciliation rather than by
  precedence.** No mechanism stacks on another's residual — the seam's stated
  contract ("RECONCILES with — never adds to").

**Consequential edits to what was pre-registered** (nothing else changes; the
mechanism, class scope, physics band, artifact, year-scoping, guards, kill gates
and predictions all stand exactly as written):

* **§1 / §2** — "REPLACE-BY-MASK" is replaced by "bid-LEVEL `max()`
  reconciliation" wherever it describes *this tier's* composition. The rule-19
  table's rows are otherwise unchanged: the gas commitment bridge stays disjoint
  by object (bound vs price), the CT pool disjoint by physics, the steam/coal
  lanes disjoint by min-run. The wall/RT/peak surfaces are now **reconciled by
  `max()`** rather than replaced — a weaker claim on those rows, and the honest
  one.
* **§4 SP-4** is restated: *on the tier's own row-hours the composed P1 bid
  equals `max(control bid, tier level)`* — proving reconciliation, and in
  particular that the tier's rows are **not** priced at `ladder + startup`. The
  old formulation (composed == tier markup alone) described the additive design
  and is void.
* **§4 SP-5** is restated as: no row's P1 bid is lower under the arm than under
  the control, anywhere. (Structural under `max()`; asserted anyway.)
* **§8 P-5** is unchanged and if anything easier to satisfy: a bid level touches
  no bound, so D-2/D-4 stay vacuous.

**No kill gate is relaxed, and no prediction is revised.** G-DOF is untouched:
the correction removes an arithmetic error, it adds no scalar.

---

**Next shorthand: ercot-177.**
