# FINDING — SCN-WS5A-LOAD / ERCOT: the Stage A-LOAD legs, scored at the horizon

**Lane** SCN-WS5A-LOAD (ERCOT) · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Branch** `claude/scn-ws5a-load-campaign-f5znk9` ·
**PRECOMMIT** `docs/handoffs/PRECOMMIT-scn-ws5a-load-2026-09-06.md` + its pin ADDENDUM
(both pushed before the first solve) · **Frozen pin** `1cc45bb2` (solved at `20f9ce9f`
= that pin + the docs-only addendum commit; `git.dirty = false` on every leg) ·
**Campaign** `scn-campaign-load-2026-09-06`, kind `scenario`, `reference_case: REF` ·
**Scored against** SCN-WS4b's `load-hi-adequacy-reading-2026-09-06.md` §5.1 and SCN-WS4c's
T0 verdicts (`FINDING-scn-ws4c-2026-09-06.md` §3.2).

---

## 0. Bottom line

1. **The headline result is about the REFERENCE case, not the load cases.** At HEAD, ERCOT
   `REF` — the shipped posture, `demand_growth_path=mid`, `datacenter_load_path=mid`,
   `set_overrides={}` — is already in deep shortage: unserved energy **0.38 → 127.2 TWh**
   (14.7 % of 2030 load), load-weighted price **$91 → $4,438/MWh**, `hours_ge_500`
   **74 → 7,962** of 8,760. Every ERCOT delta below is a difference between arms that are
   **both shedding at VOLL from ~2027**.
2. **Prediction P-1 is a HIT: ERCOT never enters the tail regime.** The load arms carry
   *identical* energy deltas (≈23 TWh at 2030, not +660 TWh) and `LOAD-HI`'s peak sits
   **below** `LOAD-HI-ORGANIC`'s in every year — the relocate signature. WS-4b's
   1,800 TWh / 267 GW discontinuity does not reproduce.
3. **WS-4b's ERCOT 2030 outcome lands while its stated mechanism is absent** (§3.2): they
   predicted "hundreds of TWh" of slack and `hours_ge_500` "near 8,760" *as a consequence of
   the tail regime*; measured **538.9 TWh** and **exactly 8,760** — with no tail. Right
   number, wrong cause. Scored **SPLIT**, not HIT.
4. **Their peak/adequacy artefact is a clean MISS.** WS-4b expected `LOAD-HI`'s peak
   9–18 GW *below* REF and I12 therefore to "improve or pass". Measured: the peak is
   **above** REF in all five years (110.6 vs 104.1 GW … 215.8 vs 161.8 GW) and I12 is
   uniformly **worse**. Cause identified: the retired 122 GW DC anchor (§4).
5. **Three of my own six predictions miss**, reported at full magnitude in §5 — including
   both of the ones carrying the most reasoning.

---

## 1. What was solved

| leg | years | wall / solve-year | peak RSS |
|---|---|---|---|
| REF | 2026–2030 | 0.85 – 2.84 min | 3.41 – 4.10 GB |
| LOAD-HI | 2026–2030 | 0.41 – 2.49 min | 3.35 – 3.78 GB |
| LOAD-HI-ORGANIC | 2026–2030 | 0.42 – 2.48 min | 3.31 – 3.45 GB |

Three legs, 15 solve-years, **20 min wall** — under the 30 min budget and far under the
§2.4 anchor. Years sequential; ERCOT was co-run with one light ISO only (rule 12).
`gas_cc_ccs` conversions: **NONE** in any arm or year (ruling S5 flag, §6).

## 2. The headline table

`emissions_mt` is never read alone — `unserved_mwh` and the import line sit beside it.

| case | year | CO2 Mt | ΔCO2 | $/MWh | peak GW | margin | unserved TWh | import CO2 | backstop MW |
|---|---|---|---|---|---|---|---|---|---|
| REF | 2026 | 214.39 | — | 91.04 | 104.05 | +0.033 | 0.38 | 0.0 | 0 |
| REF | 2030 | 328.87 | — | 4437.53 | 161.75 | −0.253 | **127.22** | 0.0 | 0 |
| LOAD-HI | 2026 | 256.02 | **+41.63** | 769.48 | 110.63 | −0.028 | 2.66 | 0.0 | 0 |
| LOAD-HI | 2027 | 298.77 | +42.80 | 4039.41 | 127.90 | −0.158 | 71.32 | 0.0 | 0 |
| LOAD-HI | 2028 | 301.53 | +15.83 | 4990.95 | 150.43 | −0.281 | 227.79 | 0.0 | 0 |
| LOAD-HI | 2029 | 321.88 | +16.69 | 4998.44 | 179.30 | −0.355 | 360.98 | 0.0 | 0 |
| LOAD-HI | 2030 | 342.28 | **+13.41** | 4999.55 | 215.81 | −0.431 | **538.87** | 0.0 | 0 |
| ORGANIC | 2026 | 255.26 | +40.87 | 1134.07 | 118.24 | −0.091 | 5.87 | 0.0 | 0 |
| ORGANIC | 2030 | 342.28 | +13.41 | 4999.99 | 241.94 | −0.492 | 538.86 | 0.0 | 0 |

**ΔCO2 FALLS as Δunserved rises** (+41.6 Mt at 2026 → +13.4 Mt at 2030, while Δunserved goes
2.3 → 411.6 TWh). That is not a shrinking emissions response; it is the fossil fleet
saturating while the increment leaves through the slack column. **The 2028–2030 ΔCO2 is not
an emissions response and is not quoted as one.**

## 3. SCORING — SCN-WS4b §5.1, and against WS-4c's T0 verdict

| clause | WS-4b said | measured | verdict | WS-4c T0 |
|---|---|---|---|---|
| **(a)** mechanism | scarcity-priced entry **or nothing**; backstop OFF by design; residual → VOLL slack | `backstop_built_mw` = **0.0** in every year of every arm; residual leaves through slack | **HIT** | HIT — agrees |
| **(b)** invariants | I12/I3 FAIL 2027–30; widening **non-monotone**, peak 9–18 GW *below* REF so I12 "improves or passes"; I3 ambiguous in sign | peak **above** REF every year; I12 uniformly **worse** (+3.3 % → −2.8 % at 2026); I3 uniformly worse (0.06 % → 0.39 %); REF itself fails I12 from **2026**, a year early | **MISS** | HIT at T0 — **flips** |
| **(b) 2030 magnitude** | slack "hundreds of TWh", `hours_ge_500` "≈ 8,760" — *because of the tail regime* | **538.9 TWh**, `hours_ge_500` **8,760 exactly** — with **no tail regime** | **SPLIT** (outcome right, mechanism absent) | untestable at T0 |
| **(d)** table line | `unserved_mwh` beside CO2; backstop printed and **0.0** (non-zero = config defect); CO2/served MWh; `hours_ge_500` | all four present; backstop 0.0 → no config defect | **HIT** | HIT — agrees |
| **(e)** import line | **0.0 exactly**, both cases, every year (no import node) | `import_co2_mt_reported` = **0.0000** in all 15 leg-years | **HIT** | HIT — agrees |

**On the (b) flip, stated precisely so it is not over-read.** WS-4c scored ERCOT (b) a HIT at
T0 — but they ran on the **pre-SCN-LOAD** constants (their phase 0 reproduced the 34.6 →
103.7 GW block). My MISS is on the **re-derived** constants. So the flip is attributable to
the **input re-derivation**, not to extending T0 to the horizon; separating the two cleanly
would need a T0 re-run at HEAD, which this lane did not spend. Recorded as an attribution
limit rather than papered over.

**(c) what a reader may and may not conclude.** *May:* the direction of the fleet response;
the 2026 in-ISO rise at the implied **marginal** rate (§4); CO2 per served MWh. *May not:*
any 2028–2030 total (understated by 228–539 TWh of shed energy); any adequacy claim; that
`LOAD-HI − LOAD-HI-ORGANIC` is "DC emissions" — at 2030 the two arms differ by **0.003 Mt**
on identical energy, so the DC axis's whole measured effect here is **shape**, not volume.

## 4. The implied MARGINAL rate — and why it inverts WS-4c's sign

Charter duty: predict against the **implied marginal** rate, not the fleet average.

| year | ΔCO2 Mt | Δfossil TWh | implied t/MWh | fleet avg | **ratio** |
|---|---|---|---|---|---|
| 2026 | +41.63 | +75.95 | 0.5480 | 0.5858 | **0.94** |
| 2027 | +42.80 | +68.03 | 0.6291 | 0.5916 | **1.06** |
| 2028 | +15.83 | +22.98 | 0.6890 | 0.5865 | **1.17** |
| 2029 | +16.69 | +27.70 | 0.6026 | 0.5691 | **1.06** |
| 2030 | +13.41 | +24.67 | 0.5435 | 0.5579 | **0.97** |
| *WS-4c T0* | +13.69 | +30.63 | *0.447* | *0.610* | ***0.73*** |

**WS-4c's ERCOT sign does not survive to the horizon.** They measured 0.73× — below fleet
average, because inframarginal coal dilutes the marginal response downward. Measured here:
**0.94 → 1.17 → 0.97**, i.e. *above* 1.0 in three of five years. The by-fuel split says why:

| 2026 | coal | gas_cc | gas_ct | gas_st | nuclear/hydro/solar/wind |
|---|---|---|---|---|---|
| Δ TWh (HI − REF) | **−0.00** | +34.83 | +21.89 | +19.24 | **0.00** |

| 2030 | coal | gas_cc | gas_ct | gas_st | solar | wind |
|---|---|---|---|---|---|---|
| Δ TWh (HI − REF) | **+0.00** | +1.21 | **+22.55** | +0.91 | **−16.99** | +15.30 |

Coal is flat to three decimals in **every** year — WS-4c's "coal is inframarginal" holds — but
at HEAD the *rest* of the stack is short, so the marginal unit is the **dirtier peaker**, not
the CC. By 2030 gas_ct carries 92 % of the fossil increment. **The coal/no-coal heuristic WS-4c
derived is therefore conditional on the fleet having headroom; under shortage the marginal rate
rises above fleet average even in a coal ISO.** That is the generalisable result here, and it
sharpens rather than contradicts WS-4c §6.

## 5. My own PRECOMMIT predictions — three misses at full magnitude

- **P-1 HIT (the headline).** ERCOT stays in the **relocate** regime in all five years of both
  arms. Evidence: the two arms' energy deltas are identical (2030: 22.978 vs 22.984 TWh — a
  tail step would add ~660 TWh), and `LOAD-HI`'s peak is below `ORGANIC`'s in every year
  (215.8 vs 241.9 GW at 2030), the flat block's shape signature. `dc_E/E` never approaches 1.0.
- **P-2 MISS, 3 of 5 years.** Predicted the implied rate within ±25 % of WS-4c's 0.447, i.e.
  [0.335, 0.559]. Measured 0.5480 ✓ / 0.6291 ✗ / 0.6890 ✗ (+54.1 %) / 0.6026 ✗ / 0.5435 ✓.
- **P-3 MISS.** Predicted the ratio stays **< 1.0** in coal ISOs. It is 1.06 / 1.17 / 1.06 in
  2027–2029. My reasoning treated "coal inframarginal" as sufficient for a sub-1.0 ratio; §4
  shows it is not — it also requires the gas stack to have headroom, which at HEAD it does not.
- **P-4 SPLIT.** Predicted the ratio drifts monotonically **up** toward 1.0 as coal retires.
  It rises 0.94 → 1.17 (2026–28) then **falls back to 0.97**. The rise is real; the driver is
  not retirement (coal is flat, not retiring) but the scarcity mix, and the late fall is the
  fossil fleet saturating.
- **P-5 MISS.** Predicted the fossil share of Δenergy **falls** with entry. Measured 1.00 /
  1.00 / 1.00 / 1.18 / 1.07 — it *rises* above 1.0, because clean output **reallocates**
  (solar −16.99, wind +15.30 TWh at 2030) rather than growing into the gap.
- **P-6 HIT.** `import_co2_mt_reported` = 0.0 exactly (no import node).

## 6. STOP gate (structural, kill-only) — PASS on every leg

| gate | result |
|---|---|
| **S1** direction | CO2 and price both rise vs REF in every year — PASS |
| **S2** magnitude band | ratio 0.94–1.17, inside [0.5, 2.0] — PASS |
| **S3** footprint | ΔCO2 confined to gas classes; coal/nuclear/hydro Δ = 0.00; VRE carries no CO2; no import tranche — PASS |
| **S4** identity | demand-side energy invariance holds; the arms' *generation* differs only by shed energy (2026: 2.99 TWh generation gap vs 3.22 TWh shed gap) — PASS |
| **S5** collateral flip | FAIL set is **{I3, I12}** in all three arms, unchanged from the board's bare key — PASS |

The gate killed nothing and promoted nothing, as designed.

## 7. The honest-unfit line

- **ERCOT's levels are not quotable at any year, and its deltas only at 2026–2027.** REF sheds
  0.38 TWh at 2026 but **127.2 TWh by 2030**; the load arms shed up to 538.9 TWh with
  `hours_ge_500` pinned at 8,760. From 2028 both arms price at the VOLL ceiling
  (~$4,990–5,000), so ΔCO2 there measures fleet saturation, not an emissions response.
- **A correction to my own earlier reporting in this session:** I first described the HEAD REF
  FC-1 fail set as `{I3, I12, I13, I14}`. That is wrong — **I13 and I14 are WARN, not FAIL**.
  The FAIL set is `{I3, I12}`, *identical* to the board's bare key. What changed is severity,
  not membership.
- `emissions_mt` is read with `unserved_mwh` and the import line beside it, never as a total.

## 8. Routed (not executed — outside this lane's regions)

1. **`ercot-2026-2030-d50-ccscapex` is stale as a description of HEAD**, and by more than the
   NEISO staleness WS-4c routed: energy **+16.5 %** at 2030 (862.5 vs 740.2 TWh), price
   $2,341 → $4,438, `hours_ge_500` 4,039 → 7,962, unserved 127.2 TWh. Cause is SCN-LOAD's
   growth re-derivation (ERCOT REF 7.9 %/yr → 13.48 %/yr), an owner-ruled data intake (S4/D-4).
   Records item for the capx director; `program-status.json` / `ff-verdicts.json` are forbidden
   to every SCN lane.
2. **The shipped ERCOT REF posture now fails I12 from 2026 and sheds 14.7 % of 2030 load.**
   Whether a reference case in permanent shortage is the intended posture is a **levels**
   question (D-2), not a modelling defect this lane may repair. Flagged, not fixed.
3. **A registration defect, repaired here, that any future campaign lane will hit:**
   `register_forecast_baseline` builds `run_id` as `iso-start-end-LABEL` with **no case
   component**, so N cases registered under one `--label` silently collapse onto one sidecar,
   each overwriting the last. The fix is to carry the case in the label (the convention WS-4c's
   own 19 arms used). Worth hardening at the seam rather than in each lane's driver.

## 9. Duties

- **No default moved, no knob moved, no `ScenarioConfig` field added.** DOF ledger: **zero**
  free parameters. No `authorized_price_tuning` (a backcast offer-curve channel; untouched).
- **Consumed, never edited:** `configs/scenario_campaign_matrix.yaml`,
  `report_scenario_deltas.py`, `register_forecast_run.py`, everything under `src/`.
  `program-status.json`, `ff-verdicts.json` and the whole backcast namespace: **untouched**.
- **Rule 15 / §7.5:** registered into the forecast namespace only; generated `registry/` +
  `runs/` stay gitignored. **Rule 27:** no existing ≥300-line source file rewritten; pushes
  fetch-back verified. **Rule 29(c):** no screen or control bundle produced — these are
  registered campaign arms. **Backcast byte-identity:** untouched (forecast-mode only).
