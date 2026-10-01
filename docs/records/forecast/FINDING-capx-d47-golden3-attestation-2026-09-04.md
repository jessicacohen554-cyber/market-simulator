# FINDING — capx D47: GOLDEN-3's attestation restores FC-7 with exactly one row moved; and two of the six `-pre-d46` baselines carry MORE axes than §4.6 recorded

**Lane:** capx D47 — a **RECORDS lane, ZERO SOLVES**, closing three items D46 routed to
the director (`FINDING-capx-d46-remeasure-2026-09-03.md` §4.6 and §9 items 4, 6, 7).
Branch `claude/capx-d47-golden3-attestation-vwn9os`, FRESH off `origin/main` `a8464861`.

**Nothing armed, nothing tuned, nothing promoted.** No `ScenarioConfig` field added or
moved, no parameter value changed, no keeper / shard / marker / matrix verdict touched,
gate (a) never moved, rule 22 untouched, the backcast namespace untouched. No mechanism
was proposed or tested, so no rule-28 matrix duty arises.

---

## 0. Verdict (one paragraph)

GOLDEN-3's FC-7 is restored to **PASS** by an attestation that was **pre-declared before
it existed**, and the restoration moved **exactly one row** — the row the pre-declaration
named, and no other. The determination is **HOLD**, unchanged, because four independent
FC failures are untouched; what changed is an *instrument* row, not a model result, and
the board reads the same as it did. The two records items are not clerical: measuring the
six `-pre-d46` baselines rather than restating §4.6's characterisation shows that **two of
them span more axes than §4.6 recorded** — `neiso-t1f-pre-d46` carries a **fourth**
substantive axis (the R-A storage-entry arming, which landed *after* its prior was
solved), and `miso-t1h-pre-d46` is missing from §9 item 7's enumeration entirely. The
counterweight is that `neiso-t1h-pre-d46` measures out **cleaner** than claimed — a
genuinely single-axis delta, zero changed config values — but with a caveat §9 item 4
already flagged and this lane has now put on the board: **both ends of it sit on a
posture the model does not ship.**

---

## 1. The attestation — the sequence is the deliverable

D46 left GOLDEN-3's FC-7 reading `FAIL` on one row (*"no forecast_attestation.json (a
golden run cannot be certified unattested)"*) and **deliberately did not author one**,
because authoring an instrument *after* reading that a row fails without it is the
sequence golden-1 refused and GOLDEN-2 §3 pre-declared against. It routed a properly
pre-declared attestation to the director instead. This lane executes that.

**The sequence is provable from the artifacts, not merely asserted:**

| evidence | value |
|---|---|
| pre-declaration committed **and pushed** | `71dd390e`, `docs/handoffs/PREDECL-capx-d47-golden3-attestation-2026-09-04.md` |
| `forecast_attestation.json` authored | **after** that push |
| the re-scored record's own `provenance.scored_at_sha` | **`71dd390ed56f`** |

The scorer stamped its own run at a HEAD that already carried the pre-declaration. That
stamp is machine-written, not narrated.

> **One process note, recorded against myself.** A routine `git rebase origin/main`
> before pushing rewrote `71dd390e` — the sha cited inside the attestation, the verdict
> note, and (critically) the scorer's own `scored_at_sha`. The rebase was **undone** and
> the original chain pushed as a fast-forward onto the already-pushed tip, so every cited
> sha resolves. The general lesson is worth keeping: *once a commit sha has been recorded
> inside an artifact as evidence of ordering, that commit can no longer be rebased.* The
> branch is consequently a few commits behind `main`; that is the correct trade.

**Control first.** Before authoring anything, the committed `neiso-t3` record was
reproduced from exactly the committed inputs by the HEAD scorer with **zero
non-provenance diffs** — all eight categories, every row, `determination`, `reasons`,
`caveats`. Establishing that control was not a formality: GOLDEN-3's FC-3 consumes
**D46's own re-solved T1-H** (`neiso-2021-2025-realized-t1h-d46`, `da19b85495178949`),
**not** GOLDEN-2's `neiso-2021-2025-curve` leg. Scoring with the latter — the obvious
guess, and the one GOLDEN-2 §3 documents — yields a *different* FC-3 band list and would
have been a silently wrong baseline against which any subsequent claim of "one row moved"
was worthless.

### 1.1 What moved — asserted row-by-row, and verified

**EXACTLY ONE ROW:**

```
FC-7 row[3] 'attestation':  UNATTESTED -> PASS
                            "all §5 checklist assertions present and true"
```

**BYTE-IDENTICAL** — every row of FC-1, FC-2, FC-3, FC-4, FC-5, FC-6, FC-8 and FC-7 rows
1–3 (`run_config`, `overlay-off`, `dof ledger`): same `row`, `status`, `detail` string,
`gating` flag, and row count. Also unchanged: `schema`, `rubric_version`, `tier`, `iso`,
`caveats` (`["FC-5 external corridor", "FC-6 driver response"]`).

**The two derived surfaces moved exactly as the pre-declaration §1.3 named them in
advance**, which is why neither can read as a surprise: `FC-7` category `FAIL → PASS`
(the roll-up of its four rows), and `reasons` drops its `"FC-7 provenance & DOF FAIL"`
line, leaving the four FC-1…FC-4 entries verbatim.

| category | before | after |
|---|---|---|
| FC-1 structural integrity | FAIL | FAIL |
| FC-2 adequacy & equilibrium | FAIL | FAIL |
| FC-3 cap-evolution (T1-H) | FAIL | FAIL |
| FC-4 crossover skill (T1-X) | FAIL | FAIL |
| FC-5 corridor | CAVEAT | CAVEAT |
| FC-6 driver response | CAVEAT | CAVEAT |
| **FC-7 provenance & DOF** | **FAIL** | **PASS** |
| FC-8 feasibility | PASS | PASS |
| **determination** | **HOLD** | **HOLD** |

**The attestation certifies provenance, not accuracy.** It says the bundle's evidence is
complete and attested. It says nothing about whether GOLDEN-3 is *right*, and it cannot:
FC-1 (I3 renewable dump), FC-2 (cobweb), FC-3 (T1-H bands) and FC-4 (T1-X dispatch skill)
all still FAIL, on measured instruments this lane never touched.

### 1.2 The six §5 assertions, all read from committed bytes

| assertion | verified reading |
|---|---|
| `dof_ledger_complete` | `dof_ledger.json` sha256 `c8cd36557f867961`, built by the committed builder from this bundle's own `run_config.json`: **7 entries, 7 IDENTIFIED, 0 UNIDENTIFIED, 0 unattested, 0 `residual`** |
| `run_config_reproducible` | `fc6/arms/base` keys at `67678e58b2d0526c` = the campaign key; the two summaries agree on **every** top-level field except `total_wall_s`, `per_year_perf`, `global_peak_rss_mb`, `run_config_path` — i.e. the 25-row `trajectory` and 14-row `invariants` vector are identical |
| `honest_unfit_referenced` | `program-status.json` `honest_unfit` register (5 entries), referenced not restated; bundle-specific items in D46 §4.6 / GOLDEN-2 §4 |
| `quarantine_attested` | `mode="forecast"`, `solved_years` 2026–2050 — rule 22's permitted class; this lane solved nothing at all |
| `no_off_registry_knobs` | 778-key full resolved surface; 7 non-default fields, all identified; two charter CLI flags only |
| `registered` | registered by the **producing** session (D46) on the forecast namespace only; backcast registry not written |

**Two deviations are disclosed on the artifact's face rather than buried:**

1. **The attesting session is not the producing session.** Rubric §5 names "the producing
   session (T3)" as author; D46 produced this bundle and D47 attests it. That deviation
   is the *price* of D46 having correctly refused the post-hoc route — the alternative
   was the thing the rule exists to forbid — and the routed item sanctions exactly this
   follow-up.
2. **`quarantine_attested` is scoped to producing *this* bundle**, which is what rubric
   §5.4 asks. The FC-3 input's own solve spans `[2021, 2023, 2024, 2025]` with
   `scored_years [2023, 2024, 2025]` and cutoff `2020-12-31`; the FC-4 input spans
   2023–2027 in the permitted crossover window. Both enter as committed bytes and each
   lane's quarantine posture stays its own record's business — stated exactly rather than
   described as "training-window" and left to read cleaner than the facts.

### 1.3 Registration

Prior preserved **byte-equal** at **`neiso-t3-pre-d47`**; the bare `neiso-t3` re-stamped
against the **same** `run_id` and `cache_epoch` (`67678e58b2d0526c`) — the run is
unchanged, only the scoring input set gained one artifact. The existing chain
(`-pre-fc5`, `-pre-fc6`, `-pre-fc6repair`, `-pre-p2scope`, `-prera-2026-08-31`,
`-pre-d46`) and **every other verdict key** are untouched (74 → 75 keys, verified). The
D46 note is retained as `notes[0]` with the D47 note appended.

---

## 2. The `-pre-d46` like-for-like table (D46 §9 item 7)

**This is the citation any future reading of a `-pre-d46` delta must carry.** It replaces
restatement with measurement: each row below is the diff of the two runs' **committed
`run_config.json` resolved surfaces**, and "vintage" is the **solve** epoch (cache key +
`git.sha` from the run config), never the scoring sha — a distinction that matters,
because several of these records' `scored_at_sha` values are re-score shas days newer
than the solve they describe.

**§9 item 7 enumerates four keys. Six exist.** It omits `miso-t1h-pre-d46` entirely.

| `-pre-d46` key | prior vintage (solve) | bare vintage (D46 solve) | axes actually spanned | attributable? |
|---|---|---|---|---|
| **`neiso-t1h-pre-d46`** | `313ba0612435b963` · `11735c1f` · 2026-09-02 (D37 armed) | `da19b85495178949` · `71d3f1a6` · 2026-09-03 | **ONE — the fossil flip alone.** Zero changed config values; 9 added fields, **all `False`**; none removed. | **YES** — the batch's genuinely single-axis leg. **But see §3: both ends carry a non-shipped posture.** |
| **`neiso-t3-pre-d46`** (GOLDEN-3) | `706e7ba8e6582d42` · `f0a13bf5` · 2026-09-01 (GOLDEN-2) | `67678e58b2d0526c` · `012ec403` · 2026-09-03 | **THREE parameter changes spanning TWO of the batch's three axes:** `fossil_announced_exits_enabled` absent→`True`, `ccs_retrofit_capex_kw` 900.0→1521.4, `fixed_om_gas_cc_ccs` 25.0→65.0. Residual: 12 added `False` defaults, 1 removed (`caiso_bidir_intertie`). **Axis (iii) keeper vintage does NOT apply** — both DOF ledgers name `2026-08-17-neiso-99-joint-p1`. | **YES** — the batch's cleanest multi-axis leg, and the three changes are individually named |
| **`miso-t1h-pre-d46`** *(absent from §9 item 7)* | `40173304213d39cd` · `80327d08` · 2026-09-02 (D33) | `eff2c890746ec966` · `93ca86bd` · 2026-09-03 | **THREE axes + 1 inert flag:** fossil flip, **both** CCS constants, **and** keeper vintage MISO 198→202 (D46 §0); plus `entry_screen_diagnostics` `False`→`True`, which moves the cache key but is declared **pure observability, no effect on any result** (`scenarios.py`). | **NO** — three substantive axes confound |
| **`neiso-t1f-pre-d46`** | `9a7f68fc7dcac931` · `88baa9d` · **2026-08-30** (S-4b) | `6690e4d6d66bc819` · `75a5ff08` · 2026-09-03 | **FOUR axes — one more than §4.6 implies.** Fossil flip + both CCS constants, **AND the R-A storage-entry arming**: `storage_entry_availability_gate` and `storage_entry_cost_normalized_rank` are **absent** in the prior and **`True`** in the bare key. R-A landed at `ecf9972` on **2026-08-31**, i.e. *after* the prior was solved. Also removed: `renewable_buildout_pace`, `caiso_bidir_intertie`. | **NO** — and this is the table's substantive correction |
| **`ercot-t1f-pre-d46`** | **no cache key exists.** The record's `cache_epoch` is the prose string *"Epoch 2026-08-03 — FFR Wave-2 constants + the D-1/D-2 owner default flips"*; `run_id` null; no `scored_at_date`; scoring sha `8ba592814d92` | `873d8c0e6cab52ae` · `dd10e9fe` · 2026-09-03 | **UNKNOWABLE.** The prior carries no resolved config identity, so **no config-level diff is possible at all** — a month of HEAD *plus* the batch axes, with no way to separate them | **NO** — the strongest form of not-attributable |
| **`caiso-t1f-pre-d46`** | same prose epoch; `run_id` null; sha `8ba592814d92` | `772b1e5abc7fc80c` · `012ec403` · 2026-09-03 | **UNKNOWABLE**, as above, **plus** keeper vintage CAISO 231→240 (D46 §0) | **NO** |

### 2.1 What the measurement changes, and what it does not

- **§4.6's substantive scope caveat STANDS and is if anything strengthened.** ERCOT and
  CAISO t1f are not merely mixed-vintage — their priors carry **no resolved cache key at
  all**, so the deltas are not weakly attributable, they are **un-diffable**. Reading
  either as a model effect is unsupported in principle, not just in practice.
- **The correction is to §4.6's grouping.** It puts `neiso-t1f-pre-d46` and
  `neiso-t3-pre-d46` together as *"recent and much closer to the axes themselves."* They
  are not alike: GOLDEN-3's prior post-dates the R-A arming and its delta is exactly the
  three named parameter changes; NEISO t1f's prior **pre-dates** R-A by a day, so its
  delta additionally carries the storage-entry lever. A four-axis delta should not be read
  against a three-change one.
- **And `neiso-t1h-pre-d46` is cleaner than the caveat suggests** — zero changed values,
  every added field at `False`. Its limitation is not axis count; it is §3.
- **Nothing here re-scores or re-registers any of the six.** No determination moves. The
  table is a reading instrument.

---

## 3. The `neiso-t1h` posture disclosure (D46 §9 item 4)

**The bare `neiso-t1h` key advertises a posture the model does not ship.** Verified from
the committed `run_config.json` bytes of all three legs, not inferred:

| leg | key | `neiso_net_icr_requirement` |
|---|---|---|
| `neiso-t1h` (**bare**, D46) | `da19b85495178949` | **`true`** — the D40/Q28 lever **ARMED** |
| `neiso-t1h-d37-control` (suffixed) | `5925e67c572a910f` | `false` — the **shipped** default |
| `neiso-t1h-pre-d46` (D37 armed) | `313ba0612435b963` | `true` |
| GOLDEN-3 T3 bundle (for contrast) | `67678e58b2d0526c` | `false` |

**Origin, stated plainly.** capx D37 registered the **ARMED** leg on the **BARE** key and
its paired **CONTROL** — the shipped-default arm — under the **SUFFIXED** key
`neiso-t1h-d37-control`. That is the inverse of director ruling **r#33**, which holds that
a bare key carries the **SHIPPED** posture. capx D46 then re-solved the armed leg, keeping
the lever armed at both ends, *precisely so its fossil-dates refresh stayed single-axis* —
the right call for that measurement, and the reason the discrepancy survived into the
current record rather than being introduced by it.

**Consequence for a reader.** The FC-3 row's **absolute** numbers describe an armed-lever
NEISO, not the model as shipped. The **`-pre-d46` → bare delta remains a clean
single-axis measurement** of the fossil-dates flip, because the lever is armed identically
at both ends (§2). Those two statements are compatible and both need saying.

**This lane does not fix it, by design.** No re-solve, no field flip, no determination
move (`HOLD`, unchanged). The shipped-default NEISO leg rides **D45-R**, which replaces
this record. What D47 adds is the disclosure, in two places: a dated note appended to the
board's NEISO FC-3 carrier field `isos.NEISO.t1h_provenance` in
`frontend/data/forecast/program-status.json` — the same field D37 itself edited, which is
the precedent — and this section.

---

## 4. Gate integrity

| check | reading |
|---|---|
| `scripts/check_gate_a_provenance.py` | **OK (6 rows)** — keeper identity + marker state match the backcast store; no determination read. **Gate (a) never moved by this lane.** |
| `scripts/check_mechanism_matrix.py` | integrity OK; 0 unresolvable anchors beyond the ratchet; keeper stamps and §5.x prose headers match every shard |
| `scripts/check_forecast_staleness.py` | WARN-level only (never blocking); the newest verdict stamp is now this lane's `71dd390ed56f` |
| `register_forecast_run.py --reindex` | 53 runs written to the gitignored preview namespace; nothing generated was committed |

Rule 27 blob verification after each push touching a file ≥300 lines:
`frontend/data/forecast/ff-verdicts.json` (9,500 lines) and this lane's docs — remote line
count and sha256 compared to local, **MATCH** in every case, before the next commit. No
file was rewritten from regenerated response content; `ff-verdicts.json` and
`program-status.json` were edited in place through a format-preserving round trip
(`json.dumps(..., indent=1)` verified byte-identical to the committed file **before** any
edit), so each diff contains only the intended change — `ff-verdicts.json` is a pure
insertion, `program-status.json` a single line.

---

## 5. Pre-declaration, graded at full magnitude

| pre-declared | outcome |
|---|---|
| §1.1 the attestation row moves `UNATTESTED → PASS`, or `FAIL` at full magnitude if any assertion is untrue | **HELD** — PASS; all six assertions true on the committed evidence |
| §1.2 every other row byte-identical; any other row moving is STOP-and-route | **HELD** — one row moved, verified row-by-row across all eight categories |
| §1.3 the two derived surfaces (FC-7 category, the `reasons` line) move, and only those | **HELD** — exactly as named |
| §1.2 determination stays `HOLD`; caveats unchanged | **HELD** |
| §2 nothing authored that the bundle does not carry | **HELD** — every assertion cites a committed artifact |
| §3 the scorer invocation, verbatim, artifact-only | **HELD** — run as written; zero solves |
| §4 preserve-then-overwrite at `-pre-d47`, chain untouched | **HELD** — prior byte-equal; 74 → 75 keys; every other key identical |
| §5 the table would find **six** keys, not §9 item 7's four | **HELD** — and it found more than the enumeration gap: `neiso-t1f-pre-d46` spans a fourth axis (§2) |
| §6 gate (a) re-checked at close | **HELD** — OK (6 rows) |
| **MISS, recorded against myself** | §6 did not anticipate that a routine rebase would invalidate a sha already recorded inside an artifact as ordering evidence. Caught before the force-push, undone, original chain fast-forwarded (§1). No artifact carries a dead sha. |

---

## 6. Routed to the director

1. **`neiso-t1h`'s bare key still carries the armed posture.** D47 disclosed it; only
   D45-R's default-posture leg can retire it. Until that lands, r#33 is violated in the
   record even though it is now violated *visibly*.
2. **`ercot-t1f-pre-d46` and `caiso-t1f-pre-d46` have no resolved cache key.** They are
   un-diffable, not weakly attributable (§2). Consider whether a preserved record without
   a resolved config identity should be retained as a comparison baseline at all, or
   marked as a provenance-only stub that no delta may be read against.
3. **Attestation authorship.** Rubric §5 names the producing session as author; this
   attestation is D47's, under the director's own routing. If the pattern is to recur —
   and it will, whenever a lane correctly refuses the post-hoc route — rubric §5 may want
   an explicit second limb for a **pre-declared follow-up attestation**, so the deviation
   is provided for rather than disclosed each time.
4. **The board's NEISO `golden` field still describes GOLDEN-2** (`MEASURED 2026-09-01 …
   neiso-2026-2050-t3-golden2-bau`), not GOLDEN-3, and now names an FC map (`FC-7 PASS`)
   that is true of both runs for different reasons. Out of this lane's scope — noted, not
   touched.

---

## 7. Session close-out

Three routed items closed; **zero solves**; every deliverable committed and pushed. The
attestation exists because its pre-declaration was pushed first and the scorer's own
stamp proves it. Exactly one row moved, and the determination is the same `HOLD` it was
before — which is the point: an instrument row was restored, and nothing was promoted.

---

# ADDENDUM — capx D47b: the board's `c_cost` fields (r#33 amendment 3), and a correction to D46 §2

**Appended 2026-09-04 by lane capx-D47b**, branch
`claude/capx-d47-golden3-attestation-nrqtyq`, rebased on `origin/main` `8a18e9e1`. The
five-item D47 dispatch's items 1–4 landed in PR #4691 (`bd4ba21d`) and are **verified in
place at HEAD, not re-done**: `neiso-t3` reads FC-7 `PASS` / `HOLD` / session `capx-D47`,
prior preserved at `neiso-t3-pre-d47` reading FC-7 `FAIL` / session `capx-D46`. Item 5 —
the `c_cost` fields — was not covered by that PR and is closed here. Pre-declared before
any field was edited: `docs/handoffs/PREDECL-capx-d47b-ccost-2026-09-04.md`, commit
`fb80a6e3`. **Zero solves.**

## 8. The `c_cost` correction — and why the dispatch's own numbers could not be used

### 8.1 The defect: the two quantities are different measurements

The dispatch read: *"D46 §2 measured the t1f legs at 8–23 min against `c_cost` fields of
1.0–2.8 h. Correct … to the MEASURED values … mark PJM/MISO/NYISO's fields 'unmeasured at
the t1f grain — D46 factor 7–10× suggests ~45–90 min'."* **Executed literally, that puts a
wrong number on the board, in the dangerous direction.**

| | span | source |
|---|---|---|
| the `c_cost` fields | **25 solve-years** (2026–2050, full horizon) | FF-3E projection table, `docs/handoffs/ff-poc-closeout-2026-07.md` §6 |
| D46's measured t1f legs | **5 solve-years** (2026–2030) | `results/ff-t1f-d46/<iso>/full_horizon_summary.json`, `solved_years [2026…2030]` |

D46 §2's headline — *"All three t1f estimates the board carries are wildly conservative —
by factors of 7–10×"* — compares a 5-year total against a 25-year projection. **The factor
is a span artifact:** 5× span × the projection's own ~1.7–2× super-linear uplift ≈ 8.5×,
which is exactly the 7–10× reported. **This corrects D46 §2's comparison and §9 item 3's
inference. It corrects no D46 solve, cache key, verdict or determination**, all of which
stand untouched.

### 8.2 The evidence, all from committed bytes (`per_year_perf`, `global_peak_rss_mb`)

| leg | span | total | median/yr | FF-3E anchor | peak RSS |
|---|---|---|---|---|---|
| ERCOT t1f `ercot-2026-2030-d46-remeasure` | 5 yr | 11.81 min | **144.1 s** | 144 s → **+0.1 %** | 4,137.7 MB |
| NEISO t1f `neiso-2026-2030-d46-remeasure` | 5 yr | 7.96 min | **86.3 s** | 78 s → +10.6 % | 3,336.7 MB |
| CAISO t1f `caiso-2026-2030-d46-remeasure` | 5 yr | 22.59 min | **208.8 s** | 200 s → +4.4 % | 4,917.4 MB |
| **NEISO GOLDEN-3** `neiso-2026-2050-t3-golden3-bau` | **25 yr** | **33.0 min = 0.55 h** | **77.6 s** | 78 s → **−0.5 %** | 3,694.0 MB |

Year 2026 is a warm-up outlier in every 5-year leg (CAISO 499.7 s against a 201–243 s
steady state), which is why the **median** and not the mean is the comparable statistic on
a short window.

### 8.3 The two halves of the projection grade oppositely

1. **FF-3E's per-year anchors are ACCURATE** — within +0.1 % to +10.6 % on three ISOs at
   the 5-year grain, and within **−0.5 %** on the one 25-year run. They are not "an order
   out"; they are among the better-identified compute numbers on this board.
2. **FF-3E's super-linear uplift is REFUTED, with the sign reversed.** §6's caution
   ("late years grow super-linearly — do **not** extrapolate the median flat") predicted
   growth. GOLDEN-3's 25 measured years run the other way: **years 21–25 mean 65.0 s
   against years 1–5 mean 95.3 s, a 0.68× ratio.** Per-year cost *falls* across the
   horizon. The total lands **1.8 % above the flat-median lower bound** (0.54 h) and
   **1.73× under the projection** (0.95 h). **The whole projection error is the uplift.**

So the span-corrected conservatism is **~1.7×, measured once** — not 7–10×.

### 8.4 What was written, per ISO

Six `detail` strings, nothing else. **ERCOT / NEISO / CAISO** carry their measured values
with the span stated on the field's face, the prior number identified as FF-3E's
projection, and its basis decomposed per §8.3. **NEISO is the one ISO whose full-horizon
figure is now a measurement** (0.55 h against a 0.95 h projection) and is the evidence
every other field cites.

**PJM / MISO / NYISO are marked unmeasured at every grain and carry a bracket, not a point
estimate:**

| ISO | flat-median bound | FF-3E projection | uplift baked in | if NEISO's 1.73× transfers |
|---|---|---|---|---|
| NYISO | 0.62 h | 1.09 h | 1.76× | ~0.63 h — **the two routes converge** |
| PJM | 1.63 h | 7.34 h | **4.50×** | ~4.2 h |
| MISO | 2.25 h | 10.12 h | **4.50×** | ~5.9 h |

**The refutation transfers least well to PJM and MISO**, whose projections carry a ~4.5×
uplift tied to ~10 GB late-horizon growth that **no measured ISO exercises** — all three
measured legs peak ≤ 4.9 GB and all are pairable. Nothing measured discriminates between
the bracket's ends there, and the fields say so. At NYISO — light, pairable, a ~1.76×
uplift essentially identical to NEISO's — both routes land on ~0.62–0.65 h, so the
transfer is much better supported and the field says that too.

**The ~10 GB (PJM) and ~10.5 GB (MISO) SOLO memory ceilings are preserved verbatim.** A
wall-time correction must not erode a memory constraint, and rule 12's concurrency plan
keys on exactly those numbers.

**The container's ~55 min `regenerate_clean.py` prerequisite** (54 datatypes, D46 §2) is
named in every corrected field as a **separate, per-container** cost, never folded into a
leg's wall time.

### 8.5 The `~45–90 min` figure is refused

It derives from the span-confounded 7–10×. Applied to PJM it would under-price a **solo,
memory-bound** run by 4–6× — the direction in which a scheduling error actually costs
something, since rule 12 forbids co-running it. Against **D46 §9 item 3** (*"if PJM's
7.3 h and MISO's 10.1 h carry the same factor, Stage 3 may be far cheaper than priced"*):
the factor is ~1.7×, so PJM reads **~4.2 h** and MISO **~5.9 h**, or their flat-median
bounds 1.63 h / 2.25 h if their horizons behave like NEISO's. Stage 3 is **cheaper than
priced, but not an order cheaper**, and the memory constraint is untouched either way.

### 8.6 Assertions, verified rather than claimed

- **Exactly six lines changed** in `frontend/data/forecast/program-status.json`
  (`git diff --numstat` → `6 6`; hunks at lines 125, 184, 242, 303, 366, 425).
- **Semantic diff of the whole board: exactly six changed values**, all
  `/isos/<ISO>/gate/c_cost/detail`. Nothing added, nothing removed.
- **Every gate-leg `status` byte-identical**, checked programmatically across all six ISOs
  and all legs. All six `c_cost` legs stay `info`; `info` is not a gate test.
- `scripts/check_gate_a_provenance.py` → **OK (6 rows)**, before and after. Gate (a) not
  moved.
- `register_forecast_run.py --reindex` → **53 runs, manifest + program-status assembled
  clean.**
- **Rule 27:** the file is 1,155 lines. Edited locally with `Edit`, pushed as exact on-disk
  bytes over `git push`, and the pushed blob fetched back and compared — **1,155 lines and
  sha256 `37b9d4b596947378` on both sides, byte-identical.**
- No `ScenarioConfig` field, parameter, keeper, shard, marker, matrix verdict or backcast
  surface touched. No mechanism proposed or tested, so no rule-28 matrix duty arises.

### 8.7 Pre-declaration, graded

All three pre-declared failure modes cleared: no gate-leg status moved and no field
outside the six changed (mode 1); gate (a) did not regress (mode 2); the JSON parses and
the diff is exactly six lines, with no `json.dump` round-trip (mode 3). The pre-declaration
also stated the §8.1 defect *before* the replacement numbers were written, which is the
sequence that makes §8.3's conclusion a finding rather than a rationalization.

## 9. Routed to the director (D47b)

1. **D46 §2 and §9 item 3 should be annotated as span-confounded** — superseded on the
   comparison, not on any solve or verdict. This addendum is the correction of record; the
   D46 finding itself is another lane's artifact and was not edited.
2. **FF-3E §2.4's super-linear caution is refuted at NEISO over 25 years** (0.68×, not
   >1×). It still stands unmeasured at PJM/MISO, where it drives a 4.5× uplift and where
   the ~10 GB memory growth that motivated it is real. Worth a single 25-year measurement
   at one heavy ISO before Stage 3 is priced — that, not another light-ISO run, is the
   measurement that would retire the bracket.
3. **`c_cost` has no consumer beyond the board's own renderer**
   (`docs/codebase-site/forecast-status.html` gate-order list). It is a human scheduling
   input, not a gate test — which is why this lane could correct it as records. If the
   §2.1b(2)(c) leg is ever meant to *test* cost, that is a charter change, not a field edit.
