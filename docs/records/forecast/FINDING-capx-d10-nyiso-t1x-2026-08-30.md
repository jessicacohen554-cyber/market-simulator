# FINDING capx-D10 — NYISO's first T1-X crossover: FC-4 measured, §2.1b leg (c) closes on measurement

**Session.** capx-D10 (capacity-expansion / Forecast Finalization track), chartered by the
owner's card-A signature (A-A, 2026-08-25 —
`docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md` §5) and the director's ledger
lane D10 (`docs/handoffs/capx-director-ledger-2026-08.md` §1). Branch
`claude/capx-d10-nyiso-t1x`, solved at **`3ebbd466fc4f`** (origin/main fetched in-session,
clean tree — recorded in the bundle's own `run_config.json` git block). 2026-08-30.

**Nothing is promoted. Nothing is tuned.** No `ScenarioConfig` default moved, no band
widened, no parameter adjusted in response to any score. FC-4 is reported at full
magnitude, whatever it says, and the registration was never conditional on it (charter:
"do not treat a miss as a reason to withhold registration").

---

## 0. Headline

**NYISO now has a T1-X crossover — the first in its history — and FC-4 is MEASURED AND
REPORTED: FAIL on the dispatch-skill row, quarantine row PASS, determination HOLD.**
Registered as run `nyiso-2023-2027-crossover-capxd10`, live verdict key **`nyiso-t1x`**
(new — nothing displaced). **§2.1b leg (c) CLOSES on this measurement** under the
owner-signed card-A reading: the leg requires FC-4 *measured and reported*, not passing —
exactly how ERCOT/PJM/MISO (all FC-4 FAIL) carry a passing leg (c).

Two findings beyond the gate mechanics, both reported rather than acted on:

1. **NYISO does NOT reproduce the program-wide crossover CO2 miss.** Its CO2 gap is
   **10.1 % / 10.3 % / 3.9 %** (2023/2024/2025) against ERCOT 43–50 %, PJM 43–58 %,
   MISO 63–76 %. Two years a hair over the 10 % commercial band (CAVEAT), one PASS.
   Direct evidence for lane D5 that the CO2 derivation question is not universal.
2. **The price miss is concentrated in 2023 (+29.9 %, input-gap 30.2×) and 2025
   (−24.0 %, gap 2.0×), with 2024 essentially at keeper skill (+2.5 %, gap 1.28×).**
   The 2023 gap is the largest input-gap ratio measured in any crossover leg to date —
   driven jointly by a large forecast-side error and the keeper's repaired 2023 skill
   (+1.0 % post-PAR-attribution).

## 1. What ran, and the posture verification

```
uv run python scripts/run_capacity_hindcast.py --iso NYISO --crossover --vintage 2023 \
    --start-year 2023 --end-year 2027 \
    --out-dir results/hindcast/nyiso-2023-2027-crossover-capxd10
```

**Every solve-affecting flag omitted** (the MISO FFR-3A-4 posture precedent), and the
posture verified in the **resolved** artifacts, never the request:

| field | resolved value (run_config.json ← the bundle's own config.yaml; meta.json and the startup log agree) |
|---|---|
| mode / hindcast | `forecast` / `True` (crossover: no backcast overlay fires) |
| `retirement_rule` | `pipeline` |
| `entry_rate_limits` / `entry_commissioning_lag` / `entry_lookahead_reprice` | `True` / `True` / `True` |
| `correlated_forced_outage` | `True` — **runtime-confirmed no-op ×5** ("armed but no curve/weather coverage — no-op", once per solve year; the FFR-3A-2 §3.2b structural inertness, NYISO has no `CORRELATED_OUTAGE_CURVE` entry) |
| `exit_rate_limits` | `False` (D-8 default-OFF, honoured) |
| `hindcast_verified_announced_exits` | `True` (harness default since the 2026-08-22 owner directive) |
| `capacity_market_clearing_by_iso` | `{PJM, MISO, CAISO, NEISO: True}` — **NYISO absent ⇒ curve-OFF**, the FF-2C flip posture; meta records `capacity_clearing_posture: shipped`, `forced: False`. The R5a Option B question was not touched. |
| window | forward boundary 2026, gas fwd path `mid`, weather pinned 2025, fuel `realized` / `hindcast_realized` |

**Cache key: `7323dc2ddabc95c7` — request-side prediction, resolved preflight, and the
on-disk solved key are all IDENTICAL.** The NYISO no-override property FFR-3A-2 §2.3
recorded (the one ISO whose request and resolution coincide) held again at this HEAD, and
was verified ex ante (pre-launch attestation written before the solve).

Solved `[2023, 2024, 2025, 2026, 2027]`, bridged `[]`; **solve-year parity held**
(the runner's rule-22 STOP-THE-LINE assertion did not fire); `leakage_violations: []`.
Wall ≈ **10.1 min** (18:13:25→18:23:30 UTC; per-year P0 73–96 s, P1 33–76 s). Peak RSS
was deliberately not sampled mid-solve (bookkeeping kept outside the solve window per
FFR-3A-4 §6.2); the NYISO T1-F anchor is 2.82 GB and free memory never pressured 12 GB.
The mid-session S-5 landing (`hold-last-FPR`) was checked before launch: the FPR table
is **PJM-only**, so the change is provably inert for this leg.

## 2. FC-4 — the measurement, at full magnitude

Bands (pre-registered, `forecast_verdict.py`): NYISO **K_iso = 1.5** (the strict tier) ⇒
price/CO2 PASS ≤ 10 % < CAVEAT ≤ 15 % < FAIL; gas/coal TWh PASS ≤ 5 % < CAVEAT ≤ 7.5 % < FAIL.

| FC-4 row | verdict | detail |
|---|---|---|
| quarantine | **PASS** | ≥2026 refusal marker present and clean (`read_ge_2026: False`, `scored_max_year: 2025`) — no H1-2026 actual read |
| dispatch skill | **FAIL** | rows below |
| input-gap ratio | report-only | rows below |

| metric | 2023 | 2024 | 2025 |
|---|---|---|---|
| price (C3a lw-mean) | **+29.9 % FAIL** | **+2.5 % PASS** | **−24.0 % FAIL** |
| CO2 (C5a full-plant) | **+10.1 % CAVEAT** | **+10.3 % CAVEAT** | **+3.9 % PASS** |
| gas_twh (±5 % family) | **+21.0 % FAIL** | **+19.8 % FAIL** | +5.9 % — *uncovered* (preliminary EIA-923 vintage; reported, not banded) |
| coal_twh | *uncovered ×3 — family not benchmarked for NYISO* | | |

8 banded rows, 4 uncovered — every uncovered row declared with its reason, never passed.

**Input gap** (`|forecast_err| / |keeper_backcast_err|`; keeper at this HEAD =
`2026-08-30-nyiso-157-par-attribution`, promoted the same day):

| metric | 2023 | 2024 | 2025 |
|---|---|---|---|
| C3a price mean | +29.9 % vs +1.0 % → **30.2×** | +2.5 % vs +2.0 % → 1.28× | −24.0 % vs −12.0 % → 2.00× |
| C3b monthly NRMSE | 0.337 vs 0.116 → 2.9× | 0.252 vs 0.173 → 1.46× | 0.394 vs 0.203 → 1.94× |
| C1 fuel-mix TWh gap | 24.1 vs 5.1 → 4.75× | 24.3 vs 7.0 → 3.46× | unscored (preliminary vintage) |
| gas_twh | +21.0 % vs +1.5 % → 14.4× | +19.8 % vs +2.1 % → 9.4× | (reported-only) 2.85× |
| CO2 | keeper side unscored (no C5a scalar in the keeper's determine() records — C5a is reported-only since rubric v2.9) → gap None ×3 | | |

Reading, stated without tuning anything: the forecast input stack **over-dispatches gas**
(+12.4 / +12.6 TWh family volume 2023/2024) and correspondingly **over-prices 2023**;
2025 flips sign (−24.0 %) in the same direction as the keeper's own open C3a-2025 object
(−12.0 %, the owner-court offer-level face) at twice the depth. 2024 is the clean year on
both sides. The 2023 30.2× ratio has a denominator effect in it — the keeper's 2023 error
is only −1.0 % since the PAR-attribution repair — but the numerator is large in absolute
terms (+29.9 %), so the gap is real, not an artifact of a near-zero denominator.

**Capacity events 2023–2025** (vs registry actuals, decision basis): retirements
**FAIL** — model 0.008 GW vs actual 1.711 GW (−99.5 %), recall 0/1 reachable ≥300 MW
target. Additions total 3.311 GW model vs 3.375 GW actual (close in aggregate), with
wind **PASS** (+12.3 %), solar −42 % FAIL, gas_ct −49.7 % FAIL, gas_cc SKIP (actual 0).

## 3. Verdict and registration (rule 15, forecast namespace only)

`forecast_verdict.py --tier t1x --crossover-score … --run-config …` →
**determination HOLD** — FC-1 SKIPPED (required, unscored — a crossover bundle carries no
invariant record; the same shape as every T1-X leg in the program) + **FC-4 FAIL**.
**FC-7 reads CAVEAT, not FAIL** (DOF ledger absent — the program-wide lane-D8 instrument
gap): the bundle **tracks its own `run_config.json`** (written natively by the runner —
the FFR-3K fix), so **this leg does NOT join the seven-leg FC-7 run_config debt**
(c0562d9 convention satisfied). Provenance stamp: `scored_at_sha 3ebbd466fc4f`,
`cache_epoch 7323dc2ddabc95c7`, session `capx-D10-nyiso-t1x`.

Registered:

- `frontend/data/forecast/ff-verdicts.json` — **new live key `nyiso-t1x`** (157-line pure
  insertion; keys before/after diffed — **nothing displaced**, no preserve-then-overwrite
  needed since no prior NYISO t1x key ever existed).
- `scripts/register_forecast_run.py::VERDICT_MAP` — `nyiso-2023-2027-crossover-capxd10 →
  nyiso-t1x` (the per-session map-entry pattern; the bare key IS this run's own verdict, so
  the "never render a verdict the run's own score contradicts" rule is satisfied trivially).
- `register_forecast_run.py --bundle …` — canonical sidecar
  `frontend/data/hindcast/nyiso-2023-2027-crossover-capxd10.json`; namespace regenerated
  (generated files stay gitignored; the Pages deploy rebuilds them).
- Committed run artifacts under `results/hindcast/nyiso-2023-2027-crossover-capxd10/`:
  `meta.json`, `run_config.json` (the FC-7 artifact), `run_config.yaml`, and the key dir's
  `config.yaml` + `crossover_score.json` + `evolution_2023..2027.json` + floor-retention
  sidecars — the tracked-score convention that makes this verdict re-scorable from a
  checkout (`rescore_forecast_verdicts.py` reads exactly this layout). Year parquets stay
  untracked (≈2.1 MB × 5), per precedent.
- Report: `docs/hindcast-reports/nyiso-2023-2027-crossover-capxd10-crossover-2026-08-30.md`.
- Board seed `frontend/data/forecast/program-status.json` — NYISO `t1x_determination`
  n/a → HOLD; leg (c) fail → **pass (measured and reported)** with the full-magnitude
  numbers in the detail; `closed_on` ['a','c'] → ['a']. **The backcast registry was not
  touched** (plan §7.5), nor was any keeper shard, status page, offer curve, bridge, or
  `calibration-complete.json`.

## 4. The §2.1b gate: leg (c) verdict, and what remains

**Leg (c) CAN NOW CLOSE, and the board now carries it as pass.** Its requirement — FF-3E
readiness green (already held) AND the T1-X input gap **measured and reported** — is
satisfied by this run. The owner signed exactly this reading on card A: an ISO with no
T1-X run fails the leg; a measured FC-4 closes it *whatever it says*. FC-4's FAIL is the
measurement, reported at full magnitude above, identical in kind to the three ISOs whose
leg (c) already reads pass.

**What now stands between NYISO and an open gate — two things, and the set changed
mid-session:**

1. **Leg (a)** — at charter time it read PASS and this session was instructed not to
   re-read it. Mid-session (2026-08-30, owner r#12 ruling, commit `ecc2d60`) **Q5 was
   resolved the CAISO-precedent way: NYISO's `complete` marker was WITHDRAWN** ("a
   `complete` marker cannot stand on a NOT-YET keeper"), flipping board leg (a) to fail.
   This session neither re-read nor edited leg (a); restoration is the owner-managed
   backcast lane's (a future CALIBRATED keeper + re-declaration), not a forecast-track run.
2. **Leg (d)** — owner authorization. None exists; each full-horizon campaign is
   authorized separately. **This session does not request it and cannot grant it.**

Leg (b) is untouched and still PASS on the bare `nyiso-t1f` key (PROMOTE-WITH-CAVEATS;
sole caveat FC-7 DOF-ledger, lane D8).

## 5. Structural observations — reported, not acted on

- **The scored window executes essentially no exits: the crossover is a STRUCTURAL NULL
  for the retirement rule in NYISO.** Evolution ledgers 2023–2025: one 8.0 MW `announced`
  biomass exit (plant 54782), **zero economic retirements in any year, forward years
  included**. This reproduces on NYISO's own evidence (rule 25 clean) both FFR-3A-2 §3.7
  (NYISO T1-H: the economic screen never fires) and FFR-3A-4 §2.3 (MISO T1-X: a scored
  window with no executed exits cannot test D-1). The −99.5 % retirement band is therefore
  "the announced/confirmed channels miss what NYISO actually retired 2023–2025 under this
  vintage's information gate", not a statement about the economic screen.
- **D-2's commissioning lag is visible exactly as designed**: entry decided 2024
  (gas-CC 1.0 GW + wind 1.0 GW + solar 0.637 GW) and 2025 (solar 0.637 GW) commissions in
  2026/2027 — outside the scored window (the FFR-3A-2 §3.5 censoring, biting the
  additions bands here too: in-window additions are planned-pipeline only).
- **`correlated_forced_outage` is runtime-confirmed inert** (5/5 solve years no-op) — the
  flag flips nothing in NYISO; attribution surfaces stay as pre-registered in FFR-3A-2 §3.2b.
- **The CO2 result is the program-relevant one** (§0.1): lane D5's derivation question
  should now be scoped as "why do ERCOT/PJM/MISO miss 43–76 % while NYISO lands at
  10.1/10.3/3.9 % on the same construction (bench intensities, full-plant basis, BTM added
  back)?" — a discriminating fact D5 did not previously have.

## 6. The D7/D10 hydro-consistency paragraph (director's ledger §0d.3 — owed here)

Verified, not speculated: the nyiso-155 hydro repair pair (`hydro_backfill_year=2024` +
`hydro_eia930_monthly=true`) is plumbed **only** through `scripts/run_calibration_full.py`
→ `data.fleet.assembly` — the crossover/hindcast harness has no path to arm it, so this
run consumed the **forecast-side hydro construction** (the complete-census clamp +
climatology budget; the log shows 147 plants / 4,587 MW / 26.2 TWh in every year — never
the 3-plant truncated 2025 vintage, confirming the ledger §0d.3 immunity claim). The
consequence for THIS instrument: the FC-4 input-gap now has the two constructions of one
physical quantity on its two sides — numerator (forecast) on the clamped census +
climatology, denominator (keeper backcast) on the repaired per-year measured input. For
2025 specifically, where the repair moved the keeper's C3a by ~2.7 pp, a slice of the
measured 2.00× price gap is that construction difference rather than driver skill. Not a
defect in either lane — the backcast half is rule-13-admissible measured input, the
forecast half is the correct forward analogue — but any future decomposition of NYISO's
2025 crossover gap should carry this term explicitly. (One paragraph, as owed; no action.)

## 7. Governance attestation

- Holdout spend freeze **ACTIVE** (tier-scoped: locked test 2019/H1-2026, every ISO) —
  printed by the runner at launch, never worked around. **No marker consulted or spent**:
  the crossover window is freeze-legal by construction (solves = training years + forecast
  forward years; NYISO's marker withdrawal mid-session is irrelevant to this run's
  legality). No out-of-training backcast year solved, scored, or registered; the scorer's
  quarantine row **PASS** is the machine check of the same claim.
- Scoring read **only committed benchmark artifacts** (`bench/NYISO/2023..2025.json.gz`,
  capacity actuals registry, the keeper's committed determine() records). No measured
  outcome was fed back (rule 13); nothing was re-derived (rule 21); no off-registry knob
  (rule 24 — the one code edit is the VERDICT_MAP registration entry, not a tunable).
- **Mechanism matrix: no cell minted, by charter** — running an existing instrument on a
  new ISO tests no mechanism; nothing was armed, so no NYISO shard edit. The
  `mechanism-matrix-guard` CI WARN on a run registration without a matrix touch is
  expected and acceptable here (it is a WARN, not a gate).
- Instrument notes for successors: the FFR-3A-4 §6 blockers did not reproduce —
  `git push` created the session branch through this remote with no HTTP 413 (twice), the
  run-id collision guard had nothing to refuse (fresh id), and FC-7's run_config row is
  satisfied natively by the runner. The one live trap remains `pgrep` self-matching
  (use `ps -eo rss,args | grep "[r]un_…"`).

## 8. For the successor

1. **The leg is registered and re-scorable from the checkout.** Do not re-run it without
   new evidence; a re-score goes through `rescore_forecast_verdicts.py` /
   `forecast_verdict.py` on the committed artifacts.
2. **D5 should absorb §0.1/§5**: NYISO is the counter-example to a uniform CO2-derivation
   defect.
3. **Do not attribute NYISO crossover retirement bands to the retirement rule** (§5 —
   structural null; same instruction FFR-3A-4 §8.2 gave for MISO).
4. **The 2023 price face (+29.9 %, 30.2× gap) is the biggest unexplained object this leg
   surfaced.** It is a forecast-input-stack question (realized fuel + realized demand are
   already in, so the gap lives in the remaining forward-vs-overlay differences: offer
   conduct, outage overlay, seam/import representation, hydro construction §6). Unowned;
   worth a charter only after D5.
5. **Gate arithmetic**: leg (c) pass · leg (b) pass · leg (a) fail (Q5-W) · leg (d) none.
   The gate stays `open: false`; nothing here schedules a full-horizon campaign.
