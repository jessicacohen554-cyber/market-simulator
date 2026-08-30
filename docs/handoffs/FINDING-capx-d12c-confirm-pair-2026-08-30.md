# FINDING — D12-C: the arming confirmation pair, measured closed-loop

_2026-08-30 · capacity-expansion (Forecast Finalization) track, lane D12-C
ARMING CONFIRMATION PAIR · chartered by the owner's Q10 ruling (r#15 sitting,
2026-08-30, `docs/handoffs/capx-director-ledger-2026-08.md` §0l.2/§3):
**"CONFIRM-PAIR, THEN ARM. Lane D12-C chartered: ONE arm-vs-control A/B on the
ERCOT T1-H leg at the registered posture with the TWO fields
(`entry_margin_exhaustion` + `entry_forward_reserve_leg`) as the single
logical delta, measuring the closed loop D12 open-loop-predicted. Arming
auto-executes on a confirming record (both flip to ERCOT forecast defaults,
honestly described); a contradiction does NOT arm and comes back to the owner
at full magnitude."** Branch `claude/capx-d12c-confirm-pair-oji8wv`.
Predecessors: `FINDING-capx-d12-scarcity-basis-2026-08-30.md` (+ its PREDECL)
and `FINDING-capx-d11r-entry-volume-rule-2026-08-30.md` §3 (the A/B protocol
repeated here and the committed control bracket)._

---

## 1. Pre-declared expectations and tolerances (§1 COMMITTED BEFORE EITHER SOLVE COMPLETED)

**Timing note (the S-4 discipline, as in D12's PREDECL):** everything in this
§1 was written and committed BEFORE the control or arm invocation was
launched. Seen at write time: the two predecessor findings and their committed
artifacts (`entry_signal_l1_dual_replay_ercot.json`,
`entry_signal_l1b_allocator_ercot.json`, `entry_volume_rule_ab_ercot.json`),
the committed d11r bundle sidecars, and the code seams. NOT seen: any output
of the D12-C invocations (none existed). The expected arm cache key below was
computed ex ante from the committed control `run_config.json` plus the two
flags via `ScenarioConfig.cache_key()` — an arithmetic derivation, not a
solve.

**The pair.** ERCOT `ercot-2021-2025-realized` T1-H leg at the registered
posture, same HEAD (`origin/main` @ `9c3f221` + this lane's probe-extension
commit), both invocations solved by this session, concurrently (rule 12),
years sequential within each:

- CONTROL — bare `run_capacity_hindcast.py --iso ERCOT --start-year 2021
  --end-year 2025`, out-dir `…-t1h-d12c-control`.
- ARM — same plus `--entry-margin-exhaustion --entry-forward-reserve-leg`,
  out-dir `…-t1h-d12c-armed`.
- Probe: `scripts/probes/entry_volume_rule_compare.py` extended with
  `--expect-delta entry_margin_exhaustion,entry_forward_reserve_leg` (the
  two-field delta gate; hard-fails on anything else). Artifact:
  `results/calibration/entry_confirm_pair_d12c_ercot.json`.

### 1.1 Gates (stop-the-line, before any verdict is read)

- **G-1 control integrity.** The control reproduces the committed registered
  bracket EXACTLY: cache key `28cef3500ec1fd9e`; RM path
  19.00 → 8.54 → 14.65 → 25.19 at the reported 2 dp; the additions table
  verbatim (wind 0.350 / solar 17.987 / gas_cc 9.000 / gas_ct 7.571 / storage
  5.000 GW); per-step decisions equal to the committed
  `entry_volume_rule_ab_ercot.json` control block row-for-row. Any drift is a
  stop-the-line finding (HEAD drift on the fleet side), NOT a baseline — no
  A/B verdict is read on a drifted control.
- **G-2 posture.** `run_config` delta exactly
  {`entry_margin_exhaustion`: False→True, `entry_forward_reserve_leg`:
  False→True} (probe-gated); expected arm cache key **`f061b2646bfaac8b`**
  (computed ex ante as above; D12 §8's `1eda234b96a95fee` is the
  pinned-GLOBAL-default + leg hash, a different posture — verified ex ante
  against `ScenarioConfig()` before declaring). A different arm key with a
  clean two-field delta is posture drift: stop the line.

### 1.2 Verdict criteria (ALL must land inside tolerance for a CONFIRMING record)

The record CONFIRMS iff V-1 … V-5 all hold. A miss on any single one is a
CONTRADICTION: nothing arms, the divergence is decomposed at full magnitude,
and the owner re-decides. Margin recomputation tolerance wherever a margin is
quoted: **$0.05/MW-yr** (D12 §4's own reproduction error against the
dual-replay rows — declared here, ex ante, as the numeric basis; every
committed margin this pair tests sits ≥ $5.7k from zero, so $0.05 flips no
sign and maps to < 1 tranche of walk arithmetic).

- **V-1 — the phantom step builds nothing.** The arm's entering-2025 step
  builds ZERO gas (gas_cc = 0 AND gas_ct = 0). Every committed open-loop
  estimate agrees the one-object margin is negative there on both measured
  states (walk state: "2025 nothing"; the D11-R arm's thinner state:
  −$117.4k / −$101.5k under B). Exact, no tolerance.
- **V-2 — the gas half of the exhaustion rule is LIVE at the state-clean
  step.** Entering-2022 is the one step where the live closed-loop state ≡
  the walk state (first decision off the common 2021 seed), so the walk's
  arithmetic must reproduce nearly exactly: gas_cc ∈ **[750, 1,250] MW**
  (walk: 1,000, ± 1 tranche of 250 MW) and gas_ct ≤ **250 MW** (walk: 0,
  + 1 tranche) — both strictly below their caps (3,000 / 1,571). This is the
  first live record of ERCOT gas entry stopping on its own exhausted margin.
- **V-3 — nothing that was right changes.** Entering-2023 gas_cc = 3,000
  (cap; B margins +$3.1M — no repricing can exhaust them) and entering-2024
  gas_cc ∈ **[2,500, 3,000]** (the walk caps it at 3,000 with the last
  tranche still +$19.9k and declining ≈ $13k/tranche, so a modestly fatter
  live state may stop 1–2 tranches short; both measured open-loop states
  agree cc is carried at 2024 — walk +$46k → +$19.9k, D11-R-arm state
  +$343.6k).
- **V-4 — terminal ledger RM.** Expected at the walk bracket
  **[18.08, 18.71] %**; CONFIRMING band **[15.0, 21.0] %**. Derivation, ex
  ante: the walk's RM accounting rides the registered trajectory with
  thermal/storage firm deltas ONLY (`entry_signal_l1b_allocator_ercot.json`
  `rm_trajectory` — VRE deltas excluded by construction, its "ELCC deltas
  cancel" note), so the live closed loop adds two effects the bracket cannot
  carry: (i) live VRE/storage exhaustion feedback, whose measured magnitude
  under the D11-R live arm was **−3.17 pp** (its entire terminal delta vs
  control — in-window gas was identical); (ii) a richer entering-2023 state
  (the live 2022 solar cut lands COD 2023) that can carry gas_ct past the
  walk's 1,500 MW stop toward its 3,000 cap, worth ≤ **+1.8 pp** in-window.
  Band = bracket − 3.2 / + 2.3, i.e. [14.9, 21.0], rounded to [15.0, 21.0]
  with the top held ≥ 1.0 pp below the nearest committed alternative anchor.
  Both committed alternatives lie OUTSIDE the band: 22.02 (exhaustion under
  basis A, live) and 25.19 (shipped bang-bang) — the tolerance cannot absorb
  a phantom (one 3 GW cap-slam ≈ 3.6 pp in-window) or a dead gas half.
- **V-5 — the reason matches the arithmetic.** Recomputed from the arm's own
  emitted `screen_signal_diag` dumps with D12 §4's exact method (energy leg
  `Σ max(base+adder−vc, 0)`, basis-B leg `Σ max(base+adder−vc, adder)`, fixed
  costs from `resolve_new_entry_costs`), the arm's entering-2025 gas margins
  are NEGATIVE for both techs at walk start (± $0.05) — the step builds
  nothing FOR D12's reason, not coincidentally.

### 1.3 Reported expectations (recorded ex ante; NOT verdict criteria)

- **R-1 gas bands** (attached evidence, never the verdict — rule 1
  [R-STRUCT]; the charter's own framing): both scored gas band errors shrink
  vs the shipped control (|err| gas_cc < 8.756, gas_ct < 3.879 GW; actuals
  0.244 / 3.692). Committed anchors, all quoted ex ante: B+bang-bang
  open-loop 6.000 / 4.571 (err 5.756 / 0.879); B+exhaustion walk-state
  totals 7.000 / 1.500 (err 6.756 / 2.192); shipped control 9.000 / 7.571
  (err 8.756 / 3.879); D11-R live exhaustion arm 12.000 / 10.571. The closed
  loop decides where in that fan it lands.
- **R-2 the B-2 cobweb**, re-measured and reported whatever it shows.
  Expected ex ante: the −/+/+ sign pattern survives; first swing near the
  D11-R arm's −12.65 pp (the 2022 VRE/storage exhaustion carries over,
  possibly damped — fewer 2022 gas tranches leave solar exhausting later);
  middle swing SHRINKS from the arm's +5.20 pp toward the offline walk's
  +1.59 pp (the 2022 gas cut lands COD 2024); expected RM path shape
  ≈ 19.00 → 6.3–8.5 → 7–11 → V-4's band.
- **R-3 entering-2024 gas_ct**: state-dependent and admissible either way —
  the walk (fatter, VRE-held state) builds 0; the D11-R arm's thinner state
  priced ct at +$310.7k (would build). Reported with its own dump-recomputed
  margins; only cc is gated (V-3).
- **R-4 entering-2023 gas_ct**: walk says 1,500 (1,000 at the 8 GW sweep);
  the live richer state can carry it up to the 3,000 cap. Reported, with the
  in-window RM consequence already inside V-4's band arithmetic.
- **R-5 storage/wind**: expected qualitatively as the D11-R arm behaved
  (iron_air-only second slot or exhaustion below 5,000; wind entry > 0 in
  2023 plausible); li-ion still never builds (L-3/D-3 territory, not this
  lane's). Reported.

### 1.4 What confirmation triggers (pre-authorized by Q10 — no further ask)

On a CONFIRMING record, IN THIS SESSION: both fields flip to ERCOT forecast
defaults via the ISOConfig `default_scenario_overrides` route (the FFR-9C
stage-B pattern), with the Q10 ruling cited verbatim in the citation block;
the ERCOT matrix shard cells move (`entry_margin_exhaustion` O →
K-forecast-armed; `entry_forward_reserve_leg` ERCOT cell likewise) with this
pair as evidence; sister-ISO cells stay U (rule 26); both bundles register on
the FORECAST namespace (`ercot-2021-2025-realized-t1h-d12c-{control,armed}`)
with `run_config.json` committed. The armed posture is recorded honestly: the
margin-exhaustion volume rule with its gas half live on a one-object forward
margin — i.e., ERCOT forecast entry becomes exhaustion-bounded on the
entering year's own expected-ORDC surface for every candidate class. On a
CONTRADICTING record: nothing arms, cells stay O, this finding reports the
divergence decomposed at full magnitude, and the owner re-decides.

---

## 2. Control gate (measured)

_TO BE FILLED after the solves; nothing below §1 existed when §1 was
committed._

## 3. The armed record (measured)

_TO BE FILLED._

## 4. Adjudication

_TO BE FILLED._

## 5. Rule compliance

_TO BE FILLED._

## 6. Reproduction

```
# the two arms (bare invocation = the registered posture; TWO flags differ)
uv run python scripts/run_capacity_hindcast.py --iso ERCOT --start-year 2021 --end-year 2025 \
    --out-dir results/hindcast/ercot-2021-2025-realized-t1h-d12c-control
uv run python scripts/run_capacity_hindcast.py --iso ERCOT --start-year 2021 --end-year 2025 \
    --entry-margin-exhaustion --entry-forward-reserve-leg \
    --out-dir results/hindcast/ercot-2021-2025-realized-t1h-d12c-armed

# score each, then the A/B probe (posture-gated: exactly the two fields may differ)
uv run python scripts/score_capacity_hindcast.py --bundle <each bundle>
uv run python scripts/probes/entry_volume_rule_compare.py \
    --arm results/hindcast/ercot-2021-2025-realized-t1h-d12c-armed \
    --control results/hindcast/ercot-2021-2025-realized-t1h-d12c-control \
    --expect-delta entry_margin_exhaustion,entry_forward_reserve_leg \
    --out results/calibration/entry_confirm_pair_d12c_ercot.json
```
