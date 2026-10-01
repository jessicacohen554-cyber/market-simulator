# PRE-REGISTRATION — nyiso-216: is 54034 Rensselaer Cogen's sign flip a ZONE, a COST, or a FLEET-REPRESENTATION effect, and does it belong in the `cc_reserve_duty_split` cohort?

**Session:** nyiso-216, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-n1kwem`, on `main` at `71e62675`. **Date:** 2026-09-07.
**Keeper:** `2026-09-07-nyiso-213-summer-seam`. **Nothing is promoted, armed, screened or
registered by this session, and no marker moves.**

**THERE ARE NO IN-SAMPLE RUBRIC FAILURES.** NYISO's keeper reads **CALIBRATED** with **zero
failing criteria** across 2023–2025 (grade 7/8, C3c the lone ledgered caveat) — re-verified by
nyiso-215 at HEAD, artifact-only. Nothing below is selected because a residual moved
(rule 1 `[R-STRUCT]`), no residual is consulted at any point, and the 2022 held-out rung is named
nowhere as a target (rule 22 `[R-HOLDOUT]`).

**ZERO LP.** Every fleet rebuild is `fleet_only=True`; every dispatch and price number is read
from the keeper's own committed sidecars. Rule 29(b) form 4 — **no control solve**; the keeper's
committed bundle IS the control. Nothing under `results/calibration/` is produced that rule 29(c)
would require deleting before merge.

---

## 1. The object

nyiso-215 §4 measured, named and did not pursue: of the seven `reserve_duty = True` plants that
`cc_reserve_duty_split` routes wholesale to the `CC_REGULAR` class **peak** band, six
(all `Upstate_West`) run the mechanism one way — implied economic on-share 0.58–0.68 in 2025
against meters of 1.2–4.7 % — while **54034 Rensselaer Cogen** (`Capital_Hudson`, 78.0 MW) runs it
the **opposite** way in all three years: implied 0.0038 / 0.0064 / 0.0098 against a measured online
share of 0.0635, the **highest** in the cohort. The same mechanism over-corrects there by roughly
an order of magnitude.

**The question is structural and zero-LP: is the sign flip a ZONE effect, a COST effect, or a
fleet-representation effect — and does 54034 belong in a cohort whose other six behave nothing
like it?**

**This is DISJOINT from nyiso-215 §6's level card** (pending owner ruling (vii)) and from
nyiso-214 §6's duct-membership card (pending ruling (vi)). Those ask what basis a duty role's
*level* should be expressed in, and which plants `cc_duct_peaking` should flag. This asks whether
`cc_reserve_duty_split`'s **membership** is coherent at **one** plant. **No successor form is
built, armed, screened, sized or recommended, and none of the seven pending owner rulings is
prejudged.** A clean negative — "the sign flip is a cost artifact and the cohort is coherent" —
is the outcome this session expects and is a **success**, not a null.

## 2. What is already in hand — full disclosure before any prediction was written

Rule-29 step 0 census work legitimately precedes this document. Everything below was read
**before** §4's predictions were written, and saying so costs nothing.

**(a) From the committed `_nyiso215_reserve_duty_census.json` (nyiso-215's `P4_P5_by_year`),
per plant per year:** zone, `pmax`, `mc_peak` hour-mean, own-zone LMP hour-mean, implied on-share,
and `duty_stat`. In particular 54034's `mc_peak` hour-means **$74.053 / $67.219 / $113.714** for
2023/24/25 against a six-plant cohort range of **$44.4–$51.4 / $44.7–$53.5 / $58.3–$70.7**, and
its own-zone LMP hour-means **$35.648 / $39.027 / $59.491** against `Upstate_West`'s
**$24.483 / $35.826 / $53.906**. I therefore already know that (i) 54034's modelled cost is well
above the cohort's in every year, (ii) its 2023→2024 `mc_peak` **falls** while the cohort's rises,
and its 2024→2025 jump is ~+69 % against the cohort's ~+31 %, and (iii) `Capital_Hudson`'s
**mean** price is **higher** than `Upstate_West`'s in every year, so any zone story must run
through distribution *shape*, not level. These priors are why §4's preferred answer is the cost
one, and they are disclosed rather than hidden.

**(b) From `data/raw/_processed-legacy/reserve_duty_cc_NYISO.csv` (23 NYISO `CC_REGULAR` rows):**
54034's basis is `campd_online_share` (**not** the EIA-923 fallback whose bias nyiso-215 §3
quantified), `duty_stat` 0.0635, `reserve_duty` True. The seven members are 10620 (0.0122),
7784 (0.0173, the one `e923_pooled_cf` member), 50744 (0.0239), 54593 (0.0246), 54592 (0.0398),
10621 (0.0470), 54034 (0.0635). The nearest **non**-member above is 56188 Pinelawn at **0.1700**.
Two cohort names carry "Cogen" (7784 Allegany, 54034 Rensselaer), so cogeneration alone does not
distinguish 54034.

**(c) From `_nyiso214_duct_gap_census.json`:** **54034 is `boundary_clean`** — it is one of the 17,
not one of the six boundary-contaminated plants. Its CAMPD-basis statistics are therefore citable
under nyiso-214's boundary discipline, and this document states that basis wherever it uses one.

**(d) From the code, read not measured:** `campd_bins.py:2333` and `offer_curves.py:1037` set
`pct_mc = 0.0`, `pct_peak = room` for a cohort plant, routing its whole dispatchable capacity to
the class **peak** band; `FleetArrays` carries `heat_rate`, `vom`, `emission_rate`; `run_year`
returns `fuel_prices`. So `mc = HR × F + VOM + ER × C` is decomposable **by identity**, which is
what P3 exploits.

**(e) Governance and environment, measured this session:** keeper `run_config.json` reads
`mode = backcast`, **`hindcast = False`**, `cc_reserve_duty_split = True`, `cc_duct_peaking = True`,
`capacity_screen_peak_measured_hindcast = False`. The keeper's `cache_key` **re-measured at this
HEAD is `95d4d8d167373eb7`** (its committed `solve_surface.fingerprint` is `48353917f7510af3` at
`git_sha 51f2fc2d`). No solve is spent, so the key is recorded, not used.

**(f) NOT measured, and deliberately behind the gates:** 54034's heat rate, its fuel-price series,
its emission rate; the 2×2 zone/cost swap; either zone's price distribution at any threshold;
54034's **per-year** CAMPD online share; and its measured load-when-online and run-length profile.

## 3. G-DRIFT (rule 29(b)) — `51f2fc2d` → `71e62675`, audited before any arm

`git diff` over `src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference`: **14 files, +9,523 / −23.** The set has
**grown by three files since nyiso-215 audited `51f2fc2d..dcb609f4`** (11 files), and the new
hunks are audited here rather than inherited.

| file | verdict | reason |
|---|---|---|
| `data/raw/_validation-source/**` (4 paths) | INERT | SPP LMP actuals + a CAISO 2022 demand CSV + README/provenance; neither ISO nor year is NYISO 2023–2025 |
| `config/constants.py` | INERT | one `NUCLEAR_MONTHLY_CF_BY_YEAR["CAISO"][2022]` row (caiso-262) |
| `config/fuel_trajectories.py` | INERT | `STATE_CARBON_PRICE_BY_ISO["CAISO"][2022]` added; the NYISO dict is untouched |
| `data/fuel/__init__.py`, `data/fuel/basis/__init__.py` | INERT | pure re-export of one new ERCOT symbol |
| `data/fuel/basis/ercot.py` | INERT | ERCOT branch (`ercot_zonal_gas_basis_source_group`, ercot-daily-gas-basis) |
| `model/interchange/spec.py` | INERT | three CAISO 2022 depth rows (caiso-262) |
| `pipeline/backcast_config.py` | INERT | SPP coal-class band identity entries; NYISO `CC_REGULAR` is not a coal key |
| `results/cache.py` | INERT | docstring epoch note for capx D76-ARM-B; no solve behaviour |
| `config/scenarios.py` | INERT | two hunks: a new default-off ERCOT flag `ercot_zonal_spread_ep_referenced` absent from the keeper's recipe; and the `capacity_screen_peak_measured_hindcast` default flip, whose `__post_init__` coercion restores the frozen `False` for **`hindcast = False`** configs — which the keeper is (§2e) — and whose consumer a `mode="backcast"` run never enters |
| `data/eia930/actuals.py` | **LIVE** | `_screen_fuel_spike_columns` screens EIA-930 `NG:` unit-slip hours for **every** BA (lane SPP-41) and can therefore move the C1/C4 benchmark and the delivered VRE profile |

**The one LIVE hunk is discharged by execution, not by reading**, and that is what P1 exists for.
`scripts/probes/nyiso196_rebuild_checks.py --year 2024` was run at this HEAD and **reproduced its
committed record byte-identically** with `git status --porcelain -uno` **empty**. P1 below
re-tests the same question on the exact quantities this session cites. **This session does not
re-solve and does not re-score C1 or C4**, so the benchmark half of that hunk is out of scope and
is passed forward, not absorbed: a NYISO lane that re-solves or re-scores C1/C4 still owes it a
check.

## 4. The gates — declared before any number behind them was read

Every partition below is checked to cover the whole outcome space. nyiso-215's P2 landed in a gap
between its own three declared branches; each partition here is closed by construction and the
closure is stated with it.

### P1 — REPRODUCTION BAR (this is a bar, not a hypothesis)

Rebuild the keeper's fleet (`fleet_only`) for 2023, 2024 and 2025 at this HEAD and recompute
nyiso-215's P4 construction — per-plant `mc_peak` hour-mean and implied on-share against the
keeper's own committed per-zone P1 LMP.

**Declared:** for **all seven** plants in **all three** years, the implied on-share reproduces the
committed record to **≤ 0.005 absolute** and `mc_peak` hour-mean to **≤ 2.0 % relative**.
**VOID on any breach** — the §3 audit would then be wrong by execution and every gate below is
void. *(Partition: reproduces / VOID. Exhaustive.)*

### P2 — THE SWAP DECOMPOSITION: is the flip PRICE-side or COST-side?

**Construction, declared now.** Over the 8,760 committed P1 hours of each year, with
`A` = 54034 and `B` = the six other cohort plants:

* `S(A, z) = mean_t 1[ mc_peak_A(t) ≤ LMP_z(t) ]`
* `S(B, z) = Σ_p w_p · mean_t 1[ mc_peak_p(t) ≤ LMP_z(t) ]`, `w_p = pmax_p / Σ pmax` over the six
  (the same capacity weighting nyiso-215 reported the cohort figure under)
* `z ∈ {CH = Capital_Hudson, UW = Upstate_West}`

Then, **exactly and with no residual by construction**:

* `G = S(B,UW) − S(A,CH)` — the observed gap
* `price_leg = S(A,UW) − S(A,CH)` — same cost, swap the price
* `cost_leg  = S(B,UW) − S(A,UW)` — same price, swap the cost
* `price_leg + cost_leg = G` identically

**Per-year classification, disjoint and exhaustive over the reals, in this order:**

1. **DEGENERATE** if `G ≤ 0`.
2. otherwise let `r = cost_leg / G` (which may be negative or exceed 1):
   **COST** if `r ≥ 0.80`; **PRICE** if `r ≤ 0.20`; **MIXED** if `0.20 < r < 0.80`.

**Verdict** = the class holding in ≥ 2 of 3 years; if all three years classify differently,
**NO-MAJORITY**. *(Every (G, r) pair lands in exactly one branch, and every year-triple lands in
exactly one verdict. Closed.)*

**PREDICTION: COST in ≥ 2 of 3 years.**

**The limb that HURTS this prediction, declared separately and scored separately:** I further
predict `price_leg ≤ 0` in **≥ 2 of 3** years — moving 54034 to `Upstate_West` should *lower*, not
raise, its on-share, because UW is the cheaper zone (§2a), so cost must over-explain (`r ≥ 1`).
**If instead `price_leg ≥ +0.10 absolute` in ≥ 2 of 3 years**, then `Capital_Hudson`'s price
*shape* is materially adverse to 54034 at its own threshold, the zone is load-bearing after all,
and my clean cost story is **partially defeated even if `r` still reads COST**. I will report that
as a partial defeat rather than restate the gate.

### P3 — THE COST DRIVER, by exact identity

With `A` = 54034's peak tranche and `B` = the capacity-weighted six, on hour-means, and
`C` the resolved carbon price:

* `Δ = mc_peak_A − mc_peak_B`
* `HR   = (HR_A − HR_B) · (F̄_A + F̄_B)/2`
* `FUEL = (F̄_A − F̄_B) · (HR_A + HR_B)/2`
* `OTHER = (VOM_A + ER_A·C) − (VOM_B + ER_B·C)`
* `COV = Σ_p w_p·HR_p·F̄_p − HR_B·F̄_B` — the cross-plant covariance the cap-weighting introduces,
  named now so it is not discovered later as a residual

`HR + FUEL + OTHER + COV = Δ` must hold to **< $0.01/MWh**; a larger residual is a **VOID on P3**.

**Per-year classification, disjoint and exhaustive, evaluated in this stated order** (the order
resolves the only ambiguity — two terms can both exceed half only if another is negative):

1. **SIGN-FLIP** if `Δ ≤ 0`.
2. otherwise **HEAT-RATE** if `HR/Δ ≥ 0.50`; else **FUEL** if `FUEL/Δ ≥ 0.50`; else **OTHER** if
   `OTHER/Δ ≥ 0.50`; else **COVARIANCE** if `COV/Δ ≥ 0.50`; else **MIXED**.

**Verdict** = modal class in ≥ 2 of 3 years; all three different → **NO-MAJORITY**. *(Closed.)*

**PREDICTION: HEAT-RATE in ≥ 2 of 3 years.**

**The limb that HURTS:** I predict `FUEL/Δ < 0.25` in **all three** years. If the fuel term reaches
**≥ 0.25 in any year**, then part of 54034's out-of-merit position is a **zonal gas basis** effect —
a price-side story wearing a cost-side coat — which partially reinstates the zone as a cause even
if P2 reads COST. Reported as such.

**Also reported, not gated:** the implied *base* heat rate (`HR / 2.25`) for A and for each of the
six, so a reader can see whether 54034's underlying physics is high or whether the multiplier is
doing the work.

### P4 — MEMBERSHIP ON THE RULE: does 54034 qualify robustly?

Recompute 54034's CAMPD plant-summed online share with `derive_reserve_duty_cc`'s **own**
construction (`grossLoad ≥ max(1.0 MW, 0.05 × plant p99.5 HSL)`), **per year** as well as pooled.
`derive_reserve_duty_cc.py` is **AUDITED, never re-derived** (rule 23 `[R-FROZEN-DERIVE]`): no
source data changed and this session writes no derive artifact.

**Classification, disjoint and exhaustive:**

* **ROBUST** — pooled `< 0.10` **and** all three per-year shares `< 0.10`.
* **MARGINAL** — pooled `< 0.10` **and** ≥ 1 per-year share `≥ 0.10`.
* **FAILS** — pooled `≥ 0.10`.

**PREDICTION: ROBUST.**

**The limb that HURTS:** **MARGINAL** would say the pooled statistic hides a year in which 54034 is
not a duty-role plant at all, while the mechanism holds it out of merit in that year regardless —
a membership defect on the same two-basis family nyiso-215 §3 opened.

**A reproduction bar, not a prediction (the value is disclosed in §2b):** the nearest non-member
above 54034 sits at `0.1700` (56188 Pinelawn), so the `0.0635 → 0.1700` population gap straddling
the `0.10` threshold is expected to reproduce; I record it to confirm the threshold is not
knife-edge, and claim no predictive credit for it.

### P5 — BEHAVIOURAL COHERENCE: is 54034 unlike its six in the METER, not the model?

Over CAMPD 2023–2025, for **each cohort plant that has a CEMS record** — six of the seven; **7784
Allegany has none** (§2b, and nyiso-214 lists it boundary-contaminated for exactly that reason), so
it is excluded here and that exclusion is stated, not silent — measure, on the CAMPD basis on both
sides and in every year: (i) pooled online share, (ii) **intensity when on** = mean `grossLoad`
over online hours ÷ plant p99.5 HSL, (iii) **mean run length** in contiguous online hours.

**Classification of 54034 against the range spanned by the other five, disjoint and exhaustive:**

* **COHERENT** — both (ii) and (iii) inside the other five's measured min–max range.
* **OUTLIER-INTENSITY** — (ii) outside, (iii) inside.
* **OUTLIER-DURATION** — (iii) outside, (ii) inside.
* **OUTLIER-BOTH** — both outside.

**PREDICTION: COHERENT** — 54034's *measured* conduct is cohort-like, and the divergence is
entirely on the model side.

**The limb that HURTS:** **OUTLIER-INTENSITY** or **OUTLIER-BOTH** would say 54034 is a genuinely
different kind of plant and the membership rule pools two behaviours under one threshold.

## 5. What each outcome means for the deliverable

* **P2 COST + P3 HEAT-RATE + P4 ROBUST + P5 COHERENT** → the **clean negative**: the sign flip is a
  cost-level artifact at a plant with a genuinely high heat rate, the cohort's membership is
  coherent, and the defect is **entirely** nyiso-215 §6's level question, which is the **owner's**
  card and stays untouched. This *strengthens* the existing card by removing a competing
  explanation; it does not open a new one.
* **P4 MARGINAL/FAILS or P5 OUTLIER-\*** → a measured **membership** defect in
  `cc_reserve_duty_split`, reported at full magnitude. Still no form is built or proposed.
* **P2 PRICE/MIXED or P3 FUEL** → the level card's framing needs a **zonal** term, reported to the
  owner as an amendment note to card (vii). **No form, no sizing, no recommendation** — sizing
  invites choosing, and (vii) is not mine.
* **Any VOID** → the session reports the VOID as its result and stops. A gate that misses is a
  result, not a drafting problem, and no gate below is restated after its number is seen.

## 6. Standing commitments

* **No gate is rewritten after its number is read.** Magnitude limbs that miss are reported as
  written (the nyiso-212 / nyiso-215 standard).
* **No analytic claim is asserted untested.** nyiso-215's PREREG argued CF ≤ online share as an
  identity and it is not one; nothing here rests on an unmeasured ordering. In particular §2a's
  observation that `Capital_Hudson`'s *mean* price exceeds `Upstate_West`'s is a **measured**
  hour-mean from the committed record, and P2's `price_leg` limb tests the *distribution* claim
  that it does not imply.
* **Basis discipline:** CAMPD on **both** sides in **every** year, stated at each use. No
  CAMPD-basis gap is ever quoted as a C1 number (C1 scores against bench `classFull`, which sits
  below the CAMPD plant sum by −0.44 / −2.38 / −0.34 TWh in 2023/24/25). **EIA-923 2025 is the
  preliminary vintage and returns 0.0 for small plants** — a 2025 EIA-923 zero is *undefined*, never
  a measurement, and no gate here uses one.
* **Rule 22:** training tier only. No out-of-training year is solved, scored or registered.
  `complete` / `frontier` and the locked-test freeze are untouched; **2020/2021 stay unspent and
  are not this session's spend**; `final` remains never granted. No promotion is contemplated, so
  D-5(b) does not attach.
* **Rule 15:** no run is produced, so there is nothing to register and keeper-only retention is
  untouched. **Rule 28:** NYISO's matrix shard cell for `cc_reserve_duty_split` (registered on the
  `offer_curve_by_group` base row) is stamped in this session with whatever this audit finds,
  negative outcome included.
* **The seven pending owner rulings are untouched and none is prejudged.**

*(nyiso-216, 2026-09-07. Written and pushed before P1–P5 were measured.)*
