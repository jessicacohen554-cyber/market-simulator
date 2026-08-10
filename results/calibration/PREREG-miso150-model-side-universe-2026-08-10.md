# PREREG — miso-150: the MODEL-SIDE UNIVERSE FIX (§5.4 MISO queue, item 8)

**Session** miso-150 · **ISO** MISO · **Keeper** `2026-08-09-miso-148-basis-aware`
(bundle `results/calibration/miso148_basis_B`) · **Date** 2026-08-10 ·
**Model** Opus (rule 27 `[R-PUSH]`).

**Posture: PHASE 0, NO LP SOLVE.** Item 8 is a *measurement* fix, not a
mechanism. No `ScenarioConfig` field is added, nothing enters the LP, and no
run is produced. Rule 13 `[R-MEASURED]` is not engaged by the construction
itself (§8).

**This PREREG is pushed before any adjudicating statistic exists.** Every
number quoted below is read from an artifact already committed at HEAD
(`_miso145_offer_conduct.json`, `_miso146_intermittent_screen.json`) or is
arithmetic on those numbers. No new measurement has been taken.

---

## 1. The object, stated so it can be wrong

miso-145 compared MISO's **real submitted offer book** against the **model's
own offer stack** and refuted the offer-LEVEL hypothesis. miso-146 found that
the comparison is measured on **asymmetric universes**:

* MISO's DA/RT offer book carries its VRE at ≤ $0 — partially: miso-146
  identifies **7.755 GW (RT) / 3.751 GW (DA)** of intermittent capability in
  the corpus against **16.286 GW** of model VRE dispatch in the same hours;
* the model's wind and solar are **LP decision variables at MC ≈ 0** and are
  **entirely absent** from the model-side curve — `_miso143_stack.fleet_state`
  builds the model curve from generator rows only.

miso-146 §8(a) **refuted** fixing this by subtracting VRE from the corpus (most
of MISO's VRE is not in the corpus to subtract) and named the fix: **add the
model's own VRE to the model's curve at its own offer price.** That
symmetrises on the model side and costs no new data. This session builds it.

**What is at stake.** Three independent instruments agree the object is a
price LEVEL miss (miso-145's missing offer wall; miso-147's "marginal on gas in
76 % of S1-2025 hours yet clearing $40.7 below actual"; miso-149's G-3, 95.4 %
of the CC deficit out of merit at the model's own price). Item 8 is item 9's
stated prerequisite: item 9 (a MISO `measured_offer_surface`) is an owner
decision and is **NOT chartered here**. What this session can settle is
whether the wall measurement that would motivate item 9 **survives a
symmetrised universe** — and whether the universe asymmetry was ever
load-bearing on the LEVEL term.

---

## 2. Footing — reproduce before extend (HARD STOP)

**G-F0.** `_miso145_offer_conduct.run()` is re-executed **unchanged**, on
`_miso143_stack.KEEPER` at its own committed value (`miso132_ccmin_B` — the
keeper-pointer seam miso-149 documented). Every cell of the committed
`_miso145_offer_conduct.json` must reproduce.

* bar: worst |Δ| ≤ **$0.01** on every price statistic, ≤ **0.05 GW** on every
  MW statistic, ≤ **0.0005** on every percentile.
* **A footing failure is a HARD STOP.** No new statistic is computed or
  reported. The session ends with the footing failure as its finding.

**G-F1.** The six committed miso-142/143 window deficits reproduce inside
`_miso145_offer_conduct` (its own TRAP 7 gate), bar $0.01.

**Only after G-F0/G-F1 pass** is `_miso143_stack.KEEPER` re-pointed to the
CURRENT keeper `miso148_basis_B` (the miso-149 save/restore pattern, so the
shared modules keep their own pointer and the footing stays valid). **Every
new statistic is measured on the CURRENT keeper, and every Δ this session
quotes is U-arm-vs-U0 on that SAME basis** — never against a committed
miso-145 number, which sits on a superseded keeper. The miso-148 K0
non-reproducibility caveat is inert here: there is no solve.

---

## 3. The constructions (fixed before any is evaluated)

All four are the **same** miso-145 statistics on the **same** hours, windows
(`W1_jun_jul_h8_20`, `JJA_h12_17`), markets (RT, DA), years (2023/2024/2025)
and brackets (`lo`/`hi`). Only the **model-side segment set** changes.

| id | model-side universe | why |
|---|---|---|
| **U0** | fleet generator rows only | miso-145's construction, re-based on the current keeper. The baseline every Δ is taken against. |
| **U1** | U0 **+ model VRE** at its own offer price | **the charter's named fix.** Per zone-hour, `wind_cap[z]·wind_cf[z,t]` at `wind_mc[z,t]` and `solar_cap[z]·solar_cf[z,t]` at `solar_mc[z,t]`. |
| **U1S** | U1 **+ storage discharge capability** at ε | the model's COMPLETE offerable universe. U1S is the **upper bound** on any foot-addition correction: there is no further model resource to add. |
| **U4** | U1 **− the model's import tranches** | the residual asymmetry miso-146 **requires be stated**: 32 tranches / 17.2 GW with no analogue in a book of MISO-internal resources, priced in the **body** of the curve, not at its foot. Sized, not glossed. |

A **locator**, not a construction: **U2** re-reads U1 with the model VRE mass
truncated per hour to the intermittent MW miso-146's screen identifies in the
book, so the two universes carry the *same* VRE content. Because the readings
are monotone in the added mass, **U0 ≤ U2 ≤ U1** always holds; U2 only says
where in that bracket the matched universe sits. miso-146's P-1 found its
screen thresholds load-bearing, so U2 is reported as a **band across the swept
thresholds and is never load-bearing on any verdict here** — the verdict rests
on U1/U1S, which bound U2 from above by construction.

**Offer prices are read from the run's own assembly, never re-derived.**
`wind_mc`/`solar_mc` are the post-EAC, post-`apply_negative_renewable_offer_floor`
arrays the LP is handed. They are produced *before* `run_year`'s `fleet_only`
exit but are not currently returned by it; this session adds the two keys to
that return dict (§10). No other change.

---

## 4. Gates, fixed with their reasons, in advance

| gate | statement | bar | why this bar |
|---|---|---|---|
| **G-1 (invariance, ladder slope)** | The model's ladder slope `$/GW above its own clearing` is **analytically invariant** to any mass added at a price ≤ the hour's anchor: `below` and the ladder target `below + G·1000` shift by exactly the same MW, so `price_at_cum` returns the same segment. Measured `\|Δslope\|` U1−U0 must be ≈ 0. | ≤ **$0.05/GW**, on every year·window·bracket | The identity is exact. Anything above the bar is a **construction defect**, not a result (see TRAP-2 for the one legitimate channel). |
| **G-2 (invariance, the wall)** | `model_gw_anchor_to_hour_actual` counts MW priced **strictly above** the anchor and ≤ the hour's actual. VRE at `wind_mc/solar_mc` ≤ 0 ≤ anchor cannot enter that band. `\|Δwall\|` U1−U0 ≈ 0. | ≤ **0.05 GW** | Same identity. This is the gate that decides whether **miso-145's standing measurement survives symmetrisation** — the whole point of item 8. |
| **G-3 (the LEVEL move)** | ΔLEVEL = LEVEL(U1) − LEVEL(U0), every year·window·market·bracket, reported at full magnitude and sign. | **no bar — this is the measurement**, and its size decides §6's branch | A bar here would be a fitting target. |
| **G-4 (the ceiling)** | The zero-priced mass **V\*** that the model curve would need for the LEVEL term to reach miso-145's **+$18** reinstatement bar, solved from the *measured* real-curve percentile grid. | reported against MISO's **total VRE nameplate** (49.7 GW in 2025, EIA-860, miso-146's control) | Converts "is the universe load-bearing?" into a falsifiable quantity with a physical yardstick. |
| **G-5 (the import asymmetry)** | U4−U1 on LEVEL, clearing percentile and capability. | reported, no bar | miso-146 **requires** this be stated when the fix is built. |

---

## 5. Two-sided numeric prior (committed before measuring)

Arithmetic on committed artifacts, 2025 · `JJA_h12_17` · RT · `lo`:
model capability **107.519 GW**, model clearing percentile **0.7911** ⇒ mass
below the anchor **85.06 GW**; real RT curve **p80 $28.784 / p85 $31.388**
(**$0.521 per percentile point**); LEVEL(U0) **−14.376**; anchor **$44.245**.

Adding V GW of zero-priced mass moves the model's clearing percentile to
`(85.06 + V)/(107.519 + V)`:

| V (GW) | new percentile | ΔLEVEL (RT, lo) |
|---|---|---|
| 12 | 0.8121 | **+$1.09** |
| 16.286 (miso-146's committed model VRE dispatch) | 0.8186 | **+$1.43** |
| 24 | 0.8292 | **+$2.00** |
| 35 (implausibly high) | 0.8424 | **+$2.68** |

**Central prediction: ΔLEVEL(U1) = +$1.4, band [+0.9, +2.2]** for 2025 RT `lo`;
same sign, similar order elsewhere. **Predicted LEVEL(U1) ≈ −13.0**, against
miso-145's **+$18** reinstatement bar and a 2025 JJA deficit of **−$30.4**.

**The falsification side, stated as a number.** Solving the same identity for
the percentile at which the real curve reaches `anchor + $18 = $62.2`:

* **RT** (~p97): **V\* ≈ 641 GW** — **13× MISO's entire 2025 VRE nameplate.**
* **DA** (~p91.5): **V\* ≈ 157 GW** — **3.2×** that nameplate.

**So the prior is that the universe asymmetry CANNOT be load-bearing on the
LEVEL term, and this session expects to say so.** What would overturn it, and
what I commit to reporting as a genuine finding rather than noise:

* **ΔLEVEL(U1) ≥ +$5** on any 2025 cell — an order of magnitude above the
  identity's prediction. The identity would then be wrong about *something*
  (most likely: the model's VRE capability is far larger than its dispatch, or
  a material share of anchors is at or below the VRE offer). **Report, do not
  explain away.**
* **G-1 or G-2 breached** — the wall/slope statistics are NOT invariant, i.e.
  miso-145's standing measurement is universe-sensitive after all. This is the
  outcome that would *most* change what the program does next, and it is the
  one the prior says is least likely. **Report at full magnitude.**
* **ΔLEVEL(U1) < 0** — symmetrising moves the level term the *wrong* way.
  Possible only if the model's anchor sits below its own VRE offer in a
  material share of hours. **Report; it would make the asymmetry worse, not
  better, and that is still an answer.**

---

## 6. Pre-committed branches (the verdict is fixed before the number)

* **BRANCH-NULL** — G-1 and G-2 hold, and `max ΔLEVEL(U1S)` over all cells is
  **< +$5**. Verdict: **the model-side universe asymmetry is NOT load-bearing
  on the LEVEL term.** miso-145's refutation of the offer-LEVEL hypothesis
  **stands on a symmetrised universe**; the missing offer wall
  (5.698–6.038 GW) and the slope contrast ($73.46 vs $1.496 per GW) are
  **re-affirmed as universe-robust measurements**. Item 8 **CLOSES**; the
  blocker miso-146 named is dissolved by showing it was never load-bearing.
  Item 9 remains an owner decision, its prerequisite discharged.
* **BRANCH-MATERIAL** — G-1/G-2 hold but `max ΔLEVEL(U1S) ≥ +$5`. Verdict:
  **the universe was partly load-bearing.** The corrected LEVEL term is
  reported as the new baseline, miso-145's refutation is **weakened, NOT
  reinstated** (reinstatement needs ≥ +$18 and that bar does not move), and
  the residual is handed to the owner with the corrected number attached.
* **BRANCH-DEFECT** — G-1 or G-2 breached. **No LEVEL verdict fires.** The
  breach is the finding: the standing wall/slope measurements are
  universe-sensitive, the channel is diagnosed, and item 9's prerequisite is
  **NOT** discharged.

**No branch licenses a mechanism, an arm, or a `ScenarioConfig` field.** If
BRANCH-MATERIAL or BRANCH-DEFECT fires, the successor is named and **not
opened** (rule 25 `[R-ISO-SCOPE]` scope discipline).

---

## 7. Traps, each with its counter-measurement

* **TRAP-1 — the invariance is assumed instead of tested.** G-1/G-2 are stated
  as identities; a probe that *implements* them by construction would prove
  nothing. Counter-measurement: U1's model curve is built by **concatenating
  segments and re-running the unmodified `curve_readings`/`price_at_pctl`
  primitives** — never by adjusting `below`/`total` analytically. The identity
  is a *prediction about the output*, tested numerically.
* **TRAP-2 — the one legitimate channel for non-invariance.** Hours whose
  anchor price is **at or below** the model's VRE offer price. There VRE is
  *not* foot mass and both identities legitimately break. Counter-measurement:
  the share of window hours with `anchor ≤ max(wind_mc, solar_mc)` is
  **counted and reported for every cell**, and G-1/G-2 are additionally
  evaluated on the **complement** subset, where the identity must hold exactly.
* **TRAP-3 — units against denominators (miso-149's own lesson).** Every gate
  is checked for unit/denominator consistency *before* it is pushed: G-1 is
  $/GW vs $/GW; G-2 is GW vs GW; G-3/G-5 are $/MWh vs $/MWh; G-4's V\* is GW
  against a GW nameplate. No gate compares a per-hour capability against an
  annual energy, and no share can exceed 1 by construction.
* **TRAP-4 — the model's VRE is a POTENTIAL, not a delivery.** MISO reaches
  `load_renewable_profiles` through `_forecast_uncurtailed_cf` (the potential
  is grossed up so the dispatch re-curtails), so `cf × cap` **exceeds**
  delivered VRE and exceeds the 16.286 GW dispatch figure. That is the correct
  quantity for an *offer* curve and it makes U1's correction **larger**, i.e.
  it biases against this session's own prior. Counter-measurement: the
  measured V is reported per cell next to the 16.286 GW committed dispatch, and
  the prior's V-table is re-read at the measured V.
* **TRAP-5 — a class silently reading zero.** `klass_of` falls back to
  `_model_class_for_unit` for non-fossil rows; filtering on `plant_group`
  returns ZERO import/hydro rows (miso-141/142 hit exactly this). U4 depends on
  identifying the import tranches. Counter-measurement: the import row count
  and MW are **asserted non-zero and reconciled to the committed 32 tranches /
  17,200 MW** before U4 is evaluated; a mismatch voids G-5 only, never G-1/G-2/G-3.
* **TRAP-6 — the keeper pointer.** `_miso143_stack.KEEPER` is hard-coded to the
  superseded `miso132_ccmin_B`. Counter-measurement: the footing runs at that
  pointer (and must reproduce), the new measurement runs re-pointed to
  `miso148_basis_B`, and the pointer is **saved and restored** around the call.
* **TRAP-7 — the cache in the CWD.** `_miso147_strata._cache_dir()` writes npz
  into the CWD (`Path("")` is truthy). Counter-measurement: this probe sets its
  own cache env var to a `/tmp` path and never inherits the miso-147/149 caches
  (different keeper).
* **TRAP-8 — reading the level off the real curve's own percentile.** Would
  make the LEVEL term identically zero. Counter-measurement: miso-145's
  discipline is kept verbatim — the real curve is read at the **model's** own
  clearing percentile, never its own.

---

## 8. Rules engaged

* **Rule 13 `[R-MEASURED]`** — nothing here enters the LP; no measured outcome
  is fed back. The construction re-labels the model's *own* offer prices onto
  its *own* capability. Not engaged by the construction; engaged by any
  successor, which is named and not opened.
* **Rule 19 `[R-ONE-MECH]`** — no mechanism is added, so nothing stacks. Item 9,
  if the owner ever charters it, must still state how it replaces or subsumes
  `gas_offer_margin`.
* **Rule 24 `[R-REGISTRY]` / rule 28(c)** — no `ScenarioConfig` field is added,
  so no matrix row and no `_CACHE_KEY_OPTIONAL_FIELDS` registration is due.
* **Rule 28(b)** — no mechanism cell changes status. The §5.4 MISO lever queue
  **is** stamped in this session with item 8's outcome.
* **Rule 22 `[R-HOLDOUT]`** — 2023/2024/2025 only. MISO holds no marker. No
  solve, so no year is spent in any sense.
* **Rule 15 `[R-DASHBOARD]`** — no run is produced, so there is nothing to
  register (the miso-149 precedent: a Phase-0 session's deliverable is its
  FINDING plus its committed artifact).

## 9. Named failure modes

1. **The footing does not reproduce.** HARD STOP per §2; the finding is the
   footing failure.
2. **`wind_mc`/`solar_mc` are not what the LP saw.** Mitigated by returning
   them from the orchestrator's own exit rather than re-deriving them — the
   exact failure mode miso-143's docstring warns against. If the additive
   change cannot be made cleanly, the session reports that and stops rather
   than hand-reproducing the credit sequence.
3. **The corpus slice does not fit memory.** miso-145 loads ~11 M rows per
   year·market over the union of both windows and caches per year; that path is
   reused verbatim. No LP runs, so no swap is provisioned.
4. **U2's screen thresholds swing the locator.** Anticipated (miso-146's P-1
   FAILED well-posedness); U2 is banded and never load-bearing (§3).

## 10. Disclosure

* **One additive change to a core file**, declared here before it is made:
  `scripts/run_calibration.py`'s `fleet_only` return dict gains
  **`"wind_mc"` and `"solar_mc"`**. Both are already assembled in scope at that
  point (post-`compute_dispatch_credits`, post-EAC, post-negative-offer floor).
  **No solve path is touched; no existing key changes; no behaviour changes.**
  The file is ≥300 lines, so rule 27 `[R-PUSH]` applies: edited locally with
  Edit, pushed as exact on-disk bytes, and the pushed blob verified against the
  fetched remote ref.
* **Reused verbatim, not re-derived:** `_miso145_offer_conduct`
  (`load_real_segments`, `curve_readings`, `price_at_pctl`, `price_at_cum`,
  `model_*`), `_miso143_stack` (`fleet_state`, `hygiene`, `klass_of`,
  `markup_ceiling`, `windows`, `sidecar_price`), `_miso146_intermittent_screen`
  (`load_declarations`, `unit_features`, `classify`) for the U2 locator only.
* **This session is Phase 0.** If item 8 escalates to an arm, that arm is
  **not** taken here: it would need a same-HEAD zero-delta control first
  (miso-148 K0), a single `--year 2023 2024 2025` invocation, and its own
  charter.
* **Not this session's scope** (rule 25): MISO's un-re-tuned outage extract
  (measured `X_cc = 0.240`; needs a cross-ISO charter) and the 2025 EIA-860
  vintage under-carry (cross-ISO, needs an owner decision). Neither blocks this
  object — item 8 is a comparison-universe question and touches neither input.
* **Kill gates carried from the charter** are inert this session: no gate can
  move because no solve is taken. They are restated in the FINDING for the
  record.
