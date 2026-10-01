# Full-horizon forecast findings — 2026–2050, all six ISOs (P-3A)

**Session.** P-3A of `docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md`
§2 (testing-audit **G1**: the full 2026–2050 horizon had never been solved
end-to-end). First time the reference forecast is driven across the complete
horizon per ISO with the I1–I14 forecast invariants scored.

**Findings only.** No model code, threshold, or offer curve was changed to alter
a result (rules 1/11/14). Forecast probes — nothing registered on the backcast
dashboard. No 2022 / H1-2026 solve (rule 22; forecast mode uses no measured
holdout actuals). Two supporting *tooling* changes were made (neither touches
model behavior): the forecast golden fixture was deepened 2032→2040, and a
latent import bug in the collator was fixed (see §8).

> **⚠ Coverage caveat — this is a PARTIAL run, stopped mid-horizon at the
> owner's request.** Of the six ISOs: **CAISO and NEISO completed all 25 years**;
> **PJM reached 22/25 (through 2047)** and **ERCOT 15/25 (through 2040)** before
> being stopped; **NYISO reached only 1/25 (2026)**; **MISO could not execute at
> all** (hard blocker, §3). The findings below are robust for the four ISOs with
> ≥15 solved years and are explicitly flagged as partial or thin where they are
> not. The run should be re-executed to completion (est. ~8 h for PJM alone —
> §2) once the MISO blocker is cleared.

**Config (identical across ISOs).** `ScenarioConfig(mode="forecast",
start_year=2026, end_year=2050)`, every other field default →
`use_campd_bins=True` (per-plant CAMPD bins where an artifact exists, the ISO
default), **`capacity_market_clearing=False`** (the P-2A recommendation,
`docs/handoffs/capacity-price-validation-2026-07-12.md` §7 — the CR-1 sloped
curve is validated as an instrument but not yet wired to a trustworthy accredited
position; **NOT an A/B this pass**). Runs used `MALLOC_ARENA_MAX=2
MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1`, ≤2 ISO invocations concurrent,
years sequential within each invocation (rule 12).

**Reproduce.**
```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_full_horizon.py --iso <ISO> \
  --start-year 2026 --end-year 2050 --out-dir results/full-horizon/<iso>
uv run python scripts/collate_full_horizon.py --root results/full-horizon \
  --out results/full-horizon/_tables.md
```
Harness landed by the prior P-3A session (`scripts/run_full_horizon.py`,
`scripts/collate_full_horizon.py`; on main via #2083). The per-year cache makes
the runs resumable — a stopped/killed run resumes from its last cached year.

---

## 1. Headline findings (lead)

1. **MISO forecast is completely broken — it cannot execute (hard blocker).**
   `build_default_storage` (runner.py:573, called unconditionally) →
   `_resolve_pace` raises `ValueError: Unknown iso 'MISO'` because
   `STORAGE_BASE_FLEET_MW` (storage.py) omits MISO. The G1 run's very first act
   was to surface that 1/6 registered ISOs has no runnable forecast path. Not
   fixed (findings-only); one-line remedy in §3.
2. **The capacity trajectory does not equilibrate — the non-responsive
   (`cmc=False`) capacity price produces a two-phase failure in every scored
   ISO:** an **early de-firming dip** (2026–~2035, reserve margin falls *below*
   the planning floor — I12 fails, and I7 fails at the base year for the
   capacity-market ISOs), followed by market-design-dependent divergence —
   capacity-market ISOs **over-correct into massive over-build** (CAISO RM→60%,
   NEISO→67%, PJM→32% by 2047), while energy-only **ERCOT stays chronically
   short and develops scarcity** (RM troughs at 2.6% in 2037; VOLL price spikes;
   LW price $24→$216). This is the audit §1 prediction — "an entry/retirement
   loop driven by a non-responsive capacity price cannot equilibrate" — realized
   end-to-end. **F1/F2 do NOT simply compound monotonically to 2050; they
   overshoot in both directions.**
3. **#2064 (ERCOT scarcity non-monotonicity) PERSISTS over the full horizon.**
   ERCOT slack>1MW hours = `[0,0,0,1,0,2,0,0,0,0,0,11,0,39,107]` (2026–2040) —
   non-monotone, with VOLL ($5000) scarcity spikes at 2029/2031/2037 tracking
   the reserve-margin troughs. Same discrete retirement/entry-vs-load
   non-equilibrium under one-pass evolution that T1.4a flagged, now visible along
   a single reference path.
4. **Feasibility: the per-plant multi-zone full-horizon run is expensive and
   the late-horizon years dominate.** CAISO 179 min / 5.3 GB and NEISO 72 min /
   3.9 GB *completed*; PJM ran **>8 h wall and ~9–10 GB RSS** and still did not
   finish 25 years — its 2045–2050 LPs are ~30–40 min each, and its late-horizon
   RSS (~9 GB) means **two per-plant multi-zone ISOs cannot solve their
   late-horizon years concurrently on a 15 GB box** (observed: two OOM-kills of
   the co-running ISO). A full-horizon release gate must budget accordingly.

---

## 2. Feasibility — wall time & peak RSS (release-gate data)

| ISO | years | status | total wall | median yr | max yr | peak RSS | notes |
|---|---|---|---|---|---|---|---|
| CAISO | 25/25 | complete | 178.8 min | 470 s | 773 s | 5.33 GB | full horizon |
| NEISO | 25/25 | complete | 71.9 min | 85 s | 620 s | 3.92 GB | full horizon |
| PJM | 22/25 | **partial** | >8 h (unfinished) | ~30–40 min (late yrs) | — | ~9–10 GB | 2045–2050 LPs dominate |
| ERCOT | 15/25 | partial | — (not captured) | ~3–8 min | ~3.6 GB | through 2040 |
| NYISO | 1/25 | partial | — | — | ~2 GB | barely started |
| MISO | 0/25 | **ERROR** | 0.3 min | — | 0.36 GB | cannot execute (§3) |

Timing for the partial runs was not captured (the harness records it only at
completion; the partial summaries were reconstructed post-hoc from cached
parquets). Two robust feasibility conclusions stand:

- **Runtime is super-linear in horizon year.** CAISO/NEISO median-year walls
  (85–470 s) understate the tail: the max-year wall is 620–773 s and PJM's
  2045–2050 years each took ~30–40 min — the fleet grows every year (endogenous
  entry) so the LP grows, and the last years are 10–20× the first.
- **Peak RSS scales with fleet size and is the binding concurrency constraint.**
  PJM's per-plant 8-zone LP reached ~9–10 GB in its late years. Running a second
  per-plant multi-zone ISO alongside PJM's tail OOM-killed the co-runner twice
  (and once coincided with a container restart). **Making the full horizon a
  release gate requires either a larger box (≥32 GB) or serializing the
  per-plant ISOs' late-horizon years** (early years co-run fine).

---

## 3. MISO hard blocker (ranked issue #1)

```
ValueError: Unknown iso 'MISO'. Supported: CAISO, ERCOT, NEISO, NYISO, PJM
  scripts/run_full_horizon.py:277  run_scenario_iso(config, iso)
  src/market_sim/runner.py:573     build_default_storage(iso_config, config)
  src/market_sim/model/storage.py:207  _resolve_pace(config)
  src/market_sim/model/storage.py:176  raise ValueError(...)
```

`build_default_storage` is called **unconditionally** in `run_scenario_iso`
(not mode-gated), and `_resolve_pace` requires `config.iso ∈ STORAGE_BASE_FLEET_MW`.
That registry has keys `{CAISO, ERCOT, NEISO, NYISO, PJM}` — **MISO is the only
registered ISO absent.** So any MISO forecast raises before the first solve.
(MISO *backcast* keepers exist because the backcast calibration path supplies the
storage fleet differently; the reference forecast via `runner.run_scenario_iso`
hits the gap.)

**Not fixed** (findings-only; adding a base fleet is a data/calibration decision,
not a residual-neutral edit — rules 5/24 require cited values). **Suggested remedy
for a future session:** add `STORAGE_BASE_FLEET_MW["MISO"]` with a base-year
storage fleet from EIA-860 MISO batteries (cited), mirroring the other five ISOs'
pace dict. Until then MISO has **no forecast coverage**, and the full-horizon
gate cannot include it.

---

## 4. Invariant matrix (I1–I14)

`P`=PASS `**F**`=FAIL `W`=WARN `-`=not scored (MISO did not run). ERCOT/NYISO
columns reflect partial horizons (15 and 1 years).

| ISO | I1 | I2 | I3 | I4 | I5 | I6 | I7 | I8 | I9 | I10 | I11 | I12 | I13 | I14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ERCOT (15y) | P | P | **F** | P | P | P | **F** | P | P | P | P | **F** | W | W |
| CAISO (25y) | P | P | **F** | P | P | P | **F** | P | **F** | W | P | **F** | W | W |
| PJM (22y) | P | P | **F** | P | P | P | P | P | P | P | P | **F** | W | W |
| MISO | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| NYISO (1y) | P | P | P | P | P | P | **F** | P | P | P | P | W | P | P |
| NEISO (25y) | P | P | **F** | P | P | P | **F** | P | P | W | P | **F** | P | W |

**Structural invariants hold everywhere they were scored:** I1 (energy balance,
≤1.6e-10 MW), I2 (no NaN/inf), I4 (capacity accounting closes), I5 (no
retire-and-reenter), I6 (retirement bounded), I8 (planned-additions gating),
I11 (one-pass). The failures are all *economic/behavioral*, concentrated in the
capacity-adequacy and price/curtailment invariants — consistent with §1 finding 2.

**Recurring FAIL/WARN (offending years abbreviated):**

- **I12 reserve-margin band [13.8%, 28.7%] — FAIL in every multi-year ISO.**
  CAISO 2026 −12.7% → 2034–2050 48–60%; NEISO 2026 5.0% → 2050 67.5%; PJM 2026–2038
  0.3–13% (below floor) → 2046–2047 30–32% (above band); ERCOT 2027–2039 2.6–12.9%
  (chronically below floor). The single most-violated invariant — the direct
  fingerprint of the non-equilibrium capacity price.
- **I7 reliability floor — FAIL for CAISO/NEISO/NYISO at the base year 2026**
  (accredited firm < requirement: CAISO 42.8<56.4 GW, NEISO 26.2<28.9, NYISO
  31.4<37.2), and for ERCOT 2027 (retirement-bounded, energy-only branch). **PJM
  PASSES I7** — its accredited firm capacity clears its requirement every year
  even at low RM. The base-year I7 failures for the other capacity-market ISOs
  suggest a base-year accreditation/requirement basis mismatch (the #1532 basis
  flag surfacing on the accreditation side) distinct from the evolution over-build.
- **I3 unserved/dump — FAIL, two different mechanisms.** For CAISO/NEISO it is
  **VRE curtailment** growing monotonically with over-build (CAISO dump 2.5%→29%,
  NEISO →28% of renewable potential). For ERCOT/PJM it is **slack (unserved
  load)** appearing late-horizon (ERCOT 0.09% by 2040, PJM 0.12% by 2047) — the
  de-firming producing genuine shortage.
- **I9 storage integrity — FAIL for CAISO** (simultaneous charge+discharge grows
  0.6%→5.8% of throughput). The ε=0.001 storage tiebreaker is insufficient at
  high storage penetration + high negative-price frequency; a degeneracy/numerical
  issue, not physics.
- **I10 RPS dual — WARN (oscillation)** for CAISO/NEISO: REC dual flips
  50↔0.001 $/MWh year-to-year as VRE builds through the RPS target (binding ↔
  slack toggling — a cobweb in the REC price).
- **I13 cobweb — WARN** (CAISO solar/wind, ERCOT storage/solar/gas_cc, PJM wind):
  lumpy on/off build patterns from one-pass evolution + non-responsive prices.
- **I14 price sanity — WARN, two modes.** ERCOT/PJM: LW price exits the
  fuel-implied band on the *high* side late-horizon (ERCOT $216 vs CC-MC band
  ~$47 by 2040; PJM $152 by 2047) — de-firming scarcity rent. CAISO/NEISO:
  10–18% *negative*-price hours from VRE oversupply.

---

## 5. F1/F2 de-firming verdict (does it compound to 2050?)

**No — it does not simply compound. It overshoots in both directions, and the
sign of the late-horizon error depends on market design.** Reserve margin
(accredited firm / peak − 1) at snapshots (ERCOT/PJM partial → last available year
shown; NYISO 1 year only):

| ISO | design | RM 2026 | RM 2030 | RM 2040 | RM 2050 | pattern |
|---|---|---|---|---|---|---|
| ERCOT | energy-only | 14.9% | 9.0% | 12.9% | — | de-firm to 2037 trough (2.6%), no backstop recovery |
| CAISO | cap-market | −12.7% | 25.3% | 59.7% | 55.7% | short → **over-build** (ΔRM +68.5pp) |
| PJM | cap-market | 6.3% | 1.8% | 17.7% | (31.9% @2047) | **both**: de-firm to 2031 (0.3%) → over-build |
| NEISO | cap-market | 5.0% | 29.3% | 44.7% | 67.5% | short → **over-build** (ΔRM +62.6pp) |

Two-phase mechanism, same root cause (the fixed net-CONE capacity price never
falls as the fleet lengthens; CR-1 landed but gated off per P-2A):

- **Phase 1 (2026–~2035) — de-firming compounds in every ISO.** The base fleet
  starts at or below the planning floor (I7/I12 fail early); economic entry lags
  load growth, so RM *falls* further (ERCOT to 2.6% @2037, PJM to 0.3% @2031). In
  energy-only ERCOT this is where scarcity emerges (§6). This is the F1/F2
  de-firming the plan flagged — and it is real and material through mid-horizon.
- **Phase 2 (~2035–2050) — divergence by market design.** Capacity-market ISOs'
  adequacy backstop + entry *over*-correct with no price signal to stop, so RM
  balloons to 30–67% (I12 fails high; VRE dump and negative prices climb).
  Energy-only ERCOT has no backstop, so it stays chronically short — the
  de-firming does not recover, it expresses as persistent scarcity instead.

**So the plan's question — "does de-firming compound to 2050?" — answers:** it
compounds *early* everywhere, then the capacity-market backstop overshoots the
other way while ERCOT stays short. Neither endpoint is an equilibrium; both are
artifacts of the non-responsive capacity price. (PJM is the clearest single-ISO
demonstration of *both* phases in one trajectory.)

---

## 6. #2064 watch — ERCOT scarcity-hours non-monotonicity (PERSISTS)

The manager asked whether T1.4a's ERCOT scarcity non-monotonicity persists over
the full horizon. **It does.** ERCOT single reference path, slack>1MW hours and
price-scarcity (VOLL=$5000):

| year | slack_hrs | hrs p≥500 | hrs p≥2000 | max $ | RM | retire GW |
|---|---|---|---|---|---|---|
| 2029 | 1 | 13 | 13 | 5000 | 7.1% | 0 |
| 2031 | 2 | 12 | 12 | 5000 | 5.5% | 0 |
| 2037 | 11 | 40 | 40 | 5000 | **2.6%** | 0 |
| 2038 | 0 | 0 | 0 | 78 | 8.4% | 0 |
| 2039 | 39 | 445 | 253 | 2761 | 5.7% | 0 |
| 2040 | 107 | 516 | 408 | 2761 | 12.9% | 0 |

`slack_hrs` is **non-monotone** (0→1→0→2→0…→11→0→39→107; collator flag
"monotone non-decreasing: False"). The scarcity spikes coincide with reserve-margin
troughs, and the 2037→2038 collapse (11→0 slack, $5000→$78) then 2038→2039 jump
(0→39) is the exact discrete-transition signature #2064 describes. Note ERCOT
**retires only 1.85 GW (2027) and nothing thereafter** — so here the de-firming
is driven by **load growth outpacing entry**, not retirement, but the resulting
one-pass discreteness (a year's entry either does or doesn't clear the adequacy
gap before scarcity is realized) reproduces the same non-monotone scarcity T1.4a
found across the demand ladder. #2064 is a full-horizon phenomenon, not a
short-window artifact. (Capacity-market ISOs show ~0 slack — over-built — so #2064
is ERCOT-specific, as expected.)

---

## 7. Capacity / price / CO2 trajectory snapshots

| ISO | year | LW $/MWh | CO2 Mt | thermal GW | VRE GW | total GW | cum build GW |
|---|---|---|---|---|---|---|---|
| ERCOT | 2026 | 23.7 | 155.3 | 78.8 | 80.0 | 158.8 | 0.0 |
| ERCOT | 2040 | **216.4** | 208.1 | 100.3 | 99.0 | 215.3 | 78.3 |
| CAISO | 2026 | 49.7 | 37.8 | 31.2 | 29.0 | 76.8 | 0.0 |
| CAISO | 2050 | 50.7 | **6.9** | 44.9 | 129.0 | 198.8 | 142.8 |
| PJM | 2026 | 33.4 | 303.3 | 169.8 | 25.0 | 201.7 | 0.0 |
| PJM | 2040 | 58.3 | **476.4** | 243.8 | 50.5 | 300.1 | 123.5 |
| NEISO | 2026 | 46.2 | 24.3 | 23.5 | 4.1 | 33.1 | 0.0 |
| NEISO | 2050 | 69.0 | **7.6** | 30.8 | 73.1 | 109.4 | 85.7 |

**CO2 diverges by ISO and it is not obviously right.** CAISO/NEISO decarbonize
hard (VRE over-build: CAISO −82%, NEISO −69% to 2040) while **ERCOT (+34% to 2040)
and PJM (+57% to 2040) CO2 *rises*** — load growth + thermal expansion
(PJM thermal 170→244 GW) outrunning clean entry, with no carbon price binding in
the reference config. The rising ERCOT CO2 independently reproduces in the
2026–2040 golden fixture (§8: 151→238 Mt) so it is a genuine model behavior, not
a run artifact — but a 2040 ISO with *rising* emissions under default policy is a
driver-wiring question (IRA/RPS/carbon strength) worth a Tier-1 follow-up, not a
finding to tune here.

---

## 8. Ranked issue list

Every item routes to a root-cause investigation, not a threshold change (rules
1/11/14). The dominant root cause behind #2–#7 is one thing: **prices (capacity
and energy) do not respond to the fleet the model is building** — the CR-1/CR-2
lane's exact remit.

1. **MISO forecast cannot execute** (§3) — missing `STORAGE_BASE_FLEET_MW["MISO"]`.
   Hard blocker; no forecast coverage for MISO until fixed.
2. **Non-equilibrium capacity trajectory / I12 fails everywhere** (§5) — fixed
   net-CONE capacity price gives no signal to halt entry/backstop; RM overshoots
   to 30–67% (cap-market) or collapses to scarcity (ERCOT). Blocks any
   capacity-expansion use of the 2026–2050 forecast until CR-1 is validated +
   flipped on (gated on P-2A prereqs: #1532 basis, position calibration, CR-3.1
   ELCC).
3. **Base-year I7 failures for CAISO/NEISO/NYISO** (§4) — accredited firm <
   requirement in 2026; likely the #1532 accreditation/requirement basis mismatch
   on the supply side. PJM does not exhibit it — a useful A/B for isolating the
   basis bug.
4. **ERCOT de-firming → scarcity + non-monotone #2064** (§5/§6) — energy-only
   adequacy expresses as VOLL spikes and rising LW price ($216 by 2040); one-pass
   discreteness makes scarcity non-monotone. Root cause is entry-vs-load timing,
   not retirement.
5. **VRE over-curtailment (I3) + negative prices (I14) in cap-market ISOs** —
   direct consequence of #2's over-build; CAISO dump→29%, neg-price hours→18%.
6. **Storage simultaneous charge+discharge (I9, CAISO→5.8%)** — ε=0.001
   tiebreaker insufficient at high storage penetration / frequent negative
   prices; numerical degeneracy.
7. **RPS-dual (I10) and build (I13) oscillation** — cobweb instability from
   one-pass evolution + non-responsive prices.
8. **Rising ERCOT/PJM CO2 under default policy** (§7) — driver-wiring question
   (carbon/IRA/RPS strength vs load growth), route to a Tier-1 driver-battery
   follow-up.
9. **Feasibility / concurrency** (§2) — per-plant multi-zone late-horizon years
   need ~9–10 GB each and ~8 h wall (PJM); a release gate needs a bigger box or
   serialized late-horizon years.

---

## 9. Supporting tooling changes (no model behavior touched)

- **Golden fixture deepened 2032 → 2040** (`scripts/golden_forecast_bands.py`;
  fixture renamed `tests/golden/ercot_2026_2040.*`). The pinned ERCOT reference
  band regression now validates a deeper mid-horizon checkpoint (2040 end-year
  capacity + 15-year annual series). Re-seeded on real HiGHS at the current HEAD;
  per-PR presence test passes. Observation baked in: ERCOT golden CO2 rises
  151→238 Mt 2026→2040 (matches the per-plant run's rising ERCOT CO2, §7).
- **Collator import fix** (`scripts/collate_full_horizon.py`) — added the
  `results.outputs` import that late-binds `DispatchResult.from_parquet`. Without
  it every `_slack_hours` read raised `AttributeError` and silently returned −1,
  so the **#2064 slack metric never computed**. Reporting-tool fix only.

## 10. What this session did / did not do

- **Did:** ran the reference forecast to 25/25 for CAISO+NEISO, 22/25 PJM, 15/25
  ERCOT, 1/25 NYISO; scored I1–I14 on each; discovered + root-caused the MISO
  blocker; confirmed the F1/F2 two-phase non-equilibrium and #2064 persistence;
  captured feasibility data; deepened the golden fixture; fixed the collator slack
  metric.
- **Did not:** finish PJM/ERCOT/NYISO or run MISO (stopped mid-horizon at owner
  request — re-run to completion is required for a full gate); change any model
  code, threshold, offer curve, or capacity_market_clearing default; register
  anything on the backcast dashboard; solve/score any 2022 or H1-2026 data.
- **Re-run note (owner):** expect to re-run P-3A once P-2C's ELCC curves land and
  shift the accredited retirement/build trajectory — and after the MISO blocker
  (#1) is cleared so all six ISOs are covered.

*Data provenance: `results/full-horizon/<iso>/full_horizon_summary.json` (per-ISO)
and `results/full-horizon/_tables.md` (collated), reconstructed for partial ISOs
from cached per-year parquets via `scripts/archive/_gen_partial_summaries.py`. Forecast
probes — not dashboard-registered.*
