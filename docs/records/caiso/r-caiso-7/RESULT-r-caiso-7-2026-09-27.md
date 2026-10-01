# RESULT — R-CAISO-7: the 2019–21 CC_REGULAR excess is a missing DSW import; 2021 discards measured hub prices; SD LCT caps over-bind (2026-09-27)

Zero LP. No shard launched, no run registered, keeper unchanged:
`2026-09-26-caiso-r5-pastoria-co2` (CALIBRATED, single ledgered C3c 2024). Fold
`2026-09-27-caiso-r6-malin-fold` unchanged.

Probe: `scripts/probes/_rcaiso7_dsw_import_census.py` → `results/calibration/_rcaiso7/object1_census.json`.
It reads the R-CAISO-6 leg bundles from their shard commits (2019 `11d774b8`, 2020 `daee0429`, 2021 `e419162a`).

## Object 1 — why 2019–21 over-dispatch CC_REGULAR by ~20 TWh

**The excess is DSW-corridor import that the model does not buy.** The gap is flat across hours and months.

| TWh | 2019 | 2020 | 2021 |
|---|--:|--:|--:|
| DSW net import, model / EIA-930 | 20.9 / 44.7 | 17.3 / 41.9 | 15.8 / 40.9 |
| PNW net import, model / EIA-930 | 16.7 / 9.1 | 21.5 / 17.3 | 21.8 / 13.6 |
| total import gap | −16.2 | −20.4 | −16.9 |
| CC_REGULAR over the C1 target | +20.4 | +24.8 | +19.4 |

- DSW short by 2.3–3.6 GW in every window (h0–6, h8–16, h17–22) and every month.
- In 2022–25 total imports run +3 to +8 TWh **over** EIA-930, so this is specific to the three fold years.
- By zone, the CC excess is system-wide: NP15 +6 to +9 TWh, SDGE only +2.4 to +2.9 (EIA-923 zone split).

**Suspects checked and cleared:**
- Demand: model within ±3 TWh of EIA-930 all three years.
- Hydro: model 29.2 / 16.2 / 11.4 TWh is at or above measured, which pushes gas **down**, not up. (EIA-930's CISO
  hydro for 2019–20 is itself incomplete, 24.4 / 4.5.)
- Other / biomass: same offset in 2022–25, where the ISO is calibrated.
- BTM: `btm_backfill_year` unset; demand matches.

**Root cause: no measured intertie hub price for 2019–21.**

| year | measured hub hours | what happens |
|---|---|---|
| 2019, 2020 | 0 | every tranche on the static ladder; DSW clean-depth tranches unbuilt (0 MW) |
| 2021 | 5,976 of 8,760 (May–Dec) | **defect:** the pricing loader drops the whole year (>25 % gap), but the arming loader still builds ~2.75 GW of DSW clean-depth tranches, which sit on the $180 placeholder and dispatch 0 |

- DSW_CCGT offers $63–69 and DSW_CT $102–112 on the ladder, against a CAISO λ of $36–56. DSW_CCGT runs at CF 0–18 %.
- The static $36 PNW_midC is **below** measured Malin in 2021 ($56.5), which is why PNW over-imports.
- The code comment at `inject_caiso_per_hub_intertie_prices` already names the $180-placeholder failure mode as a
  silent defect.

**2021 lever (proposed, not armed):** price each hub at its measured print in the hours it prints, and keep the
ladder only in unprinted hours.
- Zero new parameters; rule 14 (measured over estimate); rule 19 (no new mechanism; arming and pricing become one
  gate).
- First-order sizing on the 2021 leg: up to **+24.2 TWh** DSW imports clear (no price feedback, so an upper bound)
  against a measured DSW deficit of 25.1 TWh. PNW_midC would dispatch less.
- By construction inert in 2022–25 (≤ 1 unprinted hour, or 2023's 23 % gap already on the fill path) and in 2019–20
  (no print). G-DRIFT should prove it.
- Cost: a flag (rule 24, matrix row per rule 28(c)); for a same-recipe fold, a 7-year re-solve (7 shards, ~25 min
  wall); a promotion question on a recipe change that is byte-identical for 2022–25.

**2019–20: no admissible lever. The STOP stands.** The forward reference formula (`caiso_hub_reference_price`)
rides the forward Henry Hub trajectory (Palo Verde 2022: $36.9 vs measured $82.9), and its measured-gas variant
prints nothing for most 2019–21 state-months.

**Bench basis (owner decision, carried from R-CAISO-5 §6).** Adding CAISO to `EIA930_GAS_FOLD_REFUTED` raises the
2019–21 CC_REGULAR targets by ≈ +5.5 / +3.9 / +2.4 TWh and moves 2022–25 by nothing.

| C1 CC_REGULAR miss, TWh | 2019 | 2020 | 2021 |
|---|--:|--:|--:|
| now | +20.4 | +24.8 | +19.4 |
| with the flip (approx.) | ≈ +14.9 | ≈ +20.9 | ≈ +17.0 |

Still FAIL. Exact values need a bench re-render. Not flipped.

## Object 2 — 2022 LCT area rows: recommend NOT landing as-is

The 2019–21 fold legs already run the per-year LCT caps (`peak_load − requirement`), and they show what a low cap
does:

| | 2019 | 2020 | 2021 | 2022 if landed |
|---|--:|--:|--:|--:|
| SD import cap, MW | 386 | 718 | 635 | 587 (static now 1,436) |
| SP15_rest>SDGE binding hours | 7,461 | 4,058 | 4,876 | — |
| SDGE mean price, $/MWh (SP15) | **388.8** (40.8) | 53.6 (35.9) | 60.9 (56.4) | 2022 keeper: 88.3 (86.4) |
| SDGE hours > $500 | 1,534 | 77 | 20 | 24 now |
| SDGE unserved, MWh | **419,683** | 12,125 | 2,259 | — |

- `peak_load − requirement` is the import capability in the LCT's 1-in-10 N-1-1 **planning** case. Applying it as
  an all-hours TTC is a definition misalignment (rule 14's exception), and it produces VOLL-level scarcity when the
  number is small.
- A 587 MW cap sits between 2021 (635) and 2020 (718): expect tens of $500+ hours and GWh of SD unserved in the
  keeper's **gating** 2022 leg.
- Recommendation: do not land the 2022 rows under this construction. Route the construction itself: find the
  operating SD import limit (SWPL / Sunrise nomogram) before any year uses a low LCT cap. This also affects the
  already-armed 2019–21 caps (reported-only).

## Object 3 — C4 2025 margin

Nothing here touches 2025: L1 changes only 2021, and the LCT rows only 2022. **C4 2025 stays 0.2987** vs ≤ 0.30.

## Also checked

`test_caiso_st_gas_peak_measured` fails because `caiso_offer_curve_measured.json`'s CT_PEAKER peak band reads 1.154,
not the registry's 1.166. The authoring commit is beyond this clone's shallow history (`92a6dc35` is only the graft
root). Either the artifact was re-derived without the registry following, or the reverse. This is CAISO-scoped:
routed to the next lane. Not in this diff.

## Owner decisions

1. **Arm the 2021 partial-year measured hub pricing?** (flag + 7 shards; keeper 2022–25 expected byte-identical)
2. **2022 LCT rows:** recommend NOT landing; route the SD-limit construction instead.
3. **`EIA930_GAS_FOLD_REFUTED` for CAISO:** before/after above; still FAIL either way.

## Housekeeping

- PR #6790 (the R-CAISO-6 handoff) was already on `main` at `faa8a376`; closed as a duplicate.
- Nothing to salvage: `claude/r-caiso-6-O2-2019/2020/2021` are composed into `rcaiso6_tp_2019_2021` on `main`.
- **Leftover branches for the owner to delete:** `claude/r-caiso-6`, `claude/r-caiso-6-O2-2019/2020/2021`.
  `claude/r-caiso-5-XE-*` are already gone.
- No shards launched this session.
