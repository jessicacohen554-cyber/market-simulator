# FINDING capx-D14 — NEISO's first T1-X crossover: FC-4 measured, and NEISO is the first ISO holding §2.1b legs (a)+(b)+(c)

**Session.** capx-D14 (capacity-expansion / Forecast Finalization track), chartered at director
refresh #13 (`docs/handoffs/capx-director-ledger-2026-08.md` §0j.4, lane D14) under the owner's
Q7 ruling (leg (c) closes on a MEASURED FC-4 — the card A-A reading made uniform, 2026-08-30).
Branch `claude/capx-d14-neiso-t1x-r2yt44`, solved at **`8412c3f6`** (origin/main fetched
in-session, clean tree — recorded in the bundle's own `run_config.json` git block); rebased onto
`df03eec0` (post-D13/D5) before the board edit. 2026-08-30.

**Nothing is promoted. Nothing is tuned.** No `ScenarioConfig` default moved, no band widened,
no parameter adjusted in response to any score. FC-4 is reported at full magnitude, whatever it
says, and the registration was never conditional on it (charter: "do not withhold registration
on a miss").

---

## 0. Headline

**NEISO now has a T1-X crossover — the first in its history — and FC-4 is MEASURED AND
REPORTED: FAIL on the dispatch-skill row, quarantine row PASS, determination HOLD.** Registered
as run `neiso-2023-2027-crossover-capxd14`, live verdict key **`neiso-t1x`** (new — nothing
displaced). **§2.1b leg (c) CLOSES on this measurement** under the owner's Q7 ruling: the leg
requires FC-4 *measured and reported*, not passing — exactly how ERCOT/PJM/MISO (all FC-4 FAIL)
carry a passing leg (c) since D13 executed Q7.

**NEISO IS NOW THE FIRST ISO IN PROGRAM HISTORY WITH LEGS (a)+(b)+(c) ALL SATISFIED**: (a) PASS
(keeper `2026-08-17-neiso-99-joint-p1`, CALIBRATED, `complete` marker) · (b) PASS (bare
`neiso-t1f`, PROMOTE-WITH-CAVEATS, the S-4V re-score) · (c) PASS on this measurement. **Only leg
(d) remains — the explicit per-campaign owner authorization. This session does NOT request it
and cannot grant it**; the gate stays `open: false`.

Three findings beyond the gate mechanics, all reported rather than acted on:

1. **NEISO does NOT reproduce the program-wide crossover CO2 miss — and it is the SECOND
   counter-example, sharpening D5's diagnosis.** CO2 gap **+12.8 % / +10.6 % / −2.3 %**
   (2023/2024/2025) against ERCOT 43–51 %, PJM 42–57 %, MISO 60–77 %. Lane D5 (merged
   mid-session, `FINDING-capx-d5-crossover-co2-2026-08-30.md`) established that the three-ISO
   miss is dominated by a scoring-taxonomy drop (model-class `COAL` generation dropped from the
   bench-keyed intensity sum) that needs a *material coal fleet* to bite. NEISO's coal family is
   0.2–0.3 TWh actual and the model dispatches ≤0.085 TWh of it, so the drop is bounded ≲0.4 %
   of scored CO2 here — immaterial, exactly as D5's mechanism predicts for a no/low-coal ISO.
   NEISO's miss is honest **gas-volume error, positive sign** (over-dispatch → over-CO2), the
   NYISO control pattern (10.1/10.3/3.9 %).
2. **NEISO is the FIRST crossover leg in the program whose scored window executes economic
   exits — it is NOT a retirement-rule structural null.** 3,563 MW exit, all in 2024, all
   reason `economic` (36 tranche records: gas_cc 3,128 MW + gas_st 435 MW), against 4,997 MW
   actual (−28.7 %). Every prior T1-X (ERCOT per FFR-3L, PJM/MISO per FFR-3A-3/-4, NYISO per
   D10 §5) executed zero economic exits in-window, so their retirement bands could not test the
   screen. NEISO's can, and what it shows is a **composition miss**: the screen concentrates
   the exit wave in gas (over-retiring gas_cc 3.128 vs 1.884 GW actual) and misses the
   biomass/coal/gas_ct/oil exits entirely (recall 2/6 reachable ≥300 MW targets).
3. **The price miss is concentrated in 2025 (−21.8 %, input-gap 13.2×), with 2023 +13.3 %
   (CAVEAT, gap 4.3×) and 2024 +7.9 % (PASS, gap 1.4×).** The sign flips at 2025 exactly as
   NYISO's did (−24.0 % there), and the 13.2× ratio carries a denominator effect — the keeper's
   2025 error is only 1.65 % — but the numerator is large in absolute terms, so the gap is
   real. The 2024 exit wave (finding 2) sits between the over-priced years and the under-priced
   one; that adjacency is reported as an observation, **not attributed** (no control arm was
   run).

## 1. What ran, and the posture verification

```
uv run python scripts/run_capacity_hindcast.py --iso NEISO --crossover --vintage 2023 \
    --start-year 2023 --end-year 2027 \
    --out-dir results/hindcast/neiso-2023-2027-crossover-capxd14
```

**Every solve-affecting flag omitted** (the FFR-3A-4 / D10 posture precedent), and the posture
verified in the **resolved** artifacts — `run_config.json` (written from the bundle's own
resolved config.yaml), `meta.json` (built from the seam-resolved config) and the startup log all
agree:

| field | resolved value |
|---|---|
| mode / hindcast | `forecast` / `True` (crossover: no backcast overlay fires; `outage_source='statistical'`) |
| `retirement_rule` | `pipeline` |
| `entry_rate_limits` / `entry_commissioning_lag` / `entry_lookahead_reprice` | `True` / `True` / `True` |
| `correlated_forced_outage` | `True` — **runtime-confirmed no-op ×5** ("armed but no curve/weather coverage — no-op", once per solve year; `CORRELATED_OUTAGE_CURVE` is `['ERCOT']` only — the FFR-3A-2 §3.2b structural inertness, on NEISO's own evidence) |
| `exit_rate_limits` | `False` (D-8 default-OFF, honoured) |
| `hindcast_verified_announced_exits` | `True` (harness default since the 2026-08-22 owner directive) |
| `capacity_market_clearing_by_iso` | `{PJM, MISO, CAISO, NEISO: True}` — **NEISO present ⇒ curve-ON**, the FF-2C flip posture the charter requires; meta records `capacity_clearing_posture: shipped`, `forced: False` |
| hydro accreditation | `HYDRO_ACCREDITATION_CREDIT_BY_ISO['NEISO'] = 1,396.472 / 1,899.5 = 0.7352` — the capx-S4 sourced factor, resolving as a shipped **constant** (not a flag), confirmed in the imported module at this HEAD |
| window | forward boundary 2026, gas fwd path `mid`, weather pinned 2025, fuel `realized` / `hindcast_realized`, vintage 2023 |

**Cache key `07e416f3f8072e7c` — the ex-ante prediction, the launch banner and the on-disk
solved key are all IDENTICAL.** A pre-launch attestation (written before the solve) recorded the
resolved-preflight key from `build_config → apply_iso_scenario_defaults`. Unlike NYISO (the
no-override ISO), NEISO's request and resolution **differ**: `apply_iso_scenario_defaults` arms
its production ORDC scarcity footing (6 fields: `scarcity_price_overlay` True, `ordc_voll` 2000,
`ordc_mcl_mw` 1200, `ordc_lolp_sigma_mw` 900, `ordc_lolp_shift_sigma` 0.0,
`ordc_multistep_floor` False), so the request-side key `9fe2a133319db8ca` is NOT the run's key —
the FFR-3A-2 §1.2 trap, measured ex ante rather than tripped over.

Solved `[2023, 2024, 2025, 2026, 2027]`, bridged `[]`; **solve-year parity held** (the runner's
rule-22 STOP-THE-LINE assertion did not fire); `leakage_violations: []`. Wall **≈ 6.8 min**
(20:38:24 → 20:45:13 UTC), observed RSS ~2.5 GB early in year 2023 (peak not sampled mid-solve;
bookkeeping kept outside the solve window per FFR-3A-4 §6.2). NEISO contended for no heavy slot
(fresh container, nothing else running; the owner's MISO backcast solve lives in another
environment).

Two environment notes for successors, neither a defect of this leg:

- The container ships no Python env (`uv sync` first — FFR-3A-2 §0.2) and no `data/clean`
  (`scripts/regenerate_clean.py`, ~50 min here; the only failure was `miso-m2m-flowgates`, whose
  raw is outside the `neiso` hydration profile — irrelevant). *(That failure had a second cause,
  now gone: the mirrors were absent from git entirely; tracked since 2026-08-30 —
  `miso-m2m-flowgates-raw-mirror-2026-08.md` — so a fully-hydrated tree regenerates 51/51.)*
- The runner logs `NEISO zonal load file not found (data/raw/zone-specific-demand/NEISO/
  NEISO_load_hourly_2025.csv); skipping`. This is a property of the repository, not the session:
  the clone is FULL (hydration reported every blob local) and **no `NEISO/` subtree exists under
  `zone-specific-demand/`** — `parse_neiso_shares` returns None and the shipped fallback zonal
  shares apply, identically to every prior NEISO leg (keeper, T1-F, T1-H) on this data surface.

## 2. FC-4 — the measurement, at full magnitude

Bands (pre-registered, `forecast_verdict.py`): NEISO **K_iso = 1.5** (the strict tier) ⇒
price/CO2 PASS ≤ 10 % < CAVEAT ≤ 15 % < FAIL; gas/coal TWh PASS ≤ 5 % < CAVEAT ≤ 7.5 % < FAIL.

| FC-4 row | verdict | detail |
|---|---|---|
| quarantine | **PASS** | ≥2026 refusal marker present and clean (`read_ge_2026: False`, `scored_max_year: 2025`) — no H1-2026 actual read |
| dispatch skill | **FAIL** | rows below |
| input-gap ratio | report-only | rows below |

| metric | 2023 | 2024 | 2025 |
|---|---|---|---|
| price (C3a lw-mean) | **+13.3 % CAVEAT** | **+7.9 % PASS** | **−21.8 % FAIL** |
| CO2 (C5a full-plant) | **+12.8 % CAVEAT** | **+10.6 % CAVEAT** | **−2.3 % PASS** |
| gas_twh (±5 % family) | **+14.8 % FAIL** | **+12.6 % FAIL** | −4.5 % — *uncovered* (preliminary EIA-923 vintage; all five gas classes incomplete — reported, not banded) |
| coal_twh | **−99.7 % FAIL** | **−66.4 % FAIL** | −70.9 % — *uncovered* (same vintage; COAL_BIT incomplete) |

10 banded rows, 2 uncovered — every uncovered row declared with its reason, never passed.
Coverage honesty note the charter asked for: the preliminary-vintage gap NEISO hits is the same
one D10 hit in NYISO (2025 fuel volumes), plus NEISO's coal family: `coal_twh` IS banded here
for 2023/2024 (NYISO's never was — no coal), but on a **0.2–0.3 TWh family** (model 0.001/0.085
vs actual 0.203/0.254 TWh): a −99.7 % headline on a family that is <0.3 % of ISO load. The
keeper's own coal misses are 60.1/50.0 % on the same tiny denominators.

**Input gap** (`|forecast_err| / |keeper_backcast_err|`; keeper at this HEAD =
`2026-08-17-neiso-99-joint-p1`, whose committed determine() records the scorer read):

| metric | 2023 | 2024 | 2025 |
|---|---|---|---|
| C3a price mean | +13.3 % vs |3.1 %| → **4.3×** | +7.9 % vs |5.7 %| → 1.4× | −21.8 % vs |1.7 %| → **13.2×** |
| C3b monthly NRMSE | 0.324 vs 0.088 → 3.7× | 0.403 vs 0.159 → 2.5× | 0.547 vs 0.054 → **10.1×** |
| C1 fuel-mix TWh gap | 9.46 vs 0.88 → **10.8×** | 7.93 vs 0.70 → **11.4×** | unscored (preliminary vintage) |
| gas_twh | +14.8 % vs 0.6 % → 23.9× | +12.6 % vs 0.3 % → 37.1× | (reported-only) |
| CO2 | keeper side unscored (no C5a scalar in determine() records — C5a reported-only since rubric v2.9) → gap None ×3 | | |

Reading, stated without tuning anything: the forecast input stack **over-dispatches gas**
(+8.0 / +7.4 TWh family volume 2023/2024, concentrated in CC_REGULAR: +7.2 / +6.1 TWh) and
correspondingly **over-prices and over-emits 2023/2024**; 2025 flips sign on price (−21.8 %)
with gas volume also flipping under (−4.5 %, uncovered). 2024 is the cleanest year (price PASS
at +7.9 %). The gas_twh input-gap ratios (23.9×/37.1×) are denominator-driven — the keeper's
gas errors are 0.6 %/0.3 % — but the numerators are +8.0/+7.4 TWh, so the gap is real.

**Capacity events 2023–2025** (vs registry actuals, decision basis): retirements **FAIL** —
model 3.563 GW vs actual 4.997 GW (−28.7 %), recall 2/6 reachable ≥300 MW targets; per-fuel:
gas_cc +66 % over (3.128 vs 1.884), gas_st −9 % (0.435 vs 0.480), biomass/coal/gas_ct/oil
0.0 vs 0.262/0.846/0.319/1.208 GW (missed entirely). Additions total 4.5 GW model vs 2.981
actual: solar **PASS** (+2.7 %, 2.0 vs 1.947 GW), wind FAIL (1.0 vs 0.225), gas_ct FAIL (0.5 vs
0.162), storage FAIL (0.0 vs 0.642 — the D-2 commissioning-lag censoring signature,
FFR-3A-2 §3.5), gas_cc SKIP (actual 0, model 1.0). On the COD basis every in-window addition is
0.0 — decisions of 2024/2025 commission in 2026/2027, outside the scored window by construction.

## 3. Verdict and registration (rule 15, forecast namespace only)

`forecast_verdict.py --tier t1x --crossover-score … --run-config …` → **determination HOLD** —
FC-1 SKIPPED (required, unscored — a crossover bundle carries no invariant record; the same
shape as every T1-X leg in the program) + **FC-4 FAIL**. **FC-7 reads CAVEAT, not FAIL** (DOF
ledger absent — the program-wide lane-D8 instrument gap): the bundle **tracks its own
`run_config.json`** (written natively by the runner — the FFR-3K fix), so this leg carries no
run_config debt. Provenance stamp: `scored_at_sha 8412c3f623e7`, `cache_epoch
07e416f3f8072e7c`, session `capx-D14-neiso-t1x`.

Registered:

- `frontend/data/forecast/ff-verdicts.json` — **new live key `neiso-t1x`** (157-line pure
  insertion; keys diffed before/after — nothing displaced, no preserve-then-overwrite needed
  since no prior NEISO t1x key ever existed).
- `scripts/register_forecast_run.py::VERDICT_MAP` — `neiso-2023-2027-crossover-capxd14 →
  neiso-t1x` (the bare per-tier key IS this run's own verdict, so the "never render a verdict
  the run's own score contradicts" rule is satisfied trivially — the D10 LIVE-vintage
  convention).
- `register_forecast_run.py --bundle …` — canonical sidecar
  `frontend/data/hindcast/neiso-2023-2027-crossover-capxd14.json`; namespace regenerated
  (generated files stay gitignored; the Pages deploy rebuilds them).
- Committed run artifacts under `results/hindcast/neiso-2023-2027-crossover-capxd14/`:
  `meta.json`, `run_config.json` (the FC-7 artifact) and the key dir's `crossover_score.json` —
  the same tracked set as the D10 bundle (`run_config.yaml`, `config.yaml`, `evolution_*.json`
  and the year parquets are gitignored by the standing `results/hindcast` patterns), which is
  what `rescore_forecast_verdicts.py` needs to re-score this verdict from a checkout.
- Report: `docs/hindcast-reports/neiso-2023-2027-crossover-capxd14-crossover-2026-08-30.md`.
- Board seed `frontend/data/forecast/program-status.json` — see §4. **The backcast registry was
  not touched** (plan §7.5), nor was any keeper shard, `status/*.js`, offer curve, commitment
  bridge, or `calibration-complete.json`.

## 4. The §2.1b gate: the (a)+(b)+(c) statement, and the board refresh

**Stated plainly, as the charter requires: NEISO now holds legs (a), (b) and (c) — the first
ISO in program history to hold all three — and leg (d), the explicit per-campaign owner
authorization, remains. No authorization exists, none is requested here, and the gate stays
`open: false`.**

Board refresh (on the post-D13 file — D13 merged mid-session and its Q7 harmonisation is kept
intact; my branch was rebased onto `df03eec0` before the edit, and the round-trip was verified
byte-identical before touching it):

- `isos.NEISO.t1x_determination`: `n/a` → `HOLD`.
- `isos.NEISO.gate.c_crossover_gap`: `fail` → **`pass`**, with the full-magnitude FC-4 record —
  the D13 annotation on that cell explicitly anticipated this lane.
- `isos.NEISO.gate.closed_on`: `['c','d']` → `['d']`; `open` stays `false`.
- `isos.NEISO.gate.note` rewritten (the (a)+(b)+(c) statement above); a T1-X row appended to
  `blocking_rows` explicitly marked "leg-(c) MEASUREMENT, not a T1-F blocker".
- Three top-level `headline` sentences D13 wrote that this measurement made stale are updated
  in place, in D13's own annotation style: "leg (c) now fails … NEISO and CAISO" → only CAISO;
  the program-lead leg list `(c) fail (genuinely unrun)` → `(c) PASS on measurement`; "an unrun
  crossover (NEISO)" → the measured-FAIL wording. This is exactly the top-prose-vs-blocks drift
  D13 existed to repair, not re-introduced.

Leg (b) is untouched and still PASS on the bare `neiso-t1f` key; leg (a)'s basis (keeper +
`complete` marker) is unread and unedited by this session.

## 5. Structural observations — reported, not acted on

- **The economic screen fires in-window (the program first, §0.2).** All 3,563 MW of model exit
  is reason `economic`, executed 2024, spread over 36 tranches. Do NOT read the −28.7 % level
  band as a screen-inertness null (the NYISO/MISO instruction inverts here): NEISO's T1-X CAN
  test the retirement rule, and what it measures is a gas-concentrated composition miss plus
  four missed non-gas fuels. The actuals it misses include the non-economic channels (the
  4.997 GW actual includes exits the announced/confirmed channels under this vintage's
  information gate do not carry) — so the band mixes screen skill with channel coverage,
  and this leg ran no control to separate them.
- **D-2's commissioning lag is visible exactly as designed**: decision-basis additions 4.5 GW
  vs COD-basis 0.0 GW in-window — entry decided 2024/2025 commissions 2026/2027, outside the
  scored window (the FFR-3A-2 §3.5 censoring, biting the storage band to 0.0 vs 0.642 actual).
- **`correlated_forced_outage` is runtime-confirmed inert in NEISO** (5/5 solve years no-op) —
  the pre-registered FFR-3A-2 §3.2b prediction, confirmed on NEISO's own evidence (rule 25
  clean).
- **The CO2 result strengthens D5** (§0.1): the second no/low-coal ISO lands at ~10 % with a
  positive (volume-driven) sign, while the three coal-heavy ISOs miss 43–77 % negative under
  the taxonomy drop D5 located. D5's repair lane, when it lands, is predicted to move
  ERCOT/PJM/MISO materially and NEISO/NYISO almost not at all — a falsifiable statement this
  leg's committed artifacts can check for free.
- **A crossover-construction note for decomposition work**: the weather year is pinned 2025, so
  2023/2024 demand is the 2025 weather-year load de-grown by compounded growth (factor 1.0262
  for 2023 — the runner's own banner line). The keeper backcast uses each year's own weather.
  Any future decomposition of the 2023/2024 gaps should carry that construction term
  explicitly, as D10 §6 did for NYISO's hydro construction.

## 6. Governance attestation

- Holdout spend freeze **ACTIVE** (tier-scoped: locked test 2019/H1-2026, every ISO) — printed
  by the runner at launch, never worked around. **No marker consulted or spent**: the crossover
  window is freeze-legal by construction (solves = training years + forecast forward years).
  No out-of-training backcast year solved, scored, or registered; the scorer's quarantine row
  **PASS** is the machine check of the same claim, and the ≥2026 half ran forecast-mode with no
  measured overlay (`outage_source='statistical'`, FC-7 overlay-off row PASS).
- Scoring read **only committed benchmark artifacts** (`bench/NEISO/2023..2025.json.gz`, the
  capacity actuals registry, the keeper's committed determine() records). No measured outcome
  was fed back (rule 13); nothing was re-derived (rule 21); no off-registry knob (rule 24 — the
  one code edit is the VERDICT_MAP registration entry, not a tunable). Nothing was
  reverse-engineered to clear an invariant; FC-4's FAIL and every uncovered row stand as
  measured.
- **Mechanism matrix: no cell minted, by charter** — running an existing instrument on a new
  ISO tests no mechanism; nothing was armed, so no NEISO shard edit. The
  `mechanism-matrix-guard` CI WARN on a run registration without a matrix touch is expected and
  acceptable (a WARN, not a gate).
- Instrument notes: the FFR-3A-4 §6 blockers again did not reproduce — the branch pre-existed
  (harness-created), `git push` carried the commits with no 413, the run-id collision guard had
  nothing to refuse (fresh id), FC-7's run_config row is satisfied natively. The one live trap
  remains `pgrep` self-matching (use `ps -eo rss,args | grep "[r]un_…"`, used here). Mid-session
  merges (D13 board reconcile, D5 CO2 diagnosis) were absorbed by rebase before the board edit;
  D5 changed no code, so this leg's scoring surface was never moved under it.

## 7. For the successor

1. **The leg is registered and re-scorable from the checkout.** Do not re-run it without new
   evidence; a re-score goes through `rescore_forecast_verdicts.py` / `forecast_verdict.py` on
   the committed artifacts.
2. **S-4b (ARA requirement re-vintage) dispatches now that D14 has merged** — it shares
   ff-verdicts.json and the NEISO board block, which is why it was sequenced strictly after
   this lane. Its pre-declared arithmetic can re-tighten the T1-F years; that is leg (b)'s
   surface, not this leg's.
3. **Do NOT carry the "crossover retirement bands are structural nulls" instruction onto
   NEISO** (§5 — the instruction is ISO-specific and inverts here; FFR-3A-4 §8.2 and D10 §8.3
   remain correct for MISO/NYISO).
4. **The 2025 price face (−21.8 %, 13.2× gap) is the biggest unexplained object this leg
   surfaced**, the NYISO-2025 sign twin at NEISO magnitude. It is a forecast-input-stack
   question (realized fuel + realized demand are already in), with two named construction terms
   to carry in any decomposition: the pinned-2025-weather de-growth (§5) and the 2024 exit
   wave's 2025 fleet effect. Unowned; worth a charter only after D5's repair lands.
5. **Gate arithmetic**: leg (a) pass · (b) pass · (c) pass (measured) · (d) none. The gate
   stays `open: false`; nothing here schedules a full-horizon campaign — leg (d) is the
   owner's, every time.
