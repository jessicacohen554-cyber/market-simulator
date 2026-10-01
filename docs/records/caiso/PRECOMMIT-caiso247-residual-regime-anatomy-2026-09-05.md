# PRECOMMIT — caiso-247: PHASE-0 RESIDUAL ANATOMY on the caiso-246 keeper. Split every 2023 / 2024 / 2025 ZONE-HOUR by what sets the model's price, and attribute the C3a gap by month × regime. ZERO LP, NOTHING ARMED. Pushed BEFORE any measurement of the object.

**Session caiso-247, 2026-09-05.** Branch
`claude/caiso-backcast-calibration-247-zxaba3` off `main` `c9f1d26e` (caiso-246
merged as #4751). Keeper at open **`2026-09-05-caiso-246-b1-spot`**
(bundle `caiso246_b1_spot_coverage`, `git_sha` `900402b`), **NOT-YET**, C3a the
sole load-bearing FAIL at **+3.9 / +12.3 / +11.4 %** (2023 PASSES;
load-weighted model/actual 56.29/54.17, 38.92/34.65, 38.36/34.42 $/MWh).
No `complete` / `final` marker; holdout freeze ACTIVE; **every read stays
inside 2023–2025**.

This document is pushed to `origin` **before the probe is written and before
any cell of the object is computed.** Nothing in §2 was measured first.

---

## §0 — WHAT THIS SESSION IS

### §0.1 — The object: queue item A, taken as ranked

The handoff ranks **A. PHASE-0 RESIDUAL ANATOMY ON THE NEW KEEPER
(zero LP, measure-don't-arm)** first. It is taken as ranked, on-queue
(rule 28(a); `docs/mechanism-testing-matrix.md` §5.2, CAISO lever queue).
Items B / C / E / G are owner objects or need a charter; D is a methodology
question; F is re-read below and not opened. **No mechanism is tested, so no
matrix cell moves** — this session's rule-28(b) duty is discharged by the
evidence append described in §4.

**The question.** C3a is the lane's single load-bearing failure and its
carrier has never been attributed by *price-formation regime* over a whole
year. Two live readings compete:

* the **hub-basis** reading — caiso-244 §3.6 measured an import row marginal
  at its WECC node with the corridor link unbound in **19.9 / 17.7 / 23.0 %**
  of hours, so in those hours the model's NP15 / SP15_rest price **IS** an
  import offer (raw Palo Verde hub + adders, Malin + wheel + CARB, or one of
  the two **fitted** firm prices $28 / $48). A residual there is a
  **hub-basis / firm-price** residual, not a domestic-offer residual;
* the **domestic offer surface** reading — caiso-242 §2.4 / caiso-243 P-5 /
  caiso-246 §3 (CC_REGULAR +1.467 TWh displacing imports −1.531 TWh on a
  three-month gas repricing) put the carrier on the CA gas offer stack.

They are not exclusive and no session has adjudicated between them on the
scored statistic. **This one measures the split and does not arm.**

### §0.2 — What is already known, and is NOT re-measured

* caiso-245 §3 measured December ONLY, and on the **model** price by regime,
  not on the residual: Dec-2025 model lw **44.6** (import-marginal) vs
  **44.0** (domestic-marginal) against a 34.97 actual — a level common to both
  regimes. The **residual** by regime needs the actual in those hours and has
  never been computed; that is this session's new content.
* caiso-244 §3.5: the two fitted firm prices are **bound-setting** on
  0.7–3.3 TWh/yr; caiso-245 §3(b): **`DSW_solar_PV` at $48 is the marginal
  offer in 101 Dec-2025 hours.** Never quote them as inert (caiso-244 §7.4).
* caiso-246 §3: the 2025 residual now sits in Apr–Jul (+5.0 / +3.9 / +4.3 /
  +4.1) and December (+8.6); 2024 (+12.3 %) is 12/12 covered and is **not** a
  coverage object.
* caiso-186os L4 measured this instrument's own bias (§1 G-GAP).

### §0.3 — Admissibility, stated against interest

**Nothing enters the model.** No `ScenarioConfig` field, no CLI flag, no
solve, no fleet change; `data/clean` is regenerated only so the on-recipe
fleet rebuild can run. Rule 13 `[R-MEASURED]` is not engaged because no
measured quantity is being fed to the LP — the actual hourly RT LMP is used
**only as the scoring comparator it already is**
(`data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet`, the same
series the rubric's `avgLMP.rt_lw` is built from). Using it to *attribute* a
residual is diagnosis; using it to *close* one would be pinning, and this
session does neither.

### §0.4 — HARD STOPS

1. **NO ARM, NO SOLVE, NO FIELD, NO FLAG — whatever the result.** Item A is
   measure-don't-arm by charter. Any arm this measurement motivates needs its
   own PRECOMMIT in a later session.
2. **Years 2023 / 2024 / 2025 only.** The holdout freeze is active and no
   marker exists; no out-of-training year is read, solved or scored.
3. **No parameter is derived, swept or fitted here.** The only numbers this
   session produces are measurements of a committed keeper.
4. If the instrument fails its own gates (§1), **no attribution is claimed**
   for the failing year and the finding says so in its headline.

### §0.5 — THE HAZARD

caiso-241 → -246 have each moved C3a in the **favourable** direction; the
sixth would be the next. **This session spends no arm, so the count stays at
five** — and nothing below is scored on whether it helps C3a. The specific
hazard here is different and worse: an attribution instrument can be steered
by its taxonomy. Two guards, both fixed now: the regime taxonomy in §1 is
frozen before any cell is computed, and §2 registers **falsifiers in both
directions** for the headline discriminator, so "the hub is the carrier" and
"the hub is acquitted" are equally reportable outcomes.

### §0.6 — DO-NOT-REDO acknowledged

caiso-246 §8 (the 2025 coverage gap is CLOSED — no F923-side repair for
Sep–Nov 2025; never predict a month-scoped arm leaves adjacent months at
0.000, storage couples them by ~$0.6/MWh; never quote +0.442 TWh as the CC
elasticity), caiso-245 §7 (never re-key the firm split on RA holdings; never
attribute the December slab to import-marginal hours; never quote the firm
prices as inert), caiso-244 §7 (the `import` klass is GROSS; cite §2.2 not
caiso-242 §3; the over-import is not the 8,800 MW ladder; caiso-202 §C's
< 5 % is not the import-marginal share; December is not an import-VOLUME
object; never rebuild a recipe by parameter name), caiso-243 §10, caiso-242
§9, caiso-241 §10, caiso-240 §7, caiso-239 §8, caiso-230 §9 — **read in full,
none re-opened.** In particular caiso-230 §9.2 (locational repricing is
mean-preserving on C3a) is why this session decomposes the gap by **regime**,
not by zone.

---

## §1 — THE ESTIMATOR, NAMED, AND ITS GATES

### §1.1 — Instrument

The **caiso-244 dual-merit reconstruction**
(`scripts/probes/_caiso244_import_level_anatomy.py`: `rebuild` on
`replay_keeper.run_year_kwargs`, `sidecars`, `reconstruct`), imported
verbatim — the caiso-245 §3 code path — re-pointed at
`results/calibration/caiso246_b1_spot_coverage`. Zero LP: the fleet is
rebuilt `fleet_only=True` and every dispatch state comes from LP
complementarity against the keeper's **committed P1 duals**.

### §1.2 — The gap decomposition (the caiso-131 §2 / caiso-140 §A convention)

The C3a gap is decomposed **over zone-hours**, on the rubric's own weights
applied to **both** sides:

* `w_t` = measured system load (`eia_loader.load_demand(CAISO, y).sum(axis=0)`)
  — the weights `avgLMP.rt_lw` is built on;
* `s_{z,t}` = model zone demand share over the five CA load zones
  (NP15, ZP26, LA_BASIN, SDGE, SP15_rest), from `hourly/system_<y>.parquet`;
* `a_t` = the committed hourly actual RT LMP;
* cell contribution `C(z,t) = w_t · s_{z,t} · (λ_{z,t} − a_t) / Σ_{t∈ok} w_t`.

Since `Σ_z s_{z,t} = 1`, the cells sum **exactly** to
`gap_hourly = Σ_t w_t (λ_t − a_t)/Σ w_t` with `λ_t` the CA-load-weighted model
price — the same statistic caiso-186os L4 used. Hours with a null actual
(2023 has 48) are excluded from both numerator and denominator.

### §1.3 — The regime taxonomy, FROZEN NOW

Each **zone-hour** `(z,t)` gets exactly one label, in this priority order:

1. **HUB_FITTED** — a landing zone `L ∈ {NP15, SP15_rest}` has an import row
   marginal at its WECC node (`|c − λ_WECC| ≤ TOL`) with the corridor link
   unbound (`|λ_WECC − λ_L| ≤ TOL`), that row is one of the two **fitted**
   firm rows (`PNW_hydro_base` $28 / `DSW_solar_PV` $48), and
   `|λ_{z,t} − λ_{L,t}| ≤ TOL` (the internal link is unbound so the hub price
   reaches `z`);
2. **HUB_MEASURED** — the same, with the marginal row priced off a **measured**
   hub series (`PNW_midC`, `DSW_CCGT`, `DSW_CT`, `WECC_scarcity`,
   `DSW_{surplus,overnight,daytime}_clean`);
3. **DOM_GAS** — an available domestic gas unit (`CC_REGULAR`, `CC_CHP`,
   `CT_PEAKER`, `CT_CHP`, `ST_GAS`, `ST_CHP`) has `|mc_{g,t} − λ_{z,t}| ≤ TOL`;
4. **DOM_OTHER** — the same for any other available domestic unit;
5. **STORAGE** — no unit matches and system storage is active at `t`
   (`charge_mw > 0` or `discharge_mw > 0`);
6. **SURPLUS** — no unit matches, storage idle, and `λ_{z,t} ≤ 0.01` or the
   hour carries `dump > 0`;
7. **UNRESOLVED** — everything else.

`TOL = 0.05 $/MWh`, the caiso-244 value, **reported not tuned.** Where both a
HUB and a DOM_GAS match exist the priority above decides; the **overlap count
is reported**, and a **reversed-priority variant (DOM_GAS before HUB)** is run
as the taxonomy's own falsifier (§1.4 G-ORDER).

### §1.4 — Gates

* **G-RECON** (the caiso-244 instrument's own gate, re-run on the NEW keeper):
  the reconstruction reproduces the committed `import` klass to ≤ 1 % annual
  energy and < 100 MW hourly RMSE on one of the two bases, in each year.
  **FAIL in a year → no HUB attribution is claimed for that year.**
* **G-GAP:** `|gap_hourly − (model_C3a − rt_lw)| ≤ 1.00 $/MWh` in each year.
  The two differ by construction (the rubric's model side is a zone-demand
  weighted mean of zone **equal-hour** means; `gap_hourly` is hourly and on
  measured load), and caiso-186os L4 measured that bias at
  **0.78 / 0.48 / 0.81 $/MWh** on an older keeper. **FAIL → the instrument is
  reported as SHARES-ONLY** and no cell is quoted in $/MWh.
* **G-CLASS:** UNRESOLVED carries ≤ 12 % of the rubric weight in each year.
  **FAIL → the attribution is reported as WEAK, with the unidentified share
  named in the headline.**
* **G-ORDER:** the headline discriminator (§2 P-5) does not change sign of its
  verdict under the reversed-priority variant. **FAIL → the verdict is
  reported as taxonomy-dependent and NOT used to rank any object.**
* **G-BENCH:** the recomputed `rt_lw` from the hourly actual reproduces the
  committed `avgLMP.rt_lw` to ≤ 0.01 $/MWh in each year (the comparator is the
  one the rubric scores on). **FAIL → stop; the comparator is wrong.**

### §1.5 — The headline statistic

**Concentration ratio** for a regime `R`:

    CR(R) = [share of gap_hourly carried by R] / [share of rubric weight in R]

`CR = 1` means the residual in `R` is exactly the system-average level — the
regime is **not** a carrier, it is just where the hours are. `CR > 1` means
the residual is concentrated there. This is the discriminator the handoff's
falsifier is written against, and it is scale-free, so a regime with few hours
cannot look large merely by being expensive.

---

## §2 — PREDICTIONS, REGISTERED BEFORE ANY MEASUREMENT

Windows are deliberately **wider** than instinct: caiso-246's post-solve
windows were 3.3× too small on the dispatch response (§5.3 there), and the
correction is to register wide and then score against interest, not to register
narrow and explain a miss. Every one is falsifiable and none is a gate.

| # | prediction | falsifier / what it would mean |
|---|---|---|
| **P-1** | **G-RECON passes in all three years on the gross basis** on the caiso-246 keeper, as it did on caiso-243 | fail → no HUB attribution that year |
| **P-2** | **G-GAP holds**: `gap_hourly` is BELOW the printed gap in all three years, by 0.3–1.0 $/MWh | above the printed gap, or > 1.0 apart → shares-only |
| **P-3** | **G-CLASS**: UNRESOLVED ≤ 12 % of weight in every year. *Uncomfortable* — storage- and hydro-marginal zone-hours may not price-match at all | > 12 % → attribution reported WEAK |
| **P-4** | HUB (FITTED + MEASURED) carries **20–34 %** of the rubric weight in each year, and the 2025 share is the largest of the three | outside → the zone-hour propagation differs materially from caiso-244's hour-level 19.9/17.7/23.0 % |
| **P-5** | **THE DISCRIMINATOR.** `CR(HUB)` lands in **1.0–1.8** in BOTH 2024 and 2025 | **`CR(HUB) < 1.0`** → the Palo Verde hub + adder chain is **ACQUITTED** and the object is the domestic offer surface (the handoff's own falsifier). **`CR(HUB) > 1.8`** → the hub chain is the dominant carrier and item C / the hub-basis question outranks the domestic surface |
| **P-6** | **HUB_FITTED** carries **≥ 25 %** of the total HUB gap contribution in 2025. *Uncomfortable* — it is the strongest form of the "$28/$48 are live" reading | < 25 % → the fitted prices are NOT the hub carrier; item B stays a G-26 honesty item and is DEMOTED as a C3a object |
| **P-7** | **THE 2023 CONTROL.** `CR(HUB)` in 2023 (the year C3a PASSES) is within **±0.4** of the mean of 2024 and 2025 | 2023 more than 0.4 BELOW → the hub regime IS what separates the passing year from the failing ones, and the hub becomes the ranked object regardless of P-5 |
| **P-8** | In 2025, **Apr–Jul together carry more of `gap_hourly` than December does**, and inside Apr–Jul the DOM_GAS share exceeds the HUB share. *Uncomfortable* — it contradicts the lane's December focus | either leg fails → December is the ranked month object and the Apr–Jul slab is secondary |
| **P-9** | **STORAGE** carries **5–20 %** of the rubric weight in 2025 | outside → the caiso-246 §5.1 storage coupling is either negligible or far larger than that finding implies |
| **P-10** | Every regime's CR in 2024 and 2025 lies in **[0.6, 2.2]** — i.e. NO regime is more than ~2× the system-average residual. *Uncomfortable* — it predicts the residual is substantially a LEVEL and that this measurement will NOT hand the lane a single carrier | any regime outside → that regime is the carrier and the object is named |

**Pre-solve vs post-solve:** all ten are computed by one probe run; there is no
solve. P-1/P-2/P-3 are instrument predictions, P-4–P-10 are the object.

---

## §3 — STOP RULE

* **G-BENCH fails** → stop, fix the comparator, claim nothing.
* **G-RECON fails in all three years** → the finding reports the instrument
  failure, claims **no** attribution, and the session ends with a negative
  result. No arm is proposed on a failed instrument.
* **G-CLASS > 25 %** (twice the registered bound) → the attribution is
  reported as **not usable for ranking**; P-5's verdict is withheld.
* **G-ORDER fails** → P-5's verdict is reported as taxonomy-dependent and is
  not used to rank any object.
* In every case the run is registered and the finding published; a negative
  result is the deliverable, not a reason to keep measuring until something
  moves.

---

## §4 — WHAT THIS SESSION DELIVERS, AND WHAT IT DOES NOT

**Delivers:** this PRECOMMIT; `scripts/probes/_caiso247_residual_regime_anatomy.py`
+ `results/calibration/_caiso247_residual_regime_anatomy.json`; a finding
scoring all ten predictions against interest; the calibration-log entry; and
the **evidence-only** append to the CAISO matrix shard naming what the
measurement says about `import_hub_pricing` / `measured_offer_surface`
without moving any cell (no mechanism is tested — rule 28(b) attaches to
evidence, per the caiso-236 precedent recorded in that shard).

**Does not:** arm anything; move a keeper; register a new bundle (there is no
solve, so there is no run to register under rule 15 — the deliverable is the
probe artifact and the finding, as at caiso-244 and caiso-245, both ZERO-SOLVE
sessions); touch items B / C / E / G, the transport adder (D), the CT_PEAKER
volume miss (F), the SoCalGas OFO arm, the DOF-provenance instrument, or any
other ISO's shard (rule 25).

**Promotion basis:** none — nothing is promoted. C3a is not moved by this
session and no direction is claimed.

---

## §5 — OWNER ASKS THIS WILL SHARPEN (not answer)

1. **Item B** (the two fitted firm prices) — P-6 measures whether they carry
   the hub residual on the scored statistic, which is the missing input to the
   "is there a measured contract-cost source" decision.
2. **Item C** (the north-corridor firm block's energy basis) — P-5/P-7 say
   whether the import seam is where the scored residual lives, which is what
   should decide whether form (ii)'s OASIS re-fetch is worth a session.
3. **Item E / F** (fuel-invariant-margin flatness; CT_PEAKER volume) — P-8's
   Apr–Jul leg says whether the domestic gas surface is the ranked object.
