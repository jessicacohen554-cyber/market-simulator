# FFR-4C — §45 wind PTC windowed to its statutory 10 years

**Session:** ffr-4c, 2026-08-04. **Bounded lane, owner decision D-13** (sitting
Addendum O). Zero free parameters: one published statutory number, 10 years.
Base commit `5eac75b0` (origin/main at session start) — **all measurements in
this doc sit on the PRE-4B side**: no FFR-4B (D-12 + D-2′) commit had landed
when the paired arms were built or run.

## 1. What changed

The defect (measured by FFR-3V, `ffr-3v-miso-entry-screen-2026-08-04.md` §6.2
and §4): the new-entry screen credited the §45 wind PTC over the plant's full
30-year book life, while the solar ITC in the same file was booked correctly —
the mechanical origin of the MISO T1-H leg's inverted tech mix (model wind
share 43.7 % / solar 0.0 % vs actual 22.5 % / 58.3 %).

The remedy reuses the existing §45Q pattern (rule 19 `[R-ONE-MECH]`), one
levelization construction shared by both credits:

* **`ScenarioConfig.ira_ptc_credit_window_years: int | None = 10`** — statutory:
  26 U.S.C. §45(a)(2)(A)(ii) ("during the 10-year period beginning on the date
  the facility was originally placed in service"); §45Y(b)(1)(B) is identical
  for the tech-neutral successor. `None` = indefinite-extension / control arm
  (reproduces pre-4C crediting exactly). Registered in
  `_CACHE_KEY_OPTIONAL_FIELDS` (+ recorded default "10") and `TIER_TAGS` (2).
* **`new_entry.wind_ptc_levelized_per_mwh(config)`** — the ONE computation
  site: credit × CRF(life)/CRF(min(window, life)) at the screen's own wind
  discount rate, exactly the §45Q construction (`_ccs_45q_window_years`,
  `_emerging_lcoe`'s gas_cc_ccs branch). `compute_lcoe`'s wind branch and
  `policy.ira.apply_ira_credits_to_lcoe`'s wind branch both delegate to it.
  At the shipped wind record (30-yr life, 5.675 % real): factor **0.52429**,
  effective credit **$26.00 → $13.63/MWh** — matching FFR-3V §6.2's
  independent arithmetic to the digit.
* **Eligibility unchanged:** the `ira_wind_solar_last_year` OBBBA cliff still
  decides *whether* a vintage earns; the window only decides *how much* an
  earning vintage's credit is worth per levelized MWh. The DISPATCH-side PTC
  (flat `-ira_ptc_wind` wind offer, default-off `wind_ptc_vintage_offers`) is
  a separately-adjudicated surface, untouched.
* **Cache:** same-key invalidation by design — a default-config run hashes as
  before (pinned `603c2498bf71d21d` byte-stable) while forecast-lane results
  change. Recorded as **cache epoch 2026-08-04d** in `results/cache.py`
  (backcast bundles and keepers NOT invalidated; capacity evolution does not
  run in a backcast). An explicit `None` control hashes distinctly.
* **Harness:** `run_capacity_hindcast.py --ptc-window` (omit = shipped
  default; `none` = unwindowed control; integer = sensitivity).
* **Tests:** credit stops at year 10 of plant life (PV-equivalence assert),
  `None` restores full-life crediting, window ≥ life clips to life, solar ITC
  path byte-identical across window settings, both call sites agree (one
  mechanism), non-positive window rejected. Stale unwindowed assertions in
  `test_capacity.py` / `test_emerging_tech.py` updated.

## 2. PREDICTION — recorded BEFORE measurement

Written and committed before either arm was launched. Derived from FFR-3V's
measured instrumented ledgers (solve `ca36ba26ebe1640f` — whose cache key, as
a cross-check of the epoch note, is byte-identical to this session's TREATMENT
arm key at the same flags) plus the measured levelization factor:

* The wind credit inside `annual_cost` is `PTC × 8760 × base_cf(0.38)`:
  unwindowed **$86,549/MW-yr** → windowed **$45,377/MW-yr**, a
  **−$41,172/MW-yr** hit to wind's screened margin in every decision year
  (year-independent: rate, life and base_cf are year-independent and the
  nominal rate is flat through the 2027 cliff).
* FFR-3V's measured MISO wind margins are +32,172 / +34,210 / +19,165 /
  +18,687 $/MW-yr for decision years 2022/2023/2024/2025 — **all smaller than
  $41,172** — so:
  1. **Wind flips unprofitable in ALL FOUR decision years** (predicted margins
     ≈ −9,000 / −6,962 / −22,007 / −22,485), `binding_cap: "unprofitable"`.
  2. **MISO wind economic entry falls 4.0 GW → 0.0 GW decided in-window;
     commissioned-in-window falls 4.0 → 0.0 GW against 7.2 GW actual** (band
     −44.4 % → −100 %).
  3. Solar rows byte-identical to control (−26,446 / −22,681 / −35,946 /
     −33,406, all `unprofitable`, 0 MW) — the window touches wind only.
  4. 2022–2024 thermal rows unchanged (capacity payment $0 all techs); 2025
     gas_cc/gas_ct still build ≈3,000 / ≈1,484 MW — second-order shifts in
     their 2025 margins possible (the treatment removes the control's 4 GW
     COD-2024 wind, slightly tightening the 2024–2025 fleet the 2025 screen
     prices), but both were cap-bound, so built MW should not move.
  5. Ledger cross-check: `ptc_wind_levelized_per_mwh` = 13.6315 (treatment) /
     26.0 (control); `ptc_wind` (nominal) = 26.0 in both.
* **Control arm** (`--ptc-window none`, same code, same commit): reproduces
  FFR-3V's ledger to the digit — wind +32,172 in 2022, builds 4,000 MW at
  `per_tech_cap`, etc. If it does not, base drift 2c412668→5eac75b0 is doing
  it and the control is the comparator, not FFR-3V's numbers.

**Expected direction is AWAY from the actual (owner signed knowing this,
Addendum O.2).** MISO wind moves 4.0 → 0.0 GW against 7.2 GW actual. Under
rule 1 `[R-STRUCT]` the statutory window stays in regardless; the enlarged
wind under-build becomes a named open root cause on wind's revenue side (§4).

## 3. Measurement — paired MISO capacity hindcast (PENDING — filled in after the runs)

```
uv run python scripts/run_capacity_hindcast.py --iso MISO --fuel-variant realized \
  --vintage 2020 --start-year 2021 --end-year 2025 --entry-screen-diagnostics \
  --out-dir results/ffr4c/miso-ptcwindow-treatment            # window=10 (shipped default)
uv run python scripts/run_capacity_hindcast.py --iso MISO --fuel-variant realized \
  --vintage 2020 --start-year 2021 --end-year 2025 --entry-screen-diagnostics \
  --ptc-window none --out-dir results/ffr4c/miso-ptcwindow-control   # unwindowed
```

Both arms at THIS session's fix commit; the ONLY delta is the window field
(one field, two cache keys). Launched concurrently (rule 12), years sequential
within each.

## 4. Open root cause (rule 11) — handed on, not fixed here

To be written against the measured result: the statutory window removes
≈$41k/MW-yr of non-real revenue from the wind screen; whatever true revenue
the screen still lacks (RA accreditation via `entry_vre_capacity_revenue` +
MISO's on-disk-but-unwired wind/solar ELCC, the missing IRP/PPA procurement
channel FFR-3V §7.1 names, the scarcity-less lookahead price signal FFR-3V
§3.2 measures) is now visible as a wind under-build instead of being papered
over by a 30-year credit. FFR-4B (D-12 + D-2′) touches the same revenue side
from the solar direction.

## 5. Same-defect finding REPORTED for owner chartering (not fixed, per scope)

**The geothermal PTC has the identical defect**: `apply_ira_credits_to_lcoe`'s
geothermal branch books the flat `ira_ptc_wind × ira_phaseout_fraction` with
no credit window over EGS's full book life, though the §45/§45Y 10-year credit
period applies to geothermal too. Deliberately left as-is (D-13's scope is the
wind PTC); the branch's docstring and a pinned test
(`test_geothermal_ptc_still_flat_wind_ptc_windowed`) mark it so the eventual
fix changes it knowingly. No other unwindowed production credit was found in
the entry screens: §45Q is windowed (12 yr), §45U/§45V/H2 are expiry-gated
$/MWh operating credits with no levelization over life, offshore wind carries
no credit at all, and the solar/storage ITCs are one-time capital credits
(correctly windowless).
