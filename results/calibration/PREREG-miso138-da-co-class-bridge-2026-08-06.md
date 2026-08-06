# PREREG — miso-138: demonstrate or refute an OFFER-SIDE-ONLY class bridge (CT / CC / coal) for MISO's masked `da_co` submitted-offer corpus

**Session:** miso-138, 2026-08-06, branch `claude/miso-138-shape-lever-rp25g4`.
**Lane:** charter option **(b)** — the §5.4 standing chartered item
(`FINDING-miso136-ct-offer-conduct-corpus-exists-2026-08-06.md` §6).
**Committed and pushed BEFORE any adjudicating statistic is computed.**

---

## 0. State of play — re-verified from committed artifacts this session

Keeper **`2026-08-05-miso-132b-cc-committed`**, bundle
`results/calibration/miso132_ccmin_B`. Read from the committed
`metrics.json` **this session** (not from the handoff): determination
**NOT-YET**, rubric **3.0**, scorable years **[2023, 2024, 2025]**, criteria
`fuelmix` PASS · `sysvol` PASS · `price_mean` **CAVEAT (ledgered)** ·
`price_shape` PASS · `price_tail` **CAVEAT (ledgered)** · `dispatch_corr`
PASS · `governance` PASS · `shape` **FAIL** · `forced_share` PASS; reasons
`["undocumented out-of-tolerance (FAIL) criteria: shape"]`; ledgered caveat
budget 2 of 3 used, `{C3a, C3c}`.

C3a per-year magnitudes are carried from **miso-137's own committed
re-verification** (`results/calibration/_miso137_c3a_gap_decomposition.json`,
read this session), which the charter directs is not to be re-derived:
RT **−0.46 / −5.90 / −13.97 %**, DA **−4.45 / −8.34 / −15.65 %** for
2023 / 2024 / 2025. Model scalars 32.7179 / 30.3667 / 39.0472.

**Owner directive honoured:** the target is the 2024/2025 mean-LMP level
miss. No C7 lane is chartered here and no C7 ledger is sought — C7 is the
keeper's sole FAIL and is explicitly out of scope by owner order.

**Rule 22 `[R-HOLDOUT]`:** MISO holds **no** `calibration-complete` marker.
Only 2023-, 2024- and 2025-dated report days will be fetched; the exact file
list will be enumerated in the finding as a rule-22 audit line. No
out-of-training year is read, solved, scored or registered.

### 0.1 Why this lane, and why it is a prerequisite rather than a lever

miso-137 established that MISO's mean-LMP gap is a **compressed price
distribution** — the model over-prices every hour below ~$40 and under-prices
every hour above it, monotonically in the actual price level, with the same
compression visible on the clock (summer h00–05 over-priced +18 %, summer
h12–17 under-priced −41 % in 2025). The charter's lane (a) therefore admits
only a mechanism that **steepens the offer stack** and explains the **sign
reversal within one season and one fleet**; a level lever is disqualified on
its face.

Every non-measured route to such a mechanism is already closed on the
DO-NOT-REDO list (fitted trough adder REFUSED at miso-128; trough
marginal-unit pricing SPENT at miso-134; level adders/multipliers
disqualified). Under rule 13 `[R-MEASURED]` the steepness has to come from
**measured conduct**, and the only MISO source at class grain is the `da_co`
submitted-offer corpus (miso-136). That corpus is identity-masked, so the
class bridge is the gating prerequisite: **without it there is no admissible
lane (a) at all.** This session tests the bridge, not a lever.

### 0.2 Disclosure — what was inspected BEFORE this PREREG was written

Structural/feasibility inspection only, no adjudicating statistic:

* miso-136's committed record `_miso136_ct_offer_conduct_survey.json` — the
  corpus's 41 DA / 51 RT column names, per-day row and unit counts, region
  row counts, masked-ID persistence counts, and the zero type/fuel columns.
* One HTTP status check that `20240715_da_co.zip` is still live (`200`).
* EIA-860 column **coverage** only: `Minimum Load (MW)` non-null 0.700,
  `Summer Capacity (MW)` 0.997, `Winter Capacity (MW)` 0.997, `Nameplate
  Capacity (MW)` 1.000 nationally; the prime-mover code set; and that
  `eia860_plant.parquet` carries `Balancing Authority Code` with **2,855**
  MISO-coded plants (the scoping mechanism).
* The repo's `plant_taxonomy.PLANT_CLASSES` list.

**No per-class MISO aggregate, no corpus numeric field, and no classifier
output has been computed.**

---

## 1. The question

**Can masked units in MISO's `da_co` corpus be assigned to the model's
thermal classes — CT_PEAKER, CC_REGULAR, coal-steam — using OFFER-SIDE
declarations only, well enough that the resulting class aggregates reproduce
EIA-860's MISO fleet aggregates?**

If YES, the miso-134 successor lever (a measured MISO offer-curve surface at
class grain — the only admissible lane-(a) family left) becomes charterable
with its own PREREG. If NO, the prerequisite is closed with the corpus on
record and the charter's lane (c) owner assessment becomes the honest next
step.

---

## 2. Two-sided prior, disclosed AS a prior

My model-memory prior is that declared operating limits carry genuine
technology signal: gas CTs are small, near-zero-min-load and lose 10–25 % of
capability between winter and summer ambient; gas CCs are large with a
~0.4–0.6 min-load fraction and a milder derate; coal steam is large with a
high min-load fraction and a small derate; nuclear is large, ~flat, min-load
near 1.0.

**I hold the outcome genuinely uncertain — call it near 50/50** — and I name
the failure mode I consider most likely in advance:

> **`Economic Max` is a submitted COMMERCIAL declaration, not a measured
> capability.** If MISO participants submit a static registration value, the
> seasonal-derate fingerprint is identically zero for every technology, the
> feature space collapses to "big vs small", and CC cannot be separated from
> coal — which is precisely the split the lane needs, since both are large.

A second, independent failure mode: the corpus's commercial **unit grain**
(a whole combined-cycle block registered as one market unit) does not match
EIA-860's **generator grain** (CT and CA parts as separate generators), so
even a perfect classifier would mis-count. This is handled by the
pre-registered two-grain sensitivity in §5, not by choosing the grain that
wins.

I am not predicting which way this goes and I will report whichever it is.

---

## 3. Admissible and forbidden inputs

**Admissible (offer-side declarations + registration-grain public data):**

| source | fields |
|---|---|
| `da_co` corpus | `Economic Max`, `Economic Min`, `Emergency Max`, `Emergency Min`, `Economic Flag`, `Emergency Flag`, `Must Run Flag`, `Unit Available Flag`, `Self Scheduled MW`, `Region`, `Unit Code` (as an opaque key), `Min/Max/EmerMinEnergyStorageLevel` (exclusion only), `Date/Time Beginning (EST)` |
| EIA-860 | `Prime Mover`, `Technology`, `Energy Source 1`, `Nameplate/Summer/Winter Capacity (MW)`, `Minimum Load (MW)`, `Plant Code`, `Balancing Authority Code`, `Status` |

**FORBIDDEN — machine-enforced by the probe, which asserts the feature
builder never dereferences them:**

* every `Price1…Price10` and `MW1…MW10` offer-curve column, and `Slope`, and
  `Curtailment Offer Price` — these ARE the conduct statistic the successor
  lever would measure; classifying by them is circular (miso-136 §6);
* the corpus's outcome columns — DA `MW` award, RT `Cleared MW1…12`;
* any CEMS / dispatch / generation / metered series, at any grain — the
  miso-103 answer-key family;
* any model output, any residual, any scorer quantity. **Nothing in this
  session is sized to a residual** (rules 1 / 21 / 24).

---

## 4. Design — the discriminant is identified on a HELD-OUT population

Zero parameters are fitted to the corpus, and zero to MISO.

**Features (three, each with an exact EIA-860 analogue so the discriminant
can cross populations):**

| feature | corpus construction | EIA-860 analogue |
|---|---|---|
| `logcap` | log10 of the per-unit max `Economic Max` over all sampled hours | log10 `Summer Capacity (MW)` |
| `derate` | 1 − (max `Economic Max` over summer days) / (max over winter days) | 1 − Summer / Winter Capacity |
| `minfrac` | median over hours with `Economic Max` > 0 of `Economic Min` / `Economic Max` | `Minimum Load (MW)` / `Summer Capacity (MW)` |

Secondary offer-side features — emergency headroom
`(Emergency Max − Economic Max)/Economic Max`, self-schedule hour fraction,
must-run hour fraction, available hour fraction, Region — have **no EIA-860
analogue**, so they are **reported as corroborating evidence and are NOT in
the primary discriminant**.

**Pre-specified classifier:** Gaussian naive Bayes over
(`logcap`, `derate`, `minfrac`), fitted on **EIA-860 generators OUTSIDE
MISO** (`Balancing Authority Code != "MISO"`, `Status` operable), with class
priors set to the **non-MISO** class frequencies. Validated against EIA-860
**inside** MISO. No hyperparameter is tuned; no threshold is chosen after
seeing a corpus number. Pre-registered sensitivity: the uniform-prior
variant is reported alongside.

**Class set:** `{CT, CC, COAL, NUC, OTHER}`. Targets are CT / CC / COAL;
NUC is the positive control (§6 G-4); OTHER absorbs the rest.

**Pre-registered exclusion screens, offer-side only, applied before
classification:**

1. **Storage** — any of the three energy-storage-level columns populated.
2. **Variable-output (VER)** — median over sampled days of the within-day
   coefficient of variation of `Economic Max` > **0.15**. A thermal unit's
   declared capability moves only with ambient (CV ≈ 0.03–0.05); a wind or
   solar unit's tracks its forecast and collapses to zero overnight. The
   excluded set's total capability is checked against EIA-860 MISO wind+solar
   as a secondary.
3. **Coverage** — a unit needs ≥ 2 valid days (≥ 1 hour with
   `Economic Max` > 0) in **each** season to receive a `derate`; units
   failing this are dropped from the primary and the loss is reported.

**Sampling (rule 22 — 2023–2025 only), 24 `da_co` days, 4 per season per
year, fixed before any fetch:**

* 2023 summer `0718 0719 0815 0816` · winter `0117 0118 0214 0215`
* 2024 summer `0716 0717 0813 0814` · winter `0116 0117 0213 0214`
* 2025 summer `0715 0716 0812 0813` · winter `0114 0115 0211 0212`

Fetched to scratch only. **Nothing is written under `data/raw/`** — an actual
corpus intake needs its own authorization and the `data-intake` contract
(charter DATA GATE).

---

## 5. Gates, in order. G-0 and G-1 are GATING

**G-0 — basis reconciliation (GATING).** Does the corpus's declared
capability reconcile with EIA-860 MISO registration capacity at *fleet*
grain? Compare total classified-eligible capability and unit count.
**PASS** if total MW is within **±30 %** and unit count within **±40 %** —
deliberately generous, because the market's commercial unit model genuinely
differs from the registration grain (aggregated CC blocks, pseudo-ties, DR,
external resources). **If the total is off by more than 2×, no distributional
validation against EIA-860 is meaningful: report the basis defect and STOP.**

**G-1 — identification, on ground truth (GATING).** Do the three features
separate the classes in the held-out non-MISO EIA-860 population, where
labels are known? **PASS** if the pre-specified classifier reaches
**≥ 0.70 balanced accuracy** over `{CT, CC, COAL, NUC}` under 5-fold
cross-validation within the non-MISO population. **If G-1 fails, the bridge
is REFUTED on identification** — the features carry no usable class signal
even where the answer is known, so no masked-corpus bridge built on them can
work. This is a clean, informative NO and it costs no corpus statistic.

**G-2 — the primary separation statistic (two-sided).** For each target
class k ∈ {CT, CC, COAL}:

    S_cap(k)   = (MW_corpus(k)   − MW_860(k))   / MW_860(k)
    S_count(k) = (N_corpus(k)    − N_860(k))    / N_860(k)

**G-3 — within-class shape.** For each target class, the corpus's
within-class capability **p50** must agree with EIA-860 MISO's same-class p50
within **±30 %**, and **p90** within **±35 %**.

**G-4 — the nuclear positive control.** MISO's nuclear fleet is small and
exactly known. The rule must recover its unit count within **±3** and its
capacity within **±25 %**. Two-sided: failure here is diagnostic in its own
right — it would say the corpus's declaration basis is commercially
flattened even for the most distinctive technology on the system.

---

## 6. THE LOOK-ALIKE TRAP, named in advance — and the null that catches it

> **Aggregate distributional agreement is compatible with an arbitrarily
> scrambled per-unit assignment.** The masked units carry no ground-truth
> labels, so matching per-class counts and MW does **not** establish that any
> individual unit is correctly classified. A classifier that merely
> reproduced the right class *sizes* would pass G-2 while carrying no
> information at all — and the derived class offer curves would be averages
> over the wrong units.

Pre-committed mitigation, both legs required:

* **(i)** G-3 within-class quantile agreement, which a size-preserving
  scramble cannot reproduce; and
* **(ii)** a **size-preserving label-permutation null**: shuffle the assigned
  class labels across the classified corpus units, holding the class sizes
  fixed, **1,000 draws**, and recompute the G-3 discrepancy. The observed
  G-3 discrepancy must fall **below the 5th percentile** of the null.

**If (ii) fails, the bridge is NOT demonstrated no matter how well G-2
reads.** This leg outranks the aggregate statistic.

---

## 7. Pre-committed decision rule

**DEMONSTRATED** — all four:

* **D1** for each of {CT, CC, COAL}, |S_cap| ≤ **0.25** and |S_count| ≤
  **0.35**, at **both** EIA-860 grains and in **≥ 2 of the 3** sampled years;
* **D2** G-3 passes for all three target classes;
* **D3** the §6(ii) permutation null is beaten (observed < 5th percentile);
* **D4** the G-4 nuclear control passes.

**REFUTED** — any one:

* **R1** G-1 fails (identification, on ground truth); or
* **R2** some target class has |S_cap| > **0.50** at both grains in ≥ 2
  years; or
* **R3** degenerate collapse — one class takes > **60 %** of classified
  capability; or
* **R4** the §6(ii) null is not beaten.

**NOT ASSERTED** — the verdict flips across the two EIA-860 grains, or across
the three years. Carrying miso-137's own lesson forward: *a grain is a
hypothesis, not a definition* — if the answer moves with the grain, the grain
is the finding, and the flip is reported rather than resolved by choosing.

---

## 8. Kills and standing bars

* **K1** No LP is solved and no arm is proposed in this session. A bridge is a
  data prerequisite, not a mechanism.
* **K2** **No cell verdict is minted** unless a mechanism is tested — none is
  (rule 28(b), the miso-131…137 precedent). `measured_offer_surface` MISO
  stays `U` whatever this session concludes.
* **K3** Nothing is written under `data/raw/`; no parameter is derived from
  the corpus; the corpus is not committed (charter DATA GATE).
* **K4** No threshold, band or feature is changed after a corpus number is
  seen. If the design proves unworkable mid-run, the session reports the
  design failure — it does not re-cut and re-report.
* **K5** No number in this session is sized to any residual, and no window,
  magnitude or localisation from miso-137 enters any construction here
  (rules 1 / 21 / 24).
* **K6 — ONE BASIS.** The EIA-860 comparison is made at each grain
  separately and never blended (miso-133 bar).
* **K7 — a bridge is not a lever.** Even a DEMONSTRATED verdict licenses only
  a *charter* for the successor, with its own PREREG and full kill stack; it
  arms nothing.

---

## 9. Stop rules

* G-0 fails by more than 2× → report the basis defect and stop.
* G-1 fails → REFUTED on identification; report and stop, no corpus
  classification computed.
* Corpus unavailable for a sampled day → substitute the next operating day of
  the same month, record the substitution, never widen the year span.

---

**Probe:** `scripts/probes/_miso138_da_co_class_bridge.py` ·
**Record:** `results/calibration/_miso138_da_co_class_bridge.json`.
