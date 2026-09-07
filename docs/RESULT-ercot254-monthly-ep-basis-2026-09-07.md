# RESULT — the root cause is CONFIRMED and the level repair works on the price; it is **NOT a keeper candidate**, and the reason is a diagnosed second-order defect (ercot-254)

> Scored against `docs/PRECOMMIT-ercot254-monthly-ep-basis-2026-09-07.md`, its
> `docs/ADDENDUM-ercot254-g1-scope-correction-2026-09-07.md`, and the 2021
> predictions registered **before the solve** in
> `docs/ADDENDUM-ercot254-2021-retest-prediction-2026-09-07.md`. All four bundles
> were **deleted before merge** (rule 29 `[R-SCREEN]` clause c); every number this
> session cites is here, and git history is the record for the bytes.
> **Rule 30(c): ERCOT's determination is the train-tier verdict and is untouched —
> it stays CALIBRATED on `2026-09-05-ercot248-two-config-keeper`.**

## 0. Bottom line

| | |
|---|---|
| **Root cause (phase 0)** | **CONFIRMED and quantified.** `FINDING-ercot254` stands unamended. |
| **The level repair on price** | **WORKS, decisively.** The eleven non-Uri months' bias falls **+160.8 % → +79.1 %**; **every one of the twelve months improves**; February moves **−4.1 % → +16.7 %**. |
| **The merit order (C1)** | **Barely moves, and two of my three pre-registered class predictions were WRONG IN SIGN.** |
| **2021 gates** | **REGRESS.** C3c PASS → FAIL (234 → 688 h vs actual 258); C3b 0.361 → 0.501. |
| **In-sample 2024/2025** | **Near-inert**, no criterion flips, exactly as the pre-solve footprint said. |
| **Keeper candidate?** | **NO — not recommended.** §5. |
| **Successor** | Named and identified in-sample: §6. |

## 1. The screen (2025), all gates PASS

Pre-solve, zero-LP, on the reconstructed 2025 fleet:

| gate | measured | STOP bar | verdict |
|---|---|---|---|
| G-1 (as written) | 0.6151 $/MMBtu | > 1e-9 | **FIRED** — mis-scoped, diagnosed in the addendum |
| **G-1′** (rows the applier owns) | **0.0000**, 1,727/1,727 rows | > 1e-9 | **PASS** |
| **G-1″** West inertness (new, stricter) | **exactly 0.0** on all 97 West rows | any nonzero | **PASS** |
| G-2 confinement | non-gas 0.000e+00; gas max 0.6151 | >0 / >0.62 | PASS |
| G-3 level | 3.1552 → 3.1565, **+0.0013** | > 0.05 | PASS |

Post-solve, arm vs a same-HEAD control one flag apart (G-CTRL form 2):

| gate | measured | STOP bar | verdict |
|---|---|---|---|
| G-4 magnitude | Δ system LW LMP **+$0.2974/MWh** (pre-solve arithmetic ≈ $1.76 upper bound) | > $5.00 | PASS |
| G-5 non-target | C2 PASS→PASS, C3b PASS→PASS (0.101 → 0.107) | any PASS→FAIL | PASS |
| G-6 protective | C6 UNATTESTED in **both** (a replay bundle writes no attestation); C8 SKIPPED in both | any flip | PASS (by identity, not by a positive attestation — stated) |
| G-7 shed | slack **0.0000** and dump **0.0000** in both | > 1.0 MWh | PASS |

**The control solve earned its cost.** It measured HEAD drift against the committed
keeper at **+0.0293 $/MWh** on the 2025 system load-weighted LMP — an order of
magnitude below the mechanism's own +0.2974. `PRECOMMIT` §3 spent it because the
G-DRIFT audit (172 files, 153,004 insertions since the keeper's `0207d69d`) could
not honestly be classified INERT hunk by hunk. The measurement is a stronger
statement than that audit would have been, and it retroactively supports G-CTRL
form 4 for the other years **empirically** rather than by assertion.

## 2. The training window — near-inert, and 2023 is CONFOUNDED

Full span 2023–2025 vs the committed keeper (registry verdict):

| criterion | year | keeper | arm | keeper val | arm val | actual |
|---|---|---|---|---|---|---|
| C3a | 2024 | PASS | PASS | 30.9214 | 30.8179 | 30.99 |
| C3a | 2025 | PASS | PASS | 33.4132 | 33.7399 | 36.29 |
| C3b | 2024 | PASS | PASS | 0.131 | **0.123** | — |
| C3b | 2025 | PASS | PASS | 0.101 | 0.107 | — |
| C3c | 2024 | CAVEAT | CAVEAT | 22 | 22 | 53 |
| C3c | 2025 | CAVEAT | CAVEAT | 1 | 1 | 31 |
| C1 (all classes) | 2024/2025 | PASS/SKIPPED | **identical statuses** | — | — | — |
| C2 | 2024/2025 | PASS | PASS | — | — | — |

**No criterion flips in either keeper-matched year**, and the price moves are
−$0.10 and +$0.33/MWh. That is the pre-solve footprint (0.2064 / 0.2412 $/MMBtu)
landing exactly where it was predicted to.

**2023 is NOT interpretable and is reported as such.** `scripts/replay_keeper.py`
on the merged `ercot248_two_config_keeper` bundle applies the **FORWARD** config to
every year, because the merged `meta.json` carries only that config — the three
fields that distinguish the two (`ercot_offer_swcap_clip`, the CC_REGULAR `peak`
band 151.008 vs 4.576, `unit_outage_fleet_status_scope`) appear in
`run_config_carveout_2023.json` and in **no** `meta.json` key. The replay's 2023
therefore reads C3a $38.92 (−39.5 % vs actual $64.32) and C3b 0.725 — which are the
**ercot-234 forward-config-on-2023 numbers** the keeper's own matrix stamp records
(−39.7 %, 0.730), not this mechanism's effect. **This is a third provenance defect
of the same family as `FINDING-ercot254` §5, and it is the single thing blocking a
promotion decision on merits.**

## 3. The 2021 re-test, against predictions registered before the solve

Same recipe as the committed `2026-09-07-ercot253-2021-rung`, one flag apart.

**All prices below are on ONE basis — the hourly system load-weighted LMP,
recomputed from each bundle's own `hourly/system_2021.parquet`.** On that basis the
committed run253 reads Feb **−4.1 %** and ex-Feb **+160.8 %**, where `RESULT-ercot253`
§2a reported −14.9 % / +144.0 % on a different aggregation. **The two are not mixed
here**; every number in this section is arm-vs-control on the same basis.

| month | actual | run253 | **re-test** | run253 err | **re-test err** |
|---|---|---|---|---|---|
| Jan | 20.79 | 61.06 | **32.59** | +193.7 % | **+56.8 %** |
| **Feb (Uri)** | 1521.84 | 1459.52 | **1776.45** | −4.1 % | **+16.7 %** |
| Mar | 19.42 | 63.22 | **33.16** | +225.5 % | **+70.8 %** |
| Apr | 46.80 | 105.17 | **72.84** | +124.7 % | **+55.6 %** |
| May | 23.39 | 63.99 | **34.93** | +173.6 % | **+49.3 %** |
| Jun | 38.39 | 103.95 | **72.72** | +170.8 % | **+89.4 %** |
| Jul | 36.80 | 98.38 | **68.33** | +167.3 % | **+85.7 %** |
| Aug | 35.37 | 92.42 | **61.18** | +161.3 % | **+73.0 %** |
| Sep | 41.57 | 92.84 | **60.42** | +123.3 % | **+45.3 %** |
| Oct | 46.87 | 146.43 | **116.93** | +212.4 % | **+149.5 %** |
| Nov | 40.38 | 77.19 | **48.95** | +91.2 % | **+21.2 %** |
| Dec | 25.82 | 61.66 | **60.54** | +138.8 % | **+134.5 %** |
| **ex-Feb** | **34.15** | **89.06** | **61.15** | **+160.8 %** | **+79.1 %** |
| annual | 148.19 | 189.97 | 187.47 | +28.2 % | +26.5 % |

### 3a. Prediction scorecard — reported at full magnitude, hits and misses alike

| # | registered prediction | measured | verdict |
|---|---|---|---|
| **P1** | ex-Feb falls to $45–60, bias +30 % to +75 % | **$61.15, +79.1 %** | **direction RIGHT; magnitude just OUTSIDE the registered band** |
| **P2** | February rises, bias turns positive, 0 % to +60 % | **+16.7 %** | **CORRECT, inside the band** |
| **P3** | annual C3a sign **declined** | +28.2 % → +26.5 % | declining was right — a +$317 February rise nets against a −$27.9 ex-Feb fall |
| **P4** | CC_REGULAR rises, miss to −6…−13 TWh | 97.226 → **98.095**; miss −16.02 → **−15.15 TWh** | **direction right, magnitude BADLY WRONG** |
| **P5** | CT_PEAKER falls | 10.641 → **11.133 (RISES)** | **WRONG IN SIGN** |
| **P6** | ST_GAS falls | 17.105 → **18.533 (RISES)** | **WRONG IN SIGN** |
| **P7** | West rows exactly inert | 0.0 delta | correct |

**Why P5/P6 were wrong, diagnosed not excused.** My arithmetic reasoned only within
the gas fleet: a flat $/MMBtu term multiplies through heat rate, so removing it
relieves peakers most and should widen CT−CC. It ignored **the coal margin
entirely.** Cheaper gas displaced coal — COAL_PRB 58.956 → **55.306 TWh** (−3.65),
C2 coal 76.40 → **72.44** — and that ~3.7 TWh redistributed across the *whole* gas
fleet (CC +0.87, ST_GAS +1.43, CT +0.49, CC_CHP −0.13), not preferentially to CC.
Within gas the merit order is still set by the **zonal SPREAD**, which this arm does
not touch and whose 2021 rows carry the same February contamination
(`FINDING-ercot254` §1a). `ADDENDUM-ercot254-2021-retest-prediction` §3 pre-declared
that the spread was untouched and that C1 would improve but not close; it did not
foresee the coal channel, and that is a miss in my reasoning, not in the record.

### 3b. The gate regression, and its cause

| criterion | run253 | re-test | actual | |
|---|---|---|---|---|
| **C3c** (h > $200) | 234 (**PASS**, 0.907×) | **688 (FAIL, 2.67×)** | 258 | **PASS → FAIL** |
| **C3b** NRMSE | 0.361 | **0.501** | — | worse |
| C3a | +28.2 % | +26.5 % | — | ~flat |
| C1 CC_REGULAR | 97.226 | 98.095 | 113.245 | FAIL → FAIL |
| h ≥ $9,000 | 34 | 47 | — | — |

**The cause is the same defect one resolution finer, and it is not hand-waving.**
The measured EP series is **monthly**, so the repair applies February 2021's
$59.73/MMBtu to **all 672 February hours**. The real Uri gas spike lasted about
**five days** (Feb 13–18). February's model mean therefore lands close to right
(+16.7 %) while its *breadth* is far too wide: the 454 extra hours above $200 are
almost exactly February's non-storm hours. The annual smearing is fixed; a
**within-February** smearing is exposed underneath it.

## 4. What the phase-0 finding got right, and what it did not close

**Right:** the object, its magnitude, its two opposite signs, and the direction of
the price repair on all twelve months. **Not closed:** C1. The FINDING claimed the
level term "explains both load-bearing failures." The price half is demonstrated;
the **merit-order half is not** — removing the level moves CC_REGULAR by +0.87 TWh
of a 16 TWh miss, and the CT/ST over-run gets *worse*. The C1 driver is more
plausibly the **zonal spread's** 2021 dispersion (range 6.45 vs 1.95 $/MMBtu in
2023, with Houston on a flat cited −0.15 and West absent), which is a separate
input defect this arm never touched. **`FINDING-ercot254` §3's C1 paragraph is
overclaimed and this document supersedes it on that point**; §§1–2, §1a, §5 and §6
stand as measured.

## 5. Disposition — **NOT a recommended keeper candidate**

Against the owner's standing standard ("structural integrity improves but gates
regress may still be a keeper"), four things weigh, and they do not get there:

1. **Structural integrity does improve**, and materially — a measured series used at
   the resolution it was measured at, zero DOF, and an eleven-month price bias
   halved. That is a real rule-1 `[R-STRUCT]` gain.
2. **But it is not a promotable bundle.** The full-span run's **2023 is the FORWARD
   config, not the keeper's carve-out** (§2), so it does not satisfy rule 16
   `[R-ALLYEARS]` on the keeper's own recipe. Promoting it would silently drop the
   2023 carve-out. This is a blocking fact, not a judgement.
3. **In the two keeper-matched years the arm changes nothing** — no criterion flips,
   ±$0.33/MWh. There is no in-sample gain to bank, and rule 22 forbids banking the
   2021 gain: a validation rung is model-selection evidence and can neither certify
   nor decertify (rule 30(c)).
4. **The 2021 gate regression has a named cause that is fixable at the next
   resolution** (§6). Promoting the monthly form now would bake in the
   within-February smearing and then have to be re-promoted over it.

**Recommendation: keep `ercot_ep_gas_basis_monthly` BUILT and default-OFF**, on
main, byte-identical off, with the matrix cell at `O`. It is one CLI switch from the
successor's A/B.

## 6. The successor, identified in-sample

**A DAILY delivered-gas basis for the ERCOT hub zones.** The EP series is monthly by
construction, so this needs a different measured source — daily Waha / Houston Ship
Channel / Katy settlement prices — which is **data intake, unrestricted under rule
22** ("what is held out is the SCORE, never the DATA") and identifiable entirely on
2023–2025, where the daily-vs-monthly footprint can be measured before any 2021
solve exactly as this session measured the monthly-vs-annual one. It subsumes this
mechanism (rule 19 `[R-ONE-MECH]`: a daily series carries the monthly level, so the
two never stack), and it is the only construction under which February 2021 prices
its five storm days rather than its twenty-eight.

Three further items this session measured and did **not** touch, each named:

* **The 2021 zonal SPREAD table** (`FINDING-ercot254` §1a) — the likelier C1 driver,
  per §4. Needs a monthly/daily per-zone re-derivation from EIA-923 receipts.
* **The absent 2021 West `neg_day_freq`** — falls back to a **2024** default of 0.42
  and produces **inverted** regimes (deep $7.45 above firm $3.41).
* **Two provenance defects**: `meta.json` records `ercot_zonal_gas_basis` and
  `ercot_west_netload_gas_shape` as `false` on runs that armed them through
  `prb_overrides` (so `replay_keeper._ENV_GATED_INERT`'s hard-fail is blind exactly
  where it was written to bite), and the merged two-config `meta.json` cannot
  reproduce the 2023 carve-out at all (§2).

## 7. Governance

Four bundles solved (2025 control, 2025 arm, 2023–2025 full span, 2021 re-test), all
**deleted before merge**. Nothing registered, no dashboard entry moved, no keeper
changed, ERCOT stays **CALIBRATED** on the train tier. The 2021 spend is a rule-22
validation touchpoint under ERCOT's `complete` marker (declared 2026-08-31;
validation tier is outside the holdout freeze) and is **step 4 of the touchpoint
loop — a re-test of a repair identified from the input file and screened on 2025 —
never step 3.** No parameter was identified on, fitted to, or selected against 2021,
and the predictions it was scored against were committed upstream of the solve.
