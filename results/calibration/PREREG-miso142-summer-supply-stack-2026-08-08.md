# PREREG — miso-142: §5.4 QUEUE ITEM 3, the MISO summer-afternoon supply stack

**Session:** miso-142, 2026-08-08. **Lane:** §5.4 queue item 3 (NEW, owner-set
2026-08-08) — the summer-afternoon supply stack: four owner-observed objects
(O1–O5) and one unifying hypothesis (H1) against its null (H0).

**Posture: PHASE 0, DIAGNOSIS-FIRST, NO SOLVE.** Every instrument this PREREG
names is a **committed artifact**. No LP is solved, no `ScenarioConfig` field is
added, no parameter is set, no mechanism is armed and no run is registered
unless gate **G-D** is reached AND its kill gates pass. Keeper unchanged at
**`2026-08-05-miso-132b-cc-committed`** (bundle `results/calibration/miso132_ccmin_B`).

**Owner directive honoured:** the target is the 2024/2025 mean-LMP level miss.
No C7 lane is chartered and no C7 ledger is sought. The owner's 2026-08-08
addition — *close the 2025 −14 % underrun WITHOUT disturbing the other metrics* —
is enforced as the **kill gates of §5**, whose bars are fixed in this document
before any of their numbers are seen.

**This PREREG is pushed BEFORE any adjudicating statistic.** §1 records exactly
what was measured before it was written, so there is no ambiguity about what is
pre- and post-registration.

---

## 0. §0 re-verified from committed artifacts — NOT from the charter

`scripts/calibration_verdict.py --run-id 2026-08-05-miso-132b-cc-committed`, at
HEAD, **no re-solve**, all three years in ONE invocation (rule 16). Rule 22:
MISO holds **no** `calibration-complete` marker in either block, so the scorable
span is **2023, 2024, 2025 only**.

| | value |
|---|---|
| determination | **NOT-YET** |
| rubric | **v3.1**, 8 criteria |
| **C3a `price_mean` — SOLE FAIL** | RT **−0.4 / −6.0 / −14.1 %** (model **32.72 / 30.37 / 39.05** vs **32.85 / 32.30 / 45.46**) |
| C3a DA companions (diagnostic, not gated) | **−4.4 / −8.4 / −15.8 %** (actual 34.23 / 33.14 / 46.35) |
| C3b `price_shape` | **PASS** — monthly load-weighted NRMSE **0.075 / 0.112 / 0.191**, bar ≤0.20 |
| C3c `price_tail` | **CAVEAT, ledgered** — the sole ledgered caveat, budget **1 of 1** |
| C1 / C2 / C4 / C6 / C8 | **PASS** |
| C8 note | ST_GAS **grounded above budget** 31.9 / 33.1 / **45.1 %** forced; CT_PEAKER 13.8 / 9.9 / 10.7 % (cap 15 %); CC_REGULAR 0.1 / 0.0 / 0.1 %; COAL 0.4 / 0.5 / 0.2 % |
| C8 hydro | **SKIPPED — immaterial**, 1.6 / 1.7 / **1.5 %** of ISO load, below the 2 % gate floor |

**Identical to the charter §0 in every cell.** Determination unchanged.

**The 2025 gap in dollars, on the scorer's own basis:** `39.05 − 45.46 = −6.41
$/MWh` load-weighted RT. 2024 **−1.93**; 2023 **−0.13** (miso-137 §4, to be
reproduced by this session's own probe as gate G-A0).

---

## 1. WHAT WAS MEASURED BEFORE THIS PREREG WAS WRITTEN — full disclosure

Nothing below bears on H1 vs H0 or on any of O1–O5. All of it is **instrument
calibration and schema/rubric inventory**, gathered so the conventions of §2
could be fixed *in writing* as Trap 2 demands. It is disclosed here rather than
presented later as a result.

1. **§0 above** (charter-mandated).
2. **Keeper config** re-verified from `run_config.json`: `hydro_ror_split=False`,
   `hydro_dispatch_envelope=False`, `hydro_min_flow_floor=False`,
   `hydro_budget_nameplate_aware=False`, `hydro_year="normal"`;
   `interchange_shaping=False` (so `interchange_shape_import_pct/export_pct=90.0`
   are **inert**), `miso_firm_imports=True`, `miso_manitoba_seam=True`,
   `miso_seam_measured_ladder=True`, `miso_seam_flow_limit=True`,
   `miso_seam_export_limit=True`, `miso_seam_envelope_merit_cap=True`,
   `miso_south_seam_split=True`, `priced_interchange=True`,
   `miso_pjm_lmp_import_pricing=False`, `miso_firm_import_floor=False`.
   **Charter config facts confirmed.**
3. **Sidecar schema.** `class_hourly_<y>.parquet` = `year, pass, klass, hour, mw`,
   pass `P1` only, 17 classes as the charter lists. `system_<y>.parquet` =
   `year, pass, zone, hour, price, slack, dump, demand, reserve_price`, **8 zones**
   (`MISO-East, MISO-Illinois, MISO-Indiana, MISO-Plains, MISO-South, MISO-West,
   MISO_external, MISO_external_South`), hour 0…8759.
4. **The model `import` klass is NET and generation-side positive** — it goes
   negative (export sinks: 23 / 519 / 945 hours in 2023 / 2024 / 2025) and tops
   out at a flat **8700 / 8700 / 8410.5 MW** (the seam cap).
5. **EIA-930 sign identity** (§2.2 below) — pure arithmetic on the file.
6. **EIA-930 clock availability**: `_eia_hourly_frame_filled("MISO", y)` returns
   8760 rows on the model's clock for all three years, with **0 / 24 / 1** NaN
   hours (2023 / 2024 / 2025). The strict frame returns `None` for 2025.
7. **Rubric key inventory** (§2.5 below) — a property of the rubric, not of the
   data. Disclosed because the charter asks the session to *state plainly* which
   of the four objects any criterion scores, and it would be dishonest to
   present a fact gathered pre-PREREG as a post-PREREG measurement.

---

## 2. THE BASES, FIXED IN WRITING BEFORE ANY COMPARISON

### 2.1 The price basis — ONE basis, the scorer's own (miso-133 bar)

Every price number is the **scorer's load-weighted RT basis** and nothing else.
The instrument is **`scripts/probes/_miso137_c3a_gap_decomposition.py`'s
`model_hourly` / `actual_hourly` / `contrib`**, reused verbatim rather than
re-implemented, because miso-137 gate G-0(ii) verified it reproduces the
scorer's C3a model scalar **to the penny and its percentage to 0.04 pp in all
three years**, with additivity residual exactly 0.0. *A repair is not a
verification, and the instrument that checks it needs checking too* (miso-140b):
re-deriving it a third way is on DO-NOT-REDO, so it is **reused, not rebuilt**.

The exact additive identity that makes every decomposition in G-A exact:

```
model_lw − actual_lw = Σ_h W_h (p_h − a_h) / Σ_h W_h
C(S)                 = Σ_{h∈S} W_h (p_h − a_h) / Σ_h W_h      (S any hour-set)
```

so the parts of any partition sum to the total with **no residual term**. G-A0
asserts additivity residual = 0.0 exactly and the annual totals = −0.13 /
−1.93 / −6.41; if either fails the session reports a basis defect and stops.

DA is reported **as a companion only, never blended** with RT.

### 2.2 The interchange sign convention — Trap 2, fixed HERE

Measured on the file as pure arithmetic (n = 74,390 non-null rows), per year the
median absolute residual of the two candidate identities:

| year | `|NG − D − TI|` | `|D − NG − TI|` | TI mean | (NG − D) mean |
|---|---:|---:|---:|---:|
| 2023 | **1360.5** | 7198.0 | −4328.0 | −2791.8 |
| 2024 | **1639.0** | 3812.0 | −2627.8 | −969.7 |
| 2025 | **1621.0** | 3938.0 | −2163.5 | −531.7 |

`NG − D − TI` is the smaller residual in **every year of the file (2018–2026)**,
and TI's sign tracks `NG − D`'s sign. **Therefore: EIA-930 `Total interchange`
is the STANDARD convention — positive = net EXPORT.**

> **DEFINITION, binding for this session:**
> `actual_net_import_MW := −(EIA-930 "Total interchange")`.
> The model's `import` klass is already net-import-positive (§1.4). The two are
> compared on that single convention and on no other.

**A single hand-picked row does NOT establish this and was not allowed to.** The
file's first row (2018-01-01 HE01) satisfies `D − NG − TI = 0` exactly — the
*opposite* identity — and would have inverted the whole session's O5 verdict if
taken as the convention. It is one row against 74,390. This is recorded because
it is precisely the shape of the failure Trap 2 names.

**Gate G-C0 (pre-committed direction verification, run before any shape
comparison):** on a month where the direction is unambiguous — MISO summer
afternoon, a well-documented net-import period — `actual_net_import_MW` must
come out **positive** on the monthly mean. If it comes out negative, the
convention above is wrong, and **the session stops and reports the basis
defect** rather than proceeding on an inverted instrument.

### 2.3 The clock — one clock, the repo's own

EIA-930 rows are drawn through **`market_sim.data.eia930.frames._eia_hourly_frame_filled("MISO", y)`**,
the repo's own loader: 8760 rows, row *k* = local hour *k* of the year on the
model's fixed standard-time calendar, **Feb 29 dropped**, which is the same
clock as `MONTH_START` in the miso-137 probe (non-leap `DAYS_IN_MONTH`) and the
same clock as the keeper's sidecars. This is used **instead of** any hand-rolled
mapping, because the loader's own docstring records that the HE→interval-beginning
correction it applies is the fix for a **+1 h shift that hit MISO-2025 specifically**
(FINDING-caiso102). Hand-rolling the clock here would re-introduce exactly that
defect on exactly the year this session is about.

NaN hours (**0 / 24 / 1**) are **masked, never interpolated**, and every
statistic reports its own effective *n*.

### 2.4 The "summer" definition — a live basis crossing, named now

**Two committed MISO documents use different summers.** miso-137's `SEASONS`
has `summer = (6, 7, 8)` → 92 days → **552** h12–17 hours. miso-139's cushion
table quotes **732** summer h12–17 hours → 122 days → **Jun–Sep** (the
`SUMMER_CLASS_DERATE` window). Both are correct in their own document and they
are **not interchangeable**.

> **Binding for this session:** price windows use **miso-137's Jun–Aug**, because
> this session reuses miso-137's instrument. Wherever a number is bounded against
> **miso-139's ~12 GW cushion**, the cushion is recomputed on **both**
> definitions and both are reported. A cushion quoted on one definition against a
> deficit computed on the other is not a comparison.

### 2.5 What the rubric actually scores — the Trap 3 inventory

From the scorer's own `--json` records:

| criterion | keys scored |
|---|---|
| C1 `fuelmix` | CC_CHP, CC_REGULAR, COAL_BIT, COAL_LIGNITE, COAL_PRB, CT_PEAKER, ST_CHP, ST_GAS |
| C2 `sysvol` | `gas`, `coal` |
| C4 `dispatch_corr` | `gas`, `coal` |
| C8 `forced_share` | CC_REGULAR, COAL, CT_PEAKER, ST_GAS, **hydro (SKIPPED — immaterial)** |

**`hydro` is reported and never gated; `OTHER` and `import` appear as a key in
NO criterion at all.** Three of the four owner-observed objects therefore sit
entirely outside the gated surface. That is a fact about the rubric, and by
itself it is **not** evidence that a defect exists there — establishing whether
one does, and whether it has any dollar reach, is what G-C is for.

---

## 3. THE HYPOTHESES, AND THE FALSIFIABLE PREDICTIONS

**H1 (the unifying hypothesis, to be tested FIRST and actively attacked):**
O3 + O4 + O5 are one object — the model fills MISO's summer afternoon with cheap
non-thermal supply (hydro + OTHER + mis-shaped imports) that is not really
there, which simultaneously (a) depresses the clearing price and (b) displaces
the marginal CT, producing O2's coal-over/CT-under signature. If H1 holds, O1/O2
are downstream symptoms and the repair is an **input/representation** fix
(rule 14), not a price lever.

**H0 (the null, not to be skipped):** the four are independent; the Jun/Jul miss
is a merit-order/offer-level defect in the coal-vs-CT stack with nothing to do
with hydro or imports.

I hold **H0/branch-C as the more likely outcome** going in, at roughly 60/40,
and the reason is stated so it can be held against me: miso-137 measured the
object as a **compressed price distribution** and miso-139 measured **11.6–13.3 GW
of idle CT** sitting in the very window at issue. A quantity story has to
traverse that cushion before it reaches a price. I am nonetheless required to
test H1 first and to try to kill it, and P9/P10 are written so that a genuine
H1 result would show up plainly.

| # | prediction | falsified if |
|---|---|---|
| **P1** | **O1, the window's share.** Jun+Jul h8–20 (793 h) carries **45–70 %** of the 2025 RT load-weighted gap; point estimate **55 %** | share **< 40 %** or **> 80 %** |
| **P2** | **O1, cross-year.** The same window's *absolute* dollar contribution is larger in 2025 than 2024, and in 2023 is within **±$1.00/MWh** of zero | either leg fails |
| **P3** | **O1 sub-window / Trap 4.** Jun 21–24 h8–20 (52 h) carries **< 15 %** of the 2025 gap | **≥ 25 %** |
| **P4** | **O2, coal.** Model coal (BIT+LIG+PRB) in Jun+Jul h8–20 2025 exceeds EIA-930 `NG: COL` by **+5 % to +30 %** in mean MW | \|Δ\| ≤ 5 % (H0-variant) or Δ > +45 % |
| **P5** | **O2, CT — Trap 1's counter-measurement.** In that window model CT_PEAKER runs at **< 45 %** of its own summer capability and holds **> 8 GW** idle | headroom **< 5 GW** |
| **P6** | **O3, hydro.** Model hydro is materially flatter than measured: hour-of-day CV (24 summer hod means) **< 0.5×** the `NG: WAT` equivalent in all three years; **and** annual level off by **> 20 %** in ≥1 year | CV ratio ≥ 0.5 **and** level within ±20 % in all years ⇒ **O3 REFUTED as stated** |
| **P7** | **O4, OTHER — the classification question first.** **≥ 60 %** of the model's `OTHER` capacity is natural-gas-fuelled (the `plant_taxonomy.py:314` branch), so the correct comparator for that portion is `NG: NG`, **not** `NG: OTH`, and a naive `OTHER`↔`NG: OTH` comparison overstates the overrun | **< 40 %** of OTHER capacity is gas |
| **P8** | **O5, imports.** Pearson *r* of the 24-point summer hour-of-day profile, model `import` vs `actual_net_import_MW`, 2025: **r < 0** (inverted) | **r > +0.3** (H0). **−0.3 ≤ r ≤ +0.3 ⇒ reported as "no clear phase relation", NOT as inversion** |
| **P9** | **H1, the quantity.** ΔQ_aft = (model − actual) over {hydro, import, OTHER on its *correct* comparator}, Jun+Jul h8–20 2025 mean MW. **H1 predicts ΔQ_aft ≥ +2 GW**; H0 predicts \|ΔQ_aft\| < 1 GW | see branches, §4 |
| **P10** | **H1, SUFFICIENCY — the decisive gate.** Reach = ΔQ_aft × (local slope of the model's own summer-afternoon offer stack at the clearing point). **I predict INSUFFICIENT: reach < 30 % of the window deficit, and stack slope < $3/MWh per GW over the first 5 GW above the clearing point** | slope **> $6/MWh per GW** ⇒ H1 becomes a live sufficient explanation and my prior was wrong |

---

## 4. GATES, IN ORDER, WITH PRE-COMMITTED DECISION RULES

**G-A — ATTRIBUTION BEFORE ANYTHING ELSE. No solve.**
- **G-A0 (instrument):** reproduce annual totals −0.13 / −1.93 / −6.41 $/MWh and
  assert additivity residual **exactly 0.0**. Fail ⇒ report basis defect, stop.
- **G-A1:** full **12 × 24 month-by-hour-of-day surface** of C(S) in **dollars**,
  all three years, RT (DA companion reported separately). The owner's window is
  **marked on** the surface, never reported alone (Trap 4).
- **G-A2:** C(S) for W1 = Jun+Jul h8–20, W2 = Jun 21–24 h8–20, and the
  complement; the remainder is decomposed until ≥90 % of the annual total is
  attributed to named cells.
- **Percentage guard (miso-137's threshold discipline):** if a year's \|total gap\|
  < **$0.50/MWh**, shares are **not** reported as percentages for that year —
  absolute dollars only. (2023's total is −$0.13, so this fires by construction.)
- **G-A proceeds on what the number says, not on what the charter says.**

**G-B — SIGNATURE vs CAUSE (the miso-129 bar). No solve.**
- Establish the **marginal unit** in the affected hours before any causal claim
  about coal. Instrument: rebuild the model's own MISO offer stack at HEAD via
  the loader path miso-139/miso-141 already used (fleet + availability + SRMC
  arrays — **this is not an LP solve and not a keeper replay**), and for each
  affected hour report the **class composition of units whose SRMC lies within
  ±$1/MWh of the model's clearing price**.
- **G-B also produces the P10 instrument**: the **local slope of the stack**
  above the clearing point ($/MWh per GW, first 1 / 2 / 5 / 12 GW).
- **Decision rule:** coal is credited as *causing* the low price only if coal is
  in the marginal bracket. If coal is strictly inframarginal, the causal channel
  is displacement-of-CT, whose magnitude **is** the stack slope — and it is
  reported as that number, not as an inference from co-occurrence.

**G-C — H1 vs H0. No solve.**
- **G-C0:** the §2.2 direction verification. Fail ⇒ stop.
- **G-C1:** hour-of-day profiles, model vs EIA-930, for **hydro / OTHER / import**,
  all three years, on the §2.2–2.4 conventions. `OTHER` is decomposed **by plant
  and fuel first** (P7) and only then given a comparator.
- **G-C2:** the counterfactual arithmetic — ΔQ_aft (P9) × stack slope (P10) vs
  the window deficit, **bounded against the miso-139 idle cushion on both summer
  definitions** (§2.4).
- **Trap 7 guard:** a ΔQ smaller than the EIA-930 adjustment residual for that
  window is **not asserted**.

**G-D — arming. Licensed ONLY if a single object resolves to a repairable INPUT
defect with an EXISTING mechanism AND every kill gate passes.**
- **At most ONE object** (rule 19 `[R-ONE-MECH]`). **Four objects may not be armed
  in one session.**
- Same-HEAD **zero-delta control FIRST**, then `replay_keeper --set`, one
  invocation per arm, `--years 2023 2024 2025` in a **single** invocation, arms
  **sequential** (rules 12/16).
- Otherwise: report, specify the successor, write the §5.4 queue item.

### Verdict branches, pre-committed

- **A — H1 SUPPORTED & SUFFICIENT:** P9 ≥ +2 GW **and** reach ≥ 50 % of the
  window deficit ⇒ G-D considered for exactly one object, subject to §5.
- **B — H1 SUPPORTED, INSUFFICIENT:** P9 ≥ +2 GW, reach < 50 % ⇒ the defects are
  reported as **rule-14 input-correctness** items with **no C3a claim attached**;
  successor specified; nothing armed.
- **C — H1 REFUTED:** P9 < +2 GW ⇒ O1/O2 are their own object, H0 stands;
  report; specify successor.
- **D — INSTRUMENT-BLOCKED:** if a taxonomy crossing or the EIA-930 residual puts
  ΔQ below measurable precision, say so and stop rather than assert.
- **MIXED is explicitly allowed:** some of O3/O4/O5 defective, others not. The
  session reports per-object verdicts and does not force a single story.

### Stop rule

If G-B shows that **no** quantity displacement of any size within the ~12 GW
cushion can produce the window deficit at the measured stack slope, the session
reports **"no quantity lever can close C3a in MISO"** and specifies a
**price-formation** successor — *regardless* of what O3/O4/O5 turn out to be, and
regardless of how defective they are. A confirmed defect with no reach is
reported as a confirmed defect with no reach.

---

## 5. KILL GATES — bars fixed HERE, before their numbers are seen

The owner's *"without disturbing the rest"* is a **binding constraint**, enforced
as follows. Any arm reaching G-D is scored against all of these, all three years:

1. **C3b.** 2025 monthly load-weighted NRMSE is **0.191** against a **≤0.20**
   bar — **headroom 0.009**. **Bar: an arm that puts 2025 C3b > 0.200 converts a
   PASS into a FAIL and is NOT a fix**, whatever it does to C3a. 2023 (0.075) and
   2024 (0.112) likewise must stay ≤0.20.
2. **C1 / C2 / C4.** All currently PASS and must stay PASS. **The
   `cc-high-cf-investigation` precedent is expected to bite here**: removing a
   false capacity wall in PJM *exposed* a CC offer-level miss and blew out the
   fuel mix. An arm that changes non-thermal supply changes what the thermal
   fleet must serve, so C1/C2 are the most likely casualty of any H1 repair.
3. **C8.** ST_GAS 2025 is already **grounded-above-budget at 45.1 %** forced. An
   arm that **raises any material class's forced share**, or that **breaks a D-4
   window**, fails C8. CT_PEAKER's cap is 15 % and it sits at 10.7 % in 2025.
4. **C3c.** Sole ledgered caveat, budget **1 of 1 — SPENT**. No second ledger
   entry is available; under rubric v3.1 C3c is the only ledgerable criterion at
   all. **No arm may be justified by a new ledger.**
5. **Rule 1 `[R-STRUCT]` is one-directional.** A structurally-correct mechanism
   stays even if the residual worsens. It does **not** license breaking a passing
   criterion to buy C3a. Rule 14: if an accurate input makes the fit worse, keep
   it and open the root cause.

---

## 6. LOOK-ALIKE TRAPS, each with its pre-committed counter-measurement

- **TRAP 1 — the miso-141 anti-connection (the obvious wrong turn).** miso-141
  measured a ~2.5 GW CT_PEAKER summer capability double-count and O2 reports CT
  under-running in the same hours. **These are not the same thing.** miso-139 G-2
  measured the derate **non-binding in 95.2–99.9 %** of summer h12–17 hours with
  CT at **25–34 %** of capability. *A class 12 GW below its ceiling does not
  under-run because its ceiling is 2.5 GW too low.*
  **Counter-measurement: P5 — CT headroom is reported in the affected hours
  BEFORE anything is attributed to capability.** The derate is not re-opened as a
  cause of O2.
- **TRAP 2 — the interchange sign/basis crossing.** **Counter-measurement: §2.2**
  — the convention is fixed in writing from the 74,390-row identity, the
  single-row counter-example that would have inverted it is recorded, and **G-C0**
  verifies the direction on an unambiguous month before any shape is compared.
- **TRAP 3 — the unscored-class illusion.** hydro / OTHER / import may be large in
  MW and absent from every gated criterion (**§2.5 confirms they are**). "Way off"
  in an unscored class is a real defect, but its dollar reach must be measured.
  **Counter-measurement: G-C2's counterfactual arithmetic, bounded against the
  cushion.** No reach ⇒ no C3a claim, however bad the defect.
- **TRAP 4 — calendar cherry-pick.** Jun 21–24 is four days; a window chosen
  because it looks bad is a threshold-as-definition (miso-137 bar).
  **Counter-measurement: G-A1 reports the full 12 × 24 surface with the named
  window marked on it, never the window alone; plus the P3 bound.**
- **TRAP 5 — the coal sidecar alias.** The sidecar splits coal into
  `COAL_BIT`/`COAL_LIGNITE`/`COAL_PRB` while the model's `plant_group` is the bare
  `COAL`; miso-141's unmapped lookup silently returned **zero** dispatch and handed
  ~32 GW back as phantom headroom. **Counter-measurement: an explicit alias map
  plus an assertion that fails loudly on any unmapped class**, carried over from
  `scripts/probes/_miso141_cc_rows_and_cushion.py`.
- **TRAP 6 — fixing the number.** Any hydro/import/OTHER change sized so the 2025
  gap closes is a fitted input (rules 1/13/24), not a repair.
  **Counter-measurement: every parameter derived from its own measured source,
  with the derivation frozen before the residual is looked at.** No parameter is
  set in this session at all unless G-D is reached.
- **TRAP 7 — the EIA-930 adjustment residual (ADDED by this session).** The
  BA-level identity does **not** close: median `|NG − D − TI|` is **1.36 / 1.64 /
  1.62 GW** (2023/24/25). So every model-vs-EIA-930 *quantity* comparison carries
  a ~1.6 GW floor of instrument noise, and a ΔQ below it is not measurable.
  **Counter-measurement: the residual's own magnitude and hour-of-day profile are
  reported alongside every quantity comparison, and no ΔQ below it is asserted.**

---

## 7. PROBE HYGIENE — binding (miso-140b §6)

`load_demand` **silently** returns a different **zonal** split when the repo root
is off `sys.path` (`_zonal_shares_from_raw` imports `scripts.data.curate_zonal_shares`;
`data/clean` is gitignored, so that raw path is the only measured route) — same
ISO total, different allocation, up to **6,747 MW per zone-hour** on MISO 2025.

Every probe in this session:
1. inserts the **REPO ROOT** on `sys.path` (not just `src/`), and
2. asserts `load_zonal_shares(...) is not None`,

**regardless of whether it consumes per-zone demand**, so the guard cannot rot.
Where a demand weight is needed, this session uses the **keeper's own committed
`system_<y>.parquet` `demand` column** — miso-140b measured it identical to
`load_demand` at HEAD (0.0 MW max hourly Δ, 3/3 years, 6/6 zones), so this is the
same number by the shortest path.

---

## 8. DUTIES AND POSTURE

- **Rule 15** — if no LP is solved there is **no run to register** (the
  miso-131…141 precedent). If G-D is reached, every solve is registered in this
  session.
- **Rule 28(b)** — the §5.4 queue stamp is written **in this session** whatever
  the outcome, and this new item is written **into** the queue (which is empty).
  A mechanism cell is minted only if a mechanism is actually tested.
- **Rule 22** — 2023–2025 only; MISO holds no marker.
- **Rules 13 / 14 / 19 / 21 / 24 / 25** observed throughout: no measured *outcome*
  fed back, accurate inputs kept even if the fit worsens, one mechanism per
  phenomenon, derive scripts not re-run against a residual, no off-registry
  channel, no cross-ISO parameter transfer.
- **DO-NOT-REDO honoured** (rule 28(a)): the ambient-derate family as a price
  lever, the literature temp-derate slopes, `temp_derate_hourly_grain` reversion,
  the {capacity, seasonal derate, min-load} bridge family, the price-threshold gap
  split, the "88 spike hours" arithmetic, any level adder/multiplier, a third
  `*_lw` derivation, `gas_offer_margin_zonal_anchor`, the seam price/ceiling/floor
  classes, the fitted trough adder, **trough** marginal-unit pricing (miso-134 —
  G-B's **summer-peak** marginal unit is a different window and is in scope),
  the CC committed band, the coal deep-discount premise, CEMS/dispatch bridging,
  SOM PDFs as a unit-hour corpus, FERC EQR, Michigan PSCR,
  `cc_nameplate_summer_derate` as a MISO repair without a new mechanism, and
  re-opening the miso-141 / miso-139 successors as price levers.
- **A CONCURRENT-SESSION CHECK was run before claiming this item**: `git ls-remote
  --heads origin` shows **no other MISO branch**, and the designated branch sits
  at `origin/main`. Open PRs are re-checked before the discharge stamp.

---

## 9. WHAT WOULD MAKE THIS SESSION WRONG

Stated in advance so it can be checked afterwards:

1. If **P10's slope comes out steep** (> $6/MWh per GW), my 60/40 prior for H0 is
   wrong, H1 is a live sufficient explanation, and I should say so plainly rather
   than retreating to "insufficient reach".
2. If **P1 comes out far outside 45–70 %**, the owner's O1 window is not the
   object I priced it as, and G-A's own number governs — not the charter's
   framing and not mine.
3. If **G-C0 fails**, everything downstream of the interchange comparison is
   void and the session stops, even though that would leave the item undischarged.
4. The most likely way this session goes wrong is **P7**: mapping the model's
   residual `OTHER` bucket onto EIA-930 `NG: OTH` because the names match. The
   names matching is exactly what makes it a trap.
