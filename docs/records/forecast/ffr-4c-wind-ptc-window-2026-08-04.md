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

## 3. Measurement — paired MISO capacity hindcast (MEASURED)

```
uv run python scripts/run_capacity_hindcast.py --iso MISO --fuel-variant realized \
  --vintage 2020 --start-year 2021 --end-year 2025 --entry-screen-diagnostics \
  --out-dir results/ffr4c/miso-ptcwindow-treatment            # window=10 (shipped default)
uv run python scripts/run_capacity_hindcast.py --iso MISO --fuel-variant realized \
  --vintage 2020 --start-year 2021 --end-year 2025 --entry-screen-diagnostics \
  --ptc-window none --out-dir results/ffr4c/miso-ptcwindow-control   # unwindowed
```

Both arms at THIS session's fix commit; the ONLY delta is the window field
(one field: treatment key `ca36ba26ebe1640f`, control key `18688555edc0342a`).
Run sequentially in the end — the concurrent launch OOM-killed the treatment
arm ~40 s in (exit 137; two simultaneous MISO LP builds exceed this
container's 15 GB), which is rule 12's own memory bound binding at 1, not a
protocol deviation. Committed evidence: the evolution ledgers + config/meta
under `results/ffr4c/` (slim files; year parquets untracked).

**Control arm first — it validates the baseline.** Every screen number
reproduces FFR-3V's registered leg to the digit (wind margins +32,172 /
+34,210 / +19,165 / +18,687; builds 4,000/0/4,000/0 alternating
`per_tech_cap`/`per_tech_cap_zero`; in-window commissioned wind 4.0 GW;
`ptc_wind_levelized_per_mwh` = 26.0). Base drift 2c412668 → 5eac75b0 is ZERO
on this screen.

**Treatment vs prediction — §2 scores 5-for-5, three margins to the dollar:**

| decision yr | § 2 predicted margin | measured | wind builds |
|---|---|---|---|
| 2022 | −9,000 | **−9,001** | 0 (`unprofitable`) |
| 2023 | −6,962 | **−6,962** | 0 (`unprofitable`) |
| 2024 | −22,007 | **−22,007** | 0 (`unprofitable`) |
| 2025 | −22,485 | **−21,516** | 0 (`unprofitable`) |

* **Headline: MISO in-window wind economic entry falls 4.0 GW → 0.0 GW**
  against 7.2 GW actual (additions band −44.4 % → −100 %). Wind is
  `unprofitable` in all four decision years; `entry_decided_mw_by_tech`
  carries no wind anywhere in the window. Exactly the pre-registered result.
* `ptc_wind_levelized_per_mwh` = **13.6315** (treatment) / **26.0** (control),
  `ptc_wind` nominal 26.0 in both — item 5 exact.
* **Solar rows 2022–2024 byte-identical across arms** (−26,446 / −22,681 /
  −35,946, all `unprofitable`) — item 3 exact; the window touches wind only.
  Gas rows 2022–2024 byte-identical too.
* **The single off-by-$969 cell (2025) is the pre-registered second-order
  coupling of item 4, and it decomposes exactly:** the treatment never
  commissions the control's 4 GW COD-2024 wind, so the 2025 decision year
  screens a tighter fleet — reserve margin 10.9 %/16.8 % vs the control's
  11.4 %/17.3 % in 2024/2025 (≈0.5 pp = the missing wind × ELCC on a
  114 GW peak). Wind's 2025 revenue is +$1,018 (76,589 vs 75,571) and its
  cost +$49 (the arm builds no wind, so the Wright wind stock sits slightly
  lower), +1,018 − 49 = **+969**. Same channel on the other rows: 2025 solar
  −33,020 vs −33,406, and the 2025 gas capacity payment RISES ~$66 k/MW-yr
  (gas_cc margin +175,844 → +242,229) on the tighter VRR position — while
  both gas builds stay cap-bound and UNCHANGED at 3,000 / 1,483.8 MW
  (item 4's "built MW should not move" holds).

**Verdict: the mechanism does exactly what the statute says and nothing
else.** The correction moves the wind additions band AWAY from the actual
(−44 % → −100 %), the owner signed knowing it (Addendum O.2), and the fix
stays in under rule 1 `[R-STRUCT]`.

## 4. Open root cause (rule 11) — DISCOVERED WIND UNDER-BUILD, handed on

The statutory window removes $41,172/MW-yr of never-real revenue from the
wind screen, and with it MISO wind entry goes to zero against 7.2 GW actually
built. **That gap is now an honest, named residual instead of a coincidence
of two offsetting errors** (an over-credited PTC papering over an
under-represented revenue stack). Measured bounds on where the real revenue
is missing, all from this session's own ledgers and FFR-3V's:

* Wind's four windowed margins miss break-even by only **$7.0–22.5 k/MW-yr**
  — small against the identified omissions below.
* **RA accreditation:** `entry_vre_capacity_revenue` is default-off, and in
  the 2025 decision year the treatment arm's own VRR pays a new gas CC
  $389,172/MW-yr of capacity revenue while wind is denied any share; MISO's
  published wind capacity credit is intaken on disk and unwired
  (FFR-3V §4.6b — the same gate FFR-4B's D-2′ lane is probing from the
  solar side).
* **The IRP/PPA procurement channel** (FFR-3V §7.1): the real builder of
  MISO renewables, represented nowhere in `apply_economic_new_entry`.
* **The scarcity-less lookahead signal** (FFR-3V §3.2): the 2024 entry
  price series' max is $39/MWh, so every technology whose economics live in
  a tail is under-revenued at the screen.

Rule-1 boundary, restated for the next lane: do NOT re-inflate the credit,
soften the window, or add an adder to buy the band back — the fix is on the
revenue side, through mechanisms that exist in the real market. FFR-4B
(D-12 + D-2′) is already working the same seam from the solar direction;
these measurements sit on the PRE-4B side and should be re-based if 4B's
entry-revenue changes land first.

**Post-rebase note (same session).** FFR-4B merged to main after §3 was
measured, and this branch was rebased over it. Both arm cache keys are
BYTE-IDENTICAL at the post-merge head (`ca36ba26ebe1640f` /
`18688555edc0342a`), i.e. the §3 harness commands still build exactly the
measured configs — 4B's D-2′ arming was probe-scoped (its own explicit
flags), not a shipped-default flip, so the §3 numbers stand as the pre-4B
baseline without adjustment. (The epoch was also re-lettered
**2026-08-04d** in the rebase: FFR-4D's concurrently-landed CAISO entry
took `c`.) Whichever lane next arms D-2′ or the D-12 accreditation for
MISO wind should quote the §3 control/treatment pair as its own baseline
and re-run both arms at its head.

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
