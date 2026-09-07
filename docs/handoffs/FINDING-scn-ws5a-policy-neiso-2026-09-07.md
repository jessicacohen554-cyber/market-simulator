# FINDING — SCN-WS5A-POLICY-NEISO: the policy axis is invisible to NEISO's deployment screen, and the one case the charter ordered killed is a policy LOOSENING

**Lane** SCN-WS5A-POLICY-NEISO · **Model** Opus (`claude-opus-5`, rule 27 `[R-PUSH]`) ·
**Date** 2026-09-07 · **Branch** `claude/scn-ws5a-policy-neiso-bhlkdp` · **Data profile** `neiso` ·
**Campaign** `scn-campaign-policy-2026-09-06`, kind `scenario`, `reference_case: REF` ·
**THE PIN** `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b` · **Charter** SCN-DESK ledger §5 policy
charter **v6** (r#17) · **Predecessors** `PRECOMMIT-scn-ws5a-policy-neiso-2026-09-06.md` and its
**ADDENDUM 1**, both pushed before the legs they predict.

**9 legs solved, 45 solve-years, 139.0 min of LP. 4 of 13 chartered cases killed at phase 0 on a
proven identity; 1 kill refused on a proven NON-identity. Every leg 14/14 invariants PASS, so this
lane adds no line to `invariant-failures.json`.**

---

## 0. Bottom line

1. **NEISO'S ENTIRE POLICY AXIS IS INVISIBLE TO THE DEPLOYMENT SCREEN, FOR ONE SHARED REASON THE
   CAMPAIGN NEVER SET.** `vre_mw` is **4100 / 4100 / 4100 / 5902 / 7100 MW in REF and in every one
   of the eight non-cap arms, in every year** — the CES premium at $10, $20 and $30, the CES target
   row at its $50 ACP, and both voluntary ceilings all produce **exactly zero** incremental entry.
   NEISO's state RPS row escapes at its own **$50/MWh ACP in 5 of 5 years in every arm**, and the
   entry screen's fold `attr = max(effective_eac_price_for_tech, rps_credit_for_zone(...),
   clean_credit)` (`new_entry.py:1132-1143`) applies that RPS leg to **every candidate tech with no
   fuel gate**. Every level this campaign carries sits at or under $50. **Pre-registered in
   ADDENDUM 1 before the deciding legs ran** (§5).
2. **`CAP-STATE-TIGHT` — the case the charter and `FINDING-scn-cap` §3 both ordered killed as
   "byte-identical to REF" — binds in ALL FIVE years and is a policy LOOSENING of +2.9 to
   +13.9 Mt.** Emissions equal the budget to 3.2e-13 relative. Its dual (12.23 → 8.26 $/t) is
   **below** the RGGI adder it replaced (26.05 → 34.15) in every year while permitting up to 293 %
   more emissions, and it **builds less clean capacity than REF** (2030: 287.4 vs 1198.0 MW).
   Refusing the kill was the single highest-value decision in the lane (§1.2, §2.4).
3. **The CES ladder's monotonicity REVERSES on the leakage line.** $20 → $30 at 2030 makes in-ISO
   `emissions_mt` worse (2.8713 → 2.9392 Mt) and the leakage-inclusive total better (6.102 →
   5.225 Mt), because the extra premium pulls 5.5 TWh of `gas_cc_ccs` in and pushes imports out.
   This is the strongest case the campaign has produced for the WS-0 duty (§2.3).
4. **A binding mass-cap row costs 14.6 min/solve-year against 1.05–3.09 for every other arm** —
   57 % of the lane's total LP on one of nine legs (§6).
5. **Five of my own pre-registered predictions MISSED and are reported at full magnitude** —
   P-1, P-3, P-6, P-11, P-13, plus P-8 as a SPLIT whose stated mechanism was falsified outright
   (§5). The two ADDENDUM 1 predictions, written after two legs and before seven, both HIT.

---
## 1. Phase 0 — what was killed, and the one kill that was refused

Every case below was resolved at THE PIN through `runner.run_scenario_iso`'s own chain
(`matrix_configs` → `resolve_policy_bundle` → `set_caiso_fsno_partition(False)` →
`apply_iso_scenario_defaults` → `cache_key()`), validated by reproducing the two committed NEISO
keys exactly: `REF` `8878d29743555b45` and `LOAD-HI` `0d5c394b6c4e5cb6`.

### 1.1 Four cases killed on a proven LP-input identity — 20 solve-years never spent

| case | key at THE PIN | the ONLY resolved field that differs | killed against |
|---|---|---|---|
| `CARB-LO` | `89059734b9b32165` | `carbon_price_path: zero → low` | REF |
| `CARB-MID` | `ee3f6db1f77352fd` | `carbon_price_path: zero → mid` | REF |
| `CARB-HI` | `2b15ede95d461f6c` | `carbon_price_path: zero → high` | REF |
| `CARB-MID+LOAD-HI` | `7bbc4a70b0720cae` | `carbon_price_path: zero → mid` | the **committed** `LOAD-HI` leg |

Under owner ruling S2's floor, `resolved = max(RFF path, program trajectory)`. NEISO's projected
RGGI trajectory is **26.0545 / 27.8783 / 29.8298 / 31.9179 / 34.1521 $/tCO2** across 2026–2030 and
**dominates every registered path in every year** — the closest approach is `CARB-HI` at 2030,
$30.00 against $34.15. A repo-wide census of `carbon_price_path` at the pin finds its only
LP-affecting consumer to be `policy/carbon.py::resolved_base_trajectory_price`'s `max` (`:187`);
everything else is a docstring, a policy-bundle preset the campaign does not reach, or the
`carbon_path_below_program_warning` guard, which only logs. So the four cases' LP inputs are
identical to their baseline's in every year: the keys move because the field differs, the answers
cannot. This reproduces `FINDING-scn-ws1b-2026-09-06.md`'s "EXACTLY INERT on CAISO/NYISO/NEISO"
from this lane's own resolve, at this lane's own pin, and extends it from WS-1b's single 2027
probe to the whole T1-F window.

`CARB-MID+LOAD-HI` is the sharpest of the four: its answer **already exists on `main`** as the
committed `LOAD-HI` leg, so the campaign's one combined carbon+load case contributes exactly
nothing on NEISO beyond what the load lane published (ΔCO2 +0.444 / +0.644 / +0.801 / +0.482 /
+0.251 Mt).

### 1.2 The kill that was REFUSED, and why

The charter's phase-0 rule for case 13, and `FINDING-scn-cap-2026-09-06.md` §3's NEISO verdict,
both say: budget slack in every year ⇒ `CAP-STATE-TIGHT` is byte-identical to REF ⇒ kill without
solving. **That premise is false on any program ISO, and the charter's own gate G11 is what says
so.** Two code facts, neither a judgement:

1. **The row REPLACES the adder.** `resolve_carbon_program` returns a resolution carrying
   **exactly one** of `price_adder` / `cap_spec` (its `__post_init__` invariant). With
   `mass_cap_enabled` and a schedule naming NEISO, `_power_sector_cap` returns a spec in every
   year, so `price_adder` is `None`, and `resolved_base_trajectory_price`'s documented row-path
   guard (`float(resolution.price_adder or 0.0)`) makes the resolved carbon price **0.0000 $/t in
   every year** — measured, against REF's 26.05 → 34.15. A resolved-input delta of that size is
   the opposite of byte-identical.
2. **The slack test is not evaluable pre-solve.** It compares the budget against emissions
   produced *under the price the case removes*. REF's low 2028–2030 CO2 exists **because** the
   RGGI adder drove 22.6 / 36.3 / 25.9 TWh of `gas_cc_ccs` retrofits; at carbon 0 the repaired
   screen closes (capx D50, owner Q42, measured on NEISO itself).

The case was therefore solved, on the owner's ruling. **§2 shows the refusal was correct**: the
row binds from 2026 and the case is a policy *loosening*, which the naive test would have
recorded as "no difference from REF".

## 2. Per-case deltas vs the committed post-D77 REF

REF is **never re-solved**. Its trajectory is the `-r2` bundle at key `8878d29743555b45`; its
headline scalars — including the import line, clean share, curtailment and unserved that the
slim summary does **not** carry — come from the delta-report CSV SCN-WS5A-RESOLVE regenerated
post-D77 at its leg 2 (`931866cc`). Every CO2 number below carries `import_co2_mt_reported`
beside it (the WS-0 leakage duty). `duals` are `clean_region_duals` in region order
(`FEDERAL_CES`, then `VOLUNTARY`) with the state RPS dual after them.

| case | year | CO2 Mt | dCO2 | import CO2 Mt | clean share | lw $ | avg $ | curt TWh | unserved | duals | builds renew MW | retire MW |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **REF** | | | | | | | | | | | | |
| REF | 2026 | 15.8319 | — | 4.536035 | 0.3485 | 51.892 | 51.20 | 0.0000 | 0.0 | rps 50.0 | 0.0 | 0.0 |
| REF | 2027 | 17.0960 | — | 4.376392 | 0.3458 | 51.403 | 50.50 | 0.0000 | 0.0 | rps 50.0 | 0.0 | 2758.324170000001 |
| REF | 2028 | 9.8722 | — | 4.487150 | 0.5255 | 52.626 | 51.56 | 0.0000 | 0.0 | rps 50.0 | 0.0 | 0.0 |
| REF | 2029 | 4.7566 | — | 4.369626 | 0.6588 | 51.586 | 50.48 | 0.0000 | 0.0 | rps 50.0 | 1802.0 | 1.638 |
| REF | 2030 | 6.1058 | — | 4.765739 | 0.5877 | 54.022 | 53.22 | 0.0000 | 0.0 | rps 50.0 | 1198.0 | 0.0 |
| VOL-MID | 2026 | 15.8323 | +0.0004 | 4.536035 | 0.3485 | 51.888 | 51.20 | 0.0000 | 0.0 | [4.5] rps 50.0 | 0.0 | 0.0 |
| VOL-MID | 2027 | 17.0962 | +0.0002 | 4.376392 | 0.3458 | 51.400 | 50.50 | 0.0000 | 0.0 | [4.5] rps 50.0 | 0.0 | 2758.324170000001 |
| VOL-MID | 2028 | 9.8760 | +0.0038 | 4.487150 | 0.5255 | 52.626 | 51.56 | 0.0000 | 0.0 | [4.5] rps 50.0 | 0.0 | 0.0 |
| VOL-MID | 2029 | 4.7587 | +0.0021 | 4.369626 | 0.6588 | 51.594 | 50.48 | 0.0000 | 0.0 | [-0.0] rps 50.0 | 1802.0 | 1.638 |
| VOL-MID | 2030 | 6.0217 | -0.0841 | 4.765888 | 0.5897 | 54.025 | 53.22 | 0.0000 | 0.0 | [-0.0] rps 50.0 | 1198.0 | 0.0 |
| VOL-HI | 2026 | 15.8323 | +0.0004 | 4.536035 | 0.3485 | 51.888 | 51.20 | 0.0000 | 0.0 | [7.0] rps 50.0 | 0.0 | 0.0 |
| VOL-HI | 2027 | 17.0962 | +0.0002 | 4.376392 | 0.3458 | 51.400 | 50.50 | 0.0000 | 0.0 | [7.0] rps 50.0 | 0.0 | 2758.324170000001 |
| VOL-HI | 2028 | 9.8760 | +0.0038 | 4.487150 | 0.5255 | 52.626 | 51.56 | 0.0000 | 0.0 | [7.0] rps 50.0 | 0.0 | 0.0 |
| VOL-HI | 2029 | 4.7587 | +0.0021 | 4.369626 | 0.6588 | 51.594 | 50.48 | 0.0000 | 0.0 | [-0.0] rps 50.0 | 1802.0 | 1.638 |
| VOL-HI | 2030 | 6.0217 | -0.0841 | 4.765888 | 0.5897 | 54.025 | 53.22 | 0.0000 | 0.0 | [-0.0] rps 50.0 | 1198.0 | 0.0 |
| CES-P10 | 2026 | 15.8319 | +0.0000 | 4.536035 | 0.3485 | 51.892 | 51.20 | 0.0000 | 0.0 | None rps 50.0 | 0.0 | 0.0 |
| CES-P10 | 2027 | 17.0960 | +0.0000 | 4.376392 | 0.3458 | 51.399 | 50.49 | 0.0000 | 0.0 | None rps 50.0 | 0.0 | 2758.324170000001 |
| CES-P10 | 2028 | 9.9012 | +0.0290 | 4.492274 | 0.5266 | 52.560 | 51.48 | 0.0000 | 0.0 | None rps 50.0 | 0.0 | 0.0 |
| CES-P10 | 2029 | 4.2573 | -0.4993 | 4.029449 | 0.7178 | 48.795 | 47.54 | 0.0000 | 0.0 | None rps 50.0 | 1802.0 | 1.638 |
| CES-P10 | 2030 | 3.0942 | -3.0116 | 3.868015 | 0.7538 | 47.708 | 46.83 | 0.0000 | 0.0 | None rps 50.0 | 1198.0 | 0.0 |
| CES-P20 | 2026 | 15.8318 | -0.0001 | 4.536035 | 0.3485 | 51.888 | 51.20 | 0.0000 | 0.0 | None rps 50.0 | 0.0 | 0.0 |
| CES-P20 | 2027 | 17.0940 | -0.0020 | 4.376392 | 0.3458 | 51.398 | 50.49 | 0.0000 | 0.0 | None rps 50.0 | 0.0 | 2758.324170000001 |
| CES-P20 | 2028 | 9.8152 | -0.0570 | 4.482254 | 0.5292 | 52.493 | 51.41 | 0.0000 | 0.0 | None rps 50.0 | 0.0 | 0.0 |
| CES-P20 | 2029 | 4.1123 | -0.6443 | 3.827303 | 0.7321 | 47.384 | 45.95 | 0.0000 | 0.0 | None rps 50.0 | 1802.0 | 1.638 |
| CES-P20 | 2030 | 2.8713 | -3.2345 | 3.230353 | 0.8341 | 42.238 | 41.12 | 0.0000 | 0.0 | None rps 50.0 | 1198.0 | 0.0 |
| CES-P30 | 2026 | 15.8319 | +0.0000 | 4.536035 | 0.3485 | 51.888 | 51.20 | 0.0000 | 0.0 | None rps 50.0 | 0.0 | 0.0 |
| CES-P30 | 2027 | 17.0941 | -0.0019 | 4.376392 | 0.3458 | 51.399 | 50.49 | 0.0000 | 0.0 | None rps 50.0 | 0.0 | 2758.324170000001 |
| CES-P30 | 2028 | 9.8131 | -0.0591 | 4.481523 | 0.5293 | 52.491 | 51.41 | 0.0000 | 0.0 | None rps 50.0 | 0.0 | 0.0 |
| CES-P30 | 2029 | 4.1042 | -0.6524 | 3.751125 | 0.7352 | 47.010 | 45.51 | 0.0000 | 0.0 | None rps 50.0 | 1802.0 | 1.638 |
| CES-P30 | 2030 | 2.9392 | -3.1666 | 2.285939 | 0.8767 | 37.448 | 35.95 | 0.0000 | 0.0 | None rps 50.0 | 1198.0 | 0.0 |
| CES-T80 | 2026 | 15.8323 | +0.0004 | 4.536035 | 0.3485 | 51.888 | 51.20 | 0.0000 | 0.0 | [50.0] rps 50.0 | 0.0 | 0.0 |
| CES-T80 | 2027 | 17.0990 | +0.0030 | 4.376392 | 0.3458 | 51.400 | 50.50 | 0.0000 | 0.0 | [50.0] rps 50.0 | 0.0 | 2758.324170000001 |
| CES-T80 | 2028 | 9.8418 | -0.0304 | 4.479056 | 0.5272 | 52.532 | 51.44 | 0.0000 | 0.0 | [50.0] rps 50.0 | 0.0 | 0.0 |
| CES-T80 | 2029 | 4.7587 | +0.0021 | 4.369626 | 0.6588 | 51.594 | 50.48 | 0.0000 | 0.0 | [-0.0] rps 50.0 | 1802.0 | 1.638 |
| CES-T80 | 2030 | 4.1093 | -1.9965 | 4.391022 | 0.6608 | 51.220 | 50.38 | 0.0000 | 0.0 | [4.29117172636024] rps 50.0 | 1198.0 | 0.0 |
| CES-P20+VOL-HI | 2026 | 15.8319 | +0.0000 | 4.536035 | 0.3485 | 51.889 | 51.20 | 0.0000 | 0.0 | [7.0] rps 50.0 | 0.0 | 0.0 |
| CES-P20+VOL-HI | 2027 | 17.0961 | +0.0001 | 4.376392 | 0.3458 | 51.402 | 50.50 | 0.0000 | 0.0 | [7.0] rps 50.0 | 0.0 | 2758.324170000001 |
| CES-P20+VOL-HI | 2028 | 9.8145 | -0.0577 | 4.482254 | 0.5292 | 52.497 | 51.41 | 0.0000 | 0.0 | [7.0] rps 50.0 | 0.0 | 0.0 |
| CES-P20+VOL-HI | 2029 | 4.1126 | -0.6440 | 3.827000 | 0.7321 | 47.381 | 45.94 | 0.0000 | 0.0 | [-0.0] rps 50.0 | 1802.0 | 1.638 |
| CES-P20+VOL-HI | 2030 | 2.8711 | -3.2347 | 3.230353 | 0.8341 | 42.254 | 41.13 | 0.0000 | 0.0 | [-0.0] rps 50.0 | 1198.0 | 0.0 |
| ALL-CLEAN | 2026 | 16.2812 | +0.4493 | 4.568258 | 0.3450 | 52.112 | 51.40 | 0.0000 | 0.0 | [50.0, 7.0] rps 50.0 | 0.0 | 0.0 |
| ALL-CLEAN | 2027 | 17.7414 | +0.6454 | 4.448649 | 0.3406 | 51.529 | 50.64 | 0.0000 | 0.0 | [50.0, 7.0] rps 50.0 | 0.0 | 2244.8888000000006 |
| ALL-CLEAN | 2028 | 10.6514 | +0.7792 | 4.533788 | 0.5157 | 52.870 | 51.68 | 0.0000 | 0.0 | [50.0, 7.0] rps 50.0 | 0.0 | 0.0 |
| ALL-CLEAN | 2029 | 5.2369 | +0.4803 | 4.463386 | 0.6551 | 52.307 | 51.07 | 0.0000 | 0.0 | [-0.0, -0.0] rps 50.0 | 1802.0 | 1.638 |
| ALL-CLEAN | 2030 | 4.4475 | -1.6583 | 4.438269 | 0.6608 | 51.620 | 50.76 | 0.0000 | 0.0 | [4.205105269436287, -0.0] rps 50.0 | 1198.0 | 0.0 |
| CAP-STATE-TIGHT | 2026 | 20.6700 | +4.8381 | 3.592228 | 0.3485 | 46.675 | 46.07 | 0.0000 | 0.0 | None rps 50.0 | 0.0 | 0.0 |
| CAP-STATE-TIGHT | 2027 | 20.0025 | +2.9065 | 3.761912 | 0.3458 | 48.164 | 47.32 | 0.0000 | 0.0 | None rps 50.0 | 0.0 | 2758.324170000001 |
| CAP-STATE-TIGHT | 2028 | 19.3350 | +9.4628 | 3.955239 | 0.3433 | 49.298 | 48.35 | 0.0000 | 0.0 | None rps 50.0 | 0.0 | 0.0 |
| CAP-STATE-TIGHT | 2029 | 18.6675 | +13.9109 | 3.712614 | 0.3904 | 47.474 | 46.65 | 0.0000 | 0.0 | None rps 50.0 | 1802.0 | 1.638 |
| CAP-STATE-TIGHT | 2030 | 18.0000 | +11.8942 | 3.962221 | 0.3791 | 48.697 | 48.00 | 0.0000 | 0.0 | None rps 50.0 | 287.4 | 0.0 |

**On the REF column itself:** the import line is **26–92 % of the in-ISO level** on this REF
(4.536/15.832 = 28.7 % in 2026; 4.370/4.757 = **91.9 %** in 2029), materially larger than the
charter's "25–41 %", which is the **pre-D77** reading. The denominator collapsed when the retrofit
seam was repaired; the numerator did not. Routed §7 item 3.

### 2.1 The voluntary axis — a pure ceiling ladder that moves nothing

`VOL-MID` and `VOL-HI` carry the **identical volume to the MWh** on NEISO (`E_DC` is exactly 0, so
`f_commit` multiplies zero and `s_base` is 0.08 on both paths), which makes the pair a pure
$4.50-vs-$7.00/MWh WTP-ceiling experiment with no volume confound — cleaner than either lane's
charter anticipated. **Measured: the two arms are byte-identical in every reported scalar, fuel
column and capacity column in all five years. The only difference anywhere is the dual itself.**

**G7 PASS, per arm.** The row binds 2026–2028 (V 8.4289 / 8.4917 / 8.5549 TWh against an eligible
fleet pinned at its CF ceiling, 6.9162) and is slack 2029–2030 (V 8.6186 / 8.6828 vs 10.1517 /
12.0494) — the phase-0 regime table reproduced leg for leg. The dual is **$4.50 and $7.00 exactly**
in the binding years and **−0.0 exactly** in the slack ones.

**The escape absorbs the entire deficit because NEISO has no within-year closure**: eligible
generation is already at its hourly CF ceiling, `offshore_wind` and `geothermal` capacity are zero,
and entry is a between-year screen under one-pass evolution. 2026 escape = 8.4289 − 6.9162 =
**1.5127 TWh exactly**, costing $6.81M at the mid ceiling and $10.59M at the high one — the whole
difference between the two arms.

### 2.2 The CES premium ladder — large, entirely retrofit-driven, and non-saturating

| 2030 | REF | CES-P10 | CES-P20 | CES-P30 |
|---|---|---|---|---|
| `emissions_mt` | 6.1058 | 3.0942 | **2.8713** | 2.9392 |
| `import_co2_mt_reported` | 4.7657 | 3.8680 | 3.2304 | **2.2859** |
| leakage-inclusive total | 10.8715 | 6.9622 | 6.1017 | **5.2251** |
| `clean_share` | 0.5877 | 0.7538 | 0.8341 | **0.8767** |
| `gas_cc_ccs` TWh | 25.9318 | 46.8343 | 57.0604 | **62.5748** |
| `vre_mw` | 7100.0 | 7100.0 | 7100.0 | 7100.0 |

The response is **large** (−49 % to −53 % on in-ISO CO2 by 2030) and **entirely dispatch and
retrofit** — `vre_mw` and `builds_renew_mw` are identical to REF in every rung and every year. This
is the shape SCN-WS2b measured on NEISO in July ("adds ZERO economic entry … the whole response is
dispatch"), now with the mechanism identified: the premium is masked on the entry screen by the $50
RPS escape, and reaches the ISO only through the retirement and CCS-retrofit screens, whose RPS leg
**is** fuel-gated to `{wind, solar}` (`retirements.py:3509-3516`) and therefore does not mask a
credit paid to `gas_cc_ccs` at its 0.95 crediting.

### 2.3 THE LEAKAGE REVERSAL — the campaign's best argument for the WS-0 duty

Read the table above along the bottom two rows. From $20 to $30, **in-ISO `emissions_mt` gets
worse** (+2.36 %) while **the leakage-inclusive total gets better** (−14.4 %). The extra $10/MWh
pulls a further 5.5 TWh of `gas_cc_ccs` into the domestic stack, which displaces imports whose CO2
is reported beside `emissions_mt` and never inside it. **A reader given `emissions_mt` alone would
conclude that a higher CES premium raises NEISO's emissions.** That conclusion is an artefact of
the accounting boundary, and G-E3's reported-only import line is the only thing that makes it
visible. No other arm in this campaign has produced a sign reversal on the scored basis.

### 2.4 `CAP-STATE-TIGHT` — binding, loosening, and investment-suppressing

| year | budget Mt | `emissions_mt` | rel. gap | `co2_cap_price` $/t | REF adder $/t | ΔCO2 vs REF | import line Δ |
|---|---|---|---|---|---|---|---|
| 2026 | 20.670 | 20.6700 | 3.2e-13 | 12.2258 | 26.0545 | **+4.8381** | −0.9438 |
| 2027 | 20.0025 | 20.0025 | 5.2e-14 | 19.0306 | 27.8783 | **+2.9065** | −0.6145 |
| 2028 | 19.335 | 19.3350 | — | 20.3238 | 29.8298 | **+9.4628** | −0.5319 |
| 2029 | 18.6675 | 18.6675 | — | 12.9222 | 31.9179 | **+13.9109** | −0.6570 |
| 2030 | 18.000 | 18.0000 | — | 8.2629 | 34.1521 | **+11.8942** | −0.8035 |

**G10 PASS** in all five years — there is no slack year to test the dual-is-zero limb against.
**G11 PASS**: the resolution carries `cap_spec` with `price_adder` `None`, `resolve_carbon_price`
returns 0.0000, and no federal price is composed on top. **G12**: the quantity instrument's dual is
**below the price instrument it replaced in every year** while permitting far more emissions —
reported with the asymmetry the PRECOMMIT declared before the solve (the adder reaches dispatch
**and** `evolve_fleet`'s screen; the cap dual reaches dispatch only).

**The asymmetry is now visible in the deployment, not merely argued.** 2030 `builds_renew_mw` is
**287.4 MW against REF's 1198.0**, and `vre_mw` ends at 6189.4 against 7100.0. The cap arm caps
emissions **and simultaneously builds less clean capacity than the price arm**, because its dual
never reaches the entry screen and its lower energy price ($48.70 vs $54.02 lw) worsens VRE entry
economics. Routed §7 item 2, measured.

**Leakage cuts the same way**: the import line **falls** in every year (−0.53 to −0.94 Mt) as
unpriced domestic gas undercuts imports (import generation 28.42 → 20.49 TWh in 2026), so the 2026
leakage-inclusive total goes 20.37 → 24.26 Mt — a larger gap than `emissions_mt` alone shows.

### 2.5 The combined legs — ruling S11, both nettings, and they disagree

`CES-P20+VOL-HI` carries a premium (a screen price, no row), so its only row is the voluntary one;
its dual is 7.0 / 7.0 / 7.0 / −0.0 / −0.0, identical to standalone `VOL-HI`. **P-15 confirmed to
four decimals**: pure `CES-P20` 2030 CO2 is 2.8713 Mt and `CES-P20+VOL-HI` is 2.8711 — the
voluntary row adds 0.0002 Mt on top of the same premium.

`ALL-CLEAN` is the one arm where both rows are live at once, and **G4 and G7 pass simultaneously**:
`clean_region_duals` = [50.0, 7.0] exactly in 2026–2028, [−0.0, −0.0] in 2029, [4.2051, −0.0] in
2030. Each row escapes at its own price and goes slack on its own schedule; neither contaminates
the other's dual. **G9, both nettings side by side (TWh):**

| year | obligation `target×D` | federal credited | **counts-toward** (headline) | **additional** | implied extra escape | at the $50 ACP |
|---|---|---|---|---|---|---|
| 2026 | 58.544 | 40.372 | −18.172 | −26.687 | 26.687 | $1,334M |
| 2027 | 62.275 | 40.372 | −21.903 | −30.526 | 30.526 | $1,526M |
| 2028 | 66.092 | 61.904 | −4.188 | −12.919 | 12.919 | $646M |
| 2029 | 69.994 | 79.641 | **+9.646** | **+0.805** | 0.000 | — |
| 2030 | 73.985 | 81.324 | **+7.338** | **−1.614** | 1.614 | $81M |

**In 2030 the two nettings give OPPOSITE verdicts** — counts-toward clears the standard by
7.338 TWh while additional falls 1.614 TWh short. D-6 is not a formality on this ISO. **P-16 HIT**
(predicted a 12–15 % wedge; measured 12.1–14.5 %).

---

## 3. Gate verdicts G1–G12

| gate | verdict | evidence |
|---|---|---|
| **G1** resolved-input premise reproduces at THE PIN | **PASS, pre-solve** | The carbon table reproduced the RGGI trajectory 26.0545 → 34.1521 $/t; volumes came from the runner's own demand chain; REF and LOAD-HI keys reproduced exactly (`8878d29743555b45`, `0d5c394b6c4e5cb6`). |
| **G1a** 2026 bit-identical to REF | **SPLIT, reported not smoothed** | EXACT in the three premium-only arms (`CES-P10/P20/P30`) and in `CES-P20+VOL-HI`. Off by **+0.0004 Mt / −0.004 $/MWh** in the four row-bearing arms (`VOL-MID`, `VOL-HI`, `CES-T80`, `ALL-CLEAN`); every other 2026 scalar exact, `import_co2_mt_reported` included. Cause identified and then isolated by controlled comparison — §5, P-1. |
| **G2** REF-side precondition | **PASS** | REF 14/14 invariants PASS, `unserved_mwh` 0.0 in all five years, reserve margin +0.1681 → +0.0840 all in-band, `hours_ge_500` 0, curtailment 0.0000. **NEISO's price side IS campaign-grade**, unlike ERCOT's. The one standing data note: the NEISO zonal load file for weather-year 2024 is absent, so the demand chain falls back to the ISO-total shape — identical in REF and every arm, so every delta is protected. |
| **G3** footprint confinement | **PASS, all nine arms** | Eligible generation pinned at its CF ceiling in every arm-year (6.9162 / 6.9162 / 6.9162 / 10.1517 / 12.0494 TWh); nuclear and hydro flat; curtailment 0.0000 everywhere; movement confined to thermal and import rows, plus the retrofit ledger. |
| **G4** `CES-T80` dual identity | **PASS, both limbs** | `FEDERAL_CES` = **50.0000 exactly** (the ACP to the digit) in 2026/2027/2028 where the target is unmet; **−0.0** in 2029 where REF's own credited share clears it; **strictly interior 4.2912** in 2030. Both limbs exercised by one arm; `ALL-CLEAN` reproduces it. |
| **G5** no non-target invariant flips | **PASS** | 14/14 PASS in all nine arms against REF's 14/14. No arm killed. |
| **G6** no unserved where REF has none | **PASS** | `unserved_mwh` = 0.0 in every arm-year. Declared not to bind on `ALL-CLEAN`, which raises load by construction. |
| **G7** voluntary dual bounded, per arm | **PASS** | $4.50 exactly on `VOL-MID`; $7.00 exactly on `VOL-HI`, `CES-P20+VOL-HI` and `ALL-CLEAN`; **−0.0 exactly** in every slack year. Escape MWh = the deficit exactly (2026: 1.5127 TWh). |
| **G8** curtailment before thermal | **VACUOUS, and reported as such** | REF's eligible curtailment is **0.0000 TWh by construction** — wind + solar run at exactly their unconstrained CF ceiling (6.9162 TWh, derived zero-LP and confirmed by the committed report at ≤1.9e-9). There is no dumped MWh for a REC buyer to buy first. Measured Δcurtailment = 0.0000 in every arm. **This gate cannot kill an arm on NEISO and the campaign's cross-ISO G8 row must not read NEISO as a pass it never earned.** |
| **G9** both nettings | **PASS, and they disagree** | §2.5. Counts-toward as headline, additional beside it, CES dual under each. The 2030 verdicts are opposite. |
| **G10** cap row identity | **PASS, all five years** | Emissions = budget to 3.2e-13 relative or better; `co2_cap_price` > 0 and `n_co2_caps_binding` = 1 in every year. No slack year exists to test the dual-is-zero limb. |
| **G11** one instrument at a time | **PASS, pre-solve and re-confirmed** | `cap_spec` set with `price_adder` `None`; `resolve_carbon_price` = 0.0000 in every year; `carbon_price_path: zero` so no federal price composes on top. |
| **G12** price vs quantity, side by side | **PASS, reported with its asymmetry** | §2.4's table. The dual is below the adder in all five years while permitting more emissions; the asymmetry (adder → dispatch **and** screen; dual → dispatch only) was declared before the solve and is now measured in the deployment. |

**No gate killed an arm.** A gate may kill an arm and may never promote one; none did either.

---

## 4. The deployment response — the campaign's first policy-side reading for NEISO

| | REF | every non-cap arm | `CAP-STATE-TIGHT` |
|---|---|---|---|
| `vre_mw` 2026–2030 | 4100 / 4100 / 4100 / 5902 / 7100 | **identical, all eight arms** | 4100 / 4100 / 4100 / 5902 / **6189.4** |
| `builds_renew_mw` 2029 / 2030 | 1802.0 / 1198.0 | **identical, all eight** | 1802.0 / **287.4** |
| `retire_mw` 2027 | 2758.3 | identical (2244.9 on `ALL-CLEAN`, a LOAD-HI effect) | 2758.3 |
| `gas_cc_ccs` TWh 2030 | 25.9318 | 25.93 → **62.57** across the arms | **0.9326** |

Two readings, and they point the same way:

1. **Entry does not respond to any policy instrument on this ISO** — §0 item 1. Whatever the
   campaign is measuring on NEISO's clean-attribute axes, it is not deployment.
2. **The only instrument that moves capacity moves it DOWNWARD.** The mass cap ends 2030 with
   910.6 MW less VRE than REF. A quantity instrument that binds on dispatch while its price signal
   never reaches the investment screen produces exactly this: emissions capped, investment
   suppressed. That is routed §7 item 2 in measured form, and it is the campaign's first
   policy-side deployment result for NEISO.

The retrofit fleet is where every non-cap arm's response lands: `gas_cc_ccs` 2030 generation runs
25.93 (REF) → 46.83 (P10) → 57.06 (P20) → 62.57 (P30) TWh, and 35.12 on `CES-T80`. Under the cap
arm it very nearly vanishes (0.93 TWh) because the retrofit screen sees carbon 0.

---

## 5. Predictions, scored at full magnitude

**The PRECOMMIT's, written before any leg.** Five missed. A miss is the finding, not something to
explain away, and each is reported with what it cost me to be wrong.

| # | prediction | verdict | measured |
|---|---|---|---|
| **P-1** | every surviving arm's 2026 is **bit-identical** to REF | **SPLIT → effectively a MISS** | EXACT in the four arms that build no LP row; off by **+0.0004 Mt / −0.004 $/MWh** in the four that do. My §6.1 argument — that the escape column "couples to nothing" — was wrong: the row and its escape column are built in **every** year, slack ones included, so their presence perturbs the simplex path in a fleet whose `gas_cc` / `gas_cc_ccs` classes are near-degenerate after capx D65-B moved the capture VOM adder 8.0 → 2.95. **`CES-P10` supplied the controlled comparison the earlier legs could not**: no row, no residual. The same mechanism dominates `VOL-MID`'s 2030 delta — 259 GWh reshuffles `gas_cc` → `gas_cc_ccs` at identical capacity and identical builds, worth −0.0841 Mt in a year the row does not bind — so **a NEISO voluntary arm's 2030 CO2 delta is degeneracy, not instrument, and is not quotable as a response.** |
| **P-2** | escape MWh = the deficit exactly; dual = the ceiling exactly | **HIT** | 2026 escape 1.5127 TWh = 8.4289 − 6.9162 exactly; duals $4.50 and $7.00 exactly, −0.0 when slack. |
| **P-3** | `CAP-STATE-TIGHT` carries **0.0** `gas_cc_ccs` in every year | **MISS** | 0.0 in 2026–2028 but **2.7788 TWh in 2029 and 0.9326 in 2030** against REF's 36.28 and 25.93. The repaired retrofit screen at carbon 0 very nearly closes — 7.7 % of REF's 2029 CCS energy survives — but does **not** close entirely, as capx D50's asymmetry would have it. My §4.3 second argument was directionally right and absolutely wrong. |
| **P-6** | `VOL-HI` builds **strictly more** than `VOL-MID` in at least one year | **MISS** | Identical in all five. The two arms differ in **nothing** except the dual. Cause: the $50 RPS escape (§0 item 1). |
| **P-7** | \|ΔCO2\| < 1.0 Mt and \|Δlw_price\| < $1.50 on the voluntary arms | **HIT on the numbers, wrong reason** | Max 0.084 Mt and 0.008 $/MWh — but because the arms do nothing, not because the instrument is small. Stated rather than absorbed. |
| **P-8** | `CES-P20` ≈ `CES-P30` within 1 %; `CES-P10` separates; cause = queue saturation | **SPLIT, mechanism FALSIFIED** | "P10 separates" HIT (7.2 % on 2030 CO2). "P20 ≈ P30 within 1 %" holds 2026–2029 (0.03–0.42 %) and **FAILS in 2030** (clean share 5.11 %, CO2 2.36 %). The **reason is falsified outright**: `vre_mw` is identical in REF, P10, P20 and P30 in every year, so there is **no entry to saturate**. A retrofit response has no queue budget to exhaust, which is why the ladder keeps scaling. |
| **P-10** | `CES-T80` escapes 2026/2027, met 2029; 2028 and 2030 either way | **HIT on both discriminating years** | Escape at the ACP in 2026–2028, met in 2029, interior 4.2912 in 2030 — both inside the declared band. |
| **P-11** | `CES-T80` exhausts the 4 GW/yr queue from 2027; offshore wind enters | **MISS** | Zero incremental entry, no offshore wind, `binding_cap` never reached. |
| **P-12** | `CAP-STATE-TIGHT` 2030 CO2 in 16–20 Mt | **HIT** | 18.000 Mt (pinned by the cap). |
| **P-13** | the cap row is **slack** 2026–2027, binds 2029–2030 | **MISS** | Binds in **all five**. The §4.3 argument was right — REF's emissions are not the comparator, because the case removes the price that produced them — and P-13 then anchored on REF's priced 15.83 Mt anyway. My error, in the prediction, not the argument. **Flagged in the PRECOMMIT as "the least certain prediction in the document", which it was.** |
| **P-15** | the voluntary dual is irrelevant to deployment on `CES-P20+VOL-HI` | **HIT, to four decimals** | Pure `CES-P20` 2030 = 2.8713 Mt; `CES-P20+VOL-HI` = 2.8711. |
| **P-16** | the two nettings differ by 12–15 % of the standard | **HIT** | 12.1–14.5 %. |

**ADDENDUM 1's, written after two legs and before the other seven — both HIT.** (a) Zero entry
difference across `CES-P10/P20/P30`: measured identical in all three, in every year. (b) Any
response arriving through the retirement and CCS-retrofit screens instead: measured, `gas_cc_ccs`
25.93 → 62.57 TWh across the ladder with capacity untouched. It also correctly predicted **its own
parent's P-11 would miss**, which is the discipline working rather than a lucky call — it was
pushed as a commit before `CES-T80` was solved.

**What I got wrong has a pattern.** Four of the five misses (P-1, P-6, P-8, P-11) share one root:
I reasoned about each instrument's *own* mechanism and never asked what else was already in the
`max()` the screens read. The $50 RPS escape was measurable at zero LP cost before the first solve
— it is in REF's own trajectory as `rps_dual` — and I did not look. ADDENDUM 1 exists because
leg 2 forced the question; it should have been phase 0's.

---

## 6. Cost — wall and peak RSS per solve-year (the D-5 cost table's input)

| leg | wall (min) | min / solve-year | peak RSS (GB) | LP rows added |
|---|---|---|---|---|
| `CES-P20` | 5.2 | 1.05 | 3.55 | **none** — a premium is a screen price |
| `CES-P30` | 5.5 | 1.09 | 3.39 | none |
| `CES-P10` | 5.5 | 1.11 | 3.65 | none |
| `CES-P20+VOL-HI` | 5.7 | 1.15 | 3.63 | voluntary (escaping) |
| `VOL-HI` | 7.4 | 1.48 | 3.64 | voluntary (escaping) |
| `VOL-MID` | 7.8 | 1.57 | 3.69 | voluntary (escaping) |
| `CES-T80` | 13.5 | 2.70 | 3.44 | federal CES target (escaping, then interior) |
| `ALL-CLEAN` | 15.4 | 3.09 | 3.56 | federal CES target + voluntary |
| **`CAP-STATE-TIGHT`** | **72.9** | **14.57** | 2.90 | **mass cap, BINDING in all five years** |
| **lane total** | **139.0** | **3.09 avg** | 3.69 max | 45 solve-years |

**A BINDING annual mass-cap row is an order of magnitude more expensive than an ESCAPING
clean-tier row** — 14.57 min/solve-year against 1.05–3.09 for every other arm, at 100 % CPU
throughout and with *lower* peak RSS, so it is solver iterations rather than memory. One of nine
legs is **57 % of the lane's LP**. The campaign budget assumed ~1.1 min/solve-year (the load lane's
own NEISO measurement), which is right for six arms and wrong by 13× for the seventh.

Two second-order readings worth carrying to the D-5 table:

- **Cost tracks whether the row BINDS, not whether it exists.** The voluntary arms carry a row and
  run at REF-like speed because it escapes — the escape column is one cheap slack. `CES-T80` and
  `ALL-CLEAN` sit in between (2.70–3.09) because their target row goes interior. Only the mass cap
  is tight against real dispatch in every hour.
- **A premium is free.** The three premium arms are the fastest in the lane, faster than the
  campaign's own REF measurement, because they add no row at all.

**A campaign running `CAP-STATE-TIGHT` on all three program ISOs should budget it separately**
rather than at the per-ISO average — the row binds on NYISO and CAISO too (SCN-CAP §3), so the
same multiple should be expected there.

**One scheduling note, for the record and not for the model.** This lane's chain was interrupted
twice by session-level events: a monitor timeout killed a foreground chain (30 min of cap-arm
progress), and a later idle gap cut `CES-P10` mid-solve. Both recovered at **zero LP cost**,
because `run_ces_leg.py` resumes from `results/<ISO>/<key>/year_<Y>.parquet`. A long leg should be
launched **detached** (`setsid nohup`) with a progress file tailed separately, never owned by the
watcher — and a branch checkout mid-chain will (correctly) trip the HEAD guard on the next leg.

## 7. Routed to SCN-DESK — measured here, not executed

1. **THE CHARTER'S CASE-13 KILL TEST IS UNSOUND ON ANY PROGRAM ISO, AND `FINDING-scn-cap-2026-09-06.md`
   §3'S NEISO VERDICT WITH IT.** Both say a slack budget makes `CAP-STATE-TIGHT` byte-identical to
   REF and order it killed without a solve. On a program ISO it never can be: the row **replaces**
   the adder (the resolver's one-source invariant — and the charter's own gate **G11** states it),
   so NEISO's resolved carbon price is $0.00/t under the case against REF's $26.05–34.15/t. §2
   shows what the kill would have suppressed: the row binds from 2026 and the case is a **policy
   loosening of +2.9 to +4.8 Mt**, which the naive test would have published as "no difference from
   REF". The correct form of the rule is *"byte-identical only where `resolve_carbon_program`
   returns `None` — i.e. on a NON-program ISO (ERCOT, MISO)"*, which is exactly the identity the
   ERCOT lane proved for itself and is where the rule is sound. **NYISO's and CAISO's verdicts do
   not change** (their rows bind, so they solve either way), but their lanes' phase-0 reasoning
   should be re-cut on the same correction, and SCN-CAP §3's sentence *"the post-fix REF cannot
   change this verdict"* is true of the **binding** question and false of the **identity** question
   it is attached to.
2. **The mass-cap row's dual reaches NO capacity screen** — a structural asymmetry inside the one
   case the campaign runs as a quantity instrument, and it must not be discovered inside a result
   table. `evolve_fleet` is handed `carbon_price=resolve_carbon_price(config, driver_year)`
   (`runner.py:2322`), which is **0.0** under the case, and `co2_cap_price` has no consumer outside
   `results/export.py` / `results/outputs.py`. So the campaign's PRICE instruments price dispatch
   **and** investment while its one QUANTITY instrument prices dispatch only, and a
   price-vs-quantity comparison across the two is not like-for-like. Measured consequence on NEISO:
   the cap arm carries **no CCS retrofit at all** while REF carries 22.6–36.3 TWh of it, because
   the retrofit screen sees carbon 0 (capx D50 / owner Q42's asymmetry). Not repaired here —
   outside this lane's regions, and a real design question for cards D-1 / D-2.
3. **The charter's "25–41 %" import-line figure for NYISO/NEISO is the PRE-D77 reading.** On the
   post-D77 NEISO REF the line is **26–92 %** of the in-ISO level, peaking in 2029 where the
   retrofit fleet takes in-ISO CO2 to 4.757 Mt against an unchanged 4.370 Mt of import-attributed
   CO2. The denominator collapsed; the numerator did not. The duty is unchanged; the number in the
   charter should move with the pin.
4. **`VOL-MID` is LIVE on NEISO and carries the IDENTICAL volume to `VOL-HI`** — the mirror of the
   ERCOT lane's §9 item 4, and a better instrument than either lane's charter anticipated. Because
   `E_DC` is exactly zero, the mid/high pair on this ISO is a **pure WTP-ceiling ladder with no
   volume confound**. What it measured is that the ladder is **inert on deployment at any level**
   (§2), for the reason in item 5. If the desk wants one ISO to carry card **D-2(b)**'s ceiling
   evidence, NEISO is the ISO — but the answer it gives is "the ceiling cannot be discriminated
   here", not a level.
5. **NEISO's $50/MWh RPS escape masks the entire policy axis on the ENTRY screen**, and no campaign
   case sets or varies it. `rps_dual = 50.0` in 5 of 5 years in every arm; the entry screen folds
   `attr = max(effective_eac_price_for_tech, rps_credit_for_zone(rps_shadow_price, zi),
   clean_credit)` (`new_entry.py:1132-1143`) with that RPS leg applied to **every** candidate tech,
   no fuel gate. Every level this campaign carries — the $4.50 and $7.00 WTP ceilings, the $10 /
   $20 / $30 CES premiums, and `CES-T80`'s $50 ACP — sits at or under it. This is rule 19
   `[R-ONE-MECH]`'s attribute doctrine working as designed and nothing here proposes changing it;
   what it means is that **NEISO cannot discriminate any of those levels by deployment**, which is
   a fact about what this ISO can be used to measure. Pre-registered in ADDENDUM 1 before the
   deciding legs ran. Whether a $50 escape in every forecast year is the right NEISO posture is
   **not** this lane's question and is asserted neither way.
6. **A slim-artifact gap the campaign got away with only by luck.** A registered leg's committed
   evidence is `full_horizon_summary.json` + `run_config.json`, and **neither carries
   `import_co2_mt_reported`, `clean_share`, `curtailment_twh` or `unserved_mwh`** — the WS-0
   leakage duty's own numbers. They were recoverable for NEISO only because SCN-WS5A-RESOLVE
   happened to regenerate the delta-report CSVs at its leg 2 (`931866cc`). A lane whose REF cache
   lives in another container and whose report CSVs were not refreshed **cannot discharge the duty
   at all**. One line in the campaign's registration recipe fixes it: the delta-report CSVs are
   part of a leg's committed evidence, not an optional extra.

---

## 8. Files

**Written by this lane, all inside its declared regions:**

| file | what |
|---|---|
| `docs/handoffs/PRECOMMIT-scn-ws5a-policy-neiso-2026-09-06.md` | phase 0 at THE PIN, pushed before the first solve |
| `docs/handoffs/PRECOMMIT-scn-ws5a-policy-neiso-2026-09-06-ADDENDUM-1.md` | the $50 RPS escape, pushed after 2 legs and before the other 7 |
| this document | — |
| `results/scn-campaign-policy-2026-09-06/NEISO/<CASE>/{full_horizon_summary,run_config}.json` | 9 legs, slim by construction (`redirect_cache=False`) |
| `frontend/data/hindcast/neiso-2026-2030-scn-campaign-policy-2026-09-06-<slug>.json` | 9 registry sidecars, forecast namespace only |

**Consumed, never edited:** `configs/scenario_campaign_matrix.yaml`, the NEISO base YAML,
everything under `src/`, `scripts/run_ces_leg.py`, `scripts/register_forecast_run.py`,
`scripts/report_scenario_deltas.py`, and every committed bundle, sidecar and report CSV of the load
and resolve lanes.

**Untouched:** `program-status.json`, `ff-verdicts.json`, the whole **backcast** namespace, every
other ISO's files and every other lane's files. `data/clean/confirmed-retirements` was regenerated
locally (derived, gitignored, never committed).

## 9. Duties

- **No default moved, no knob moved, no `ScenarioConfig` field added.** DOF ledger: **zero** free
  parameters. No `authorized_price_tuning` — that is a backcast offer-curve channel and this is a
  forecast lane.
- **Rule 15 / plan §7.5:** every leg registered into the **forecast** namespace under campaign
  `scn-campaign-policy-2026-09-06`, one run id per (ISO, case). The backcast registry is never
  touched. **This lane produces no keeper and no keeper candidate** — a keeper is a backcast
  artifact and a scenario-campaign arm cannot be one.
- **The Y-24 ratchet:** all nine legs are 14/14 invariants PASS, so this lane adds **no** line to
  `frontend/data/hindcast/invariant-failures.json` and leaves the audit exactly as it found it.
- **Rule 22 / R-AZ:** every solve year is 2026–2030, forecast mode, inside the §2.1b five-year
  window. No holdout tier is touched, at launch or at registration.
- **Rule 29(b):** form 4 valid — the committed post-D77 REF **is** the control, and no control
  solve was earned or spent. **Rule 29(c):** no screen bundle and no control bundle exists.
- **Rule 27:** no source file ≥300 lines was rewritten; every push was fetch-back verified.
- **Backcast byte-identity:** untouched by construction (`mode="forecast"` on every leg).
