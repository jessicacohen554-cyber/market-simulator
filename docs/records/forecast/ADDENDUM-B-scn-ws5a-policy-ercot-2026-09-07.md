# ADDENDUM B — the eleven ERCOT policy legs, re-differenced against THE PIN's REF

**Owed by** `FINDING-scn-ws5a-policy-ercot-2026-09-06.md` §7 item 1, and named again by
`FINDING-scn-ws5a-resolve-ercot-2026-09-07.md` §4 items 1 and 4 · **Lane**
ERCOT-POLICY-ADDENDUM-B (with SCN-RESOLVE-G1-RECHECK) · **Model** Opus (`claude-opus-5`) ·
**Date** 2026-09-07 · **Branch** `claude/scn-resolve-g1-recheck-t13bm6` · **PRECOMMIT**
`docs/handoffs/PRECOMMIT-scn-resolve-g1-recheck-2026-09-07.md` (pushed before any measurement).

**ZERO LP.** Every number is read from a committed artifact: the eleven policy legs'
`full_horizon_summary.json` / headline CSVs, the three re-solved load legs in
`results/scn-campaign-load-2026-09-06-r2/ERCOT/`, and the **pre-fix** REF recovered from git
history at `c29f6107^` (rule 15 `[R-DASHBOARD]`: git history is the record). No leg was re-solved.

---

## 0. Bottom line

1. **The re-difference is exact arithmetic and it lands cleanly.** The new REF differs from the
   deleted pre-fix one in **two quantities only** — CO2 (−7.9521 Mt at 2029, −16.0087 at 2030) and
   clean share (+0.0258, +0.0512). `unserved`, `curtailment`, `generation`, `avg_price`,
   `negative_price_hours` and every 2026–2028 value are **byte-identical**. So exactly two of §2's
   columns move, in exactly two years, by exactly those amounts.
2. **About 60 % of ERCOT's headline 2030 policy abatement was the control's own retrofit screen.**
   CARB-HI's ΔCO2 at 2030 goes **−26.7447 → −10.7360 Mt**; CARB-LO **−26.6103 → −10.6016**;
   CES-P10 **−26.0387 → −10.0300**. The correction removes 16.0087 Mt from every REF-paired arm,
   i.e. **60.2 %** of CARB-LO's headline number.
3. **VOL-HI's entire 2029–2030 CO2 effect was the control.** ΔCO2 **−7.9504 → +0.0017** (2029) and
   **−16.0087 → +0.0000** (2030). Against the correct REF the voluntary row's CO2 delta is **zero
   in all five years**, its `gas_cc_ccs` generation is byte-identical to REF's (21.575 / 46.463 TWh)
   and its retrofit schedule reproduces REF's **to the tenth of a MW** (0 / 2,763.8 / 5,763.8). This
   **re-scores the policy FINDING's own P-15** from MISS to **HIT** (§5).
4. **ALL-CLEAN's sign flip is WITHDRAWN.** §2.5 read ALL-CLEAN vs REF as +41.63 / +42.78 / +6.81 /
   **−0.42** / **−11.78** Mt and drew a reading from the sign change. Against the new REF it is
   +41.6259 / +42.7772 / +6.8144 / **+7.5276** / **+4.2334** — **positive in every year**. ALL-CLEAN
   never goes CO2-negative against ERCOT's reference case.
5. **Claim (a) — "the CCS retrofit row is a NULL for the policy reading" (§4 reading iv) — is FALSE
   at 2028, and it is ALSO false at 2029–2030, though for a smaller number.** At 2028 the new REF
   converts **0 MW** while the carbon and CES-premium arms convert **2,932–2,996 MW**: the row is
   the policy's, entirely. At 2029–2030 REF converts on its own, but the arms still carry
   **+3,165 to +3,232 MW** of policy-attributable conversion (§3.2). The correct statement is not
   "null" and not "all policy" — it is **a durable ~3.2 GW policy increment on top of a control that
   converts 5.76 GW by 2030**. And the increment is a **carbon/clean-attribute-price** response
   specifically: `CES-T80` adds only 185–187 MW and `VOL-HI` adds **exactly 0**.
6. **Claim (b) — the +2.28 / +2.89 TWh unserved attribution — does NOT close, and the FINDING's
   named cause was wrong.** Every arm's Δunserved is **unchanged in every cell** (§4, Table C),
   because REF's unserved never moved. The capture derate is measured at **exactly zero** (2028:
   2,947.6 MW converted, Δunserved 0.0000). **The real driver is measured here and it is the entry
   screen**: every arm carrying +2.2832 TWh at 2029 also carries **Δthermal −500 MW** (gas_ct
   500 → 0, replaced by 500 MW of solar); CES-P30 carries −1,500 MW and +6.9661 TWh; CES-T80
   −3,500 MW and +16.8184 TWh; **VOL-HI carries Δthermal 0 and Δunserved exactly 0.0000** — a
   perfect control. Monotone in the firm-MW loss, with the derate contributing nothing.
7. **What is NOT affected, stated so it is not re-litigated:** every **2026–2027** delta (identical
   to the digit — the "VALID" label §2 gave those years is confirmed by measurement, not assumed);
   every **2028** delta (the new REF's 2028 is identical to the old one); the whole **§2.6
   leg-vs-leg** table (both sides at the pin, REF cancels — all seven rows recomputed and
   reproduced exactly); §2.2's negative-price and premium-arithmetic readings; §2.3's CES dual;
   §2.4's voluntary dual; and every **Δcurtailment**.

---

## 1. Gate verdicts

Pre-registered in PRECOMMIT §2 before any number was computed. Structural, kill-only.

| id | gate | verdict |
|---|---|---|
| **T2-G1** | base validity | **PASS** — all eleven legs `git.sha = bdfb3095`, `dirty = false`; new REF `de9c68e19316910e` at the same pin. No leg excluded. |
| **T2-G2** | read-back identity | **PASS** — every ΔCO2 the FINDING §2 quotes is reproduced from `arm_absolute − pre-fix REF_absolute` to 1e-3, in all 11 legs × 5 years, **plus** all seven §2.6 leg-vs-leg rows. |
| **T2-G3** | 2026–2027 invariance | **PASS** — new REF's 2026, 2027 **and 2028** absolutes are identical to the pre-fix REF's on all six headline quantities. |
| **T2-G4** | claim (a) re-scored | **DONE** — §3. Claim FALSE at 2028; false-but-smaller at 2029–30. |
| **T2-G5** | claim (b) re-scored | **DONE** — §4. Δunserved unchanged; the FINDING's attribution replaced by a measured one. |

**T2-G1's basis, and a correction to a reading aid.** The policy `report/G*` CSVs' `*_bau` columns
are **not** REF — each group's report is referenced to that group's own first case (the FINDING §7
item 8 already said so). They are unusable as a control and were not used as one here. The pre-fix
REF vector came from `git show c29f6107^:results/scn-campaign-load-2026-09-06/ERCOT/report/
ercot_headline_deltas.csv`; the post-fix one from the rebuilt report at HEAD.

---

## 2. The control, pre-fix vs THE PIN — the only thing that moved

| quantity | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| REF CO2 Mt **pre** | 214.3926 | 255.9732 | 285.6966 | 305.1914 | 328.8742 |
| REF CO2 Mt **new** | 214.3926 | 255.9732 | 285.6966 | **297.2393** | **312.8655** |
| **Δ** | 0.0000 | 0.0000 | 0.0000 | **−7.9521** | **−16.0087** |
| REF clean share pre → new | 0.3953 → 0.3953 | 0.3519 → 0.3519 | 0.3257 → 0.3257 | 0.3246 → **0.3504** | 0.3172 → **0.3684** |
| REF unserved TWh | 0.3816 | 4.6218 | 41.3892 | 76.3864 | 127.2204 | 
| REF curtailment TWh | 4.3337 | 4.9079 | 4.9079 | 4.9079 | 4.9194 |
| REF generation TWh | 597.1376 | 674.2659 | 728.3662 | 796.4267 | 862.5258 |
| REF avg price $/MWh | 73.12 | 828.16 | 2853.66 | 3501.60 | 4092.42 |

The last four rows are **identical pre and post in every year** — one row each, not two. That is
why the addendum is short: only ΔCO2 and Δclean share change, and only at 2029–2030.

The same holds for the LOAD-HI pairing base used by `CARB-MID+LOAD-HI` and `ALL-CLEAN`: CO2
321.8841 → 313.1458 (2029) and 342.2814 → 325.4633 (2030), clean share 0.3102 → 0.3367 and
0.3071 → 0.3584; unserved 360.9840 / 538.8695 TWh and curtailment 4.9079 **unchanged**.

---

## 3. Claim (a) — the CCS retrofit row

### 3.1 The schedules, as measured

Cumulative `gas_cc_ccs` capacity, MW:

| leg | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| **REF (new control)** | 0 | 0 | **0** | 2,763.8 | 5,763.8 |
| LOAD-HI (new) | 0 | 0 | **0** | 2,932.1 | 5,932.1 |
| CARB-LO | 0 | 0 | **2,932.2** | 5,928.8 | 8,928.8 |
| CARB-MID | 0 | 0 | **2,947.6** | 5,928.8 | 8,928.8 |
| CARB-HI | 0 | 0 | **2,984.0** | 5,965.3 | 8,965.3 |
| CES-P10 | 0 | 0 | **2,986.0** | 5,969.5 | 8,969.5 |
| CES-P20 / CES-P20+VOL-HI | 0 | 0 | **2,986.0** | 5,954.6 | 8,954.6 |
| CES-P30 | 0 | 0 | **2,990.7** | 5,989.2 | 8,983.4 |
| CARB-MID+LOAD-HI / ALL-CLEAN | 0 | 0 | **2,995.8** | 5,995.7 | 8,995.7 |
| **CES-T80** | 0 | 0 | **0** | 2,951.2 | 5,948.9 |
| **VOL-HI** | 0 | 0 | **0** | **2,763.8** | **5,763.8** |

### 3.2 Policy-attributable conversion (arm − new REF), MW

| leg | 2028 | 2029 | 2030 |
|---|---|---|---|
| CARB-LO | **+2,932.2** | +3,165.0 | +3,165.0 |
| CARB-MID | **+2,947.6** | +3,165.0 | +3,165.0 |
| CARB-HI | **+2,984.0** | +3,201.5 | +3,201.5 |
| CES-P10 | **+2,986.0** | +3,205.7 | +3,205.7 |
| CES-P20 | **+2,986.0** | +3,190.8 | +3,190.8 |
| CES-P30 | **+2,990.7** | +3,225.4 | +3,219.6 |
| ALL-CLEAN | **+2,995.8** | +3,231.9 | +3,231.9 |
| **CES-T80** | **0.0** | **+187.4** | **+185.1** |
| **VOL-HI** | **0.0** | **0.0** | **0.0** |

### 3.3 The reading

- **At 2028 the FINDING's "null" is FALSE.** The control converts nothing; the carbon and
  CES-premium arms convert 2.93–3.00 GW. The whole 2028 row is the policy's, and the policy pulls
  ERCOT's first retrofit forward **a full year**.
- **At 2029–2030 it is false by a smaller number, not true.** REF converts 2.76 / 5.76 GW on its
  own, but every carbon and premium arm still carries a **durable +3.17 to +3.23 GW** on top —
  the 2028 head-start propagating forward at the annual cap. Roughly **36 %** of CARB-HI's 8.97 GW
  at 2030 is policy-attributable; the other 64 % is the control's.
- **It is a carbon / clean-attribute-price response, not a "policy" response.** `VOL-HI` — a $7
  voluntary WTP whose row cannot credit CCS — reproduces the control's schedule **exactly**, and
  `CES-T80` (an ACP-escape target, dual pinned at $50 in every year) adds only 185–187 MW and
  converts **a year late**. The two arms carrying no CCS-crediting price add nothing.
- **The FINDING's own residual question is now answerable.** §4 reading (iv) asked whether
  "CARB-HI's 2,984 vs CARB-LO's 2,932 MW is signal". Against the correct control it is: the
  ordering CARB-LO < CARB-MID < CARB-HI < CES-P10 ≲ CES-P20 < CES-P30 < ALL-CLEAN is **monotone in
  the CCS-crediting price at 2028** and holds at 2029–2030 (CES-P20's small 2029 dip aside, where
  its extra wind displaces a marginal retrofit). The spread is small — 63.6 MW across the whole
  carbon ladder at 2028 — but it is a signal, not noise, and it was invisible against a control
  that converted zero.

---

## 4. Claim (b) — the unserved attribution

### 4.1 Δunserved does not move (Table C)

| case | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| CARB-LO / CARB-MID / CARB-HI / CES-P10 | 0.0000 | 0.0000 | 0.0000 | **+2.2832** | **+2.8907** |
| CES-P20 / CES-P20+VOL-HI | 0.0000 | 0.0000 | 0.0000 | **+2.2832** | **+1.3111** |
| CES-P30 | 0.0000 | 0.0000 | 0.0000 | **+6.9661** | **+4.8995** |
| CES-T80 | 0.0000 | 0.0000 | 0.0000 | **+16.8184** | **+16.4469** |
| **VOL-HI** | 0.0000 | 0.0000 | 0.0000 | **0.0000** | **0.0000** |
| CARB-MID+LOAD-HI / ALL-CLEAN (vs LOAD-HI) | 0.0000 | 0.0000 | 0.0000 | **0.0000** | **0.0000** |

Old and new are **equal in every cell to 1e-9 TWh**, because the control's unserved never moved.
The routed expectation that this number would "largely close against the control" is **not what the
artifacts say**, and it is reported here at full magnitude: it closes by zero.

### 4.2 What actually causes it — measured, not argued

The FINDING §2.1 attributed it to "the capture parasitic derate on 5.9 / 8.9 GW of converted CC".
The derate's contribution is **exactly zero**, and the artifacts say so three separate ways:

1. **2028 is the clean isolation.** Every carbon and premium arm converts 2.93–3.00 GW at 2028 and
   carries **Δunserved = 0.0000 TWh** and **Δthermal_mw = 0.0**. Conversion at 3 GW moves unserved
   by nothing.
2. **`VOL-HI` is the perfect control.** It converts 2,763.8 / 5,763.8 MW — the same as REF — and its
   Δunserved is 0.0000 in every year.
3. **`Δthermal_mw` explains the whole ladder.** Every arm's firm-thermal loss vs REF, and its
   unserved:

| leg | Δthermal MW (2029, 2030) | capacity swap vs REF | Δunserved TWh 2029 | 2030 |
|---|---|---|---|---|
| CARB-LO / MID / HI, CES-P10 | **−500** | gas_ct 500 → 0, +500 MW solar | **+2.2832** | **+2.8907** |
| CES-P20 | **−500** | as above, plus 2030 +2,000 wind / −2,000 solar | +2.2832 | +1.3111 |
| CES-P30 | **−1,500** | gas_ct 500 → 0, +1,500 solar (2029); +5,000 wind / −3,500 solar (2030) | **+6.9661** | +4.8995 |
| CES-T80 | **−3,500** | gas_ct 500 → 0, +3,500 solar (2029) | **+16.8184** | **+16.4469** |
| VOL-HI | **0** | none | **0.0000** | **0.0000** |

At 2029 — the year where the only difference between the arms is *how much solar replaces how much
firm gas* — the relation is monotone and near-linear: **4,566 / 4,644 / 4,805 MWh of extra unserved
per MW of firm thermal not built**, at −500 / −1,500 / −3,500 MW. 2030 is noisier only because the
premium and target arms also swap 2–5 GW of solar for wind.

**The corrected statement for the record:** the carbon and CES arms' extra unserved energy is the
**entry screen substituting solar for the 500 MW gas-CT the reference case builds in 2029**, not a
capture parasitic derate. The retrofit raises the converted unit's heat rate, not its `pmax`; on an
ISO already shedding 76–127 TWh at $3,500–4,100/MWh, a heat-rate change moves no deliverable MWh.

### 4.3 The consequence for the abatement numbers

Some of the residual ΔCO2 in §5's Table A is **load not served**, not abatement. CARB-HI's 2030
by-fuel movement vs the new REF is `gas_cc_ccs` **+24.408**, `gas_cc` **−24.189**, `gas_ct`
**−4.257**, `solar` **+1.114**, `coal` −0.009 TWh. The gas-CT leg is not displaced generation —
it is 500 MW of capacity the arm never built, showing up as +2.891 TWh of extra unserved and
+1.114 TWh of solar. Any statement that ERCOT carbon pricing abates ~10.7 Mt at 2030 must carry
that with it: **part of the number is bought with unserved energy**, and the ISO has no capacity
instrument to stop it. (The FINDING §7 item 4 already routed the same point for CES-T80's
+16.8 TWh; it applies, smaller, to every carbon arm.)

---

## 5. The re-differenced tables

### A. ΔCO2 vs the correct control (Mt) — old → **NEW**

| case | base | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|
| **CARB-LO** | REF | +0.0000 → **+0.0000** | −0.3930 → **−0.3930** | −8.4528 → **−8.4528** | −18.2399 → **−10.2878** | −26.6103 → **−10.6016** |
| **CARB-MID** | REF | +0.0000 → **+0.0000** | −0.9280 → **−0.9280** | −8.5789 → **−8.5789** | −18.2932 → **−10.3411** | −26.6392 → **−10.6305** |
| **CARB-HI** | REF | +0.0000 → **+0.0000** | −2.3348 → **−2.3348** | −8.9475 → **−8.9475** | −18.5303 → **−10.5782** | −26.7447 → **−10.7360** |
| **CES-P10** | REF | −0.0001 → **−0.0001** | +0.0000 → **+0.0000** | −7.6385 → **−7.6385** | −17.5816 → **−9.6295** | −26.0387 → **−10.0300** |
| **CES-P20** | REF | +0.0000 → **+0.0000** | +0.0000 → **+0.0000** | −7.6556 → **−7.6556** | −17.2393 → **−9.2872** | −25.7953 → **−9.7866** |
| **CES-P30** | REF | +0.0000 → **+0.0000** | +0.0000 → **+0.0000** | −7.6067 → **−7.6067** | −19.4285 → **−11.4764** | −29.2882 → **−13.2795** |
| **CES-T80** | REF | +0.0003 → **+0.0003** | −0.0014 → **−0.0014** | +0.0002 → **+0.0002** | −16.7306 → **−8.7785** | −27.2637 → **−11.2550** |
| **VOL-HI** | REF | +0.0003 → **+0.0003** | −0.0014 → **−0.0014** | +0.0002 → **+0.0002** | −7.9504 → **+0.0017** | −16.0087 → **+0.0000** |
| **CES-P20+VOL-HI** | REF | +0.0004 → **+0.0004** | −0.0015 → **−0.0015** | −7.6555 → **−7.6555** | −17.2383 → **−9.2862** | −25.7953 → **−9.7866** |
| **CARB-MID+LOAD-HI** | LOAD-HI | +0.0000 → **+0.0000** | −0.0232 → **−0.0232** | −9.0151 → **−9.0151** | −17.1172 → **−8.3789** | −25.1825 → **−8.3644** |
| **ALL-CLEAN** | LOAD-HI | +0.0003 → **+0.0003** | −0.0230 → **−0.0230** | −9.0151 → **−9.0151** | −17.1172 → **−8.3789** | −25.1825 → **−8.3644** |
| **ALL-CLEAN** | **REF** | +41.6259 → **+41.6259** | +42.7772 → **+42.7772** | +6.8144 → **+6.8144** | −0.4245 → **+7.5276** | −11.7753 → **+4.2334** |

Every REF-paired row moves by exactly **+7.9521** (2029) and **+16.0087** (2030); every
LOAD-HI-paired row by exactly **+8.7383** and **+16.8181**. That is the arithmetic check
(PRECOMMIT P-D) and it holds in all 60 cells.

### B. Δclean share — old → **NEW**

| case | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| **CARB-LO** | +0.0000 | +0.0000 | +0.0292 | +0.0571 → **+0.0313** | +0.0804 → **+0.0292** |
| **CARB-MID** | +0.0000 | +0.0000 | +0.0294 | +0.0571 → **+0.0313** | +0.0805 → **+0.0293** |
| **CARB-HI** | +0.0000 | +0.0000 | +0.0297 | +0.0574 → **+0.0316** | +0.0807 → **+0.0295** |
| **CES-P10** | +0.0000 | +0.0000 | +0.0298 | +0.0575 → **+0.0317** | +0.0809 → **+0.0297** |
| **CES-P20** | +0.0000 | +0.0000 | +0.0299 | +0.0575 → **+0.0317** | +0.0820 → **+0.0308** |
| **CES-P30** | +0.0000 | +0.0000 | +0.0299 | +0.0629 → **+0.0371** | +0.0886 → **+0.0374** |
| **CES-T80** | +0.0043 | +0.0047 | +0.0045 | +0.0492 → **+0.0234** | +0.0764 → **+0.0252** |
| **VOL-HI** | +0.0000 | +0.0000 | +0.0045 | +0.0298 → **+0.0040** | +0.0548 → **+0.0036** |
| **CES-P20+VOL-HI** | +0.0000 | +0.0000 | +0.0342 | +0.0613 → **+0.0355** | +0.0854 → **+0.0342** |
| **CARB-MID+LOAD-HI** | +0.0000 | +0.0000 | +0.0289 | +0.0536 → **+0.0271** | +0.0764 → **+0.0251** |
| **ALL-CLEAN** (vs LOAD-HI) | +0.0041 | +0.0045 | +0.0332 | +0.0574 → **+0.0309** | +0.0798 → **+0.0285** |

REF-paired rows fall by exactly 0.0258 (2029) and 0.0512 (2030); LOAD-HI-paired by 0.0265 and
0.0513. **The crediting convention still binds** (resolve FINDING §2.4): `gas_cc_ccs` counts as
clean under `clean_capture`, so both the old and new numbers are convention-dependent and must
name it.

### C. Δunserved, Δcurtailment, and the rest

**Unchanged in every cell** — Δunserved is Table §4.1; Δcurtailment, Δgeneration,
Δnegative-price-hours, Δavg-price and every 2026–2028 value are identical to the FINDING §2 as
published. §2.6's leg-vs-leg table is recomputed and reproduces exactly: CARB-HI − CARB-LO
−0.4947 / −0.2904 / −0.1344; CARB-MID − CARB-LO −0.1261 / −0.0533 / −0.0289; CES-P30 − CES-P10
+0.0318 / −1.8469 / −3.2495; CES-P20 − CES-P10 −0.0171 / +0.3423 / +0.2434; (CES-P20+VOL-HI) −
CES-P20 +0.0001 / +0.0010 / 0.0000; CES-T80 − VOL-HI 0.0000 / −8.7802 / −11.2550; ALL-CLEAN −
(CARB-MID+LOAD-HI) 0.0000 in all three years.

---

## 6. What this does to the policy FINDING's own predictions

Two of its §5 scores were the control's fault, not the prediction's. Re-scored:

| pred | as written | scored in the FINDING | **re-scored on the correct control** |
|---|---|---|---|
| **P-15** | voluntary \|ΔCO2\| < 2 Mt every year | HIT 2026–28; **MISS 2029–30** (7.95 / 16.01) | **HIT in all five years** — 0.0003 / 0.0014 / 0.0002 / **0.0017** / **0.0000** Mt. The miss was the pre-fix REF's. |
| **P-6** | ΔCO2 shrinks toward 0 by 2029–30 under scarcity | MISS vs REF (contaminated); HIT leg-vs-leg | **STILL A MISS vs REF, now uncontaminated** — CARB-HI runs −2.335 → −8.948 → −10.578 → **−10.736** Mt: it *grows*, because the arms carry a durable +3.2 GW of extra conversion. The leg-vs-leg HIT is untouched. |

Reported both ways deliberately. The re-difference is not a rehabilitation exercise: it rescues one
prediction and leaves the other failing for a cleaner reason.

---

## 7. Scored predictions — this lane's own, as pre-registered

- **P-A (claim (a) split, with the VOL-HI/CES-T80 sharpening) — HIT.** FALSE at 2028, and VOL-HI
  reproduces the control's schedule 0 / 2,763.8 / 5,763.8 to the tenth of a MW while CES-T80
  converts a year late. **One qualification against myself:** I wrote "TRUE at 2029–2030" following
  the routing. It is **not true** — the arms carry +3.17 to +3.23 GW there too (§3.2). The
  contamination reading survives at 2029–30 in the sense that most of the row is the control's;
  the word "null" does not survive in any year.
- **P-B (the +2.28 / +2.89 does not close, and the cause is the 500 MW gas-CT the arms do not
  build) — HIT, both limbs.** Δunserved is unchanged in every cell, and the Δthermal ladder
  (−500 / −1,500 / −3,500 MW → +2.28 / +6.97 / +16.82 TWh, with VOL-HI at 0 / 0) identifies the
  entry screen as the driver, monotone and near-linear at 2029.
- **P-C (2026–2027 unchanged) — HIT**, and stronger: **2028 is unchanged too**.
- **P-D (the arithmetic gate) — HIT.** Every REF-paired arm moves +7.9521 / +16.0087 Mt and every
  LOAD-HI-paired arm +8.7383 / +16.8181, in all 60 cells, to 1e-4.
- **E-1 (offered as a directional read, not scored) — lands at 60.2 %.** 16.0087 / 26.6103 of
  CARB-LO's 2030 headline abatement was the control's own retrofit screen.

---

## 8. Routed, not executed

1. **`FINDING-scn-ws5a-policy-ercot-2026-09-06.md` §2 and §4 should now be read only through this
   addendum** at 2029–2030. Its §7 item 1's standing embargo ("until it lands, no ERCOT
   policy-vs-REF delta at 2028–2030 should be quoted") is **lifted for 2028** (unchanged) and
   **lifted for 2029–2030 in favour of §5's Table A**. A pointer is added to that FINDING's §7
   item 1 in this commit; its §2/§4 body text is the parent lane's to restate, not this lane's.
2. **The campaign synthesis and any cross-ISO policy rollup** carrying ERCOT's −26 Mt figure needs
   the −10.6 Mt one. Desk's region.
3. **§4.3's "abatement bought with unserved energy"** belongs beside the load lane's adequacy
   reading and the FINDING's own §7 item 4 — it is now a property of every carbon arm at ERCOT,
   not only CES-T80.
4. **The dump-crediting defect (§7 item 2) is untouched by this addendum** and still inflates every
   credited volume in §2.3–§2.5 by ~4.9 TWh/yr. Nothing here fixes or measures it.

---

## 9. Files

- `docs/handoffs/ADDENDUM-B-scn-ws5a-policy-ercot-2026-09-07.md` (this file)
- `docs/handoffs/PRECOMMIT-scn-resolve-g1-recheck-2026-09-07.md` (pushed pre-measurement)
- `docs/handoffs/FINDING-scn-ws5a-policy-ercot-2026-09-06.md` §7 item 1 — a one-line pointer to
  this addendum, and nothing else in that document touched.

No bundle, no registry sidecar, no solve, no config, no `src/`. Zero LP.
