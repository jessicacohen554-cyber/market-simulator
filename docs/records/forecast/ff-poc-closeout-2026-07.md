# FF-3E — Full-solve readiness battery + POC close-out (the §2.1b evidence)

**Session.** FF-3E (Wave 3, plan `docs/forecast-development-plan-2026-07.md`
§2.1b full-solve authorization gate; §0 Phase A definition-of-done items 3-4).
Proves the full-horizon forecast **path** is bug-free BEFORE any full solve is
authorized, assembles the per-ISO §2.1b gate scorecard, absorbs FF-4B's
honest-unfit list, and hands the owner the gate-open decision. **Findings only**
— no model code, threshold, offer curve, or default was changed (rules 1/11/14).
The gate-open decision is the owner's (§2.1b(d)).

Requires FF-2D scored (`docs/handoffs/ff-t1-gate-2026-07.md` +
`ff-t1-gate-verdicts.json`, all six ISOs `HOLD`). Branched off `origin/main`
HEAD `f49cf768`.

---

## 0. Headline

**No ISO clears the §2.1b full-solve gate. But the readiness battery is GREEN —
the full-horizon PATH is bug-free.** The plumbing that would waste a 10-hour
golden run resolves cleanly for every ISO across every year 2026-2050; the
config round-trips with a stable cache_key; a killed run resumes to a
result-identical bundle. So **every remaining blocker is structural** (the I4
capacity-accounting leak, base-year adequacy, ERCOT scarcity, MISO cobweb) —
routed to its L-CAP lane, none an FF-3E target (rule 1). That is the honest
answer to "what would 10 hours of compute buy today": a **mechanically-clean but
structurally-flawed** golden run. The compute is **not yet worth spending** on
any ISO.

**NEISO is closest** — the only ISO with a live calibration-complete marker
(§2.1b(a)) whose sole T1-F blocker is the single I4 leak — but it too fails
(b) (T1-F `HOLD`). The gate stays closed until the I4/A1 lane lands and FF-2D +
this readiness battery are re-scored.

---

## 1. What the readiness battery is (built + run this session)

`scripts/ff_readiness_battery.py` — five instruments (FF-3E prompt items a-e),
none solving beyond T0 scale. Reproduce the no-LP instruments with
`python scripts/ff_readiness_battery.py all`:

| # | Instrument | Solve? | Result |
|---|---|---|---|
| a | **Input-resolution walk** — every exogenous forward input, every ISO, every year 2026-2050, loader-level, fail-loud | no LP | **GREEN** (0 hard fails; plateau/horizon notes §3) |
| b | **Config completeness** — golden-posture round-trip, cache_key stable, §2.1a reflected (rule 24) | no LP | **GREEN** (6/6 ISOs) |
| c | **Kill-resume drill** — T0 NEISO 2026-2028 killed + resumed vs uninterrupted control | T0 solve | **GREEN** — 2026/2027 loaded from cache, 2028 solved, all years identical to control (§5) |
| d | **Wall/RSS projection** — per-ISO full-horizon cost + co-run plan ("what 10 h buys") | no LP | published (§6) |
| e | **Schedulability guard** — `run_full_horizon.py` refuses > 5 solve-years without `--full-solve-authorized` | no LP | live + tested |

Tests: `tests/test_ff_readiness_battery.py` (21, all no-solve, <2 s).

---

## 2. Per-ISO §2.1b gate scorecard

Gate opens only when **ALL** of (a)-(d) hold for the ISO (§2.1b(2)).

| ISO | (a) keeper + marker | (b) T1-F verdict (FF-2D) | (c) crossover gap (FC-4) | (c) readiness | (c) projected cost | (d) owner auth | **Gate?** |
|---|---|---|---|---|---|---|---|
| **NEISO** | ✅ marker 2026-07-07; keeper `neiso-60-phantom-outage` | ❌ HOLD — FC-1 FAIL **I4** (2028 coal off 54 MW) | not run (FF-2D scope) | ✅ green | ~1.0 h (0.95 h proj) | — | **CLOSED** (b) |
| **PJM** | ❌ keeper `pjm-gasshape-interpfix`, **no marker** | ❌ HOLD — FC-1 FAIL **I4** (2029 coal off 743 MW) | ❌ FAIL — price 2025 17.5% CAVEAT; CO2 43-58% | ✅ green | ~7.3 h (solo, 10 GB) | — | **CLOSED** (a,b) |
| **NYISO** | ❌ marker **WITHDRAWN 2026-07-19** | ❌ HOLD — FC-1 FAIL **I7** (2026 firm 30.3<32.1 GW) | not run | ✅ green | ~1.1 h | — | **CLOSED** (a,b) |
| **ERCOT** | ❌ frontier withdrawn 2026-07-17, **no marker** | ❌ HOLD — FC-1 FAIL **I3** (scarcity slack 2027-30) | ❌ FAIL — price 69%→9% (converges); CO2 43-50% | ✅ green | ~2.0 h | — | **CLOSED** (a,b) |
| **CAISO** | ❌ keeper `caiso-102-hourfix`, **no marker** | ❌ HOLD — FC-1 FAIL **I3,I4,I7,I9** | not run | ✅ green | ~2.8 h | — | **CLOSED** (a,b) |
| **MISO** | ❌ keeper `miso-81-phantom-outage`, **no marker** | ❌ HOLD — FC-1 FAIL **I4,I7** + FC-2 FAIL **I13 cobweb** | launched (may fold) | ✅ green | ~10.1 h (solo, 10.5 GB) | — | **CLOSED** (a,b,+FC-2) |

**Reading.** (a) is met only by NEISO. (b) is met by **no ISO** — all six read
`HOLD` on FC-1 structural integrity, dominated by the **I4 capacity-accounting
leak** (NEISO/PJM/MISO/CAISO), **I7 base-year adequacy** (CAISO/MISO/NYISO), and
**ERCOT I3 scarcity**. (c) readiness is green for all six; (c) crossover gap is
measured only for ERCOT/PJM (FF-2D scope) and both `FAIL` on CO2 (a partly
reconstruction-basis artifact — treat price as the load-bearing signal:
ERCOT converges 69%→9% by 2025, PJM in-band except a 2025 CAVEAT). (d) no
authorization exists for any ISO.

---

## 3. Input-resolution walk (part a) — findings

**GREEN: 0 hard (`MISSING`/`ERROR`) findings across 6 ISOs × 25 years × ~14
inputs.** Every forward driver the golden run leans on resolves at loader level
with no LP: demand growth + DC block, gas/coal/oil paths, carbon program, ATB
entry costs, IRA/OBBBA windows, RPS target + ACP, federal-CES premium seam,
capacity-market params, confirmed-retirements horizon, weather-year pool.

The walk reports two non-failing classes — both exactly the "held-constant past
year N" honesty §2.1b(c) asks for:

**Held-flat horizon tails (`PLATEAU`).** A forward value the model holds constant
through 2050. Two kinds, both benign but named:

| Input | Plateau from | Kind |
|---|---|---|
| `datacenter_block_mw` (ERCOT/PJM/MISO) | **2030** | source-horizon limit — the published DC-boom anchors end ~2030 |
| `datacenter_block_mw` (CAISO) | 2040 | source-horizon limit (CAISO anchors reach 2040) |
| `rps_target` (CAISO/PJM/NEISO) | 2045 | policy — the state RPS reaches its final target and plateaus |
| `rps_target` (NYISO) | 2040 | policy (NYISO 70×30 / 100×40 final target) |
| `capacity_price_firm` (CAISO/MISO/NYISO) | **2026** | design constant — fixed net-CONE anchor (no forward curve vintages past the published set) |
| `capacity_price_firm` (PJM/NEISO) | 2027 | design constant — last published VRR vintage held flat |
| `demand_growth_rate` (all) | 2031 | design constant — the modeled long-era rate (`DEMAND_GROWTH_TRANSITION_YEAR`=2030) |

**Horizon notes (`INFO`).** Fuel (gas/coal/oil) and carbon-program trajectories
are live to 2050 (no plateau). Two horizon-bounded inputs:

- **Confirmed-retirements** run out mid-window and the economic screen governs
  the tail: ERCOT to 2025, NEISO to 2028, CAISO to 2030, PJM/MISO to their last
  instrument; **NYISO registry is empty (0 rows) → no confirmed channel** (the
  economic screen carries every NYISO exit). No confirmed exit past ~2030 in any
  ISO — late-horizon retirements are entirely the economic screen's.
- **IRA/OBBBA windows close inside the horizon (policy-correct):** wind/solar
  PTC/ITC to **2027** (the OBBBA cliff), 45U to 2032, 45Q to 2032, 45V to 2027.
  Forecast years 2033-2050 run with the federal credits expired — as legislated.

None of these is a plumbing bug. Each is a documented modeling limit the golden
run inherits and this close-out names (§8).

---

## 4. Config completeness (part b) — GREEN

The §2.1a golden-posture `ScenarioConfig` (per ISO):

- round-trips through `config.yaml` value-identically under JSON/`run_config`
  normalization (the only representational change is tuple→list on the
  `*_offer_surface_netload_pcts` sequence fields — exactly how `run_config.json`
  already stores them, and LP-inert), with a **stable `cache_key`** (rule 24);
- reflects every §2.1a decision: `datacenter_load_path="mid"` (c),
  `correlated_forced_outage=True` (d), `entry_lookahead_reprice=True` (e), and
  decision (a) per-ISO capacity-market clearing ON for every real-capacity ISO
  (PJM/MISO/NYISO/NEISO/CAISO) and OFF for energy-only ERCOT;
- dumps its full flag surface (rule 24 — every tunable visible in `run_config`).

**One plumbing gap found + fixed (§9):** `run_full_horizon.py`'s `reference_config`
is the P-3A *probe* posture (capacity clearing OFF) — a golden solve launched
through it would silently run the wrong posture. Added a `--golden-posture` flag
(additive; default off = byte-identical probe) so the schedulable runner can
carry the frozen §2.1a decision (a).

---

## 5. Kill-resume drill (part c)

**GREEN.** T0 NEISO 2026-2028, killed after 2027, resumed over the partial cache:

| check | result |
|---|---|
| killed mid-horizon (after 2027) | ✅ true |
| cache_key match (control == resume) | ✅ true (`e2a0d4b6fe1c9087`) |
| pre-kill years LOADED from cache, not re-solved | ✅ 2026, 2027 (parquet mtimes unchanged across resume) |
| per-year dispatch+ledger identical to control | ✅ 2026, 2027, 2028 all equal |

The resumed run loaded 2026 and 2027 from the partial cache (their parquets
predate the resume phase by ~2.5 min) and solved only 2028; every year's
dispatch hash, price hash, and evolution-ledger counts matched the uninterrupted
control exactly. A killed golden run resumes to a byte-equivalent bundle.

*Measurement note:* the runner applies per-ISO default config overrides
(`runner.py` ~431-441) BEFORE hashing the cache key, so the drill locates every
bundle by the **runner-returned** key, never a recomputed
`golden_posture_config().cache_key()` — a bookkeeping subtlety the battery
handles explicitly.

**Mechanism proven.** The runner evolves the fleet deterministically every year
and only the LP *solve* is cache-skipped (`is_cached` short-circuit,
`runner.py:1156`); a killed run re-invoked over the partial per-year cache
reloads the completed years and solves only the remainder, so the evolution
state (fleet, cumulative deployment, prior-year duals) reconstructs identically.
The drill runs the T0 NEISO 2026-2028 window three ways in isolated cache roots
— uninterrupted control, "kill" after year N-1, resume over the partial cache —
and compares per-year dispatch+ledger signatures.

---

## 6. Wall/RSS projection (part d) — "what would 10 hours buy"

From the measured FF-2D §2.1 T1-F anchors + the §2.4 late-horizon super-linear
caution (LPs grow as economic entry adds units; **early years are a firm lower
bound, late years grow super-linearly — do NOT extrapolate the median flat**).
Full 2026-2050 (25 solve-years), one ISO at the golden posture:

| ISO | T1-F median/yr | lower-bound wall | **projected wall** | late yr | proj peak RSS | co-run? |
|---|---|---|---|---|---|---|
| NEISO | 78 s | 0.54 h | **0.95 h** | 3.2 min | 4.3 GB | pairable |
| NYISO | 90 s | 0.62 h | **1.09 h** | 3.8 min | 4.2 GB | pairable |
| ERCOT | 144 s | 1.0 h | **2.0 h** | 7.2 min | 4.6 GB | pairable |
| CAISO | 200 s | 1.39 h | **2.78 h** | 10.0 min | 5.5 GB | pairable |
| PJM | 235 s | 1.63 h | **7.34 h** | 31.3 min | **10.0 GB** | **solo** |
| MISO | 324 s | 2.25 h | **10.12 h** | 43.2 min | **10.5 GB** | **solo** |

**Concurrency plan (rule 12).** PJM and MISO reach ~10 GB late-horizon and must
run **solo** on the 15 GB box (two per-plant ISOs ≥8.6 GB cannot co-run —
measured OOM, §2.4). The four lighter ISOs pair. Serial worst-case for all six
under this plan: **~21 h**. CES-armed legs add ~4-5 h/ISO (deferred W4).

**What 10 hours buys.** A 10-hour budget buys **one** full-horizon golden ISO
comfortably for every ISO except MISO (which needs ~10 h alone); NEISO/NYISO/ERCOT/CAISO
each finish in ≤3 h. So compute is **not** the binding constraint — the T1-F
structural blockers are. Ten hours today would produce a bug-free-plumbing but
structurally-flawed run; the honest recommendation is to spend it on the L-CAP
lanes, not a golden solve.

---

## 7. Schedulability guard (part e)

`run_full_horizon.py` now refuses any window > 5 solve-years unless
`--full-solve-authorized` is passed — the §2.1b window cap made executable,
mirroring `run_calibration_full.py`'s rule-22 `--holdout-authorized` gate. The
guard is the pure function `assert_schedulable(start, end, authorized)` (unit
tested: refuses 25 yr and 6 yr unauthorized, allows 5 yr, allows 25 yr
authorized). Discipline-level, per the plan (§2.1b(4)).

---

## 8. Honest-unfit list (absorbs FF-4B; plan §0.3)

What a golden bundle **cannot** claim, named so it is never implied-solved. The
five FF-2D/FF-4B structural blockers, plus the FF-3E readiness findings and the
standing §0.3 items:

**Open structural blockers (route to L-CAP; NOT FF-3E targets — rule 1):**

1. **I4 "A1" capacity-accounting leak** (`model/capacity.py` +
   `results/evolution_ledger.py`) — the **dominant T1-F blocker** (4/6 ISOs:
   CAISO gas_st, PJM/MISO/NEISO coal lose MW with no matching ledger
   `retirements` record). Fix A1 and NEISO+PJM clear FC-1. Un-actioned since
   FF-0B.
2. **I7 base-year adequacy "A2"** (CAISO/MISO/NYISO) — hydro dispatched but
   excluded from the accredited firm-capacity ledger (`accredited_firm_capacity_mw`
   reads the persistent `fleet`, which never contains hydro). NEISO closed via
   the FF-2C flip. Route: FF-1C (hydro-in-ledger) + CR-3.1 (VRE/storage ELCC).
3. **ERCOT I3 scarcity slack** (2027-2030, + the #2064 non-monotone signature)
   — one-pass discreteness + cfo/AEO fuel. Route: L-CAP/L-SCAR.
4. **MISO I13 gas_ct cobweb** (NEW, FF-2C flip-induced) → FC-2 FAIL. Alternating
   gas_ct entry loop under the priced curve. Route: L-CAP entry-sizing
   (BLK-10/FF-1A).
5. **Frozen ERCOT golden fixture** (`tests/golden/ercot_2026_2040.json`, seeded
   `f0f7c67` with `use_campd_bins=False`) — the bands moved (FF-1F DC=mid+cfo,
   FF-2A entry-lookahead, FF-G2 AEO fuel; 2030 LW $45→$79.5). Reseed is a
   15-solve-year invocation → **owner-authorized golden-refresh one-off**, not
   schedulable here (§2.1b cap). Left un-widened and un-touched (a stale-but-honest
   fixture > a silently-regenerated one).

**Standing §0.3 un-certified (until an instrument says otherwise):**

6. **Locational siting** — `DATACENTER_ZONE_SHARE` is empty, so the DC block
   sites by load-share, not published campus locations; and the DC block
   plateaus post-2030/2040 (§3). No zonal DC siting claim.
7. **Forward-auction timing** — capacity price uses fixed net-CONE anchors past
   the last published VRR vintage (§3 `capacity_price_firm` plateau); no forward
   auction-clearing-date claim.
8. **Gated mechanisms/ISOs** — `capacity_deliverability_limits` part (b) is
   unvalidated in any keeper; the legacy P2 economic-commitment screen is
   archived; the CES premium ladder is CES-off in the BAU posture (its seam is
   verified, its campaign deferred, W4).

**FF-3E-surfaced readiness limits (documented, not bugs):**

9. **Confirmed-retirement horizon is near-term** (no confirmed exit past ~2030;
   NYISO registry empty) — 2031-2050 retirements are entirely the economic
   screen's; the golden run's late-horizon exit path is un-anchored to any
   binding instrument.
10. **IRA/OBBBA credits expire mid-horizon** (wind/solar 2027, 45U/45Q/45V by
    2032) — 2033-2050 runs credit-expired (policy-correct, but the late-horizon
    entry economics carry no federal credit).
11. **NYISO curve-eligible but not gate-ready** — the §2.1a decision has NYISO
    curve-ON, but its calibration marker was withdrawn 2026-07-19 (co-dependent
    offer curves vs the corrected phantom-outage envelope); gate (a) stays closed
    until NYISO re-calibrates.

---

## 9. Plumbing gaps fixed this session (task 2; NOTHING structural — rule 1)

- **`run_full_horizon.py --golden-posture`** (additive) — layers the §2.1a
  decision-(a) per-ISO capacity clearing so the schedulable runner carries the
  frozen golden posture, not the P-3A probe posture. Default off =
  byte-identical to the probe.
- **`run_full_horizon.py --full-solve-authorized` + `assert_schedulable`** — the
  part-e §2.1b guard.
- **`data/clean/confirmed-retirements` built** via
  `scripts/data/curate_confirmed_retirements.py` — the loader is designed to
  fail loud in forecast mode when this derived (gitignored) partition is absent
  (the W1-B B3/B4 phantom-477-MW guard). A golden solve on a fresh checkout WILL
  hit it; the fix is the documented precondition (the curation command), since
  the partition is derived and must not be committed. Raw registry
  (`data/raw/confirmed-retirements/*.csv`) present for all six ISOs.

No offer curve, threshold, mechanism, or default was changed.

---

## 10. Owner-decision box — opening the gate per ISO

The gate-open decision is the owner's (§2.1b(d)). This session's recommendation:

**Hold every gate.** No ISO meets (b); five of six fail (a). The binding
constraint is structural, not compute or plumbing — the readiness battery proves
a golden run would execute cleanly, it just would not be *correct*.

**Recommended sequence:**

1. **Land the I4/A1 capacity-accounting lane** (L-CAP) — the single highest-leverage
   fix: it clears FC-1 for NEISO and PJM outright and removes the dominant blocker
   for CAISO/MISO.
2. **Re-score FF-2D** (T1 gate battery) and **re-run this readiness battery** at
   the post-A1 HEAD.
3. **Authorize NEISO first** if it then clears (a)✅+(b) — it is the cheapest
   (~1 h full-horizon), already marker-complete, and its only T1 blocker is A1.
   Then PJM (needs a marker), then the I7/I13 lanes for CAISO/MISO/NYISO.
4. Each authorization is a **separate, session-logged owner sign-off** naming the
   ISO, window, and compute budget (§2.1b(d)); no standing authorization; a
   regressed gate condition (e.g. a withdrawn marker) re-closes the gate.

**Owner sign-off box (per ISO):**

```
Gate-open authorization (§2.1b(d))
  ISO: __________     Window: 2026-2050 (T3 golden) | 2026-2035 (T2)
  (a) keeper+marker present: [ ]   (b) T1 rubric no-FAIL: [ ]
  (c) crossover gap + readiness + cost reviewed: [ ]
  Compute budget authorized: __________ h
  Authorized by / date: __________
```

---

## 11. Registration & what this session did / did not do

- **Registered** the readiness battery summary on the **forecast-validation
  namespace** (`frontend/data/hindcast/ff-3e-readiness.json`, kind `readiness`) —
  never the backcast registry (plan §2.3 / rule 15). The full per-ISO/per-year
  detail regenerates from `scripts/ff_readiness_battery.py all`.
- **Did:** built the 5-instrument readiness battery + 21 no-solve tests; added
  the §2.1b schedulability guard + `--golden-posture` flag to
  `run_full_horizon.py`; ran the T0 NEISO kill-resume drill; built the
  confirmed-retirements clean partition; produced this per-ISO §2.1b scorecard +
  honest-unfit list + owner-decision box.
- **Did not:** change any model code, threshold, offer curve, or default (rule
  1); solve/score any 2022 / ≤2021 / 2019 / H1-2026 year (rule 22); run any solve
  on CI (the one T0 drill ran in-session, rule 12); touch the backcast registry;
  solve beyond T0 scale anywhere in the battery.

*Produced 2026-07-20 (FF-3E). Findings only; no LP solved beyond the T0
kill-resume drill; no backcast keeper, dashboard artifact, or holdout year
touched (rules 1/13/14/22). The gate-open decision is the owner's.*
