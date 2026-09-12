# FINDING (pjm-h1): the PJM hydro miss is **100 %** an accounting seam, not ~80 % — and the
# mechanism is NOT `classify_plant`. It is the benchmark's own EIA-930 swap, on a series the
# repo already registers as pumped-storage-contaminated.

**Session** `pjm-h1` · **ISO** PJM · **Date** 2026-09-12 · **Branch** `claude/pjm-h1`
**ZERO LP.** Committed artifacts + the on-disk measured sources only. Nothing solved, nothing
registered, nothing armed, no shared code changed.
**Keeper UNCHANGED** — `2026-09-11-pjm-d4-4-gasoutage` (2023-2025) re-scored in this session:
**CALIBRATED, 0 caveats, 0 fails, basis verbatim "all criteria pass, governance attested."**
Holdout `2026-09-11-pjm-holdout-gasoutage-touchpoint` (2020-2022) unchanged at NOT-YET.

---

## 1. RESULT — and the first line is against the card that commissioned it

> **THE HANDOFF'S PREMISE IS REFUTED AS STATED, AND THE SEAM IS REAL BY A DIFFERENT ROUTE THAT
> MAKES IT BIGGER.**
>
> The card's mechanism — `classify_plant`'s `fuel == "WAT"` short-circuit routing pumped storage
> into `hydro`, putting "≈ 5-6 TWh/yr of PS gross generation" into the EIA-923 `classFull.hydro`
> actual — **fails on the data in two independent ways**:
>
> 1. **EIA-923 reports pumped storage as NET generation, which is NEGATIVE** (the round-trip
>    loss). PJM's PS rows contribute **−1.78 to −2.67 TWh/yr** to the 923 hydro bucket, not
>    +5-6. The sign is backwards.
> 2. **The 923 hydro bucket is not the C1 actual for PJM anyway.** PJM's 923 bucket is
>    6.19-8.44 TWh; the committed bench's `classFull.hydro` is **15.47-16.64 TWh**. They are not
>    the same number and never were.
>
> **What IS true** is the code fact the card found — `classify_plant('WAT','PS',…) → 'hydro'`,
> flatly contradicting the comment two lines above it — and it is a real latent trap worth
> fixing (§5). It is simply not the cause of PJM's hydro miss.
>
> **THE ACTUAL MECHANISM, traced end-to-end:**
> `run_calibration_full._backfill_renewables_eia930` lists `hydro` in
> `_EIA930_RENEWABLE_CLASSES` and **replaces the whole class with the EIA-930 `NG: WAT` grid
> total** whenever the 923 class total falls below `_EIA923_RENEWABLE_COMPLETENESS_FRACTION`
> (0.90) of it. For PJM that ratio is **0.40-0.55**, so the swap fires in **every year**, and
> the C1/dashboard hydro actual **IS** EIA-930 `NG: WAT` (matched to 4 dp in all six years).
> And `constants.EIA930_PS_FOLDED_INTO_WAT` — the repo's own registry — already declares
> **`{"MISO", "PJM"}`**: PJM files no `NG: PS` column, so its `NG: WAT` is a conventional-hydro
> **plus pumped-storage-gross-discharge** series.
>
> **So the model's conventional-hydro LP class is being scored against a different population's
> meter.** That is not a modelling miss; it is a unit mismatch.
>
> **AND THE ASYMMETRY IS SELF-INFLICTED, BY A KEEPER PROMOTION.** `pjm-143` (2026-07-31,
> `hydro_level_923_hy` PJM `U` → `K`) fixed exactly this contamination **on the model side** —
> it moved PJM's hydro budget LEVEL off `NG: WAT` and onto EIA-923 `HY`, removing 6.47-7.04 TWh
> of phantom hydro budget, and its §7 "Open, not actioned" list names three items, **none of
> which is the benchmark**. The model was deliberately moved to the clean population; the
> benchmark was left on the contaminated one. The ~44 % "miss" is the gap between the two
> decisions.
>
> **MEASURED LIKE-FOR-LIKE, THE MODEL'S CONVENTIONAL HYDRO IS WITHIN ±0.9 % IN EVERY
> COMPLETE-VINTAGE YEAR** (§3) — and §3 also states plainly why that is **plumbing, not skill**.
>
> **WHAT IS AT STAKE IS SMALLER THAN THE CARD ASSUMED, AND I CORRECT THE CARD ON IT (§4):**
> **`hydro` is not a C1 row at all.** C1 scores gas and coal classes only. The card read
> `class_is_gated('PJM','hydro',y) == True` as "hydro is C1-gated"; that predicate answers
> only "is the 923 vintage complete enough for this class this year". Measured: the repair
> moves the C1 volume band by **0.000 TWh** in all six years (the 8 TWh cap binds either way)
> and flips **zero** C1 cells. The repair is **gate-neutral** — which is why proposing it
> cannot be a residual fit.
>
> **NOTHING IS EXECUTED. `classify_plant` and the benchmark path are SHARED, ISO-AGNOSTIC code
> and this is a PJM lane** (§6 carries the measured cross-ISO blast radius: MISO and NEISO are
> contaminated too, ERCOT/CAISO/NYISO/SPP are not). **ESCALATED TO THE OWNER (§7).**

---

## 2. PHASE 0 — the group-by the card asked for, with PS stated per year

`classify_plant` over the F923 Page-1 monthly-generation extract, restricted to PJM by
`build_zone_lookup("PJM")` — the exact frame `run_calibration_full._eia923_frame` builds.

**Rows `classify_plant` routes to `hydro`, by `(fuel_type, prime_mover)`, TWh:**

| fuel / PM | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|
| `WAT` `HY` | 9.9324 | 10.2909 | 8.8854 | 8.9763 | 8.8612 | 2.2898 |
| **`WAT` `PS`** | **−1.7837** | **−1.8503** | **−2.3794** | **−2.5249** | **−2.6732** | **−2.6600** |
| **bucket total** | **8.1487** | **8.4406** | **6.5060** | **6.4513** | **6.1880** | **−0.3703** |

Every PS-prime-mover row in PJM lands in `hydro` (none anywhere else): −18.5296 TWh over
2018-2026, one cell. The five plants are Bath County (−1.0343 TWh in 2023), Muddy Run (−0.4657),
Seneca (−0.4391), Smith Mountain (−0.4206), Yards Creek (−0.1652).

**The card predicted ≈ +5-6 TWh of PS in this bucket. It is −1.78 to −2.67.** EIA-923 reports PS
*net*, and a pumped-storage fleet is a net consumer. 2025 is an early monthly release (2.29 TWh
of `HY` against a modal ~8.9) and is not differenced anywhere below.

**Where the C1 actual really comes from:**

| year | bench `classFull.hydro` | EIA-930 `NG: WAT` | 923 bucket | 923/930 | swap fires? |
|---|---:|---:|---:|---:|:--:|
| 2020 | 15.8943 | **15.8943** | 8.1487 | 0.51 | YES |
| 2021 | 16.6400 | **16.6400** | 8.4406 | 0.51 | YES |
| 2022 | 15.9967 | **15.9967** | 6.5060 | 0.41 | YES |
| 2023 | 15.4676 | **15.4676** | 6.4513 | 0.42 | YES |
| 2024 | 15.8562 | **15.8562** | 6.1880 | 0.39 | YES |
| 2025 | 15.5065 | **15.5065** | −0.3703 | — | YES |

`classFull.hydro == NG: WAT` to 4 dp in every year, so the BTM subtrahend on hydro is exactly
**0.000000 TWh** (the card's item 3, answered). PJM files **no `NG: PS` series** — confirmed on
the extract, whose fuel columns are `COL NG NUC WAT SUN WND OIL OTH`. That is signature (a) of
`pjm-143` §1, reproduced independently here.

---

## 3. THE RESIDUAL, DECOMPOSED — and it is not four legs, it is two

Sizing the PS fold as `NG: WAT − 923 HY`, with an independent physical cross-check:

| year | `NG: WAT` | 923 `HY` | **PS fold** | 923 PS net | implied pump load | **implied round-trip η** |
|---|---:|---:|---:|---:|---:|---:|
| 2020 | 15.8943 | 9.9324 | **5.9619** | −1.7837 | 7.7456 | **0.770** |
| 2021 | 16.6400 | 10.2909 | **6.3491** | −1.8503 | 8.1994 | **0.774** |
| 2022 | 15.9967 | 8.8854 | **7.1113** | −2.3794 | 9.4907 | **0.749** |
| 2023 | 15.4676 | 8.9763 | **6.4913** | −2.5249 | 9.0162 | **0.720** |
| 2024 | 15.8562 | 8.8612 | **6.9950** | −2.6732 | 9.6682 | **0.724** |

The implied round-trip efficiency lands at **0.72-0.77** in every complete-vintage year — a
physically correct number for a five-plant PS fleet, derived from two independent surveys that
were never reconciled to each other. **That is the corroboration that the residual `NG: WAT` −
923 `HY` really is PS gross discharge** and not a 923 coverage gap. (My 2023/2024 fold,
6.4913 / 6.9950, reproduces `pjm-143` §1's 6.475 / 6.957 to ≤ 0.04 TWh on an independently
built frame.)

**The card's premise table, reproduced from the committed payloads:**

| yr | bench hydro | model hydro | m/a | model PS discharge | h+PS | (h+PS)/a | residual |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2020 | 15.8943 | 10.0218 | 0.631 | 5.5062 | 15.5280 | 0.977 | −0.3663 |
| 2021 | 16.6400 | 10.3759 | 0.624 | 5.0817 | 15.4576 | 0.929 | −1.1824 |
| 2022 | 15.9967 | 8.9685 | 0.561 | 5.1560 | 14.1245 | 0.883 | −1.8722 |
| 2023 | 15.4676 | 8.9030 | 0.576 | 5.2597 | 14.1627 | 0.916 | −1.3049 |
| 2024 | 15.8562 | 8.8608 | 0.559 | 5.8569 | 14.7177 | 0.928 | −1.1385 |
| 2025 | 15.5065 | 8.4636 | 0.546 | 5.7449 | 14.2085 | 0.916 | −1.2980 |

(The card's numbers reproduce to ≤ 0.05 TWh; the small drift is the current keeper vs the one
its table was built on.)

**THE DECOMPOSITION — the residual is ONE leg, not a spread of four:**

| yr | residual | leg 1 · conventional hydro | leg 2 · PS discharge | leg 1 share | leg 2 share |
|---|---:|---:|---:|---:|---:|
| 2020 | −0.3663 | **+0.0894** | −0.4557 | −24.4 % | 124.4 % |
| 2021 | −1.1824 | **+0.0850** | −1.2674 | −7.2 % | 107.2 % |
| 2022 | −1.8722 | **+0.0831** | −1.9553 | −4.4 % | 104.4 % |
| 2023 | −1.3049 | **−0.0733** | −1.2316 | 5.6 % | 94.4 % |
| 2024 | −1.1385 | **−0.0004** | −1.1381 | 0.0 % | 100.0 % |

**Leg 1 — conventional hydro — is ≤ 0.09 TWh in every year, i.e. ±0.9 %.** The card's item 4
asked me to chase the 5× spread between 2020 (−0.41) and 2022 (−1.87) rather than average it
away: **the spread is entirely leg 2**, the model's PS fleet discharging 5.08-5.86 TWh against
an implied actual 5.96-7.11. That is a **storage-cycling** question, and PJM's
`pumped_storage_cycling_depth` cell is already **`G`** (governance-closed,
`docs/multi-iso/pjm-ps-cycling-diagnosis-2026-06.md`) — so it is routed, not opened.

**STATED AGAINST THE RESULT, because it decides how much the ±0.9 % is worth:** the model's
hydro level is **PINNED** to EIA-923 `HY` by `hydro_level_923_hy` (PJM `K`, pjm-143), and hydro
is a declared D-10 **free class** (L6, "hydro (monthly budgets)") precisely because its actual
is a measured realization the model is pinned to. **±0.9 % here measures plumbing, not skill.**
What it *does* establish — which is the point — is that the model and the benchmark are on two
different populations, and which of the two is the mismatched one.

---

## 4. WHAT IS AND IS NOT AT STAKE — the card is corrected here

**`hydro` is not a C1 row.** `calibration_verdict.score_fuelmix` iterates exactly
`['CC_REGULAR','CC_CHP','CT_PEAKER','ST_GAS','ST_CHP','COAL_PRB','COAL_LIGNITE','COAL_BIT','COAL_WC','COAL']`.
`class_is_gated(iso, klass, year)` is the **EIA-923 vintage-completeness** predicate — it returns
True for any class in a complete vintage — and the card read it as C1 row membership.

Measured, replacing `classFull.hydro` with the conventional-only 923 `HY` actual:

| yr | `a_gen` now | repaired | Δ | C1 band now | repaired | Δ band | 8 TWh cap binds? | C1 cell flips |
|---|---:|---:|---:|---:|---:|---:|:--:|:--:|
| 2020 | 788.457 | 782.495 | −5.962 | 8.000 | 8.000 | **+0.000** | yes | **none** |
| 2021 | 814.849 | 808.499 | −6.349 | 8.000 | 8.000 | **+0.000** | yes | **none** |
| 2022 | 824.530 | 817.419 | −7.111 | 8.000 | 8.000 | **+0.000** | yes | **none** |
| 2023 | 818.784 | 812.292 | −6.491 | 8.000 | 8.000 | **+0.000** | yes | **none** |
| 2024 | 847.454 | 840.459 | −6.995 | 8.000 | 8.000 | **+0.000** | yes | **none** |
| 2025 | 866.320 | 853.104 | −13.217 | 8.000 | 8.000 | **+0.000** | yes | **none** |

So the honest prioritisation, stated rather than inflated: **this does not threaten the keeper,
does not move a gate, and is not urgent for the backcast determination.** It matters for
(i) the correctness of a **published** per-class number — the Run Explorer's non-fossil panel
reads PJM hydro at −44 % on a comparison that cannot be right in either direction;
(ii) **forecast credibility**, since the forward hydro level rides the same `NG: WAT`-vs-`923 HY`
choice `eia930_wat_level_folded` already adjudicates; and (iii) the fact that a shared
classifier contradicting its own comment (§5) is a live trap for every future lane.

---

## 5. THE `classify_plant` DEFECT IS REAL — it is just a different, smaller defect

```python
# Hydro: fuel code WAT or a hydraulic-turbine prime mover (HY / HA). Pumped
# storage (PS) is left to OTHER — it is a storage resource, not a generator.
HYDRO_PRIME_MOVERS: frozenset[str] = frozenset({"HY", "HA"})
...
    if fuel == "WAT" or pm in HYDRO_PRIME_MOVERS:
        return "hydro"
```

Run: `classify_plant('WAT','PS',False,0) -> 'hydro'`; only `classify_plant(None,'PS',…)` reaches
`'OTHER'`. **The comment describes behaviour the code does not have.**

**Two live consequences, both measured:**

1. **Where the EIA-930 hydro swap does NOT fire, the 923 hydro bucket carries PS NET and
   DEFLATES the hydro actual** (making the model look long, the opposite of PJM's sign):
   NYISO −0.33 to −0.45 TWh/yr (2020-2024, swap never fires), CAISO −0.14 to −0.53 (2020, 2023,
   2024), SPP −0.05 to −0.12 (2020-2024), NEISO 2023 −0.375, MISO 2021 −0.72. Small, but real,
   and in five ISOs.
2. **`run_calibration_full._pumped_storage_plant_ids()` is a DEAD NO-OP.** Its docstring says
   *"`classify_plant` buckets PS into OTHER, but PS is dispatched as an LP storage resource
   … so leaving its EIA-923 net generation in the injection would double-count it"*, and
   `_reconciled_mustrun_class` filters PS out of `OTHER`. PS never reaches `OTHER`. The guard
   protects nothing, and it reads as though the PS question is handled.

Neither is executed here. Both are ISO-agnostic shared code (§6/§7).

---

## 6. §4 CROSS-ISO BLAST RADIUS — measured, so the owner rules with the numbers

Per ISO-year: does the benchmark's EIA-930 hydro swap fire, and is that ISO-year's `NG: WAT`
PS-folded by the repo's own `data.hydro.eia930_wat_level_folded`?

| ISO | swap fires | `NG: WAT` folded | **C1 hydro actual CONTAMINATED** | fold size (TWh/yr) |
|---|---|---|---|---|
| **PJM** | every year | **yes (flat registry)** | **2020-2025, all six** | **5.96 - 7.11** |
| **MISO** | 2020, 2022-2025 | **yes (flat registry)** | **2020, 2022, 2023, 2024, 2025** | 0.39 - 1.70 |
| **NEISO** | 2020-2022, 2024 | **yes (< 2025, time-split)** | **2020, 2021, 2022, 2024** | 0.42 - 0.68 |
| CAISO | 2021, 2022, 2025 | no | no | — |
| NYISO | 2025 only | no | no | — |
| SPP | 2025 only | no | no | — |
| ERCOT | 2025 only | no (no PS fleet) | no | — |

(2025 folds are inflated by the early-release 923 vintage and are not a clean size.)

**PJM is 4-10× the next-largest and is the only ISO contaminated in every year.** The repair
has a precedent that is already owner-adjudicated on the *model* side: `eia930_wat_level_folded`
is a shared, cited predicate (miso-109 backcast pin, miso-110 forward climatology, neiso-72
time split) carrying **zero free parameters**. The benchmark repair is the same predicate,
applied at the other end of the same comparison.

---

## 7. THE OPTIONS — my recommendation is stated so it can be overruled

**(a) REPAIR THE BENCHMARK — my recommendation.** Gate the `hydro` limb of
`_backfill_renewables_eia930`'s EIA-930 swap on `not eia930_wat_level_folded(iso, year)`, so a
folded ISO-year keeps its conventional-only EIA-923 `HY` actual — **the same population the LP's
hydro units are, and the same population `hydro_level_923_hy` already moved the model onto.**
* Basis is rule 14 `[R-ACCURATE]` and rule 19 `[R-ONE-MECH]`, **never a residual**: it is a
  construction repair to a comparison whose two sides are different populations, and its
  gate-neutrality (§4) means it cannot be a fit.
* **Zero new parameters, zero new registry, zero new constants** — it reuses a shared predicate
  the owner has already adjudicated three times.
* **Cost, stated at the gate:** a folded ISO-year's hydro actual then rests on EIA-923's
  completeness, so an early-release vintage (2025 everywhere) must fall through to the existing
  carry-forward rather than to a truncated number. That is a real design detail and it is the
  reason this is an escalation, not a patch.
* **Blast radius: PJM + MISO + NEISO bench parts regenerate**, three lanes, ~16 ISO-years.
  Rule 23 `[R-FROZEN-DERIVE]`: the commit cites the construction repair and
  `EIA930_PS_FOLDED_INTO_WAT`, never a residual.

**(b) Compare `model hydro + model PS discharge` against `NG: WAT` in the scorer.** Also
like-for-like, no bench regeneration. **I do not recommend it:** it welds two model classes
together for one ISO's benchmark, it breaks the `storage` class's own comparison, and it makes
a *scorer* carry an *input* asymmetry — rule 19's exact failure mode.

**(c) Leave both and document the seam on the C1 hydro row.** The cheapest and the most honest
of the do-nothing options; it is what this document already achieves. **It leaves a published
number wrong**, so I recommend it only as the fallback if (a)'s 2025-vintage detail is judged
too large for one lane.

**`classify_plant` (§5) is a SEPARATE decision** and should be taken separately: fixing the
short-circuit (`if pm == "PS": return "OTHER"` before the WAT test, per rule 26
`[R-DELETE]` — fix it, do not flag it both ways) moves five ISOs' hydro actuals by
0.05-0.72 TWh/yr and would retire the dead guard. It is *not* needed for (a), and (a) is not
needed for it.

**ESCALATED, NOT EXECUTED.** Both touch shared ISO-agnostic code; rule 25 `[R-ISO-SCOPE]` and
the per-ISO lane convention mean a PJM lane does not make that call.

---

## 8. RULES

* **Rule 29 `[R-SCREEN]` clause 0** — zero-LP phase 0 first, and this card **completed with no
  LP at all**, which was the pre-registered good outcome.
* **Rule 28 `[R-MECH-MATRIX]` (a)** — the `hydro_*` cells were read before anything was
  proposed: `hydro_level_923_hy` **K** (pjm-143, and this finding is its unactioned
  complement), `hydro_budget_nameplate_aware` **I**, `hydro_dispatch_envelope` /
  `hydro_min_flow_floor` / `hydro_ror_split` **U** (all CAISO-derived; rule 28(d) — they enter
  PJM as `U` and none is reached for here), `pumped_storage_cycling_depth` **G**. **No hydro
  dispatch mechanism is proposed: an accounting mismatch cannot be fixed by a dispatch lever,
  and arming one to close a seam-inflated gap would be fitting to a measurement error.**
  Duty (b): no mechanism was tested, so no verdict moves; `hydro_level_923_hy`'s PJM evidence is
  annotated with this measurement.
* **Rule 30(c)** — the training span is untouched and re-verified CALIBRATED.
* **Rule 31 `[R-RETAIN]`** — nothing solved, so nothing to retain. One **pre-existing** PJM
  Class-E parity RED is discharged by `.gitignore` + untracking, never `rm` (§9).
* **Rule 27 `[R-PUSH]`** — no file ≥ 300 lines rewritten; no shared source edited at all.

---

## 9. THE PRE-EXISTING PJM PARITY RED — discharged, and a rule-text discrepancy found

`check_registry_payload_parity` was **already failing on `origin/main`** before this session, on
two bundle dirs: `results/calibration/pjm_d4_4_y2025` (PJM's — mine) and
`results/calibration/nyiso227_rebasis_span` (**NYISO's lane, left untouched and reported**).

`pjm_d4_4_y2025` is a leftover **per-year shard dir** from the pjm-d4-4 promotion. Rule 32(d)
`[R-SHARD]` is explicit that these are kept out of `main` and the composite is what registers;
`results/calibration/pjm_d4_4_A/hourly/` already carries **every** 2025 sidecar the shard dir
duplicates (`class_band_hourly` / `class_hourly` / `reserve_family` / `storage` / `system`), so
nothing is unique to it. The owner ruled on promotion on 2026-09-11 — pjm-d4-4 **is** the keeper
— so rule 31 `[R-RETAIN]` trigger (i) is satisfied.

**Discharged by `git rm -r --cached` + `.gitignore`, never by `rm`** (rule 31's amended clause,
the ercot-255 incident): 8 files leave the commit tree, **the bytes stay on local disk**, and git
history keeps the blobs, so the action is reversible.

**A DISCREPANCY BETWEEN RULE 31'S TEXT AND THE GATE'S CODE, reported rather than worked around.**
Rule 31 states that *"the parity gate (`check_registry_payload_parity.py`) **only ever sees
committed dirs**, so an ignored bundle can sit on local disk indefinitely without turning
anything red."* At HEAD that is **not what the code does**: the sweep is
`for path in sorted(p for p in calib_root.iterdir() if p.is_dir())`
(`check_registry_payload_parity.py:437`) — it reads the **working tree**, not git. The
consequences are worth stating exactly, because they cut both ways:
* **In CI the rule's conclusion holds** — the runner checks out from git, an untracked+gitignored
  dir is simply absent, and the gate passes. Verified: `git ls-files` on the path is now empty and
  `git check-ignore` resolves it to `.gitignore:1941`.
* **Locally it does not** — the gate still reports the dir while the bytes remain, which is
  exactly the state rule 31 tells a lane to leave them in. A lane that obeys rule 31 therefore
  sees a red gate on its own machine and may be tempted into the `rm` rule 31 exists to forbid.

Not fixed here: the gate is shared, ISO-agnostic infrastructure and the fix is a governance
choice (teach the sweep to skip gitignored dirs, or amend rule 31's sentence). **Escalated with
§7.**
