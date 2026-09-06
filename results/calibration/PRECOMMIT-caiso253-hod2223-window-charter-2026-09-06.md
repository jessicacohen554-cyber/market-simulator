# PRECOMMIT — caiso-253: THE hod 22–23 GAP. A WINDOW CHARTER ON TWO FROZEN DERIVES: which of the two at-hub WEIM clean-transfer windows owns hours 22–23, decided by the discriminator the two constructions THEMSELVES name — and a registered branch that arms NOTHING.

**Session caiso-253, 2026-09-06.** Branch
`claude/caiso-backcast-calibration-253-9dgorn` off `main` `82f79693`.
Keeper **`2026-09-05-caiso-252-b1-notrim`** (`caiso252_b1_notrim`),
DETERMINATION **CALIBRATED** — 8/8 scored criteria hold, fails 0, the single
ledgered caveat C3c 2024. Rule 22 `[R-HOLDOUT]`: **2023–2025 only**; CAISO
holds NO `complete` and NO `final` marker; the holdout spend freeze is ACTIVE.

**Pushed BEFORE any measurement of the object and before any arm is coded.**
Nothing below has been computed. The phase-0 numbers, the screen year and the
arm (if one is admissible) enter by a registered ADDENDUM.

---

## §0 — THE OBJECT

`FINDING-caiso252` §11 ranks it first, and the handoff carries it as object A:
**hours 22 and 23 carry NO at-hub clean-transfer capability row, by
construction.** The model's CC_REGULAR over-generates **+1,619 / +1,617 MW**
at hod 22 / 23 in 2025 (§2.2 of that finding — the two largest CC error hours
of the whole day), and the caiso-252 arm moved them by **−66 MW**: it could
not reach them, because its window stops at 21.

### §0.1 — Why the gap exists: two frozen windows that do not tile the clock

Two at-hub WEIM/EDAM clean-transfer rows carry the CAISO south corridor, and
each was chartered independently:

| row | window | scoping | depth statistic | window fixed by |
|---|---|---|---|---|
| `DSW_overnight_clean` (caiso-93) | hod **0–5** | **UNCONDITIONAL** | p95 corridor net import over ALL overnight hours | FINDING-caiso91c/92b, *before any spread was measured* |
| `DSW_daytime_clean` (caiso-94) | hod **6–21** | caiso-87 surplus-trigger **OFF** | p95 over the daytime trigger-OFF window | FINDING-caiso94, *before the depth was measured* |

`0–5 ∪ 6–21` is **22 hours**. The `spec.py` comment on the daytime bounds
says the band "Complements the caiso-93 overnight window (hod 0-5)" — it does
not. Neither boundary was ever *tested* at 22–23: caiso-91c sliced the day as
overnight 0–5 / belly 10–14 / evening 17–21 for a CC-cycling decomposition,
and caiso-94 sliced it as morning ramp / belly / afternoon 15–17 / evening
peak 18–21. **Hours 22–23 fell between two independently-chosen analytic
blocks. That is a construction artifact, not a measured boundary** — which is
what makes this a *structural* object under rule 1 `[R-STRUCT]` rather than a
residual.

### §0.2 — The discriminator is NOT mine to choose: the two constructions name it

The ONE structural difference between the two rows is their scoping, and the
code states the ground for each in its own words (`interchange/spec.py`,
`interchange/caiso.py` docstrings, both quoted here from HEAD):

* overnight is unconditional **because** "the caiso-87 surplus tranche cannot
  cover this: its hub-below-gas-floor trigger fires in only **1.2-3.6 %** of
  2024/25 overnight hours (the no-wedge state overnight is UNCONDITIONAL, not
  hub-state-gated)";
* daytime is trigger-OFF scoped **because** "daytime caiso-87 is
  coverage-RICH (**66-90 %** trigger-ON in the belly), so this leg is scoped
  to the COMPLEMENT to stay DISJOINT from caiso-87".

So the charter's question — *which window owns 22–23* — has a **measured
answer that exists independently of any residual**: the caiso-87 surplus-
trigger ON share at hod 22 and hod 23. That measurement, not the C4 or C3a
residual, decides the branch. **G-WINDOW below is registered with all three
of its outcomes, including the one that arms nothing.**

### §0.3 — Admissibility

* **Rule 1 `[R-STRUCT]`.** The object is a window that does not tile the
  clock; the mechanism is the WEIM clean-transfer construction the lane has
  carried since caiso-87/93/94. No new mechanism, no adder, no proxy. The
  residual tells me the gap is *material*; it plays no part in whether the
  gap is *real* or in which branch the charter takes.
* **Rule 13 `[R-MEASURED]`.** The depth is a frozen percentile of a measured
  corridor series; the window is the complement of two upstream-fixed
  windows; the hub price is measured and forward-substitutable; the CARB
  EIM/EDAM attribution structure regenerates for a forward year. No same-year
  outcome enters.
* **Rule 14 `[R-ACCURATE]`.** The 22–23 admissibility is *newly* measured
  here — neither finding covers those hours. If it fails, the charter closes
  the object.
* **Rule 19 `[R-ONE-MECH]`.** The arm, if any, **widens ONE existing row's
  window**. It does NOT add a third row and it does NOT stack on the
  daytime row (which is 0 MW at 22–23 by construction). The daytime injector
  already nets its depth against the overnight row's armed capability, so no
  hour double-carries.
* **Rule 23 `[R-FROZEN-DERIVE]`.** The derive's thresholds (CV ≤ 0.20,
  LOYO ≤ 25 %), statistic (p95) and corridor series are FROZEN and untouched.
  Only the **population** changes, and the population is *implied by the
  window*, not chosen — this is the same window-match re-derivation caiso-97
  performed when it trimmed the daytime window (`--evening-trim`), which the
  spec calls "the derive script's CRITICAL window-match rule".
* **Rule 5 `[R-NO-MAGIC]` / rule 21 `[R-DOF]`.** **The boundary carries ZERO
  degrees of freedom**: `{22, 23}` is the exact complement of `21` (frozen,
  caiso-94) and `0` (frozen, caiso-91c/92b). There is no boundary to sweep.
  The only new *values* are the re-derived measured depths.
* **Rule 25 `[R-ISO-SCOPE]`.** CAISO-only, gated, default off.
* **Rule 28(a).** The `import_hub_pricing` family cell is **K**; this is a
  window question inside an armed keeper mechanism, not a re-test of an
  `R`/`I`/`G` cell. The caiso-252 DO-NOT-REDO §12.3 requires exactly what
  this document is: *"never extend the daytime window past 21 or the
  overnight window below 0 to reach 22–23 **without a charter**"*.

### §0.4 — Direction hazard, declared NOW

More at-hub import at 22–23 → 22–23 λ falls → **C3a favourable** (the model
runs high). This would be the **EIGHTH consecutive favourable direction** for
this lane (caiso-241/242/243/246/246§5.2/251/252, now 253). Declared, as the
handoff requires. **C3a and C4 are EXCLUDED from the promotion basis in both
directions** and from every gate below.

---

## §1 — THE GATES, WITH THEIR FALSIFIERS (all zero-LP, all pre-registered)

### G-REPRO — the instrument is the committed record
The probe reproduces, from the keeper's committed `hourly/` sidecars and the
committed benches, the caiso-252-reported hod-22–23 CC_REGULAR error
(+1,619 / +1,617 MW, 2025) to **≤ 25 MW**. A miss means my instrument is not
reading what the finding read, and everything downstream stops.

### G-WINDOW — WHICH WINDOW OWNS 22–23 (the charter's decision, three branches)
Measure the caiso-87 surplus trigger (`PaloVerde < HR_DSW_CCGT ×
SoCal citygate weekly + remote VOM`, the injector's own predicate) ON share
at **hod 22 and hod 23 separately**, per year. Decided on **2024 and 2025**,
with 2023 reported but not decisive — exactly as caiso-93 §3 did, because
2023's overnight 26.4 % ON share is the documented rule-14 SoCal-citygate
misalignment (the 2023 gas spike inflates the floor), not a coverage fact.

| branch | condition | consequence |
|---|---|---|
| **STARVED** | ON ≤ **10 %** at BOTH hours in BOTH 2024 and 2025 | 22–23 belong to the **caiso-93 UNCONDITIONAL overnight** construction — the arm is a window extension of `DSW_overnight_clean` |
| **RICH** | ON ≥ **30 %** at either hour in either year | 22–23 belong to the **caiso-94 trigger-OFF daytime** construction — the arm would be a daytime-window extension, and is **NOT taken this session** (it re-opens the caiso-97 evening trim's own window one hour past where caiso-252 just landed it; that needs its own charter and its own overshoot falsifier) |
| **AMBIGUOUS** | anything between | **NO ARM.** The charter reports the ambiguity and the session ends on the finding |

The 10/30 thresholds are the two constructions' own measured signatures
(1.2–3.6 % starved; 66–90 % rich) with a deliberately wide dead band between
them, so a middling number CANNOT be resolved in the convenient direction.

### G-WEDGE — is an at-hub clean transfer ADMISSIBLE at 22 and at 23?
The caiso-93 §2 / caiso-94 §2–3 gate, re-run at **hod 22 and hod 23
separately** (neither finding covers them), unconditional over all such
hours, DA and RT, per year, on the measured CAISO system LMP against the
PALOVRDE hub with `CAISO_IMPORT_DELIVERY_BASIS`:

* **G-WEDGE-1** median delivered-basis spread (`actual − hub×(1+loss) − wheel`)
  **≤ +$4** (caiso-94's G1) — one-sided; fails only if actual clears ABOVE
  delivered parity;
* **G-WEDGE-2** wedge-consistent share (spread ≥ wedge − 2) **≤ 6 %** (the
  caiso-94 measured daytime range was 0–6 %);
* **G-WEDGE-3** raw-hub discriminator median (`actual − PALOVRDE`) within
  **[−2, +4]** — raw-hub parity, the caiso-94 §3 "IMPORT-LEVER admissible"
  band. Strongly negative ⇒ a battery/ramp floor sets that price and NO
  import can (caiso-94 §3); strongly positive ⇒ a real wedge, leave alone
  (rule 1).

**ALL THREE, BOTH HOURS, ALL THREE YEARS, OR NOTHING.** The arm is the whole
`{22, 23}` block or it does not exist: taking only the hour that passes would
be choosing a boundary on a measurement rather than inheriting one from a
frozen window, which is the window-shopping caiso-252 §12.3 forbids. A
one-hour split is reported as a **finding**, and arms nothing.

### G-DEPTH — the frozen derive, re-run over the window it must price
`derive_caiso_overnight_clean_depth.py` with the window extended
(`--late-evening`: hod ≥ 22 OR hod ≤ 5), **same frozen statistic (p95), same
frozen gates (CV ≤ 0.20, LOYO ≤ 25 %), same corridor series
(`corridor_net_import`, EIA-930 CISO DIBAs, model clock)**. Passes iff both
gates pass on their frozen thresholds. Nothing is iterated; a FAIL closes the
object and is reported.

### G-FOOT / G-DIR / G-OVERSHOOT / G-NOBREAK — the rule-29 screen (structural, STOP-only)
Registered in form now; their year is named in the Addendum from the phase-0
footprint. **The target residual is excluded from every one of them.**

* **G-FOOT** — ≥ 90 % of the overnight row's ADDED energy (arm − keeper)
  lands in hod 22–23; no non-WECC row's capability differs; hod 0–5
  capability moves only by the depth re-derivation.
* **G-DIR** — the row carries energy at 22–23 where the keeper's is **zero by
  construction**, AND CC_REGULAR's 22–23 dispatch FALLS.
* **G-OVERSHOOT** — the caiso-97 objection, re-armed as this arm's own
  falsifier at the hours it actually touches: the arm's hod-22–23 net import
  lands within **[measured − 0.25 TWh, measured + 0.40 TWh]** of the EIA-930
  hod-22–23 total. **This band is NOT re-chosen**: it is caiso-252's
  registered [−0.5, +0.8] TWh over four hours held at the same per-hour
  tolerance (−342 / +548 MW) over two hours. **Above the top of the band the
  arm is REFUSED regardless of what C4 or C3a do.**
* **G-NOBREAK** — no C1 class row moves from inside its band to outside it;
  the load-weighted price stays inside the ±10 % C3a band.
* **G-HOLDOUT** — every solved year ∈ {2023, 2024, 2025}.
* **G-C6/C8/DOF** — C6 attested, C8 PASS, and the DOF ledger's **residual
  count does not rise** (a measured depth on a frozen statistic is not a free
  parameter; the ledger entry, if any, is identified by the derive).

---

## §2 — PREDICTIONS, WRITTEN TO BIND

Registered before any of the object is computed. The uncomfortable reading is
stated for each.

| # | prediction | uncomfortable reading if it fails |
|---|---|---|
| **P-1** | G-REPRO reproduces the two committed CC hod-22/23 errors within 25 MW | my instrument is not the finding's — stop |
| **P-2** | G-WINDOW reads **STARVED**: caiso-87 trigger ON ≤ 10 % at both 22 and 23 in 2024 and 2025 (no solar anywhere in WECC at 22–23 Pacific, so the West-wide surplus signature should be as absent as at 0–5) | RICH ⇒ the hours are daytime-construction hours and this session arms nothing; AMBIGUOUS ⇒ the two constructions do not cleanly partition the clock and the whole two-window design needs re-charting |
| **P-3** | G-WEDGE passes at BOTH hours in ALL THREE years | a wedge at 22–23 means reality's marginal import there IS carbon-paying and the model's wedge is CORRECT (rule 1: leave alone) — the object closes and the CC over-run at 22–23 is a MODEL-SIDE object (commitment/storage), not an import object |
| **P-4** | G-DEPTH passes and the hod-22–05 depth lands **within ±8 % of the committed hod-0–5 depth** in every year (5,870 / 6,205 / 6,487 MW) — 22–23 should look like the rest of the night | outside that: 22–23 are NOT overnight-like in the corridor flow either, which contradicts P-2's branch and is evidence the hours belong to neither window |
| **P-5** | the keeper UNDER-imports at hod 22–23 vs EIA-930 in 2025 by **0.3–1.2 GW** (the §3.1 night block read −0.2…−1.7 GW over 22–05) | if the keeper is already AT or ABOVE measured at 22–23, then the CC over-run there is NOT an import shortfall and the caiso-252 mirror does not extend to these hours — the object closes |
| **P-6** | phase-0 added capability at 22–23 is **1.5–4.0 GW/hour** and the largest-footprint year is **2025** | a much smaller footprint means the firm block + the re-derived depth already cover 22–23 and the arm is inert before it is solved |
| **P-7** | if solved: CC_REGULAR's 22–23 dispatch falls by **≥ 0.25 TWh** in the screen year, and the 0–5 block moves by **< 0.15 TWh** (the depth re-derivation is the only thing that reaches it) | a large 0–5 move means the re-derived depth, not the new hours, is doing the work — the arm would then be a depth change wearing a window's clothes |
| **P-8** | if solved: G-OVERSHOOT passes — hod-22–23 net import lands inside the registered band | above the band: caiso-97's objection is right at these hours too and the arm is REFUSED even if every scored criterion improves |

**I expect P-2 and P-3 to hold and I am registering the branches that make
holding them non-automatic.** P-5 is the prediction most likely to kill the
object cheaply, and it is measured in phase 0 before anything is coded.

---

## §3 — THE ARM, IN FORM (only if G-WINDOW=STARVED and G-WEDGE and G-DEPTH pass)

ONE new `ScenarioConfig` field, **CAISO-only, default `False`**, so every
other ISO and every existing keeper replays byte-identical:

    caiso_dsw_overnight_clean_late_evening: bool = False

Armed, `inject_caiso_dsw_overnight_clean`'s window predicate becomes
`hod ≥ CAISO_OVERNIGHT_CLEAN_HOD_MIN_LATE (= 22) OR hod ≤
CAISO_OVERNIGHT_CLEAN_HOD_MAX (= 5)` and the depth dict becomes the
G-DEPTH re-derivation over that population. Everything else is untouched:
unconditional scoping, raw Palo Verde hub, EF 0, no wheel, `pmin` 0 (a
capability, never a floor — no D-2 row), the same per-hour netting against
firm + surplus, the same measured-hub arming (the 2023 Jan–Feb OASIS gap
hours stay 0 MW), the corridor ATC envelope still caps delivered flow.

**Rule 28(c):** the new field gets its matrix row in
`docs/codebase-site/data/mechanism-matrix.js` **plus a cell line in EVERY
ISO shard** in the same PR (`U` everywhere but CAISO — rule 25: a verdict
transfers to no other ISO).

**No second flag, no third row, no depth outside the frozen derive, no touch
of the daytime window, no calendar or season gate, no tuning under any
outcome.**

---

## §4 — G-DRIFT (rule 29(b)): keeper `fa23c1f7` → HEAD `82f79693`, recorded BEFORE anything is solved

The keeper's `run_config.json` records `git.sha` **`fa23c1f7`**; it is
reachable at HEAD (`git cat-file -t` → commit), so the audit runs on the
keeper's own basis and no FINDING-stated fallback is needed.

`git diff fa23c1f7 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source
data/raw/reference`: **23 files, +1,763 / −227.** Every hunk is **INERT for a
CAISO backcast**, with its reason. The keeper's recipe facts the audit leans
on, read from its own `run_config.json`: `mode="backcast"`, `iso="CAISO"`,
`rps_enabled=False`, `miso_clean_tier_rows=False`, `carbon_price=0.0`
(program-resolved posture).

| change | why it cannot reach this ISO's backcast solve |
|---|---|
| `data/raw/_validation-source/actual_lmp.json` (+66) | both hunks (old lines 1257, 1316) sit inside the **PJM** block — the CAISO block opens at old line 1319 — and add `rt_lw`/`da_lw` load-weighted keys to PJM years only; **verified by locating the enclosing ISO key in the pre-change blob**, not by the `src` string alone |
| `config/scenarios.py` (+216) | **THREE fields ADDED** (`federal_ces_target_by_year=None`, `federal_ces_acp_usd_per_mwh=None`, `unit_outage_extract_basis_share=False`) and **ZERO existing defaults changed** — verified programmatically by parsing every field default at both shas and diffing the maps, not by reading the diff |
| `model/lp/{__init__,model,rows}.py` (+274) | the clean-tier family: a vector crediting spec and the SCN-WS2a relaxation of the "clean rows require the RPS region family" coupling. The family builds rows only when `clean_region_zone_mask is not None`; with `rps_enabled=False` and `miso_clean_tier_rows=False` the runner's single resolver returns `None`, so no row exists and the tuple-form path is untouched anyway |
| `runner.py` (+112), `policy/{clean_tiers,federal_ces}.py` (+287) | `federal_ces_target_row_active` is False at `federal_ces_target_by_year=None`, so `append_federal_ces_region` **returns its input object unchanged**; with no state family that input is `None` |
| `policy/cap_and_trade.py` (+70) | a NEW `carbon_mc_column` lifted verbatim so the FORECAST orchestrator carries the backcast's partial-footprint gate; `scripts/run_calibration.py` — the backcast orchestrator — **is not in this diff at all**, so the backcast path still runs its own unchanged block |
| `model/interchange/spec.py` (+24) — the corridor-inventory border adder now prices off `resolve_carbon_price` | CAISO-specific and therefore audited to the consumer: the value feeds ONLY `Corridor(carbon_adder=…)`, and `InterchangeSpec.corridors` is **written and never read anywhere in `src/` or `scripts/`** (grep for `.carbon_adder` reads returns nothing). The LP's border adder is `runner.py`'s own `wecc_border_carbon_adder(resolve_carbon_price(...))`, unchanged |
| `data/cod_ramp.py` (+121) — vectorized `_reduce_cod_groups` | `cod_ramp_enabled=True` makes this a **LIVE-path** file, so the claim was not accepted on its docstring: `tests/unit/data/test_cod_ramp.py` — which gates the reducer on dict equality against the shipped loop — **was RUN at HEAD: 46 passed, 8 subtests passed** |
| `data/{outages,fleet/arrays}.py` (+153) | the `unit_outage_extract_basis_share` leg; the field is absent from the keeper recipe and defaults `False`, so `_extract_basis_index` never runs and `extract_basis=None` selects the old path verbatim |
| `config/constants.py` (+114) | every hunk is inside `DATACENTER_ADDITIONS_MW` / `DATACENTER_ZONE_SHARE`, whose only consumer is `data/datacenter.py` (forward demand growth); a backcast takes measured EIA-930 demand |
| `results/{emissions,export,outputs}.py` (+236) | additive emissions grain: `emissions_by_fuel_mt` / `emissions_by_zone_mt` / `import_co2_mt_reported`, the last **reported-only and never inside `emissions_mt`** (grep confirms the `emissions_mt` computation is untouched); `DispatchResult.emissions` is derived on READ, and the three `emissions is not None` branches live in the forecast/crossover/capacity-hindcast scorers, none of which scores a backcast |
| `matrix.py` (+60) | `scalar_metrics`/`PRIMARY_METRIC` for the scenario matrix; not on the calibration solve path |
| `scripts/lib/bench_stamp.py` (+68) | owner ruling R-AS: the part fingerprint hashes the **AST** instead of raw bytes — a provenance stamp, no payload |
| `data/{benchmark_corridor,offer_curves,reserve_requirements}.py` | a dead-code removal + docstring; a ruff reformat of one dict comprehension; a trailing blank line |
| `scripts/run_calibration_full.py` (+173) | timing-log relocation (post-solve) + `_band_categorical`, a per-distinct-id rewrite of the class-band sidecar's band column claimed element-wise identical. **This is the ONE claim not yet verified**; it is verified empirically on the keeper's own unit-id population in phase 0, BEFORE any solve, and the result is recorded in the Addendum |

**Conclusion: G-CTRL form 4 is VALID at this HEAD — the committed keeper
`caiso252_b1_notrim` IS the control, and NO control solve is spent** (owner
rule 29(b)). As at caiso-251/252 this is a reading of code and inherits my
reading; it is falsifiable by re-running the same diff.

---

## §5 — RULE 29 `[R-SCREEN]`, AS IT APPLIES HERE

* **Phase 0 first (zero LP).** The two-rebuild footprint (extending
  `scripts/probes/_caiso252_evening_trim_phase0.py`), the model-vs-EIA-930
  hod-22–23 import gap and CC error from committed sidecars, and the four
  measured gates above. **An arm that fails any of them never reaches a
  solve.**
* **The screen year is named in an ADDENDUM before the screen runs**, and it
  is the year the mechanism's **own measured footprint is largest** (added
  armed capability × hours, then energy clearing at the keeper's committed
  duals) — **never** the year with the largest residual. The owner may name
  it instead.
* **The screen gate is STRUCTURAL and STOP-ONLY** (G-FOOT / G-DIR /
  G-OVERSHOOT / G-NOBREAK). It may kill the arm; it may never promote one; it
  never contributes to a determination; **C4 and C3a are excluded from it.**
* **The full span only if the screen clears**, as ONE
  `--year 2023 2024 2025` invocation and ONE bundle (rule 16 `[R-ALLYEARS]`).
  The screen bundle is a throwaway probe: never registered, never quoted as a
  keeper number, its numbers extracted to a committed JSON, and **DELETED
  before the PR merges** (rule 29(c)).
* **No control solve** (rule 29(b), G-CTRL form 4 per §4).

---

## §6 — STOP RULE

1. **G-WINDOW = RICH or AMBIGUOUS ⇒ NOTHING IS ARMED.** The session ends on
   the finding, the keeper is unchanged, and the object is handed on with its
   measured branch recorded.
2. **G-WEDGE failing at either hour in any year, or on any of its three legs,
   ⇒ NOTHING IS ARMED**, and the CC over-run at 22–23 is re-named as a
   model-side object.
3. **G-DEPTH failing on its frozen gates ⇒ NOTHING IS ARMED.** The gates are
   not re-thresholded, the statistic is not changed, and no alternative
   corridor series is tried (that is gate-shopping — caiso-93 §3's own
   prohibition).
4. **P-5 falsified (the keeper is not short of import at 22–23) ⇒ NOTHING IS
   ARMED**, whatever the CC error there does.
5. G-FOOT / G-DIR / G-OVERSHOOT / G-NOBREAK failing on the screen ⇒ the
   remaining years are never spent; the numbers are extracted and the bundle
   deleted.
6. **No gate is re-run to a pass or redefined after its result.** No second
   flag, no window other than `{22, 23}`, no partial-hour arm, no depth
   outside the frozen derive, no tuning under any outcome.
7. Every number this session will ever cite from a screen or control bundle
   lives in this document's Addendum or the FINDING, never only in a parquet.

---

## §7 — DELIVERABLES

This PRECOMMIT (pushed first); a phase-0 probe + committed JSON; a registered
ADDENDUM carrying the measured gates, the branch taken, the screen year and —
only if every gate passes — the arm exactly; a FINDING; the
`docs/calibration-log/caiso.md` entry; the rule-28 matrix duties (a new
mechanism row + a cell in every shard IF a field is added, the CAISO cell +
evidence either way); and, if an arm is promoted, the rule-15 same-session
registration with the full rule-28 stamp set.

**Under every branch except the one where all four gates pass, the deliverable
is a finding and an unchanged keeper — and that is a result, not a failure.**
