# FINDING — entry signal L-1/L-1b measured, L-5 landed

_2026-08-24 · ENTRY SIGNAL lane (charter: `docs/FINDING-entry-screen-t1h-2026-08.md`
§7 levers L-1, L-1b, L-5) · **NO LP SOLVE, NO HINDCAST RE-RUN. Two probes replaying
committed arithmetic on committed artifacts, plus ONE code change (a diagnostic dump
gate, output-only, proven).** This rung produces EVIDENCE ONLY: no signal replacement
is armed or built here, and no mechanism cell verdict moves (rule 26 — L-1/L-1b test
no mechanism; L-5 adds no `ScenarioConfig` field)._

Subject bundle: the ERCOT T1-H capacity hindcast
`ercot-2021-2025-realized-t1h-refresh` (cache key `28cef3500ec1fd9e`; every probe
below reconstructs the run's exact `ScenarioConfig` from its committed
`run_config.json` and refuses to run unless the cache key reproduces).

---

## 0. The one-paragraph answer

**Signal construction owns the sign structure of ERCOT's entry error; the allocator
owns the amplitude; and the cobweb itself is real.** Replaying both entry screens at
identical fleet/cost/driver state against the model's own committed hourly LP duals
instead of the zone-flat MC-step signal (L-1) flips the margin **sign** of gas_cc,
gas_ct, solar and iron-air in the entering-2024 screen and kills the fictitious
$3.1M/MW-yr gas margins of the entering-2023 screen; wind's "anti-correlation" with
the signal vanishes (zone-row capture ratio 0.49–0.93 shipped → **0.99–1.06** on
duals) — it was manufactured by the ORDC adder, confirming B-3's defect is upstream
(D-8). On real price shape, storage entry becomes a **steady ~3 GW/yr of the
longest-duration tech** instead of a one-shot 5 GW spike — but **li-ion still never
builds** (it is 3rd of 6 by margin on duals and negative at seed costs), so signal
replacement alone does not fix the technology split: that remains L-3's (availability
gate) and D-3's (merit metric) domain. On the volume side (L-1b), re-running each
decision year under the one admissible closure — **build until the screen's own
repriced margin is exhausted, bounded by the same caps** — the reserve-margin
oscillation **survives** (swings −10.5/+1.6/+8.6 pp vs the registered
−10.5/+6.2/+10.5 pp): **B-2 is real market dynamics; D-1 owns the amplitude**, and
D-1's contribution is concentrated in the moderate-signal years, not the 2023 peak
(where the caps bind under *both* rules). L-5 is landed: the screen-signal dump now
also arms on the existing `entry_screen_diagnostics` gate, so CAISO's entry screens
become diagnosable next cycle without changing its registered posture.

---

## 1. L-1 — the screens replayed on committed LP duals

### 1.1 Construction, and what the dual arm is (and is not)

The counterfactual §5 of the charter finding names is `entry_lookahead_reprice =
False`, where every screen falls back to `prior_results["prices"]` — the LP duals
(`runner.py:1787-1789`). The T1-H bundle commits **no hourly prices** (only
`score.json` + the four `screen_signal_diag_*.npz` dumps), so the committed instance
of "the model's LP duals for an ERCOT year" is the **backcast keeper's hourly
sidecar** — `results/calibration/ercot223_release_arm/hourly/system_<year>.parquet`
(rule 15), 7 zones × 8760, whose `price` column is the year's final scored hourly
price with the scarcity components included (measured: corr(price, ordc_adder) =
0.912 in 2023; the residual `price − ordc_adder − rtordpa_overlay` has p99.9 =
$329/MWh, i.e. merit-range — `price` is the overlay-inclusive object, the right
analogue of the fallback's `econ_prices`).

Two stated bounds, so this is never over-read:

- **It is a stand-in, not the exact counterfactual.** The exact object is the T1-H
  run's *own* prior-year duals at its *own* evolved fleet; the keeper is a different
  run (backcast mode, measured overlays, actual fleet). The delta measures **signal
  construction (MC-step vs LP dual) plus a fleet/run-identity residual**.
- **Decision years 2022/2023 are data-blocked for the exact map** (they price off the
  2021 solve; no 2021 hourly duals are committed anywhere — the keeper spans
  2023–2025). The entering-2023 screen is additionally reported on the 2023 keeper
  duals as a **same-year, foresight-caveated diagnostic**, labelled `dual_same_year`,
  never the counterfactual. The exact-map arm is live for entering-2024 (2023 duals)
  and entering-2025 (2024 duals).

Everything else is held identical across arms: the dump's own fleet state
(storage MW, wind/solar potential), the run's resolved realized fuel (gas 2.04 /
1.69 / 3.03 $/MMBtu for drivers 2023/2024/2025, carbon 0), and seed-state costs
(`cumulative_gw=None`, exactly as the charter's phase-0 probe ran) — so the
cross-arm **delta** is exact even where the level carries seed-vintage capex.

**Validation gates (the probe refuses to report without them):** the shipped arm
reproduces the committed phase-0 storage margins **24/24** and the committed FFR-9B
thermal energy margins **8/8** at the recorded rounding
(`entry_signal_l1_dual_replay_ercot.json → validation`).

### 1.2 (i) Margin signs

Margins $/MW-yr at seed costs, energy leg (`r_none`); the reserve-leg bound
(`r_dump_adder`) is in the artifact and changes no sign below.

| screen | tech | shipped signal | committed duals | flip |
|---|---|--:|--:|:--|
| entering-**2024** (2023 duals, exact map) | gas_cc | −10,730 | **+22,583** | **− → +** |
| | gas_ct | −42,684 | **+350** | **− → +** |
| | solar (per-MWh) | −2.94 | **+6.75** | **− → +** |
| | iron_air | −94,999 | **+114,854** | **− → +** |
| entering-**2025** (2024 duals, exact map) | gas_cc | −136,300 | −68,049 | no |
| | gas_ct | −122,584 | −79,791 | no |
| | iron_air | −137,367 | **+110,091** | **− → +** |
| entering-**2023** (2023 duals, SAME-YEAR diagnostic) | gas_cc | +3,147,581 | +6,403 | no (level ÷ 490) |
| | gas_ct | +3,105,235 | −17,545 | **+ → −** |
| | wind (per-MWh) | +161.16 | −0.74 | **+ → −** |
| | li_ion_4hr | +1,469,715 | −66,605 | **+ → −** |
| | flow_battery | +2,650,473 | −146,947 | **+ → −** |

The entering-2024 row is the sharpest: the shipped signal told every screen "build
nothing" in the very decision year the registered run decided 6 GW of gas — a
decision the energy signal could not have produced under either offline reserve-leg
bound, so it was carried by the **prior solve's post-solve ORDC reserve leg**
(`runner.py:3536-3564`, `screen_reserve_value_enabled` with
`ercot_thermal_as_endogenous=False`), which is not persisted offline (the FFR-9B
probe's pre-registered degradation). On the LP duals the same margins are positive
**in the energy price itself** — the shape the MC-step signal cannot carry is
exactly the value the reserve leg was substituting for.

### 1.3 (ii) Storage ranking and allocation

| arm | ranking (by $/MW-yr margin) | profitable | allocator result |
|---|---|---|---|
| shipped, entering-2023 | iron_air, flow, li12, CAES, li8, li4 | **all six** (li4 6th at +$1.47M) | iron_air 3,000 + flow 2,000, once, then nothing ever again |
| duals, any available year | **iron_air, CAES, li4, flow, li8, li12** | **iron_air only** (+$115k / +$110k) | **iron_air 3,000 MW per year, steady** |

The finding's "li-ion is not unprofitable, it is out-competed" was a property of the
adder-inflated 2023 signal. On real price shape at seed costs, li-ion is *both* — 3rd
of 6 and negative — while iron-air clears in every dual year (its §4-sharpest-number
$14.36/MWh nine-day-window requirement sits below the duals' measured daily spread of
$37.9–51.5). **Signal replacement alone therefore converts the storage error from
"one 5 GW spike of the wrong techs" to "steady entry of one long-duration tech" — it
does not restore li-ion.** That remains the availability-gate (L-3) and merit-metric
(D-3) work, exactly as sequenced in the charter.

### 1.4 (iii) Wind/solar capture ratios

Build-zone row (West) against each arm's own mean — the screen's own construction
(`new_entry.py:1182-1204`):

| screen | wind shipped | wind duals | solar shipped | solar duals |
|---|--:|--:|--:|--:|
| entering-2023 (same-year diag) | 0.494 | **0.988** | 2.581 | 1.545 |
| entering-2024 (exact map) | 0.805 | **0.988** | 1.379 | 1.545 |
| entering-2025 (exact map) | 0.927 | **1.055** | 1.027 | 1.276 |

Wind at **capture parity** on the model's own duals. The B-3 inversion (wind
anti-correlated, solar 2.6×-correlated) is manufactured by the ORDC adder's
summer-afternoon shape, not by wind's market value — measured, closing the charter's
"defect is upstream (D-8)" attribution. The dual arrays also carry what the shipped
signal structurally cannot: zonal dispersion (zone-mean range $15.6–17.5/MWh, mean
hourly cross-zone spread $17–19/MWh), which makes the storage screen's per-window
best-zone selection (`storage.py:1486`) live for the first time.

---

## 2. L-1b — bang-bang vs margin exhaustion: the cobweb is real, the amplitude is not

### 2.1 Rule 21 `[R-DOF]`, in those words

**Any elasticity or damping parameter chosen to make this trajectory match is an
open root-cause issue, not a parameter.** The probe contains no such coefficient.
The volume rule is the one closure the model already contains — **build until the
screen's own repriced margin is exhausted** — implemented by adding capacity in
250 MW tranches (a resolution constant; halving it moves no reported GW by more than
one tranche) and re-pricing the dump's own committed stack construction after each:
the base merit price from the dump's `mc_sorted`/`cap_sorted` arrays, the ORDC tail
via the model's own `ercot_lookahead_expected_ordc_adder` on the dump's own
`r_online`/`r_full`/`sigma_r`, the storage shave via the model's own
`_storage_peak_shave_net_load`. **At zero added capacity both reproduce the four
committed dumps to 0.0 maximum absolute error** — the machinery is the run's own
arithmetic, not a model of it. Physical increments use registry constants only
(NERC-GADS `EFORD`, `ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC`), and the
capacity→reserve increment applies only in the hours the dump shows reserves
**headroom-bound** — measured to be 100 % of the top-adder hours in the 2023/2024
screens, i.e. the binding branch of `min(rtolcap, headroom)`, not an assumption.

Open-loop honesty: each decision year is repriced within-year, and the later dumps'
states are adjusted by the counterfactual-vs-shipped build deltas (thermal at the
2-year COD lag, storage in-year) with the same stack arithmetic — but the committed
signals were produced by the shipped path, so demand/procurement/retirement
feedbacks stay at shipped values. VRE decisions are held at shipped in both arms
(their ELCC deltas cancel in the comparison); an ISO-budget crowding sweep
(0 / 8 GW consumed by VRE) changes no conclusion below.

### 2.2 The builds

| step | bang-bang (shipped, reconstructed¹) | margin-exhaustion | note |
|---|---|---|---|
| 2022 | gas_cc 3,000 + gas_ct 1,571 | **gas_cc 1,000, gas_ct 0** | margin exhausts in 4 tranches (+$46k → +$8k); bang-bang built 3.6 GW past exhaustion, incl. gas_ct's full ladder on a +$5.8k/MW-yr margin |
| 2023 | gas_cc 3,000 + gas_ct 3,000 + storage 5,000 (iron+flow) | gas_cc 3,000 (cap) + gas_ct 1,500 (ladder²) + storage 5,000 (iron 3,000 + **CAES** 2,000) | **caps bind under BOTH rules** — the last storage tranche still clears +$750k/MW-yr; the 2023 signal is deeper than the caps |
| 2024 | gas_cc 3,000 + gas_ct 3,000 (reserve-leg-carried) | **gas_cc 3,000 (cap)** | the damping feedback, measured: 3.57 GW less prior build ⇒ the 2024 energy margin itself turns positive (+$46k at the 10th tranche) |
| 2025 | none | none | slack under both |

¹ The bundle commits no evolution ledgers; the shipped per-step split is
reconstructed from the committed report's window totals (9.0/7.571/5.0 GW), the
ladder arithmetic (gas_ct seed 0.7855 GW × 2 = 1,571, committed in
`docs/handoffs/ffr-9b/entry-screen-replay.json`), the charter's §2 storage replay,
and this lane's own margin signs. ² 1,500 vs the 1,571 ladder is tranche
quantization (< one tranche).

### 2.3 The trajectory, and the verdict

Numbers quoted from the 0 GW VRE-crowding arm; the 8 GW arm moves only 2025
(18.1 %, swing +8.0 pp) and no conclusion.

| entering year | registered RM % | margin-exhaustion RM % |
|---|--:|--:|
| 2022 | 19.0 | 19.0 |
| 2023 | 8.5 | **8.5** |
| 2024 | 14.7 | 10.1 |
| 2025 | 25.2 | 18.7 |
| **swings (pp)** | **−10.5 / +6.2 / +10.5** | **−10.5 / +1.6 / +8.6** |

**The oscillation SURVIVES ⇒ B-2 is confirmed as real market dynamics, and D-1 owns
only the amplitude.** Three structural facts sharpen that:

1. **The down-swing is exogenous to ANY volume rule.** The first decision step is
   2022 and the COD lag is 2 years (`ENTRY_COD_LAG_YEARS`), so nothing any allocator
   decides can reach the fleet entering 2023. 19.0 → 8.5 is realized load growth
   against a lagged queue — market structure, not the allocator.
2. **The peak is cap-bound under both rules.** In 2023 the caps, not the volume rule,
   are the forecast (the charter's D-1 line, now measured from the other side): with
   a signal this deep, bang-bang and margin-exhaustion produce the same decision.
3. **D-1's amplitude lives at the shoulders.** 2022: 4.571 GW on margins as thin as
   +$5.8k/MW-yr where exhaustion supports 1.0 GW (×4.6). 2024: 6 GW where the
   repriced state supports 3 GW. Terminal RM 25.2 % vs 18.7 % — ~6.5 pp of the
   recovery overshoot is the bang-bang volume.

A secondary observation for the storage lanes: under repricing, the *second* storage
slot flips from flow_battery to compressed_air — the winner-take-share split is
signal-sensitive even when the budget outcome is identical, another face of D-3.

---

## 3. L-5 — the diagnostic dump decoupled from the behavioural flag (LANDED)

**Change** (`runner.py`, the `_diag` gate; one expression):
`screen_signal_diag_*.npz` now arms on `unified_screens OR
config.entry_screen_diagnostics` instead of `unified_screens` alone. D-7's defect
was that the dump — pure diagnostics — was tied to `capacity_screen_unified_lookahead`,
a *behavioural* gate, so CAISO's registered posture (`unified_lookahead=False`)
could not be diagnosed offline at all. `entry_screen_diagnostics` is the existing
RC-0C default-off diagnostics flag that already gates the per-candidate screen
ledger; **no new `ScenarioConfig` field, no new CLI flag**
(`--entry-screen-diagnostics` already exists in `run_capacity_hindcast.py`), hence
no mechanism-matrix row (rule 26 duty c does not fire).

**No-behaviour-change proof, without a solve:**

1. *Function level (tested):* the `diagnostics` dict is write-only inside
   `_lookahead_reprice_signal` — the new unit test
   (`tests/unit/model/test_price_signal.py::test_diagnostics_dict_is_write_only`)
   asserts byte-identical returned signals with and without the dict, on both the
   plain and the scarcity-tail path, and that the dict records exactly the signal
   the caller received.
2. *Block level (inspection):* between the gate and the end of
   `_screen_signal_for`, `_diag` is consumed only by the `np.savez_compressed`
   block, which reads existing state (`plant_group`, the sigma function, shave
   terms, potentials — all pure) and writes a file; no variable any screen or the
   solve reads (`sig`, `price_signal`, `unified_signals`, `prior_results`) is
   touched. This is the same property the FFR-8A control arm proved for the dump
   under the old gate.
3. *Default level:* at the flag's default (False) the gate expression is
   byte-identical to the old `{} if unified_screens else None` — every existing
   configuration is unchanged. Suite: `test_price_signal.py` 9/9,
   `test_capacity_screen_unified_lookahead.py` + `test_capacity_screen_scarcity_
   restoration.py` 45/45.

**What this unblocks, and its honest cost.** CAISO's L-1 needs two committed
halves: hourly LP duals (already committed — the CAISO keeper
`caiso200_h1_memberpanel` carries `hourly/system_{2023,2024,2025}.parquet`) and the
screen-signal dumps (missing — D-7). Next cycle re-runs the CAISO 2021–2025 T1-H
hindcast with `--entry-screen-diagnostics` under its **registered posture** —
fleet-outcome byte-identical by the flag's documented contract — and CAISO's L-1
then replays offline exactly as ERCOT's did here. This is finding §8 item 1's solve,
now strictly cheaper than the alternative it named (arming
`capacity_screen_unified_lookahead`, which *changes* the screens being diagnosed).
One caveat stated so it is not rediscovered: `entry_screen_diagnostics` enters the
cache key when armed (pre-existing property of the flag, not of this change), so the
rerun recomputes its solves under a new key rather than reusing the registered
bundle's cache.

---

## 4. What requires a solve (named, not run — checked against charter §8)

1. **CAISO dump production** — §8 item 1, unchanged, now via the cheaper L-5 route
   above.
2. **The exact ERCOT counterfactual** — the L-1 dual arm's stand-in bound (§1.1) is
   removable only by a T1-H ERCOT re-run under `entry_lookahead_reprice=False`
   (the fallback path is existing code, one flag), which would simultaneously (a)
   produce the armed-counterfactual ledger the L-1 replay predicts and (b) persist
   nothing extra — its own prior-year duals ARE its screens' input. This is also
   the adjudicating measurement for the next rung (§5).
3. **Nothing else here needs a solve.** Both probes and the L-5 proof are closed on
   committed artifacts; this matches §8 item 3 ("nothing else"), with item 2's
   ERCOT half now DONE offline (this document) at the stated stand-in bound.

---

## 5. Recommendation for the next rung

**Next rung: adjudicate the signal REPLACEMENT — `entry_lookahead_reprice=False`
(the existing duals fallback) as the T1-H entry signal — with a single ERCOT
disarm-probe solve.** The measurement that decides it: re-run
`ercot-2021-2025-realized` T1-H with the one flag flipped, score on the same
additions/retirements bands, and compare the ledger to this finding's L-1
predictions (gas signs, steady iron-air entry, wind capture parity). L-1's evidence
is the new-evidence predicate the matrix discipline requires to touch the
`entry_lookahead_reprice` cell (currently `K`/`fc K` — a keeper, so this is a
measured challenge to a keeper cell, chartered on this finding, not a re-test of an
adjudicated `R`/`I`/`G`). The session that runs it updates the ERCOT shard cell in
the same session (rule 26 duty b).

**Rule 19 `[R-ONE-MECH]`, restated for the next lane as the charter requires:** what
governs the entry price today is `entry_lookahead_reprice` +
`capacity_screen_unified_lookahead` + `capacity_screen_scarcity_restoration`. A
future lever must **REPLACE** the signal's construction — never stack a shape
correction, adder, or multiplier on top of it. The fallback-duals candidate
satisfies this by construction (it is the disarm of the reprice, not a new object),
and it keeps exactly one reserve-price mechanism (the post-solve adder leg,
unchanged). Two results from this lane that the next lane inherits as constraints:
signal replacement does **not** restore li-ion (L-3/D-3 remain separate work, L-3
before L-6 as sequenced), and it does **not** remove the cobweb (B-2 is real; only
D-1's amplitude — the bang-bang volume rule — is separately repairable, with the
margin-exhaustion closure measured here as the zero-DOF candidate).

CAISO's queue is unchanged: L-5 rerun (dump production) → CAISO L-1 offline → only
then any CAISO signal lever (L-4 stays an open root-cause issue, not a parameter).

---

## 6. Rule compliance

- **Rule 1 `[R-STRUCT]`** — cuts both ways, honoured: B-2 is *confirmed* real
  dynamics (not "fixed"); no number is reached through an unreal mechanism; the
  keeper duals are used as measurement instrument only, nothing is armed.
- **Rule 5/24 `[R-NO-MAGIC]`/`[R-REGISTRY]`** — no new tunable, no new gate, no new
  field; the one constant introduced (250 MW tranche) is a probe resolution
  constant in a probe, documented as such. `STORAGE_TECH_BUILD_SHARE_CAP`'s missing
  citation (D-3) is deliberately NOT fixed, per charter.
- **Rule 13 `[R-MEASURED]`** — the probes feed no measured outcome back into any
  model path; keeper duals are committed *model* output, and appear only in
  evidence artifacts.
- **Rule 19 `[R-ONE-MECH]`** — stated in §5 for the next lane; L-5 replaces a wrong
  gate with the right existing one and adds no mechanism.
- **Rule 21 `[R-DOF]`** — §2.1, in the charter's words; no elasticity or damping
  coefficient exists in either probe.
- **Rule 22 `[R-HOLDOUT]`** — no year outside 2023–2025 solved, scored, or
  registered; the probes read committed 2021-solve *dumps* (artifacts of the
  already-registered run), never holdout data.
- **Rule 25 `[R-ISO-SCOPE]`** — every measured number here is ERCOT's; CAISO gets a
  deferral statement and an unblock path, no transferred verdict.
- **Rule 26 `[R-MECH-MATRIX]`** — L-1/L-1b tested no mechanism: no cell verdict
  moves. L-5 adds no `ScenarioConfig` field: no matrix row. The two fresh
  adjudications honoured, not re-opened: `ercot_adaptive_fixed_point`
  MEASURED-INERT-AT-FIXED-POINT (ercot-230; within-year backcast conduct — no
  collision with L-1b's cross-year forecast-lane object, per the charter's own
  check) and `miso_offer_level_dispersion` `R` (MISO out of scope).
- **Rule 27 `[R-PUSH]`** — `runner.py` edited locally, pushed as on-disk bytes,
  blob-verified post-push (4,076 → 4,096 lines; sha match; nothing shrank).
- **Out of scope, untouched:** keeper shards, `calibration-complete.json`,
  `holdout-freeze.json`, backcast registry, L-2/L-3/L-4/L-6, workflows.

---

## 7. Reproduction

Committed artifacts, `code` data profile, no solve:

```
uv run python scripts/probes/entry_signal_l1_dual_replay.py \
    --bundle results/hindcast/ercot-2021-2025-realized-t1h-refresh \
    --duals-bundle results/calibration/ercot223_release_arm \
    --out results/calibration/entry_signal_l1_dual_replay_ercot.json

uv run python scripts/probes/entry_signal_l1b_allocator_counterfactual.py \
    --out results/calibration/entry_signal_l1b_allocator_ercot.json

uv run python -m pytest tests/unit/model/test_price_signal.py -q
```

Both artifacts are committed alongside this document. The L-1 probe hard-fails
unless its two validation gates (phase-0 storage 24/24, FFR-9B thermal 8/8)
reproduce; the L-1b probe records the 0.0-error reproduction of all four committed
dumps' adder and shave at zero delta.
