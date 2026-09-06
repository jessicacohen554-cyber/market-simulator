# ADDENDUM to PRECOMMIT-caiso253b — caiso-254: the G-DRIFT delta audit, and the rule-29 SCREEN the partition repair must earn before it reaches a solve

**Session caiso-254, 2026-09-06.** Branch
`claude/caiso-253b-backcast-calibration-3i1wj1` off `main` `fbef3a91`.
Keeper **`2026-09-05-caiso-252-b1-notrim`** (`caiso252_b1_notrim`,
`git_sha` `fa23c1f7`) UNCHANGED, DETERMINATION **CALIBRATED**. Rule 22
`[R-HOLDOUT]`: 2023–2025 only; no `complete`/`final` marker; freeze ACTIVE.

**Pushed BEFORE G-BIMODAL is scored** — before `--gate` is run and before any
statistic of the bid population exists in this session. The parent
`PRECOMMIT-caiso253b-offer-surface-contamination-2026-09-06.md` (merged, PR
#4927) registered G-BIMODAL and is UNAMENDED: its antimode window
[10.9, 12.5], its capacity bracket [1.5, 4.5] GW, its stop rule and its
predictions P-1…P-7 stand exactly as written and **nothing here relaxes any of
them**. This document adds only the two things that PRECOMMIT expressly
declined to authorize — its §4 stop rule 6, "**No solve is earned by this
document**" — namely the drift audit and the screen.

---

## §1 — G-DRIFT: `82f79693` → `fbef3a91`. Every hunk INERT for a CAISO backcast, three of them VERIFIED rather than asserted

Rule 29 `[R-SCREEN]` clause (b): the incumbent keeper's COMMITTED bundle is the
control (G-CTRL **form 4**), and the code-level drift audit — not a control
solve — is what establishes that form 4 is valid. The chain is complete in two
links: the keeper's own `meta.json` records `git_sha` **`fa23c1f7`**;
caiso-253 audited **`fa23c1f7` → `82f79693`** and found every hunk INERT, its
one open item (`_band_categorical`) closed by exhaustive branch verification
(FINDING-caiso253 §5.10). This session audits only the delta
**`82f79693` → `fbef3a91`**.

Command (rule 29(b)'s own form):

```
git diff 82f79693 fbef3a91 -- src/market_sim scripts/run_calibration.py \
  scripts/run_calibration_full.py scripts/lib data/raw/_validation-source \
  data/raw/reference
```

14 files, +672 / −22.

| file | Δ | verdict | reason |
|---|--:|---|---|
| `scripts/lib/forecast_parity_registry.py` | +83 | **INERT** | two `ParityDeclaration` rows in the FR-22 governance ledger. A registry read by the parity reporter; nothing on any solve path imports it. |
| `scripts/lib/holdout_policy.py` | +73 | **INERT** | `registration_refusals()` — owner ruling R-AZ's registration-time marker gate. Governance at the registration seam, not the LP. This run is train-tier 2023–2025, so it is additionally never reached. |
| `src/market_sim/config/scenarios.py` | +95 | **INERT** | one new field, `ccs_retrofit_fixed_cost_co2_scaling: bool = False`. Default-off, absent from the keeper recipe, and registered in the cache-key **drop map** at `"False"` (`scenarios.py:1941`), so the keeper's key is unmoved. Its only consumer is the forecast-only CCS retrofit step. |
| `src/market_sim/data/egrid_sheets.py` | +151 (new) | **INERT — VERIFIED** | §1.1. |
| `src/market_sim/data/fleet/eia860.py` | ±20 | **INERT — VERIFIED** | §1.1: `pd.read_excel` → `read_egrid_sheet` on the two boundary-HR-repair projections. |
| `src/market_sim/data/zone_assignment.py` | ±13 | **INERT — VERIFIED** | §1.1: same swap on `_plnt23()`'s raw-parse fallback. |
| `src/market_sim/model/capacity_evolution/ccs.py` | +94 | **INERT** | capacity-evolution **step 2**. A `mode="backcast"` run never enters capacity evolution at all; the branch is additionally behind the default-off gate above, which `__post_init__` refuses without `ccs_retrofit_capex_co2_scaling`. |
| `src/market_sim/pipeline/solve.py` | +12 | **INERT** | one `malloc_trim()` call at the P0→P1 seam. Returns heap the allocator **already considers free** to the kernel; it cannot reach a live object, so the LP's rows, bounds and objective are unchanged. |
| `src/market_sim/policy/constraints.py` | ±11 | **INERT** | module docstring only (G-S6 prose). |
| `src/market_sim/results/cache.py` | +41 | **INERT** | module docstring only — the SCN-MX-R-r2 cache-epoch ledger entry. No code line changed. |
| `src/market_sim/results/emissions.py` | ±14 | **LIVE — and confined to a stream no gate reads** | §1.2. |
| `src/market_sim/results/export.py` | +31 | **INERT** | additive `co2_cap_price_usd_per_t` / `_by_cap` / `n_co2_caps_binding` reporting fields, `0.0` / `[]` / `0` with no mass cap — which is every CAISO backcast. |
| `src/market_sim/results/outputs.py` | +16 | **INERT** | additive parquet metadata key `co2_cap_price`, read back with `.get` so an older cached year restores `None`, which is what it already meant. |
| `src/market_sim/utils/heap.py` | +40 (new) | **INERT** | the `ctypes` `malloc_trim(0)` helper above. |

### §1.1 — The eGRID mirror swap, VERIFIED not asserted

`egrid_sheets.read_egrid_sheet` replaces `pd.read_excel` on three solve-path
projections and claims to be "equivalent in every observable way … including
the resulting column order and dtypes". That claim is load-bearing for a CAISO
fleet build (`zone_assignment` sites every plant; `eia860`'s boundary-HR
repairs set heat rates), so it was **measured, not taken**: each projection was
read both ways and compared with `pd.testing.assert_frame_equal(check_exact=True)`
after a mirror write and a mirror hit.

| sheet | projection | shape | column order | dtypes | frame |
|---|---|---|---|---|---|
| `PLNT23` | `ORISPL, LAT, LON, PLHTIAN, PLNGENAN, PLHTRT` | (12612, 6) | identical | identical | **EXACT** |
| `UNT23` | `ORISPL, HTIAN, UNTYRONL` | (26186, 3) | identical | identical | **EXACT** |
| `PLNT23` | `ORISPL, LAT, LON, FIPSST, FIPSCNTY, BACODE` | (12612, 6) | identical | identical | **EXACT** |

The parquet round-trip is the only drift channel the design leaves open, and on
all three it is exact.

### §1.2 — The one LIVE hunk, disclosed at full magnitude

`results/emissions.py::import_co2_tons` now clamps negative energy out
(`np.maximum(gen_mwh, 0.0)`) so an EXPORT sink — which shares the `"import"`
fuel type and dispatches negative by construction — no longer credits the ISO
for the neighbour's generation. **CAISO has export sinks**
(`WECC_import_export_solar` −2,500 MW @ $8, `WECC_import_export_curtail`
−4,000 MW @ $0, all three years), so this is genuinely LIVE for CAISO: the
keeper's committed import-attributed CO2 was computed on the **pre-clamp**
construction and a new run's will not be.

Its scope, stated so it cannot be quietly widened later:

* it is **post-solve accounting** — the sole caller is
  `results/export.py:219`, after the LP has been solved and its duals read.
  It cannot change dispatch, prices, or any parquet the LP writes.
* the stream it touches is **`co2`, which is not in `CRITERIA`** — demoted to
  REPORTED-ONLY at rubric v2.9, so it contributes no status, no caveat budget
  and no reason line to any determination.

**Consequence, and the discipline it imposes on this session:** G-CTRL form 4
is valid for **every gated criterion** and for every number in §3's screen
gate. It is **NOT** valid for `co2`, so this session will not difference a new
run's import-CO2 against the keeper's committed number, and will not read a
`co2` movement as an effect of the partition repair. Because no screen gate and
no determination reads that stream, the LIVE hunk earns **no control solve**
under rule 29(b) — a control would buy nothing the gate table asks for. Had the
screen gated `co2`, it would have.

**⇒ G-CTRL form 4 STANDS. The keeper's committed bundle is the control. No
control solve is spent.**

---

## §2 — WHAT THIS SESSION MAY DO, AND IN WHAT ORDER

Unchanged from the parent PRECOMMIT's stop rule, restated because §3 hangs off
step 3:

1. Re-fetch the corpus. **P-1** scores coverage (1,095 / 1,096; 2023-06-01 the
   one genuine OASIS hole).
2. `--pass1` then `--gate`. **P-2** scores whether the classifier reproduces
   the frozen buckets (46 CC / 100 CT, ±3 resources and ±5 % capacity).
   **P-2 failing stops the session before any re-derive.**
3. **G-BIMODAL.** FAIL ⇒ nothing is re-derived, the bands stay, the disclosed
   note stands as a known bound, and that is the session's result. Only a PASS
   opens step 4.
4. The class-partition repair + the re-frozen artifact.
5. **Phase 0** (§3.1) → the screen year is NAMED → **the screen solve** (§3.2).
6. The full `--year 2023 2024 2025` bundle, ONE invocation, ONE bundle
   (rule 16 `[R-ALLYEARS]`), registered (rule 15 `[R-DASHBOARD]`).

---

## §3 — THE RULE-29 SCREEN, REGISTERED HERE BEFORE IT IS RUN

Rule 29 `[R-SCREEN]`: a 3-year CAISO replay is ~36 min of LP per arm. The
repair does not reach that until a one-year screen clears a **structural**,
**STOP-ONLY** gate.

### §3.1 — Phase 0, zero-LP, and it is what NAMES the screen year

Rule 29 clause (0): an arm with a computable pre-solve gate does not reach a
solve until that gate passes, and clause (1): the screen year is **the year the
mechanism's own measured footprint is largest** — **never** the year with the
biggest residual.

The estimator, fixed here:

> For each year *y* ∈ {2023, 2024, 2025}, build the CAISO gas offer arrays on
> the keeper recipe twice — once with the frozen `caiso_offer_curve_measured.json`
> and once with the repaired artifact — and report
> **F(y) = Σ_tranches |Δmc| × pmax** (MW·$/MWh) over every gas tranche, together
> with **X(y)**, the count of tranche pairs whose merit-order rank crosses.
> `Δmc` is evaluated at each year's own gas and CARB carbon price, which is what
> makes F differ across years.

**The screen year is `argmax_y F(y)`**, with X reported beside it. F and X
contain no price actual, no residual and no criterion — they are the
mechanism's own arithmetic. The value of `argmax_y F(y)` will be **written into
this document and pushed before the screen solve is launched**, so the naming
cannot be back-fitted.

If phase 0 measures **F ≈ 0 in every year** the repair is INERT and rule 29's
own exclusion applies: there is nothing to screen, and the session reports an
inert repair rather than spending an LP to confirm it.

### §3.2 — The screen gate: STRUCTURAL, STOP-ONLY, and the target residual is EXCLUDED

**S-1 — the dispatch response matches the pre-solve arithmetic.** The repair
moves two multipliers in *opposite* directions by construction (parent
PRECOMMIT §2.2): CT_PEAKER's median loses its high-HR tail so its multiplier
FALLS, and ST_GAS stops borrowing a base HR 9 % below its own so its multiplier
RISES. S-1 asks only that the screen year's class energy moves the way that
arithmetic says — **CT_PEAKER up, ST_GAS down** — and within a factor of 3 of
the displacement F(y) implies. FAIL ⇒ the mechanism is not doing what it
claims and the arm dies here.

**S-2 — footprint confinement.** Classes the repair does not reprice —
nuclear, hydro, wind, solar — move by **< 0.5 %** of their keeper annual
energy. (Storage and imports are price-responsive and are reported, not gated;
so are CC_REGULAR / CC_CHP, which the repair leaves on the CC bucket but which
re-dispatch against moved CT/ST offers.) FAIL ⇒ the change is reaching rows it
does not claim.

**S-3 / S-4 — C1 and C4 are STOP gates, and a flip ESCALATES rather than kills.**
A PASS→FAIL flip in C1 (class energy) or C4 (gas r / NRMSE — 2025 holds 0.003
of margin) **stops the screen**: the remaining two years are not spent. But it
does **not** by itself retire the repair, because the owner ruled this session
that *"if structural integrity improves but gates regress that may still be a
keeper"* — rule 1 `[R-STRUCT]`'s first half restated, and the caiso-230/231
precedent. A flip is therefore reported with its measured magnitude and **put
to the owner**, whose call it is. What the session may never do is spend the
full span on a flipped screen without saying so first.

**EXCLUDED FROM THE GATE IN BOTH DIRECTIONS:**

* **C3a is the target residual and is excluded entirely** — it can neither kill
  the arm nor promote it. Rule 29: "a screen that reads 'did C3a improve' is
  exactly the fitted-mechanism selection rule 1 forbids, done one year at a
  time."
* **Neither C3a nor C4 may PROMOTE.** Rule 29: the screen "may kill an arm; it
  may never promote one." An improvement in either is reported and does no
  work. The repair is adopted on **G-BIMODAL alone**, whatever the bands turn
  out to be and whichever way C3a moves — **including WORSE** (parent PRECOMMIT
  §2.2; caiso-230/231 armed the measured surface knowing it cost C3a
  +0.235 / +0.344 / +0.421 $/MWh).
* **`co2` is excluded**, per §1.2 — the one stream the control cannot carry.

**The screen bundle is a throwaway diagnostic probe**: never registered, never
a keeper, never quoted as a keeper number, its year re-solved inside the full
bundle (rule 29 clause (2)), and **DELETED from `results/calibration/` before
the PR merges** (rule 29 clause (c), owner ruling R-AV). Every number this
session will ever cite from it lives in the FINDING.

---

## §4 — PREDICTIONS ADDED HERE (the parent's P-1…P-7 stand unchanged)

| # | prediction | uncomfortable reading if it fails |
|---|---|---|
| **P-8** | phase 0 measures **F(2025) largest**, so 2025 is the screen year — CAISO's ST_GAS/CT fleet is most exposed there and 2025 carries the highest gas+carbon basis of the three | a different argmax is fine and is simply used; but F within ±10 % across all three years would mean the "largest footprint" criterion cannot discriminate, and the screen year would then have to be named on a stated tie-break rather than on a measurement |
| **P-9** | **S-1 holds**: CT_PEAKER energy RISES and ST_GAS energy FALLS in the screen year | if the signs come out the other way, §1 of the parent PRECOMMIT has the bias backwards and the repair is not the repair I described |
| **P-10** | **S-2 holds**: nuclear / hydro / wind / solar each move < 0.5 % | a non-gas class moving means the offer-array edit is not confined to the gas path — a plumbing defect, not a mechanism result |
| **P-11** | neither C1 nor C4 flips PASS→FAIL in the screen year | a flip is an owner escalation (§3.2), not a silent kill and not a silent proceed |

---

## §5 — STOP RULE (adds to the parent's §4; nothing there is relaxed)

1. Every clause of the parent PRECOMMIT §4 stands verbatim — G-BIMODAL FAIL ⇒
   nothing re-derived; P-2 FAIL ⇒ stop before any re-derive; no threshold in
   the derive retuned; no gate re-run to a pass or redefined after its result;
   per-year multipliers never armed; the frozen artifact never hand-edited.
2. **The screen gate as written in §3.2 is fixed.** It is not re-specified
   after F(y) is measured, and not after the screen is solved.
3. **The screen year is named by §3.1's estimator and by nothing else** — and
   is pushed before the screen solve launches.
4. **No `complete` marker is declared.** CAISO holds none; declaring one is an
   owner act (rule 22). Raised in the FINDING, not granted.
5. `frontend/data/forecast/program-status.json`'s stale top-level
   `isos.CAISO.keeper` is **not touched** — the owner ask is open (handoff item
   B) and this session asks before editing.

---

## §6 — DELIVERABLES

This addendum (pushed before `--gate` runs); the re-fetched corpus
(gitignored); `results/calibration/_caiso253b_ct_bucket_bimodality.json`; a
FINDING scoring P-1, P-2 and G-BIMODAL; the `docs/calibration-log/caiso.md`
entry; the rule-28 CAISO matrix-shard stamp. **Only if G-BIMODAL passes:** the
derive's class-partition repair, the re-frozen artifact, the phase-0 census,
the screen, the full three-year bundle and its registration — with the keeper
promotion decided on structure, and any gate regression put to the owner.

---

## §1.3 — G-DRIFT EXTENSION: `fbef3a91` → `bc77b189`, recorded before any solve

`main` advanced 45 commits while the corpus was being re-fetched (this
addendum's own commit `672bf473` merged into it), so the audit chain is
extended rather than re-opened. Same command, same classification duty:

```
git diff fbef3a91 bc77b189 -- src/market_sim scripts/run_calibration.py \
  scripts/run_calibration_full.py scripts/lib data/raw/_validation-source \
  data/raw/reference
```

7 files, +833 / −28 — all of it the capx D61/D62 going-forward-cost lane.

| file | Δ | verdict | reason |
|---|--:|---|---|
| `src/market_sim/config/scenarios.py` | +94 | **INERT** | one new field, `capacity_going_forward_bar_published_by_iso: dict[str, bool] \| None = None` (`:15696`), coerced to `None` in `__post_init__` (`:16487`) and registered in the cache-key **drop map** at `"None"` (`:1970`) — the keeper's key is unmoved. The rest of the hunk is comment text on the SCN-WS2a CES placeholder. |
| `src/market_sim/config/capacity_market.py` | +51 | **INERT** | the resolver for that gate. Measured at the shipped default: `resolve_capacity_going_forward_bar_published` returns **`False` for all six ISOs**, CAISO included. |
| `src/market_sim/data/avoidable_cost_rate.py` | +291 (new) | **INERT** | published net-ACR intake, read only under the gate above. |
| `src/market_sim/model/capacity_evolution/retirements.py` | +134 | **INERT — two independent proofs** | §1.3.1. |
| `scripts/lib/bench_stamp.py` | +201 | **INERT** | dashboard bench-stamp tooling; nothing on the solve path imports it. |
| `scripts/lib/mech_matrix.py` | +81 | **INERT** | rule-28 matrix tooling; governance only. |
| `scripts/lib/…/__init__.py` | +9 | **INERT** | package export for the above. |

### §1.3.1 — Why the retirement-screen hunk cannot reach a CAISO backcast

The new `resolve_going_forward_bar_per_kw_yr` is the retirement screen's
going-forward-cost operand (capacity evolution **step 3**). Two arguments, and
either alone is sufficient:

1. **The gate is off, measured not assumed.** `retirements.py:2251` returns
   `(atb, "atb_fom")` — the pre-existing value — on the first line whenever the
   gate is false, and the gate was executed and reads **False for every ISO**
   at the shipped default. Nothing downstream of that early return runs.
2. **The lane never enters capacity evolution at all.** The calibration path
   rebuilds each year's fleet with `fleet.build_base_fleet` and never calls
   `evolve_fleet` — stated in the codebase itself at `results/cache.py:337-339`
   ("builds each year's fleet with `fleet.build_base_fleet` and never calls
   `evolve_fleet` or `capacity_evolution.new_entry`"), which is why a multi-year
   backcast has no evolution step to reach.

**⇒ Every hunk in `fbef3a91` → `bc77b189` is INERT for a CAISO backcast. The
chain `fa23c1f7` (keeper) → `82f79693` (caiso-253) → `fbef3a91` (§1) →
`bc77b189` (here) is complete, and G-CTRL form 4 still stands with no control
solve spent.** §1.2's single LIVE hunk and its `co2` restriction are unchanged.

### §1.3.2 — A gate-power disclosure, made BEFORE the screen year is named

Read from the keeper's committed `_verdict.json` while the corpus was still
downloading, and recorded here so it cannot be mistaken for a post-hoc excuse:
**the keeper's C1 gas records for 2025 are all SKIPPED** on the preliminary
EIA-923 vintage (CT_PEAKER at 38 % plant reporting; ST_GAS has no per-class
actual). If §3.1's footprint census names **2025**, the S-3 C1 stop gate has
little bite in that year and S-4 (C4, which is scored in all three years)
carries the protective load alone.

**This changes nothing about how the year is named.** The year is
`argmax_y F(y)` and F contains no criterion — naming it instead on "which year
my gate can see" would be gate-shopping, which is precisely what §3.1 exists to
prevent. The limitation is disclosed, not designed around.

### §1.4 — G-DRIFT EXTENSION: `bc77b189` → `d13d1cba` (the SCN-WS1c carbon lane)

`main` advanced again mid-fetch. 5 files, +318 / −34 — and unlike the two
earlier deltas this one lands on the **carbon** path, which a CAISO backcast
genuinely uses (CAISO's marginal cost carries a CARB allowance adder). It was
therefore audited on the number, not on the narrative.

| file | Δ | verdict | reason |
|---|--:|---|---|
| `src/market_sim/config/scenario_resolvers.py` | +28 | **INERT** | comment-only — verified by filtering the diff to non-`#`, non-blank changed lines: **empty**. |
| `src/market_sim/results/cache.py` | +51 | **INERT** | docstring-only (the S2 cache-epoch entry); no `def`/`import`/assignment/`return`/`if` line changed. |
| `src/market_sim/config/scenarios.py` | +18 | **INERT** | one new `__post_init__` warning, guarded `if self.mode == "forecast" and self.carbon_price_path not in ("zero", None)`. A `mode="backcast"` config never reaches it, and it emits a `RuntimeWarning` rather than changing a value. |
| `src/market_sim/policy/cap_and_trade.py` | +63 | **INERT** | the S2 repair is explicitly in the **forecast** branch ("the forecast branch previously returned a zero adder whenever a non-default `carbon_price_path` was set"). The backcast branch — the measured auction average — is untouched, and the keeper carries `mass_cap_enabled: False`, `mass_cap_tons: None`, `mass_cap_program: None`. |
| `src/market_sim/policy/carbon.py` | +192 | **INERT — VERIFIED ON THE NUMBER** | §1.4.1. |

### §1.4.1 — The carbon price itself, measured at HEAD against the keeper's frozen basis

Owner ruling S2 makes a named `carbon_price_path` a **floor** under the state
program (`resolved_base_trajectory_price` → `max(program, RFF path)`) instead of
a replacement. That is a real semantic change to `carbon.py`, so the claim that
it cannot move a CAISO backcast was **executed rather than argued** —
`resolve_carbon_price` was called at HEAD on the actual per-year
`backcast_config("CAISO", …)`, and compared to the carbon basis frozen into
`caiso_offer_curve_measured.json`, which is the basis the keeper's offer
multipliers were derived against:

| year | `resolve_carbon_price` at HEAD | `STATE_CARBON_PRICE_BY_ISO["CAISO"]` | frozen artifact basis | match |
|---|--:|--:|--:|:--:|
| 2023 | 33.03 | 33.03 | 33.03 | ✔ |
| 2024 | 35.23 | 35.23 | 35.23 | ✔ |
| 2025 | 28.06 | 28.06 | 28.06 | ✔ |

Exact in all three years. The floor's own documentation states the same result
from the other direction — the RFF mid path never exceeds a program trajectory,
so the leg is "an exact NO-OP on CAISO, NYISO and NEISO" — but the table is the
evidence and the comment is only the corroboration.

**⇒ The chain `fa23c1f7` (keeper) → `82f79693` → `fbef3a91` → `bc77b189` →
`d13d1cba` is complete and every hunk is INERT for a CAISO backcast. G-CTRL
form 4 stands; no control solve is spent.** §1.2's single LIVE hunk and its
`co2` restriction remain the only exception on the whole chain.

### §1.5 — G-DRIFT EXTENSION: `d13d1cba` → `d520b891` (SCN-LOAD). The one delta that moved a table a CAISO backcast config carries

10 files, +1,944 / −263. Eight are the new `scripts/lib/load_forecast/*` intake
package (not imported by any solve path) and `data/datacenter.py` (+82, read
only when `datacenter_load_path != "off"`). The tenth is
`config/constants.py`, +735 / −263 — and constants.py IS on the backcast path
(rule 5 `[R-NO-MAGIC]`), so it was audited by **extracting and comparing the
values of every top-level constant the diff touches**, at both shas, rather
than by reading the commit subject.

Four constants are touched. Their values, compared object-to-object:

| constant | changed? | verdict |
|---|---|---|
| `CORRELATED_OUTAGE_CURVE` | **identical** | the one constant here that a backcast genuinely reads did not move. |
| `DATACENTER_ADDITIONS_MW` | changed (all 5 ISOs incl. CAISO) | read only by `data/datacenter.py`; the CAISO backcast config carries `datacenter_load_path='off'`, so the reader never runs. |
| `ELECTRIFICATION_LAYERS` | changed (ERCOT/NEISO/NYISO — **not CAISO**) | same reader, same gate. |
| `DEMAND_GROWTH_RATES` | changed, **CAISO included** | §1.5.1 — the one that needed a real proof. |

### §1.5.1 — `DEMAND_GROWTH_RATES["CAISO"]` moved, and the backcast is still byte-identical — measured, not argued

The CAISO row genuinely changed:

| path | before | after |
|---|---|---|
| `mid.near` | 0.028 | **0.032425** |
| `mid.long` | 0.025 | **0.016710** |
| `low` / `high` | 0.015/0.015, 0.042/0.035 | 0.017371/0.010026, 0.048638/0.023394 |

and `backcast_config("CAISO", …)` carries `demand_growth_path='mid'` in all
three years — i.e. the changed row IS selected by the config. So "forecast-only"
would have been an assertion, not a finding. The proof is that the *span* is
empty, not that the table is unread: `runner._scale_demand` compounds
`range(config.weather_year, year)`, and a backcast pins `weather_year == year`.
Executed at HEAD on the real per-year configs:

| year | `weather_year` | `year == weather_year` | scale factor | demand array identical |
|---|--:|:--:|--:|:--:|
| 2023 | 2023 | ✔ | 1.000000000000 | ✔ |
| 2024 | 2024 | ✔ | 1.000000000000 | ✔ |
| 2025 | 2025 | ✔ | 1.000000000000 | ✔ |

The function's own docstring says the same ("A backcast (`year == weather_year`)
still gets a factor of 1"), but the table is the evidence. The only other
consumer, `capacity_evolution/retirements.py:340`, is unreachable for the
reason §1.3.1 already established: the calibration lane never calls
`evolve_fleet`.

**⇒ Chain complete through `d520b891`; every hunk INERT for a CAISO backcast.
G-CTRL form 4 stands, no control solve spent, and §1.2's `import_co2_tons`
hunk with its `co2` restriction remains the only LIVE exception on the chain.**

---

## §7 — RULE-21 `[R-DOF]` INVENTORY: the repair is implementable with ZERO new free parameters (verified ahead of the gate)

The parent PRECOMMIT §2.3 asserts "**zero new free parameters**". That is an
admissibility claim, so it was checked against the code **before** G-BIMODAL was
scored — it holds or fails on its own terms whichever way the gate goes, and if
it had failed the repair would have been inadmissible no matter how clean the
antimode.

A separated ST_GAS bucket needs six operands. Every one already exists in a
source the model reads today:

| operand | source | value | new DOF? |
|---|---|--:|:--:|
| `base_hr` | `bin_assignments_CAISO.csv`, cap-weighted `Plant_Avg_HR` — the same statistic CC 7.442 / CT 10.862 come from | **11.847** | no |
| `fleet_mw` (the G1 denominator) | same file | **2,858.8 MW** | no |
| `pct_committed` | same file | **6.617** | no |
| `pct_peaking` | same file | **15.0** | no |
| `econ_low_share` | the model's OWN `_CAISO_OFFER_CURVE["ST_GAS"]` geometry | **0.50** | no |
| `VOM` | `constants.VOM["gas_st"]` — the same table the derive's `VOM_BY_CLASS` already reads for CC (`gas_cc` 2.0) and CT (`gas_ct` 3.5) | **4.0** | no |

The seventh quantity, the second cut itself, is the measured antimode — located
the same way `hr_cut = 8.5` was (the derive's own G2 capacity-density-valley
criterion), not swept and not chosen against any criterion.

**The consumer-side plumbing is one line.** `backcast_config.py:2204` currently
reads `"ST_GAS": "CT_PEAKER"` in `_ungrounded_source` — i.e. the steamers are
explicitly pointed at the bucket their own presence biased, which is §1 of the
parent PRECOMMIT stated in code. Re-pointing it is the whole consumer change;
`CT_CHP → CT_PEAKER` needs no edit at all, since under the repair CT_PEAKER's
bucket is the de-contaminated one.

**Rule 21 therefore holds as claimed, verified rather than asserted.** Noted
with it, because it is a boundary the session must not cross quietly: the
2.9 GW ST_GAS fleet is **three plants** (Alamitos / Huntington Beach / Ormond
Beach). A per-plant statistic would be inadmissible on the masked OASIS ids in
any case, and remains out of scope — the repair is per-CLASS, exactly as the
derive already is.

### §7.1 — G-DRIFT: `d520b891` → `03bd0671` is EMPTY in scope

`main` advanced again; the audited path (`src/market_sim`, the two calibration
CLIs, `scripts/lib`, `_validation-source`, `reference`) shows **no changed
files at all**. The chain stands through `03bd0671` with nothing new to
classify.

### §1.6 — G-DRIFT EXTENSION: `03bd0671` → `1aab49a0` (wall-clock A-4). The fleet path again, so re-verified rather than carried forward

3 files, +306 / −18 — and two of them (`egrid_sheets.py`, `fleet/eia860.py`)
are the SAME fleet-path files §1.1 verified at `fbef3a91`. A prior verification
does not transfer across a change to the thing verified, so both were measured
again at HEAD.

| file | Δ | verdict | reason |
|---|--:|---|---|
| `src/market_sim/data/disk_memo.py` | +249 (new) | **INERT** | the extracted hashing + JSON-memo primitive; no LP-visible value. |
| `src/market_sim/data/egrid_sheets.py` | ±27 | **INERT — RE-VERIFIED** | the inline sha256 was replaced by `disk_memo.content_digest`, which the module claims is byte-compatible so existing mirrors keep their names. Re-ran §1.1's identity test at HEAD: `PLNT23` (12612, 6), `UNT23` (26186, 3) and `PLNT23` FIPS/BACODE (12612, 6) all **EXACT** against `pd.read_excel` under `assert_frame_equal(check_exact=True)`, on both the mirror-write and mirror-hit paths. |
| `src/market_sim/data/fleet/eia860.py` | +48 | **INERT — VERIFIED** | §1.6.1. |

### §1.6.1 — The new cross-process memo on the boundary-HR repairs

`_egrid_boundary_hr_repairs` now caches its accepted repair set in a JSON memo
named by a sha256 over both source files' bytes. That set **sets plant heat
rates**, so a serialization defect there would move the fleet silently — and
`dict[int, float]` through JSON is exactly where key types get quietly
stringified. Measured three ways at HEAD: the pure computation, the memo path,
and the memo path again after `cache_clear()` to force the on-disk hit.

| check | result |
|---|---|
| n repairs (direct / memo / forced disk hit) | 1 / 1 / 1 |
| keys identical across all three | ✔ |
| key **types** preserved | `{int}` → `{int}` (not stringified) |
| values identical at full precision | ✔ — `{55641: 6.880032798350796}` |

**⇒ Chain complete through `1aab49a0`; every hunk INERT for a CAISO backcast,
with the two fleet-path files re-verified rather than carried forward on §1.1's
earlier result. G-CTRL form 4 stands; no control solve spent.**

### §1.7 — `1aab49a0` → `7a42c7c5`, and a note on how the rest of this audit will be kept

6 files, +69 / −18. Four are `scripts/lib/load_forecast/*` (the intake package;
no solve path imports it). The two in scope:

| file | Δ | verdict | reason |
|---|--:|---|---|
| `src/market_sim/config/constants.py` | +1 | **INERT** | one name added to an existing `from market_sim.config.capacity_market import (…)` block (`resolve_capacity_going_forward_bar_published`). A re-export made available, not a value changed — and the constant *values* audited in §1.5 are untouched. |
| `src/market_sim/policy/carbon.py` | +27 | **INERT — RE-VERIFIED** | `float(resolution.price_adder)` → `float(resolution.price_adder or 0.0)`: a None-guard that can only change behaviour where the old code raised `TypeError`. Because carbon.py moved again, §1.4.1's measurement was re-run rather than carried forward — CAISO backcast carbon still **exactly** 33.03 / 35.23 / 28.06. |

**How the remainder of this audit is kept, stated so it is a method and not a
drift.** `main` is advancing several times an hour while the corpus downloads,
and a section per delta is becoming less readable without becoming more
truthful. The audit that actually binds under rule 29(b) is the one against the
sha **the arm is solved at**, so:

* the incremental sections above stand as the record of what was checked and
  when — including the three occasions a delta touched a file a CAISO backcast
  genuinely reads (§1.4.1 carbon, §1.5.1 demand growth, §1.6 the fleet path),
  each measured on the number rather than argued;
* the remaining pre-solve deltas are folded into **one consolidated re-audit
  from the keeper's `fa23c1f7` to the solve-time HEAD**, recorded in the
  FINDING before any LP is spent. A consolidated audit over the whole span is
  strictly stronger than the sum of the increments — it cannot miss a hunk that
  was added and then revised between two of them.

Nothing about the standard changes: every hunk on the backcast path is
classified INERT with its reason, or it is LIVE and earns a control solve.
