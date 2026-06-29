# Temperature reliability-floor coefficients

Derived by `scripts/derive_reliability_coeffs.py`. `floor_pct = commit_frac x min_stable_pct` (never residual-tuned, CLAUDE.md #9/#11). A limb is `enabled` only when `rho >= 0.3`, `n >= 30`, and `floor_pct > baseline`; weak limbs ship OFF but stay visible below.

## ERCOT

| zone | plant_class | driver | threshold | floor_pct | enabled | commit_frac | min_stable_pct | rho | n | baseline |
|---|---|---|---|---|---|---|---|---|---|---|
| North | COAL | tmax | 25.0 | 0.3272 | False | 0.9348 | 0.35 | 0.471 | 681 | 0.595 |
| North | COAL | tmin | 0.0 | 0.3378 | False | 0.965 | 0.35 | 0.3034 | 53 | 0.6175 |
| South | CT_PEAKER | tmax | 25.0 | 0.0 | False | 0.3243 | 0.0 | 0.3476 | 844 | 0.0299 |
| South | CT_PEAKER | tmin | 0.0 | 0.0 | False | 0.4827 | 0.0 | -0.4857 | 6 | 0.0418 |
| South | CC_REGULAR | tmax | 25.0 | 0.0 | False | 0.6741 | 0.0 | 0.5789 | 872 | 0.2399 |
| South | CC_REGULAR | tmin | 0.0 | 0.0 | False | 1.0 | 0.0 | -0.7143 | 6 | 0.2832 |
| North | ST_GAS | tmax | 25.0 | 0.0 | False | 0.704 | 0.0 | 0.5244 | 649 | 0.0783 |
| North | ST_GAS | tmin | 0.0 | 0.0 | False | 0.7062 | 0.0 | 0.4288 | 51 | 0.137 |
| Houston | ST_GAS | tmax | 25.0 | 0.0 | False | 0.4943 | 0.0 | 0.3923 | 559 | 0.1201 |
| Houston | ST_GAS | tmin | 0.0 | 0.0 | False | 0.4943 | 0.0 | 0.3151 | 11 | 0.1595 |
| Houston | CT_PEAKER | tmax | 25.0 | 0.0056 | False | 0.6934 | 0.0081 | 0.5413 | 781 | 0.0693 |
| Houston | CT_PEAKER | tmin | 0.0 | 0.0059 | False | 0.7242 | 0.0081 | 0.2914 | 15 | 0.0967 |
| Houston | CC_REGULAR | tmax | 25.0 | 0.0 | False | 0.8151 | 0.0 | 0.6623 | 781 | 0.3344 |
| Houston | CC_REGULAR | tmin | 0.0 | 0.0 | False | 0.9494 | 0.0 | 0.7693 | 15 | 0.3927 |
| Houston | COAL | tmax | 25.0 | 0.25 | False | 1.0 | 0.25 | 0.5616 | 781 | 0.53 |
| Houston | COAL | tmin | 0.0 | 0.25 | False | 1.0 | 0.25 | 0.0701 | 15 | 0.6342 |
| West | CT_PEAKER | tmax | 25.0 | 0.0 | False | 0.5858 | 0.0 | 0.0726 | 618 | 0.107 |
| West | CT_PEAKER | tmin | 0.0 | 0.0 | False | 0.5038 | 0.0 | 0.172 | 86 | 0.1151 |
| Northeast | ST_GAS | tmax | 25.0 | 0.0 | False | 1.0 | 0.0 | 0.4558 | 516 | 0.2525 |
| Northeast | ST_GAS | tmin | 0.0 | 0.0 | False | 1.0 | 0.0 | 0.5246 | 36 | 0.2743 |
| South_Central | CT_PEAKER | tmax | 25.0 | 0.0 | False | 0.6292 | 0.0 | 0.4853 | 676 | 0.0727 |
| South_Central | CT_PEAKER | tmin | 0.0 | 0.0 | False | 0.5868 | 0.0 | 0.3282 | 34 | 0.0868 |
| South_Central | ST_GAS | tmax | 25.0 | 0.0 | False | 0.7869 | 0.0 | 0.6616 | 771 | 0.2109 |
| South_Central | ST_GAS | tmin | 0.0 | 0.0 | False | 0.754 | 0.0 | 0.3932 | 43 | 0.2787 |
| North | CT_PEAKER | tmax | 25.0 | 0.0 | False | 0.2754 | 0.0 | 0.4293 | 565 | 0.005 |
| North | CT_PEAKER | tmin | 0.0 | 0.0 | False | 0.2754 | 0.0 | 0.3554 | 35 | 0.0079 |
| South_Central | CC_REGULAR | tmax | 25.0 | 0.0776 | False | 0.9052 | 0.0857 | 0.7016 | 771 | 0.4594 |
| South_Central | CC_REGULAR | tmin | 0.0 | 0.0824 | False | 0.9614 | 0.0857 | 0.1474 | 43 | 0.5376 |
| Northeast | COAL | tmax | 25.0 | 0.25 | False | 1.0 | 0.25 | 0.4795 | 689 | 0.496 |
| Northeast | COAL | tmin | 0.0 | 0.25 | False | 1.0 | 0.25 | 0.1596 | 50 | 0.5338 |
| South | COAL | tmax | 25.0 | 0.2819 | False | 0.8675 | 0.325 | 0.5098 | 763 | 0.5654 |
| South | COAL | tmin | 0.0 | 0.2597 | False | 0.799 | 0.325 | -0.6571 | 6 | 0.5836 |
| South_Central | COAL | tmax | 25.0 | 0.222 | False | 0.8882 | 0.25 | 0.6271 | 771 | 0.4442 |
| South_Central | COAL | tmin | 0.0 | 0.2407 | False | 0.963 | 0.25 | 0.371 | 43 | 0.47 |
| Houston | CT_CHP | tmax | 25.0 | 0.2749 | False | 0.4531 | 0.6067 | 0.2681 | 781 | 0.3447 |
| Houston | CT_CHP | tmin | 0.0 | 0.2792 | False | 0.4602 | 0.6067 | -0.1158 | 15 | 0.3296 |
| South | CC_CHP | tmax | 25.0 | 0.1742 | True | 0.2903 | 0.6 | 0.3939 | 868 | 0.1609 |
| South | CC_CHP | tmin | 0.0 | 0.1742 | False | 0.2903 | 0.6 | -0.0286 | 6 | 0.1709 |
| Houston | CC_CHP | tmax | 25.0 | 0.4715 | False | 0.7858 | 0.6 | 0.6263 | 781 | 0.5542 |
| Houston | CC_CHP | tmin | 0.0 | 0.4743 | False | 0.7906 | 0.6 | 0.324 | 15 | 0.5584 |
| North | CC_REGULAR | tmax | 25.0 | 0.0 | False | 0.8399 | 0.0 | 0.6144 | 681 | 0.4286 |
| North | CC_REGULAR | tmin | 0.0 | 0.0 | False | 0.8711 | 0.0 | 0.2922 | 53 | 0.4992 |
| West | CC_CHP | tmax | 25.0 | 0.6 | False | 1.0 | 0.6 | -0.128 | 373 | 0.2374 |
| West | CC_CHP | tmin | 0.0 | 0.6 | False | 1.0 | 0.6 | -0.2213 | 36 | 0.242 |
| Northeast | CC_REGULAR | tmax | 25.0 | 0.0 | False | 1.0 | 0.0 | 0.2102 | 487 | 0.5391 |
| Northeast | CC_REGULAR | tmin | 0.0 | 0.0 | False | 1.0 | 0.0 | 0.1146 | 51 | 0.5312 |
| West | CC_REGULAR | tmax | 25.0 | 0.0 | False | 0.9037 | 0.0 | 0.187 | 677 | 0.588 |
| West | CC_REGULAR | tmin | 0.0 | 0.0 | False | 0.905 | 0.0 | 0.3585 | 100 | 0.6513 |

## MISO

| zone | plant_class | driver | threshold | floor_pct | enabled | commit_frac | min_stable_pct | rho | n | baseline |
|---|---|---|---|---|---|---|---|---|---|---|
| MISO-South | ST_GAS | tmax | 25.0 | 0.0 | False | 0.7459 | 0.0 | 0.6769 | 620 | 0.2819 |
| MISO-South | ST_GAS | tmin | 0.0 | 0.0 | False | 0.6863 | 0.0 | 0.7056 | 48 | 0.3822 |
| MISO-Central | COAL | tmax | 25.0 | 0.2716 | False | 0.9246 | 0.2937 | 0.5583 | 334 | 0.5272 |
| MISO-Central | COAL | tmin | 0.0 | 0.2716 | False | 0.9246 | 0.2937 | 0.5989 | 267 | 0.5381 |
| MISO-Central | CT_PEAKER | tmax | 25.0 | 0.0 | False | 0.5375 | 0.0 | 0.6374 | 334 | 0.2516 |
| MISO-Central | CT_PEAKER | tmin | 0.0 | 0.0 | False | 0.2845 | 0.0 | 0.4715 | 267 | 0.3088 |
| MISO-Central | ST_GAS | tmax | 25.0 | 0.0 | False | 0.4514 | 0.0 | 0.4523 | 334 | 0.1598 |
| MISO-Central | ST_GAS | tmin | 0.0 | 0.0 | False | 0.38 | 0.0 | 0.2115 | 267 | 0.1937 |
| MISO-Central | CC_REGULAR | tmax | 25.0 | 0.0 | False | 0.7967 | 0.0 | 0.4235 | 334 | 0.6502 |
| MISO-Central | CC_REGULAR | tmin | 0.0 | 0.0 | False | 0.7564 | 0.0 | 0.2867 | 267 | 0.6735 |
| MISO-North | CT_PEAKER | tmax | 25.0 | 0.0 | False | 0.41 | 0.0 | 0.4923 | 386 | 0.0653 |
| MISO-North | CT_PEAKER | tmin | 0.0 | 0.0 | False | 0.1614 | 0.0 | 0.0261 | 299 | 0.1102 |
| MISO-North | COAL | tmax | 25.0 | 0.223 | False | 0.865 | 0.2578 | 0.4346 | 389 | 0.5206 |
| MISO-North | COAL | tmin | 0.0 | 0.2128 | False | 0.8255 | 0.2578 | 0.499 | 311 | 0.5481 |
| MISO-North | ST_CHP | tmax | 25.0 | 0.0327 | False | 0.0364 | 0.9 | 0.1153 | 25 | 0.0035 |
| MISO-North | ST_CHP | tmin | 0.0 | 0.0327 | False | 0.0364 | 0.9 | 0.4 | 11 | 0.0051 |
| MISO-North | ST_GAS | tmax | 25.0 | 0.0 | False | 0.3942 | 0.0 | 0.4306 | 368 | 0.1173 |
| MISO-North | ST_GAS | tmin | 0.0 | 0.0 | False | 0.3096 | 0.0 | 0.0517 | 310 | 0.136 |
| MISO-South | CT_CHP | tmax | 25.0 | 0.1274 | False | 0.3639 | 0.35 | -0.3002 | 620 | 0.5714 |
| MISO-South | CT_CHP | tmin | 0.0 | 0.1274 | False | 0.3639 | 0.35 | 0.1542 | 48 | 0.5449 |
| MISO-Central | ST_CHP | tmax | 25.0 | 0.2883 | False | 0.3203 | 0.9 | 0.1503 | 296 | 0.2859 |
| MISO-Central | ST_CHP | tmin | 0.0 | 0.3363 | True | 0.3737 | 0.9 | 0.3329 | 165 | 0.2752 |
| MISO-South | CC_REGULAR | tmax | 25.0 | 0.0 | False | 0.9087 | 0.0 | 0.7938 | 620 | 0.4972 |
| MISO-South | CC_REGULAR | tmin | 0.0 | 0.0 | False | 0.9112 | 0.0 | 0.5424 | 48 | 0.5566 |
| MISO-South | CT_PEAKER | tmax | 25.0 | 0.0 | False | 0.4987 | 0.0 | 0.6134 | 620 | 0.3493 |
| MISO-South | CT_PEAKER | tmin | 0.0 | 0.0 | False | 0.4219 | 0.0 | 0.5279 | 48 | 0.4009 |
| MISO-North | CC_REGULAR | tmax | 25.0 | 0.0 | False | 0.8499 | 0.0 | 0.1803 | 388 | 0.4461 |
| MISO-North | CC_REGULAR | tmin | 0.0 | 0.0 | False | 0.7579 | 0.0 | -0.0633 | 307 | 0.535 |
| MISO-South | COAL | tmax | 25.0 | 0.3015 | False | 0.8595 | 0.3508 | 0.7335 | 620 | 0.403 |
| MISO-South | COAL | tmin | 0.0 | 0.3217 | False | 0.9169 | 0.3508 | 0.7637 | 48 | 0.4512 |
| MISO-Central | CC_CHP | tmax | 25.0 | 0.2835 | False | 0.8101 | 0.35 | 0.3469 | 334 | 0.5514 |
| MISO-Central | CC_CHP | tmin | 0.0 | 0.2851 | False | 0.8145 | 0.35 | 0.2369 | 267 | 0.5518 |
| MISO-South | ST_CHP | tmax | 25.0 | 0.4067 | False | 0.4519 | 0.9 |  | 620 | 1.0 |
| MISO-South | ST_CHP | tmin | 0.0 | 0.4067 | False | 0.4519 | 0.9 |  | 48 | 1.0 |
| MISO-Central | CT_CHP | tmax | 25.0 | 0.1843 | False | 0.5265 | 0.35 | 0.268 | 334 | 0.8439 |
| MISO-Central | CT_CHP | tmin | 0.0 | 0.1539 | False | 0.4398 | 0.35 | 0.0446 | 267 | 0.8752 |
| MISO-South | CC_CHP | tmax | 25.0 | 0.2923 | False | 0.8351 | 0.35 | 0.1168 | 620 | 0.7522 |
| MISO-South | CC_CHP | tmin | 0.0 | 0.2935 | False | 0.8385 | 0.35 | 0.2759 | 48 | 0.7479 |
| MISO-North | CC_CHP | tmax | 25.0 | 0.2387 | False | 0.6819 | 0.35 | 0.241 | 274 | 0.3937 |
| MISO-North | CC_CHP | tmin | 0.0 | 0.2387 | False | 0.6819 | 0.35 | -0.116 | 247 | 0.4017 |

## CAISO

| zone | plant_class | driver | threshold | floor_pct | enabled | commit_frac | min_stable_pct | rho | n | baseline |
|---|---|---|---|---|---|---|---|---|---|---|
| NP15 | CT_PEAKER | netload | 0.0 | 0.0 | False | 0.3334 | 0.0 | 0.4816 | 394 | 0.053 |
| NP15 | CC_REGULAR | tmax | 25.0 | 0.0 | False | 0.7899 | 0.0 | 0.5998 | 407 | 0.4225 |
| SP15 | ST_GAS | tmax | 25.0 | 0.0 | False | 0.5694 | 0.0 | 0.2327 | 135 | 0.2113 |
| SP15 | CT_PEAKER | netload | 0.0 | 0.0 | False | 0.4401 | 0.0 | 0.2322 | 134 | 0.0286 |
| SP15 | CC_REGULAR | tmax | 25.0 | 0.0 | False | 0.5982 | 0.0 | 0.2047 | 136 | 0.2262 |
| NP15 | CC_CHP | tmax | 25.0 | 0.1813 | False | 0.4422 | 0.41 | 0.4003 | 384 | 0.3008 |
| ZP26 | CT_PEAKER | netload | 0.0 | 0.0 | False | 0.3022 | 0.0 | 0.2738 | 195 | 0.0169 |
| NP15 | CT_CHP | netload | 0.0 | 0.094 | False | 0.2123 | 0.4429 | 0.3589 | 394 | 0.1122 |
| SP15 | CC_CHP | tmax | 25.0 | 0.028 | True | 0.0637 | 0.44 | 0.3889 | 39 | 0.0177 |
| ZP26 | CT_CHP | netload | 0.0 | 0.0299 | False | 0.0675 | 0.4431 | 0.3314 | 317 | 0.0156 |
| ZP26 | CC_REGULAR | tmax | 25.0 | 0.0 | False | 0.8293 | 0.0 | 0.3948 | 562 | 0.3097 |
| ZP26 | CC_CHP | tmax | 25.0 | 0.35 | False | 1.0 | 0.35 | 0.2563 | 524 | 0.7416 |

### CAISO review notes (post-derivation, CLAUDE.md #1/#9/#11)

Only **tmax** limbs were produced — CAISO zone TMIN never falls below the 0 °C
cold onset in 2023–2025 (mild California winters), so no cold limb has data. This
is physically correct, not a gap.

**CT classes are net-load-driven, not temperature-driven (architecture decision,
rebuild-plan §B/§C resolved-decision #2).** The derive script regresses every
class on temperature; for CAISO the CT fleet (simple-cycle peakers + CT cogen)
commits for the evening net-load ramp / duck curve, *not* for absolute air
temperature. The five `CT_PEAKER`/`CT_CHP` rows are therefore reclassified to
`driver="netload"` and ship **`enabled=False`**, because:
- The reported `commit_frac`/`rho`/`n` were measured against a **tmax** gate. A
  temperature correlation does **not** validate a net-load gate, so it would be
  dishonest to enable a net-load limb on that evidence.
- Per-zone net load is not yet plumbed into the derive script (no net-load-gated
  `commit_frac`) nor into the floor engine (`driver="netload"` limbs no-op until
  Phase 2). `threshold=0.0` is a **placeholder**, not a derived MW gate — the
  net-load threshold and a net-load-gated `commit_frac` are Phase-2 work.
- The retained `floor_pct`/`commit_frac` are the temperature-measured **structural
  placeholders** only; they are NOT quoted as forward skill and the limbs are OFF.

**Why so many limbs are OFF — `min_stable_pct = 0` for merchant thermal.** In the
CAISO model bins (`bin_assignments_CAISO.csv`), `CC_REGULAR` (13.7 GW), `CT_PEAKER`
(7.6 GW) and `ST_GAS` (2.9 GW) carry **0 % must-run** — merchant CAISO thermal has
no must-run obligation. Since `floor_pct = commit_frac × min_stable_pct`, their
floor is **0 by construction** regardless of how heavily they commit on hot days
(e.g. ZP26 `CC_REGULAR` runs `commit_frac=0.83` on hot days but still floors 0).
This is the correct CLAUDE.md #9/#11 outcome: no physical must-run tranche → no
floor. Only the **CHP** classes carry a must-run tranche (CC_CHP ≈ 0.42, CT_CHP ≈
0.45 — the cogeneration thermal-host obligation), so they are the only classes that
can produce a non-zero structural floor.

**The single enabled limb — `SP15 CC_CHP` (tmax, floor_pct = 0.028).** Passes the
gate (ρ=0.389 ≥ 0.3, n=39 ≥ 30, floor 0.028 > baseline 0.0177). Note this is a
**marginal, low-commitment** limb (`commit_frac=0.064`, small n=39) — only ~6 % of
SP15 CC_CHP nameplate reports online on hot days in CAMPD, so the floor it imposes
is tiny (2.8 % of available). It is a real-but-weak positive temperature response;
kept enabled per the honest gate, but flagged here as marginal.

**Other CC_CHP limbs ship OFF correctly:** NP15 (floor 0.181 < baseline 0.301) and
ZP26 (floor 0.350 < baseline 0.742) both fail `floor_pct > baseline` — on mild days
these cogen fleets already run *above* the hot-day commitment floor, so a floor
would be slack. Correctly disabled, not invented.

**Net:** 12 limbs, **1 enabled** (SP15 CC_CHP, tmax). 5 CT limbs reclassified to
`driver="netload"` and disabled (Phase-2 net-load derivation pending); 6 other
temperature limbs disabled — 4 by `min_stable_pct=0` (NP15/SP15/ZP26 CC_REGULAR +
SP15 ST_GAS) and 2 CC_CHP by floor ≤ baseline (NP15, ZP26). No limb was tuned to a
price/volume residual; no measured-CF ceiling was used.

## NYISO

| zone | plant_class | driver | threshold | floor_pct | enabled | commit_frac | min_stable_pct | rho | n | baseline |
|---|---|---|---|---|---|---|---|---|---|---|
| Capital_Hudson | ST_GAS | tmax | 25.0 | 0.0 | False | 0.6308 | 0.0 | 0.5538 | 233 | 0.1302 |
| Capital_Hudson | ST_GAS | tmin | 0.0 | 0.0 | False | 0.4612 | 0.0 | 0.4634 | 204 | 0.1335 |
| Capital_Hudson | CT_PEAKER | tmax | 25.0 | 0.0 | False | 0.4413 | 0.0 | 0.3578 | 41 | 0.0195 |
| Capital_Hudson | CT_PEAKER | tmin | 0.0 | 0.0 | False | 0.4902 | 0.0 | 0.2046 | 37 | 0.0253 |
| NYC | ST_GAS | tmax | 25.0 | 0.0 | False | 0.9695 | 0.0 | 0.6302 | 343 | 0.1583 |
| NYC | ST_GAS | tmin | 0.0 | 0.0 | False | 0.8577 | 0.0 | 0.143 | 143 | 0.2101 |
| NYC | CT_CHP | tmax | 25.0 | 0.4021 | False | 0.8693 | 0.4625 | 0.3262 | 343 | 0.7037 |
| NYC | CT_CHP | tmin | 0.0 | 0.4021 | False | 0.8693 | 0.4625 | 0.2121 | 143 | 0.6562 |
| NYC | ST_CHP | tmax | 25.0 | 0.35 | False | 1.0 | 0.35 | 0.3268 | 343 | 0.742 |
| NYC | ST_CHP | tmin | 0.0 | 0.35 | False | 1.0 | 0.35 | 0.2576 | 143 | 0.7171 |
| NYC | CT_PEAKER | tmax | 25.0 | 0.0 | False | 0.3456 | 0.0 | 0.6622 | 333 | 0.0398 |
| NYC | CT_PEAKER | tmin | 0.0 | 0.0 | False | 0.2641 | 0.0 | 0.0235 | 142 | 0.06 |
| NYC | CC_REGULAR | tmax | 25.0 | 0.0 | False | 0.7129 | 0.0 | 0.51 | 343 | 0.7307 |
| NYC | CC_REGULAR | tmin | 0.0 | 0.0 | False | 0.705 | 0.0 | -0.0126 | 143 | 0.7799 |
| Long_Island | CT_PEAKER | tmax | 25.0 | 0.0 | False | 0.8177 | 0.0 | 0.6053 | 304 | 0.3142 |
| Long_Island | CT_PEAKER | tmin | 0.0 | 0.0 | False | 0.7274 | 0.0 | 0.3242 | 209 | 0.3848 |
| Long_Island | ST_GAS | tmax | 25.0 | 0.0 | False | 0.9828 | 0.0 | 0.6619 | 304 | 0.2009 |
| Long_Island | ST_GAS | tmin | 0.0 | 0.0 | False | 0.9419 | 0.0 | 0.3447 | 209 | 0.27 |
| Upstate_West | ST_GAS | tmax | 25.0 | 0.0 | False | 0.7795 | 0.0 | 0.2229 | 261 | 0.5627 |
| Upstate_West | ST_GAS | tmin | 0.0 | 0.0 | False | 0.7704 | 0.0 | 0.3756 | 290 | 0.5556 |
| Capital_Hudson | CC_REGULAR | tmax | 25.0 | 0.0 | False | 0.9183 | 0.0 | 0.4416 | 328 | 0.5035 |
| Capital_Hudson | CC_REGULAR | tmin | 0.0 | 0.0 | False | 0.7321 | 0.0 | -0.2363 | 348 | 0.6002 |
| Upstate_West | CT_PEAKER | tmax | 25.0 | 0.0 | False | 1.0 | 0.0 | -0.2924 | 69 | 0.6933 |
| Upstate_West | CT_PEAKER | tmin | 0.0 | 0.0 | False | 1.0 | 0.0 | 0.3088 | 101 | 0.5095 |
| Long_Island | CC_REGULAR | tmax | 25.0 | 0.0 | False | 0.8429 | 0.0 | 0.3213 | 303 | 0.5223 |
| Long_Island | CC_REGULAR | tmin | 0.0 | 0.0 | False | 0.7162 | 0.0 | 0.2729 | 209 | 0.52 |
| Upstate_West | CC_REGULAR | tmax | 25.0 | 0.0 | False | 0.3438 | 0.0 | 0.2703 | 224 | 0.1106 |
| Upstate_West | CC_REGULAR | tmin | 0.0 | 0.0 | False | 0.3835 | 0.0 | 0.335 | 263 | 0.1065 |
| Capital_Hudson | CC_CHP | tmax | 25.0 | 0.2572 | False | 0.6638 | 0.3875 | 0.4769 | 317 | 0.308 |
| Capital_Hudson | CC_CHP | tmin | 0.0 | 0.1938 | False | 0.5002 | 0.3875 | -0.1778 | 344 | 0.3743 |
| Upstate_West | CC_CHP | tmax | 25.0 | 0.2688 | False | 0.7332 | 0.3667 | 0.4294 | 270 | 0.4242 |
| Upstate_West | CC_CHP | tmin | 0.0 | 0.2607 | False | 0.711 | 0.3667 | 0.5289 | 284 | 0.39 |
| NYC | CC_CHP | tmax | 25.0 | 0.1195 | False | 0.3085 | 0.3875 | 0.1911 | 343 | 0.1924 |
| NYC | CC_CHP | tmin | 0.0 | 0.1024 | False | 0.2643 | 0.3875 | 0.2939 | 143 | 0.1924 |
| Long_Island | CT_CHP | tmax | 25.0 | 0.4207 | False | 0.9349 | 0.45 | 0.0398 | 294 | 0.9819 |
| Long_Island | CT_CHP | tmin | 0.0 | 0.4207 | False | 0.9349 | 0.45 | -0.0624 | 209 | 0.9815 |
