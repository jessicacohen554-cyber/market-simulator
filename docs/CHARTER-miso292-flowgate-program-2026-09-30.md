# CHARTER — miso-292 Part 2: a reduced-network (flowgate) program for MISO internal congestion. Verdict: DATA-BLOCKED for 2022; recommend NO-GO.

```
LANE    : miso-292 (owner ruling "Charter flowgate program", miso-291 §7) — this is RO-2 for
          internal_congestion_split (cell G). It re-opens that cell for design only; no other R/I/G cell.
KEEPER  : 2026-09-28-miso-280-splitremap, unchanged
LP      : none. Design only.
```

## 1. The object

| | value | source |
|---|---:|---|
| C3a 2022 (load-weighted basis, Jan–Oct) | model 59.98 vs INDIANA.HUB 73.56, **−18.5 %** | RESULT-miso292 §2 |
| C3b 2022 (monthly NRMSE) | **0.224** (tol 0.20), new since the basis repair | RESULT-miso292 §2 |
| Indiana hub congestion + losses, Jan–Oct 2022 | **+8.47 $/MWh** (MCC 5.84, MLC 2.63) | miso-291 §1 |
| same, 2023–2025 | +2.3 to +2.5 | miso-291 §1 |
| West (MINN) − Indiana, 2022 | −25.64 actual vs 0.00 model; 72 % congestion | miso-277 §1 |
| Hours with \|West − Indiana\| > $10 | 68.7 % (2022) vs 11.6–33.3 % other years | miso-277 §1 |
| Model Midwest zonal price separation | 0.0000 of 2022 hours | miso-277 §1, miso-240 |

Scope: 2022 only is failing on this object. Hours: every month, widest midday (HE12–15) and June. Zones:
the four Midwest zones West / Illinois / Indiana / East (the step is West vs everything east of it).

**Size vs C3a (inferred, additive approximation).** Adding the 2022 congestion excess over 2023–25
(≈ +6.1 $/MWh) to the model would move C3a 2022 to about −10 % (still FAIL). Reproducing the full
+8.47 would move it to about −7 % (PASS). So the program clears C3a 2022 only if it reproduces 2022's
congestion almost entirely, which requires the 2022-specific drivers (below), not a generic network.
The residual −4.02 $/MWh energy part (day/evening shoulder, coal scarcity) is outside this program and
its main driver (the coal line) is closed.

## 2. What a reduced-network representation would be

Two options, both on the existing six zones (`iso_configs.py` MISO zones; links L1–L6 are a 40,000 MW
never-bind placeholder that "must never be tuned to a price residual"):

- **A. Zone-boundary limits.** Replace the placeholders with real MW transfer limits on L1–L6. Cheap in
  code (the LP already has link bounds). But miso-79/miso-240 measured 88–99.7 % of MISO congestion
  **inside single balancing areas**, not on zone boundaries, and `measured_interface_limits` is already
  **R** (miso-174: no per-seam or zonal MW limit series exists at our grain). Option A has no admissible
  input and is the wrong shape for the object.
- **B. Flowgate constraints on zone injections.** Add rows `Σ_z PTDF[f,z] × net_injection[z,t] ≤ limit[f,t]`
  for a set of named flowgates f, with zone-to-flowgate distribution factors. This is the right shape, and
  it is new LP code (`model/transmission.py`, a new constraint family, rule 2 vectorized). It needs **three**
  inputs per flowgate: a MW limit, a distribution factor per zone, and (for 2022) the outage/derate state.

## 3. Admissible inputs, by year (inventory, on disk and public)

| source | years | what it gives | MW limit? | PTDF? | status |
|---|---|---|---|---|---|
| MISO `YYYY_{rt,da}_bc_HIST.csv` | 2023–2025 (**404 for 2019–2022**, re-checked this session) | binding constraint name, monitored element, contingency, shadow price, TCDC breakpoints | no | no | fetch script exists; not on disk |
| MISO daily `YYYYMMDD_{rt,da}_bc.xls` | 2023+ (**404 for tested 2021/2022 dates**) | same, daily | no | no | public |
| MISO `M2M_Settlement_srw_YYYY.csv` | 2023–2025 on disk (**404 for 2019–2022**) | seam flowgates under M2M: flow, firm-flow entitlement, shadow price | no | no | on disk |
| MISO RDT PBC | 2023–2025 | RDT binding intervals, % breakpoints of an unpublished limit | no | no | on disk |
| Hub LMP components (MEC/MCC/MLC) | 2022 partial (RT Jan 1–Nov 11), 2023–2025 full; **2019–2021 LMP only** | congestion by hub | — | — | answer class (rule 13): localization only |
| LOLE CIL/CEL | PY2022/23+ | RA deliverability per LRZ | RA quantity, not dispatch | no | on disk; lever R (miso-174) |
| PJM DataMiner2 `da_marginal_value` | multi-year incl. 2022 (not verified this session) | PJM-monitored constraints incl. M2M flowgates, shadow price | no | no | licensing-restricted, PJM-side only |
| IMM 2022 State of the Market | 2022 | facility-level narrative: wind-loaded constraints > $1.5 B, overlapping outages $1.1 B, understated ratings $540 M | no | no | narrative, not an input |
| MISO OASIS flowgate TFC / MTEP and FERC 715 cases | current vintage; CEII | ratings, topology | yes (TFC / ratings) | derivable | **not public**: CEII/registration, and no 2022 vintage of the operator derate state |

**Is there any admissible 2022 source? No.** No public dataset gives a MW limit or a distribution factor
for any MISO internal constraint in any year, and for 2022 even the constraint-identity feeds (bc_HIST,
daily bc, M2M) are absent. The only 2022 quantity that localizes the congestion is the hub MCC, which is
the answer (rule 13). The SOM's three 2022 drivers (wind-loaded facilities, overlapping transmission
outages, operator line-rating derates) are each a facility-level, time-varying state that MISO does not
publish historically.

## 4. Rule tests

- **Rule 17 `[R-FLOOR-WINDOW]` (driver, window, forward story).** Driver: physical thermal limits on named
  facilities. Window: whenever flow reaches the limit, which is state-dependent (wind output, outages). A
  forward story exists in principle (MTEP models carry forward ratings and topology) but not for the
  outage and derate state that made 2022 different.
- **Rule 13 `[R-MEASURED]`.** A published rating or TFC would be admissible. A limit, PTDF or derate chosen
  so the Indiana MCC comes out right is forbidden: that is the answer fed back in. Hub MCC may be used only
  to check where congestion lands, never to set a number.
- **Rule 14 `[R-ACCURATE]` misalignment.** A 2025-vintage TFC applied to 2022 is misaligned on time; the
  2022 derate state is precisely the part that is missing, so it cannot be reconciled.
- **Rule 1 `[R-STRUCT]`.** The mechanism is real and would stay in even if it hurt the fit. That does not
  help when its inputs do not exist.

## 5. DOF ledger (if built on the only obtainable inputs)

| parameter | count | identification |
|---|---:|---|
| flowgate set (which facilities) | 1 choice | SOM / bc_HIST 2023–25 names; 2022 unpublished |
| MW limit per flowgate | n | CEII rating (owner-obtained) or none |
| zone distribution factor per flowgate × zone | n × 6 | CEII network model reduction, or none |
| 2022 outage / derate state | time series | **none** — unpublished |

With public data only, every entry after the first is a free parameter, which rule 20 `[R-DOF]` counts as
an open root-cause issue, not a calibration.

## 6. Kill rule (pre-registered here)

The program stops, with no LP spent, if **any** of these holds at the end of Stage 0:
1. No MW limit for the chosen flowgates is obtainable from a published or owner-obtained (CEII) source.
2. No zone distribution factor is obtainable from a network model rather than fitted.
3. For 2022 specifically, the outage and derate state cannot be sourced, so the program could at most add
   a generic network that would reproduce the 2023–25 congestion level (≈ −10 % C3a 2022, still FAIL).

On today's inventory conditions 1–3 all hold for public data. The program is **data-blocked**.

## 7. Staged plan and cost (only if the owner obtains data)

| stage | work | cost |
|---|---|---|
| 0. Data | Owner requests MISO CEII (MTEP / FERC 715 cases) and OASIS flowgate access; confirm licensing lets the repo hold derived numbers; check for any 2022 outage record | owner time; weeks; unknown outcome |
| 1. Design (zero LP) | Network reduction to 6 zones → PTDF table; choose flowgates from 2023–25 bc_HIST; PRECOMMIT the limits from the source | 1–2 sessions |
| 2. Code | New flowgate constraint family (`model/transmission.py`), `ScenarioConfig` gate default off, matrix row in every ISO shard, tests | 1–2 sessions (Opus/Fable, rule 27) |
| 3. Screen | Keeper recipe + flowgates, one shard per year 2019–2025 (rule 36), composed | 7 shards, ~20 min each |
| 4. Decide | Owner ruling on promotion | — |

Even at best, 2022 would still lack its outage state, so Stage 3 is expected to move 2022 toward the
2023–25 congestion level and not clear C3a 2022 (§1).

## 8. Recommendation

**No-go.** The program is data-blocked for 2022 on public data, and a generic network cannot reach the
PASS line for C3a 2022 because the missing part is 2022's facility outages and derates. C3a 2022 and
C3b 2022 stay routed misses. `internal_congestion_split` stays **G**, with this charter added as its RO-2
record. The only way forward is Stage 0 by the owner (CEII access), which is offered as an option, not
recommended.
