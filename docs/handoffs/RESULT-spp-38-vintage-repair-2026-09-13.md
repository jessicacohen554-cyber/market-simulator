# RESULT — SPP-38: the vintage-cache repair LANDED, and SPP's keeper re-solved on a correct LP input

**ONE LINE: the repair landed and is merged; the re-solved run is `2026-09-13-spp-38-vintage-cache`,
`CALIBRATED` (rubric v3.7), grade 7 of 8, 0 FAILS, 1 ledgered C3c caveat — the SAME SHAPE as keeper 10
on every scored criterion; 2023 reproduces keeper 10 byte-for-byte, and 2024/2025 move to exactly the
values FINDING-spp-37 §4c measured for the CORRECT single-year construction (2025 LW price
29.5377 → 30.0737, slack 0 → 240.5966 MWh, ST_GAS 12.6132 → 11.3395 TWh, all to 4 dp).**

Lane **SPP-38** · base `origin/main` @ `859c5dd52f4ac9e2be6381faf595a85ec66de217` ·
repair commit `760012f7a12b5d6fae01c5a6a4c96c9dc8588ed9` (**merged to `main`**) ·
branch `claude/spp-38-vintage-cache-repair-k4m2` ·
PRECOMMIT `docs/handoffs/PRECOMMIT-spp-38-vintage-cache-repair-2026-09-13.md`.
**Parent LP: ZERO** (rule 32(a)). **Shards: ONE**, archived.

---

## 1. A1 — THE REPAIR. TWELVE LOADERS, NOT ELEVEN.

Each public name became an **uncached thin shim** over a **cached core keyed on the active EIA-860
directory** — the pattern the repo already used four times. Where a core reads a sheet directly it now
reads **from its own argument**, so a stale global cannot desync from the key.

FINDING-spp-37 §3's table has **twelve** rows and calls eleven "LEAKS". The twelfth,
`eia860_selfcommit_scope_plants`, is vintage-blind by exactly the same construction — a `maxsize=1`
cache over a union of two loaders that both move — and would have pinned year 1's union even with its
inputs repaired. **Its "stable" reading was an artifact of the probe clearing the union's own cache but
not its two legs, not a property of the data.** All twelve are repaired.

Two reach SPP keeper 10's solve path and are direct LP inputs: `outages._iso_plant_capacity` (the
denominator of BOTH outage overlays) and `campd_bins.cc_duct_peaking_pct` (the CC peak offer band).

**Zero free parameters, zero `ScenarioConfig` fields, zero gates, zero declared default flips, no
matrix row and no cell verdict moves** (rules 21 / 24 / 28 — a cache key is not a tuning channel).
Basis: rule 14 `[R-ACCURATE]`, never the residual.

### 1.1 Proof, not assertion

| measurement | pre-repair | post-repair |
|---|---|---|
| census §2b — warm cache, vintage flipped | 12 loaders serve a STALE vintage | **all 12 `rekeys`** |
| census §5 — LP's own 2025 availability input, ≥5-day overlay | **−5,817,173 MWh** (18 bins differ) | **+0 MWh (0 bins)** |
| census §5 — same, <5-day overlay | **+142,296 MWh** (5 bins differ) | **+0 MWh (0 bins)** |
| census §6 — blast radius at `tracks_solve_year=False` | — | `constant → strict NO-OP` |

`tests/unit/data/test_eia860_vintage_cache_keying.py` (**33 hermetic tests**) pins both legs: re-keying
on a vintage switch, a strict no-op at a constant vintage (same object back, `currsize == 1`,
`hits ≥ 1`), and structurally that each public name is uncached and each core's first parameter is
named `eia860_dir`.

Hard stops: `test_run_year_kwarg_binding.py` **4 passed**. Fast lane **9,410 passed** against the base's
**9,377**, with the **identical 16 pre-existing failures** — verified by re-running the whole lane on a
stashed clean tree, not assumed. Blob verification after push (rule 27) on all three ≥300-line modules
plus the new test: line counts and SHA-256 identical, all three files **grew**.

### 1.2 The SPP-27 inherited item: SAME DEFECT, CLOSED BY THIS REPAIR

SPP-27 recorded `scripts/lib/bundle_fleet.reconstruct_bundle_fleet` order-dependent across years for
SPP and concluded "nothing scored is affected". **It needs no separate repair — it IS this defect one
layer over.** It calls `run_year(fleet_only=True)`, which re-points the vintage per year.

Measured at zero LP, digesting `fleet_arrays.availability` (the array the LP's generator bounds come
from) for **2025**, built alone vs. after 2023→2024, **each leg in its own process**:

| tree | 2025 alone | 2025 after 2023→2024 | verdict |
|---|---|---|---|
| PRE-repair | 7,580,565.41768 (`1c4c9c43ec00ce1f`) | **7,625,968.40751** (`e038bf45ba97e90a`) | **ORDER-DEPENDENT** |
| POST-repair | 7,580,565.41768 (`1c4c9c43ec00ce1f`) | **7,580,565.41768** (`1c4c9c43ec00ce1f`) | **IDENTICAL** |

The span held **more** availability (+45,402.99), i.e. removed **less** capability — the same sign
FINDING §4b measured on the overlays, from a different instrument, neither adjusted toward the other.
`mc_base` is byte-identical (`6ad5725b21565235`) in all four legs, so for SPP 2025 the
`cc_duct_peaking_pct` leak — live by the census — did not reach the marginal-cost array.

> **METHOD NOTE, recorded because it nearly produced a wrong answer.** The first attempt ran both legs
> in ONE process, alone-first. Pre-repair that makes the comparison pass **for the wrong reason**: the
> alone-2025 build populates the vintage-blind cache and the chain's 2025 reads that same entry, so
> both legs agree by accident. **Each leg must be its own process.** This is the same class of trap
> FINDING-spp-37 §3's own method note records (a swallowed `json.dumps` exception reporting a leaking
> loader "stable"). Any future census of this family must isolate its legs.

---

## 2. A2 — THE RE-SOLVE

One shard, one `--years 2023 2024 2025` invocation, one bundle, years sequential inside it. **9m35s
wall, 6.12 GiB peak** (well under the 13.34 GiB nested-cgroup ceiling). Config signature machine-checked
by the shard before solving and by the parent after: `offer_curve_by_group` SHA-256
`090abd79…62f65` **identical**, `eia860_vintage_tracks_solve_year` True, `unit_outage_short_windows`
True, `unit_outage_short_windows_gas` False. The **only** two differing `scenario_config` keys are
`miso_import_sil_measured_envelope` and `gas_offer_margin_zonal_anchor_vintage` — exactly the two
default-off fields the G-DRIFT audit predicted, both absent when keeper 10 solved.

### 2.1 THE 2023 SELF-CHECK PASSES EXACTLY

2023 is year 1 in both constructions, so the cache key cannot reach it. LW price **25.7428**, slack
**0.0000**, dump **0.0000**, 0 hours > $200, max price **61.4221**, and **all fifteen class TWh at
+0.0000**. A 2023 that moved would have been a stop-the-line event.

### 2.2 2024/2025 LAND ON THE CORRECT SINGLE-YEAR CONSTRUCTION, TO 4 dp

| 2025 | keeper 10 (stale) | SPP-38 (repaired) | FINDING §4c single-year leg |
|---|---|---|---|
| LW price $/MWh | 29.5377 | **30.0737** | 30.0737 ✓ |
| slack MWh | 0.0000 | **240.5966** | 240.5966 ✓ |
| hours > $200 | 0 | **2** | 2 ✓ |
| COAL_PRB TWh | 77.4872 | **78.0526** | 78.0526 ✓ |
| COAL_LIGNITE TWh | 6.5483 | **6.5890** | 6.5890 ✓ |
| CC_REGULAR TWh | 36.1986 | **36.3783** | 36.3783 ✓ |
| CT_PEAKER TWh | 15.5101 | **15.9916** | 15.9916 ✓ |
| **ST_GAS TWh** | 12.6132 | **11.3395** | 11.3395 ✓ |

2024: LW 26.0214 → **26.3509**, slack 370.1017 → **1295.6995** MWh, hours > $200 7 → 8, ST_GAS
13.2733 → 13.0946, CT_PEAKER 19.3074 → 19.4420 TWh. Energy conserved to ≤ 0.0026 TWh on ~300 TWh;
dump 0.0000 everywhere.

### 2.3 THIS OVERTURNS A CONCLUSION IN KEEPER 10'S OWN PROMOTION NOTE

That note dismissed three single-year fan-out shards' slack readings — **1295.6995 MWh in 2024,
240.5966 in 2025** — as *"a CONSTRUCTION MISMATCH IN THE PARENT'S OWN DESIGN"* and declared the
span-vs-span A/B *"the valid one"*. **The repaired span reproduces those exact numbers.** The
single-year legs were right; the span carried the defect, and the dismissal was the wrong call.

The SPP-36 A/B **itself still survives** — both its legs were 3-year invocations sharing the identical
stale state, so the *difference* it measured is real. What was not sound is the *level* either leg
reported for 2024/2025, which is what C3a/C3b/C1 score. **The note is left standing as the historical
record rather than edited**; this document is the correction.

---

## 3. THE GATES — reported at full magnitude, gated on NOTHING

`2026-09-13-spp-38-vintage-cache` · **`CALIBRATED`** (rubric v3.7) · grade **7 of 8** · **0 FAILS** ·
**1 ledgered C3c caveat** · 0 protective · free-class C1 **16/16 all · 12/12 free**. Every criterion
carries the same status as keeper 10: `fuelmix` `sysvol` `price_mean` `price_shape` `dispatch_corr`
`governance` `forced_share` PASS, `price_tail` CAVEAT.

| criterion | 2023 | 2024 | 2025 |
|---|---|---|---|
| **C3a** keeper 10 err % | +2.43 | +2.24 | +3.29 |
| **C3a** SPP-38 err % | **+2.43** | **+3.54** | **+5.17** |
| **C3b** keeper 10 NRMSE | 0.176 | 0.175 | 0.175 |
| **C3b** SPP-38 NRMSE | **0.176** | **0.169** | **0.188** |

**Two of three C3a years get WORSE and the repair stays.** Rule 14 `[R-ACCURATE]` is explicit that a
worse fit from an accurate input is a discovered bug to root-cause, never a reason to revert; and no
gate, band or residual was consulted in deciding to land it. Equally, C3b 2024 *improving* is not
evidence for it. **There was deliberately NO screen gate and NO residual gate for this arm**: rule 29
`[R-SCREEN]`'s screen applies to a candidate *mechanism*, and a known-wrong LP input is not a candidate
mechanism competing against a correct one. All six band values remain inside their tolerances.

**Diagnostics: identical non-zero row counts** — D1 25, D2 15, D4 71, D5 8, D9 5, D10 6. Checked
explicitly because a composite bundle's diagnostics pass **vacuously at zero rows**. D-4 still FAILS,
unchanged: **card R-be's day-selection half is untouched by this lane.**

**Rule 21 `[R-DOF]`: ZERO free parameters added.** `build_dof_ledger.py` rebuilt the ledger at HEAD
from this bundle's *own* config — the like-for-like baseline the rule asks for — and returned the same
**5 entries / 3 residual** with the same names. `--check` reads `current`.

---

## 4. G-DRIFT — recorded BEFORE the arm, and one classification CORRECTED AFTER

The audit (PRECOMMIT §2) classified 10 changed solve-path files. Eight were inert by inspection
(default-off gates, new modules behind them, additive CLI). Two needed proof and got it:
`_hydro_benchmark_is_923_only("SPP", y)` reads **False** in all three years (SPP is in neither
`EIA930_PS_FOLDED_INTO_WAT` nor `EIA930_PS_SPLIT_COMPLETE_FROM`), and keeper 10's **committed bundle
re-scored at this base reproduced its committed determination exactly** — zero LP. **Form 4 valid; no
control solve spent.**

**CORRECTION, owed on my own audit.** I argued `config/plant_taxonomy.py` was covered because keeper 10
re-scored identically. That was incomplete: the re-score reads keeper 10's **committed payload**, not a
rebuilt input store. The arm's `eia923` shared-input hash *did* move
(`58267fd3f822` → `7da41467dba7`) while **all seven other shared inputs are byte-identical**, because
`gov-hydro-seam-1` landed between keeper 10's basis and this base and repaired
`plant_taxonomy.classify_plant` so prime mover `PS` returns `OTHER` instead of falling through to
`hydro`. `data/raw` is unchanged between the two bases (`git diff` returns nothing), so this is a code
effect, not a data refresh.

**Measured rather than assumed, and separated rather than folded in:** it moves the **scored actuals**,
not the LP. On SPP the largest move in any class actual is **+0.023 TWh** (COAL_PRB 2023, 65.279 →
65.302) on ~300 TWh; **hydro does not move at all**; there are **zero status flips**. So it is a real
confound on any C1/C2 comparison against keeper 10, and a negligible one.

---

## 5. RETRIEVABILITY, RETENTION, AND WHAT IS **NOT** DONE

**The bundle is COMMITTED and pushed**, not stranded (rule 34 `[R-SHARD-PROMOTABLE]`): the registered
slim set + `hourly/` sidecars are on the branch, the **identical file set keeper 10 carries**. The full
125 MB bundle and its 23 MB input store are recoverable by immutable SHA (rule 33(d)):

```
git checkout 0b58650a323d4b2da2529511ba45dfb137cccb12 -- results/calibration/spp38_span
git checkout ea3458ff92280a41fb532bc5f23ea481c3b3e689 -- results/calibration/_shared/SPP
```

**REGISTRATION IS NOT PROMOTION, and this lane did not promote.** `keepers/SPP.json`,
`calibration-complete.json`, `prune_iso_runs.py` and the matrix keeper stamp are all **untouched**:
rule 31 `[R-RETAIN]` puts the promotion decision with the owner, and rule 35 `[R-PROMOTE]` (e) orders it
promote → verify → **then** delete. **`audit_keepers` E13 therefore reports the new run as
registered-but-unstamped**, which is the expected and correct state of an undecided promotion, not a
defect to tidy away.

**Rule 35(b), done before any prune could be contemplated:** the union of `years` over every SPP
sidecar is exactly **{2023, 2024, 2025}** — one registered run, nothing stamped `holdout.keeper`. The
new run covers that union, so a promotion would shrink no year set (rule 35(c)). *(`bench/SPP/` is
2023–2025 only, so SPP-30's 2019–2022 LMP coverage stays unscoreable. Not this lane's.)*

SPP holds **no `complete` and no `frontier`**, and this lane creates neither.

---

## 6. TWO LAUNCH-DISCIPLINE FAILURES IN MY OWN SHARD PROMPT — worth rule-32 coverage

Both cost real wall time and neither is covered by rule 32(c)'s checklist.

1. **The shard backgrounded its solve and ENDED ITS TURN**, going idle at "2023 LP in progress; ~1 min
   of ~8-10 min" with nothing pushed. The parent cannot read a cloud shard's disk, so that work was
   unreachable. Recovered by waking it with a **poke-only Routine bound to its session**
   (`create_trigger` + `fire_trigger` with `persistent_session_id`) — there is no `send_message` for
   cloud sessions in the parent's toolset and they do not appear in `ListAgents`. **Cost ≈ 30 min.**
   Rule 32(c) should require, verbatim in every shard prompt: *"run the solve in the FOREGROUND; never
   `nohup`, never `&`, and never end your turn while it is in flight."*
2. **The `_shared/` input store is not part of "the bundle".** `results/calibration/_shared/<ISO>/`
   holds the content-addressed EIA-923/930/CAMPD inputs `meta.json` references, it is separately
   gitignored, and **registration fails without it** (`build_payload` → `bundle_input_path` → `None`).
   Rule 34(a)'s negation recipe covers only the out-dir. **Cost: a second round-trip.** A shard prompt
   must negate **both** paths.

Also worth recording: `git checkout <sha> -- <path>` **stages** the files even when the path is
gitignored, so a parent fetching a shard bundle must `git reset HEAD -- <path>` immediately or it will
carry 125 MB into its next commit.

---

## 7. RULES

- **32(a) `[R-SHARD]`** — the parent ran **zero** LP. All zero-LP work (census, order-dependence probe,
  differencing, scoring, registration) stayed in the parent. **32(b)** — one registrable run, one shard,
  one invocation, one bundle; no per-year fan-out.
- **33 `[R-SHARD-ARCHIVE]`** — the shard was archived only after fetch + checkout + **verify** (config
  signature and the 2023 identity). Recovery pinned by full SHA above. **One shard launched, one
  archived, none left alive.** Its branch `claude/spp-38-span` is **deliberately retained** under
  33(f)(3): it carries the only copy of the per-plant `dispatch/` layer a promotion would register, and
  rule 31 forbids destroying that while the promotion is open.
- **34 `[R-SHARD-PROMOTABLE]`** — the bundle was pushed, not stranded; `git ls-tree` confirmed 34 files
  before archiving; retrievability is stated in §5.
- **1 `[R-STRUCT]` / 13 `[R-MEASURED]`** — `offer_curve_by_group` byte-identical, SHA-256 verified twice;
  not re-cut, not swept, not examined against any gate. No adder, offset, haircut, proxy or rescaled input.
- **23 `[R-FROZEN-DERIVE]`** — `campd-unit-outages-short-SPP.csv` and `thermal_tranches_SPP.csv` neither
  re-derived nor touched.
- **C3c** — untouched, not gated on, still the accepted model-class limitation SPP-29 measured.
- **`[R-HOLDOUT]` removed 2026-09-09** — no SPP number here is a certified out-of-sample skill claim;
  `CALIBRATED` is a rubric determination on years that have been iterated against.

## 8. INHERITED, CORRECTED

The handoff's standing facts were partly stale and are corrected on the record:

- **`offer_curve_by_group` is NOT "uniform 0.93"** — it carries **18 distinct values** (0.5 … 15.0).
  The SHA-256 matched and is the binding check; the "uniform 0.93" phrasing was not used as a gate.
- **`results/calibration/spp36_2025` is no longer a parity-gate offender** — it was pruned upstream by
  `654c561a` ("Prune non-keeper runs and dead solve output to keeper-only retention"). **SPP now has
  ZERO offenders.** The three remaining are CAISO's (`caiso279_ablate_dswcouple_{2022,span}`) and
  NYISO's (`nyiso230_arm_y2022`) — raised, not acted on. FINDING-spp-37 §4c's evidence remains
  recoverable at its recorded pin `18ef91756ac84482a78ea719c2fc8d57ec7d5cf5` (verified: resolves, 7 files).
- **An anomaly in keeper 10's promotion note, reported and not chased.** It records C3b
  0.1760 / **0.1658** / **0.1878**; the scorer reads 0.176 / 0.175 / 0.175 and an independent
  reconstruction off the committed sidecars gives 0.1760 / 0.1722 / 0.1753. C3a reproduces to 4 dp on
  all three instruments, so the bundle and bench agree — it is the note's 2024/2025 **C3b** figures
  that are not reproducible from the committed artifacts. Nothing turns on it (all PASS against ≤ 0.20).

---

## 9. THE PROMOTION QUESTION — ASKED, AND ANSWERED: **PROMOTED**

**OWNER RULING, in session, 2026-09-13: PROMOTE.** `2026-09-13-spp-38-vintage-cache` is **SPP
keeper 11**. Executed in the same session, in rule 35 `[R-PROMOTE]` order:

| step | rule | done |
|---|---|---|
| year set enumerated **before** any delete | 35(b) | {2023, 2024, 2025}; incoming keeper covers it, so 35(c) holds — no year set shrinks |
| `keepers/SPP.json` re-keyed | 35(a) | keeper 10's note preserved verbatim as `prior_keeper_note_spp36`; keeper 9's dropped; predecessors cited **by lane**, never by run id |
| `calibration-complete.json` | — | **deliberately untouched**: SPP has no entry, and creating one would create a `complete` marker, a separate owner act this lane is forbidden to take |
| `audit_keepers --iso SPP` **between** promote and prune | 35(e) | incoming three stores resolve; E13 correctly re-pointed at keeper 10 |
| `prune_iso_runs.py --iso SPP` | 35(a), (d) | keeper 10's three stores removed together; **`--force-uncite` NOT needed and NOT used** — no governance file blocks it, the only citation is the matrix shard, which is reported but non-blocking |
| matrix keeper + gates stamp | 28 | **stamps only** — cell verdict counts byte-identical before and after (K 9, R 6, I 3, G 0, O 2, U 155) |
| `mechanism-testing-matrix.md` §5.7 prose header | 28 | re-stamped; it was **two generations stale** because keeper 10's promotion never discharged that duty — stated in the new header, not papered over |
| `build_status.py --iso SPP` | 15 | re-cut |
| **verified after** | 35(f) | **`audit_keepers --iso SPP` PASSES, 0 failures / 0 warnings.** Parity gate: 3 offenders, all CAISO's and NYISO's; **SPP zero** |

Keeper 10's bundle is recoverable at `f6e3ed374682059291605b0d425b81c399baaa96` (17 files); git
history is the record, exactly as rules 15 and 35(d) say.

**THE SHARD BRANCH `claude/spp-38-span` COULD NOT BE DELETED AND IS STILL THERE.** Rule 33(f)
steps 1–3 were done — no unique record on it (every doc is inherited from `main`), the bundle's
registered layer is on `main` — but `git push origin --delete` returns **HTTP 403**: this session's
credential can create and update refs but not delete them, and the GitHub MCP server exposes no
branch-deletion tool. This is exactly what rule 33(f)(5) documents, including the misleading
`send-pack: unexpected disconnect` → `Everything up-to-date` that masks the 403 until you force
HTTP/1.1. **Reported rather than claimed as done.** One upside: the recovery pins in §5 stay live.

## 9b. WHAT THE PROMOTION DOES NOT DO

**Next shorthand: spp-39.** The queue (R-be day selection → R-ba merit inversion → R-bc
price-forming curtailment) was **not** entered: card A consumed the lane, which is what the handoff
ordered, and every queue card reasons off per-plant 2024/2025 thermal behaviour that only now has a
correct basis. **Rule 29(b) form 4 for SPP now differences against keeper 11**; against keeper 10 it
is void for 2024/2025, and keeper 10 is no longer registered.

<!-- superseded question, kept so the decision's basis is legible -->
## 9c. THE RECOMMENDATION AS IT WAS PUT (superseded by the ruling above)

**Recommendation: promote `2026-09-13-spp-38-vintage-cache` to SPP keeper 11.** Keeper 10's 2024 and
2025 numbers are computed on an LP input proven wrong; this run is its own recipe on a correct one,
with an identical determination and an exactly-reproduced 2023. Leaving keeper 10 designated means
SPP's dashboard keeps publishing 2024/2025 numbers we have shown are built on a stale fleet.

**Nothing is lost if the answer is no or late:** the bundle is committed and pushed, not gitignored and
not on ephemeral disk. Recovery costs zero re-solves either way.

On a **yes**, the promoting session does, in one session (rule 35):
1. re-key `frontend/data/backcast/keepers/SPP.json` to `2026-09-13-spp-38-vintage-cache`;
2. re-key SPP's `calibration-complete.json` entry;
3. `scripts/audit_keepers.py --iso SPP` (E1) to verify the incoming three stores resolve — **before**
   any delete (rule 35(e));
4. `scripts/prune_iso_runs.py --iso SPP` (`--force-uncite` is the intended route here, rule 35(d)) to
   remove keeper 10's three stores;
5. re-stamp `docs/codebase-site/data/mechanism-matrix/SPP.js` keeper id + open gates (**stamps only —
   no cell verdict moves**, rule 28 does not reach a cache key);
6. `scripts/build_status.py --iso SPP`, then delete branch `claude/spp-38-span` (rule 33(f)(3) releases
   it only once the promotion is decided).

**Next shorthand: spp-39.** The queue (R-be day selection → R-ba merit inversion → R-bc price-forming
curtailment) was **not** entered: card A consumed the lane, which is what the handoff ordered, and
every queue card reasons off per-plant 2024/2025 thermal behaviour that only now has a correct basis.
Until a promotion, rule 29(b) form 4 for SPP 2024/2025 should difference against **this run**, not
keeper 10.
