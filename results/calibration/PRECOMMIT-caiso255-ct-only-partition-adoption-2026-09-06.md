# PRECOMMIT — caiso-255: the owner grants FINDING-caiso254 §4 **OPTION 1**. Adopt the CT-side de-contamination ALONE; the G4-failing ST_GAS bucket is MEASURED, REPORTED and REFUSED CONSUMPTION. No gate is relaxed, no threshold is retuned, and the direction of the band move is pre-registered as UNUSABLE evidence.

**Session caiso-255, 2026-09-06.** Branch
`claude/caiso-255-backcast-calibration-272jxd` off `main` `173d0a78`.
Keeper **`2026-09-05-caiso-252-b1-notrim`** (`caiso252_b1_notrim`, `git_sha`
`fa23c1f7`) UNCHANGED at the time of writing, DETERMINATION **CALIBRATED**.
Rule 22 `[R-HOLDOUT]`: **2023–2025 only**; CAISO holds no `complete`/`final`
marker; the holdout spend freeze is ACTIVE.

**Pushed BEFORE the corpus finishes downloading, before the derive is edited,
and before any statistic of this session's bid population exists.** The corpus
re-fetch was started first because rule 22's own clause makes data intake
unrestricted ("what is held out is the SCORE, never the DATA"); it produces no
measurement.

---

## §0 — THE GRANT, AND EXACTLY WHAT IT AUTHORIZES

caiso-254 measured the class-partition repair and the derive's own **G4
physical-sanity** gate refused it: the separated `ST_GAS` bucket's `peak`
(1.196) sits **0.350 below** its `econ_high` (1.546) against a 0.05 flatness
tolerance. Nothing was written. Three options went to the owner
(`FINDING-caiso254-partition-repair-2026-09-06.md` §4).

**The owner grants OPTION 1, 2026-09-06: adopt the CT-side repair only —
write CC + CT, omit the G4-failing ST_GAS bucket.**

This document is the pre-registration FINDING §4 requires ("if taken it must be
pre-registered before the artifact is written, not adopted here"), and it is
written **before** the derive is touched. What the grant does **not**
authorize, stated so it cannot drift:

* it does **not** relax G4, its 0.05 tolerance, or any other gate;
* it does **not** retune `hr_cut`, the antimode locator, the estimator, the
  body probe, the gas gates, the statistic, the VOM or the band geometry;
* it does **not** license per-year multipliers (rule 13; caiso-229 §10.2);
* it does **not** decide the keeper. Promotion is decided at the end, on the
  basis registered in §5 below, and C3a/C4 enter it in **neither** direction.

---

## §1 — THE OBJECT: what is written, what is omitted, what is still measured

The repair is the three-way class partition caiso-254 built and G-BIMODAL
admitted (antimode **11.738** MMBtu/MWh inside the pre-registered
[10.9, 12.5], **2.559 GW** above it inside [1.5, 4.5] GW). Option 1 changes
only **which buckets are consumed**:

| bucket | classified | gated | **consumed** | why |
|---|:--:|:--:|:--:|---|
| `CC_REGULAR` | ✔ | ✔ G1/G2/G3/G4 | **YES** | passes every gate; caiso-254 measured it unchanged to the digit (1.066 / 1.072 / 1.386) |
| `CT_PEAKER` | ✔ | ✔ G1/G2/G3/G4 | **YES** | passes every gate; this is the whole model-visible effect |
| `ST_GAS` | ✔ | measured & **REPORTED** | **NO** | G4 FAILS (peak inverted 0.350 below econ_high). Refused consumption, not hidden |

**The de-contamination happens in the CLASSIFICATION, not in the consumption.**
The steamers are removed from the CT bucket by being classified `ST_GAS`;
omitting the `ST_GAS` *entry from the written artifact* does not put them back.
This is the load-bearing distinction of the whole option and P-3 below tests it
directly.

**What the omission costs, stated plainly.** With no `ST_GAS` entry in
`caiso_offer_curve_measured.json`, `backcast_config.py`'s `_ungrounded_source`
falls back to `"ST_GAS": "CT_PEAKER"` — the pre-repair map. So the parent
PRECOMMIT's §1 objection (the `_ungrounded` map *asserts* ST_GAS is priced off
the CT bucket) is **NOT repaired by this option**, and I will not claim it is.
What the option does fix is the **circularity**: the CT bucket ST_GAS borrows
from no longer contains ST_GAS, so the multiplier is no longer a statistic
biased by its own borrower. It remains a **borrowed** multiplier, and that
stays on the queue.

Both facts are, in the LP, moot: caiso-254 §3 proved — by execution, not by
reading — that `data/offer_curves._offer_curve_for_group` bypasses
`offer_curve_by_group` entirely for CAISO's whole ST_GAS fleet
(`ST_GAS_PEAKER_PLANTS` ⊇ plants 315 / 335 / 350 = 2,858.8 MW = the class), so
**no `ST_GAS` band, present or absent, reaches a CAISO plant.** Re-verified at
HEAD this session: the bypass is at `offer_curves.py:259` and again at `:318`.

---

## §2 — THE MECHANISM: one derive flag, zero consumer change

**Derive (`scripts/data/derive_caiso_offer_surface.py`), new flag
`--st-split-report-only`:**

1. `st_cut` is located exactly as caiso-254 located it (the CT-side
   capacity-density antimode; **not** swept, **not** chosen against any
   criterion) and `_assign_classes` partitions three ways. **Unchanged.**
2. A new `consumed_classes` set is introduced = the measured classes minus
   `ST_GAS` under the flag. `active_classes` — what is measured and reported —
   is **unchanged**, so ST_GAS's G1/G3/G4 rows and its bands are still computed.
3. `all_pass`, G2's pass leg, the `_nan_consumed` refusal, and the two written
   JSONs (`static_doc`, `cond_doc`) are taken over `consumed_classes`.
4. Provenance gains a `reported_not_consumed` block carrying ST_GAS's full
   measured bands and gate rows **with its G4 failure recorded verbatim**, plus
   the citation to this grant. Rule 26 `[R-DELETE]` is respected in spirit: the
   measurement is not deleted and not zeroed, it is **published as refused**.

**Consumer: no change at all.** `pipeline/backcast_config.py:2213` already
reads `"ST_GAS": "ST_GAS" if "ST_GAS" in _measured_bands else "CT_PEAKER"` —
caiso-254's merged fallback. An artifact with no `ST_GAS` entry resolves
through the `CT_PEAKER` limb automatically. **Zero lines of consumer code are
edited by this session.**

**Why this is not gate-shopping.** Gate-shopping would be re-running G4 to a
pass, widening its tolerance, or dropping the failing bucket to make an
aggregate verdict flip. None happens: G4 runs unchanged, ST_GAS still FAILS it,
the failure is published at full magnitude, and the two consumed buckets pass
G4 **on their own rows** — the same rows they would have had under caiso-254's
three-way run, because G4 is per-class and CC/CT's rows do not depend on
whether ST_GAS is consumed. The decision being registered is a **scope**
decision (which measured buckets the model is allowed to read), taken by the
owner, before the artifact is written, and published with the refused
measurement attached.

---

## §3 — ADMISSIBILITY

* **Rule 23 `[R-FROZEN-DERIVE]`** — not a re-derivation of the same
  construction hoping for a different number. The estimator (Theil-Sen), body
  probe (0.35), gas gates, statistic (cap-weighted median), VOM, carbon netting
  and band-window geometry are all frozen and untouched. The commit cites the
  construction defect, as the rule requires.
* **Rule 21 `[R-DOF]` — ZERO new free parameters.** Verified in
  `ADDENDUM-caiso254 §7` against the code: every operand already exists. This
  option needs **strictly fewer** operands than caiso-254's, since the ST_GAS
  geometry is no longer consumed. `--st-split-report-only` is a boolean scope
  switch on a derive, not a solve-affecting `ScenarioConfig` field — no matrix
  row is created (rule 28(c) is not engaged) and no ledger entry is added.
* **Rule 14 `[R-ACCURATE]`** — a measured-input improvement. If it makes the
  backcast worse it still stands; that is the rule's central case.
* **Rule 25 `[R-ISO-SCOPE]`** — CAISO's own OASIS bid record throughout.
* **Rule 13 `[R-MEASURED]`** — pooled 2023–2025, one construction across every
  scored year. Per-year multipliers remain inadmissible and are not proposed.
* **Rule 1 `[R-STRUCT]`** — C3a and C4 are excluded from the adoption decision
  in both directions (§5).

### §3.1 — THE DIRECTION IS PRE-COMMITTED AS UNUSABLE, AND IT IS UNCOMFORTABLE

caiso-254 measured the de-contaminated CT bands. Against the frozen artifact:

| `CT_PEAKER` band | frozen | separated | Δ |
|---|--:|--:|--:|
| `econ_low` | 1.145 | **1.103** | **−0.042** |
| `econ_high` | 1.166 | **1.146** | **−0.020** |
| `peak` | 1.166 | **1.154** | **−0.012** |

**All three move DOWN**, and the keeper's open residual is a C3a *overshoot*
(+4.65 / +9.04 / +8.86 %). So this repair moves prices in the direction the
residual wants, and I register **before the artifact exists** that this is
**not evidence for it** and will not be quoted as any. The adoption rests on
**G-BIMODAL + the G1 capacity reconciliation alone** — the two statistics that
contain no price:

| bucket | pooled (frozen) | separated | own fleet | ratio |
|---|--:|--:|--:|---|
| `CT_PEAKER` | 9,950 MW | **7,391 MW** | 7,616 MW | **1.306 → 0.970** |

A 30 % capacity excess collapsing to 3 % against the class's own published
fleet is the argument. It would be the argument if the bands had moved up.

---

## §4 — PREDICTIONS, WRITTEN TO BIND

| # | prediction | uncomfortable reading if it fails |
|---|---|---|
| **P-1** | the corpus re-fetches to **1,095 / 1,096**, `20230601` the one genuine OASIS hole | the archive changed under us since caiso-254 ran this morning; the frozen artifact is not reproducible from its stated source and the session stops |
| **P-2** | the re-derive **reproduces caiso-254's measured numbers EXACTLY** — antimode 11.738; `CC_REGULAR` 1.066/1.072/1.386; `CT_PEAKER` 1.103/1.146/1.154; G1 ratios 0.871 / 0.970 | a deterministic estimator on the same corpus and the same code that does not reproduce means one of the two runs is not what it claims. **Stop before writing the artifact.** |
| **P-3** | with `--st-split-report-only`, the **written** `CT_PEAKER` bucket is byte-identical to the three-way run's `CT_PEAKER` bucket (bands, `bucket_mw` 7,391, G1 0.970) | omitting ST_GAS from consumption silently changed the CT bucket — i.e. the classification/consumption separation §1 rests on does not hold, and the option is not the option granted |
| **P-4** | ST_GAS's G4 failure is still **computed and published** in `reported_not_consumed`, with `peak` 1.196 < `econ_high` 1.546 | the refusal was hidden rather than recorded, which is the failure mode this whole document exists to prevent |
| **P-5** | phase 0 measures a **strictly CT-side** footprint: F(y) > 0 in all three years, and **zero** ST_GAS tranches move | the ST_GAS inertness proof (caiso-254 §3) is wrong, or the artifact edit is reaching rows it does not claim |
| **P-6** | S-1: in the screen year, `CT_PEAKER` energy **RISES** (cheaper offers ⇒ more dispatch) by an amount within a factor of 3 of what F(y) implies | the mechanism is not doing what its own arithmetic says; the arm dies at the screen |
| **P-7** | S-2: nuclear / hydro / wind / solar each move **< 0.5 %** of keeper annual energy | the offer-array edit is not confined to the gas path — a plumbing defect |
| **P-8** | neither C1 nor C4 flips PASS → FAIL in the screen year | a flip is an owner escalation (§7.2), not a silent kill and not a silent proceed |
| **P-9** | the net first-order effect on annual load-weighted price is **under ±$1.0/MWh**; its **sign is deliberately not predicted** | a larger move means the CT bucket dominates price formation more than the construction implies, and the "first-order small" framing was wrong |

P-2 and P-3 are the two that can stop the session before an LP is spent.

---

## §5 — STOP RULE, AND THE PROMOTION BASIS (registered before any solve)

1. **P-1 or P-2 failing ⇒ stop before the artifact is written.** A derive that
   does not reproduce this morning's measurement is not one I may consume.
2. **P-3 failing ⇒ stop.** The option granted is CT-side de-contamination; if
   the written CT bucket is not the de-contaminated one, this is a different
   object and goes back to the owner.
3. **No gate is relaxed, re-run to a pass, or redefined after its result.** G4
   keeps its 0.05 tolerance. ST_GAS keeps its FAIL.
4. **No threshold in the derive is retuned**, `hr_cut = 8.5` and the antimode
   locator included. **The frozen artifact is never hand-edited.**
5. **Per-year multipliers are never armed.**
6. **No `complete` marker is declared** — an owner act (rule 22), raised in the
   FINDING, not granted here.
7. `frontend/data/forecast/program-status.json`'s stale top-level
   `isos.CAISO.keeper` is **not touched**; the owner ask stays open.
8. **THE PROMOTION BASIS, fixed here:** the run is promoted to keeper iff
   **(a)** the screen's structural gates S-1 / S-2 pass, **(b)** no
   **load-bearing** criterion (C1 / C2 / C3a / C3b) regresses to a **new
   failure** in any of the three years, and **(c)** governance holds (C6
   attested, C8 passes). **C3a and C4 enter (a)–(c) in neither direction** —
   an improvement in either does no promotion work, and C4 regressing to a new
   failure is an owner escalation under §7.2, not an automatic kill. This is
   the caiso-251/252 basis, restated verbatim and registered before the corpus
   finished downloading.

---

## §6 — G-DRIFT: the chain from the keeper, and the ONE hunk that is genuinely LIVE

**Chain to date.** Keeper `fa23c1f7` → `82f79693` (caiso-253) → `fbef3a91` →
`bc77b189` → `d13d1cba` → `d520b891` → `03bd0671` → `1aab49a0` → `7a42c7c5` →
`1ce47fc0` (caiso-254, `ADDENDUM §1–§1.7`): **every hunk INERT** for a CAISO
backcast, with the three deltas touching files a backcast genuinely reads
(carbon, `DEMAND_GROWTH_RATES`, the eGRID fleet path) measured on the number
rather than argued. The single LIVE hunk on that chain,
`results/emissions.py::import_co2_tons`, is confined to `co2`, which is **not
in `CRITERIA`** — so this session **never differences `co2` against the
keeper**, exactly as caiso-254 registered.

**This session's delta, `1ce47fc0` → `173d0a78`, is 4 files / +249 −6, and it
is NOT all inert.**

| file | Δ | verdict |
|---|--:|---|
| `src/market_sim/model/lp/model.py` | +12 | **INERT** — a diagnostic `getInfo().simplex_iteration_count` / `getObjectiveValue()` read **after** `h.run()`, formatted into a log line. Cannot touch the solve. |
| `src/market_sim/pipeline/solve.py` | +139 | **LIVE — §6.1** |
| `scripts/run_calibration.py` | +80 | **LIVE by default — §6.1** (`resolve_p1_basis_seed_default`) |
| `scripts/run_calibration_full.py` | +24 | **LIVE by default — §6.1** (the CLI flag + the default flip) |

### §6.1 — The same-year P1 basis seed is armed BY DEFAULT for calibration runs, and this session turns it OFF

`bf37a0dc` ("Seed the cold-rebuilt P1 from the same year's P0 basis") hands the
cold-rebuilt P1 model the same year's P0 optimal basis before its first solve.
It is gated on `MARKET_SIM_P1_BASIS_SEED`, **whose default
`resolve_p1_basis_seed_default` flips ON for a fresh calibration solve**
(`--no-p1-basis-seed` opts out).

**It reaches CAISO by construction.** The seed fires on exactly the route a
P1-native floor bridge takes — the second `DispatchModel` built on the floored
fleet — and the CAISO keeper carries `caiso_ra_mustoffer`, one of the three
bridges the memo names.

**Prices are LP duals, and a different starting basis can select a different
vertex among degenerate optima.** The owner memo
(`docs/handoffs/p1-basis-seed-decision-memo-2026-09.md` §3.3) measures the seed
as warm-start-class neutral and its evidence is strong — ERCOT 2025 forward:
objective identical to 8e-16 relative, total generation Δ **0 MWh**, max |Δ
zonal price| **1.1e-12 $/MWh**, **0 / 61,320** dual-degenerate hours, every
moved unit-hour a marginal tie at an identical LMP. But that is **ERCOT, one
year, one config**. CAISO is a different LP with a different bridge and its own
degeneracy structure, and no CAISO measurement exists. Rule 29(b) admits two
classifications and neither is "probably fine": a hunk is INERT **with its
reason cited**, or it is LIVE and earns a control solve.

**⇒ This session solves every arm with `--no-p1-basis-seed`.** That is
strictly stronger than classifying it: the hunk becomes **unreached** rather
than asserted-inert, the solve path returns to exactly the one the keeper's
committed bundle was produced on, and it costs **zero LP**. The alternative —
spending a CAISO control solve to establish the seed's dual-neutrality — would
buy nothing this session's gate table asks for, and would confound an
offer-surface arm with a solver-path change.

**⇒ G-CTRL FORM 4 STANDS. `caiso252_b1_notrim`'s committed bundle is the
control. NO control solve is spent.**

**A governance observation, raised not acted on.** The seed is now default-ON
for *every* ISO's next calibration run, and its price neutrality is established
on ERCOT alone. Any future CAISO keeper solved with it armed is not
form-4 comparable to `caiso252_b1_notrim` without a CAISO-side neutrality
measurement first. That measurement is a clean, cheap object (one A/B on one
year under the `diff_warmstart_bundles.py` standard) and it belongs to whoever
takes it — **not to this session**, which would be scope creep on a granted
option. Recorded in the FINDING's queue.

### §6.2 — The consolidated re-audit before the LP

Following `ADDENDUM-caiso254 §1.7`'s stated method: `main` advances several
times an hour, and the audit that binds under rule 29(b) is the one against the
sha **the arm is solved at**. A **consolidated `fa23c1f7` → solve-time HEAD**
audit is therefore recorded in the FINDING **before any LP is spent** — it is
strictly stronger than the sum of the increments, since it cannot miss a hunk
added and then revised between two of them. The classification standard is
unchanged: INERT with a cited reason, or LIVE and it earns a control solve.

---

## §7 — THE RULE-29 `[R-SCREEN]` SCREEN, REGISTERED BEFORE IT RUNS

A 3-year CAISO replay is ~36 min of LP. The repair does not reach it until a
one-year screen clears a **structural, STOP-ONLY** gate.

### §7.1 — Phase 0 (zero-LP) NAMES the screen year

The estimator is caiso-254's, already built and null-validated
(`scripts/probes/_caiso254_partition_footprint_phase0.py`; null control
F = 0.0 exactly, X = 0, 0 of ~1,450 gas tranches moved):

> For each year *y* ∈ {2023, 2024, 2025}, build the CAISO gas offer arrays on
> the keeper recipe twice — once with the frozen artifact, once with the
> repaired one — and report **F(y) = Σ_tranches |Δmc| × pmax** (MW·$/MWh) over
> every gas tranche, with **X(y)** the count of tranche pairs whose merit-order
> rank crosses. `Δmc` is evaluated at each year's own gas and carbon price.

**The screen year is `argmax_y F(y)`.** F and X contain no price actual, no
residual and no criterion. **The measured value of `argmax_y F(y)` is written
into this document and pushed BEFORE the screen solve is launched**, so the
naming cannot be back-fitted. If F ≈ 0 in every year the repair is INERT and
rule 29's own exclusion applies: nothing is screened and the session reports an
inert repair.

**Disclosed in advance** (carried from `ADDENDUM-caiso254 §1.3.2`): the
keeper's **C1 gas records for 2025 are all SKIPPED** on the preliminary EIA-923
vintage. If phase 0 names 2025, the S-3 C1 stop gate has little bite there and
S-4 (C4, scored in all three years) carries the protective load alone. **This
changes nothing about how the year is named** — naming it on "which year my
gate can see" would be the gate-shopping §7.1 exists to prevent.

### §7.2 — The screen gate: STRUCTURAL, STOP-ONLY, target residual EXCLUDED

* **S-1 — the dispatch response matches the pre-solve arithmetic.** All three
  CT bands fall, so `CT_PEAKER` energy must **RISE**, within a factor of 3 of
  the displacement F(y) implies. FAIL ⇒ the arm dies here. *(The ST_GAS leg of
  caiso-254's S-1 is dropped — not relaxed — because caiso-254 §3 proved it
  structurally impossible; it is reported INERT-BY-CONSTRUCTION.)*
* **S-2 — footprint confinement.** Nuclear / hydro / wind / solar each move
  **< 0.5 %** of keeper annual energy. Storage, imports and the CC classes are
  price-responsive and are **reported, not gated**. FAIL ⇒ the change reaches
  rows it does not claim.
* **S-3 / S-4 — C1 and C4 are STOP gates; a flip ESCALATES rather than kills.**
  A PASS → FAIL flip in C1 (class energy) or C4 (gas r / NRMSE — 2025 holds
  0.003 of margin) **stops the screen**: the remaining years are not spent. It
  does not by itself retire the repair — the owner's standing ruling ("if
  structural integrity improves but gates regress that may still be a keeper")
  bears here — so a flip is reported with its measured magnitude and **put to
  the owner**. What may never happen is spending the full span on a flipped
  screen without saying so first.

**EXCLUDED IN BOTH DIRECTIONS:** **C3a** is the target residual and can neither
kill the arm nor promote it. **Neither C3a nor C4 may PROMOTE** — rule 29: the
screen "may kill an arm; it may never promote one." **`co2` is excluded**, per
§6's LIVE-hunk restriction.

**The screen bundle is a throwaway diagnostic probe**: never registered, never
a keeper, never quoted as a keeper number, its year re-solved inside the full
bundle (rule 29(2)), and **DELETED from `results/calibration/` before the PR
merges** (rule 29(c), owner ruling R-AV). Every number this session will ever
cite from it lives in the FINDING.

---

## §8 — DELIVERABLES

This PRECOMMIT (pushed first); the re-fetched corpus (gitignored); the derive's
`--st-split-report-only` scope flag; the re-frozen artifact carrying CC + CT
with ST_GAS published as `reported_not_consumed`; the phase-0 footprint census
with `argmax_y F(y)` pushed before the screen; the screen and its gate table;
the full `--year 2023 2024 2025` bundle in ONE invocation (rule 16
`[R-ALLYEARS]`), registered on the dashboard (rule 15 `[R-DASHBOARD]`); the
consolidated G-DRIFT re-audit (§6.2); a FINDING scoring P-1…P-9; the
`docs/calibration-log/caiso.md` entry; and the rule-28 CAISO matrix-shard
stamp. Keeper promotion is decided on §5(8) and on nothing else.
