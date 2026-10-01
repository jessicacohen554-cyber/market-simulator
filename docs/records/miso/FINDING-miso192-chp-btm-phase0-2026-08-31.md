# FINDING — miso-192: the D-4 posture sitting found the exhaustion premise OVERSTATED, and the chartered `chp_btm_measured` successor is REFUTED at its own pre-frozen coverage line

**Session:** miso-192, 2026-08-31, branch `claude/miso-192-d4-posture-6p2jp7`.
**Keeper at entry and at exit:** `2026-08-30-miso-191-bexit` (bundle
`results/calibration/miso191_bax_B`) — **UNCHANGED. Nothing promoted, nothing armed.**
**No LP was solved.** No run is registered (rule 15 binds runs; the miso-156 /
miso-189 no-solve precedent).

---

## 1. Ask A — zero-solve validation (reproduced EXACTLY)

`python3 scripts/calibration_verdict.py --run-id 2026-08-30-miso-191-bexit` →
**NOT-YET at rubric v3.5**, basis *"undocumented out-of-tolerance (FAIL)
criteria: price_mean"*, on **{C3a-2025} ALONE**.

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| C3a model $/MWh | 32.88 | 30.83 | 39.85 |
| C3a actual (RT, load-wtd) | 32.85 | 32.30 | 45.46 |
| C3a | +0.1% PASS | −4.6% PASS | **−12.3% FAIL** |

C1 16/16 all / 12/12 free · C2/C3b/C4 PASS · C3c the single ledgered caveat
(1/1) · C6 attested · C8 PASS with the two grounded-above-budget notes (2023
CT_PEAKER 15.6%, 2025 ST_GAS 34.2%) · DOF ledger **37/2**
(`offer_curve_by_group`, `offer_curve_smoothing`). Supporting checks all clean:
`audit_keepers --iso MISO` PASS 0/0; `build_status --iso MISO --check` in sync;
`check_mechanism_matrix.py` integrity OK. MISO absent from both `complete` and
`final`; freeze ACTIVE. **Distance to band: $1.06/MWh = +2.34 pp.**

Re-verified unchanged after rebasing onto a HEAD that had moved 12 commits.

---

## 2. THE HEADLINE, AND IT IS AGAINST THE LANE'S OWN STANDING RECORD

The owner declined to rule on D-4 posture and asked instead: *"Can you really
identify no other options to test? How far off are we?"* The census that
question forced turned up **two corrections to the lane's standing record**.

### 2.1 The lever queue is empty; the MATRIX IS NOT. Exhaustion was overstated.

miso-189 §8 and miso-191 §7 state the queue is empty "of named candidates at
every grain", and the miso-192 handoff carried that forward as *"the lane's
mechanism queue is EMPTY at every grain"*. That is true of the **curated lever
queue** in `docs/mechanism-testing-matrix.md` §5.4. It is **NOT** true of
MISO's shard, which is the rule-28(a) instrument a session is required to
check. Census of `docs/codebase-site/data/mechanism-matrix/MISO.js`:

| verdict | cells |
|---|---:|
| K keeper | 68 |
| U untested | **40** |
| R rejected | 14 |
| I inert | 13 |
| G governance-refused | 7 |
| O open | **5** |
| · n/a | 103 |
| **total** | **250** |

Of the 45 `U`/`O` cells, **13 are forecast-lane** (`mode: F`) and irrelevant to
a backcast C3a; **32 are backcast-touching** (9 `B`, 23 `BF`). Several are
**keeper-armed in another ISO and never examined here** — live transfer
candidates under rule 28(d), which is exactly the state that rule contemplates:

| mechanism | ERCOT | CAISO | PJM | **MISO** | NYISO | NEISO |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| `chp_btm_measured` | U | U | U | **U** | **K** | U |
| `cc_duct_peaking` | U | U | U | **U** | **K** | U |
| `egrid_identity_heat_rates` | U | U | U | **U** | **K** | U |
| `gas_st_startup_spread` | U | U | U | **U** | **K** | U |
| `gas_coldsnap_derate` | U | · | · | **U** | · | **K** |
| `winter_fuelsec_posture` | U | · | · | **U** | · | **K** |
| `tac_load_coverage` | U | **K** | U | **U** | U | U |
| `lcr_tsl_published` | · | **K** | U | **U** | **K** | · |

**This does not reopen any adjudicated cell** — every `R`/`I`/`G` verdict in
the offer, ORDC, seam, South-export and fuel families stands untouched, and the
DO-NOT-REDO discipline is unbroken. What it corrects is the *claim of
exhaustion*: the lane is at the frontier of its **named** objects, not of its
**testable** ones. Any future D-4 filing must say so, because a
`kind: "model-class"` ledger entry is admissible under rubric v3.0 only when it
**cites exhaustion of the within-class mechanism space** — a citation this
census would contradict.

### 2.2 The offer family IS genuinely exhausted — for a reason worth recording

Four of the ERCOT-`K` offer cells (`coal_perplant_offer_level`,
`coal_peak_offer_margin`, `coal_offer_net_revenue_margin`,
`cc_committed_offer_margin`) initially read as untested transfer candidates.
They are **structurally blocked for MISO** and should not be chartered: MISO's
offer corpus publishes **masked unit identity with no fuel or technology
attribute**, and the offer-side class bridge was **built and REFUTED at
miso-138** (`data/raw/miso-energy-offers/README.md`). ERCOT's constructions are
per-plant/per-class by design and cannot be formed on a masked book. This is
precisely why miso-178 §7 forced the *distributional, rank-mapped* form — and
that form is what miso-179 (`R`) and miso-180 (`I`) adjudicated. **The offer
family's exhaustion is real and is now recorded with its cause.**

---

## 3. THE RULE-14 CHARTER THE OWNER FIRST RULED — WITHDRAWN, ALREADY REPAIRED

The owner's first ruling was to charter the **miso-141 summer-derate double
count** as a rule-14 accuracy repair, accepting that C3a-2025 would worsen.
**That premise does not hold, and the error was mine.**

`summer_derate_basis_aware` was built at **miso-148** and is the exact successor
miso-141 §11.2 specified: class-agnostic across all four flat-derate classes, a
pure basis swap with **zero continuous DOF**, `plant_level_fleet`-gated so
ERCOT's nameplate-basis CAMPD-bin path correctly keeps the derate, and
corrupt-filing plants handled explicitly by *keeping* them on the flat derate.
It is **armed on the live keeper** (`summer_derate_basis_aware=True`,
`plant_level_fleet=True`; the suppression set resolves live), and its matrix
cell is `K`.

**The adverse cost has already been paid, and the current −12.34% is
post-repair.** miso-148 measured it: the summer availability hole closed
(Jun–Sep 2025 `AV_CC − A_CC` **−2,296/−2,451/−2,157/−1,560 → −373/−369/−77/+419
MW**) and C3a worsened in every year (**−0.49/−6.01/−14.15 →
−1.98/−8.03/−15.58**), exactly as its PREREG predicted at 0.75 confidence.

**How the error happened, stated plainly:** I read the `cc_nameplate_summer_derate:
U` cell together with miso-141's "refused as insufficient" note, and did not
cross-read the shard's own `summer_derate_basis_aware: K` cell, which records
the repair. The miso-141 note is accurate about *that flag*; it is not the whole
record of *that defect*.

Two adjacent possibilities were checked so the answer is complete rather than a
bare retraction:

* **No coal analogue exists.** `SUMMER_CLASS_DERATE` =
  `{CC_REGULAR 0.10, CC_CHP 0.10, CT_PEAKER 0.125, CT_CHP 0.125}` — no coal
  member, so there is no coal double count. `coal_nameplate_summer_derate`
  (`K`@ERCOT) is a different mechanism.
* **`unit_outage_lp_capacity_basis` (`K`@CAISO) is inert for MISO by
  construction.** It repairs the denominator `fleet_to_bins` raises *under*
  `cc_nameplate_summer_derate` — a flag MISO does not run. Arming it here would
  *introduce* a basis mismatch, not fix one. Its `U` is correct.

**The rule-14 summer-basis family is CONFIRMED CLOSED for MISO.**

---

## 4. THE CHARTERED OBJECT — `chp_btm_measured`, REFUTED ZERO-SOLVE

On the corrected picture the owner chartered `chp_btm_measured`: a
measured-input accuracy item, keeper-proven at NYISO, and right-signed for C3a
(more CHP behind the meter ⇒ more grid load the modelled fleet must serve).

### 4.1 The rule, frozen BEFORE any adjudicating quantity

Committed at **`1892bb7`** and pushed **before** the measurement was computed
(the miso-189/191 discipline), in the docstring of
`scripts/probes/_miso192_chp_btm_phase0.py`:

> **CANDIDATE** iff a per-plant, EIA-923-independent grid-delivered energy
> series exists covering **≥ 50 %** of MISO CHP nameplate (CC_CHP + ST_CHP +
> CT_CHP). The 50 % line is taken from miso-141 §11.2, which refused a
> **52 %**-coverage repair as insufficient. Otherwise **REFUSE**.

### 4.2 The identification actually available to MISO

NYISO's numerator is the **Gold Book** Table III-2a per-station net energy.
MISO publishes no equivalent — `data/raw/MISO/` is Potomac IMM/SOM PDFs, and
MISO's market reports are masked. **Rule 25/28(d): NYISO's values transfer
nothing**, and MISO's own shard note says so explicitly.

But the repo already carries an **ISO-agnostic** second construction, the
curated `chp-btm-share` datatype (`scripts/data/curate_chp_btm_share.py`):

```
btm_share = (eia923_net_mwh − campd_net_mwh) / eia923_net_mwh
```

over **CEMS units that report steam load** (`steam_load_klbh_sum > 0`). Both
meters are measured, per-plant, and model-independent — rule-13 clean.

> **AMENDMENT TO THE FROZEN RULE, DISCLOSED NOT APPLIED SILENTLY.** The rule as
> written also required the numerator to be *"published by MISO or a
> MISO-designated body"*. That clause was written around the Gold Book and is
> **over-narrow**: EPA CAMPD satisfies the rule's substance (two independent
> per-plant meters) while failing its letter. The amendment is recorded here
> and in the probe's committed JSON. It is **against the lane's interest** —
> the narrow reading would have refused the object immediately at §4.2; the
> amended reading gave it its best chance and it was refuted on the numbers.

### 4.3 The measurement — REFUSE at 5.81 % against a 50 % line

Curating the datatype for MISO writes 19 rows. Joined onto the fleet's own
(plant, group) keys:

| class | fleet plants | fleet MW | covered plants | covered MW |
|---|---:|---:|---:|---:|
| CC_CHP | 24 | 7,036.4 | **0** | **0.0** |
| CT_CHP | 52 | 2,625.5 | **0** | **0.0** |
| ST_CHP | 55 | 1,935.4 | 7 | 673.3 |
| **total** | **113 plants / 131 rows** | **11,597.3** | **7** | **673.3** |

**Coverage = 673.3 / 11,597.3 = 5.81 %**, against the frozen 50 % line.
**The two gas CHP classes holding 83 % of the MW have ZERO coverage.**

### 4.4 WHY — the diagnostic that rules out a join failure (miso-191 lesson)

Two structural gaps, neither a pipeline defect:

| class | fleet plants | present in CAMPD | reporting steam load |
|---|---:|---:|---:|
| CC_CHP | 20 | 13 | **1** |
| ST_CHP | 55 | 10 | 7 |
| CT_CHP | 38 | 5 | 3 |
| **total** | **113** | **28 (25 %)** | **11** |

1. **75 % of MISO's CHP fleet is absent from CAMPD entirely** — small /
   non-Part-75 cogens carrying no CEMS obligation.
2. Of the 28 present, only **11** report steam load, the CHP signature the
   construction keys on. **MISO's CC_CHP class — 7,036 MW, its largest — has
   exactly ONE steam-load-reporting plant.**

The construction is sound; MISO's measured record cannot identify it at
material coverage. **Cell `chp_btm_measured` MISO `U` → `R`**, on the miso-179
precedent (refuted at its own pre-registered no-LP pre-check, no field ever
created, no solve spent).

> **A gap in my own frozen rule, reported rather than resolved silently.** The
> rule enumerated two refuse sub-cases — (a) no second meter, (b) aggregate
> only — both minting `G`. The actual outcome is a **third** case it did not
> anticipate: a per-plant meter exists but covers 5.81 %. I mint **`R`** on the
> miso-179 precedent (a pre-check refutation is `R`), not `G`, and record that
> the choice was mine rather than pre-registered.

### 4.5 What the refusal LEAVES IN PLACE, stated against interest

MISO's CHP BTM share stays on `CHP_BTM_PCT_BY_SECTOR` — and
`thermal_tranches_MISO.csv` carries **no `chp_btm_pct` column at all**, so
every one of MISO's 113 CHP plants is on the sector default. The `"merchant"`
value of **35.0 %** is **self-declared residual-identified** in its own source
comment (*"no independent source yet"*). **This refusal therefore leaves a known
rule-13 weakness standing in MISO's fleet.** It is named here rather than
papered over with an invented number, and it is the honest cost of refusing:
the alternative — apportioning an aggregate wedge across plants — is forbidden
by rule 24 and the miso-176 K-2 apportionment precedent.

---

## 5. Lane state after this session

Keeper `2026-08-30-miso-191-bexit` UNCHANGED; determination NOT-YET on
{C3a-2025 −12.34 %} alone; C3a is $1.06/MWh (+2.34 pp) outside band.

**The D-4 posture question is STILL THE OWNER'S and is now better posed.** The
census changes what a posture ruling would be resting on:

* Option **(i)** (ledger C3a-2025 as a model-class limitation) needs **three**
  rubric amendments, not one — `LEDGERABLE_CRITERIA` (v3.1, C3c-only, checked
  FIRST and written *specifically* about C3a), the v3.0 SUPPORTING-tier guard,
  and `MAX_LEDGERED_CAVEATS` 1→2 (C3c already fills the budget, and the budget
  branch fires *before* v3.3's non-downgrading branch). Amending fewer than all
  three leaves the run NOT-YET with a different reason line. It is also now
  **harder to justify**: the v3.0 form requires citing exhaustion of the
  within-class mechanism space, which §2.1 contradicts, and miso-178 §3 measured
  the target as sitting **inside deterministic reach** (the DA→RT wedge is
  **+1.98 pp, net positive for the model**; the deterministic-LP ceiling for
  2025 is **+1.96 %**).
* Option **(ii)** (rest NOT-YET) remains available but is a **budget** decision
  with candidates on the table, not a frontier.
* Option **(iii)** now has **named** objects rather than none — §2.1's table.

**Standing OWNER items, restated not decided:** (1) the C8 provenance-materiality
floor; (2) committed-vs-regenerated diagnostics exposure; (3) `RHO_CLIP`
cross-ISO band; (4) **D-4 posture**; (5) the miso-189 §7.3 marginal-vs-average
delivered-cost residue (adverse sign, cross-ISO).

**Next candidates, if the lane continues** (all `U`, all keeper-proven
elsewhere, none chartered here): `gas_coldsnap_derate` + `winter_fuelsec_posture`
(`K`@NEISO — aimed at miso-178's named Jan-2025 −1.43 pp), `cc_duct_peaking` and
`egrid_identity_heat_rates` (`K`@NYISO), `tac_load_coverage` (`K`@CAISO).

---

## 6. Governance

**Rule 22 `[R-HOLDOUT]`** — 2023/2024/2025 only; MISO holds neither marker; the
spend freeze untouched; no out-of-training year read, solved, scored or
registered. The `chp-btm-share` curation pools only non-quarantined vintages
(2022/2026 excluded by the script itself).
**Rule 15 `[R-DASHBOARD]`** — no LP solved, so no run is owed (miso-156/189
precedent). Keeper unchanged.
**Rules 1/13/14** — the candidate was tested against the measured record and
refuted on a rule frozen before the measurement; no input changed, no parameter
fitted, nothing tuned to a residual. The rule-14 item of §3 was withdrawn on
evidence, not on convenience.
**Rule 19 `[R-ONE-MECH]`** — nothing stacked; the summer-capability treatments
were enumerated and reconciled (§3), not added to.
**Rule 24 `[R-REGISTRY]`** — no new `ScenarioConfig` field was minted, so 28(c)
does not fire. The aggregate-apportionment route was refused, not invented.
**Rule 25 `[R-ISO-SCOPE]`** — only MISO's shard/docs touched; NYISO's Gold Book
values transferred nothing; no other ISO's cell moved.
**Rule 28 `[R-MECH-MATRIX]`** — (a) the lever came from the shard census, and
this finding records that the census, not the curated queue, is the instrument
rule 28(a) names; (b) `chp_btm_measured` MISO `U` → `R` stamped in-session with
its citation, a **rejected** outcome recorded as the rule requires; (d) no
verdict transferred to or from another ISO.
**Rule 27 `[R-PUSH]`** — exact on-disk bytes; every pushed blob ≥300 lines
verified.
No `.github/workflows` change. **THE OWNER MERGES; no PR opened.**

---

## 7. Reproduction

```
python3 scripts/calibration_verdict.py --run-id 2026-08-30-miso-191-bexit
PYTHONPATH=.:src python3 scripts/data/curate_chp_btm_share.py --isos MISO
PYTHONPATH=.:src python3 scripts/probes/_miso192_chp_btm_phase0.py
```

Reads the committed `miso191_bax_B` bundle, `data/raw/_processed-legacy/`
(`plant_emission_rates_v2.parquet`, `eia923_monthly_generation.parquet`,
`thermal_tranches_MISO.csv`), the EIA-860 fleet, and
`docs/codebase-site/data/mechanism-matrix/*.js`. Record:
`results/calibration/_miso192_chp_btm_phase0.json`.
