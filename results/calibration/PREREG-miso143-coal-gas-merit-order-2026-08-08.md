# PREREG — miso-143: the coal-vs-gas MERIT ORDER in the 2025 high-gas regime (§5.4 queue item 4). Phase 0, diagnosis-first, no solve unless a gate licenses one.

**Session:** miso-143, 2026-08-08. **Lane:** §5.4 queue **item 4 (NEW)** — the
successor candidate **(A)** named but explicitly *not opened* at miso-142.

**Posture at open:** keeper `2026-08-05-miso-132b-cc-committed` (bundle
`results/calibration/miso132_ccmin_B`), **UNCHANGED**. No `ScenarioConfig`
field. No mechanism armed. **No LP solved** — a solve is licensed only at G-C,
for at most ONE mechanism, and only after its kill gates pass.

**Owner directive honoured:** the target is the **2024/2025 mean-LMP level
miss**, and specifically the owner's 2026-08-08 addition — *close the 2025
−14 % LMP underrun WITHOUT disturbing the other metrics*. No C7 lane, no C7
ledger.

**This document is pushed BEFORE any adjudicating statistic is computed.**
Everything below the line is fixed now: ten falsifiable numeric predictions,
four pre-committed verdict branches (including the explicit
"gain is a rounding error → candidate (A) CLOSES" branch), seven kill-gate bars
fixed before their numbers are seen, and six traps each carrying its own
counter-measurement.

---

## 0. §0 RE-VERIFIED FROM COMMITTED ARTIFACTS (not from the charter prompt)

`.venv/bin/python scripts/calibration_verdict.py --run-id 2026-08-05-miso-132b-cc-committed`
— committed artifacts only, **no re-solve**, all three years in **ONE**
invocation (rule 16). Rule 22: MISO holds **no** marker in either block, so
2023–2025 only.

**`NOT-YET`, rubric v3.1, 8 criteria.**

| criterion | tier | status | detail |
|---|---|---|---|
| C1 fuel-mix by class | LOAD | **PASS** | **all 8 classes SKIPPED in 2025** — preliminary EIA-923 vintage |
| C2 system volume (gas/coal) | LOAD | **PASS** | **both families SKIPPED in 2025** — gas **−11.2 %**, coal **+4.2 %** |
| C3a mean LMP | LOAD | **FAIL** | RT **−0.4 / −6.0 / −14.1 %**; model **32.72 / 30.37 / 39.05** vs **32.85 / 32.30 / 45.46** |
| C3b price duration/shape | LOAD | **PASS** | NRMSE **0.075 / 0.112 / 0.191** (bar ≤0.20) |
| C3c price tail / scarcity | SUPP | **CAVEAT** | ledgered, **1 of 1**, all three years |
| C4 fleet hourly dispatch corr | SUPP | **PASS** | |
| C6 governance gate | PROT | **PASS** | |
| C8 forced-energy share (D-2) | PROT | **PASS** | ST_GAS **grounded above budget** 31.9 / 33.1 / **45.1 %** |

DA companions (diagnostic, not gated): **−4.4 / −8.4 / −15.8 %**; DA−RT premium
**+1.38 / +0.84 / +0.89**. Determination basis: *"undocumented out-of-tolerance
(FAIL) criteria: **price_mean**"* — **C3a is the SOLE FAIL**.

**Identical to the charter §0 in every cell.** Determination unchanged.

*(Recorded because it is a live discrepancy in the artifacts, not in the
verdict: the bundle's own `metrics.json` carries `price_mean: CAVEAT`, while
the rubric-v3.1 scorer recomputes it to `FAIL`. The **scorer is authoritative**
— `metrics.json` is a stale write from an earlier rubric version. Noted, not
acted on; it changes nothing in this session and is not this session's object.)*

---

## 1. The object, and what miso-142 did and did not establish

miso-142 closed the **quantity** family: MISO's summer-afternoon supply-curve
slope is **+$0.637/MWh per GW** (se 0.032) against an actual **+$2.154**
(se 0.318) — **3.38× too flat** — and the model's own maximum clearing price in
2025 JJA h12–17 is **$51.97** against a load-weighted actual of **$74.68**.
Closing the **−$30.43/MWh** window deficit by quantity needs **47.7 GW** of
displacement against a **13.28 GW** cushion (**3.60×**). H1 was refuted in all
three years (ΔQ **+0.10 / +0.66 / +0.12 GW**, below the EIA-930 noise floor
**1.36 / 1.64 / 1.62 GW**).

**What it did NOT measure, and says so in its own §3:** a coal→gas substitution
at **constant thermal quantity** is a *different channel*. It changes **which**
unit is marginal, not **how many** MW are needed, so **the 0.637 slope does not
bound it**. miso-142 §6 names measuring that gain as *"the first thing a
successor should do"*.

**The miso-129 bar is already met for this object** — coal is not merely
co-occurring with the miss, it is *setting price*: the OLS of class dispatch on
total thermal requirement over 2025 JJA h12–17 gives COAL_PRB **+0.298** and
COAL_BIT **+0.138**, so coal absorbs **43.6 %** of the model's marginal thermal
MW (CT_PEAKER +0.320, ST_GAS +0.113, CC_REGULAR +0.099; slopes sum to 1.000).
Meeting the bar **licenses the question and answers nothing** (TRAP 2).

**The 2025 step change, on the scorer's own C2 basis:** coal
**−2.4 / −2.3 / +4.2 %**, gas **−5.4 / −2.7 / −11.2 %** — **+6.5 pp** and
**−8.5 pp** swings against two stable years, tracking the **$2.19 → $3.52/MMBtu**
gas move. **The model re-ranks coal ahead of gas harder than the real market
did.** Why, and what it is worth in $/MWh, is this session's whole question.

---

## 2. GATES

### G-A — MEASURE THE MERIT-ORDER GAIN BEFORE PROPOSING ANYTHING

**Instrument: the model's own MISO offer stack at HEAD, rebuilt from committed
artifacts.** Not an LP solve, not a keeper replay. The keeper's
`ScenarioConfig` is rebuilt from its committed `run_config.json`
(`_miso141_summer_derate_basis.keeper_config`, reused verbatim — DO-NOT-REDO),
and `runner.py`'s own offer sequence is reproduced in order:
`build_dispatch_fleet` → `generators_to_fleet_arrays` → `resolve_fuel_prices` →
`apply_coal_supply_pricing` → `assemble_mc` → `apply_eac_to_mc` →
`apply_coal_tranches` → `apply_gas_offer_margin` →
`apply_cc_committed_offer_margin` → `apply_interchange_injections`. Every step
gated by the keeper's own recorded flags; nothing added, nothing skipped.

**G-A0 — FOOTING, and it is a STOP GATE.** The rebuilt stack is cleared
merit-order against the model's **own** hourly thermal requirement (the keeper's
`class_hourly` sidecar, the same `THERMAL_COLS` definition miso-142 used) and
the resulting clearing offer is compared to the keeper's **committed P1 price**
(`system_2025.parquet`). Bars fixed here (§4, P1). A stack that cannot
reproduce the keeper's own prices is not an instrument for **levels**; if the
gate fails the session falls to **BRANCH-INSTRUMENT-FAIL** and reports **gaps
only**, with the gain as a bound and never a point.

**G-A1 — the three readings the charter asks for**, all on the model's own
basis so **no** EIA-930/EIA-923 instrument offset enters (TRAP 3):

(a) **The SRMC distribution of the coal tranches that are MARGINAL in the
window** — identified per hour as the tranche at the merit-order clearing
point, not by class label.

(b) **The SRMC of the gas tranches sitting immediately above them** — the next
$/MWh rungs of the same ladder, in the same hour.

(c) **The headline gain.** Re-clear each window hour with the **economic** coal
tranches' available capability scaled down by the **MEASURED** C2 excess
(coal **+4.2 %** ⇒ ×1/1.042), letting gas fill at constant total thermal
quantity, and take the load-weighted Δ(clearing price). **The size of the
displacement is set by the measured fuel-mix miss, never by the price residual**
(TRAP 6 / rules 1, 13, 24). Reported **with its own uncertainty** and
**bracketed** by a clearly-labelled second reading at the EIA-930 hourly
displacement (**+14.6 %** coal in W1 2025) — two named instruments as endpoints,
never one mixed number (TRAP 3).

**Must-run coal is NOT displaced** — only tranches that can be marginal. Which
tranches those are is reported, not assumed.

**G-A2 — the stack's OWN slope, a new instrument.** miso-142's binned curve is
*empirical* (it mixes hours with different availability and fuel). The
merit-order ladder is the **true within-hour** curve. Both are reported side by
side; if they disagree, the disagreement is the finding and miso-142's bound is
re-stated with the correct instrument. **This is two-sided** (P5): the ladder
may be steeper, which loosens miso-142's quantity bound, or it may not, which
tightens it.

**THE PRE-COMMITTED CLOSE:** if the gain is a rounding error, **SAY SO AND
STOP** — candidate (A) closes, the lane re-points to candidate (B), and that is
a legitimate and reportable outcome, not a failure (**BRANCH-CLOSE**, §5).

### G-B — WHY THE MODEL RE-RANKS HARDER THAN THE MARKET

Entered **only** on BRANCH-MATERIAL or BRANCH-DOMINANT. Four candidate
mechanisms, **each measured, none assumed**, and **exactly one** may be named as
carrying it (rule 19 `[R-ONE-MECH]`):

**B-1 — the gas offer margin's FIXED-ANCHOR FORM (the session's leading
candidate, and it is a FORM question, not a fitted level).** The keeper arms
`gas_offer_net_revenue_margin=True` at `gas_offer_margin_anchor=3.0492`
$/MMBtu. `apply_gas_offer_margin` (`data/offer_curves.py:613`) applies
`mc[g,t] += markup_hr[g] × (anchor − fuel[g,t])`, i.e. the gas markup becomes a
**fuel-invariant** $/MWh margin fixed at the anchor. The anchor is the
**2023–2025 training-window mean** delivered gas. **Mechanically, therefore, the
mechanism compresses the year-to-year swing of gas offers around 2024**: in
**2023** (fuel < anchor) it **lifts** gas offers; in **2025** (fuel ≫ anchor) it
**cuts** them, by `markup_hr × (fuel − 3.0492)`. That is a **2025-specific,
monotone-in-gas-price** haircut on exactly the class the model under-runs, and
it would push coal ahead of gas **harder as gas rises** — the observed
signature. Predicted numerically at P6; **two-sided** (it may be inert).

**B-2 — delivered coal price passthrough vs the 2025 gas move.** The model's
window delivered coal $/MMBtu against the measured F923 / EIA-923 MISO
delivered coal price. A model coal price too low in 2025 re-ranks coal ahead of
gas directly. P7.

**B-3 — the coal tranche offer curve's own slope.** The keeper runs
`coal_tranche_1_fuel_passthrough=0.0` / `_2=0.35` / `_3=1.0` with
`coal_takeorpay_from_data=True`, `coal_committed_takeorpay_regulated=True` and
`coal_econ_srmc_bound=True`. If the sunk-fuel bands (0.0 / 0.35) are
**inframarginal** the tranche structure is not the merit-order channel; if they
are **at the margin** it is. P8 decides which, by measurement.

**B-4 — the CC/CT heat-rate distribution against measured conduct.** The
keeper runs `cc_committed_hr_mult=1.23`, `cc_econ_hr_mult=0.96`,
`cc_peak_hr_penalty=1.15`, `cc_steam_part_capacity=True`,
`cc_committed_per_plant=True`. Reported descriptively; it is named last because
it is the candidate least able to produce a **2025-specific** step.

**Rule 23 `[R-FROZEN-DERIVE]` is binding throughout G-B:** a measured-behaviour
parameter re-derives **only** when its SOURCE DATA updates — never because a
residual moved. **`miso_cc_coal_rebalance` is NOT a candidate and is not
re-opened**: it is already adjudicated (miso-114 / miso-115, transcribed in the
matrix) as defining its target against another *model* quantity ("above the
priced-import hurdle"), i.e. a tuned value with no measured identification.

### G-C — ARM, only if everything above resolves

Entered **only** if a **single** mechanism resolves with **measured
identification** AND **every kill gate in §3 passes on the pre-registered bar**.
Then: exactly ONE arm (rule 19); a **same-HEAD zero-delta control FIRST**; then
`replay_keeper --set`, one invocation per arm, `--years 2023 2024 2025` in a
**SINGLE** invocation (rules 12/16), arms sequential. Otherwise: report, name
the successor, queue it.

---

## 3. KILL GATES — bars fixed NOW, before their numbers are seen

The owner's *"without disturbing the rest"* is enforced here. Any arm reaching
G-C is scored against **all seven**; **failing any one means the arm is not a
fix**, whatever it does to C3a.

| # | gate | current | **BAR (fixed now)** |
|---|---|---|---|
| **KG-1** | **C3b 2025 NRMSE** | **0.191** | **must stay ≤ 0.200.** Headroom is **0.009**. Crossing 0.200 converts a PASS into a FAIL — that is a **net loss**, not a fix. |
| **KG-2** | C3a 2023 / 2024 | −0.4 % / −6.0 % | both must stay within **±10 %**. Closing 2025 by pushing 2023 past **+10 %** is not a fix. |
| **KG-3** | C1 / C2, **gated years only** | PASS | must stay PASS on **2023–2024**. **2025 IS UNGATED** (see §6) — its fuel mix is scored **DESCRIPTIVELY vs EIA-930** and reported as such, **never** quoted as a pass. |
| **KG-4** | C4 dispatch correlation | PASS | must stay PASS. |
| **KG-5** | C8 forced share | ST_GAS **45.1 %** (grounded), CT_PEAKER **10.7 %** | no material class's forced share may **rise**; CT_PEAKER must stay **< 15 %**; **no D-4 window may break**. |
| **KG-6** | C3c ledger | **1 of 1 — SPENT** | **no second ledger entry.** Under rubric v3.1 C3c is the only ledgerable criterion at all. |
| **KG-7** | determination | NOT-YET, fail set **{C3a}** | the fail set must not **grow**. |

**Rule 1 `[R-STRUCT]` is ONE-DIRECTIONAL and is not a licence here.** A
structurally-correct mechanism stays even if the residual worsens; that does
**not** license breaking a passing criterion to buy C3a. Rule 14: if an accurate
input makes the fit worse, **KEEP IT** and open the root cause.

**The `cc-high-cf-investigation` precedent is the standing warning:** in PJM,
removing a false capacity wall EXPOSED a CC offer-level miss and blew out the
fuel mix. **A merit-order arm changes fuel mix BY CONSTRUCTION** — C1/C2 are the
expected casualty, and KG-3's vintage caveat cuts **both ways**: 2025 being
ungated means C1/C2 PASS will **not** catch a 2025 regression either.

---

## 4. PREDICTIONS — falsifiable, two-sided, fixed before measurement

| # | prediction | point | falsified if |
|---|---|---|---|
| **P1** | **G-A0 FOOTING.** Rebuilt stack cleared merit-order vs keeper committed P1 price, 2025 JJA h12–17: median \|Δ\| ≤ **$4.00**/MWh **and** Pearson *r* ≥ **0.85** | median \|Δ\| **$2.50**, *r* **0.93** | either leg misses ⇒ **BRANCH-INSTRUMENT-FAIL** |
| **P2** | **Marginal class, from the stack.** Clearing tranche is **coal** in **30–55 %** of 2025 JJA h12–17 hours (cross-check on miso-142's OLS 43.6 %) | **42 %** | < 20 % or > 70 % ⇒ the two instruments disagree; the OLS reading is re-examined before anything is built on it |
| **P3** | **The SRMC gap at the margin.** Median (cheapest gas tranche immediately above) − (marginal coal tranche) in coal-marginal hours ∈ **[$2, $12]**/MWh | **$5.00** | outside the band |
| **P4** | **THE HEADLINE GAIN.** Load-weighted Δ(clearing price) from the C2-sized (+4.2 %) economic-coal displacement ∈ **[$0.50, $6.00]**/MWh | **$2.20** = **7.2 %** of the $30.43 deficit | outside the band |
| **P5** | **G-A2, two-sided.** The true merit-order ladder over the first +2 GW above the clearing point is **steeper** than miso-142's empirical **0.637** $/MWh/GW: ≥ **$1.00**/MWh/GW | **1.8×** = **1.15** | ≤ 0.637 ⇒ the empirical curve was **not** composition-biased and miso-142's quantity bound is **tight**, which is itself a reportable strengthening |
| **P6** | **B-1, the fixed-anchor form.** 2025 JJA h12–17 gas-offer **haircut** = cap-weighted mean `markup_hr × (fuel − 3.0492)` ∈ **[$0.60, $3.00]**; 2023 **uplift** ∈ **[$0.80, $2.50]**; **2023→2025 swing** ∈ **[$1.50, $5.00]** | haircut **$1.30**, uplift **$1.45**, swing **$2.75** (≈ **44 %** of the $6.28 annual C3a drift) | swing < **$0.50** ⇒ **inert**, B-1 dies; swing > **$8.00** ⇒ **dominant**, and B-1 alone would over-explain the drift, which would itself need explaining |
| **P7** | **B-2, coal price.** Model window delivered coal $/MMBtu within **±15 %** of the measured EIA-923/F923 MISO delivered coal price | **±5 %** | \|Δ\| > 15 % ⇒ a real input defect, and B-2 becomes the named candidate |
| **P8** | **B-3, tranche passthrough.** Cap-weighted mean effective fuel passthrough of the coal tranches that are **MARGINAL** in the window ≥ **0.85** (given `coal_econ_srmc_bound=True`) | **0.95** | < 0.85 ⇒ the sunk-fuel (0.0 / 0.35) bands **are** at the margin and the tranche structure **is** the channel |
| **P9** | **Self-check (TRAP 4/5).** Rebuilt window coal MW reproduces the keeper's own sidecar coal MW to within **1 %** | **0.2 %** | > 1 % ⇒ a class-mapping defect; **stop and fix before any verdict** |
| **P10** | **The verdict itself.** Stated as a prior **now**: **BRANCH-CLOSE 30 % · BRANCH-MATERIAL 55 % · BRANCH-DOMINANT 15 %** | **MATERIAL** | recorded against interest whichever fires |

---

## 5. PRE-COMMITTED VERDICT BRANCHES

Thresholds are on the **G-A1(c) headline gain**, against the 2025 JJA h12–17
deficit of **−$30.43/MWh**, and are fixed **now**:

- **BRANCH-CLOSE — gain < $1.50/MWh (< 5 % of the deficit).** **Candidate (A)
  CLOSES.** Report it plainly, arm nothing, mint no cell verdict (no mechanism
  tested), re-point the lane to **candidate (B)**, write §5.4 item 4 with the
  CLOSED verdict and (B) as the named successor. **This is a legitimate outcome
  and is reported as one, not hedged.**
- **BRANCH-MATERIAL — $1.50 ≤ gain < $9.13/MWh (5–30 %).** The object is
  confirmed **with reach**. Proceed to G-B. **Arm only if** G-B resolves to ONE
  mechanism with measured identification **and every KG bar passes**; otherwise
  report, name the successor, queue it. **A material gain does not by itself
  license an arm.**
- **BRANCH-DOMINANT — gain ≥ $9.13/MWh (≥ 30 %).** As MATERIAL, but mechanism
  identification takes the session's whole remaining budget and no arm is
  attempted on a partial identification.
- **BRANCH-INSTRUMENT-FAIL — P1 footing fails.** The stack is not trustworthy
  for **levels**. Report **gaps only** (differences survive a level bias that
  points cannot), give the gain as a **bound** with its own caveat, and make the
  instrument repair the named successor. **No branch above may be declared on a
  failed footing.**

---

## 6. THE DATA BLOCKER — DISCLOSED, NOT WORKED AROUND

EIA-923's **2025 vintage is PRELIMINARY**. C1 is **SKIPPED for all eight
classes** in 2025 and C2 for **both families** (gas **−11.2 %**, coal
**+4.2 %**). **MISO's largest measured fuel-mix miss, in its blocker year, is
currently UNGATED.** Three consequences, honoured throughout:

1. **C1/C2 PASS is NOT evidence against this charter's object.** The criterion
   that would have caught it did not run.
2. **C1/C2 PASS after an arm is NOT evidence the arm is safe in 2025.** KG-3
   therefore scores the 2025 fuel mix **descriptively against EIA-930** and says
   so explicitly.
3. **The substitution cannot be CERTIFIED against EIA-923 until the final 2025
   vintage lands.** That is a **reportable limit on the finding**, not a reason
   to skip the diagnosis.

---

## 7. TRAPS — each with its counter-measurement

**TRAP 1 — THE QUANTITY RELAPSE.** miso-142 closed the quantity family. Any
lever whose story is "there is too much / too little X in MW" must be multiplied
by **$0.637/MWh per GW** *before* it is proposed.
**Counter-measurement:** this charter's channel is **merit order at constant
quantity**, so the slope does **not** bound it — and that exemption is stated,
not assumed: **G-A2 measures the ladder explicitly** and P5 is two-sided. Any
*quantity*-shaped sub-claim that appears mid-session gets its product with 0.637
stated in the finding before it is entertained.

**TRAP 2 — CO-OCCURRENCE AS CAUSE (miso-129).** Coal being marginal licenses
**asking** the question; it does not answer it.
**Counter-measurement:** the verdict rests on **G-A1's SRMC-gap arithmetic and
the re-clear**, never on the +0.298/+0.138 correlation. P2 additionally tests
the OLS reading against an independent instrument (the merit-order clearing
tranche) rather than inheriting it.

**TRAP 3 — THE INSTRUMENT CROSSING.** EIA-930 hourly and EIA-923 monthly
disagree by **~6 %** on coal, a well-measured fuel. miso-142's raw EIA-930 read
(**+14.6 %** coal / **−18.3 %** gas in W1) is **NOT** on the scorer's basis
(**+4.2 %** / **−11.2 %**).
**Counter-measurement:** **LEVELS on the scorer's C1/C2 basis, SHAPES/WINDOWS on
EIA-930, never mixed**, and the offset stated. G-A1(c)'s bracketing reports the
two displacement sizes as **separately-labelled endpoints**, never averaged.
G-A1(a)/(b) and G-A2 are **model-only**, so no crossing enters them at all.

**TRAP 4 — THE COAL SIDECAR ALIAS.** The sidecar splits coal into
`COAL_BIT`/`COAL_LIGNITE`/`COAL_PRB` while `plant_group` is the bare `COAL`; an
unmapped lookup silently returns **ZERO** and hands the class back as phantom
headroom (~32 GW at miso-141).
**Counter-measurement:** the explicit asserted alias map carried over verbatim
from `_miso142_marginal_and_slope.py` (`SIDECAR_ALIAS = {"COAL": COAL_COLS}`)
plus a **LOUD assertion** on every class touched, and **P9** as a numeric
self-check.

**TRAP 5 — THE `klass` FIELD IS NOT `plant_group`.** `plant_group` is populated
for the **FOSSIL** classes only; the sidecar's `klass` falls back to
`_model_class_for_unit`. Filtering the fleet on `plant_group` silently returns
**ZERO** units for hydro/OTHER/import (miso-142 hit this and caught it only by
an assertion written for another reason).
**Counter-measurement:** reproduce `run_calibration_full.py`'s own `klass` logic
and **assert non-empty** for every class this session reads.

**TRAP 6 — FIXING THE NUMBER.** Any coal or gas parameter sized so the 2025 gap
closes is a **fitted input** (rules 1/13/24), not a repair.
**Counter-measurement:** the displacement size in G-A1(c) is set by the
**measured C2 excess (+4.2 %)**, and B-1's haircut is computed from the
**committed anchor (3.0492)** and the **measured delivered fuel** — every
quantity derived from its own measured source, **derivation frozen before the
residual is looked at**. No parameter is swept.

**PROBE HYGIENE — BINDING (miso-140b §6).** `load_demand` silently returns a
**different ZONAL split** when the repo root is off `sys.path`
(`_zonal_shares_from_raw` imports `scripts.data.curate_zonal_shares`;
`data/clean` is gitignored so that raw path is the only measured route) — same
ISO total, different allocation, up to **6,747 MW** per zone-hour on MISO 2025.
**EVERY probe in this session inserts the REPO ROOT** (not just `src/`) **and
asserts `load_zonal_shares(...) is not None`**, even if it consumes no per-zone
demand, so the guard cannot rot.

---

## 8. DO-NOT-REDO honoured (rule 28(a))

The **QUANTITY family entire** (hydro, OTHER, imports, ambient/summer capability
derates as PRICE levers — CLOSED on reach, miso-139/141/142) · re-splitting the
gap at a **PRICE THRESHOLD** (a calendar/hour-of-day split is a different object
and is in scope) · the "88 spike hours" arithmetic · **any LEVEL adder or
multiplier** · re-deriving the `*_lw` comparator a third way · **TROUGH**
marginal-unit pricing (SPENT miso-134 — the **SUMMER-PEAK** marginal unit is a
different window and is this session's) · a CT/CC/coal **bridge** on the
{capacity, seasonal derate, min-load fraction} feature family (REFUTED miso-138) ·
`gas_offer_margin_zonal_anchor` MISO = **I** (miso-119/120 — B-1 is the anchor's
**FORM in time**, not its **zonal grain**, and does not re-open that cell) ·
seam price/ceiling/floor classes SPENT (miso-114/123) · fitted trough adder
(REFUSED miso-128) · CC committed band (measured-grounded 1.005) · coal
deep-discount premise (MISO-53) · CEMS/dispatch bridging · SOM PDFs as a
unit-hour corpus · FERC EQR as an offer source · Michigan PSCR (SPENT miso-135) ·
`cc_nameplate_summer_derate` as a MISO repair without a NEW mechanism (miso-141) ·
re-opening the miso-141 or miso-139 successors as **PRICE** levers ·
**`miso_cc_coal_rebalance`** (already adjudicated unlicensed — target defined
against another model quantity).

---

## 9. THE MOST LIKELY WAY THIS SESSION GOES WRONG

Named now so it can be scored later. **I expect the failure mode to be
G-A0.** Reproducing `runner.py`'s offer sequence outside `runner.py` is the
single most fragile thing this session does: a missed step
(`apply_coal_supply_pricing`, the EAC subtraction, the interchange injections)
shifts the whole stack by a level, and a **level** error is invisible in the
**gap** readings that G-A1(a)/(b) rest on but fatal to G-A1(c)'s re-clear. That
is exactly why P1 is a **stop gate with a two-legged bar** and why
BRANCH-INSTRUMENT-FAIL exists as a pre-committed landing place rather than an
improvisation.

**The second most likely** is subtler and would be worse: the re-clear in
G-A1(c) is a **merit-order approximation** of an LP dual. Where a floor, a
must-run band or a reserve co-optimization is setting the price instead of the
energy stack, the approximation silently reports the *stack's* answer to a
question the *LP* answers differently. P1's correlation leg is the guard, and if
the gain lands close to a branch boundary the boundary call is made on the
**conservative** side and said so.

---

## 10. RULE DUTIES ACCEPTED AT OPEN

- **Rule 15** — every solve registered in the same session. **If no LP is
  solved there is no run to register** (the miso-131…142 precedent).
- **Rule 28(b)** — tested cells + the **§5.4 queue stamp** written in this
  session, **rejections included**. §5.4's queue is EMPTY and **item 4 is
  written into it**. No cell verdict is minted unless a mechanism is actually
  tested.
- **Rule 22** — **2023, 2024, 2025 ONLY.** MISO holds **no** marker in either
  block. No out-of-training year is solved, scored or registered.
- **Rule 16** — any solve covers all three years in **ONE** invocation.
- **Rules 13 / 14 / 19 / 21 / 23 / 24 / 25** — every input a measured physical
  or market quantity; nothing sized to a residual; no derive script re-run
  without a source-data change; one mechanism per phenomenon; no off-registry
  tuning channel; no cross-ISO transfer.
- **Rule 27** — any pushed file ≥300 lines is blob-verified (fetch back, compare
  line count + hash).
- **Concurrent-session check** — performed at open: **zero open PRs on this
  charter and no other live MISO remote branch** (`claude/miso-summer-supply-diagnosis-05q9bm`
  is miso-142's, already merged into `main`). Re-checked at close.

---

**Artifacts this PREREG commits the session to producing:** a finding document,
per-gate JSON under `results/calibration/_miso143_*.json`, probes under
`scripts/probes/_miso143_*.py`, the §5.4 item-4 queue stamp, and the
calibration-log entry — **whatever the verdict**.
