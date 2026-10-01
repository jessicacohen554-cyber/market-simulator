# FINDING — SCN-WS5A-POLICY-NEISO: NEISO's policy axis reaches its deployment screen at $60 and nowhere below it — and the mask was never what held VRE back

**Lane** SCN-WS5A-POLICY-NEISO · **Model** Opus (`claude-opus-5`, rule 27 `[R-PUSH]`) ·
**Date** 2026-09-07 (amended the same day — see the AMENDED note below) · **Branches**
`claude/scn-ws5a-policy-neiso-bhlkdp` (legs 1–9) and `claude/scn-ws5a-ces-p60-cap-fold-wu1rh7`
(the S15 bracket and the S17 fold) · **Data profile** `neiso` ·
**Campaign** `scn-campaign-policy-2026-09-06`, kind `scenario`, `reference_case: REF` ·
**THE PIN** `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b` · **Charter** SCN-DESK ledger §5 policy
charter **v6** (r#17) + the **S15** bracketing addendum (r#18) · **Predecessors**
`PRECOMMIT-scn-ws5a-policy-neiso-2026-09-06.md` and its **ADDENDUM 1** and **ADDENDUM 2**, all
three pushed before the legs they predict.

**10 legs solved, 50 solve-years, 147.4 min of LP. 4 of 13 chartered cases killed at phase 0 on a
proven identity; 1 kill refused on a proven NON-identity and since routed to Stage B by owner
ruling S17 (§8); 1 bracketing leg added by owner ruling S15 (§2.6). Nine legs are 14/14 invariants
PASS; `CES-P60` carries one FAIL (I9, 2030 only), declared in `invariant-failures.json` in the same
commit as its registration and diagnosed in §2.6.4.**

**AMENDED 2026-09-07, same session, on two owner rulings.** **S15** added the `CES-P60` bracketing
leg — §2.6, its gates G-B1..G-B3 in §3, its predictions in §5, and a mechanism CORRECTION to
ADDENDUM 1 that this document repeated and now withdraws (§2.6.1). **S17** removed
`CAP-STATE-TIGHT` from **Stage A** and routed it to **Stage B**; the case was solved, measured and
is NOT killed — its analysis moves intact to §8, `STAGE-B SEED`, and out of the Stage-A headline,
the §2 delta table and the plan's §5.1 rows. Its registered leg stays registered.

---

## 0. Bottom line

1. **NO CHARTERED POLICY LEVEL MOVES NEISO'S DEPLOYMENT SCREEN, AND THE $60 BRACKET SAYS WHY IT
   IS NOT A MASK.** `vre_mw` is **4100 / 4100 / 4100 / 5902 / 7100 MW in REF and in every one of
   the eight non-cap arms, in every year** — the CES premium at $10, $20 and $30, the CES target
   row at its $50 ACP, and both voluntary ceilings all produce **exactly zero** incremental entry.
   NEISO's state RPS row escapes at its own **$50/MWh ACP in 5 of 5 years in every arm**, and the
   two entry-screen folds `attr = max(effective_eac_price_for_tech, rps_credit_for_zone(...),
   clean_credit)` (`new_entry.py:1190-1197` and `:1474-1483`) apply that RPS leg to **`wind` and
   `solar`** — `_RENEWABLE_NEW_FUELS`, `:121` — so every campaign level at or under $50 is invisible
   **to a VRE candidate**. **It was never invisible to the other eight eligible techs**, whose RPS
   leg is 0.0 and whose legacy EAC is $0.00, so the premium was their sole and fully visible
   attribute price from $10 up (§2.6.1 — this CORRECTS ADDENDUM 1 §2, which said the fold has no
   fuel gate at all, and every place this document repeated it). **Pre-registered in ADDENDUM 1
   before the deciding legs ran** (§5).
2. **THE BRACKET FALSIFIES "THE CES ROW IS NOT WIRED TO ENTRY", AND THE TECH THAT MOVES IS THE ONE
   THAT WAS NEVER MASKED.** At $60 the economic entry screen builds **500.0 MW of NUCLEAR in 2029**
   — `builds_by_source {'economic': 500.0}`, `nuclear` capacity 3355.4 → 3855.4 MW, exactly the
   `QUEUE_CAP_PER_TECH_GW["NEISO"]["nuclear"]` 0.5 GW/yr cap — which **no other arm in this lane
   carries**. That is the campaign's first economic entry of any kind on NEISO and a measured
   threshold between $30 and $60. **And `vre_mw` is STILL identical to REF in every year**, at the
   first level where a NEISO wind or solar candidate sees any uplift at all (attr 50.000 → 60.000).
   The mask was real and it was not the binding constraint (§2.6).
3. **`CAP-STATE-TIGHT` was solved, measured, and ROUTED TO STAGE B by owner ruling S17 — not
   killed.** The case the charter and `FINDING-scn-cap` §3 both ordered killed as "byte-identical
   to REF" binds in ALL FIVE years and is a policy **LOOSENING** of +2.9 to +13.9 Mt. Refusing that
   kill was the single highest-value decision in the lane, and the desk recorded it as such
   (r#19, card D-13). On that evidence the owner moved the case **out of Stage A** to be re-asked
   at full horizon where its 2050 glide has room to bite; ruling S12's level is **not** withdrawn
   and the registered leg **stays registered**. The whole analysis is carried intact in **§8,
   `STAGE-B SEED`**, and is excluded from the Stage-A headline and the plan §5.1 rows.
4. **The CES ladder's monotonicity REVERSES on the leakage line, and it does so on a THIRD rung.**
   $20 → $30 at 2030 makes in-ISO `emissions_mt` worse (2.8713 → 2.9392 Mt) and the
   leakage-inclusive total better (6.102 → 5.225 Mt); **$30 → $60 repeats it** (2.9392 → 3.0664 Mt
   in-ISO, 5.225 → 4.300 Mt inclusive) as imports collapse 10.2158 → 1.1113 TWh. This is the
   strongest case the campaign has produced for the WS-0 duty (§2.3, §2.6.3).
5. **A binding mass-cap row costs 14.6 min/solve-year against 1.05–3.09 for every other arm** —
   49 % of the lane's total LP on one of ten legs (§6). It is a Stage-B-seed cost, reported here
   because the D-5 cost table is a lane deliverable and does not move with the case's stage.
6. **Six of my own pre-registered predictions MISSED and are reported at full magnitude** —
   P-1, P-3, P-6, P-11, P-13 and **P-B1**, plus P-8 as a SPLIT whose stated mechanism was falsified
   outright (§5). The two ADDENDUM 1 predictions, written after two legs and before seven, both
   HIT; of ADDENDUM 2's four, two HIT, one SPLIT and P-B1 MISSED.

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

### 1.2 The kill that was REFUSED — and the case is now a STAGE-B SEED

The fifth chartered case, `CAP-STATE-TIGHT`, was the one kill this lane refused, and the refusal
was correct: the case binds in all five years and is a policy loosening. On that evidence owner
ruling **S17** (SCN-DESK r#19, card D-13) moved it **out of Stage A** and routed it to Stage B.
**The refusal's full reasoning and every number the case produced are carried intact in §8,
`STAGE-B SEED`** — nothing here is withdrawn, retracted or re-scored, and its registered leg stays
registered. Stage A therefore carries a clean price-only policy axis: carbon path, CES premium,
CES target, voluntary.

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
| **CES-P60** | 2026 | 15.8314 | -0.0005 | 4.536035 | 0.3485 | 51.887 | 51.20 | 0.0000 | 0.0 | None rps 50.0 | 0.0 | 0.0 |
| **CES-P60** | 2027 | 17.0942 | -0.0018 | 4.376392 | 0.3458 | 51.397 | 50.49 | 0.0000 | 0.0 | None rps 50.0 | 0.0 | 2758.324170000001 |
| **CES-P60** | 2028 | 9.8018 | -0.0704 | 4.474680 | 0.5294 | 52.456 | 51.37 | 0.0000 | 0.0 | None rps 50.0 | 0.0 | 0.0 |
| **CES-P60** | 2029 | 3.5733 | -1.1833 | 3.379829 | 0.7693 | 44.837 | 43.35 | 0.0000 | 0.0 | None rps 50.0 | 1802.0 | 1.638 |
| **CES-P60** | 2030 | 3.0664 | -3.0394 | 1.233828 | 0.9542 | 29.280 | 27.32 | 0.0000 | 0.0 | None rps 50.0 | 1198.0 | 0.0 |
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

### 2.2 The CES premium ladder — large, retrofit-driven, non-saturating, and VRE-blind at every rung

| 2030 | REF | CES-P10 | CES-P20 | CES-P30 | **CES-P60** |
|---|---|---|---|---|---|
| `emissions_mt` | 6.1058 | 3.0942 | **2.8713** | 2.9392 | 3.0664 |
| `import_co2_mt_reported` | 4.7657 | 3.8680 | 3.2304 | 2.2859 | **1.2338** |
| leakage-inclusive total | 10.8715 | 6.9622 | 6.1017 | 5.2251 | **4.3002** |
| `clean_share` | 0.5877 | 0.7538 | 0.8341 | 0.8767 | **0.9542** |
| `gas_cc_ccs` TWh | 25.9318 | 46.8343 | 57.0604 | 62.5748 | **68.5551** |
| `import` TWh | 29.1419 | 21.7004 | 14.8450 | 10.2158 | **1.1113** |
| `lw_price` $/MWh | 54.022 | 47.708 | 42.238 | 37.448 | **29.280** |
| `vre_mw` | 7100.0 | 7100.0 | 7100.0 | 7100.0 | **7100.0** |
| `nuclear` MW | 3355.4 | 3355.4 | 3355.4 | 3355.4 | **3855.4** |

The response is **large** (−50 % on in-ISO CO2 by 2030, −60 % on the leakage-inclusive total) and
**dispatch and retrofit at every rung of the committed ladder** — `vre_mw` and `builds_renew_mw` are
identical to REF in $10, $20, $30 **and $60**. This is the shape SCN-WS2b measured on NEISO in July
("adds ZERO economic entry … the whole response is dispatch"), and the bracket now separates the
two mechanisms that could produce it.

**The premium reaches the ISO through THREE consumers, and naming them precisely matters because
this document's earlier text named only two.** (i) **Dispatch, directly** — `apply_eac_to_mc`
(`runner.py:2824`) subtracts the effective per-unit EAC from `mc` for every credited fleet fuel, so
at $30 a `gas_cc_ccs` unit bids **28.5 $/MWh below** its unabated twin. *That*, not a screen, is
what puts 62.57 TWh of CCS into the 2030 stack; a premium builds no LP **row**, which is not the
same as leaving the **objective** alone, and §6's "a premium is free" is a statement about rows
only. (ii) The **retirement** screen, whose RPS leg **is** fuel-gated to `{wind, solar}`
(`retirements.py:3509-3516`) and therefore does not mask a credit paid to `gas_cc_ccs` at its 0.95
crediting. (iii) The **CCS-retrofit** screen (`ccs.py:475-476`), which values a retrofit as the
attribute uplift over the best unabated state. On the **entry** screen the premium is masked for a
VRE candidate by the $50 escape at every rung up to $50 — but **not** for the other eight eligible
techs — and at $60 that screen does respond, with nuclear (§2.6). At $60 the retrofit screen is pinned at its **3 GW/yr cap** (`gas_cc_ccs` capacity
3000.0 / 5998.5 / 8998.3 MW in 2028–2030, against $30's 2998.5 / 5997.9 / 8995.3), so the ladder's
retrofit leg is now cap-bound rather than economics-bound and cannot scale further inside this
window.

### 2.3 THE LEAKAGE REVERSAL — the campaign's best argument for the WS-0 duty

Read the table above along the bottom two rows. From $20 to $30, **in-ISO `emissions_mt` gets
worse** (+2.36 %) while **the leakage-inclusive total gets better** (−14.4 %). The extra $10/MWh
pulls a further 5.5 TWh of `gas_cc_ccs` into the domestic stack, which displaces imports whose CO2
is reported beside `emissions_mt` and never inside it. **A reader given `emissions_mt` alone would
conclude that a higher CES premium raises NEISO's emissions.** That conclusion is an artefact of
the accounting boundary, and G-E3's reported-only import line is the only thing that makes it
visible. No other arm in this campaign has produced a sign reversal on the scored basis.

**The $60 bracket repeats it on a THIRD rung, which is what turns one observation into a pattern.**
$30 → $60 makes in-ISO `emissions_mt` worse again (2.9392 → **3.0664 Mt**, +4.33 %) while the
leakage-inclusive total falls again (5.2251 → **4.3002 Mt**, −17.7 %), as `gas_cc_ccs` takes another
5.98 TWh and imports collapse 10.2158 → **1.1113 TWh**. Read on `emissions_mt` alone, NEISO's CES
premium ladder is **non-monotone above $10 and worst at the top**; read with the import line beside
it, the ladder is **strictly monotone at every rung** — 10.8715 → 6.9622 → 6.1017 → 5.2251 →
4.3002 Mt. The two readings give opposite policy advice from the same five solves, and only one of
them is defensible.

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

### 2.6 THE $60 BRACKET (owner ruling S15) — the CES row DOES reach entry, and the mask was not what held VRE back

`CES-P60` is the S15 bracketing leg: the committed `CES-P30` case with
`federal_ces_premium_usd_per_mwh` set to **60.0** and nothing else, at THE PIN, key
**`a37868175d5ae724`** — the value ADDENDUM 2 pre-registered before the solve. $60 is ONE common
level for every ISO, set above the footprint's highest published ACP ($50) from the published ACP
table and never from a residual (rules 1 `[R-STRUCT]` / 25 `[R-ISO-SCOPE]`). It exists to
distinguish two readings of this lane's null that the committed ladder cannot separate:
*correctly masked* versus *the CES row never reaches entry at all*.

**It separates them, and the answer is the first.**

#### 2.6.1 CORRECTION — the entry fold's RPS leg IS fuel-gated, and the mask is narrower than I said

ADDENDUM 1 §2 wrote that the entry fold applies the RPS leg "to every candidate technology with no
fuel gate at all", and §0, §2.2 and §7 item 5 of this document repeated it. Computing G-B1 forced
me to read the lines rather than the paragraph, and **it is wrong**:

- `new_entry.py:1133-1143` — the fold the S15 ruling and my own ADDENDUM cite — is inside
  `_choose_vre_zone::_zone_revenue`, a **VRE-only siting helper**. Its RPS leg carries no fuel test
  because its caller has already restricted the tech to VRE. The absence of a gate there is
  **vacuous**, not general.
- The two folds that actually decide entry, `new_entry.py:1190-1197` and `:1474-1483`, each compute
  `rps_for_tech = rps_credit_for_zone(...) if tech in _RENEWABLE_NEW_FUELS else 0.0`, and
  `_RENEWABLE_NEW_FUELS = frozenset({"wind", "solar"})` (`:121`).

So NEISO's $50 escape masks **wind and solar candidates and nothing else**. For `offshore_wind`,
`nuclear`, `geothermal`, `hydro`, `gas_cc_ccs`, `hydrogen_ct`, `hydrogen_ccgt` and `nuclear_smr`
the RPS leg is 0.0, NEISO's legacy exogenous EAC is **$0.00/MWh** for every candidate tech, and the
federal premium was therefore their **sole and fully visible** attribute price from `CES-P10`
upward. Measured at the pin, zero LP (ADDENDUM 2 §3):

| candidate | RPS leg? | credit | `attr` REF | `attr` P10 | `attr` P30 | **`attr` P60** |
|---|---|---|---|---|---|---|
| `wind` / `solar` | yes | 1.00 | 50.000 | 50.000 | 50.000 | **60.000** |
| `offshore_wind` / `nuclear` / `geothermal` / `hydro` / `hydrogen_*` / `nuclear_smr` | no | 1.00 | 0.000 | 10.000 | 30.000 | **60.000** |
| `gas_cc_ccs` | no | 0.95 | 0.000 | 9.500 | 28.500 | **57.000** |

**A second thing I had wrong, found the same way and stated here so the correction is in one
place.** ADDENDUM 1 §3 and this document's §2.2 said the premium "reaches the ISO only through the
retirement and CCS-retrofit screens". It also reaches **dispatch directly**: `apply_eac_to_mc`
(`runner.py:2824`) subtracts the effective per-unit EAC from `mc` for every credited fleet fuel, so
the CCS dispatch response this lane measured is the premium acting on the objective, not a screen
acting on capacity. Corrected in §2.2. Both errors are the same error — asserting a mechanism from
the paragraph nearest to hand rather than from the consumer list — and both cost nothing but
reading the lines.

**The mask correction makes the measured null stronger, not weaker.** Eight of the nine eligible
techs never saw a mask, and none of them built at $10, $20 or $30 either. **G-B1 PASSES pre-solve** on the `wind` /
`solar` row — 50.000 → 60.000 is the first uplift a NEISO VRE candidate gets in this campaign — and
the leg is worth solving precisely because the two legs of the fold now make opposite predictions.

#### 2.6.2 THE RESULT — 500 MW of nuclear in 2029, and VRE still does not move

| | REF | CES-P10 | CES-P20 | CES-P30 | **CES-P60** |
|---|---|---|---|---|---|
| `builds_by_source` 2029 | `{}` | `{}` | `{}` | `{}` | **`{'economic': 500.0}`** |
| `nuclear` MW 2026–2030 | 3355.4 ×5 | 3355.4 ×5 | 3355.4 ×5 | 3355.4 ×5 | 3355.4 / 3355.4 / 3355.4 / **3855.4 / 3855.4** |
| `nuclear` TWh 2029 / 2030 | 26.4822 / 26.4822 | 26.4822 / 26.4822 | 26.4822 / 26.4822 | 26.4822 / 26.4822 | **30.4284 / 30.4284** |
| `reserve_margin` 2029 / 2030 | 0.0440 / 0.0840 | 0.0440 / 0.0840 | 0.0440 / 0.0840 | 0.0440 / 0.0840 | **0.0639 / 0.1037** |
| `vre_mw` 2026–2030 | 4100 / 4100 / 4100 / 5902 / 7100 | identical | identical | identical | **identical** |
| `builds_renew_mw` 2029 / 2030 | 1802.0 / 1198.0 | identical | identical | identical | **identical** |

**The economic entry screen builds 500.0 MW of nuclear in 2029 — exactly
`QUEUE_CAP_PER_TECH_GW["NEISO"]["nuclear"] = 0.5 GW/yr`, the per-tech annual queue cap — and no
other arm in this lane carries it.** It is the campaign's **first economic entry response of any
kind on NEISO**, it is a measured threshold lying between $30 and $60, and it is decisive for what
S15 asked: **the CES row is wired to entry.** The alternative reading an expert would otherwise
have been entitled to — that the row never reaches the screen — is falsified by a build, not by an
argument.

**And at the same level, `vre_mw` and `builds_renew_mw` are still byte-identical to REF.** $60 is
the first level at which a NEISO wind or solar candidate sees ANY attribute uplift (50.000 →
60.000, +20 %), the queue budget is unbound (REF's 1802 / 1198 MW against 4 GW/yr), and the screen
still declines to build one MW of either. **So the $50 mask was real and it was not the binding
constraint on VRE.** The honest statement of NEISO's VRE result is therefore not "masked" but:
*within this window and at every attribute price this campaign can reach, NEISO's economic VRE
entry screen is far enough from its threshold that clearing the mask does not move it* — and its
`builds_renew_mw` is invariant to every attribute price tried, which reads as the step-4
known-additions channel rather than an economic screen near its margin. That is a fact about what
this ISO can be used to measure, asserted about the model and not about New England.

**Pre-registered prediction P-B1 — "`vre_mw` moves in at least one year" — therefore MISSES**, and
it is the more useful outcome of the two. ADDENDUM 2 declared its confidence as **low** and named
this exact branch as the reportable finding, before the solve.

#### 2.6.3 What else $60 does — and the leakage reversal on a third rung

In-ISO 2030 `emissions_mt` goes 2.9392 → **3.0664 Mt**, i.e. **worse than $30**, while the
leakage-inclusive total goes 5.2251 → **4.3002 Mt**, i.e. better — the §2.3 reversal repeating on
the $30 → $60 rung exactly as it did on $20 → $30. The mechanism is the same and larger:
`gas_cc_ccs` takes another 5.98 TWh (62.5748 → 68.5551) and imports collapse **10.2158 → 1.1113
TWh**, so `import_co2_mt_reported` falls 2.2859 → 1.2338 Mt. `clean_share` reaches **0.9542** and
the load-weighted price falls to **$29.280/MWh** from REF's $54.022. Curtailment is 0.0000 and
`unserved_mwh` is 0.0 in every year, as in every other arm.

#### 2.6.4 The one invariant FAIL in this lane, and what it does and does not put at risk

`CES-P60` is the only leg of ten that is not 14/14: **I9 (storage integrity) FAILs in 2030 only —
simultaneous charge+discharge 9.41 % of throughput.** It is declared in
`frontend/data/hindcast/invariant-failures.json` in the same commit as the registration, with the
diagnosis, and nothing was tuned to make it go away.

**Diagnosis, from the arm's own numbers.** At $60 the 2030 stack is 68.56 TWh of `gas_cc_ccs` on a
retrofit screen pinned at its 3 GW/yr cap, imports down to 1.11 TWh, VRE at its CF ceiling and
nuclear 500 MW larger. That produces the campaign's **first negative-price hours on NEISO — 585 h,
6.68 % of 2030**, against 0.0000 in REF and in every other arm. Across a wide band of hours the
charge/discharge price spread is then not bounded away from zero, so the rule 9 `[R-EPSILON]`
tiebreaker (0.001 $/MWh on charge + discharge) stops being decisive and the LP is free to cycle
both columns; storage throughput goes from REF's 0.295 TWh of charge to **4.100 TWh**. **The
epsilon was not moved** — rule 9 fixes it, and a lane that raised it to buy a PASS would be fitting
the diagnostic. Routed to SCN-DESK (§7 item 7).

**Containment, stated so no reader has to infer it.** The **deciding** result — the 500 MW nuclear
build — is in **2029, where I9 PASSES**, so the entry threshold between $30 and $60 does not rest
on a failing year. The **2030 dispatch, price and storage columns do carry the caveat** and are
quoted with it above. **Gate G-B3 is scored FAIL** on this, reported not smoothed (§3).

---

## 3. Gate verdicts G1–G12 and G-B1–G-B3

| gate | verdict | evidence |
|---|---|---|
| **G1** resolved-input premise reproduces at THE PIN | **PASS, pre-solve** | The carbon table reproduced the RGGI trajectory 26.0545 → 34.1521 $/t; volumes came from the runner's own demand chain; REF and LOAD-HI keys reproduced exactly (`8878d29743555b45`, `0d5c394b6c4e5cb6`). |
| **G1a** 2026 bit-identical to REF | **SPLIT, reported not smoothed** | EXACT in the three committed premium-only arms (`CES-P10/P20/P30`) and in `CES-P20+VOL-HI`. **`CES-P60` is NOT exact** — 15.8314 against REF's 15.8319, **−0.0005 Mt** — and it builds no row either. A premium is row-free but **not objective-free**: `apply_eac_to_mc` (`runner.py:2824`) subtracts the effective per-unit EAC from `mc` for every credited fleet fuel, so the premium is in the 2026 LP's objective even though the 2026 fleet is byte-identical to REF's (`capacity_by_fuel_mw` identical in all three arms). At $10–$30 that shifts no vertex; at $60 it does, and the measured move is a **1.2 GWh swap between `biomass` (5.6968 → 5.6956 TWh) and `gas_cc` (39.3177 → 39.3189)** — two **non-credited** fuels. So the residual is a degeneracy reshuffle of exactly the class P-1 identifies, not an instrument response, and it is reported rather than smoothed. Off by **+0.0004 Mt / −0.004 $/MWh** in the four row-bearing arms (`VOL-MID`, `VOL-HI`, `CES-T80`, `ALL-CLEAN`); every other 2026 scalar exact, `import_co2_mt_reported` included. Cause identified and then isolated by controlled comparison — §5, P-1. |
| **G2** REF-side precondition | **PASS** | REF 14/14 invariants PASS, `unserved_mwh` 0.0 in all five years, reserve margin +0.1681 → +0.0840 all in-band, `hours_ge_500` 0, curtailment 0.0000. **NEISO's price side IS campaign-grade**, unlike ERCOT's. The one standing data note: the NEISO zonal load file for weather-year 2024 is absent, so the demand chain falls back to the ISO-total shape — identical in REF and every arm, so every delta is protected. |
| **G3** footprint confinement | **PASS, all nine chartered arms** *(the bracket is scored under G-B2)* | Eligible generation pinned at its CF ceiling in every arm-year (6.9162 / 6.9162 / 6.9162 / 10.1517 / 12.0494 TWh); nuclear and hydro flat; curtailment 0.0000 everywhere; movement confined to thermal and import rows, plus the retrofit ledger. **`CES-P60` reproduces every limb except the nuclear one, where it builds 500 MW** — the target of the leg, scored under G-B2, not a footprint breach here. |
| **G4** `CES-T80` dual identity | **PASS, both limbs** | `FEDERAL_CES` = **50.0000 exactly** (the ACP to the digit) in 2026/2027/2028 where the target is unmet; **−0.0** in 2029 where REF's own credited share clears it; **strictly interior 4.2912** in 2030. Both limbs exercised by one arm; `ALL-CLEAN` reproduces it. |
| **G5** no non-target invariant flips | **PASS on the nine chartered arms; see G-B3 for the bracket** | 14/14 PASS in all nine chartered arms against REF's 14/14. No arm killed. |
| **G6** no unserved where REF has none | **PASS** | `unserved_mwh` = 0.0 in every arm-year. Declared not to bind on `ALL-CLEAN`, which raises load by construction. |
| **G7** voluntary dual bounded, per arm | **PASS** | $4.50 exactly on `VOL-MID`; $7.00 exactly on `VOL-HI`, `CES-P20+VOL-HI` and `ALL-CLEAN`; **−0.0 exactly** in every slack year. Escape MWh = the deficit exactly (2026: 1.5127 TWh). |
| **G8** curtailment before thermal | **VACUOUS, and reported as such** | REF's eligible curtailment is **0.0000 TWh by construction** — wind + solar run at exactly their unconstrained CF ceiling (6.9162 TWh, derived zero-LP and confirmed by the committed report at ≤1.9e-9). There is no dumped MWh for a REC buyer to buy first. Measured Δcurtailment = 0.0000 in every arm. **This gate cannot kill an arm on NEISO and the campaign's cross-ISO G8 row must not read NEISO as a pass it never earned.** |
| **G9** both nettings | **PASS, and they disagree** | §2.5. Counts-toward as headline, additional beside it, CES dual under each. The 2030 verdicts are opposite. |
| **G10** cap row identity *(Stage-B seed case — §8)* | **PASS, all five years** | Emissions = budget to 3.2e-13 relative or better; `co2_cap_price` > 0 and `n_co2_caps_binding` = 1 in every year. No slack year exists to test the dual-is-zero limb. |
| **G11** one instrument at a time *(Stage-B seed case — §8)* | **PASS, pre-solve and re-confirmed** | `cap_spec` set with `price_adder` `None`; `resolve_carbon_price` = 0.0000 in every year; `carbon_price_path: zero` so no federal price composes on top. |
| **G12** price vs quantity, side by side *(Stage-B seed case — §8)* | **PASS, reported with its asymmetry** | §8.3's table. The dual is below the adder in all five years while permitting more emissions; the asymmetry (adder → dispatch **and** screen; dual → dispatch only) was declared before the solve and is now measured in the deployment. |

| **G-B1** the mask is cleared at $60 | **PASS, computed pre-solve** | ADDENDUM 2 §3, pushed before the leg ran. `attr` strictly exceeds REF's for ten eligible techs in every zone (NEISO's RPS dual is a scalar, so the fold is zone-invariant) and all five years; the decisive row is `wind` / `solar` at **50.000 → 60.000**, the first VRE uplift in the campaign. The leg was solved only because this cleared. |
| **G-B2** footprint as a CES case | **PASS** | Eligible VRE generation pinned at its unconstrained CF ceiling in every year and **identical to REF to the MWh** (`wind` + `solar` = 6.9162 / 6.9162 / 6.9162 / 10.1517 / 12.0494 TWh); `hydro` flat at 6.9735 in all five; curtailment 0.0000; `unserved_mwh` 0.0. A premium builds **no LP row**, so there is no CES dual to move and that limb is vacuous here exactly as it is on `CES-P10/P20/P30` — stated, not scored as a pass. Movement is confined to the thermal, import and retrofit rows **plus the nuclear entry the case exists to detect**, which is the target and not a footprint breach. |
| **G-B3** no non-target load-bearing invariant flips PASS → FAIL | **FAIL, reported not smoothed** | **I9 (storage integrity) flips PASS → FAIL in 2030**: simultaneous charge+discharge 9.41 % of throughput, against 14/14 in REF. Diagnosed in §2.6.4 (585 negative-price hours make the rule 9 `[R-EPSILON]` tiebreaker non-decisive), declared in `invariant-failures.json` in the registration commit, routed §7 item 7, and **not tuned away**. The failure is confined to 2030; the leg's deciding result is in 2029, where I9 passes. |

**No gate killed an arm, and G-B3's failure does not retract one.** A gate may kill an arm and may
never promote one; none promoted anything. G-B3 is a STOP gate that fired **after** the solve on a
year that is not the leg's deciding year, so what it buys is the caveat in §2.6.4 attached to the
2030 columns — not a retraction of the 2029 entry result, and not a reason to quote the 2030
storage or price columns without it.

---

## 4. The deployment response — Stage A

| | REF | every chartered arm | **`CES-P60`** |
|---|---|---|---|
| `vre_mw` 2026–2030 | 4100 / 4100 / 4100 / 5902 / 7100 | **identical, all eight** | **identical** |
| `builds_renew_mw` 2029 / 2030 | 1802.0 / 1198.0 | **identical, all eight** | **identical** |
| `nuclear` MW 2029 / 2030 | 3355.4 / 3355.4 | identical, all eight | **3855.4 / 3855.4** |
| `builds_by_source` 2029 | `{}` | `{}`, all eight | **`{'economic': 500.0}`** |
| `retire_mw` 2027 | 2758.3 | identical (2244.9 on `ALL-CLEAN`, a LOAD-HI effect) | 2758.3 |
| `gas_cc_ccs` TWh 2030 | 25.9318 | 25.93 → **62.57** across the arms | **68.56** |

Three readings:

1. **No chartered level moves the deployment screen** — every committed CES premium, the CES target
   at its $50 ACP and both voluntary ceilings leave `vre_mw` and `builds_renew_mw` byte-identical to
   REF in all five years (§0 item 1).
2. **The screen is not dead — it is above its threshold, and the bracket found where.** At $60 it
   builds 500.0 MW of nuclear in 2029, the campaign's first economic entry on NEISO (§2.6.2). So
   "entry does not respond to any policy instrument on this ISO" — which is what this section said
   before the bracket ran — is now known to be **too strong**: it does respond, above the committed
   ladder, and with a tech the ladder's masking story never covered.
3. **VRE is the exception, and clearing its mask does not change it.** `vre_mw` is invariant across
   REF, $10, $20, $30, $50-ACP, both voluntary ceilings **and $60**. Whatever holds NEISO's economic
   VRE entry back, it is not the $50 RPS escape.

The retrofit fleet is where every arm's dispatch response lands: `gas_cc_ccs` 2030 generation runs
25.93 (REF) → 46.83 (P10) → 57.06 (P20) → 62.57 (P30) → **68.56 (P60)** TWh, and 35.12 on
`CES-T80`; at $60 its capacity screen is pinned at the 3 GW/yr retrofit cap. The Stage-B seed case's
own deployment reading — a quantity instrument that moves capacity **downward** — is in §8.4, out
of Stage A on ruling S17.

---

## 5. Predictions, scored at full magnitude

**The PRECOMMIT's, written before any leg.** Five missed. A miss is the finding, not something to
explain away, and each is reported with what it cost me to be wrong. Three of them — P-3, P-12,
P-13 — belong to the **Stage-B seed case** (§8) and are scored here unchanged, because a prediction
ledger does not move with a case's stage.

| # | prediction | verdict | measured |
|---|---|---|---|
| **P-1** | every surviving arm's 2026 is **bit-identical** to REF | **SPLIT → effectively a MISS** | EXACT in the four arms that build no LP row; off by **+0.0004 Mt / −0.004 $/MWh** in the four that do. My §6.1 argument — that the escape column "couples to nothing" — was wrong: the row and its escape column are built in **every** year, slack ones included, so their presence perturbs the simplex path in a fleet whose `gas_cc` / `gas_cc_ccs` classes are near-degenerate after capx D65-B moved the capture VOM adder 8.0 → 2.95. **`CES-P10` supplied the controlled comparison the earlier legs could not**: no row, no residual. The same mechanism dominates `VOL-MID`'s 2030 delta — 259 GWh reshuffles `gas_cc` → `gas_cc_ccs` at identical capacity and identical builds, worth −0.0841 Mt in a year the row does not bind — so **a NEISO voluntary arm's 2030 CO2 delta is degeneracy, not instrument, and is not quotable as a response.** **AMENDED by `CES-P60`:** the split is not "row / no row" as this line originally read — `CES-P60` builds no row and is still off by −0.0005 Mt, because a premium moves the credited units' `mc` through `apply_eac_to_mc` even with no row (§2.2, §3 G1a). The correct statement is that any arm which perturbs the 2026 objective **at all** can land on a different vertex of a near-degenerate LP; the three committed premium rungs happen not to, and $60 does. |
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
pushed as a commit before `CES-T80` was solved. **Its stated MECHANISM, however, was wrong in a way
neither prediction could expose** — the fold's RPS leg is fuel-gated to `{wind, solar}`, so the
premium was never masked for the eight other eligible techs. Corrected in §2.6.1; the predictions
stand, the explanation attached to them does not.

**ADDENDUM 2's, written after nine legs and before the tenth.**

| # | prediction | verdict | measured |
|---|---|---|---|
| **P-B1** | `vre_mw` moves in at least one year (declared **low** confidence, with the miss branch named as the reportable finding) | **MISS** | `vre_mw` 4100 / 4100 / 4100 / 5902 / 7100 and `builds_renew_mw` 0 / 0 / 0 / 1802 / 1198, byte-identical to REF, at the first level where a NEISO VRE candidate sees any uplift. The entry screen DID respond — 500.0 MW of nuclear in 2029 — so the prediction's *reasoning* (the screen is economics-limited and reachable) was right about the screen and wrong about the tech. §2.6.2. |
| **P-B2** | `gas_cc_ccs` 2030 generation exceeds `CES-P30`'s 62.5748 TWh | **HIT** | **68.5551 TWh**, with the retrofit capacity screen now pinned at its 3 GW/yr cap. |
| **P-B3** | the leakage-inclusive 2030 total falls below `CES-P30`'s 5.2251 Mt, with in-ISO `emissions_mt` declined either way | **HIT, and the declined half was the right call** | Inclusive total **4.3002 Mt**; in-ISO `emissions_mt` went the *other* way, 2.9392 → **3.0664 Mt**, reproducing the §2.3 reversal on a third rung. |
| **P-B4** | `clean_share` 2030 exceeds 0.8767; no arm-year carries `unserved_mwh` > 0 or a 14/14-invariant regression | **SPLIT** | `clean_share` **0.9542** and `unserved_mwh` 0.0 in all five years — both HIT. The invariant half **MISSES**: I9 FAILs in 2030 (§2.6.4). I predicted no regression and got one, and it is the leg's most interesting side-effect rather than an embarrassment to bury. |

**What I got wrong has a pattern, and the bracket sharpened it.** Four of the PRECOMMIT's five
misses (P-1, P-6, P-8, P-11) share one root: I reasoned about each instrument's *own* mechanism and
never asked what else was already in the `max()` the screens read. The $50 RPS escape was
measurable at zero LP cost before the first solve — it is in REF's own trajectory as `rps_dual` —
and I did not look. ADDENDUM 1 exists because leg 2 forced the question; it should have been phase
0's. **The same failure mode produced the §2.6.1 correction**: having finally looked at the
`max()`, I read the fold in the paragraph I was citing instead of the two folds that decide entry,
and asserted "no fuel gate" from a VRE-only helper where the claim is vacuous. Both errors are the
same error — reasoning about a `max()` from one of its arguments — and the fix in both cases cost
nothing but reading the lines.

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
| **`CES-P60`** | **8.4** | **1.68** | 3.58 | none — a premium is a screen price |
| **`CAP-STATE-TIGHT`** *(Stage-B seed — §8)* | **72.9** | **14.57** | 2.90 | **mass cap, BINDING in all five years** |
| **lane total** | **147.4** | **2.95 avg** | 3.69 max | 50 solve-years |

**A BINDING annual mass-cap row is an order of magnitude more expensive than an ESCAPING
clean-tier row** — 14.57 min/solve-year against 1.05–3.09 for every other arm, at 100 % CPU
throughout and with *lower* peak RSS, so it is solver iterations rather than memory. One of ten
legs is **49 % of the lane's LP**. The campaign budget assumed ~1.1 min/solve-year (the load lane's
own NEISO measurement), which is right for six arms and wrong by 13× for the seventh.

Two second-order readings worth carrying to the D-5 table:

- **Cost tracks whether the row BINDS, not whether it exists.** The voluntary arms carry a row and
  run at REF-like speed because it escapes — the escape column is one cheap slack. `CES-T80` and
  `ALL-CLEAN` sit in between (2.70–3.09) because their target row goes interior. Only the mass cap
  is tight against real dispatch in every hour.
- **A premium is free until it changes the dispatch regime.** The three committed premium arms are
  the fastest in the lane, faster than the campaign's own REF measurement, because they add no row
  at all — though they are **not** objective-free, since `apply_eac_to_mc` moves the credited units'
  `mc` (§2.2). **`CES-P60` is the exception that shows what actually costs time**: it also adds no row,
  and still runs 1.68 min/solve-year against $30's 1.09 — its 2026 alone is 203.2 s against a
  65.7–81.9 s median — because at $60 the stack is near-degenerate across 585 negative-price hours
  (§2.6.4). **Solver cost tracks the flatness of the objective, not the number of rows.**

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
   §3'S NEISO VERDICT WITH IT.** *(STATUS: the desk took this at r#19 as card **D-13** and the owner
   ruled **S17** — `CAP-STATE-TIGHT` leaves Stage A and is re-asked at full horizon. That settles
   the CASE's stage; it does **not** settle the KILL TEST, which is a charter rule that will be
   applied again to the next program-ISO case and is still stated wrongly. The correction below
   stands and is still routed.)* Both say a slack budget makes `CAP-STATE-TIGHT` byte-identical to
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
   case the campaign runs as a quantity instrument, and the substance of the Stage-B seed (§8), and it must not be discovered inside a result
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
5. **NEISO's $50/MWh RPS escape masks the campaign's attribute levels for a WIND OR SOLAR candidate
   on the ENTRY screen — and for no other tech — and no campaign case sets or varies it.**
   *(CORRECTED 2026-09-07, §2.6.1. This item previously said the RPS leg is "applied to **every**
   candidate tech, no fuel gate", citing `new_entry.py:1132-1143`. That citation is
   `_choose_vre_zone::_zone_revenue`, a VRE-only siting helper; the two folds that decide entry,
   `:1190-1197` and `:1474-1483`, gate the leg on `_RENEWABLE_NEW_FUELS = {wind, solar}` (`:121`).
   The desk's S15 ruling text carries the same citation and the same over-broad reading, which is
   why the correction is routed here rather than only fixed in place.)* `rps_dual = 50.0` in 5 of 5
   years in every arm, and every level this campaign carries — the $4.50 and $7.00 WTP ceilings, the
   $10 / $20 / $30 CES premiums, `CES-T80`'s $50 ACP — sits at or under it, so **a VRE candidate**
   cannot discriminate them. For the eight other eligible techs the leg is 0.0 and the premium was
   fully visible from $10 up. This is rule 19 `[R-ONE-MECH]`'s attribute doctrine working as
   designed and nothing here proposes changing it. **The S15 bracket then measured what the mask
   was actually worth**: at $60 the mask clears for VRE and VRE still does not build, while nuclear
   — never masked — builds 500 MW (§2.6). So the operative NEISO limitation is **not** the escape;
   it is that this ISO's economic VRE entry screen is nowhere near its threshold in this window.
   Whether a $50 escape in every forecast year is the right NEISO posture is **not** this lane's
   question and is asserted neither way.
6. **A slim-artifact gap the campaign got away with only by luck.** A registered leg's committed
   evidence is `full_horizon_summary.json` + `run_config.json`, and **neither carries
   `import_co2_mt_reported`, `clean_share`, `curtailment_twh` or `unserved_mwh`** — the WS-0
   leakage duty's own numbers. They were recoverable for NEISO only because SCN-WS5A-RESOLVE
   happened to regenerate the delta-report CSVs at its leg 2 (`931866cc`). A lane whose REF cache
   lives in another container and whose report CSVs were not refreshed **cannot discharge the duty
   at all**. One line in the campaign's registration recipe fixes it: the delta-report CSVs are
   part of a leg's committed evidence, not an optional extra.
7. **THE STORAGE TIEBREAKER DOES NOT SCALE WITH THE NEGATIVE-PRICE REGIME A HIGH CLEAN-ATTRIBUTE
   PRICE CREATES — and `CES-P60` is the first arm in this campaign to reach that regime.** Rule 9
   `[R-EPSILON]` fixes the storage tiebreaker at **0.001 $/MWh** on charge + discharge, which is
   decisive whenever the charge/discharge spread is bounded away from zero. At $60 NEISO's 2030 has
   **585 negative-price hours (6.68 %)** and a stack that is 68.56 TWh of one class, and across a
   wide band of hours the spread is not so bounded: I9 records **9.41 % of throughput** cycling both
   columns, on throughput that itself grew from REF's 0.295 TWh of charge to 4.100 TWh (§2.6.4).
   **Nothing was tuned here and the epsilon was not moved** — raising it to buy a PASS would be
   fitting the diagnostic, and `src/` is outside this lane's regions. The question for the desk is
   whether a fixed-scalar tiebreaker is the right construction for a forecast horizon in which
   deep-decarbonization arms routinely produce hundreds of zero-and-negative-price hours, or whether
   it needs to scale with the hour's own spread. It will not stay a NEISO-only observation: any ISO
   whose clean-attribute price is pushed above its RPS escape should reach the same regime.

---

## 8. STAGE-B SEED — `CAP-STATE-TIGHT`, solved and measured, routed OUT of Stage A by owner ruling S17

**Status, stated once and plainly.** This case was **solved, gated and registered**. It was **not**
killed, not retracted and not re-scored. On **2026-09-07** the desk took its result as card
**D-13** and the owner ruled **S17**: *drop the case from Stage A, route it to Stage B* — to be
re-asked at a full horizon where its 2050 glide has room to bite, leaving Stage A a clean
**price-only** policy axis (carbon path, CES premium, CES target, voluntary). Ruling **S12** — the
80 %-decline slope, `mass_cap_tons_by_year` and the case definition — is **not** withdrawn; only
the stage moved. The registered leg
`neiso-2026-2030-scn-campaign-policy-2026-09-06-cap-state-tight` **stays registered** (removing it
would strand a bundle and redden the parity gate, and git history is the record either way), and it
is **excluded from the Stage-A synthesis and from the plan's §5.1 rows**. Everything below is the
Stage-B seed evidence, carried here intact.

**Why the desk called the refusal the lane's highest-value decision.** The charter and
`FINDING-scn-cap-2026-09-06.md` §3 both ordered this case killed unsolved, on a test that cannot be
evaluated before the solve. Had the kill been obeyed, the campaign would have published *"no
difference from REF"* for a case that is in fact a policy **loosening of +2.9 to +13.9 Mt**. The
desk's own recommendation was keep-and-rename; the owner took a third option, and the ruling
records the call as made **against** the desk's recommendation on this lane's evidence.

### 8.1 The kill that was refused, and why — carried verbatim from §1.2

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

The case was therefore solved, on the owner's ruling. **§8.2 and §8.3 show the refusal was
correct**: the row binds from 2026 and the case is a policy *loosening*, which the naive test would
have recorded as "no difference from REF". *(This paragraph's original pointer was to §2, which
carried the cap rows before ruling S17 moved them here; the pointer is re-keyed, the claim is
untouched.)*

### 8.2 Per-year deltas vs the committed post-D77 REF — the §2 table's cap rows, moved not deleted

Same columns and same REF basis as §2; `duals` are `clean_region_duals` with the state RPS dual
after them.

| case | year | CO2 Mt | dCO2 | import CO2 Mt | clean share | lw $ | avg $ | curt TWh | unserved | duals | builds renew MW | retire MW |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CAP-STATE-TIGHT | 2026 | 20.6700 | +4.8381 | 3.592228 | 0.3485 | 46.675 | 46.07 | 0.0000 | 0.0 | None rps 50.0 | 0.0 | 0.0 |
| CAP-STATE-TIGHT | 2027 | 20.0025 | +2.9065 | 3.761912 | 0.3458 | 48.164 | 47.32 | 0.0000 | 0.0 | None rps 50.0 | 0.0 | 2758.324170000001 |
| CAP-STATE-TIGHT | 2028 | 19.3350 | +9.4628 | 3.955239 | 0.3433 | 49.298 | 48.35 | 0.0000 | 0.0 | None rps 50.0 | 0.0 | 0.0 |
| CAP-STATE-TIGHT | 2029 | 18.6675 | +13.9109 | 3.712614 | 0.3904 | 47.474 | 46.65 | 0.0000 | 0.0 | None rps 50.0 | 1802.0 | 1.638 |
| CAP-STATE-TIGHT | 2030 | 18.0000 | +11.8942 | 3.962221 | 0.3791 | 48.697 | 48.00 | 0.0000 | 0.0 | None rps 50.0 | 287.4 | 0.0 |

### 8.3 `CAP-STATE-TIGHT` — binding, loosening, and investment-suppressing — carried verbatim from §2.4

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

### 8.4 The Stage-B seed's deployment reading — a quantity instrument that moves capacity DOWNWARD

| | REF | `CAP-STATE-TIGHT` |
|---|---|---|
| `vre_mw` 2026–2030 | 4100 / 4100 / 4100 / 5902 / 7100 | 4100 / 4100 / 4100 / 5902 / **6189.4** |
| `builds_renew_mw` 2029 / 2030 | 1802.0 / 1198.0 | 1802.0 / **287.4** |
| `retire_mw` 2027 | 2758.3 | 2758.3 |
| `gas_cc_ccs` TWh 2030 | 25.9318 | **0.9326** |

**The only instrument in this lane that moves capacity moves it DOWNWARD.** The cap arm ends 2030
with **910.6 MW less VRE than REF**. A quantity instrument that binds on dispatch while its price
signal never reaches the investment screen produces exactly this: emissions capped, investment
suppressed. Under the cap the retrofit fleet very nearly vanishes (0.93 TWh against REF's 25.93)
because the retrofit screen sees carbon 0. This is the reading that makes the case worth re-asking
at full horizon rather than dropping, and it is routed §7 item 2 in measured form.

**What Stage B should carry forward, and what it should not.** Forward: the case definition and the
S12 slope unchanged; the §8.3 binding/loosening measurement as the 2026–2030 anchor a longer run is
compared against; the §7 item 2 asymmetry, which is a design question a longer horizon makes worse,
not better; and the cost measurement (§6), because a binding mass-cap row is an order of magnitude
more expensive per solve-year and a 25-year Stage-B run must be budgeted for it. Not forward: the
name. The case is called TIGHT and is not, in this window — that is a labelling fact the desk's own
card records, and Stage B should not inherit a name that asserts the opposite of the measurement.

---

## 9. Files

**Written by this lane, all inside its declared regions:**

| file | what |
|---|---|
| `docs/handoffs/PRECOMMIT-scn-ws5a-policy-neiso-2026-09-06.md` | phase 0 at THE PIN, pushed before the first solve |
| `docs/handoffs/PRECOMMIT-scn-ws5a-policy-neiso-2026-09-06-ADDENDUM-1.md` | the $50 RPS escape, pushed after 2 legs and before the other 7 |
| `docs/handoffs/PRECOMMIT-scn-ws5a-policy-neiso-2026-09-06-ADDENDUM-2.md` | ruling S15's bracket: step 1's duals, the G-B1 arithmetic, the key, and the §2.6.1 correction — pushed **before** the `CES-P60` solve |
| this document | — |
| `results/scn-campaign-policy-2026-09-06/NEISO/<CASE>/{full_horizon_summary,run_config}.json` | 10 legs, slim by construction (`redirect_cache=False`) |
| `frontend/data/hindcast/neiso-2026-2030-scn-campaign-policy-2026-09-06-<slug>.json` | 10 registry sidecars, forecast namespace only |
| `frontend/data/hindcast/invariant-failures.json` | one declaration + one note — `…-ces-p60: ["I9"]`, in the same commit as its registration |

**Consumed, never edited:** `configs/scenario_campaign_matrix.yaml`, the NEISO base YAML,
everything under `src/`, `scripts/run_ces_leg.py`, `scripts/register_forecast_run.py`,
`scripts/report_scenario_deltas.py`, and every committed bundle, sidecar and report CSV of the load
and resolve lanes.

**Untouched:** `program-status.json`, `ff-verdicts.json`, the whole **backcast** namespace, every
other ISO's files and every other lane's files. `data/clean/confirmed-retirements` was regenerated
locally (derived, gitignored, never committed).

## 10. Duties

- **No default moved, no knob moved, no `ScenarioConfig` field added, no matrix case added.** DOF
  ledger: **zero** free parameters — `CES-P60`'s $60 is an externally-identified published-ACP
  bracket, one common level for every ISO, never swept and never per-ISO (rules 1 `[R-STRUCT]` /
  25 `[R-ISO-SCOPE]`). No `authorized_price_tuning` — that is a backcast offer-curve channel and
  this is a forecast lane. **Nothing was tuned to clear the I9 FAIL**, and rule 9 `[R-EPSILON]`'s
  0.001 $/MWh tiebreaker was not moved.
- **Rule 29 `[R-SCREEN]`:** ADDENDUM 2 — step 1's per-year duals, the G-B1 arithmetic and the leg's
  key `a37868175d5ae724` — was pushed **before** the `CES-P60` solve, and the solve reproduced that
  key exactly. Rule 29(b): form 4 stands, the committed REF is the control, no control solve was
  earned or spent. Rule 29(c): no screen bundle and no control bundle exists.
- **The Y-24 declaration ratchet:** `CES-P60`'s I9 FAIL is declared in
  `frontend/data/hindcast/invariant-failures.json` **in the same commit as its registration**, with
  its diagnosis. The registrar refused the first attempt for exactly that reason, which is the gate
  working; the remaining nine legs are 14/14 PASS and correctly carry no line.
- **Ruling S17:** `CAP-STATE-TIGHT` stays **registered** and is **excluded** from the Stage-A
  synthesis and the plan §5.1 rows; its evidence is §8. No sidecar was removed, so no bundle is
  stranded and the parity gate is untouched.
- **Rule 15 / plan §7.5:** all **ten** legs registered into the **forecast** namespace under
  campaign `scn-campaign-policy-2026-09-06`, one run id per (ISO, case). The backcast registry is never
  touched. **This lane produces no keeper and no keeper candidate** — a keeper is a backcast
  artifact and a scenario-campaign arm cannot be one.
- **Rule 22 / R-AZ:** every solve year is 2026–2030, forecast mode, inside the §2.1b five-year
  window. No holdout tier is touched, at launch or at registration.
- **Rule 27:** no source file ≥300 lines was rewritten; every push was fetch-back verified,
  `invariant-failures.json` (419 lines) included.
- **Backcast byte-identity:** untouched by construction (`mode="forecast"` on every leg).
