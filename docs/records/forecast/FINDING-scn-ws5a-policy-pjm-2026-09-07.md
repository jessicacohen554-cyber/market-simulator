# FINDING — SCN-WS5A-POLICY-PJM: ten Stage A-POLICY legs registered, and PJM's $45 RPS ceiling routes every clean-policy lever away from VRE

**Lane** SCN-WS5A-POLICY-PJM (coordinator) · **Model** Opus (`claude-opus-5`, rule 27
`[R-PUSH]`) · **Date** 2026-09-07 · **Branch**
`claude/scn-ws5a-policy-pjm-register-xqk1ej` · **Data profile** `pjm` ·
**Campaign** `scn-campaign-policy-2026-09-06`, kind `scenario`, `reference_case: REF` ·
**THE PIN** `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b` · **Control** the committed r2 REF
`results/scn-campaign-load-2026-09-06-r2/PJM/REF/`, key `67a786980ac38749`, solved at THE
PIN (G-CTRL form 4) · **Predecessors** `PRECOMMIT-scn-ws5a-policy-pjm-2026-09-06.md` +
its ADDENDUM 1, `9ef06cf8` (RESOLVE leg 6/13), `FINDING-scn-ws5a-load-pjm-2026-09-06.md`.

Every number in §§1–4 and §6 is read off a **committed artifact** — the ten legs'
`full_horizon_summary.json` + `run_config.json` and the r2 REF's — or is arithmetic on
two of them. **No leg was re-solved.** The one solve this session ran is the ruling-S15
bracket leg (§5a), and it is reported separately.

---

## 0. Bottom line

1. **THE REGISTRATION GAP IS CLOSED. ALL TEN SOLVED LEGS ARE REGISTERED**, each with its
   invariant FAILs declared in `frontend/data/hindcast/invariant-failures.json` in the same
   commit, and the `forecast-invariant-artifacts` audit is **EXIT 0 before and after**
   (163 → 173 sidecars, 190 → 212 declared FAILs). Ten legs — ≈**8.19 h** of PJM LP over
   50 solve-years — had been invisible for three desk refreshes to **everything that reads
   the registry**: the `forecast-invariant-artifacts` audit, the Forecast Run Explorer and
   Program Status, the registry parity sweep, and the desk's own board, which r#19 states it
   grades "by registered sidecar". **One correction to the framing this lane was handed:
   `collate_scenario_campaign.py` was *not* blind to them** — it reads
   `<root>/<iso>/<case>/full_horizon_summary.json` straight off disk, and PJM's ten summaries
   were committed, so the rollup could always see them. The gap is registry-side, and that is
   the precise thing this commit closes. Nothing blocked it; the coordinator step simply never
   ran.
2. **PJM'S $45 RPS ACP CEILING IS THE LANE'S RESULT, AND IT IS STRONGER THAN THE PRECOMMIT
   PREDICTED — BUT IN A DIFFERENT DIRECTION.** `rps_dual = 45.00` in **every** year of
   **every** one of the eleven runs (REF + ten legs). The build screen folds
   `max(EAC, rps_for_tech, clean_for_tech)` and its RPS leg is fuel-gated to wind and solar
   (`_RENEWABLE_NEW_FUELS`), so for those two a CES premium of $10/$20/$30 is strictly
   dominated by the $45 they already earn — **§5a.1 records this as a correction to the seam
   ruling S15 cites, and the gate is the reason the ceiling has the consequence it does.**
   The PRECOMMIT read the domination as "the ladder is nearly inert". **It is not.** The
   ladder is inert *on VRE entry* — `builds_renew_mw` is **+0.0 MW exactly** against REF in
   all three arms and all five years — while cutting 2030 CO2 by
   **−14.34 / −14.07 / −13.99 Mt (−3.1 %)**. The channel is entirely **gas-CC →
   gas-CC-CCS retrofit**, and it is **cap-bound at $10 already**: every rung converts within
   0.4 % of the **3,000 MW/yr** per-ISO cap in all three eligible years, so the +16.4 MW
   separation from $10 to $30 measures a **binding constraint, not an elasticity** — which
   this case set therefore does not identify. PJM's clean-policy response is a *retrofit*
   response, not a *build* response.
3. **RULING S15 EXECUTED, AND THE BRACKET LEG FALSIFIES THE OBVIOUS READING OF THE MASK.**
   The check the desk asked for: `rps_dual` = **45.00 in every year of every run**, and the
   premium legs' CES duals are $10/$20/$30 — **the mask binds in all five years on all three
   rungs**, so `CES-P60` was owed and is the session's only solve
   (`pjm-2026-2030-scn-campaign-policy-2026-09-06-ces-p60`, key `19999987cb623817`, at THE
   PIN, 5/5 years, FAIL set `{I7, I12}` = REF's). **At $60 — 33 % above the ceiling —
   `builds_renew_mw` is STILL +0.0 MW against REF in all five years.** What the extra premium
   buys is **+1,000 MW of nuclear at 2030**, the same 1,000 MW in the same year through the
   same economic-entry channel as the $50 `CES-T80` target, and −4.098 Mt more CO2 at 2030
   than `CES-P30`. The $45 ceiling was a real mask; it was **never the binding constraint on
   VRE entry on PJM**, and "lift the mask and PJM builds renewables" is now falsified by
   direct measurement (§5a).
4. **THE CES TARGET'S DEPLOYMENT CHANNEL IS NUCLEAR, NOT VRE — WHICH IS THE PRECOMMIT'S
   ONE OUTRIGHT MISS AND ITS MOST INSTRUCTIVE ONE.** P-12 predicted `CES-T80` would be the
   lane's only positive VRE-entry reading, because its $50 ACP clears the $45 RPS by $5.
   Measured: `builds_renew_mw` is **+0.0 MW** in every year, and the arm instead commissions
   **+1,000 MW of nuclear** at 2030 (economic entry; `builds_thermal_mw` 6,742.4 → 7,742.4,
   backstop unchanged). The mechanism is the same `max()`: for wind and solar the $50 ACP is
   an uplift of **+$5/MWh** over an attribute they already earn, while for nuclear —
   `RPS_ELIGIBLE_FUELS_BY_ISO["PJM"] = None` ⇒ wind+solar only, so nuclear is RPS-ineligible
   — it is an uplift of the **whole $50**. A ceiling that dominates the premium does not
   merely mute the lever; it **re-selects which technology the lever buys.**
5. **THE VOLUNTARY AXIS IS A PROOF-STRENGTH NULL ON PJM.** `VOL-MID` and `VOL-HI` are
   **bit-identical to each other in every reported trajectory field in all five years**,
   except `co2_mt` at 2029 (2×10⁻⁴ Mt) and 2030 (1×10⁻⁴ Mt) — every generation row, every
   capacity row, every price, identical. Against REF, Δ(wind+solar) is **0.0000 TWh** and
   every capacity row **+0.0 MW**. Doubling the voluntary volume from 216.1 to 360.6 TWh at
   2030 buys nothing, because both WTP ceilings ($4.50, $7.00) sit 6–10× under the $45 the
   eligible fleet already earns and there is no curtailment to recover
   (`neg_price_hour_frac = 0.0` in REF). P-14 and P-15 are confirmed **above** their bands.
6. **`CES-P20+VOL-HI` IS `CES-P20`, NOT `VOL-HI`** — the opposite of P-16. Its ΔCO2 tracks
   `CES-P20` to ≤0.013 Mt in every year and carries the same 6,745.7 MW of retrofit at 2030,
   while `VOL-HI` carries none. The composition's content is entirely the CES half; the
   voluntary half contributes nothing to it. The *conclusion* P-16 was drawn for survives —
   D-6 has no voluntary content on PJM — but its stated form is a miss.
7. **`CAP-STATE-TIGHT` IS MEASURABLY INERT ON PJM, AND IT IS OUT OF STAGE A** (owner ruling
   S17, desk card D-13). It is registered like the others, excluded from the gate scoring,
   the headline and the §5.1 rows, and reported in the **Stage-B seed** at §7. Max |ΔCO2|
   over 2027–2030 is **0.0070 Mt (0.002 %)**; 2026 is **byte-identical to REF in every
   trajectory field**. NEISO's loosening mechanism — a cap row replacing a live RGGI
   *adder* — **cannot operate on PJM**, because PJM's RGGI `price_adder` resolves to **0.0**
   in every REF year (PRECOMMIT §4.1): the row can only tighten or do nothing, and it does
   nothing.
8. **THE TWO CES INSTRUMENT FORMS ARE NOT INTERCHANGEABLE ON PJM, AND THE PRICE RATIO GOES
   THE WRONG WAY.** A **$10/MWh premium** pushes the CCS retrofit to its **3 GW/yr cap in all
   three eligible years** (2,998.6 / 5,998.4 / 8,994.4 MW against REF's 408.2 / 2,248.7 /
   2,248.7); a **$50/MWh target ACP** — five times the price, same 0.95-credited fuel, same
   ISO, same pin — adds **not one MW**, though it does raise existing-CCS *generation*
   14.805 → 17.275 TWh at 2030. Measured, not explained: the candidate causes are all `src/`
   questions outside this lane's regions (§5a.1a, routed §8.8).
9. **THREE OF THIRTEEN CHARTERED LEGS WERE NEVER SOLVED** — `CARB-LO`, `CARB-MID`,
   `CARB-HI`, 15 solve-years. **PJM therefore has no Stage-A carbon reading**, and
   predictions P-1 through P-8 are UNSCORABLE. The one carbon-bearing leg that exists,
   `CARB-MID+LOAD-HI`, carries the load axis by construction and cannot separate them.
   Routed (§8.1), not absorbed.
10. **Gate tally: 8 PASS, 1 VACUOUS, 4 UNSCORABLE, 0 KILL.** The four unscorable gates
   (G4, G7, G10's dual half, G12's read-out half) all fail for **one** reason: **no PJM leg
   committed a duals artifact**, and the LP caches are gone. MISO's lane committed
   `duals.json` beside each leg; PJM's sub-lanes did not. Routed (§8.2).

---

## 1. Phase 0 as committed — 13 of 13 survived, and it is not re-derived here

The PRECOMMIT's phase 0 stands **as written** and this session re-derives none of it. What is
re-checked, and only because it is free:

- **Every one of the ten solved legs carries the cache key the PRECOMMIT §2 table declared,
  to the digit** — `a116292f8cdb8695` / `50da3e27a4298ba2` / `664bf9cf053e7c6f` /
  `dccf5c2aa49ded42` / `ba6202d729de037d` / `3259a892ac876177` / `f4aa44cf47216299` /
  `6afe42c8d8bef012` / `cbdafe9626b105a1` / `c0b963f080625cb0`. Each leg's `run_config.json`
  records `git.basis_sha = bdfb3095e9fa0cd2bec3f4e843f320b42588c72b`, `dirty: false`. The
  key chain the PRECOMMIT resolved pre-solve is the chain the solves used.
- **The PRECOMMIT §6.1's REF-side facts reproduce exactly** from the committed r2 REF: `rps_dual` 45.00 in
  every year; CO2 373.1949 / 393.6752 / 417.3805 / 429.9513 / 463.0394 Mt; `unserved_mwh` 0
  in every year (I3 PASS).
- **The PRECOMMIT §6.3's REF credited share reproduces to four decimals** — nuclear + wind + solar + hydro
  + 0.95 × `gas_cc_ccs` over the resolved demand: **0.3686 / 0.3462 / 0.3270 / 0.3263 /
  0.3106**, and the escape volumes **167.117 / 227.136 / 290.944 / 341.312 / 414.773 TWh**
  against the PRECOMMIT's 167.1 / 227.1 / 290.9 / 341.3 / 414.8.

Three chartered legs (`CARB-LO`, `CARB-MID`, `CARB-HI`) were never solved. Phase 0 did not
kill them — they are simply absent from the artifact record.

---

## 2. Per-case deltas vs REF

**The leakage line cannot be reported, and that is a finding rather than an omission.**
`import_co2_mt_reported` is **`null` in every PJM artifact this campaign produced, the REF
included** — the field exists in the schema (WS-0 G-E3) but carries no value on PJM. Ruling
S11's duty to put it beside every CO2 number is therefore **not dischargeable here**. What
each table below carries instead is the **import generation** row, in TWh, beside every CO2
number: it is the physical quantity the missing line would be computed from, it is never
netted into the CO2 column, and it is not a substitute for the number the ruling asks for.
Routed at §8.3.

### 2.0 REF levels (the control, key `67a786980ac38749`, at THE PIN)

| year | CO2 Mt | import gen TWh | `import_co2_mt_reported` | LW $/MWh | max $/MWh | h≥500 | RM % | `rps_dual` |
|---|---|---|---|---|---|---|---|---|
| 2026 | 373.1949 | 0.279 | **`null`** | 41.711 | 64.9 | 0 | -9.466 | 45.00 |
| 2027 | 393.6752 | 0.535 | **`null`** | 42.193 | 219.9 | 0 | -11.625 | 45.00 |
| 2028 | 417.3805 | 4.938 | **`null`** | 55.285 | 2000.0 | 21 | -15.961 | 45.00 |
| 2029 | 429.9513 | 7.660 | **`null`** | 53.295 | 2000.0 | 8 | -15.631 | 45.00 |
| 2030 | 463.0394 | 13.707 | **`null`** | 80.789 | 2000.0 | 139 | -16.346 | 45.00 |

### 2.1 `CES-P10` — key `dccf5c2aa49ded42`

| year | CO2 Mt | ΔCO2 Mt | ΔCO2 % | import TWh | Δimport TWh | imp CO2 Mt | ΔLW $/MWh | ΔRM pp | Δbuild ren / th / stg MW | Δretire MW |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 373.1984 | +0.0035 | +0.001 | 0.279 | +0.0000 | `null` | +0.000 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2027 | 393.6661 | -0.0091 | -0.002 | 0.535 | +0.0000 | `null` | +0.001 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2028 | 411.4766 | -5.9039 | -1.415 | 4.911 | -0.0270 | `null` | -0.034 | +0.296 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2029 | 422.1307 | -7.8206 | -1.819 | 7.161 | -0.4993 | `null` | -0.272 | +0.409 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2030 | 448.7010 | -14.3384 | -3.097 | 13.552 | -0.1551 | `null` | -0.151 | +0.702 | +0.0 / +0.0 / +0.0 | +0.0 |

### 2.2 `CES-P20` — key `ba6202d729de037d`

| year | CO2 Mt | ΔCO2 Mt | ΔCO2 % | import TWh | Δimport TWh | imp CO2 Mt | ΔLW $/MWh | ΔRM pp | Δbuild ren / th / stg MW | Δretire MW |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 373.2173 | +0.0224 | +0.006 | 0.263 | -0.0160 | `null` | +0.000 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2027 | 393.6651 | -0.0101 | -0.003 | 0.535 | +0.0000 | `null` | +0.000 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2028 | 411.4638 | -5.9167 | -1.418 | 4.905 | -0.0321 | `null` | -0.040 | +0.298 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2029 | 422.3311 | -7.6202 | -1.772 | 7.153 | -0.5073 | `null` | -0.276 | +0.411 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2030 | 448.9696 | -14.0698 | -3.039 | 13.542 | -0.1649 | `null` | -0.159 | +0.703 | +0.0 / +0.0 / +0.0 | +0.0 |

### 2.3 `CES-P30` — key `f4aa44cf47216299`

| year | CO2 Mt | ΔCO2 Mt | ΔCO2 % | import TWh | Δimport TWh | imp CO2 Mt | ΔLW $/MWh | ΔRM pp | Δbuild ren / th / stg MW | Δretire MW |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 373.1943 | -0.0006 | -0.000 | 0.279 | +0.0000 | `null` | +0.001 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2027 | 393.6655 | -0.0097 | -0.002 | 0.535 | +0.0000 | `null` | +0.000 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2028 | 411.4733 | -5.9072 | -1.415 | 4.909 | -0.0289 | `null` | -0.036 | +0.298 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2029 | 422.3822 | -7.5691 | -1.760 | 7.140 | -0.5198 | `null` | -0.281 | +0.411 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2030 | 449.0537 | -13.9857 | -3.020 | 13.526 | -0.1806 | `null` | -0.174 | +0.703 | +0.0 / +0.0 / +0.0 | +0.0 |

### 2.4 `CES-T80` — key `6afe42c8d8bef012`

| year | CO2 Mt | ΔCO2 Mt | ΔCO2 % | import TWh | Δimport TWh | imp CO2 Mt | ΔLW $/MWh | ΔRM pp | Δbuild ren / th / stg MW | Δretire MW |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 373.2098 | +0.0149 | +0.004 | 0.264 | -0.0151 | `null` | -0.001 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2027 | 393.6693 | -0.0059 | -0.001 | 0.535 | +0.0000 | `null` | -0.003 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2028 | 416.9112 | -0.4693 | -0.112 | 4.923 | -0.0145 | `null` | -0.033 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2029 | 428.0077 | -1.9436 | -0.452 | 7.173 | -0.4868 | `null` | -0.270 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2030 | 457.9219 | -5.1175 | -1.105 | 12.915 | -0.7919 | `null` | -4.217 | +0.471 | +0.0 / +1000.0 / +0.0 | +0.0 |

### 2.5 `VOL-MID` — key `c0b963f080625cb0`

| year | CO2 Mt | ΔCO2 Mt | ΔCO2 % | import TWh | Δimport TWh | imp CO2 Mt | ΔLW $/MWh | ΔRM pp | Δbuild ren / th / stg MW | Δretire MW |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 373.2097 | +0.0148 | +0.004 | 0.264 | -0.0151 | `null` | -0.001 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2027 | 393.6692 | -0.0060 | -0.002 | 0.535 | +0.0000 | `null` | -0.003 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2028 | 417.3770 | -0.0035 | -0.001 | 4.954 | +0.0165 | `null` | +0.000 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2029 | 429.9523 | +0.0010 | +0.000 | 7.660 | +0.0000 | `null` | -0.001 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2030 | 463.0409 | +0.0015 | +0.000 | 13.707 | +0.0000 | `null` | +0.001 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |

### 2.6 `VOL-HI` — key `cbdafe9626b105a1`

| year | CO2 Mt | ΔCO2 Mt | ΔCO2 % | import TWh | Δimport TWh | imp CO2 Mt | ΔLW $/MWh | ΔRM pp | Δbuild ren / th / stg MW | Δretire MW |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 373.2097 | +0.0148 | +0.004 | 0.264 | -0.0151 | `null` | -0.001 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2027 | 393.6692 | -0.0060 | -0.002 | 0.535 | +0.0000 | `null` | -0.003 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2028 | 417.3770 | -0.0035 | -0.001 | 4.954 | +0.0165 | `null` | +0.000 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2029 | 429.9525 | +0.0012 | +0.000 | 7.660 | +0.0000 | `null` | -0.001 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2030 | 463.0408 | +0.0014 | +0.000 | 13.707 | +0.0000 | `null` | +0.001 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |

### 2.7 `CES-P20+VOL-HI` — key `3259a892ac876177`

| year | CO2 Mt | ΔCO2 Mt | ΔCO2 % | import TWh | Δimport TWh | imp CO2 Mt | ΔLW $/MWh | ΔRM pp | Δbuild ren / th / stg MW | Δretire MW |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 373.2117 | +0.0168 | +0.005 | 0.264 | -0.0151 | `null` | +0.000 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2027 | 393.6705 | -0.0047 | -0.001 | 0.535 | +0.0000 | `null` | -0.003 | +0.000 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2028 | 411.4637 | -5.9168 | -1.418 | 4.905 | -0.0321 | `null` | -0.040 | +0.298 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2029 | 422.3188 | -7.6325 | -1.775 | 7.160 | -0.5001 | `null` | -0.274 | +0.411 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2030 | 448.9699 | -14.0695 | -3.039 | 13.542 | -0.1649 | `null` | -0.157 | +0.703 | +0.0 / +0.0 / +0.0 | +0.0 |

### 2.8 `CARB-MID+LOAD-HI` — key `664bf9cf053e7c6f`

| year | CO2 Mt | ΔCO2 Mt | ΔCO2 % | import TWh | Δimport TWh | imp CO2 Mt | ΔLW $/MWh | ΔRM pp | Δbuild ren / th / stg MW | Δretire MW |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 410.5525 | +37.3576 | +10.010 | 3.459 | +3.1807 | `null` | +11.407 | -7.149 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2027 | 455.2234 | +61.5482 | +15.634 | 10.319 | +9.7840 | `null` | +72.635 | -10.277 | +0.0 / -842.8 / +1600.0 | +0.0 |
| 2028 | 498.2889 | +80.9084 | +19.385 | 23.944 | +19.0064 | `null` | +318.710 | -12.137 | +0.0 / +842.8 / +1600.0 | +0.0 |
| 2029 | 539.4261 | +109.4748 | +25.462 | 31.976 | +24.3163 | `null` | +554.198 | -14.467 | -842.8 / +0.0 / +0.0 | +0.0 |
| 2030 | 589.9690 | +126.9296 | +27.412 | 35.040 | +21.3333 | `null` | +1026.196 | -16.630 | +842.8 / +1000.0 / +0.0 | +0.0 |

### 2.9 `ALL-CLEAN` — key `a116292f8cdb8695`

| year | CO2 Mt | ΔCO2 Mt | ΔCO2 % | import TWh | Δimport TWh | imp CO2 Mt | ΔLW $/MWh | ΔRM pp | Δbuild ren / th / stg MW | Δretire MW |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 410.5625 | +37.3676 | +10.013 | 3.462 | +3.1828 | `null` | +11.407 | -7.149 | +0.0 / +0.0 / +0.0 | +0.0 |
| 2027 | 455.2288 | +61.5536 | +15.636 | 10.319 | +9.7840 | `null` | +72.632 | -10.277 | +0.0 / -842.8 / +1600.0 | +0.0 |
| 2028 | 498.2871 | +80.9066 | +19.384 | 23.944 | +19.0064 | `null` | +318.710 | -12.137 | +0.0 / +842.8 / +1600.0 | +0.0 |
| 2029 | 535.6515 | +105.7002 | +24.584 | 31.600 | +23.9398 | `null` | +532.100 | -14.100 | -1842.8 / +1000.0 / +0.0 | +0.0 |
| 2030 | 589.9690 | +126.9296 | +27.412 | 35.040 | +21.3333 | `null` | +1026.196 | -16.630 | +1842.8 / +0.0 / +0.0 | +0.0 |

### 2.10 The one mechanism behind every CES-premium number: the CCS retrofit

Δ capacity, MW, vs REF — the **only** capacity rows that move in the three premium arms and
in `CES-P20+VOL-HI`, in any year:

| arm | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| `CES-P10` gas_cc → gas_cc_ccs | 0 | 0 | **2,580.4** | **3,738.4** | **6,732.5** |
| `CES-P20` | 0 | 0 | **2,590.3** | **3,749.7** | **6,745.7** |
| `CES-P30` | 0 | 0 | **2,590.7** | **3,749.6** | **6,748.9** |
| `CES-P20+VOL-HI` | 0 | 0 | **2,590.4** | **3,749.7** | **6,745.7** |

`builds_renew_mw`, `builds_thermal_mw`, `builds_storage_mw`, `retire_mw` and every
zero-carbon capacity row are **+0.0 MW** against REF in all four arms and all five years.
The retrofit is a *conversion*, so `total_cap_mw` is byte-identical to REF too — yet the
reserve margin rises **+0.30 / +0.41 / +0.70 pp** at 2028/2029/2030 with `peak_demand_mw`
unchanged, i.e. the accredited firm capacity of a converted MW differs from that of its
unconverted host. Reported as measured; the accreditation seam behind it is not this lane's
region.

Δ generation, TWh, `CES-P20` vs REF (the ladder's other rungs agree to <0.5 TWh):

| year | gas_cc | gas_cc_ccs | coal | gas_ct | import |
|---|---|---|---|---|---|
| 2028 | −20.881 | **+21.077** | −0.107 | −0.017 | −0.032 |
| 2029 | −31.758 | **+33.844** | −0.303 | −1.073 | −0.507 |
| 2030 | −52.387 | **+54.275** | −0.009 | −1.640 | −0.165 |

**Every rung of the ladder is at the 3 GW/yr per-ISO retrofit cap in every eligible year, and
that is the whole reason the ladder is flat.** In absolute `capacity_by_fuel_mw['gas_cc_ccs']`,
`CES-P20` runs **2,998.6 / 5,998.4 / 8,994.4 MW** at 2028/2029/2030 — annual increments of
**2,998.6 / 2,999.8 / 2,996.0 MW** against the 3,000 MW/yr cap, and `CES-P10` and `CES-P30`
give **2,988.6 / 2,998.5 / 2,994.1** and **2,998.9 / 2,999.4 / 2,999.3** — every rung, every
year, within 0.4 % of the cap — where REF runs
**408.2 / 2,248.7 / 2,248.7** (increments 408.2 / 1,840.5 / 0). A $10 premium already
saturates the cap, so $20 and $30 have nowhere to go: the +16.4 MW separation over the ladder
is not a weak elasticity, it is a **binding constraint**, and the true elasticity is not
identified by this case set at all. `ccs_retrofit_available_year` = 2028 is why 2026–2027 are
untouched.

### 2.11 `CES-T80` and `ALL-CLEAN` — the target's channel is nuclear

`CES-T80` moves **no** capacity row until 2030, when it commissions **+1,000 MW nuclear**
(`capacity_by_fuel_mw['nuclear']` +1,000.0; `builds_thermal_mw` 6,742.4 → 7,742.4 with
`builds_thermal_backstop_mw` unchanged at 5,056.8, so it is **economic entry**, 1,685.6 →
2,685.6). Generation follows: nuclear **+8.278 TWh**, gas_ct **−7.335**, gas_st **−0.477**,
gas_cc_ccs **+2.470** (existing CCS running harder, no new retrofit). `builds_renew_mw` is
**+0.0 MW in every year.**

Differencing the two high-load arms isolates the target + voluntary rows under high load:

**`ALL-CLEAN` − `CARB-MID+LOAD-HI`** (identical demand, identical carbon path):

| year | ΔCO2 Mt | ΔLW $/MWh | ΔRM pp | Δ capacity | Δ builds ren / th |
|---|---|---|---|---|---|
| 2026 | +0.0100 | +0.000 | +0.000 | — | 0 / 0 |
| 2027 | +0.0054 | −0.003 | +0.000 | — | 0 / 0 |
| 2028 | −0.0018 | +0.000 | +0.000 | — | 0 / 0 |
| 2029 | **−3.7746** | **−22.098** | **+0.367** | **nuclear +1,000.0, solar −1,000.0** | −1,000 / +1,000 |
| 2030 | **+0.0000** | +0.000 | +0.000 | — | +1,000 / −1,000 |

So the CES target's entire content under high load is a **1,000 MW nuclear-for-solar swap in
2029**, worth −3.77 Mt and −$22.10/MWh, which the 2030 build mix unwinds to an exactly zero
net capacity difference. Both this and `CES-T80`'s standalone reading say the same thing: on
PJM the target buys firm clean capacity, not VRE.

### 2.12 Both nettings (ruling S11 / gate G9)

Counts-toward is the **headline** (it is what the row as built computes); additional is
reported beside it. `credited = nuclear + wind + solar + hydro + 0.95·gas_cc_ccs`; `D` is the
resolved demand of the arm's own path (PRECOMMIT §3.1); `V` is the arm's voluntary volume;
`target(y)` = 0.5500 / 0.5778 / 0.6056 / 0.6333 / 0.6611. Negative = short of the target,
i.e. **escape**.

**`ALL-CLEAN`** (high demand path, `V` = `ALL-CLEAN` row):

| year | D TWh | credited TWh | credited share | target·D TWh | **counts-toward** `cred − target·D` | V TWh | **additional** `cred − V − target·D` |
|---|---|---|---|---|---|---|---|
| 2026 | 997.309 | 339.552 | 0.3405 | 548.520 | **−208.967** | 158.420 | **−367.387** |
| 2027 | 1,104.761 | 339.552 | 0.3074 | 638.331 | **−298.778** | 213.831 | **−512.609** |
| 2028 | 1,223.790 | 361.385 | 0.2953 | 741.127 | **−379.742** | 270.168 | **−649.910** |
| 2029 | 1,355.644 | 400.572 | 0.2955 | 858.529 | **−457.957** | 327.532 | **−785.489** |
| 2030 | 1,501.704 | 428.030 | 0.2850 | 992.777 | **−564.746** | 386.031 | **−950.777** |

**`CES-P20+VOL-HI`** (mid demand path, `V` = `VOL-HI` row). This arm carries **no target row**
— it is a premium leg — so the columns below are the same arithmetic applied counterfactually,
reported because G9 asks for both nettings on both combined legs, and flagged as
counterfactual rather than quoted as a compliance position:

| year | D TWh | credited TWh | credited share | target·D TWh | counts-toward | V TWh | additional |
|---|---|---|---|---|---|---|---|
| 2026 | 921.217 | 339.552 | 0.3686 | 506.669 | −167.117 | 152.332 | −319.449 |
| 2027 | 980.769 | 339.552 | 0.3462 | 566.688 | −227.136 | 203.911 | −431.047 |
| 2028 | 1,044.171 | 361.429 | 0.3461 | 632.350 | −270.921 | 255.799 | −526.720 |
| 2029 | 1,111.672 | 394.861 | 0.3552 | 704.022 | −309.160 | 308.014 | −617.174 |
| 2030 | 1,183.536 | 419.224 | 0.3542 | 782.436 | −363.212 | 360.578 | −723.790 |

**Both nettings agree on the regime in every year of both arms — escape — and differ only by
`V`.** The choice of netting therefore changes no dispatch, no build and no CO2 number on
PJM; it changes only the escape volume, and hence the ACP payment, by exactly `V` — and, at the
committed $50/MWh ACP, that is not a small difference: `ALL-CLEAN`'s implied escape payment
is **$10.45 B/yr (2026) → $28.24 B/yr (2030)** on the counts-toward netting and **$18.37 →
$47.54 B/yr** on the additional netting, the gap being `V × $50` exactly. Neither is asserted
as the answer.

---

## 3. Gate verdicts — the NINE Stage-A legs (`CAP-STATE-TIGHT` excluded per S17, §7)

A gate may kill an arm; it may never promote one. **No arm is killed.**

| gate | verdict | measurement |
|---|---|---|
| **G1** | **PASS** | Already PASS pre-solve; re-confirmed post-solve at zero cost — all ten solved legs carry the exact key the PRECOMMIT §2 table declared, and every `run_config.json` records `git.basis_sha = bdfb3095…`, `dirty: false`. |
| **G1a** | **PASS on its only scorable clause; UNSCORABLE on the carbon clause** | The carbon-only arms were never solved, so "every carbon-bearing arm's 2026 is bit-identical to REF" has no object (the one carbon-bearing leg solved, `CARB-MID+LOAD-HI`, raises 2026 load by 14,335.7 MW of peak by construction). The clause that **is** scorable — `CAP-STATE-TIGHT` 2026 — passes **strictly**: byte-identical to REF in *every* trajectory field. Disclosure on the other seven: 2026 differs from REF by ≤0.023 Mt (≤6×10⁻⁵ relative) with **every capacity row identical**, and `CES-T80`, `VOL-MID` and `VOL-HI` produce the *same alternate optimum bit-for-bit* (coal +18,425.2 MWh, gas_cc −8,145.1, import −15,130.3) — LP degeneracy, not a 2026 policy response. |
| **G2** | **PASS** | REF carries the adequacy state the gate asserts: `unserved_mwh` **0 in every year** (I3 PASS), reserve margin **−9.466 % → −16.346 %**, FAIL set **exactly {I7, I12}**, `hours_ge_500` **0 → 139**, `max_hourly_price` at the **$2,000** cap from 2028. Its four declared consequences stand and are carried into every reading above: deltas campaign-grade in all five years; **price levels from 2028 disclosure-only**; deployment responses a **lower bound**; CO2 *levels* not quotable against the board key. |
| **G3** | **PASS** | Footprint confined in every arm. CES-premium arms: gas_cc ↔ gas_cc_ccs plus fossil/import dispatch only — **no zero-carbon capacity row moves at all**. CES-target arms: the eligible/ineligible split plus the one nuclear entry the row buys. Voluntary arms: nothing moves. The import line moves only in the arms that move dispatch, is reported (§2), and is never counted as a confinement failure. |
| **G4** | **UNSCORABLE** | The gate is a **dual identity** ($50.0000 exactly where the target is unmet) and **no PJM leg committed a duals artifact**; the LP caches are gone, so it cannot be recovered without a re-solve. What *is* measurable supports the regime the gate assumes: §2.12 shows the target unmet in all five years by 208.967 → 564.746 TWh. Routed §8.2. |
| **G5** | **PASS** | Eight arms carry REF's FAIL set **exactly** — `{I7, I12}`, I14 PASS, all twelve others PASS. The two high-load arms add **I3 FAIL + I14 WARN**, which is the load axis those cases exist to move and which G6 exempts by name. No arm gains a FAIL outside its own target mechanism. |
| **G6** | **PASS, strictly** | REF has zero unserved, so the gate binds strictly on the seven non-load policy arms **and** on `CAP-STATE-TIGHT`: all eight have **I3 PASS**. `CARB-MID+LOAD-HI` and `ALL-CLEAN` gain I3 (2030: 5,747 h / 63,687.9 GWh and 5,728 h / 63,687.9 GWh, 4.24 % of load) — the exemption the gate wrote for itself before the solves ran. |
| **G7** | **UNSCORABLE** | Same cause as G4 — the gate is a per-arm dual bound and no dual is carried. The §3.2 escape arithmetic it rests on reproduces from the committed volumes, and the LP now confirms the regime's *consequence*: zero eligible recovery (below). Routed §8.2. |
| **G8** | **VACUOUS — and it must not be read as a pass this lane earned** | The gate asks that curtailment fall before thermal is displaced. REF's `neg_price_hour_frac` is **0.0000 in every year** and Δ(wind + solar generation) is **0.0000 TWh** in every voluntary arm and year, so **there is no curtailment on PJM for the row to recover** and the gate has no object. Recorded exactly as NEISO recorded its own vacuous G8. |
| **G9** | **PASS** | Both nettings reported for `CES-P20+VOL-HI` and `ALL-CLEAN`, counts-toward as the headline, additional beside it, with the ACP-implied cost of the choice stated (§2.12). Neither asserted as the answer. |
| **G10** | *(cap arm — out of Stage A per S17; carried at §7)* | 2026-no-row half **PASS** (byte-identical). Binding-year dual half **UNSCORABLE**: no `co2_cap_price` is carried. |
| **G11** | **PASS** | Verified against the committed configs, not merely pre-solve: `CAP-STATE-TIGHT` differs from REF in exactly `{mass_cap_enabled, mass_cap_program, mass_cap_tons_by_year}`, and `carbon_price_path` stays `zero`; the carbon-bearing arms carry `carbon_price_path: mid` and **no** mass-cap field. **No leg carries both instruments.** |
| **G12** | *(cap arm — §7)* | Footprint half **PASS** (nothing moves anywhere). Price-vs-quantity read-out half **UNSCORABLE twice over**: no cap dual is carried, *and* there is no `CARB-MID` / `CARB-HI` leg to compare it against (§8.1). |

**Tally: 8 PASS, 1 VACUOUS, 4 UNSCORABLE (G4, G7, G10-dual, G12-readout), 0 KILL.**
Every unscorable verdict has the same single cause and one fix (§8.2).

---

## 4. The deployment response vs REF

| arm | `builds_renew_mw` | `builds_thermal_mw` | `builds_storage_mw` | `retire_mw` | net capacity move |
|---|---|---|---|---|---|
| `CES-P10` / `CES-P20` / `CES-P30` | **+0.0 every year** | +0.0 | +0.0 | +0.0 | 2.58 / 3.74 / 6.73 GW gas_cc → gas_cc_ccs (2028/29/30) |
| `CES-T80` | **+0.0 every year** | +1,000.0 at 2030 (economic) | +0.0 | +0.0 | **+1,000 MW nuclear** at 2030 |
| `VOL-MID` / `VOL-HI` | **+0.0 every year** | +0.0 | +0.0 | +0.0 | **none — every row identical to REF** |
| `CES-P20+VOL-HI` | **+0.0 every year** | +0.0 | +0.0 | +0.0 | identical to `CES-P20` (6.75 GW retrofit at 2030) |
| `CARB-MID+LOAD-HI` | 0 / 0 / 0 / −842.8 / +842.8 | −842.8 / +842.8 / 0 / +1,000 | **+1,600 at 2027 and 2028** | +0.0 | load-driven; +1.0 GW total capacity at 2030 |
| `ALL-CLEAN` | 0 / 0 / 0 / −1,842.8 / +1,842.8 | −842.8 / +842.8 / +1,000 / −1,000 | **+1,600 at 2027 and 2028** | +0.0 | as above, plus the 2029 nuclear-for-solar swap |

**Three statements the table supports and the campaign should carry.**

1. **No clean-policy lever on PJM commissions a single MW of wind or solar.** Not the
   premium at $10, $20, $30 **or $60**; not the target at a $50 ACP; not the voluntary row at
   $4.50 or $7.00; not any composition of them. `builds_renew_mw` is **+0.0 MW against REF in
   all five years of all eight pure-policy arms**, the ruling-S15 bracket leg included — which
   is the strongest form of the statement, because $60 clears the $45 ceiling that was the
   proposed obstruction (§5a.3). The two arms where `builds_renew_mw` moves at all
   are the two that raise **load**, and there it moves in both directions and nets to zero
   over 2029–2030.
2. **The levers that do buy something buy firm clean capacity or a retrofit.** 6.75 GW of CCS
   conversion (premium, cap-bound from $10 upward) and 1.0 GW of nuclear (target at $50, and
   the premium once it clears $45). Both are technologies whose attribute
   revenue is *not* already pinned at $45 — gas_cc_ccs is credited 0.95 by the CES row and 0
   by the RPS; nuclear is credited 1.0 and 0. That is the whole mechanism.
3. **The deployment response is a lower bound (G2c).** The reserve-margin backstop is at work
   in every year of every arm, and the retirement screen retires nothing extra anywhere, so
   these are floors on what a well-supplied PJM would build, not estimates of it.

### 4.1 P-18's re-measurement — the confound is inert, but leg 6's *reason* does not transfer

The charter required re-measuring the D67-ARM / D81 confound on any case that moves the
reserve margin, and `CARB-MID+LOAD-HI` / `ALL-CLEAN` move it from −16.3 % to **−32.98 %**.
Two separate statements, both true:

- **The confound cannot enter any delta this lane reports.** D67-ARM and D81 are LIVE at THE
  PIN, and the control is the r2 REF **solved at THE PIN itself** — so the published PJM
  Reliability Requirement is the operand on *both* sides of every difference above (G-CTRL
  form 4, PRECOMMIT §5.1). This is a structural argument and it does not depend on any
  measurement.
- **Leg 6's empirical reason — "inert *because* the backstop is rate-clamped" — does NOT
  transfer to the high-load arms, and P-18's prediction that it would is a MISS.** The
  backstop is measurably *not* clamped identically at −33 %:
  `builds_thermal_backstop_mw` moves REF **3,056.8 → 2,214.0 MW** at 2029 and
  **5,056.8 → 5,899.6 MW** at 2030 between REF and the high-load arms, with economic entry
  moving the other way at 2029 (4,000.0 → 4,842.8). A future session must not quote leg 6's
  clamp reading as a general PJM property; the form-4 argument is what carries the
  confound's inertness here, and it is the stronger of the two.

---

## 5. Predictions scored at full magnitude

Scored **as written in the PRECOMMIT**, including the misses and including the four the
missing carbon legs made unscorable.

| # | claim | verdict | measured |
|---|---|---|---|
| **P-1** | `CARB-MID` 2027 ΔCO2 ∈ [−11.0, −16.0] Mt, Δprice ∈ [+1.8, +2.5] | **UNSCORABLE** | `CARB-MID` never solved (§8.1). |
| **P-2** | all three carbon arms' 2026 bit-identical to REF | **UNSCORABLE** | no carbon-only arm exists. |
| **P-3** | CO2 falls / price rises monotonically REF → LO → MID → HI | **UNSCORABLE** | ladder never solved. |
| **P-4** | mechanism is coal→gas-CC, every zero-carbon class exactly 0.0000 TWh | **UNSCORABLE** | ladder never solved. |
| **P-5** | `CARB-LO` 2027 −5 to −10 Mt; `CARB-HI` 2027 −22 to −34 Mt | **UNSCORABLE** | ladder never solved. |
| **P-6** | ΔCO2 grows 2027 → 2030; `CARB-HI` 2030 −60 to −110 Mt | **UNSCORABLE** | ladder never solved. |
| **P-7** | `gas_cc_ccs` rises in carbon arms from 2028; the 3 GW/yr cap binds | **UNSCORABLE as stated**, but its *mechanism* is confirmed on a different axis | the cap does bind — but on the **CES** lever, not the carbon one, and in **every** eligible year rather than just at the top: all three premium rungs convert within **0.4 % of the 3,000 MW/yr cap** in 2028, 2029 and 2030 (§2.10). The one carbon-bearing arm that exists does the same (2,991.6 / 5,989.8 / 8,989.8 MW absolute), so the carbon half of P-7 is *consistent* with what was measured — it just cannot be separated from the load half in that arm. |
| **P-8** | `import_co2_mt_reported` rises in every carbon arm, reaching +1.5 to +4.0 Mt at `CARB-HI` 2030 | **UNSCORABLE, twice** | no carbon arm, **and** the field is `null` in every PJM artifact (§2, §8.3). Import *generation* falls in every CES arm (−0.03 to −0.51 TWh), i.e. the opposite direction from the carbon prediction, which is expected: a CES premium makes in-ISO clean output cheaper rather than in-ISO fossil dearer. |
| **P-9** | P10/P20/P30 commission renewables within ±5 % of REF's, and are "essentially identical to REF" | **SPLIT — letter HIT, headline MISS** | The letter is confirmed **far inside** its band: `builds_renew_mw` is **+0.0 MW exactly** vs REF in all three arms and all five years, not merely ±5 %. The headline is **wrong**: the arms are not essentially identical to REF — 2030 CO2 falls **−14.34 / −14.07 / −13.99 Mt (−3.10 / −3.04 / −3.02 %)** through 6.7 GW of CCS retrofit. The PRECOMMIT reasoned correctly from the $45 ceiling to the *VRE* null and then over-generalised it to the arm. |
| **P-10** | any P10→P30 separation shows up as `gas_cc_ccs` rising with the premium from 2028, and/or nuclear entry; nuclear `retire_mw` stays 0 | **HIT — the sharpest call in the lane** | Separation appears **exactly** there and **exactly** from 2028: gas_cc_ccs 2,580.4 → 2,590.3 → 2,590.7 MW (2028), 6,732.5 → 6,745.7 → 6,748.9 MW (2030) — monotone in the premium. Nuclear entry 0 and nuclear `retire_mw` 0 in all three, as predicted. The "clean null" branch did not occur: the channel is large in level (6.7 GW) and flat in the ladder (+16.4 MW over $10 → $30). |
| **P-11** | `CES-T80` in the escape regime in all five years; REF credited share 0.3686 / 0.3462 / 0.3270 / 0.3263 / 0.3106; escape ≈167.1 / 227.1 / 290.9 / 341.3 / 414.8 TWh | **HIT on the arithmetic; the dual leg UNSCORABLE** | Credited share reproduces to **four decimals** and escape to **167.117 / 227.136 / 290.944 / 341.312 / 414.773 TWh** — three-decimal agreement. The dual = ACP claim is G4 and is unscorable (§8.2). |
| **P-12** | `CES-T80` is the lane's **one** positive VRE-entry reading; it commissions more renewables than REF and than any premium arm | **MISS, at full magnitude** | `builds_renew_mw` is **+0.0 MW vs REF in every year**. The arm's deployment response is **+1,000 MW of nuclear at 2030**, and `ALL-CLEAN` − `CARB-MID+LOAD-HI` shows the same row buying **+1,000 MW nuclear for −1,000 MW solar** at 2029. The prediction's premise (a $50 ACP over a $45 RPS is a +$5/MWh VRE uplift) was right; its conclusion ignored that the *same* $50 is a **+$50** uplift for RPS-ineligible clean fuels, so the entry screen re-selects the technology instead of buying more of the same one. **This is the lane's most consequential result and it arrived as a failed prediction.** |
| **P-13** | voluntary dual = $4.50 (`VOL-MID`) / $7.00 (others) exactly, escape = the §3.2 shortfall | **UNSCORABLE directly; corroborated indirectly** | No dual is carried (G7, §8.2). The regime's consequence is confirmed: zero eligible recovery (P-15) is exactly what an escaping row predicts, and `VOL-MID` ≡ `VOL-HI` (P-14) is what two *escaping* rows at different ceilings must produce. |
| **P-14** | `retire_mw`, all three build rows and `capacity_by_fuel_mw` identical to REF to 0.1 MW in all five years of `VOL-MID` and `VOL-HI` | **HIT — above the claimed strength** | Identical to **0.0 MW**, every row, both arms, all five years. Stronger still: `VOL-MID` and `VOL-HI` are **bit-identical to each other in every reported trajectory field** in all five years bar `co2_mt` at 2029 (429.9523 vs 429.9525) and 2030 (463.0409 vs 463.0408) — differences of 2×10⁻⁴ and 1×10⁻⁴ Mt, i.e. 5×10⁻⁷ relative. |
| **P-15** | \|Δwind + Δsolar\| < 0.5 TWh and \|ΔCO2\| < 1.0 Mt in every year of `VOL-MID` / `VOL-HI`; escape ≈$0.67 B/yr and $2.05 B/yr at 2030 | **HIT — above the claimed strength** | Δ(wind + solar) = **0.0000 TWh exactly** (not <0.5); max \|ΔCO2\| = **0.0148 Mt** (not <1.0). The escape costs are now *verified* rather than assumed, because the measured zero recovery closes the arithmetic: (216.070 − 67.106) × $4.50 = **$0.670 B/yr** and (360.578 − 67.106) × $7.00 = **$2.054 B/yr** at 2030. That escape column is the arm's entire content. |
| **P-16** | `CES-P20+VOL-HI` indistinguishable from `VOL-HI` on every capacity row; the composition is observably empty | **MISS on the form, conclusion survives** | It is indistinguishable from **`CES-P20`**, not `VOL-HI`: ΔCO2 vs REF tracks `CES-P20` to ≤0.013 Mt in every year and it carries the identical 2,590.4 / 3,749.7 / 6,745.7 MW of retrofit, where `VOL-HI` carries **none**. So the composition is **not** empty — but its content is entirely the CES half, and the *voluntary* half contributes exactly nothing to it, which is the D-6 reading P-16 was written to produce. |
| **P-17** | `ALL-CLEAN` is the one arm where D-6 has content; both nettings reported | **HIT** | It is: `ALL-CLEAN` − `CARB-MID+LOAD-HI` is zero everywhere except 2029, where the CES-target row buys **+1,000 MW nuclear for −1,000 MW solar** (−3.775 Mt, −$22.098/MWh, +0.367 pp RM), unwound to a zero net capacity difference by 2030. Both nettings at §2.12. |
| **P-18** | the D67-ARM / D81 confound stays inert at −34 % because the backstop stays clamped; every capacity row moves for load reasons, none for a requirement reason | **PARTIAL MISS — see §4.1** | The **conclusion** holds for a *different and better* reason (form 4: the operand is identical on both sides). The **stated mechanism is wrong**: the backstop is *not* clamped at high load — 3,056.8 → 2,214.0 MW (2029), 5,056.8 → 5,899.6 MW (2030). Leg 6's clamp reading must not be inherited as a PJM property. |
| **P-19** | `CAP-STATE-TIGHT`: 2026 byte-identical; 2027–2029 slack, dual 0 exactly; **2030 binding** with covered emissions = 52.525996 Mt and a positive dual $5–40/t; whole-ISO CO2 falls <2 Mt | **MISS on the binding claim — and the PRECOMMIT said it expected to be** | 2026 byte-identical: **HIT, strictly**. 2030 binding: **NO**. A cap binding by the estimated 1.4 Mt would show as a whole-ISO ΔCO2 of that order; measured 2030 ΔCO2 is **−0.0050 Mt**, and max \|ΔCO2\| over 2027–2030 is **0.0070 Mt (0.002 %)**. The 2028 delta is bit-for-bit the same alternate optimum `VOL-HI` and `CES-T80` produce (identical import +0.0165 TWh) — LP degeneracy, not a cap response. The §4.2(c) estimator's own stated escape hatch is the answer: covered gas-CC runs enough below the ISO-average capacity factor that 2030 is slack after all. "CO2 falls <2 Mt" is technically a hit but carries no information once the cap is slack. |

**Score: 5 HIT (P-10, P-11 on its arithmetic, P-14, P-15, P-17); 2 SPLIT
(P-9, P-16); 3 MISS (P-12, P-18-mechanism, P-19-binding); 8 UNSCORABLE (P-1…P-8, P-13
directly).** The two misses that matter are **P-12**, which produced the lane's central
structural result, and **P-18**, which retires an inherited reading.

---

## 5a. Ruling S15 — the entry mask CHECKED, a correction to its stated seam, and the bracket leg

**The check, from the committed REF report, per year.** PJM's `rps_dual` is
**45.00 $/MWh in 2026, 2027, 2028, 2029 and 2030** — the `STATE_RPS_ACP["PJM"] = 45.0`
ceiling exactly, in **every year of all eleven runs** (REF and all ten legs), so the RPS row
is itself in escape throughout. The CES duals the premium legs carry are their premiums:
**$10, $20 and $30**. In every year of every premium leg, **45.00 ≥ the leg's CES dual**.

> **THE MASK BINDS, IN ALL FIVE YEARS, ON ALL THREE RUNGS. `CES-P60` IS OWED, AND IT IS THE
> ONLY SOLVE THIS SESSION RAN.**

The measured consequence is already in §2: `builds_renew_mw` is **+0.0 MW vs REF** in all
five years of all three rungs, while the same legs cut 2030 CO2 by −14 Mt through a channel
the mask does not cover.

### 5a.1 A correction to the seam ruling S15 names — the fuel gate DOES exist, and it is why nuclear escapes

S15 states the fold as `attr = max(EAC, rps_credit_for_zone, clean_credit)` **with no fuel
gate**, citing `new_entry.py` ~:1132–1143. Read at THE PIN, that citation is the
**zone-siting** helper `_zone_revenue` — which is indeed ungated, but only chooses *where* an
already-screened candidate is sited. **The build/no-build screen is a different fold, at
`new_entry.py:1190–1208`, and its RPS leg IS fuel-gated:**

```
rps_for_tech = (rps_credit_for_zone(...) if tech in _RENEWABLE_NEW_FUELS else 0.0)
effective_attribute_price = max(effective_eac_price_for_tech(...), rps_for_tech, clean_for_tech)
```

with `_RENEWABLE_NEW_FUELS = frozenset({"wind", "solar"})` (`new_entry.py:121`), while
`_clean_credit_for_tech` credits the CES row to **every** qualifying fuel including nuclear
and `gas_cc_ccs`. **The gate is not a defect in S15's reasoning — it is the reason the
reasoning has the consequence this lane measured.** Because the RPS leg reaches only wind and
solar:

| candidate | attribute at REF | at `CES-P20` | at `CES-T80` ($50) | uplift at $50 |
|---|---|---|---|---|
| wind / solar | **45.00** (RPS) | max(45, 20) = **45.00** | max(45, 50) = **50.00** | **+$5.00** |
| nuclear (RPS-ineligible) | EAC only | max(EAC, 20) | max(EAC, 50) = **50.00** | **≈ +$50.00** |
| `gas_cc_ccs` (0.95 credit) | EAC only | max(EAC, 19) | *(see 5a.1a — the target does NOT reach the retrofit screen)* | — |

So the ceiling does not merely *mute* a clean-attribute lever on PJM — **it re-points it at
whatever clean fuel the RPS cannot reach.** That is the single mechanism behind every result
in §0: the premium's 6.7 GW of CCS retrofit, the target's 1,000 MW of nuclear, and the total
absence of VRE entry anywhere in the lane. It also brackets the nuclear-entry threshold: **at
$30 no nuclear enters and at $50 it does**, so PJM's nuclear entry turns on somewhere in
**($30, $50]** — which is precisely the interval `CES-P60` does *not* probe, and worth
recording as the question the bracket leg leaves open.

**Routed:** S15's citation should be re-pointed from the siting helper to
`new_entry.py:1190–1208` in any prompt that reuses it, and the two folds' *differing* gates —
ungated for siting, wind/solar-gated for the build screen — are worth a desk look on their
own; they are `src/` and outside this lane's regions.

### 5a.1a A SECOND ASYMMETRY, MEASURED AND NOT EXPLAINED: a $10 premium saturates the CCS retrofit cap; a $50 target ACP triggers none

Absolute `capacity_by_fuel_mw['gas_cc_ccs']`, MW:

| arm | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| REF | 0 | 0 | 408.2 | 2,248.7 | 2,248.7 |
| `CES-P10` / `CES-P20` / `CES-P30` (premium $10–$30) | 0 | 0 | **2,988.6 / 2,998.6 / 2,998.9** | **5,987.1 / 5,998.4 / 5,998.3** | **8,981.2 / 8,994.4 / 8,997.6** |
| **`CES-T80`** (target, ACP **$50**) | 0 | 0 | **408.2** | **2,248.7** | **2,248.7** — *identical to REF* |
| `CARB-MID+LOAD-HI` / `ALL-CLEAN` (carbon $3.75 → $15/t) | 0 | 0 | 2,991.6 | 5,989.8 | 8,989.8 |

**A $10/MWh CES *premium* pushes the retrofit to its 3 GW/yr cap in all three eligible years.
A $50/MWh CES *target* ACP — five times the price, on the same 0.95-credited fuel, in the same
ISO, at the same pin — adds not one MW.** `CES-T80` does raise CCS *generation* (existing units
run harder: 1.951 → 3.136 TWh at 2028, 14.805 → 17.275 at 2030), so the target row reaches
**dispatch** and not the **retrofit screen**, while the premium reaches both.

This lane **measures** the asymmetry and deliberately does not explain it — the candidate
explanations (an escaping target row crediting the escape variable rather than the marginal
credited MWh; the retrofit screen reading a different clean-attribute seam from the entry
screen; a crediting-mode difference between the premium and target forms) are all `src/`
questions outside its regions. It matters because **the campaign's two CES instrument forms
are not interchangeable on PJM even at a 5× price ratio**, and any cross-ISO synthesis that
treats "the CES lever" as one thing will be wrong here. Routed at §8.

### 5a.2 The bracket leg

`pjm-2026-2030-scn-campaign-policy-2026-09-06-ces-p60`, key **`19999987cb623817`**, 5/5
solve-years, invariant FAIL set **`{I7, I12}` — REF's exactly**, I3 PASS with zero unserved
MWh, no new FAIL and no WARN.

**Provenance, stated because it is the one solve of this session.** Run at **THE PIN** —
`git.sha` `bdfb3095`, `basis_sha` `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b`, and the only
"dirty" entry is this FINDING doc itself, with an **empty `diffstat`**, so the ADDENDUM's
`exit 91` zero-solve-path-diff guard is satisfied. It was solved from a **detached checkout at
the pin**, not at `main`: capx **D75-R-ARM** (`pjm_vre_accreditation_vintage`) is armed for PJM
at HEAD and is post-pin, so solving at HEAD would have put a live accreditation change on one
side of the P60 − P30 difference and nowhere else. Invocation
`--case CES-P20 --set federal_ces_premium_usd_per_mwh=60.0`, which is why the summary's `case`
string reads `CES-P20`; the resolved config is what matters and it is exact — **vs REF it
differs in the two chartered fields only** (`federal_ces_enabled` False → True,
`federal_ces_premium_usd_per_mwh` 0.0 → 60.0) and **vs `CES-P30` in exactly one**
(30.0 → 60.0). $60 is the common cross-ISO level, above the footprint's highest published ACP,
never a per-ISO number (rule 25 `[R-ISO-SCOPE]`).

### 5a.3 The result — clearing the mask does NOT unlock VRE. It unlocks NUCLEAR.

| year | CO2 Mt | ΔCO2 vs REF | ΔCO2 vs `CES-P30` | `builds_renew_mw` (REF's) | `builds_thermal_mw` (REF's) | gas_cc_ccs MW | Δ nuclear MW |
|---|---|---|---|---|---|---|---|
| 2026 | 373.2129 | +0.0180 | +0.0186 | 0.0 (0.0) | 0.0 (0.0) | 0 | 0 |
| 2027 | 393.6671 | −0.0081 | +0.0016 | 0.0 (0.0) | 842.8 (842.8) | 0 | 0 |
| 2028 | 411.4242 | **−5.9563** | −0.0491 | 0.0 (0.0) | 0.0 (0.0) | 2,999.9 | 0 |
| 2029 | 422.3757 | **−7.5756** | −0.0065 | **6,000.0 (6,000.0)** | 7,056.8 (7,056.8) | 5,998.6 | 0 |
| 2030 | 444.9557 | **−18.0837** | **−4.0980** | **1,500.0 (1,500.0)** | **7,742.4 (6,742.4)** | 8,996.7 | **+1,000.0** |

**Three readings, and the first is the one the desk asked for.**

1. **THE MASK IS REAL AND $60 CLEARS IT — AND `builds_renew_mw` IS *STILL* +0.0 MW AGAINST REF
   IN ALL FIVE YEARS.** The 6,000.0 and 1,500.0 MW at 2029/2030 are REF's own numbers to the
   0.1 MW. A premium six times the ladder's bottom rung, and 33 % above the $45 ceiling that
   was supposed to be the whole obstruction, **commissions not one additional MW of wind or
   solar on PJM.** The ceiling was a real mask — but it was never the binding constraint on
   VRE entry here, and any reading that says "lift the $45 mask and PJM builds renewables" is
   now falsified by direct measurement.
2. **What $60 buys instead is +1,000 MW of nuclear at 2030** — the *same* 1,000 MW, in the
   *same* year, through the *same* economic-entry channel (`builds_by_source` `economic`
   1,685.6 → 2,685.6; `reserve_backstop` unchanged at 5,056.8) that the **$50 CES-T80 target**
   bought. That is §5a.1's mechanism confirmed by an independent instrument: the RPS leg is
   fuel-gated to wind and solar, so a clean-attribute price above $45 is a **+$15/MWh** uplift
   for VRE and a **+$60/MWh** uplift for RPS-ineligible nuclear, and the entry screen takes the
   second. The nuclear-entry threshold on PJM is bracketed **($30, $50]** by `CES-P30` /
   `CES-T80` and re-confirmed at $60.
3. **The extra CO2 reduction is the nuclear, not the retrofit.** `gas_cc_ccs` at $60 is
   **2,999.9 / 5,998.6 / 8,996.7 MW**, i.e. the same 3 GW/yr cap `CES-P10` already reached —
   the whole ladder $10 → $60 moves it by **±3 MW**. So P60 − P30 = **−4.098 Mt at 2030** is
   almost exactly the nuclear's 8.278 TWh displacing gas-CT (−7.613 TWh), gas-ST (−0.479) and
   imports (−0.826). Below the mask the CES lever is a *retrofit* lever pinned at its cap;
   above it, it becomes a *nuclear-entry* lever. **It is never a VRE lever on PJM.**

**One honest limit on the bracket.** `CES-P60` is a **premium**-form leg, so it does not test
whether the §5a.1a premium-vs-target asymmetry (a $10 premium saturating the retrofit cap
while a $50 target ACP adds none) survives above the ceiling; and no leg in this campaign
probes the ($30, $50] interval where PJM's nuclear entry actually switches on. Both are
recorded as open, not closed.

---

## 6. Wall clock and peak RSS per solve-year (the D-5 cost table's input)

Read from each leg's own `per_year_perf` block. PJM is the campaign's heaviest non-per-plant
ISO and the numbers below are the measurement the desk's sizing needs.

| leg | total wall s | min / solve-year | peak RSS MB | per-year wall s (peak RSS MB) |
|---|---|---|---|---|
| `CES-P10` | 2,323.1 | 7.74 | 9,012.9 | 2026:483 (9,013) · 2027:130 (6,634) · 2028:218 (7,020) · 2029:774 (7,759) · 2030:718 (8,581) |
| `CES-P20` | 1,533.2 | 5.11 | 8,917.9 | 2026:386 (8,918) · 2027:111 (6,622) · 2028:171 (6,953) · 2029:430 (7,818) · 2030:435 (8,504) |
| `CES-P30` | 5,322.3 | 17.74 | 8,988.6 | 2026:484 (8,989) · 2027:127 (7,104) · 2028:226 (6,714) · 2029:638 (7,834) · **2030:3,847** (8,291) |
| `CES-T80` | 2,712.2 | 9.04 | 8,519.9 | 2026:411 (8,520) · 2027:214 (6,854) · 2028:362 (7,028) · 2029:639 (7,538) · 2030:1,085 (7,693) |
| `VOL-MID` | 2,656.1 | 8.85 | 8,990.8 | 2026:516 (8,991) · 2027:132 (7,072) · 2028:182 (7,017) · 2029:875 (7,824) · 2030:951 (8,657) |
| `VOL-HI` | 2,597.0 | 8.66 | 8,979.0 | 2026:475 (8,979) · 2027:131 (7,010) · 2028:181 (6,986) · 2029:861 (7,902) · 2030:948 (8,647) |
| `CES-P20+VOL-HI` | 2,772.2 | 9.24 | 8,988.5 | 2026:738 (8,988) · 2027:184 (7,019) · 2028:286 (7,037) · 2029:657 (7,893) · 2030:907 (8,646) |
| `CAP-STATE-TIGHT` | 3,357.9 | 11.19 | 8,874.2 | 2026:735 (8,874) · 2027:173 (7,102) · 2028:304 (6,930) · 2029:1,111 (7,798) · 2030:1,034 (8,714) |
| `CARB-MID+LOAD-HI` | 2,003.0 | 6.68 | 8,955.1 | 2026:462 (8,955) · 2027:203 (7,245) · 2028:364 (6,991) · 2029:432 (7,985) · 2030:542 (8,925) |
| `ALL-CLEAN` | 4,200.0 | 14.00 | 9,008.9 | 2026:424 (9,009) · 2027:376 (7,184) · 2028:704 (7,409) · 2029:1,351 (7,593) · 2030:1,346 (8,845) |
| `CES-P60` *(this session, the S15 bracket)* | 2,516.2 | 8.39 | 8,950.8 | 2026:501 (8,951) · 2027:153 (7,016) · 2028:266 (7,032) · 2029:807 (7,854) · 2030:790 (8,586) |
| **ten legs (the registered Stage A + B set)** | **29,477.0 s = 8.19 h** | **9.83** | **9,012.9** | 50 solve-years |
| **eleven legs (incl. `CES-P60`)** | **31,993.2 s = 8.89 h** | **9.69** | **9,012.9** | 55 solve-years |
| *(REF, for reference)* | 2,597.5 | 8.66 | 8,878.7 | 2026:397 (8,879) · 2027:132 (6,759) · 2028:246 (7,011) · 2029:948 (7,867) · 2030:874 (8,608) |

**Three things the desk should take from this table.**

1. **PJM's measured cost is 9.83 min/solve-year**, against the campaign mean of **3.92** — a
   factor of **2.51**. The PRECOMMIT §9 item 3 warned the desk's arithmetic understated PJM
   by ~2×; measured, it understates it by 2.5×. Any Stage-B sizing that prices PJM at the
   campaign mean is wrong by that factor.
2. **The variance across legs is larger than the mean.** `CES-P20` at 5.11 min/yr and
   `CES-P30` at 17.74 differ by 3.5× on configs that differ by one scalar and produce
   near-identical answers; `CES-P30`'s 2030 alone (3,847 s) is 26 % of the whole lane's LP
   time. A per-leg budget is not predictable from the ISO; only the aggregate is.
3. **Peak RSS is stable at 8.5–9.0 GB regardless of case**, so rule 12's ~2-concurrent cap
   is the binding constraint on PJM whatever the case set, and two concurrent PJM legs would
   need ≈18 GB.

---

## 7. STAGE-B SEED — `CAP-STATE-TIGHT` (owner ruling S17, desk card D-13)

**Out of Stage A.** Registered like the other nine
(`pjm-2026-2030-scn-campaign-policy-2026-09-06-cap-state-tight`, key `50da3e27a4298ba2`,
FAILs declared) because un-registering it would strand a committed bundle and redden the
parity gate, and git history is the record either way — but **excluded from §3's gate
scoring, from §0's headline and from the plan §5.1 rows.** Ruling S12's committed level is
untouched; only the stage moves. This lane solved it before the ruling reached it.

**The measured PJM reading, for Stage B to start from.**

| year | cap tons (metric t) | REF CO2 Mt | arm CO2 Mt | ΔCO2 Mt | ΔCO2 % | Δ any capacity row |
|---|---|---|---|---|---|---|
| 2026 | *no row* | 373.1949 | 373.1949 | **0.0000** | 0.000 | **byte-identical, every field** |
| 2027 | 57,334,075.568 | 393.6752 | 393.6742 | −0.0010 | −0.000 | none |
| 2028 | 55,701,143.036 | 417.3805 | 417.3735 | −0.0070 | −0.002 | none |
| 2029 | 54,068,210.504 | 429.9513 | 429.9502 | −0.0011 | −0.000 | none |
| 2030 | 52,525,996.446 | 463.0394 | 463.0344 | −0.0050 | −0.001 | none |

**(a) The cap did not bind at 2030, and the PRECOMMIT's estimator says why it might not
have.** §4.2(c) put covered 2030 emissions 1.4–3.6 Mt above the budget on three estimators,
each assuming each fuel's capacity factor is uniform across zones, and named the escape
hatch: covered gas-CC running ~10 % below the ISO-average gas-CC capacity factor would make
2030 slack. A binding cap would have forced covered emissions down by ≈1.4 Mt and shown up as
a whole-ISO ΔCO2 of that order. Measured: **−0.0050 Mt**, three orders of magnitude smaller,
and the 2028 delta is *bit-for-bit the same alternate optimum* `VOL-HI` and `CES-T80` produce
(identical import +0.0165 TWh). This is LP degeneracy, not a policy response.

**(b) NEISO's loosening mechanism cannot operate on PJM, and this is the cross-ISO point
Stage B most needs.** S17 records NEISO's cap as a policy **loosening** of +2.9 to +13.9 Mt,
because the cap row **replaces** an RGGI price adder running 26.05 → 34.15 $/t with a dual of
12.23 → 8.26 $/t. **PJM has no adder to replace**: PJM is in `CAP_AND_TRADE_PROGRAMS` but
absent from `STATE_CARBON_PRICE_BY_ISO`, and its RGGI `price_adder` resolves to **0.0 in
every REF year** (PRECOMMIT §4.1). So on PJM the row is added where nothing stood — it can
only tighten or do nothing, and it does nothing. **The sign of the cap instrument's effect is
therefore ISO-structural, not a level question**: it depends on whether the ISO's REF already
carries a program *price*, and the campaign's six ISOs split on exactly that.

**(c) What Stage B cannot answer from this artifact.** `co2_cap_price` is not exported, so
the binding test cannot be settled and G10's dual half and G12's price-vs-quantity read-out
are unscorable (§3, §8.2). The PRECOMMIT §9 item 2 already routed the cheap fix: a
covered-emissions read-out on the REF bundle in `report_scenario_deltas.py`. Add the cap dual
to it.

---

## 8. Routed to SCN-DESK — outside this lane's regions, not executed here

1. **THREE OF THIRTEEN CHARTERED LEGS WERE NEVER SOLVED, AND PJM HAS NO STAGE-A CARBON
   READING.** `CARB-LO`, `CARB-MID` and `CARB-HI` (keys `69a2199c1d2bffd6`,
   `055ad9fc2202d385`, `0a63b91706bac093`; 15 solve-years) are absent from the artifact
   record. Phase 0 did not kill them and the ADDENDUM's owner grant was explicit that the set
   was **not** narrowed ("solve all 13 as chartered"). Consequences, stated rather than
   absorbed: **P-1 through P-8 are unscorable**; PJM cannot supply the carbon column's row-3
   evidence even though WS-1b measured PJM as one of only three ISOs where the carbon axis is
   live at all (17.4 TWh of coal shed to $3.75/t); G12's price-vs-quantity comparison has no
   comparator; and `CARB-MID+LOAD-HI` — the one carbon-bearing leg that exists — confounds
   carbon with load by construction and cannot separate them. **≈2.5 h of LP at the measured
   PJM rate.** This is the single largest hole in the lane and the desk should decide whether
   to spend it.
2. **NO PJM LEG COMMITTED A DUALS ARTIFACT, AND THE LP CACHES ARE GONE.** This is the sole
   cause of **four** unscorable gate verdicts — G4 (`CES-T80` dual = ACP $50 exactly), G7
   (voluntary dual bounded per arm), G10's binding-year dual, G12's read-out — and of P-13
   being unscorable. MISO's lane committed `duals.json` beside each leg
   (`results/scn-campaign-policy-2026-09-06/MISO/<CASE>/duals.json`, carrying
   `clean_region_duals` / `rps_region_duals` / `objective_value` per year); PJM's sub-lanes
   did not, and nothing in `run_ces_leg.py` emits one, so it was a per-lane manual step that
   PJM's shards skipped. **AND A RE-SOLVE DOES NOT FIX IT EITHER.** This session's own S15 leg
   solved with a live cache in the container, and the duals are still unrecoverable: the
   clean-tier region duals exist only on the in-memory `DispatchResult`
   (`model/lp/__init__.py:146`) and reach the outside world **through a `logger.info` line**
   (`runner.py:3695–3705`) that the driver's default log level does not emit — nothing writes
   them to the cache dir, and `evolution_<year>.json` carries only `rps_dual`. **The fix is to
   PERSIST them** (a `duals.json` beside `evolution_<year>.json`, or the block in the summary),
   not to re-run: at present a dual-identity gate is unscorable on PJM at *any* cost, and
   MISO's committed `duals.json` files are lane-local captures rather than a reproducible
   artifact of the driver.
3. **`import_co2_mt_reported` IS `null` IN EVERY PJM ARTIFACT, THE REF INCLUDED.** WS-0's
   G-E3 shipped the field and ruling S11 requires it beside every CO2 number; on PJM it
   carries no value, so the duty is not dischargeable and the leakage line the desk asked
   every campaign delta to be read with does not exist for this ISO. The physical quantity is
   there — `generation_by_fuel_mwh['import']` runs 0.279 → 13.707 TWh in REF — so this reads
   as an export gap rather than a modelling gap, but it is not this lane's region to close.
4. **PJM's `LOAD-HI` is still unsolved at THE PIN** (PRECOMMIT P2a; RESOLVE stopped at leg
   6/13). `CARB-MID+LOAD-HI` therefore still has no same-pin pairing base, and
   *carbon-under-high-load* remains unmeasurable on PJM. Unchanged since the PRECOMMIT and
   re-routed because it is now the second reason the carbon axis is dark here.
5. **LEG 6's "THE BACKSTOP IS RATE-CLAMPED, THEREFORE THE D67-ARM/D81 CONFOUND IS INERT"
   READING MUST NOT BE INHERITED AS A PJM PROPERTY.** Measured at −33 % (§4.1), the backstop
   is **not** clamped: 3,056.8 → 2,214.0 MW at 2029 and 5,056.8 → 5,899.6 MW at 2030 between
   REF and the high-load arms. The confound is still inert for this lane's deltas, but for the
   form-4 reason (same operand on both sides at THE PIN), which is the stronger argument and
   the one a future session should cite.
6. **THE COORDINATOR/SUB-LANE SPLIT HAS NO SEAM THAT FORCES REGISTRATION, AND THAT IS WHY
   THIS GAP EXISTED FOR THREE DESK REFRESHES.** Each S2–S6 shard solved, committed its
   artifacts and handed off; registration was the coordinator's step and nothing failed when
   it did not run. The backlog grew 4 → 8 → 10 while every gate stayed green, because **every
   gate in the forecast namespace fires at registration** — the Y-24 declaration ratchet, the
   invariant audit, the parity sweep — so an *unregistered* run is invisible to all of them.
   The desk may want the shard, not the coordinator, to own its own registration, or a check
   that compares `results/scn-campaign-*/<ISO>/*/full_horizon_summary.json` against
   `frontend/data/hindcast/` and goes red on the difference. **The same gap swallowed a second
   coordinator step, and this one is now UNRECOVERABLE:** ERCOT and MISO carry assembled
   `bundle/G*` + `report/G*` trees under the campaign root (`run_ces_leg.py --assemble`) and
   **PJM carries none**. It cannot be produced from the committed artifacts now, because
   `assemble_bundle` → `write_matrix_outputs` reads the **LP cache** at `results/PJM/<key>/`
   to build the trajectory table and envelope, and PJM's ten caches are gone with the
   containers that made them. **The measured cost of a coordinator step that ran late is
   therefore ≈8.19 h of LP to recreate** — the same reason the duals (§8.2) are gone. Both
   argue for the shard owning its own registration *and* its own assembly, while its cache is
   still live.
7. **PJM's measured LP cost is 9.83 min/solve-year, 2.51× the campaign mean** (§6), with
   per-leg variance up to 3.5× on configs differing by one scalar. D-5's cost table should
   carry the per-ISO number, not the mean.
8. **THE CES PREMIUM AND THE CES TARGET REACH DIFFERENT SCREENS ON PJM (§5a.1a).** $10/MWh of
   premium saturates the 3 GW/yr CCS retrofit cap in all three eligible years; $50/MWh of
   target ACP adds zero retrofit MW while raising existing-CCS generation. Both are the same
   `federal_ces_*` family, both `clean_capture`, both at THE PIN, and the price ratio is 5×
   against the instrument that does nothing. Candidate causes — an escaping target row
   crediting the escape variable rather than the marginal credited MWh; the retrofit screen
   reading a different clean-attribute seam from the entry screen; a crediting-mode difference
   between the two forms — are `src/` questions and outside this lane's regions. **Any
   cross-ISO synthesis that treats "the CES lever" as one instrument is wrong on PJM.**
9. **ROW 3 OF THE PLAN §5.1 SCORECARD AND ITS LEDGER §3 MIRROR NO LONGER RENDER AS A TABLE,
   AND IT IS NOT THIS LANE'S CELLS.** A sibling lane's appends left **raw, unescaped `|`
   characters** inside row 3's CES-premium and Voluntary cells (`ΔP30−ΔP20|/|ΔP20|`, `|20|`,
   a bare `|Δ`), so GFM splits that row into **17 cells against the header's 7** and every
   column after the first stray pipe renders in the wrong place. Measured on `a6a8cd46`
   before this lane touched the file. **This lane did not fix it** — those are another lane's
   cells and rule 25's spirit applies to the record as much as to the model — and it appended
   its own text with every pipe escaped (`\|`), detecting the true cell boundaries from each
   column's opening marker rather than by splitting, so its four inserts land in the right
   cells despite the breakage. The one-character fix is the owning lane's; flagging it is
   this lane's.
10. **An accreditation observation, reported not diagnosed.** In the CES-premium arms
   `total_cap_mw` and `peak_demand_mw` are byte-identical to REF, yet the reserve margin rises
   +0.30 / +0.41 / +0.70 pp at 2028/2029/2030 — so a gas-CC MW and its CCS-converted self are
   accredited differently. Whether that is intended is a capacity-accreditation question, not
   a scenario question.

---

## 9. Files

**Commit 1 — the ten registrations + the declaration ledger:**

- `frontend/data/hindcast/pjm-2026-2030-scn-campaign-policy-2026-09-06-{all-clean,
  cap-state-tight, carb-mid-plus-load-hi, ces-p10, ces-p20, ces-p20-plus-vol-hi, ces-p30,
  ces-t80, vol-hi, vol-mid}.json` — kind `scenario`, campaign
  `scn-campaign-policy-2026-09-06`, `reference_case: REF`, 5/5 solve-years, `error: null`.
- `frontend/data/hindcast/invariant-failures.json` — ten declarations (eight `{I7, I12}`, two
  `{I3, I7, I12}`) plus `scn_ws5a_policy_pjm_note` recording that not one FAIL is introduced
  by a policy case. Audit **EXIT 0** before and after; 163 → 173 sidecars, 190 → 212 FAILs.

**Commit 2 — the ruling-S15 bracket leg, this session's one solve:**

- `results/scn-campaign-policy-2026-09-06/PJM/CES-P60/{full_horizon_summary.json,
  run_config.json}` — key `19999987cb623817`, solved at THE PIN with an empty solve-path
  diffstat, 5/5 years, 2,516.2 s / 8,950.8 MB.
- `frontend/data/hindcast/pjm-2026-2030-scn-campaign-policy-2026-09-06-ces-p60.json` and its
  `{I7, I12}` declaration. Audit still **EXIT 0**; 174 sidecars, 214 declared FAILs.

**Commit 3 — the records:** this FINDING; the plan §5.1 rows 3 and 7 of the Carbon /
CES-premium / CES-target / Voluntary columns and the identical ledger §3 mirror; and, last
after rebase, the four PJM mechanism-matrix shard cells (rule 28(b)).

**Consumed, never edited:** the ten legs' `full_horizon_summary.json` + `run_config.json`
under `results/scn-campaign-policy-2026-09-06/PJM/`; the r2 REF bundle; every other ISO's
files; everything under `src/`; `configs/scenario_campaign_matrix.yaml`; the PJM base YAML.
`program-status.json`, `ff-verdicts.json` and the whole **backcast** namespace: untouched.

**Duties.** No default moved, no knob moved, no `ScenarioConfig` field added, no case added,
never a year past 2030. **DOF ledger: zero free parameters.** No `authorized_price_tuning`
(rule 1's carve-out is a backcast offer-curve channel; a forecast lane does not touch it).
Backcast byte-identity untouched by construction — every leg is `mode="forecast"`. Rule 29(c):
no screen bundle and no control bundle is produced; the control is the committed r2 REF.
Rule 28(b): the PJM matrix shard's `federal_ces_target`, CES-premium, `carbon_price_path` and
`voluntary_clean_demand` cells are stamped as the **last** commit, after rebase.
