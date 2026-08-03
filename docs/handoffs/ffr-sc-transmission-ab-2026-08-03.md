# FFR-SC — the owed FF-G1 T1-F transmission-expansion A/B, + the surviving input refreshes

**Session.** FFR Wave 3, the transmission-expansion gate lane
(`docs/forecast-readiness-prompt-pack-2026-07.md` §FFR-SC). Branch
`claude/ff-g1-t1-f-transmission-ab-8z4yn6`, rebased onto `origin/main` **`edf5c5a`**
(main moved twice mid-session — see §9.1). Run concurrently with FFR-3A-2 and FFR-3F
under owner decision Addendum F.2 (rule 12's cap is per prompt).

**One-line result.** *(filled in §4)*

> **⚠ THIS DOCUMENT IS INCOMPLETE AS COMMITTED.** §§2–5 are placeholders: the paired
> CAISO arms had not finished solving when this revision was pushed. §§1 and 6–9 are
> final and stand on their own (the PJM inertness measurement, both input refreshes,
> the MISO block). Do not cite an A/B result from this revision — there is none yet.

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

*(filled in §4)*

## 3. Invariants

*(filled in §4)*

## 4. Measured result — interface, flows, prices

*(filled in §4)*

## 5. What this A/B does NOT establish

*(filled in §5)*

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

### 9.4 Pre-existing test failures, unchanged by this session

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

### 9.5 The `data/clean` prerequisite, re-measured

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

