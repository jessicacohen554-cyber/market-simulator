# FFR-SC — the owed FF-G1 T1-F transmission-expansion A/B, + the surviving input refreshes

**Session.** FFR Wave 3, the transmission-expansion gate lane
(`docs/forecast-readiness-prompt-pack-2026-07.md` §FFR-SC). Branch
`claude/ff-g1-t1-f-transmission-ab-8z4yn6`, rebased onto `origin/main` **`edf5c5a`**
(main moved twice mid-session — see §9.1). Run concurrently with FFR-3A-2 and FFR-3F
under owner decision Addendum F.2 (rule 12's cap is per prompt).

**One-line result.** The gate is **INERT in CAISO 2026–2030 and provably inert in PJM
2026–2050**, and the CAISO half is inert for a *structural* reason worth more than the
verdict: `WECC_import_simultaneous` caps the **signed sum of two legs that run in
opposite directions**, so it stays slack even when both legs are individually
saturated — the registry uplifted the one element that cannot bind. **No default is
flipped**; arming remains the owner's box, and nothing here argues for it.

> **⚠ BOTH ARMS INHERIT AN OPEN ADEQUACY FINDING.** The shipped forecast posture now
> carries owner decisions D-1 (`retirement_rule="pipeline"`) and D-2 (both entry
> dampers), and FFR-3A measured that those decisions **degrade capacity adequacy in
> every ISO** — ERCOT's reserve margin to **−1.5 %**, CAISO's to **−3.1 %**
> (`docs/handoffs/ffr-t1-regate-2026-08-02.md` §6.4, open blocker 0). That finding is
> **unresolved and is not this lane's to resolve.** Every delta below is measured
> **arm-to-arm against this session's own gate-OFF leg**, never against a
> pre-decision citation, and the absolute level of both arms sits inside that open
> finding.

---

## 1. What the A/B could actually test — the registry decides, and it ruled out PJM

The charter offered PJM **or** CAISO. That choice is not free: the gate can only move
a limit the registry gives it a non-zero delta for, and **PJM's registry has none.**

**PJM is provably inert, and no solve was spent to learn it.** All six live PJM rows
(`data/raw/transmission-expansion/pjm.csv`) carry `delta_mw = 0.0` — every RTEP
Window-3 project is recorded-not-quantified, because PJM publishes component lists
rather than interface-TTC deltas and rule 5 `[R-NO-MAGIC]` forbids inventing the MW.
Measured directly against the consumption seam:

```
PJM: apply_transmission_expansion returns the SAME ISOConfig object
     (is-identical) for every year 2026-2050.        -> True
     years where it did not: []
```

So a PJM A/B could measure exactly one thing — that OFF ≡ ON — which FF-G1 §4.3
already established structurally. **The test ISO is therefore CAISO**, and this is a
finding in its own right: *the gate's PJM column cannot move until the measured
transfer-interface-limits intake lands post-COD* (FF-G1 §6 follow-up).

**CAISO gives the A/B exactly one live element**, which makes it unusually clean:

| row | kind | in service | applied? | effect in 2026–2030 |
|---|---|---|---|---|
| `swip-north--wecc_simultaneous` | `interface` | **2028** | **YES** | `WECC_import_simultaneous` cap **7,500 → 8,617.5 MW** |
| `tenwest`, `sunzia`, `ng-iv2`, `transwest` | `import_tranche` | 2024/26/31/31 | no | V1 exclusion — the import fleet is built once pre-year-loop |
| `gates-losbanos-sc`, `iv-nosongs` | `link` | 2029/2032 | 0.0 delta | control |
| `humboldt-osw` | `intra_zonal` | 2035 | n/a | no modeled limit at this grain |
| `serrano-delamo-mesa` | `link` | 2031 | superseded | excluded at load |

Two consequences worth stating before any number is read:

1. **2026 and 2027 are pre-COD null years.** The arms must be *array-identical*
   there. That is a control built into the run, not an extra leg — and it is
   checked in §4.
2. **The uplift lands on the one aggregate limit that actually envelopes CAISO's
   WECC imports in the shipped forecast posture.** The two WECC legs' own TTCs sum
   to 15,423 MW against a 7,500 MW simultaneous cap, and every CAISO corridor
   mechanism (`caiso_per_hub_intertie`, `caiso_corridor_flow_limit`,
   `caiso_corridor_atc_forward`, `capacity_deliverability_limits`) is **off** in
   the shipped forecast arm. So `WECC_import_simultaneous` is the binding envelope
   and +1,117.5 MW is a **+14.9 %** uplift on it.

## 2. The arms

Both cold-solved post-epoch at the **shipped** CAISO posture (§4.3 of the re-gate:
CAISO is curve-ON, expressed by `--golden-posture`), 5 solve-years each, run
concurrently (rule 12: ≤2 invocations, years sequential within each).

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=.:src \
python scripts/run_full_horizon.py --iso CAISO --start-year 2026 --end-year 2030 \
  --golden-posture [--transmission-expansion] --out-dir results/ffrsc/txexp-{off,on}/caiso
```

| arm | gate | years | cache key | registered id |
|---|---|---|---|---|
| **OFF** (control) | off | 5/5 | `fe814896444d8ed7` | `caiso-2026-2030-ffrsc-txexp-off` |
| **ON** | on | 5/5 | `f4a79a86d61336f8` | `caiso-2026-2030-ffrsc-txexp-on` |

**Liveness is established before any delta is read:** the keys are distinct, so the
gate genuinely produced a different scenario rather than silently reusing the control
(the `_CACHE_KEY_OPTIONAL_FIELDS` separability property doing its job).

## 3. Invariants — identical in both arms, and both carry the inherited finding

Both arms score **3 FAIL / 0 WARN (14 scored)**, the same three, with identical text:

* **I3** unserved/dump — 2030: slack 0.02 % of load
* **I7** reliability floor — 2026: accredited firm 50,729 < requirement 57,306 MW …
* **I12** reserve-margin band — 2026 **1.8 %**, 2027 **−3.1 %**, … vs band [15 %, 30 %]

These reproduce FFR-3A's CAISO T1-F leg exactly, which is the point: **the gate moves
no invariant**, and the *level* both arms sit at is the open D-1/D-2 adequacy finding
(§6.4 of the re-gate), not something this lane introduced or can fix.

## 4. Measured result — interface, flows, prices

### 4.1 The interface never binds, in either arm

`WECC_import_simultaneous` is the only element the registry moves. Cap vs realised
net flow (OFF arm; the ON arm's flows are identical — §4.2):

| year | cap OFF | cap ON | net iface mean | net iface **max** | binding h (OFF/ON) | **headroom at max** |
|---|---|---|---|---|---|---|
| 2026 | 7,500 | 7,500 | 4,839.0 | 5,067.6 | 0 / 0 | 2,432.4 |
| 2027 | 7,500 | 7,500 | 4,804.4 | 5,209.1 | 0 / 0 | 2,290.9 |
| 2028 | 7,500 | **8,617.5** | 4,917.9 | 5,614.9 | 0 / 0 | 1,885.1 |
| 2029 | 7,500 | **8,617.5** | 4,920.3 | 5,798.1 | 0 / 0 | 1,701.9 |
| 2030 | 7,500 | **8,617.5** | 5,243.3 | 6,831.6 | 0 / 0 | 668.4 |

**Zero binding hours in 43,800 hour-years, in both arms.** Raising a constraint that
never binds cannot change anything, and does not.

### 4.2 The economics are identical; only degenerate primal detail moves

| year | objective OFF | objective ON | Δ | total unserved OFF/ON (MWh) | gen OFF/ON (TWh) |
|---|---|---|---|---|---|
| 2026 | 7,101,771,414.306412 | 7,101,771,414.306412 | 0 | 0.000 / 0.000 | 168.55052 / 168.55052 |
| 2027 | 7,848,373,983.695720 | 7,848,373,983.695720 | 0 | 274.172 / 274.172 | 175.19851 / 175.19851 |
| 2028 | 9,020,042,745.686092 | 9,020,042,745.686092 | 0 | 8,362.519 / 8,362.519 | 182.16759 / 182.16759 |
| 2029 | 8,662,411,502.857380 | 8,662,411,502.858770 | +1.4e−3 | 23,704.997 / 23,704.997 | 178.31642 / 178.31642 |
| 2030 | 10,569,717,656.338373 | 10,569,717,656.337332 | −1.0e−3 | 42,320.299 / 42,320.299 | 183.65514 / 183.65514 |

Load-weighted and zonal **prices are identical to 4.3e−14** in every year; the
objective agrees to 1.6e−13 relative (solver tolerance); **fleet evolution is
identical in every year** — same peak demand, same retirements, same thermal
additions (2027: 1,492.5 MW retired / 1,396.4 MW added in *both* arms; 2029: 7,585.6
MW added in both; 2030: 1,122.0 / 4,268.8 in both).

**2026, 2027 and 2028 are BIT-IDENTICAL across the arms** — dispatch, prices, flows
and slack all `array_equal`. 2026–27 are pre-COD and *must* be (the built-in control,
which passes). **2028 is the informative one**: the cap actually moves that year, and
nothing changes at all.

**2029 and 2030 differ in the primal only**: dispatch, flows, storage and slack are
rearranged (dispatch max cell Δ 7.0/10.5 GW; slack redistributed across 18/33 cells)
at **identical duals, identical objective and identical totals**. That is textbook
**alternative optima** — a slack constraint's changed bound perturbs the solver's
pivoting and CAISO's degenerate import/storage ties resolve to a different vertex.
It is not an effect, and it must not be reported as one.

### 4.3 Why it is inert — structural, not incidental

This is the part worth carrying forward. The two WECC legs run in **opposite
directions**, and the interface caps their **signed sum**:

| 2030, OFF arm | leg TTC | mean | max | min | hours at +TTC | hours at −TTC |
|---|---|---|---|---|---|---|
| `WECC_import→NP15` | 4,800 | **−3,215.0** | 4,800.0 | −4,800.0 | 1 | **4,164** |
| `WECC_import→SP15_rest` | 10,623 | **+8,458.3** | 10,623.0 | −216.3 | **994** | 0 |
| net sum (the capped quantity) | *7,500 cap* | 5,243.3 | 6,831.6 | — | **0** | — |

So CAISO wheels: it imports into SP15_rest at up to the leg's full 10,623 MW TTC
(994 h/yr) while exporting through NP15 at its full 4,800 MW bound (4,164 h/yr). Both
legs are **individually saturated for thousands of hours** — and the net sum they are
capped on still peaks 668 MW short of 7,500. **The binding limits are the per-leg
TTCs; the net-sum envelope is structurally slack and is the wrong element to uplift.**

Two corroborations that this is the real mechanism and not a one-run accident:

* It **reproduces caiso-133's backcast measurement in the forecast lane** — that
  session found `WECC_import_simultaneous` structurally unreachable in all 26,280 h of
  2023–25 in *both* directions, duals exactly 0.000. Different mode, different fleet,
  same conclusion.
* It is the CAISO instance of **FF-G1 §4.4's own NEISO smoke finding**: the link half
  of a registry row applies, while the energy half stays bound by something else
  (there the import-tranche supply curve, here the per-leg TTCs).

### 4.4 A registry mapping note this produced

SWIP-North's instrument is a **new controlled Idaho→Eldorado corridor** with a
board-stated 1,117.5 MW N→S entitlement — physically a *per-leg / new-link*
capability. The registry maps it onto the **net-sum interface**, which §4.3 shows
cannot bind. Separately, the row's `delta_mw_reverse = 1,072.5` is **silently
dropped**: `WECC_import_simultaneous` has `reverse_cap_mw = None`, and
`apply_transmission_expansion` only writes a reverse cap where one is already
declared. Neither is changed here — re-mapping the row is a topology decision with an
owner and a methodology §6.6 tension behind it (the board entitlement vs the flat
advisory MIC), not a call this lane makes. Recorded for the FF-G1 §6 follow-up list.

## 5. What this A/B does NOT establish

* **It does not establish that the channel is broken, or that it works.** It
  establishes that in CAISO 2026–2030 the channel applied its one live delta to an
  element that never binds. The *wiring* demonstrably fires (distinct cache key;
  the cap is 8,617.5 in the ON arm from 2028) — the effect is nil downstream.
* **It says nothing about ERCOT, MISO, NYISO or NEISO** (rule 25). Their cells stay
  `U`. In particular ERCOT's STEP rows (+2,555 / +945 MW) land in **2032** and MISO's
  five CIL rows in **2030** — outside or at the very edge of a 2026–2030 window — so
  they are untested, not inert.
* **It does not extend past 2030.** Headroom is *narrowing* monotonically (2,432 →
  668 MW). A later window could well bind, and the correct read of this result is
  "inert in this window", not "inert".
* **It does not test the import-tranche half.** Four of CAISO's eight live rows are
  `import_tranche` (SunZia, TenWest, NG-IV2, TransWest = 11.7 GW of recorded external
  supply) and are recorded-not-applied by construction — the V1 exclusion. The
  per-year import-tranche seam remains the named FF-G1 §6 follow-up, and on this
  evidence it is the **higher-value** half.
* **It does not clear either arm for promotion.** Both are HOLD-grade by the §3
  invariants, both inherit the open D-1/D-2 adequacy finding, and no determination is
  claimed here.
* **It is not an argument to flip the default.** A default-off gate measured inert is
  neither promoted nor deleted: it is correct, grounded, and waiting on either a
  registry re-map (§4.4) or a window in which its deltas bind. Arming stays the
  owner's box.

## 6. Input refresh 1 — ATB derivation pin → 2024 v4.0.0 (audit FR-20)

Commit `083879d`. `curate_nrel_atb.DERIVATION_PINNED_VERSION` moves `v3.0.0` →
`v4.0.0`, triggered by the **data vintage change alone** (rule 23
`[R-FROZEN-DERIVE]`): OEDI mirrored ATB 2024 v4.0.0 on 2026-07-28 and FFR-PB landed
its extract on 2026-07-31, deliberately leaving the re-derive to this lane. No
residual was consulted and none moved.

**The charter's premise needed correcting first, and FFR-PB had already corrected
it:** there is no ATB 2025 or 2026 *edition* — 2024 is the current edition, and the
real gap was a **point version**. So "the ATB 2025/2026 re-derive" is, correctly,
the v3→v4 point-version re-derive.

**Result: a measured no-op on every committed constant.** Both derive scripts return
byte-identical output under the two versions:

| derived quantity | v3.0.0 vs v4.0.0 |
|---|---|
| `NEW_ENTRY_COSTS` (7 techs, capex + FOM) | identical |
| `TECH_COST_MULTIPLIERS` (low/high capex ratios) | identical |
| benchmark envelope table + envelope multipliers | identical |
| `STORAGE_TECHS` li-ion, `OFFSHORE_WIND_PARAMS` | identical |
| `derive_egs_fom` | 163.4 both ways |

`constants.py` is therefore **unchanged**, and the two rule-23 source-consistency
tests pass against the newer bytes (27 passed with the curation suite).

**Why the one real diff reaches nothing.** Over the whole committed slice — 3,858
rows, identical key index — exactly 56 values move materially, and **all** are
`Geothermal`/`DeepEGSFlash`/`Moderate` (CAPEX +1.50…+6.14 %, Fixed O&M
+0.13…+2.00 %); the other 16 differ at ~1e-14 relative (float round-trip noise).
The raw README anticipated that `GEOTHERMAL_PARAMS`' EGS capex band "would move on a
re-derive". **It does not**: that dict's `fom_kw_yr` reads **NFEGSFlash** (unchanged)
and its `capex_kw` 5000.0 is a **DOE Liftoff** figure, not an ATB DeepEGS one. There
is no ATB-DeepEGS-derived constant in the model.

`tests/curation/test_curate_nrel_atb.py::test_parse_defaults_to_the_pinned_derivation_version`
hard-coded `v3.0.0`. It is rewritten against `DERIVATION_PINNED_VERSION` itself, so a
future deliberate pin move re-points it rather than failing it — the property under
test is "parse reads the pin, an explicit version overrides it", not which pin is set.

**Still open in FR-20 after this** (unchanged, not addressed here): the entry-cost mid
case remains frozen at the 2026 snapshot with only Wright's-Law decline.

## 7. Input refresh 2 — NYISO demand anchor → 2026 Gold Book

Commit `16da87f`. Closes **FF-G4 §8-D4 item 3**, which flagged the 2025 edition this
row cited as superseded.

**The document.** NYISO 2026 Load & Capacity Data Report ("Gold Book"), released
April 2026, 166 pp — fetched from the URL pattern `data/raw/NYISO/README.md` already
documents for the 2024 edition, verified to be the genuine 2026 edition by reading
its own cover and release line, and landed at
`data/raw/NYISO/2026-Gold-Book-Public.pdf` (sha256 `43865c1c…`).

**The basis is now formulaic** (rule 5 `[R-NO-MAGIC]`) instead of FF-1C's "Central
~1.8 %/yr near / 1.2 %/yr long" reading, which no stated formula reproduced: each
case is the CAGR of Table I-1a's own Energy-GWh series, **near = 2026→2030, long =
2031→2050**, matching `DEMAND_GROWTH_TRANSITION_YEAR` and the *identical*
construction `DEMAND_GROWTH_RATES_VINTAGES` already uses for every NYISO row.

| case | series (GWh) | near | long | was |
|---|---|---|---|---|
| low | 150,720→149,300 ; 149,510→157,740 | **−0.0024** | **0.0028** | 0.008 / 0.006 |
| mid | 152,600→160,160 ; 161,830→205,760 | **0.0122** | **0.0127** | 0.018 / 0.012 |
| high | 153,420→170,180 ; 174,220→251,930 | **0.0263** | **0.0196** | 0.030 / 0.020 |

Cross-check against the edition's own published CAGR block: baseline energy 2026-31 =
1.18 % and 2026-46 = 1.30 %, bracketing the 1.22/1.27 computed here.

**Two changes beyond the level, both rule 14 `[R-ACCURATE]`:**

1. **low/high are now the edition's own Lower/Higher Demand series**, not
   prior-vintage band ratios re-centred on the mid. The header comment records those
   "exact published low/high scenario tables" as unavailable at FF-1C; they are in
   this edition, so the published data replaces the reconstruction.
2. **The low case's near rate is negative, and that is the forecast's real sign** —
   the 2026 Lower Demand path has NY energy *declining* to 2030 on efficiency/codes.
   The same sign already appears in the as-of-2021 vintage, so the resolver supports
   it; it is not a defect.

Note also that **long now slightly exceeds near** for the baseline: NY growth
accelerates post-2030 on electrification. The near/long split represents that fine.
Figures are TOTAL (large-load- and electrification-inclusive) — the convention every
additive layer relocates out of exactly once (`data.datacenter.add_load_layers`).

`parameters.json` / `parameter-citations.md` are re-cited to the edition, table, URL
and file hash, and the six entries lose their `auto-generated` flag.

**Cache impact, recorded rather than left to be discovered** (commit `b291aa2`): this
is a constants-level change with no `ScenarioConfig` field, so **no cache key moves**
— `ScenarioConfig()` hashes to `973a0acdef818e91` both with and without it. That is a
same-key invalidation, so it gets a cache-epoch ledger entry (**2026-08-03b**) in
`results/cache.py`. Scope: cached **NYISO forecast-mode** bundles solved before this
commit are stale; **no other ISO**, and **no backcast bundle in any ISO** — the
backcast path takes measured load and never reads this table. **No keeper moves.**

## 8. MISO's 2026 LTLF — blocked, handed forward

**Not refreshed, deliberately.** FF-G4 §8-D4 item 5 marks the MISO 2026 LTLF ⬇
(bot-walled manual download), and that is exactly what was measured:

```
403  https://cdn.misoenergy.org/2026%20MISO%20Long%20Term%20Load%20Forecast%20Results%20Summary.pdf
403  https://www.misoenergy.org/planning/planning-modeling/long-range-transmission-planning/
```

Not a proxy fault — the NYISO fetch in §7 went through the same proxy and returned
200. The MISO row therefore keeps its cited **Sept-2025 LTLF** basis. Filling it from
memory would violate rule 5, and estimating it would violate rule 14; the honest
outcome is a named blocker, not a number. **Successor: this needs a browser-session
manual download of the 2026 LTLF results summary + whitepaper, then the same
Table-based CAGR re-derive §7 applies to NYISO.**

## 9. Other findings

### 9.1 `origin/main` moved twice mid-session

Session start `98ad9c1`; the dispatch brief's `01b6a6a` was already stale on arrival.
Main advanced to **`edf5c5a`** during the session (PRs #3384–#3388). Verified before
continuing that none of it touches this lane's surface: `iso_configs.py`,
`transmission_expansion.py`, `runner.py` and `run_full_horizon.py` are **untouched**
in `98ad9c1..edf5c5a`; `scenarios.py` gains only `nyiso_seny_rcpf_increment_step`
(default-off, NYISO). The CAISO A/B baseline is unaffected — in particular
PR #3388 ("caiso asymmetric path ratings") adds probes and *calibration* CLI flags
only, no topology change.

### 9.2 The pinned default cache key moved upstream, not here

`ScenarioConfig()` now hashes to **`973a0acdef818e91`**, not the
`603c2498bf71d21d` the FFR-3A ledger entry and several handoffs quote. Measured to be
**upstream field additions, not this session**: the key is identical with and without
this session's `constants.py`. A successor reading `603c2498…` in an older document
should not treat the difference as drift.

### 9.3 The registry declares a reverse uplift the topology cannot express

`swip-north--wecc_simultaneous` carries `delta_mw_reverse = 1072.5` (the S→N half of
the board-stated entitlement). CAISO's `WECC_import_simultaneous` has
`reverse_cap_mw = None`, and `apply_transmission_expansion` only writes
`reverse_cap_mw` when one is already declared — so **the reverse half is silently
dropped**. This is defensible (the limit is an *import* cap by name and construction,
and the LP group is one-sided), but it means the registry row and the applied effect
disagree on their face. Flagged, not changed: making it visible is a loader/logging
question, and inventing an export cap would be a topology change with no instrument
behind it. Successor item for the FF-G1 §6 follow-up list.

### 9.4 A defect on main lost both arms' summaries — fixed, with a guard

Both arms solved **all five years**, then died at the finish line:

```
TypeError: write_run_config() got multiple values for argument 'run_dir'
  scripts/run_full_horizon.py:596 in solve_and_summarize
```

`write_run_config(out_dir, run_dir, **extra)` was being passed `run_dir` **both
positionally and in the kwargs**. Introduced by `34c2f25` ("Repair the T1-F
measurement instruments") — the commit that fixed FFR-3A blocker 7 (no
`run_config.json`, so FC-7 failed by construction) — so *the fix for the FC-7 blocker
was itself broken*, and it takes out **every T1-F leg** on main, after the expensive
part, losing both `full_horizon_summary.json` and `run_config.json`.

**FIXED CONCURRENTLY BY FFR-3A-2, WHOSE FIX IS THE ONE ON MAIN.** This lane hit the
defect independently and patched it locally to unblock the A/B (record `run_dir` in
the payload, drop the duplicate kwarg). On the rebase onto `6040f28c` the two fixes
collided: FFR-3A-2 had made the *same* correction, and **its version is kept** — the
code fix is semantically identical, and its test
(`test_accepts_the_real_call_sites_kwargs`) is strictly stronger than the one written
here, because it *invokes* `write_run_config` with the caller's exact shape and
asserts `run_dir` / `iso` / `cache_key` / `solved_years` all survive into the payload,
where this lane's version only bound the signature via `inspect.signature(...).bind()`.
This session's test was dropped in the merge, deliberately and with nothing lost.

So the attribution is: **found independently by two lanes on the same day; fixed by
FFR-3A-2.** What this lane contributes is the *measured operational consequence* —
re-running both arms after the fix completed in **0.6–0.7 min** each entirely off the
existing cache (no re-solve), which is what makes this defect cheap to recover from
once diagnosed, and confirms **FFR-3A blocker 7 is genuinely closed** (both arms now
write `run_config.json`).

**Why nothing caught it,** which is the durable lesson and is recorded in both lanes:
every pre-existing test in `tests/scoring/test_full_horizon_instruments.py` called
`write_run_config` directly with a hand-written kwarg set *shorter* than the caller's,
so the collision shipped green; the real call site is only reachable behind a full
solve and was never executed in CI.

### 9.5 Pre-existing test failures, unchanged by this session

The fast lane is **5 failed / 6,034 passed**. All five were confirmed pre-existing by
re-running with this session's edits stashed:

* `test_ercot_thermal_as_endogenous.py::TestScreenMutualExclusion` ×2 — D-1 fallout
  (`retirement_rule='pipeline' requires a simulation year`); this is the family FFR-3A
  logged as open blocker 6.
* `test_outages.py::NuclearUnitAvailabilityTest::test_unknown_iso_degrades_to_empty` —
  fails *because* `data/clean` now exists; the test's "degrades to empty" premise
  assumes an unregenerated checkout.
* `TestFullYearPerformance::test_full_year` and
  `TestDispatchPerformance::test_full_year_200_generator_fleet` — wall-clock
  assertions, run while the `data/clean` regeneration was saturating the container.

### 9.6 The `data/clean` prerequisite, re-measured

FFR-3A's blocker 1 reproduced exactly: a fresh container has **zero** curated
datatypes and every forecast leg fails loudly until `scripts/regenerate_clean.py`
completes. Two additions to what that note records:

* **`pip install -e .` (or `PYTHONPATH` including `src`) is part of the
  prerequisite.** Run with `PYTHONPATH=.` alone, the regeneration *appears* to run and
  fails 8 datatypes with `ModuleNotFoundError: No module named 'market_sim'` — the
  per-datatype subprocesses inherit the parent's path, and `scripts/` resolves while
  `market_sim` does not. It reports each as `[FAIL]` and keeps going, so a successor
  who does not read the log gets a silently partial `data/clean`.
* `pip install -r requirements.txt` needs `--ignore-installed PyYAML` on this image
  (the Debian-packaged PyYAML has no RECORD file and blocks the uninstall step).

