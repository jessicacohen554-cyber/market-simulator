# PRE-DECLARATION — capx D33: the MISO additions-under-build repair

**Pushed BEFORE the D33 solve starts.** Graded at full magnitude, misses
included, in `FINDING-capx-d33-miso-additions-repair-2026-09-02.md` §6.

**Lane:** capx D33 — the ADDITIONS repair upstream of D31's FC-3 exit-residual
chain (`FINDING-capx-d31-miso-caprev-repair-2026-09-02.md` §7).

**Rule 14 [R-ACCURATE] sign discipline (binding).** Nothing below was sized,
tuned, or sequenced by what it does to the exit residual, or to any band. Both
legs were identified from committed sources and measured artifacts BEFORE this
document, and this document is pushed BEFORE the solve. The exit residual's
direction is declared (P4) but no magnitude is claimed, and no parameter exists
that could have been moved to hit one — the repair has **zero free parameters**.

---

## 0. What was measured, and what is being changed

**Leg 1 — the planned-additions coverage audit (a MEASUREMENT, not a knob).**
Every MISO generator that actually reached commercial operation in 2021–2025
(canonical EIA-860 release; 716 units, 31.151 GW) traced back to each hindcast
vintage's proposed sheet by `(Plant Code, Generator ID)`. At the run's
**vintage-2020** information cutoff the known-additions channel
(`load_planned_additions` + its FFR-5E VRE limb, U/V/TS with
`Effective Year > 2020`) reaches **5.390 GW of 31.151 (17.3 %)** — of solar
**1.036 of 18.649 GW (5.6 %)** and of wind **1.384 of 7.200 GW (19.2 %)**.
**16.021 GW of the solar is ABSENT FROM THE VINTAGE FILE ENTIRELY** (not filed
with EIA at the cutoff); 1.264 GW is status-filtered (P/L/T) and 0.327 GW fails
the vintage gate. **Coverage is therefore not the gap and cannot be**, even at a
rule-13-violating widening to every status. Nothing in leg 1 is armed: the
FFR-5E procurement channel stays default-OFF, and its vintage-2020 MISO content
(1,034.4 MW solar, 1,380.0 MW wind) has COD 2021/2022 — outside the scored
window on either basis.

**Leg 2 — the economic-entry screen (the repair).** Measured on the committed
entry-screen diagnostics of probe `miso-d33-probe-entrydiag`
(key `1b0f1a5e75719b92` — the D31 recipe plus the decision-neutral
`--entry-screen-diagnostics` arm; its 2025 decisions reproduce D31's to the MW):
the step-5 screen declined **every candidate in every screen year 2022/2023/2024**
(`binding_cap: unprofitable`, five rows each) — solar at
**−24,835 / −21,070 / −34,598 $/MW-yr** and wind at
**−3,919 / −1,880 / −20,819 $/MW-yr** — with `attribute_revenue_per_mw_yr`
**exactly 0.0 on every VRE row in every year**.

That zero is structural, not incidental. `RENEWABLE_ZONE_ALLOCATION["MISO"]`
sends **100 % of economically-entered solar to MISO-South**, and MISO-South is
eligible under **no row** of `MISO_RPS_COMPLIANCE_REGIONS` (proved directly off
`build_rps_region_arrays`: MN/WI/MO carry the Midwest-footprint mask that omits
it; MI is MISO-East-only; IL is MISO-Illinois-only), while the run's own zonal
REC vector peaks at the **$30/MWh ACP** (ledger `rps_dual` = `np.max(vector)` =
30.0 in 2021/2023/2024/2025, with the measured `p[MISO-West] = −0.0` and
`p[MISO-South] = 0.0` forcing that $30 into MISO-East and/or MISO-Illinois).
The market meanwhile built 18.649 GW of MISO solar and 7.200 GW of wind,
**75.8 % / 79.0 % of it outside the two allocation buckets**.

**The repair:** `ScenarioConfig.entry_vre_zone_selection` (GATED, default False
— `cache_key(ScenarioConfig())` stays `603c2498bf71d21d`), **armed for MISO
only** through `ISOConfig.default_scenario_overrides`. Armed, the screen values
each VRE candidate in every zone that carries the resource and sites it where
its own margin is highest, over machinery the screen already had (per-zone CF
profile, per-zone LP prices, the K-row zone-resolved REC/clean credit, the zonal
RA gate). Cost is zone-invariant, so argmax(revenue) is argmax(margin). No free
parameter (rule 21), no measured outcome (rule 13), one construction of the RA
payment shared by chooser and screen (rule 19). The allocation bucket is the
incumbent and is displaced only by a **strictly** better zone, so ties, a
zone-blind scalar dual, and absent zonal inputs all leave siting untouched.

## 1. The run

```
uv run python scripts/run_capacity_hindcast.py \
  --iso MISO --start-year 2021 --end-year 2025 \
  --vintage 2020 --fuel-variant realized \
  --out-dir results/hindcast/miso-2021-2025-realized-t1h-d33
```

Bare HEAD recipe, every solve-affecting flag omitted (the arming reaches the
solve through the ISO's own overrides, not the CLI). Fresh out-dir is the
fresh-solve guard. Registered preserve-then-overwrite: bare `miso-t1h` takes the
new run, D31 is preserved at `miso-t1h-pre-d33`.

## 2. Pre-declared outcomes

**P0 — the arming reaches the solve.** `run_config.json` records
`entry_vre_zone_selection: true`, and the cache key is neither D31's
`3649264ca98a1fb4` nor the probe's `1b0f1a5e75719b92`.
*Falsifier:* the field records `false`.

**P1 — the attribute leg turns on, and it turns on in a REC-eligible zone.**
The decided VRE rows in the evolution ledgers' `entry_pipeline` /
`renewable_additions` carry a zone in **{MISO-East, MISO-Illinois}** — not
MISO-South, not MISO-West.
*Falsifier:* every decided VRE row still sites in MISO-South / MISO-West. That
would refute the identification outright and make the repair inert.

**P2 — entry fires before 2025.** Solar and/or wind decide > 0 MW in **at least
two** of the 2022 / 2023 / 2024 screens (D31: zero in all three).
*Central expectation:* solar decides 1,236.4 MW (its measured vintage-2020
ladder cap, 2 × 0.6182 GW) in 2022, and the ladder then ratchets.
*Falsifier:* zero decisions in all three, i.e. no year before 2025 fires.

**P3 — the addition bands, both still short.** `add.by_tech`:
* **solar** model rises from 1.236 GW to **2.0–5.5 GW** against 18.649 actual —
  i.e. still a **FAIL** at roughly −70 % to −89 %. The ceiling is not the
  repair's: the FFR-4A pending-stock netting (`entry_pipeline_aware_signal` OFF,
  COD lag 2) caps the long-run decision rate at C/L and throttles the ladder's
  ratchet, so a 1,236 MW/yr start cannot reach the market's 6–7 GW/yr by 2025.
* **wind** model rises from 4.000 GW to **4.0–8.0 GW** against 7.200 actual;
  it **may cross into PASS** (the ±25 % band is 5.400–9.000 GW). Declared as a
  possibility, not a prediction.
* **storage** unchanged at 4.000 GW (+437.7 %, FAIL) — a different screen.
*Falsifier:* solar `model_gw` does not rise at all.

**P4 — the exit residual moves toward the actual; DIRECTION ONLY, no magnitude
claimed.** New VRE arriving from 2024 creates accredited headroom, so the
reliability floor releases more than D31's 4.469 GW. Declared band
**4.5–12.0 GW** against 17.369 actual (D31: −74.3 %).
*Falsifier:* `retire.total_gw` **falls below** D31's 4.469 GW.
This is the residual rule 14 forbids me to have sized anything by, and I have
not: the repair carries no parameter that could move it.

**P5 — invariants hold.** All 14 forecast invariants stay **PASS** (D31's
record). *Falsifier:* any I1–I14 FAIL.

**P6 — declared, NOT predicted.** The gas bands (`gas_cc` +7.2 % PASS,
`gas_ct` +8.6 % PASS in D31) may break in either direction: more VRE depresses
the price signal the thermal screens read, and the ladder/queue interaction is
shared. Whatever they do is reported at full magnitude, not defended.

**P7 — governance.** Determination stays **HOLD** on FC-3; the ff-verdicts edit
touches exactly two keys (`miso-t1h`, `miso-t1h-pre-d33`); no verdict outside
`miso-t1h`'s own keys moves (the charter's STOP condition, checked against the
diff before the commit).

## 3. Declared observation, routed not touched

The probe's 2025 entry screen prices its capacity leg at **$304,418 /
$307,656 / $125,491 / $53,759 per MW-yr** for gas_ct / gas_cc / solar / wind —
roughly **4× MISO's ~$79.8k/MW-yr annual net-CONE anchor**, and the reason every
2025 candidate cleared at its cap. That is the D31 RBDC seam read at the entry
screen's own forward `reserve_position`, and **D31's closed repairs may not be
revisited because a residual moved** (rules 13/14/23). Recorded here so it
cannot be mistaken for something D33 introduced; routed to the capacity-price
lane.

## 4. What stays routed (unchanged from D31 §8)

D32's floor-retention composition monopoly (untouched — `_floor_retention_merit`
is not read or written by this lane); per-class SAC accreditation intake;
seasonal accreditation basis; the BTMG operating-mode split; the cross-ISO
clearing D6; the director's 8-failure unit-test census.
