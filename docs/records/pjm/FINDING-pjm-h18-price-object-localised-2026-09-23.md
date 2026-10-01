# pjm-h18 — Lever B localised: the 2020/2022 price misses are two EVENTS on top of ONE compression, not a level

**Lane:** PJM — C3a/C3b 2020+2022 price object (the handoff's "Lever B")
**Date:** 2026-09-23 · **Keeper:** `2026-09-22-pjm-hydro2-ror-span` (+ folded
`…-hydro2-ror-touchpoint`). **The handoff named `pjm-h16-coalgrain` as keeper; `hydro-2`
promoted `hydro_ror_split` on top of it the same day, so every number here is on the CURRENT
keeper.** Lane renamed h17 → h18: `pjm-h17` is taken by
`FINDING-pjm-h17-the-top-of-the-stack-is-not-the-defect-2026-09-21.md`.
**Cost:** ZERO LP, zero shards. Committed hourlies + six `fleet_only` rebuilds (~3 min each).
**Probes:** `scripts/probes/pjm_h18_price_split_phase0.py` → `results/calibration/_pjm_h18_price_split.json`;
`scripts/probes/pjm_h18_marginal_family_phase0.py` → `results/calibration/_pjm_h18_marginal_family.json`.
**Rules:** 32 `[R-SHARD]` (a), 1 `[R-STRUCT]`, 14 `[R-ACCURATE]`, 28 `[R-MECH-MATRIX]`.

---

## 0. Verdict

1. **The opposite signs are NOT one knob and NOT a level.** The probe reproduces the scored C3a
   (2020 +18.6 %, 2022 −10.8 %). In every year, **including the three passing ones**, the model is
   too high in the bottom half of hours (+$2.6 to +$4.8/MWh) and too low in the top 5 %.
   2023–2025 pass C3a **by cancellation**.
2. **The term that carries the sign flip is the PEAKER-marginal (CT/ST) hours.** Their contribution
   runs +0.27 (2020) → −10.86 (2022). The CC-marginal term is positive in **all six** years.
3. **2022 is one event.** Winter Storm Elliott (Dec 23–26, 1.1 % of hours) carries −5.6 of the
   −8.0 $/MWh. Without it 2022 reads **C3a −3.5 % (PASS), C3b 0.114 (PASS)**. PJM cleared at a
   $718 and a $997 daily mean on Dec 23–24; the model's max was $161.
4. **2020 is partly an input glitch.** The EIA-930 demand series carries two impossible hours
   (192 GW and 176 GW; the series' next-highest hour is 145.4 GW), which the model serves by **shedding
   28 GW and 13 GW** at the $2,000 VOLL. They alone are **+4.4 of the 18.6 points**, and they are
   **the whole of 2020's C3b failure** (0.208 → 0.152 without them). The existing
   `_screen_demand_spikes` misses them because its bar is 2.5× the annual median.
5. **What remains is Lever C.** Ex-glitch 2020 (+14.2 %) is the common CC-marginal overshoot
   with nothing on top to cancel it, because 2020 had almost no price spikes (top-5 % term −1.47).

**Nothing is chartered to a solve by this finding.** One card is ready for a PRECOMMIT (§5-A); the
other two need the owner's call (§5-B, §5-C).

---

## 1. The error by price region (load-weighted $/MWh contribution to the annual mean)

| year | C3a | bottom 50 % | p50–p95 | top 5 % | C3b NRMSE |
|---|---|---|---|---|---|
| 2020 | **+18.6 %** | +2.60 | **+2.83** | −1.47 | **0.208** |
| 2021 | +0.0 % | +2.76 | −0.09 | −2.67 | 0.107 |
| 2022 | **−10.8 %** | +4.80 | −2.46 | **−10.35** | **0.246** |
| 2023 | +0.2 % | +3.22 | −0.81 | −2.35 | 0.113 |
| 2024 | −3.6 % | +3.24 | −1.30 | −3.08 | 0.129 |
| 2025 | −7.2 % | +3.78 | −2.08 | −5.01 | 0.149 |

The bottom-half lift is roughly constant in $ terms. The top tail sets each year's sign: tiny in
2020, extreme in 2022. By month (`_pjm_h18_price_split.json`), 2020 is too high in **every** month
(+1.5 to +4.5; July +10.5 because of the glitch). 2022 is ≈0 except Jun–Aug (−11 to −17) and
December (−56.6).

## 2. The four named terms

| term | 2020 | 2022 | how measured |
|---|---|---|---|
| (i) marginal-unit mix | not separable against truth | not separable | **no measured PJM marginal-fuel series on disk** — see §3 for the model side |
| (ii) seam / import | **wrong sign**: model exports 13.3 TWh *less*, which *lowers* its price | −9 TWh, too small | fuelRows `interchange`; pjm-h12 §1 shows the seam gap is a *consequence* of the compression |
| (iii) fuel level | **≈0 by construction**: monthly gas = measured EIA N3045 blend + F923 plant months | **−5.48** on the 8 days the Eastern hub ran ≥2× Henry Hub vs its month (Elliott) | Transco Z6 NY daily vs Henry Hub daily, each normalised to its month; the model's daily shape is Henry Hub's |
| (iv) offer surface | CC-marginal +2.22, coal +0.54 | CC +2.69, **CT/ST −10.86** | §3 |

Transco Z6 NY is spikier than PJM's own M3/Z6-non-NY hubs, so (iii)'s 2022 figure is an **upper
bound** on the daily-gas share. It also overlaps Elliott's scarcity entirely, so (iii) and the
Elliott row are the same hours and are not additive.

## 3. The model's marginal family (fleet_only offers × committed band dispatch)

Error contribution, $/MWh, by the fuel family of the model's marginal band:

| year | CC | CT/ST | coal | CC model / actual $ in its hours |
|---|---|---|---|---|
| 2020 | +2.22 | **+0.27** | +0.54 | 23.0 / 19.1 |
| 2021 | +0.75 | −1.13 | +0.38 | 34.5 / 33.2 |
| 2022 | +2.69 | **−10.86** | +0.16 | 55.9 / 50.2 |
| 2023 | +1.83 | −1.05 | −0.73 | 27.6 / 23.8 |
| 2024 | +1.82 | −2.42 | −0.54 | 26.9 / 22.8 |
| 2025 | +0.83 | −4.57 | +0.44 | 37.6 / 35.5 |

In CC-marginal hours the model is **+16 to +20 % high in 2020, 2023 and 2024 alike**, so the
CC overshoot is year-invariant and is not what makes 2020 special. The coal term flips sign with
the coal price (2020 coal $2.12 vs 2023 $3.39/MMBtu) but is small either way. **The CT/ST column
is the only one that moves by an order of magnitude**, and it tracks how spiky the market's year
was.

## 4. What this settles

- **A level knob is refuted.** The bottom-half lift is similar in $ in every year and the sign is
  set by the top tail. A band multiplier that lifts 2022 lowers nothing in 2020's bottom half, and
  vice versa.
- **Lever B and Lever C are the same object.** The 2020/2022 C3a failures are the pjm-h12 D-2
  variance compression, exposed by two years whose top tail is thin (2020) or extreme (2022). The
  in-sample years pass only because the two halves cancel.
- **Two year-specific items sit on top, and both are localised to the hour:** the 2020 demand
  glitch (fixable input) and Elliott (a scarcity event).

## 5. Cards (none launched; the owner picks)

**A. PJM demand-spike repair — READY FOR PRECOMMIT. Zero free parameters, rule 14.** The high-side
twin of nyiso-99's promoted `demand_dropout_screen`. Three bad hours in the keeper's served demand:

| year | hour (sidecar index → date) | served | neighbours | model effect |
|---|---|---|---|---|
| 2020 | 07-27 11:00 | 192.2 GW | ~127–137 GW | 28.2 GW slack, $2,000 |
| 2020 | 07-28 15:00 | 176.1 GW | ~141 GW | 13.5 GW slack, $1,972 |
| 2020 | 08-12 07:00 | 138.6 GW | ~99 GW | no slack, $44.7 vs $19.6 |
| 2024 | 11-20 11:00 | **56.3 GW** (dropout) | ~95 GW | $20.2 vs neighbours ~$33 |

Expected, stated before any solve: 2020 C3b **FAIL → PASS** (0.208 → ~0.15); 2020 C3a
18.6 % → ~14 %, **still FAIL**. It touches one training-year hour (2024), so the keeper's 2024
re-solves too. The screen's bar must be set ex ante from a measured physical bound (e.g. PJM's
published all-time peak, or the series' own ramp distribution), **never** from these four hours.
Must repair at the source (`eia930.demand`), so it is ISO-agnostic code and every ISO shard gets a
cell under rule 28(c).

**B. Elliott (2022) — owner decision.** Clearing it clears 2022 C3a and C3b. But it is a
scarcity event (whether the model's outage windows carry that week's forced outages was NOT measured here), and the handoff's own reading is that no forecast-admissible signal reaches single-event
days (SPP-39). The only admissible input on disk is daily Eastern-hub gas. The model's daily shape
comes from Henry Hub, and even a perfect gas day would not reproduce $3,500 hours without the
outages. **I recommend accepting 2022 as an Elliott-driven miss rather than building for one
event.** It is out-of-training and never downgrades the ISO (rule 30(c)).

**C. The compression itself (Lever C) — the real structural card.** Both halves are now measured
per marginal family. **CC-marginal hours run 16–20 % high in every year; CT/ST-marginal hours run
low in every year but 2020.** pjm-h17 already located the CT half (a 22.8 GW CT_PEAKER econ shelf
priced below PJM's own offers; `pjm_ct_measured_max_reprice` has never been armed in any PJM
bundle). This finding adds the CC half. Neither half alone is safe: fixing only the top tail makes
2020 worse and pushes 2023/2024 negative. So the card must be chartered as the **pair**, and the
PRECOMMIT must state that the in-sample C3a may move **either way**, and that under rule 1 that is
not grounds to reject it.

---

## 6. Retrievability

No solve was run. Nothing is on shard disk. Both probe JSONs are committed with this doc.
