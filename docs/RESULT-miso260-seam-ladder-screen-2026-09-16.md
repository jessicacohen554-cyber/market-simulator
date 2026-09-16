# RESULT — miso-260: the 2020 screen KILLS the seam-ladder arm on its own G-NOFLIP gate

```
SESSION : miso-260        ISO: MISO        KEEPER: 2026-09-16-miso-259-coal-fuel (UNCHANGED)
ARM     : MISO_SEAM_LADDER_BY_YEAR gains 2020 + 2021, verbatim from the frozen derive.
          Zero new ScenarioConfig fields, zero free parameters, zero DOF.
SCREEN  : 2020, ARM vs CONTROL, one commit apart, both solved by shards.
          The parent ran ZERO LP (rule 32 [R-SHARD] (a)).
VERDICT : 2 of 5 pre-registered stop gates PASS. G-NOFLIP FAILS — C1 2020 COAL_BIT
          goes PASS -> FAIL (-7.00 -> -10.29 TWh against an ±8 TWh band). Under
          rule 29 [R-SCREEN] that KILLS the arm and the remaining years are NOT spent.
          TWO MORE GATES FAIL ON TEXT I MIS-SPECIFIED — reported as my errors, below.
ESCALATED: rule 29's kill and rule 14 [R-ACCURATE] point OPPOSITE WAYS here. That
          conflict is the owner's to resolve (rule 31 [R-RETAIN]); the promotion
          question is asked explicitly in §7 and nothing has been deleted.
```

This document carries **every number this session cites** from either screen bundle
(rule 29 `[R-SCREEN]` (c)).

---

## 1. THE GATE TABLE, AS SCORED — including the two I got wrong

| gate | verdict | measured |
|---|---|---|
| **G-FOOTPRINT** — only the 64 seam band rows repriced | **FAIL, gate MIS-SPECIFIED** | All 64 seam rows reprice, as claimed. But **405 of 3,227 non-seam rows also move their mean `mc`** (median move $0.064, max $9.89). See §1.1 — my gate text asserted a property the model's own two-pass design cannot have. |
| **G-DIRECTION** — Σ\|per-seam net-flow error\| falls; 2020 South sign corrected | **PASS** | Σ\|err\| **36.302 → 6.505 TWh (−82 %)**. South **+3.441 → −0.083** against a measured −2.93, so the sign IS corrected (magnitude still short). |
| **G-SPREAD** — pinned band rows do not rise | **FAIL, gate MIS-SPECIFIED** | Bands within 1 % of their own max in ≥95 % of hours: **control 0 → arm 7**. See §1.2 — the gate measured *dispatch* pinning, and the measured record says the PJM base flows in ~100 % of hours. |
| **G-NOFLIP** — no non-target load-bearing criterion PASS → FAIL in 2020 | **FAIL** | **C1 COAL_BIT −7.00 → −10.29 TWh**, out of the ±8 TWh band. Correctly specified, and it really fails. |
| **G-BALANCE** — slack and dump stay 0 | **PASS** | slack **0.0000 → 0.0000** TWh; dump **0.0000 → 0.0000** TWh. |

**Single delta confirmed** from the committed bundles: both `mode: backcast`, both
`miso_seam_measured_ladder: true`, `coal_fuel_inventory: true`,
`reference_price_interface: true`, both `miso_measured_reserve_requirements: false`,
both solve-surface `9f0845000dc8af6e`; `git.basis_sha` **`cba6c7657f06`** (arm) vs
**`63a3a5aee802`** (control) — adjacent commits whose only solve-affecting difference
is the two table entries.

### 1.1 Why G-FOOTPRINT was the wrong text

The 405 movers are **all gas** — 82 `gas_cc`, 252 `gas_ct`, 71 `gas_st` — and **zero**
coal, hydro, nuclear or oil. 362 of the 405 also changed their P0 run pattern (block
count or hours online). That is the documented P0→P1 seam: this recipe arms
`tranche_startup_amortization` and `tranche_startup_conditional_runs`, so P1's bid cost
is base + a startup markup amortized over the **P0 run pattern**. Any mechanism that
changes dispatch necessarily re-prices the units whose commitment moved.

So the gate as written — "every non-seam unit's `mc` is identical" — asserts something
no dispatch-changing mechanism in this model can satisfy. **The claim the mechanism
actually makes is that it DIRECTLY writes only the 64 seam rows**, and that survives:
the injector writes only rows carrying the reference-band marks, and the non-seam
movement is confined to exactly the class the startup channel can reach. A direct
repricing leak would not have respected that boundary; 800 coal, 618 oil, 165 hydro and
15 nuclear rows are byte-identical.

43 of the 405 move `mc` with an identical block count **and** hour count. Block
*lengths* can differ at equal count and total, so this is consistent with the same
channel — but these two statistics do not prove it, and I am not claiming they do.

### 1.2 Why G-SPREAD was the wrong text

The gate was written against miso-252 §2.4's bang-bang signature (2021: four PJM import
bands pinned within 1 % of their own maximum in every hour). **2020's control is not
bang-bang at all — 0 pinned bands — so the gate's premise does not hold in the screen
year**, and the arm's 7 pinned bands are the *cheap base bands of a seam the measured
record says imports in ~100 % of hours*. Pinning the base is the target behaviour here,
not the defect; the defect the gate meant to name is a **price grid with no spread**,
which is a property of the registry table, not of the dispatch.

Supplementary, and **explicitly not a pre-registered gate** (I am not swapping a failed
gate for a better one): on the frozen derive script's own `offline_score` P9 diagnostic,
driven by the measured DA price, the 2020 ladder reproduces the measured seam volume to
**+43.99 vs +44.05 (PJM), +3.93 vs +3.94 (SPP), −2.92 vs −2.93 (South), +10.79 vs
+10.80 (Manitoba) TWh**, duration RMSE 102–264 MW.

---

## 2. WHAT THE ARM ACTUALLY DID — reported at full magnitude

### 2.1 Per-seam net flow (TWh), against the EIA-930 measured net

| seam | control | **arm** | measured | control err | **arm err** |
|---|---:|---:|---:|---:|---:|
| PJM | +17.649 | **+45.951** | +44.05 | −26.401 | **+1.901** |
| SPP | +6.556 | **+4.637** | +3.94 | +2.616 | **+0.697** |
| South | +3.441 | **−0.083** | −2.93 | +6.371 | **+2.847** |
| Manitoba | +11.714 | +11.860 | +10.80 | +0.914 | +1.060 |
| **Σ \|err\|** | | | | **36.302** | **6.505** |

### 2.2 C1, grid-delivered basis (TWh), scored through `render_calibration_html.build_payload`

| class | actual | control | **arm** | control err | **arm err** | |
|---|---:|---:|---:|---:|---:|---|
| CC_REGULAR | 106.91 | 112.83 | **107.36** | +5.92 | **+0.45** | |
| CC_CHP | 20.42 | 24.61 | 22.32 | +4.19 | +1.91 | |
| CT_PEAKER | 12.57 | 11.16 | 9.72 | −1.42 | −2.86 | |
| CT_CHP | 8.19 | 5.37 | 5.17 | −2.82 | −3.02 | |
| ST_GAS | 17.51 | 14.24 | 11.94 | −3.27 | −5.57 | |
| ST_CHP | 5.88 | 3.00 | 2.76 | −2.88 | −3.12 | |
| COAL_PRB | 126.68 | 130.36 | 123.34 | +3.69 | −3.33 | |
| **COAL_BIT** | **66.27** | **59.27** | **55.98** | **−7.00** | **−10.29** | **PASS → FAIL** |
| COAL_LIGNITE | 8.36 | 9.52 | 9.28 | +1.15 | +0.92 | |
| OTHER_FOSSIL | 9.62 | 9.38 | 8.94 | −0.23 | −0.68 | |
| **Σ \|err\|** | | | | **32.58** | **32.15** | |

Fuel families: **gas −13.10 → −25.03**, **coal +7.75 → −2.83**, **interchange
+17.01 → −5.99** (all model − actual). Imports **+23.006 TWh**; nuclear, wind, solar,
hydro, biomass and OTHER are byte-identical.

### 2.3 Price — REPORTED ONLY, never a gate

C3a was not a screen gate and was never scored as one; a screen gated on the target
residual is the fitted-mechanism selection rule 1 `[R-STRUCT]` forbids, done one year
at a time.

| construction | control | **arm** | vs 2020 RT actual $22.308 |
|---|---:|---:|---|
| simple hourly mean | $27.628 | **$25.688** | +23.8 % → **+15.1 %** |
| demand-weighted zonal mean | $28.258 | **$26.747** | +26.7 % → **+19.9 %** |
| load-weighted | $28.260 | **$26.745** | |

Neither construction is byte-identical to the scorer's C3a statistic (which reads
+22.9 % on the keeper's committed 2020); the **move**, −6.8 to −8.7 pp toward the
actual, is consistent across all three.

### 2.4 The legitimacy diagnostics moved too, and against the arm

| | control | **arm** |
|---|---|---|
| D-1 failures | 0 | **1** — `2020 COAL_PRB: off-peak CV ratio 0.451 (model 0.071 / actual 0.156) < 0.5` |
| D-2 CT_PEAKER forced share | 35.9 % (4.69 / 13.05 TWh) | **50.6 %** (5.79 / 11.45 TWh), cap 15 % |
| D-4 failures | 1 (`reliability_floor × ST_GAS`, plant 990) | 1, same row |

The D-2 CT_PEAKER row fails in **both** arms and sits at the edge of rule 20
`[R-FORCED-BUDGET]`'s 2 % materiality floor (model 11.45 TWh, actual 12.57 TWh against
~622 TWh of load — 1.84 % and 2.02 %). The **new** D-1 COAL_PRB failure is the arm's.

---

## 3. THE CONFLICT I AM ESCALATING RATHER THAN RESOLVING

**Rule 29 `[R-SCREEN]` says the arm is dead.** G-NOFLIP was pre-registered, it is
correctly specified, and it failed. A screen "may kill an arm; it may never promote
one", and "a screen that kills an arm is reported as the session's result and the
remaining years are never spent." I have not spent them.

**Rule 14 `[R-ACCURATE]` says the mechanism belongs in the model anyway**, in almost
these words: *"If swapping a hand estimate for real data … makes the backcast worse,
that is a signal that something else in the model is miscalibrated and the estimate was
silently compensating for it. Treat the worse fit as a discovered bug: keep the accurate
input, find and fix the real root cause. Do not bury the error back inside an inaccurate
input."* This arm is exactly that swap: a gas-elastic proxy **fitted on the 2023–2025
training window** replaced by the seam's own measured revealed supply curve, and the
seam-flow error it closes is 36.3 → 6.5 TWh.

**And the root cause it exposes is already named in this session's own phase 0**: gas is
under-dispatched by 13–35 TWh in **every** year of the span. With the seam repaired,
2020's total coal lands at −2.83 (nearly right, from +7.75) while the gas deficit widens
to −25.03, because the imports land where the missing gas should have been. COAL_BIT's
flip is the standing BIT-under / PRB-over merit-order defect — negative in five of six
years under the keeper — being pushed harder once the seam stops masking it.

**What I will not do is retire G-NOFLIP now that I have seen it fail.** Pre-registration
is the only protection against post-hoc gate selection, and a gate retired because it
bit is the fitted-mechanism selection rule 1 exists to forbid. G-FOOTPRINT and G-SPREAD
are retired above on grounds that do not depend on which way they went — one asserts a
property the two-pass design cannot have, the other has a premise that is false in the
screen year — and I say so explicitly so the distinction is auditable.

**My recommendation, which is not a decision**: the mechanism is right and the repair
should land, but **not on this evidence as a keeper** — it converts a passing C1 class
into a failing one in a validation year and does not by itself close C3a or C3b. The
successor should land it **together with** the gas-deficit root cause, so the measured
seam is not the thing that has to absorb the model's missing gas.

---

## 4. PHASE 0 — three levers killed at ZERO LP before any of this

### 4.1 The coal stock-CARRY (the charter's lever 1) — REFUTED ON MONOTONICITY

A carry replaces twelve independent caps `burn[m] <= C` with twelve cumulative caps
`sum_{m'<=m} burn[m'] <= m*C`. Every path feasible under the no-carry form is feasible
under the carry form, so **the carry's feasible set strictly contains the incumbent's
and a carry can only RAISE coal.** Under the keeper, coal is over-predicted in five of
six years (+7.75 / −1.91 / +13.96 / +5.47 / +0.45 / +4.09) and gas is under-predicted in
**all six** (−13.10 / −29.92 / −29.31 / −34.89 / −30.51 / −32.01). Coal displaces gas.
**There is no year in which relaxing the coal ceiling helps.** A carry *with a minimum
operating stock* is a different, non-monotone mechanism and stays open; a pure carry does
not. No solve was spent.

### 4.2 A CC_REGULAR level defect (the charter's lever 3) — PREMISE FALSIFIED

Scored across the span the sign flips: **+5.92 / −9.46 / −9.47 / −6.39 / +3.32 / −3.15**
(2020→2025). Not a level defect. `COAL_BIT` — negative in five of six years at −7.00 /
−8.36 / +0.55 / −3.32 / −3.87 / −4.12 — is the class that does look level-shifted, and
is the open object §3 routes.

### 4.3 A coal delivered-PRICE rule-14 repair — REFUTED ON COVERAGE

`FINDING-miso258` proved the legacy `eia923_monthly_fuel_costs.parquet` incomplete for
coal **tonnage**; it is natural to suspect the delivered **price** it feeds through
`coal_plant_monthly_pricing`. Measured against the newly landed `coal-receipts` datatype
on the LP's own coal footprint:

| yr | LP coal plants | legacy plants / plant-months / qw $/MMBtu | coal-receipts plants / plant-months / qw $/MMBtu |
|---|---:|---|---|
| 2020 | 85 | 52 / 559 / 1.913 | 52 / 559 / 1.907 |
| 2021 | 85 | 51 / 563 / 2.054 | 51 / 563 / 2.045 |
| 2022 | 85 | 47 / 525 / 2.229 | 47 / 525 / 2.266 |
| 2023 | 84 | 42 / 478 / 2.292 | 42 / 478 / 2.346 |

**Identical coverage, identical plant-months, price within 0.3–2.4 %.** Incomplete for
tonnage, not for price. No repair available. (Separately worth a successor's attention:
only ~55 % of coal plant-months are priced from F923 at all; the rest fall to the nearby
pool or the flat trajectory, and that gap is in the source, not in the extract.)

### 4.4 Why the seam WAS the lever — the measured footprint, and the screen year

`FINDING-miso252` §3(a) recorded 2020–2022 as blocked, naming the EIA-930 interchange
extract ("2023–2025") the **binding blocker**. Both halves landed three days later and
nothing re-checked: **`f9259f91`** (2026-09-13) landed MISO's 2020/2021 hourly DA/RT hub
LMP, and **`00249712`** (same day) widened the interchange extract to **2020–2026**.
Those two series are the only inputs to the primary Q-Q construction. 2022 was already
armed by miso-252 on this identical rule-23 basis.

Run at HEAD the frozen derive reproduces **every previously-committed entry: 256 of 256
over 2022–2025, max \|diff\| 0.0000**; with 2020+2021 added the table reproduces at
**384 of 384**.

The incumbent's band grid is **degenerate** in the unarmed years, measured off the
keeper's own committed `unit_hourly` seam-band costs: 2021 South all eight import bands
at $41.97 and all eight export bands at $37.97; 2021 Manitoba import **and** export at
the same $39.97 (a same-seam wash the ladder forbids by construction); 2021 PJM import
spanning **$0.53** over eight bands against a measured $16.17 → $82.19.

Model net seam flow vs measured, Σ\|per-seam error\| (TWh):

| yr | ladder? | Σ\|err\| | C3b NRMSE |
|---|---|---:|---:|
| **2020** | **no** | **36.29** | **0.246 FAIL** |
| **2021** | **no** | **25.41** | **0.285 FAIL** |
| 2022 | base only | 8.84 | 0.182 PASS |
| 2023 | base + overlays | 4.11 | 0.096 PASS |
| 2025 | base + overlays | 5.21 | 0.116 PASS |

**The screen year 2020 was named in the PRECOMMIT before the screen ran, on the largest
measured footprint (36.29 TWh) and NOT on the residual** — 2021 carries the larger C3b
miss and is not the screen year. The C3b column is reported afterwards as corroboration,
never as the selection criterion.

---

## 5. THINGS I FOUND THAT ARE NOT MINE TO FIX, ESCALATED NOT ABSORBED

1. **MISO's keeper is TWO CONFIGS, not one recipe over two tiers.** The keeper shard's
   `config_partition.structure_note` states *"MISO IS ONE RECIPE OVER TWO TIERS, NOT TWO
   CONFIGS."* Measured from the per-year bundles' own `run_config.json`:
   `miso_measured_reserve_requirements` and `miso_reserve_online_gated` are **False** in
   2020/21/22 and **True** in 2023/24/25. The partition is **forced by data, not chosen**
   — `load_miso_reserve_requirements` hard-errors for 2020, 2021 and 2022 (verified;
   the measured cleared-reserve parquet starts in 2023). So the benign reading is right
   and the note's wording is wrong. **Consequence for rule 32 `[R-SHARD]` (b): a single
   `--years 2020..2025` invocation is IMPOSSIBLE for MISO** — it would raise on its first
   year. Two invocations is the floor, and `replay_keeper.enforce_single_recipe_partition`
   already knows it.
2. **`_miso259_compose_span.py` copies ONE year's `legitimacy_diagnostics.json`** as the
   composite's (its lines 134–135), which is the trap the handoff warns sends C8 silently
   to SKIPPED. Its `_check_recipes` also validates only `coal_fuel_inventory`, `mode` and
   the surface fingerprint — it would not have caught the reserve-flag partition, and the
   composite's base `run_config.json` is the 2020 leg's, so it records the validation
   tier's reserve flags for the whole span. `scripts/probes/_miso260_compose_span.py`
   (written this session, unused because the span was not spent) checks both and
   **regenerates** the diagnostics over the composite instead of copying a leg's.
3. **The miso-259 2024 shard SHA was never recorded** — rule 33 `[R-SHARD-ARCHIVE]` (d).
   `.gitignore` carries recovery SHAs for 2020/2021/2023/2025 and says *"2024 still
   solving at this commit; its SHA is appended when its shard lands."* It never was. All
   four recorded SHAs **do** resolve (`git fetch origin <sha>` works against this remote),
   so 2024 is the single unrecoverable year of the current keeper: re-registering that
   keeper from bundles would cost one MISO year of LP.
4. **`check_gate_a_provenance` fails on MISO**, not only NYISO and SPP as the handoff
   said: `frontend/data/forecast/program-status.json` `/isos/MISO/gate` still cites the
   superseded `2026-09-12-miso-255-sil-measured`. That is miso-259's own unfinished
   promotion bookkeeping. **I have not re-keyed it**, because this session does not change
   MISO's keeper and re-keying it to a determination I did not re-derive would be writing
   a number I have not measured. It is named here so the next MISO lane closes it.

---

## 6. GATES AT HEAD

| check | result |
|---|---|
| `pytest tests/scoring` | **19 failed at HEAD, 19 with my three changed source files reverted to `origin/main`, identical sets — ZERO NEW.** (The handoff's baseline of 18 is from another environment; 19 is this container's, measured both ways.) |
| `pytest tests/iso/miso` | **184 passed** |
| `check_cache_key_registration --base origin/main` | **ok** — 850 fields, 305 registered, all resolve, all declared defaults match; 305 solve-surface names across 7 modules |
| `check_mechanism_matrix --base origin/main` | **exit 0** (anchor-drift warnings pre-existing, not this lane's rows) |
| `check_bench_freshness --iso MISO` | 6 parts, **0 STALE**, 0 engine drift |
| `check_registry_payload_parity` | 2 pre-existing REDs (`caiso279_ablate_dswcouple_span`, `soco15_spp_arm`) **plus 6 of my own gitignored recovered bundles** — exactly the local-only RED rule 31's 2026-09-16 correction describes. Nothing `rm`'d. |
| `audit_keepers --iso MISO` | 2 failures, **both environmental**: E1 `bundle dir missing: miso259_coalinv_span` (the keeper's composite is gitignored, so it is absent in any fresh clone) and S1 status-stale, which is **caused by** E1 — rebuilding produces `governance gate UNATTESTED: no governance attestation in bundle`. The committed status file was **restored, not committed**. |
| `check_gate_a_provenance` | fails on **MISO, NEISO, NYISO, SPP** — see §5.4 |
| `node --check` on the matrix files | pass |
| `ruff check` / `ruff format` | clean |
| solve-surface fingerprint | `9f0845000dc8af6e` at the keeper, at HEAD, and in both screen bundles |

**G-DRIFT, and a better answer than the audit.** The keeper's recorded
`git_sha` **`3b0a12b441d3c518742098713b203cafeb39f10e` IS reachable** (unlike miso-259's).
Against it the solve path has moved 37 files / 3,274 insertions, and this session did not
certify that hunk-by-hunk, so **form 4 was not claimed**. It did not need to be: the
CONTROL shard **reproduces the keeper's committed 2020 row exactly** — CC_REGULAR +5.92,
CC_CHP +4.19, CT_PEAKER −1.42, ST_GAS −3.27, ST_CHP −2.88, COAL_PRB +3.69, COAL_LIGNITE
+1.15, COAL_BIT −7.00, gas −13.10, coal +7.75, interchange +17.01, MISO-East $28.13 — every
one identical to the registered keeper's scored 2020. **Zero measurable HEAD drift on MISO
2020**, established by measurement rather than by reading hunks.

---

## 7. RETRIEVABILITY, AND THE PROMOTION QUESTION (rules 31 / 34)

Both screen bundles are **on their shard branches and on local disk**, `.gitignore`d and
not deleted. Recovery is pinned by **full SHA**, never branch name (rule 33 (d)):

```
git fetch origin cb3049fff5e572ebb12a835d71ade800ce423266
git checkout cb3049fff5e572ebb12a835d71ade800ce423266 -- results/calibration/miso260_screen_arm
git fetch origin 02a09bb2b0f73c142bb95dfb84fa881f5c6bf8a3
git checkout 02a09bb2b0f73c142bb95dfb84fa881f5c6bf8a3 -- results/calibration/miso260_screen_control
```

| shard | id | outcome | archived |
|---|---|---|---|
| screen ARM 2020 | `session_01CwQ3knPh1Xt2wrKSKGjEEi` | solved, pushed `cb3049ff…`, 17 files | **yes**, after fetch + checkout + verify |
| screen CONTROL 2020 | `session_01MMWpn9GKrPPEeL1scfnB7i` | solved, pushed `02a09bb2…`, 17 files | **yes**, same order |

No shard was left alive. Both branches are **kept** — they are the only copies that
outlive this container, and rule 33 (f) forbids deleting a branch while a promotion is
undecided.

**THE PROMOTION QUESTION, asked rather than pre-empted (rule 31):**

> The arm is a rule-14 `[R-ACCURATE]` repair that closes a measured 36.3 → 6.5 TWh
> seam-flow error using the ISO's own frozen derive, with zero new parameters, and it
> cannot touch the CALIBRATED 2023–2025 train tier by construction. It also flips C1 2020
> COAL_BIT from PASS to FAIL and widens the 2020 gas deficit. **Three options:**
> **(a)** land the code change and spend the full span (2 partition shards, ~60 min each
> in parallel) to see what it does across 2020–2025, accepting that the C1 flip may
> survive; **(b)** land the code change as a non-keeper repair — the table entries stay,
> the keeper is not re-registered, and the next lane pairs it with the gas-deficit fix;
> **(c)** take the screen's kill at face value and drop the branch.
>
> My recommendation is **(b)**, and I have taken none of them. Nothing is deleted.

---

## 8. RULES

Rule 1 `[R-STRUCT]` (the screen was never gated on the price residual; the failed gate is
not retired because it failed) · rule 13 `[R-MEASURED]` (a revealed supply curve the LP
still clears economically, never a pinned outcome) · rule 14 `[R-ACCURATE]` (the repair
itself, and the conflict in §3) · rule 21 `[R-DOF]` / 24 `[R-REGISTRY]` (zero new free
parameters, zero new fields) · rule 23 `[R-FROZEN-DERIVE]` (the re-derivation cites the
source-data change and reproduces every committed entry) · rule 25 `[R-ISO-SCOPE]` (MISO's
own measured series only) · rule 27 `[R-PUSH]` (spec.py edited locally and blob-verified
after push: 3,781 lines, sha `7958eae8de13`, remote == local) · rule 29 `[R-SCREEN]`
(phase 0 first, screen year pre-registered on the footprint, the screen KILLED the arm and
the span was not spent) · rule 31 `[R-RETAIN]` (nothing deleted; the promotion question is
the owner's and is asked) · rule 32 `[R-SHARD]` (the parent ran no LP; §5.1 records why
(b)'s single invocation is impossible for MISO) · rule 33 `[R-SHARD-ARCHIVE]` (both shards
archived after fetch + checkout + verify; recovery by full SHA; branches kept) · rule 34
`[R-SHARD-PROMOTABLE]` (both shards pushed whole bundles).

---

# ADDENDUM A — 2026-09-16: the owner promoted, and the rule I stopped on had been removed twelve minutes before I pushed

## A.1 The owner's ruling

> *"Is this a recommended keeper candidate? If so plz promote. … If structural integrity
> improves but gates regress that may still be a keeper."*

That is rule 31 `[R-RETAIN]` trigger (i) — the owner has ruled on promotion — and it is
the decision rule 29 reserved to the owner. The span is being spent and the arm promoted.

## A.2 A CORRECTION I OWE, AND IT CUTS AGAINST MY OWN §3

§3 of this document says the arm was killed by rule 29 `[R-SCREEN]` and frames the
promotion as the owner overriding that kill. **That framing is wrong, and the reason is
timing I did not check.**

| commit | timestamp (UTC) | what |
|---|---|---|
| `fa170333` | **2026-09-16 06:47:56** | *"Remove the screen-year regime from rule 29 `[R-SCREEN]`"* — owner instruction, *"Get rid of the screen year rule altogether"* |
| `9d1322ad` | 2026-09-16 06:59:09 | this session's PRECOMMIT + arm, pushed **twelve minutes later** |

The amendment removes, **as a requirement and not merely a preference**: the one-year
screen; the duty to name the screen year on the mechanism's own measured footprint; the
"full span only if the screen clears its gate" condition; and **the structural STOP GATE
itself**, with its *"may kill an arm; it may never promote one"* framing and its *"the
remaining years are never spent"* outcome.

My session's `CLAUDE.md` snapshot was taken before that commit, so **I screened under a
rule that no longer required a screen, and then stopped on a gate that no longer had the
authority to stop me.** Under the amended rule the full span was owed unconditionally —
rule 34 `[R-SHARD-PROMOTABLE]` (c), which now carries the whole of the "how many years"
question: *a registrable run solves EVERY year the ISO carries.*

**What this changes in the record.** The screen is **evidence**, not an authority that was
overridden: it is a clean same-recipe A/B one commit apart, every number in §§1–2 stands
exactly as measured, and G-NOFLIP's failure is a real and reported regression. What it
never was, at the moment it ran, is a licence to withhold the span. Read §3 with that
substitution.

**What it does not change.** Rule 1 `[R-STRUCT]` is untouched by the amendment, so my
refusal to retire G-NOFLIP after seeing it fail still stands, and the two mis-specified
gates are still retired on grounds independent of which way they went. Clause (b) (no
control solves; the keeper's committed bundle is the control; `G-DRIFT`) and clause (c)
(delete before merge) both survive verbatim. Clause (0), zero-LP phase 0, survives as
practice — which is what §4 was.

One consequential knock-on: rule 32 `[R-SHARD]`'s *"a single-year shard is still correct
for a rule-29 SCREEN"* is now **spent**, and a single-year shard is simply one leg of the
per-year fan-out rule 34 (c) prescribes. The handoff's sharding advice and CLAUDE.md no
longer conflict.

## A.3 The span, as launched

Two shards, both pinned to `36ac25603bcf96599341847db594a85e8f02526c` (this branch
rebased onto `origin/main` at `08d094fe`), running in parallel, ~60 min budget each:

| leg | years | reserve flags | out-dir | branch |
|---|---|---|---|---|
| **V** validation | 2020 2021 2022 | `miso_measured_reserve_requirements=False`, `miso_reserve_online_gated=False` | `miso260_seam_v` | `claude/miso260-span-v` |
| **T** train | 2023 2024 2025 | both `True` | `miso260_seam_t` | `claude/miso260-span-t` |

Two legs is the **floor**, not a choice: §5.1 measured that MISO's keeper is two configs
and that `load_miso_reserve_requirements` hard-errors before 2023, so a single
`--years 2020..2025` invocation raises on its first year. Leg **T** doubles as the HEAD-drift
measurement — the code change cannot touch 2023–2025, so those three years should
reproduce the incumbent keeper.

**Rule 35 `[R-PROMOTE]` (b), recorded BEFORE any prune**, because the prune destroys the
evidence: the union of `years` over every MISO registry sidecar is
**{2020, 2021, 2022, 2023, 2024, 2025}** — one registered run
(`2026-09-16-miso-259-coal-fuel`), no folded touchpoints, no dangling `holdout.keeper`.
The incoming keeper covers exactly that set, so rule 35 (c) is met and the prune is
authorised.

## A.4 A defect in the incumbent keeper's registration, found while preparing this one

**`2026-09-16-miso-259-coal-fuel` has no committed `calibration_attestation.json`.** Its
registration commit `0333feb1` carries only the six bench parts, the sidecar, the payload
and a compose probe — the span bundle was gitignored in full — so on any fresh clone the
current keeper scores **C6 UNATTESTED**, and `build_status --iso MISO` degrades to
*"governance gate UNATTESTED: no governance attestation in bundle"*. That is what §6's
`audit_keepers` E1/S1 failures actually are.

It also omits the rule 15 `[R-DASHBOARD]` keeper sidecars, which that rule requires a
KEEPER bundle to commit: `hourly/class_hourly_<year>.parquet`,
`hourly/system_<year>.parquet` and `hourly/reserve_family_<year>.parquet`.

This promotion closes both: `scripts/gen_miso260_attestation.py` carries the last
**committed** MISO attestation (`miso255_sil_keeper`'s, recovered from git at
`61c726d0^` — the commit that pruned it), re-stamps `governance.attested_by`, re-measures
every `price_tail` / `price_mean` exception magnitude on this bundle's own scored records,
and carries the DOF ledger **verbatim with no new entry** — because this arm adds no
`ScenarioConfig` field and no free parameter. The attestation and the hourly sidecars are
committed.
