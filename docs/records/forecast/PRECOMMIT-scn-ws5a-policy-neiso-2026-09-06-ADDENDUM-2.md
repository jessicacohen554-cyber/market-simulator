# ADDENDUM 2 to PRECOMMIT-scn-ws5a-policy-neiso-2026-09-06 — the `CES-P60` bracketing leg (owner ruling S15), and a correction to ADDENDUM 1's mechanism

**Lane** SCN-WS5A-POLICY-NEISO · **Date** 2026-09-07 · **Ruling** SCN-DESK r#18 card D-12 →
**S15** (ledger §5.4) · **THE PIN** `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b` ·
**Written and pushed BEFORE the `CES-P60` solve** (rule 29 `[R-SCREEN]`), after the lane's nine
registered legs and its FINDING.

**Nothing already declared changes.** Every case, kill, key, gate and prediction in the parent
PRECOMMIT and in ADDENDUM 1 stands as written and is scored as written. This document adds ONE
leg, its key, its gates and its predictions — and corrects one mechanism claim I made in
ADDENDUM 1 §2 and repeated in the FINDING, which the G-B1 arithmetic forced me to check at the
line level rather than at the paragraph level.

---

## 1. STEP 1 — the REF RPS dual per year, and whether the mask binds (zero LP)

From the committed REF trajectory at THE PIN (`results/scn-campaign-load-2026-09-06-r2/NEISO/REF/`,
key `8878d29743555b45`; the same `rps_dual` column the FINDING §2 table reports for every arm):

| year | REF `rps_dual` $/MWh | the CES dual `CES-P10` / `CES-P20` / `CES-P30` carry | mask binds? |
|---|---|---|---|
| 2026 | **50.0** | 10.0 / 20.0 / 30.0 | **YES** |
| 2027 | **50.0** | 10.0 / 20.0 / 30.0 | **YES** |
| 2028 | **50.0** | 10.0 / 20.0 / 30.0 | **YES** |
| 2029 | **50.0** | 10.0 / 20.0 / 30.0 | **YES** |
| 2030 | **50.0** | 10.0 / 20.0 / 30.0 | **YES** |

NEISO's state RPS row escapes at its own `STATE_RPS_ACP` = **$50/MWh** in 5 of 5 years, in REF and
in every arm this lane solved. The mask binds in every year of the window, so **step 2 applies and
the `CES-P60` leg is added.**

## 2. A CORRECTION — the entry screen's RPS leg *is* fuel-gated, and the mask is narrower than I said

ADDENDUM 1 §2 wrote that the entry fold's RPS leg "is applied to every candidate technology with no
fuel gate at all", and FINDING §0(1) and §7 item 5 repeat it. The S15 addendum's own citation is
`new_entry.py ~:1132-1143`. **Read at the line level at THE PIN, that is wrong, and the error is in
which fold the citation points at.**

- `new_entry.py:1133-1143` is the `attr` fold inside `_zone_revenue`, the ranking helper **inside
  `_choose_vre_zone`** — a function called only for a VRE candidate, to pick its build zone. Its
  `rps_credit_for_zone(...)` leg carries no fuel test because its caller has already restricted the
  tech to VRE. The absence of a gate there is **vacuous**, not general.
- The two folds that actually decide entry both gate it:
  `new_entry.py:1190-1197` and `new_entry.py:1474-1483` each compute
  `rps_for_tech = rps_credit_for_zone(...) if tech in _RENEWABLE_NEW_FUELS else 0.0`, and
  `_RENEWABLE_NEW_FUELS = frozenset({"wind", "solar"})` (`new_entry.py:121`).

**So the $50 escape masks WIND and SOLAR candidates, and nothing else.** For every other CES-eligible
tech — `offshore_wind`, `nuclear`, `geothermal`, `hydro`, `gas_cc_ccs`, `hydrogen_ct`,
`hydrogen_ccgt`, `nuclear_smr` — the RPS leg contributes **0.0**, NEISO's legacy exogenous EAC is
**$0.00/MWh** for every candidate tech (measured below), and the federal premium was therefore the
**sole and fully visible** attribute price from `CES-P10` upward.

**This makes the measured null STRONGER, not weaker, and it is why the bracket is worth solving.**
`vre_mw` was identical in REF and in all eight non-cap arms in all five years — and now it is known
that in eight of the nine eligible techs the premium was never masked at all. Whatever kept
`offshore_wind` and `nuclear` out of NEISO's build set at a fully-visible $30/MWh is **not** the RPS
escape. The bracket separates the two remaining readings: at $60 the wind/solar mask is cleared for
the first time, so if entry still does not move, the finding is *"NEISO carries no economic VRE
entry at any attribute price this campaign can reach"* rather than *"the CES row is masked"*.

The FINDING is amended in the same session to carry this correction at full magnitude, in place —
not as a footnote. **The measured facts in the FINDING do not change**; the mechanism sentence
attached to them narrows from "every candidate tech" to "wind and solar".

## 3. GATE G-B1 — computed from step 1's duals, BEFORE the solve

The entry fold is `attr = max(effective_eac_price_for_tech(config, tech, year), rps_for_tech,
clean_for_tech)` with `rps_for_tech` gated as §2 states, and
`effective_eac_price_for_tech = max(legacy exogenous EAC, premium × tech_credit_fraction)`
(`policy/federal_ces.py:543-545`). NEISO's RPS dual is a **scalar** (50.0), so the fold is
zone-invariant and the tech-zone-year statement collapses to a tech-year one. The premium carries
`federal_ces_premium_escalation_real = 0.0` and no `federal_ces_premium_by_year`, so `attr` is
**year-invariant across 2026–2030** (asserted in code, all five years, all techs).

| candidate tech | RPS leg? | credit fraction | legacy EAC | `attr` REF | `attr` P10 | `attr` P30 | **`attr` P60** | **P60 − REF** |
|---|---|---|---|---|---|---|---|---|
| `wind` | yes | 1.00 | 0.00 | 50.000 | 50.000 | 50.000 | **60.000** | **+10.000** |
| `solar` | yes | 1.00 | 0.00 | 50.000 | 50.000 | 50.000 | **60.000** | **+10.000** |
| `offshore_wind` | no | 1.00 | 0.00 | 0.000 | 10.000 | 30.000 | **60.000** | **+60.000** |
| `nuclear` | no | 1.00 | 0.00 | 0.000 | 10.000 | 30.000 | **60.000** | **+60.000** |
| `geothermal` | no | 1.00 | 0.00 | 0.000 | 10.000 | 30.000 | **60.000** | **+60.000** |
| `hydro` | no | 1.00 | 0.00 | 0.000 | 10.000 | 30.000 | **60.000** | **+60.000** |
| `gas_cc_ccs` | no | 0.95 | 0.00 | 0.000 | 9.500 | 28.500 | **57.000** | **+57.000** |
| `hydrogen_ct` | no | 1.00 | 0.00 | 0.000 | 10.000 | 30.000 | **60.000** | **+60.000** |
| `hydrogen_ccgt` | no | 1.00 | 0.00 | 0.000 | 10.000 | 30.000 | **60.000** | **+60.000** |
| `nuclear_smr` | no | 1.00 | 0.00 | 0.000 | 10.000 | 30.000 | **60.000** | **+60.000** |
| `gas_cc` / `gas_ct` | no | 0.00 | 0.00 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

**G-B1 CLEARS, and it clears on the leg the mask actually covers.** `attr` strictly exceeds REF's
for ten eligible techs in every zone and every one of the five years. The decisive rows are `wind`
and `solar` at **50.000 → 60.000**: the FIRST level in this campaign at which the $50 escape stops
being the binding buyer for a VRE candidate. The screen's revenue term moves by
`Δattr × CF × 8760 h` per MW-year, so the VRE leg gains **+10.000 $/MWh of expected output** and
the eight non-VRE eligible techs gain a further **+30.000** (`gas_cc_ccs` **+28.500**) on top of what
`CES-P30` already showed them.

Also relevant to whether that uplift has anywhere to go: **REF's own build volumes are far below the
queue budget** — `builds_renew_mw` 0 / 0 / 0 / 1802.0 / 1198.0 MW against `QUEUE_CAP_GW["NEISO"]` =
**4 GW/yr** — so nothing in this ISO's entry path is queue-limited, and P-11's "exhausts the queue
budget" premise was wrong for that reason too (FINDING §5). The screen is economics-limited, which
is exactly the limb a +$10/MWh attribute price acts on.

## 4. The leg — key, isolation, and the two fields

| | |
|---|---|
| case | **`CES-P60`** |
| definition | the committed `CES-P30` case overrides with `federal_ces_premium_usd_per_mwh` set to **60.0** — i.e. the SAME two fields every `CES-P*` leg sets (`federal_ces_enabled: true`, the premium). Nothing else. |
| resolved key at THE PIN | **`a37868175d5ae724`** |
| resolved CES fields | `federal_ces_enabled=True`, `federal_ces_premium_usd_per_mwh=60.0`, `federal_ces_target_by_year=None`, `federal_ces_acp_usd_per_mwh=None`, `federal_ces_crediting=clean_capture`, `federal_ces_ccs_capture_fraction=0.95` |
| run id | `neiso-2026-2030-scn-campaign-policy-2026-09-06-ces-p60` |
| label | `scn-campaign-policy-2026-09-06-ces-p60` |

**Chain validation, this session, at THE PIN:** the same
`matrix_configs → resolve_policy_bundle → set_caiso_fsno_partition(False) →
apply_iso_scenario_defaults → cache_key()` chain reproduces `REF` `8878d29743555b45`,
`CES-P10` `4e5f93124767a5f4` and `CES-P30` `42328a83592ebfbb` **exactly**, so the chain that
produced `a37868175d5ae724` is the chain the solve will use.

**Cache isolation, two ways:** `git grep a37868175d5ae724 origin/main -- '*.json'` returns **0
hits**, and `results/NEISO/` holds **0 entries** in this container. No collision with a committed
bundle, another leg, or a warm cache.

**$60 is not re-levelled, not tuned and not per-ISO.** It is the S15 common level for every ISO,
set above the footprint's highest published ACP ($50) from the published ACP table and never from
any residual — rule 25 `[R-ISO-SCOPE]` and rule 1 `[R-STRUCT]`. Ruling S3's committed ladder
{10, 20, 30} is untouched: this is a bracketing leg beside it.

## 5. Pre-registered predictions for the bracket

Written before the solve, scored at full magnitude whatever they do.

- **P-B1.** `vre_mw` **moves** in at least one year against REF's 4100 / 4100 / 4100 / 5902 / 7100 MW.
  Reasoning: the VRE attribute leg rises 20 % (50 → 60 $/MWh) with the queue budget unbound, and
  this is the first campaign level at which a NEISO VRE candidate sees any uplift at all.
  **Confidence: low.** REF's `builds_renew_mw` is invariant to every attribute price the lane has
  tried, and is zero in three of five years, which reads more like the step-4 known-additions
  channel than an economic screen sitting near its threshold. If P-B1 misses, that reading is
  confirmed and §0(1)'s conclusion strengthens from "masked" to "not economics-limited at any
  reachable attribute price" — the reportable-finding branch S15 names, not a gate failure.
- **P-B2.** `gas_cc_ccs` 2030 generation **exceeds** `CES-P30`'s 62.5748 TWh. The retrofit screen is
  where every non-cap arm's response has landed and it has not saturated across the ladder
  (25.93 → 46.83 → 57.06 → 62.57 TWh); doubling the premium should push it further.
- **P-B3.** The **leakage-inclusive** 2030 total falls below `CES-P30`'s 5.2251 Mt, while in-ISO
  `emissions_mt` may move either way — the §2.3 reversal is a boundary artefact and I decline to
  predict its sign at a level neither side of the ladder has reached.
- **P-B4.** `clean_share` 2030 exceeds `CES-P30`'s 0.8767, and no arm-year carries `unserved_mwh`
  above 0.0 or a 14/14-invariant regression.

## 6. Gates for this leg — S15's, restated with NEISO's specifics. STOP-only.

| gate | statement | status |
|---|---|---|
| **G-B1** | the mask is actually cleared: at $60 the entry fold's `attr` strictly exceeds REF's for at least one eligible tech-zone-year, computed from step 1's duals BEFORE the solve | **PASS, pre-solve** — §3. Ten techs, every zone (scalar dual), all five years; `wind`/`solar` 50.000 → 60.000. |
| **G-B2** | footprint as a CES case: eligible/ineligible shares and the CES dual move; every zero-carbon class row otherwise as G3 declares (eligible generation pinned at its CF ceiling, nuclear and hydro flat, curtailment 0.0000, movement confined to thermal, import and retrofit rows) | scored after the solve |
| **G-B3** | no non-target load-bearing invariant flips PASS → FAIL vs REF (14/14 in REF; `unserved_mwh` 0.0 in every year) | scored after the solve |

A gate may kill this arm and may never promote it, and none reads a target residual. **A leg that
clears G-B1 and still shows no entry response is a REPORTABLE FINDING at full magnitude, not a gate
failure** (S15, verbatim) — that outcome is the reason the leg exists.

## 7. Execution — identical to the parent §8, one leg

```
H0=bdfb3095e9fa0cd2bec3f4e843f320b42588c72b
[ "$(git rev-parse HEAD)" = "$H0" ] || exit 90
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_ces_leg.py \
    --config configs/scenarios/neiso_scenario_base_2026_2030.yaml \
    --matrix configs/scenario_campaign_matrix.yaml \
    --case CES-P30 --set federal_ces_premium_usd_per_mwh=60.0 \
    --campaign scn-campaign-policy-2026-09-06 \
    --out-dir results/scn-campaign-policy-2026-09-06/NEISO/CES-P60
```

`--set` is the driver's own declared override seam (`run_ces_leg.py:136-151`, applied AFTER the
ladder's case overrides), and it is what MISO, NYISO and CAISO used for the same S15 leg — the
resolved config is therefore identical in construction across every ISO that ran it, which is what
makes $60 one common level rather than five. Years sequential, one solve at a time, HEAD guard
around the leg. **Budget: 5 solve-years at NEISO's measured 1.09 min/solve-year ⇒ ≈6 min of LP,
peak RSS ≈3.7 GB.** Registration is `register_forecast_run.py --summary … --kind scenario --label
scn-campaign-policy-2026-09-06-ces-p60`, in the same commit as any invariant FAIL it declares.

## 8. Duties

No default moved, no knob moved, no `ScenarioConfig` field added, no matrix case added, no gate
rewritten, no prediction withdrawn. **DOF ledger: still zero free parameters** — $60 is an
externally-identified published-ACP bracket, not a fitted value, and it is never swept. Everything
under `src/`, `scripts/` and `configs/` remains read-only to this lane. Rule 22 / R-AZ: the solve
years are 2026–2030, forecast mode, no holdout tier touched at launch or at registration. Rule
29(b): form 4 — the committed REF is the control and no control solve is earned or spent. Rule
29(c): no screen bundle and no control bundle exists. Backcast byte-identity: untouched by
construction (`mode="forecast"`).
