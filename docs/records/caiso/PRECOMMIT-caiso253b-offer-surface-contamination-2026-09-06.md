# PRECOMMIT — caiso-253b: THE MEASURED OFFER SURFACE'S OWN DISCLOSED DEFECT. Is the CT bucket contaminated by the 2.9 GW of OTC/RMR steamers, and does the measured-slope population say so? A CONSTRUCTION repair on a frozen derive, judged on the construction and NEVER on which way the bands move.

**Session caiso-253b, 2026-09-06.** Branch
`claude/caiso-backcast-calibration-253-9dgorn` off `main` `82f79693`.
Keeper **`2026-09-05-caiso-252-b1-notrim`** UNCHANGED, DETERMINATION
**CALIBRATED**. Rule 22 `[R-HOLDOUT]`: 2023–2025 only; no `complete`/`final`
marker; freeze ACTIVE.

**Pushed BEFORE any bid data is fetched and before any statistic is computed.**

---

## §0 — HOW WE GOT HERE, STATED PLAINLY SO THE MOTIVE IS ON THE RECORD

The owner asked whether the gas offer curves can be scaled down to pull the
+4.65 / +9.04 / +8.86 % C3a overshoot toward zero — a move rule 1
`[R-STRUCT]`'s 2026-09-05 amendment expressly authorizes. **On CAISO that
channel turns out to be empty**, and the measurement is in §0.1. The owner
then chose the data route: *re-derive the measured surface*.

**This document exists because the motive is a residual, and rule 23
`[R-FROZEN-DERIVE]` forbids re-deriving a measured-behaviour parameter because
a residual moved.** The only admissible object here is therefore a **defect in
the derive's CONSTRUCTION** — a thing that is wrong whichever way fixing it
moves the price — and the whole of §2 exists to make the direction unusable as
evidence. If no construction defect is measured, **nothing is re-derived and
the bands stay exactly where they are**, whatever C3a does. Precedent:
caiso-243, "A DATA-INTEGRITY REPAIR, NOT A CALIBRATION LEVER".

### §0.1 — Why the scale-down channel is empty (measured, zero-LP)

Armed band vs CAISO's OWN measured OASIS median, read from
`run_config.scenario_config.offer_curve_by_group` against
`data/raw/_validation-source/caiso_offer_curve_measured.json`:

| class | econ_low | econ_high | peak | `committed` (the only FREE band) |
|---|--:|--:|--:|--:|
| CC_REGULAR / CC_CHP | 1.066 = **measured** | 1.072 = **measured** | 1.386 = **measured** | 1.000 vs measured 1.030 → **0.971×** |
| CT_PEAKER | 1.145 = **measured** | 1.166 = **measured** | 1.166 = **measured** | 0.991 vs 1.166 → **0.850×** |
| CT_CHP | 1.145 = **measured** | 1.166 = **measured** | 1.166 = **measured** | 1.100 vs 1.166 → **0.943×** |
| ST_GAS | 1.145 = **measured** | 1.166 = **measured** | 1.166 = **measured** | 0.810 vs 1.166 → **0.695×** |

Both `caiso_offer_surface_measured` and `..._ungrounded` are ARMED in the
keeper, so all four bands of all five gas classes are merged from the measured
artifact at config-build time. **There is no band on CAISO's gas path where
scaling DOWN moves toward measurement**: three are already AT the measured
value and the fourth is already below it. Rule 13's own amendment: "a
rescaled measured input remains forbidden however it is motivated."

Size, for the record: zeroing C3a needs ≈ **0.91×** uniform on the gas bands,
putting CC_REGULAR `econ_low` at 0.97 against a measured 1.066 — a **9 %**
declared departure from CAISO's own bid record.

### §0.2 — And the residual is not where an offer level can reach it

caiso-229 §4's DEPTH leg, **re-measured on the current keeper** (its §10.1
expressly permits re-running against a NEW keeper; the keeper has moved three
times since, including a gas-offer functional-form change at caiso-251).
Model CC floor `cc_min = base_hr × committed × (gas + 0.057 × P_carbon)`:

| year | cc_min | hours actual clears BELOW it | mean depth | (caiso-220 keeper) |
|---|--:|--:|--:|---|
| 2023 | $32.91 | 24.9 % | $15.98 | 44.0 % / $20.77 |
| 2024 | $31.24 | 36.7 % | $19.02 | 46.9 % / $17.16 |
| 2025 | $38.10 | **48.1 %** | $18.26 | 44.9 % / $17.50 |

The kill has **shifted but not vanished**, and 2025 is worse than it was.
Nearly half of 2025 clears ~$18 below the model's floor against a ~$1.4
admissible offer-level move — caiso-229's scale-invariance kill, intact.

---

## §1 — THE OBJECT: a defect the derive DISCLOSES about itself

`scripts/data/derive_caiso_offer_surface.py` classifies masked OASIS bidders
by the **Theil-Sen slope** of their body bid price on the CA citygate — a
measured marginal heat rate — then splits the gas population at
`hr_cut = 8.5` MMBtu/MWh into a CC bucket (below) and a CT bucket (at/above).
Its own provenance block records what that leaves behind:

> "CT bucket may include the 2.9 GW OTC/RMR ST_GAS steamers and priced CT_CHP;
> CC bucket may include CC_CHP. Same-fuel near-SRMC bidders; bounded by G1,
> robust via cap-weighted medians; masked ids preclude per-plant mapping."

**The CT bucket is 100 resources** (CC is 46). The steamers' fleet heat rate
is **≈ 11.85** against CT_PEAKER's fleet base of **10.862**, and the
multiplier is `(band_price − VOM) / (base_HR_class × gas)` — so a steamer
bidding at pure SRMC still lands a multiplier inflated by roughly its own
HR ratio, ≈ 11.85 / 10.862 ≈ **1.09×**, purely because it is being divided by
another class's base heat rate. **Then `caiso_offer_surface_measured_ungrounded`
propagates that same pooled CT median to CT_CHP AND to ST_GAS itself** — so
the steamers are priced off a bucket their own presence biased.

**Why this is a construction defect and not a residual story:** a class's
multiplier is defined against *its own* base heat rate. Pooling two
populations with a 9 % heat-rate separation into one median makes the
multiplier a statistic of the mixture, not of either class. That is wrong
whichever direction it moves the price.

---

## §2 — THE TEST, AND THE MACHINERY THAT MAKES ITS DIRECTION UNUSABLE

### §2.1 — G-BIMODAL (the load-bearing gate; zero re-derive)

Rebuild the derive's own per-resource Theil-Sen slope population **with the
derive's own frozen gates** (`body_frac` 0.35, slope ∈ [4, 18], r ≥ 0.6,
≥ 120 resource-days, ≥ 20 MW) and ask ONE question: **does the capacity
density of the CT-side population (slope ≥ 8.5) carry a second antimode
separating an aero-CT mode near 9–11 from a steam mode near 11.5–12.5?**

* **PASSES** iff a capacity-density antimode exists in **[10.9, 12.5]**
  MMBtu/MWh — the interval between CT_PEAKER's fleet base HR and the steamers'
  known ≈ 11.85 — in the pooled 2023–2025 population, **and** the capacity
  sitting above it is within **[1.5, 4.5] GW** (the 2.9 GW of OTC/RMR steamers
  plus priced CT_CHP, bracketed generously in both directions).
* **FAILS** otherwise ⇒ **NOTHING IS RE-DERIVED.** A unimodal CT population
  means the contamination is not separable from measured conduct, the
  disclosed note stands as a known bound, and the bands stay where they are.

The interval and the capacity bracket are **fixed here, before the population
is built**, and are derived from published fleet heat rates — not from where a
mode happens to land, and not from any price.

### §2.2 — THE DIRECTION IS PRE-COMMITTED AS UNUSABLE

The repair splits one contaminated bucket into two clean ones. It therefore
moves **two multipliers in opposite directions by construction**:

* CT_PEAKER's median loses its high-HR tail ⇒ its multiplier should **FALL**;
* ST_GAS gains its own bucket instead of borrowing CT's ⇒ its multiplier
  should **RISE** (it is currently divided by a base HR 9 % below its own).

**I register now that BOTH are expected, that the net price effect is
genuinely ambiguous, and that the repair is adopted or refused on G-BIMODAL
ALONE.** If G-BIMODAL passes, the re-derived bands are adopted **whatever
they are and whichever way C3a moves — including if C3a gets WORSE.** That is
the caiso-230/231 precedent exactly: the measured surface was armed knowing
and disclosing that it cost C3a +0.235 / +0.344 / +0.421 $/MWh.

### §2.3 — Admissibility

* **Rule 23 `[R-FROZEN-DERIVE]`** — this is NOT a re-derivation of the same
  construction hoping for a different number. The estimator (Theil-Sen), the
  body probe (0.35), the gas gates, the statistic (cap-weighted median), the
  VOM and carbon netting and the band-window geometry are **all frozen and
  untouched**. The ONLY change is that the class partition stops pooling two
  measured populations. The commit will cite the construction defect, per the
  rule's own requirement.
* **Rule 14 `[R-ACCURATE]`** — a measured-input improvement; if it makes the
  backcast worse it still stands (the rule's central case).
* **Rule 25 `[R-ISO-SCOPE]`** — CAISO's own bid record throughout; the repair
  also RETIRES a rule-25 problem, since ST_GAS currently prices off a bucket
  it does not belong to.
* **Rule 21 `[R-DOF]`** — **zero new free parameters.** The second cut is an
  antimode located the same way `hr_cut = 8.5` was (gate G2's own criterion);
  it is not swept and it is not chosen against any criterion.
* **Rule 13 `[R-MEASURED]`** — pooled 2023–2025 throughout. **Per-year
  measured multipliers remain inadmissible** (caiso-229 §10.2: no forward
  analogue) and are not proposed.
* **Rule 1 `[R-STRUCT]`** — C3a and C4 are EXCLUDED from the adoption
  decision in both directions.

---

## §3 — PREDICTIONS, WRITTEN TO BIND

| # | prediction | uncomfortable reading if it fails |
|---|---|---|
| **P-1** | the corpus re-fetches to **1,095 / 1,096** trade dates, 2023-06-01 the one genuine OASIS hole (caiso-178's intake record) | a different coverage means the archive changed under us and the frozen artifact is not reproducible from its own stated source |
| **P-2** | rebuilding the derive's classifier on the re-fetched corpus reproduces the frozen bucket populations to **±3 resources and ±5 % capacity** per bucket (46 CC / 100 CT) | I am not rebuilding the construction the artifact came from, and nothing downstream is trustworthy — stop |
| **P-3** | **G-BIMODAL passes**: a capacity-density antimode in [10.9, 12.5] with 1.5–4.5 GW above it | unimodal ⇒ the contamination is not separable; nothing is re-derived and the note stands |
| **P-4** | the de-contaminated CT_PEAKER `econ_low` falls to **[1.03, 1.12]** from 1.145 | outside: the steamers were not what set the pooled median |
| **P-5** | a separated ST_GAS bucket's `econ_low` **RISES above 1.145** | if it does not rise, my HR-ratio account of the bias is wrong and §1's mechanism needs re-thinking |
| **P-6** | the CC bucket is **materially unchanged** (within ±0.01 on all three bands) — the repair is CT-side | a CC move means the cut at 8.5 is also mis-set, which is a bigger and separate object |
| **P-7** | net first-order effect on the annual load-weighted price is **under ±$1.0/MWh** and its SIGN is not predicted here | a large move means one bucket dominates and the "ambiguous direction" framing was wrong |

**P-7 deliberately declines to predict the sign.** If I could, the direction
would be doing work the construction is supposed to do alone.

---

## §4 — STOP RULE

1. **G-BIMODAL failing ⇒ nothing is re-derived, nothing is armed, the bands
   stay.** The session reports the population and closes the object.
2. **P-2 failing ⇒ stop before any re-derive.** A classifier I cannot
   reproduce is not one I may repair.
3. **No threshold in the derive is retuned** — not the estimator, the body
   probe, the gas gates, the statistic, the VOM, the carbon factor, the band
   geometry, or `hr_cut = 8.5` itself. The second cut is located by the
   antimode and by nothing else.
4. **No gate is re-run to a pass or redefined after its result**, and the
   antimode interval and capacity bracket in §2.1 are fixed as written.
5. **Per-year multipliers are never armed** (caiso-229 §10.2).
6. **No solve is earned by this document.** A re-derived artifact changes the
   keeper's inputs, so it needs its own rule-29 screen and its own PRECOMMIT
   addendum before any LP is spent, with C4 (0.003 of margin at 2025) and C1
   as stop gates.
7. If the corpus cannot be re-fetched, the session reports that and stops —
   the frozen artifact is not edited by hand under any circumstances.

---

## §5 — DELIVERABLES

This PRECOMMIT (pushed first); the re-fetched corpus (gitignored, as the
README specifies); an audit probe building the per-resource slope population
by **streaming** `scripts/lib/dam_public_bids/caiso.py::parse_day` (the
`derive_caiso_battery_bid_floor.py` precedent — the curation path needs
≈ 14.3 GB for one year against 15 GB of RAM and must not be used); its
committed JSON; a FINDING with G-BIMODAL scored; and, only if G-BIMODAL
passes, the derive's class-partition repair plus the re-frozen artifact — with
its own addendum, its own screen and its own solve, none of which this
document authorizes.
