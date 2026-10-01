# PRE-REGISTRATION — miso-145: the summer-afternoon OFFER-CONDUCT identification (§5.4 queue **item 6**, owner-opened 2026-08-08). Phase 0, diagnosis-first.

**Session:** miso-145, 2026-08-09, branch `claude/miso-offer-conduct-phase-0-0ue55p`,
off `origin/main` at `c452919`.

**Posture at registration: NO LP SOLVED. NO KEEPER MOVED. NO MECHANISM ARMED.
NO RUN REGISTERED. NO `ScenarioConfig` FIELD ADDED. NO CELL VERDICT MINTED.**
MISO keeper unchanged at **`2026-08-05-miso-132b-cc-committed`** (bundle
`results/calibration/miso132_ccmin_B`). A solve is licensed **only** at G-C and
only if every kill gate in §8 passes.

**Rule 22 `[R-HOLDOUT]`:** MISO holds **no** `calibration-complete` marker.
Every operating day fetched, every year scored, and every year solved (if any)
is inside **2023–2025**. No out-of-training quantity is read, and the intake
day list in §3 is fixed here, before the first fetch.

This document is committed and pushed **before any adjudicating statistic is
computed**. §10 discloses, exhaustively, everything read before registration.

---

## 0. The keeper's state, re-verified from committed artifacts (not from the handoff)

`.venv/bin/python scripts/calibration_verdict.py --run-id 2026-08-05-miso-132b-cc-committed`
— committed artifacts only, no re-solve, all three scorable years in ONE
invocation:

> **CALIBRATION DETERMINATION: NOT-YET** · scorable years 2023, 2024, 2025 ·
> **SOLE FAIL `C3a` mean LMP, 2025 RT −14.1 % [MODEL MISS]** (DA companion
> −15.8 %, skipped-diagnostic; 2023 −4.4 %, 2024 −8.4 % DA companions) ·
> C1 **PASS** (all eight 2025 classes SKIPPED, preliminary EIA-923 vintage) ·
> C2 **PASS** (both 2025 families SKIPPED: gas −11.2 %, coal +4.2 %) ·
> C3b **PASS** · C3c **CAVEAT, ledgered, all three years** · C4 **PASS** ·
> C6 **PASS** · C8 **PASS** with ST_GAS grounded above budget
> **31.9 / 33.1 / 45.1 %**, all binding mechanisms clearing D-4 ·
> determination basis: *undocumented out-of-tolerance (FAIL) criteria:
> price_mean*.

The bundle's own `metrics.json` carries a **stale** `price_mean: CAVEAT`; the
scorer is authoritative and is what this document is registered against.
**Fail set at HEAD = {C3a}.**

---

## 1. The object, and why every other family is closed

The lane's object is **not** the C3c scarcity tail. It is the level of
**ordinary summer-afternoon** prices. The committed frontier, re-read from the
prior sessions' own JSON this session (§10):

| year · window | n hours | keeper P1 lw | actual RT lw | deficit |
|---|---|---|---|---|
| 2023 · W1 Jun+Jul h8–20 | 793 | 36.223 | 40.973 | **−4.750** |
| 2023 · JJA h12–17 | 552 | 39.488 | 47.821 | **−8.333** |
| 2024 · W1 | 793 | 33.297 | 43.973 | **−10.676** |
| 2024 · JJA h12–17 | 552 | 39.100 | 49.772 | **−10.671** |
| 2025 · W1 | 793 | 44.439 | 75.438 | **−30.999** |
| 2025 · JJA h12–17 | 552 | 44.245 | 74.680 | **−30.435** |

Three model-side families are closed **by measurement**, and this session may
not re-open any of them (rule 28(a), DO-NOT-REDO):

* **QUANTITY** — miso-142: no admissible displacement closes C3a; the arithmetic
  is a slope multiplied by a displacement and it does not reach.
* **MERIT ORDER** — miso-143: the gain (+$2.297 to +$5.474/MWh) is real and
  material, but **all four** candidate mechanisms (B-1 `gas_offer_margin`'s
  fixed anchor, B-2 delivered coal price, B-3 the coal tranche curve, B-4 CC/CT
  heat rates) are eliminated by measurement. `gas_offer_margin` MISO stays `K`.
* **DISPATCH / PRICE-FORMATION OPTIMALITY** — miso-144: the 19.3 GW "in-merit
  idle block" was ~97 % an instrument universe artifact; a same-universe
  copperplate reproduces the keeper's P1 price at median |Δ| $0.38–1.00,
  r ≈ 0.99, bias +$0.06. Strict own-zone in-merit idle is 611 MW, inside the
  2,543 MW reserve holding; out-of-merit forced-in is ~1.3 GW, fully attributed
  to D-4-cleared floor families. **The floors are exonerated as this lane's
  lever.**

What is left, and what nobody has owned: **the model's stack never reaches the
actual price.** Committed 2025 JJA h12–17 readings:

* model max price **anywhere** in the window: **$51.97** vs actual lw **$74.68**;
* the model's own **true within-hour offer ladder** slope above its clearing:
  **1.4962 / 1.8946 / 2.8900 $/MWh per GW** at +1 / +2 / +5 GW (`lo`;
  1.4701 / 1.7754 / 2.7089 at `hi`);
* walking the model's own ladder to the actual price takes **16.14 GW** (`lo`;
  17.26 GW `hi`).

**The hypothesis this session tests:** MISO's *real submitted offers* in
ordinary summer-afternoon hours sit materially **above SRMC**, and that wedge
**rises with position in the stack**, so the real supply curve reaches ~$75
within a few GW of its clearing point where the model's SRMC-anchored curve
needs 16 GW. This is market conduct the model's offers do not carry.

**The measured source that has never been intaken:** MISO's own masked
submitted-offer corpus, `https://docs.misoenergy.org/marketreports/YYYYMMDD_rt_co.zip`
(RT) and `..._da_co.zip` (DA) — one row per masked unit × hour, the full
10-segment price/MW offer curve, published at ~90-day lag. Its existence and
grain were established at **miso-136**; nothing has been intaken from it.

---

## 2. Two facts fixed BEFORE registration that bound what this lane may claim

**(a) There is no fuel/technology column, and the offer-side class bridge is
REFUTED.** miso-136 machine-verified zero columns matching `fuel|type|technolog`;
miso-138 built the offer-side classifier and the pre-committed verdict was
**REFUTED** (`|S_cap| > 0.50` for CC at both EIA-860 grains in 2024 and 2025;
COAL recall 0.382 *with labels in hand*). Coal and CC are not separable in this
feature family. **Therefore this session attempts NO class crosswalk and mints
no class-conditional conduct statistic.** The handoff's G-B(1) "markup
distribution *by class*" is **declared out of reach at registration** and is
reported as such — documenting the mapping's limit rather than overclaiming
grain, exactly as the charter instructs. Every conduct statistic below is at
**fleet grain**, on universes stated on both sides.

What miso-138 *did* establish, and what this lane rests on: **G-0 PASSED — the
corpus IS the MISO fleet**, reconciling to EIA-860 MISO at fleet grain at
**+12.9 / +9.0 / +6.0 %** on MW and **−1.4 / −4.1 / −7.5 %** on unit count. A
fleet-grain supply curve built from this corpus is a supply curve for the MISO
fleet, and that is the only grain claimed here.

**(b) The corpus carries OUTCOME columns and they are structurally excluded.**
RT `Cleared MW1`–`Cleared MW12` and DA `MW` are awards — the answer class under
rule 13. They are **dropped in the curation step**, never written to the clean
datatype, and therefore cannot be read downstream even by accident. This is the
machine-enforced counter-measurement for TRAP 2 (§7).

---

## 3. G-A — the intake, scoped and fixed here

**Contract.** Extend the existing `energy-offers` clean datatype (today
PJM-only, `schema_version: 1`) to be ISO-generic at `schema_version: 2`:
`market` (`DA`/`RT`) joins the key; every MISO-specific column is declared
**nullable** so PJM's existing writer stays valid, and PJM's curate script gains
the single constant `market="RT"` column (its feed is the RT effective offer
set). Raw lands immutable under `data/raw/miso-energy-offers/` (gitignored, the
`caiso-public-bids` / `pjm-energy-offers` precedent) with a tracked README
recording per-file sha256/size. Clean parquet is written through the frozen
`clean_io.write_clean` seam. Every path resolves through `config/paths.py`.
Fetcher `scripts/data/fetch_miso_energy_offers.py`; curator extends
`scripts/data/curate_energy_offers.py`.

**Scope, fixed before the first fetch (rule 22 audit line).** Operating days
**June 1 – August 31** of **2023, 2024 and 2025** — 276 days per market —
for **both** markets (`rt_co` primary, `da_co` companion). No other date is
fetched. This is the JJA window the lane's object is defined on; the daily file
is the smallest published unit, so whole days land and the h12–17 restriction
is applied at analysis time.

**Coverage predictions (falsifiable, two-sided).**

| id | prediction | falsified if |
|---|---|---|
| **P-A1** | ≥ 99 % of the 276 RT days and 276 DA days return HTTP 200 with a parseable single-member zip | < 95 % on either market |
| **P-A2** | 900–1,600 distinct masked units per day; 20k–40k unit-hour rows per RT day; all 24 hours present in ≥ 99 % of days; h12–17 populated in every day | outside those bands on > 5 % of days |
| **P-A3** | zero columns matching `fuel|type|technolog` (miso-136 re-verified on the full span); `Region` ∈ {North, Central, South} exhaustively | any fuel/type column appears — in which case the class-grain lane **re-opens** and this PREREG is superseded, reported as such |
| **P-A4** | masked `Unit Code` persists within a year: ≥ 90 % of Jun-1 units recur on Aug-31, all three years | < 80 % in any year (longitudinal statistics then unsupported and only pooled cross-sections are reported) |
| **P-A5** | offer curves are cumulative-MW monotone: `MW1 ≤ MW2 ≤ … ≤ MW10` and `Price1 ≤ … ≤ Price10` on ≥ 99 % of populated rows | < 95 %, in which case the curve construction is re-stated before any use and the deviation characterised |

**Data-blocker branch (pre-committed).** If access, format, or the end-to-end
usability of the corpus fails — HTTP/WAF refusal, unparseable payloads, or a
coverage failure at P-A1 — the session **reports a DATA BLOCKER, names the
partial product that exists, and stops at G-A.** No workaround is attempted.

---

## 4. G-B — the conduct measurement, and the identity it is scored on

**Model side.** `scripts/probes/_miso143_stack.py` reused verbatim —
`fleet_state()` (`run_year(fleet_only=True)`, the orchestrator's own
availability reconstruction), `klass_of`, the asserted coal alias, the
`markup_ceiling` `lo`/`hi` bracket, and `hygiene()` (miso-140b §6: repo root on
`sys.path`, `load_zonal_shares` asserted non-None). The keeper's committed P1
price comes from `sidecar_price`; the measured actual RT price comes from
`_miso137_c3a_gap_decomposition.actual_hourly` — **reused, never re-derived**
(DO-NOT-REDO: no third derivation of the `*_lw` comparator).

**One weight (TRAP 7).** Every window mean on both sides is load-weighted on
the model's own zonal demand — C3a's own basis — as in miso-143.

**The primary identity (exact by construction).** For each hour, define
`p_own` = the percentile of a side's **own** offered/available capability at
which that side clears. Then, with `P_real(·)` the real corpus curve and
`P_model(·)` the model's own P1 offer stack, both evaluated at percentiles of
their **own** capability:

```
deficit  =  [ P_real(p_real) − P_real(p_model) ]   ← POSITION term
          + [ P_real(p_model) − P_model(p_model) ] ← LEVEL / CONDUCT term
```

The two terms sum to the committed deficit by construction; the split is what
is being measured. Percentile-of-own-capability is the universe-normalising
device (TRAP 3): each side is positioned against its own stack, so a universe
that is 10 % larger on one side does not manufacture a level difference.

**Pre-registered predictions.**

| id | prediction (2025 JJA h12–17, primary) | falsified if |
|---|---|---|
| **P-B1** *(real-side footing)* | clearing the corpus's own curve at the measured MISO load reproduces the actual RT lw price $74.68 to within **median \|Δ\| ≤ $15** | median \|Δ\| > $25, or the corpus curve clears **below $50** — in which case real prices are not made by the real offer stack either and the deficit's owner is elsewhere (BRANCH-CONDUCT-ABSENT) |
| **P-B2** *(the LEVEL term)* | the LEVEL/CONDUCT term is **≥ 60 %** of the −$30.435 deficit, i.e. **≥ $18/MWh** | ≤ 30 % (≤ $9) — the deficit would then be a POSITION effect, which miso-142 closed, and the contradiction is reported rather than resolved by choosing a side |
| **P-B3** *(steepness)* | the real within-hour offer-ladder slope above clearing is **≥ 2×** the model's committed 1.4962 $/MWh/GW at +1 GW, i.e. **≥ 3.0**; reported at +1/+2/+5 GW on the same construction | ≤ 1.8 at +1 GW (within ~20 % of the model) — the steepness is then not in the offer curve at all |
| **P-B3b** *(the walk)* | the real stack reaches $74.68 within **≤ 6 GW** above its own clearing, against the model's committed **16.14 GW** | ≥ 12 GW |
| **P-B4** *(the 2025 signature)* | the LEVEL term grows monotonically 2023 → 2025 with **2025 − 2023 ≥ +$5/MWh** on the JJA h12–17 window | growth ≤ $1 or negative — conduct is then flat in time while the deficit grows 6×, so conduct cannot be the deficit's sole author (BRANCH-CONDUCT-PARTIAL) |
| **P-B5** *(conduct rises with load)* | the real curve's price at a fixed percentile of its own capability rises with system load at **≥ 2×** the model's rate over the window's load range | ratio ≤ 1.2 |

**Sensitivities, pre-declared non-gating but reported.** (i) The `lo`/`hi`
markup bracket on the model side — where a verdict differs across endpoints the
boundary is called on the **conservative** side and said so. (ii) A
"dispatchable" screen on the real side (`Economic Flag = 1` or `EconMin > 0`,
storage-level rows excluded) against the model's `THERMAL_COLS` rows; the
headline verdict must hold on **both** the all-rows and screened universes or
the disagreement is the finding. (iii) The DA corpus, computed identically and
reported in its own column — **never averaged with RT** (TRAP 4).

---

## 5. Two-sided prior, stated before any number is seen

**The lane's prior is that conduct is real and material but not the whole
deficit.** Concretely: LEVEL term $12–25/MWh of the $30.4, real ladder slope
3–6 $/MWh/GW, and a visible 2023→2025 widening because 2025 is the high-gas
year in which scarcity rents and opportunity-cost offers are largest.

**The prior on the other side is not decorative.** MISO's offer floor is a
cost-based reference-level regime under the IMM's conduct-and-impact screens, so
a large fleet-wide markup in *ordinary, unconstrained, non-scarcity* hours is
exactly what that regime is designed to prevent. If the corpus shows offers
sitting close to cost in these hours, then the −40 % miss is **not** an offer-
conduct object and this session's honest output is "no admissible owner at this
frontier" — which, given quantity, merit order and dispatch are all already
closed by measurement, is an **owner-escalation** result, not a failure to find
a lever. Both outcomes are equally publishable and the branches in §6 are fixed
now so neither can be reached by choice after the fact.

**Most likely failure mode, named in advance:** a universe crossing between the
corpus's offered capability and the model's available capability that
manufactures a level difference out of a population difference. The percentile
normalisation, the two-universe sensitivity, and gate **G-F2** are the three
independent guards against it (miso-144's lesson: 97 % of a "finding" was a
universe crossing).

---

## 6. Pre-committed branches

* **BRANCH-CONDUCT-OWNED** — P-B1 passes **and** P-B2 ≥ $18 **and** P-B3 ≥ 3.0.
  The deficit has a measured conduct owner. Proceed to the §9 rule-13
  admissibility adjudication; if and only if that yields an admissible
  forward-regenerable mechanism form **and** every §8 kill gate passes, G-C
  arms **exactly one** mechanism (zero-delta control first).
* **BRANCH-CONDUCT-PARTIAL** — the LEVEL term is material but P-B4 or P-B5
  fails (no 2025 signature / no load-conditioning). Report; the object is real
  but a driver-conditioned mechanism is not identified; name the successor;
  **no arm**.
* **BRANCH-CONDUCT-ABSENT** — P-B2 ≤ $9 or P-B1 fails low. The deficit has **no
  admissible owner at this frontier**; report for owner escalation, with the
  three closed families and this one recorded together.
* **BRANCH-INSTRUMENT-FAIL** — G-F1 or G-F2 fails. The bar is **not moved**;
  the failed reading is reported at full magnitude and the instrument reports
  **gaps only**, never levels (the miso-143 precedent).
* **BRANCH-DATA-BLOCKER** — §3. Report and stop.
* **BRANCH-REOPEN-CLASS** — P-A3 falsified (a fuel/type column exists). The
  class-grain lane re-opens; this PREREG is superseded and re-registered before
  any class statistic.

---

## 7. Look-alike traps, each with its counter-measurement

* **TRAP 1 — re-sweeping `gas_offer_margin`.** Its fixed-anchor form is armed,
  cell `K`, and miso-143 B-1 measured its price-relevant haircut at **$0.33**
  with a **$0.18** 2023→2025 swing. Re-identifying its anchor or level is
  DO-NOT-REDO. *Counter-measurement:* the wedge measured here is reported **at
  the stack position where `gas_offer_margin` is price-relevant** alongside the
  headline, so the new object is shown to be a different object; and any
  mechanism proposed at §9 must state explicitly how it **replaces or subsumes**
  the existing margin mechanism (rule 19 `[R-ONE-MECH]`) — never stacks on it.
* **TRAP 2 — the outcome overlay.** Pinning measured offers into the backcast is
  pinning the answer (rule 13). *Counter-measurement:* (a) the award columns are
  dropped at curation and never written to the clean datatype (§2b); (b) the
  §9 admissibility adjudication is mandatory and precedes G-C; (c) no measured
  same-year curve may enter the LP — only a driver-conditioned parameter with a
  forward story.
* **TRAP 3 — the universe.** *Counter-measurement:* gate **G-F2**; percentile-
  of-own-capability normalisation; both universes' MW and unit counts printed
  on both sides of every subtraction; the all-rows / screened sensitivity.
* **TRAP 4 — the instrument crossing.** Offer prices are as-bid; model SRMC is
  delivered-fuel × HR + VOM. *Counter-measurement:* the LEVEL term is a
  **price-vs-price** comparison at matched percentile — both sides are offer
  prices, the model's on its own P1 offer basis — so no as-bid/SRMC subtraction
  is performed. DA and RT are computed separately and never averaged; all
  levels are reported on C3a's own basis.
* **TRAP 5 — the tail relapse.** The C3c list is exhausted and its ledger spent.
  *Counter-measurement:* gate **G-F4** — the window's hours are partitioned by
  actual RT price band (≤ $100, $100–200, > $200) with counts printed, and the
  headline is computed on the **ordinary-hours** subset (actual RT ≤ $200) as
  well as the full window; the verdict must hold on the ordinary subset.
* **TRAP 6 — fixing the number.** *Counter-measurement:* every conduct
  parameter is read from the offer corpus at a position fixed in this document;
  its C3a effect is measured **after** and never used to set a value. No search
  over C3a is run at any point.
* **TRAP 7 — weights.** *Counter-measurement:* gate **G-F1** — miso-142's six
  committed window deficits are reproduced to ≤ $0.01 before any verdict, on
  the single C3a weight used for every window mean.

---

## 8. Gates

**Footing / instrument gates (must pass before any verdict).**

* **G-F1 (footing, HARD STOP).** Reproduce the six committed window deficits
  −4.750 / −8.333 / −10.676 / −10.671 / −30.999 / −30.435 to ≤ $0.01.
* **G-F2 (universe).** The corpus's declared-available economic-max total and
  the model's available capability total reconcile at fleet grain to within
  **±25 %** (miso-138's EIA-860 reconciliation was +6.0 to +12.9 %). Outside →
  BRANCH-INSTRUMENT-FAIL.
* **G-F3 (instrument).** RT primary; DA separate; one basis per comparison.
* **G-F4 (tail separation).** §7 TRAP 5.

**Kill gates for any G-C arm — bars fixed here, before any number is seen.**

* **C3b-2025 NRMSE ≤ 0.200** (currently 0.191; headroom 0.009). Crossing it is
  not a fix.
* **C3a 2023 and 2024 stay PASS** (currently −0.4 / −6.0 %). The 2023 ±10 %
  tolerance is the tight one: a conduct mechanism raises prices in **all** years
  by construction unless driver-conditioned.
* **C1 / C2 stay PASS on gated years.** 2025 is **UNGATED** (preliminary
  EIA-923); 2025 fuel mix is scored **descriptively vs EIA-930 and labelled as
  such**. C1/C2 PASS is never quoted as 2025 safety.
* **C8:** no material class's forced share rises; no D-4 window breaks. ST_GAS
  45.1 % grounded is the live escalation. A floor is **not** this lane's lever
  (miso-144 exonerated them).
* **C3c:** ledger 1 of 1 and **SPENT**. No mechanism may be tuned to the >$200
  tail.
* **Fail set must remain ⊆ {C3a}.** Rule 1 `[R-STRUCT]` is one-directional: a
  structurally-correct mechanism stays in even if the residual does not move,
  and no mechanism enters because the residual does move.

---

## 9. Rule-13 admissibility — adjudicated in advance, binding on G-C

**Forbidden form.** Measured same-year offer curves pinned into the backcast are
a measured **outcome** overlay with no forward analogue. They may exist only as
an explicitly-labelled, default-**off** diagnostic probe and may never be armed
in a keeper or quoted as forecast skill.

**The only admissible form.** A **conduct parameter** derived from
**multi-year** offer history and **conditioned on drivers that exist in a
forecast year** — position in the stack / headroom, load percentile, gas price —
such that the same quantity could be produced for a forward year from forward
drivers and would respond to changed conditions. This is the CEMS-emission-rate
precedent, and the admissibility test is applied *before* any arm, in writing,
in the session's finding.

**Additional binding conditions on any arm.** (i) Rule 19 `[R-ONE-MECH]`: it
must replace or subsume `gas_offer_margin`, never stack on it. (ii) Rule 25
`[R-ISO-SCOPE]`: parameters are MISO's, derived from MISO's own market data.
(iii) Rule 24 `[R-REGISTRY]`: it is a `ScenarioConfig` field appearing in
`run_config.json`, with its matrix row added in the same PR (rule 28(c)).
(iv) Rule 21 `[R-DOF]`: it enters the DOF ledger with its identification source.
(v) Solve posture: same-HEAD **zero-delta control first**, then
`replay_keeper --set ... --years 2023 2024 2025` in a **single** invocation,
years sequential, arms sequential, swap enabled before any solve.

**If the identification cannot be given a forward story, it is a finding, not a
lever.**

---

## 10. Full disclosure — everything read before this registration

1. `CLAUDE.md` (repo instructions) and the session handoff prompt.
2. `docs/mechanism-testing-matrix.md` §5.4 — the miso-144 LIVE QUEUE stamp and
   the miso-143 prior stamp beneath it.
3. `results/calibration/FINDING-miso136-ct-offer-conduct-corpus-exists-2026-08-06.md`
   (§§1–6) — corpus existence, grain, the absent type column, masked-ID
   persistence.
4. `results/calibration/FINDING-miso138-da-co-class-bridge-refuted-2026-08-06.md`
   (§§1–3) — the REFUTED class bridge and the passing G-0 fleet reconciliation.
5. `results/calibration/FINDING-miso144-idle-block-is-universe-artifact-2026-08-08.md`
   (via the §5.4 stamp) and `PREREG-miso144-inmerit-idle-attribution-2026-08-08.md`
   §§2–3.
6. Committed prior JSON, read this session for the footing numbers reproduced in
   §1: `_miso143_footing.json`, `_miso143_ladder.json`.
7. `scripts/probes/_miso143_stack.py` (full), `_miso143_ladder.py` (the
   comparator construction, L215–255).
8. `scripts/data/curate_energy_offers.py` (header), `scripts/data/fetch_miso_bc_hist.py`
   (header), `scripts/probes/_miso136_ct_offer_conduct_survey.py` and
   `_miso138_fetch_da_co.py` (headers), `data/dictionary/schema/energy-offers.schema.yaml`,
   `scripts/lib/clean_io.py` (validation semantics), `data/raw/caiso-public-bids/README.md`.
9. The keeper re-verification output quoted verbatim in §0.
10. **Two corpus sample files, structural inspection only** —
    `20250715_da_co.zip` and `20250715_rt_co.zip`, fetched to the session
    scratchpad (never `data/raw/`): the CSV header line and the first 2–5 data
    rows, plus line counts (33,722 DA / 23,911 RT) and byte sizes (829,093 /
    872,270). **No conduct statistic, no aggregate, no price distribution, no
    level of any kind was computed from them.** Both days are inside 2023–2025.
11. Model memory of MISO market-report naming and of the IMM conduct-and-impact
    regime — disclosed as a **prior**, not as evidence; every load-bearing fact
    above is cited to an on-disk artifact or a live fetch.

Nothing else was opened. No statistic bearing on any §4 prediction has been
computed at the time of this commit.
