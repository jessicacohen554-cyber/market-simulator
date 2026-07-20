# Is this model fit to forecast retirements and new entry? — 2026-07 verdict

> **Rewritten 2026-07-13 (P-3C,
> `docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md` §2 T3.3/T3.2).**
> Supersedes the 2026-06-15 ERCOT-only verdict (git history preserves it). Scope is
> now **all six ISOs**, and the verdict is graded against *measured* program
> evidence, not code inspection: the Tier-1 driver battery (P-1A,
> `docs/handoffs/driver-battery-2026-07-12.md`), the CR-1 curve validation (P-2A,
> `docs/handoffs/capacity-price-validation-2026-07-12.md`), the accreditation-basis
> adjudication (P-2B, `docs/handoffs/accreditation-basis-memo-2026-07-12.md`), the
> CR-3.1 ELCC curves (P-2C, `docs/handoffs/elcc-curves-p2c-2026-07.md`), the first
> full-horizon 2026–2050 runs (P-3A, `docs/handoffs/full-horizon-findings-2026-07-12.md`),
> the capacity-market equilibrium battery (P-3B,
> `docs/handoffs/equilibrium-battery-2026-07-12.md`), the HEAD capacity hindcasts
> (`docs/hindcast-reports/{ercot,pjm}-2021-2025-realized-p2c*-2026-07-12.md`), and
> the cross-model corridor + SOM benchmark report (this session,
> `docs/handoffs/cross-model-corridor-2026-07-13.md`). All evidence is in-train
> (2021–2025 hindcasts, 2026+ forecast probes); no holdout year was solved or
> scored (rule 22).

**Question.** Can this model's capacity-evolution loop — economic retirement,
economic new entry, adequacy backstop, storage value stack — legitimately drive
entry/exit *forecasts*, per ISO and per technology?

**Verdict (one line).** **Mostly no — and the two market designs now fail in
opposite, well-measured directions.** In the five capacity-market ISOs the
fixed capacity payment makes fossil retirement *arithmetically impossible*
(§2) and inverts the retirement signal onto nuclear, the one class the payment
doesn't carry; in energy-only ERCOT the screens over-retire coal/steam ~15×
against history while missing all solar entry. The defensible uses are narrow:
ERCOT storage-entry pace (the single green hindcast band), within-ERCOT
relative ranking of the dispatchable fleet, and directional single-driver
sensitivities (carbon, gas, load, net-CONE, tech-cost — 24/25 Tier-1
expectations PASS). Absolute entry/exit calls are not yet defensible in any
ISO, and MISO cannot produce a forecast at all.

---

## 1. What changed since the 2026-06-15 verdict

The old verdict's five "what it would take" items, honestly scored:

| 2026-06 next step | Status at HEAD | Evidence |
|---|---|---|
| Realistic going-forward FOM (CT 21 / CC 30 / coal 45) | **DONE** — ATB values are the `ScenarioConfig` defaults (flip 2026-07-07) | `scenarios.py:338-362`, `fom-scarcity-defaults-flip-2026-07-07.md` |
| AS revenue in the screens | **PARTLY DONE** — hourly reserve-price signal in the retirement/entry margin (`screen_reserve_value_enabled`, default on; co-opt duals else ORDC adder); the ERCOT AS *market-revenue* module `as_revenue_enabled` remains **default off** | `scenarios.py:664,697`; capacity-economics plan Stage 2 |
| CONE-class entry hurdles; `gas_ct`/storage as entry candidates; price-duration expected revenue | **DONE** — `_NEW_ENTRY_TECHS` includes `gas_ct`; storage has its own value stack; entry margins are price-duration based | `capacity.py:1489`, `storage.py` |
| Planning-reserve-margin backstop | **DONE (design-resolved)** — tri-state: ON by default in capacity-market ISOs, OFF in ERCOT (G-41 decision) | `capacity.py:2463` |
| Calibrated annual scarcity rent per class | **NOT DONE as calibration — and correctly so** (rule 13 forbids pinning rent to the residual). The structural replacements (screen basis = attainable pro-forma margin; reserve-price signal; AS co-opt lane) moved ERCOT first-screen-year CT revenue **1.5 → 17.2 $/kW-yr vs the Potomac SOM ≈ 68 anchor** — i.e. from ~2 % to ~25 % of benchmark. The level gap is still open (G-20/G-22 lane) | capacity-economics plan Stage-2 note |

Plus mechanisms the old verdict didn't have: CR-1 sloped capacity demand
curves (landed, **default off** per P-2A), CR-3.1 penetration-indexed VRE ELCC
(landed, default on), the confirmed-retirement registry (default on), IRA §45U
and the 45Y/48E ramps, AEO2025-derived fuel files (P-1D), and — most
importantly — an actual measurement apparatus: driver ladders, forecast
invariants I1–I14, capacity hindcasts, the equilibrium battery, and the
full-horizon harness. **The 2026-06 verdict was written from code inspection;
this one is written from runs.**

## 2. The central analytic finding: the fixed capacity payment makes fossil exit impossible

P-3B found NEISO retires **exactly 0 thermal MW over all 25 forecast years**
even at a 67.5 % reserve margin, and hypothesized the flat capacity payment
alone covers going-forward cost. The no-LP ratio check its §8.3 requested has
now been run and confirms it
(`docs/handoffs/capacity-revenue-fom-ratio-2026-07-13.md`, PR #2160; this
session's independent re-derivation agrees to rounding) — the registry
arithmetic the screens actually use, `net_cone_per_kw_yr × (1 − EFORd)`
(`MARKET_DESIGN`, `constants.py:2558`; `EFORD`, `constants.py:760`) against
the FOM-only going-forward cost (`scenarios.py:338-362`, coal ×1.3 per
`retirement_fom_multiplier_coal`):

**Flat capacity payment ÷ going-forward cost (fixed mode, the active default):**

| class | GFC $/kW-yr | PJM (100) | NYISO (110) | NEISO (95) | MISO (80) | CAISO (90) |
|---|--:|--:|--:|--:|--:|--:|
| gas_ct | 21.0 | **4.5×** | **4.9×** | **4.3×** | **3.6×** | **4.0×** |
| gas_cc | 30.0 | **3.2×** | **3.5×** | **3.0×** | **2.5×** | **2.9×** |
| gas_st | 35.0 | **2.7×** | **2.9×** | **2.5×** | **2.1×** | **2.4×** |
| oil | 25.0 | **3.6×** | **4.0×** | **3.4×** | **2.9×** | **3.2×** |
| coal | 58.5 | **1.6×** | **1.7×** | **1.5×** | **1.3×** | **1.4×** |
| nuclear | 130.0 | *0.75×* | *0.82×* | *0.71×* | *0.60×* | *0.67×* |

Since the screen's test is `net_revenue = energy margin + reserve value +
capacity payment ≥ GFC` (`apply_economic_retirements`), a ratio ≥ 1 means the
unit **can never post a loss year, whatever the energy market does**. Every
fossil class in every capacity-market ISO is ≥ 1.3× (the ratio report's
per-fuel range is 1.26–4.92 including CCS-CC; MISO coal at 1.26 is the
closest any fossil class comes to the cliff). Nuclear is the **only** class
below 1.0 — the only class whose retirement the other revenue terms (energy
margin + §45U/ZEC attribute revenue) can actually decide. The consequences
are not hypothetical; they are the measured record:

- **T2.4c (P-3B):** zero NEISO thermal retirements, 25/25 years, including
  under a +10 GW overbuild shock.
- **PJM hindcast at HEAD:** thermal retirements −63 % vs actual; per-fuel
  recall **coal 0/6.9 GW, gas_ct 0/3.5 GW, oil 0/0.6 GW** — and the model's
  only retirements are **4.1 GW of nuclear, 100 % false** (actual nuclear
  retirements: zero). The retirement pattern is exactly the ratio table's
  ordering: the sign of the retirement signal is *inverted onto the wrong
  technology*.
- **Contrast (the control):** ERCOT, with no capacity payment, retires
  11.7 GW the year after the same +10 GW shock (T2.5) — the economic screen
  itself works when the price it reads can respond.

The CR-1 sloped curve is the designed fix, but it is default-off for cause:
fed the model's own PJM position (1.29–1.36, past the 1.045 zero-cross) it
pays **$0 every year including the near-cap 2025/26 shortage** (P-2A Pass 2).
So today's choice is between a capacity price that is *always too high to
allow exit* (fixed) and one that is *always $0* (curve on an untrustworthy
position). Neither supports an exit forecast in PJM/MISO/NYISO/NEISO/CAISO.

## 3. ERCOT: the opposite failure, plus one genuine success

The HEAD realized hindcast (`ercot-2021-2025-realized-p2c-2026-07-12.md`)
against 2021–2025 actuals:

| call | actual | model | verdict |
|---|--:|--:|---|
| thermal retirements | 1.5 GW | **22.8 GW (+1386 %)** — coal 14.0 vs 0.9, gas_st 8.8 vs 0.0 | massive over-retirement |
| solar additions | 25.1 GW | **0.0 GW (−100 %)** | total miss |
| wind additions | 12.7 GW | 15.0 GW (+18 %) | order right, band FAIL |
| gas additions (CC+CT) | 3.9 GW | 0.0 GW (−100 %) | miss |
| storage additions | 13.7 GW | **14.0 GW (+2 %) ✅** | **the one green band** |
| CO2 2025 | 193.6 Mt | 95.2 Mt (−51 %) | fleet+dispatch error compound |

The over-retirement direction is the old verdict's prediction realized: with
scarcity/AS revenue at ~25 % of the SOM benchmark (§1) and no capacity
payment, marginal coal/steam margins read negative and the screen cuts them
— the "systematic over-retirement bias" the 2026-06 document forecast for
peakers now lands on coal/gas-steam. (Note the direction *flipped* for the
tail-dependent classes themselves: 2026-07-05 vintage hindcasts retired
~9.7 GW; the week of AS-co-opt/FOM merges moved it to 22.8 GW — the screens
are highly sensitive to the still-uncalibrated scarcity level, which is
exactly why absolute exit calls remain unfit.) The storage-pace PASS is real
but partly pace-capped by design (`storage_deployment` pace mapping), so it
validates the value stack + cap jointly, not the economics alone.

## 4. Verdict table

"Fit" = usable today for a decision at that grain, with documented caveats.
Grades: **YES / PARTIAL / NO / BLOCKED**. Every NO carries its blocker ID (§5).

| # | Use case | Fit? | Decisive evidence | Blockers |
|---|---|:--:|---|---|
| 1 | **Directional single-driver sensitivity** (carbon, gas, load level, tech cost, net-CONE, IRA cliffs) — ERCOT/PJM | **YES** | Tier-1: 24 PASS / 1 FAIL; carbon slope 0.46–0.52 $/MWh per $/t at the analytic band edge; T1.2 duality untested (no live mass-cap) | #2064 (the 1 FAIL, load ladder) |
| 2 | **Relative ranking of the dispatchable fleet** — ERCOT | **YES** | Backcast keepers reproduce merit-order-by-profitability, stable 2023–25 | — |
| 3 | **Storage entry pace** — ERCOT | **PARTIAL** | Hindcast +2 % (only green band); T1.9 saturation monotone ↓ | pace-cap co-determines the pass; `as_revenue_enabled` default off (BLK-6) |
| 4 | **Retire/keep nuclear + efficient CC** — ERCOT | **PARTIAL** | Both kept in model and reality; margins far from threshold in both | inherits BLK-5 sensitivity |
| 5 | **Retire/keep coal / gas-steam / peakers** — ERCOT | **NO** | Hindcast +1386 % thermal retirement, 96 % false-retire | BLK-5, BLK-6 |
| 6 | **New build vs CONE (solar/wind/gas)** — ERCOT | **NO** | Solar 0 vs 25.1 GW; gas 0 vs 3.9 GW; wind +18 % | BLK-6, BLK-7, BLK-8 |
| 7 | **Retire/keep fossil** — PJM/MISO/NYISO/NEISO/CAISO | **NO (by construction)** | §2 ratio ≥ 1.3× all fossil classes; T2.4c zero retirements ×25 yr; PJM hindcast coal/CT recall 0 % | BLK-3, BLK-4, BLK-9 |
| 8 | **Retire/keep nuclear** — capacity-market ISOs | **NO (sign-inverted)** | Only class the flat payment doesn't carry; PJM hindcast: 4.1 GW retired, 100 % false | BLK-9 (+§45U/ZEC interaction untested at HEAD) |
| 9 | **New-entry thermal** — capacity-market ISOs | **PARTIAL (direction only)** | T1.7a entry monotone in net-CONE; T2.4b entry stops after +10 GW (energy channel); but PJM hindcast mix badly wrong (gas_ct +347 %, gas_cc +41 %) and the payment's CT/CC accreditation distortion is +20 %/−6 % (P-2B §3.4) | BLK-3, BLK-4 |
| 10 | **New-entry VRE** — capacity-market ISOs | **NO** | PJM hindcast solar −100 %, wind +271 %; VRE entry screens earn **zero capacity revenue** even where the ISO pays it | BLK-7, BLK-8 |
| 11 | **Reserve-margin / adequacy trajectory** (timing of tightness) | **NO** | I12 FAILs every scored ISO; two-phase de-firm→overshoot (CAISO→60 %, NEISO→67 %, PJM 0.3 %→32 %); ERCOT #2064 non-monotone scarcity; T2.2b zero oscillation | BLK-2, BLK-3, BLK-4, BLK-9 |
| 12 | **Capacity-price forecasting** (CR-1) | **NO (instrument validated, inputs not)** | P-2A: curve shapes exact, PJM spike direction reproduces; but model position pays $0 (Pass 2), anchor −22 % (ICAP/UCAP), MISO seasonal + NYISO vintage unscoreable | BLK-3, BLK-4 |
| 13 | **Anything — MISO** | **BLOCKED** | forecast raises `ValueError` before the first solve | BLK-1 |
| 14 | **Long-horizon CO2 / energy-mix trajectory** | **NO** | corridor report: PJM CO2 +57 % / ERCOT +34 % by 2040 under default policy while every external model shows declines; direct consequence of rows 5/7/10 | BLK-9 → rows 5/7/10; corridor §1 |

**Post-flip update — rows 7–12, 14 (FF-2C, 2026-07-20, commit `dbbae9c`).**
`capacity_market_clearing` is now ON by default for **PJM/MISO/CAISO/NEISO**
(owner sign-off 2026-07-19), and R1/R4 closed the −22 % anchor error. The
qualifier **"(by construction)"** on rows 7–12/14 no longer holds for those
four ISOs: their capacity-evolution screens price on the CR-1 curve, not the
flat payment, so BLK-4 is resolved and BLK-9 is off the default path (it
persists only for unflipped NYISO). The rows stay graded **NO / PARTIAL** — the
flip does not by itself make the *forecasts* right — but the binding blocker has
**shifted**:
- **Row 7 (retire/keep fossil):** from "impossible (flat payment)" → the
  curve-ON **over-retirement wave** (BLK-10) — measured for NEISO (FF-2B: 9.3
  GW, +880 %) and PJM (RC-1A: coal +44 %). Different failure, root-caused in the
  retirement-rule + backstop lanes, not a payment issue.
- **Rows 9–11 (entry / adequacy):** the curve now moves the screens, but PJM's
  position (~1.29–1.36) sits past its curve's 1.045 zero-cross → the curve pays
  $0 (BLK-3 requirement/position half, R2/R3, still open). MISO's 2025 shortage
  year stays under-priced (RC-1A one-sided residual). BLK-7 (VRE earns no
  capacity revenue) and BLK-8 (solar entry 0) are unchanged by the flip.
- **Row 12 (capacity-price forecasting):** the instrument is validated and the
  fixed-anchor −22 % error is closed (R4); the position still pays $0 until R2/R3.
- **Row 14 (CO₂ trajectory):** downstream of rows 7/10 — unchanged in sign until
  those close.
- **NYISO / ERCOT unchanged:** NYISO stays fixed-mode (curve-ineligible, R5a);
  ERCOT is energy-only (rows 5–6 unaffected, BLK-5/BLK-6).
Measured re-runs on the flipped defaults (fresh T1.7 rig-limitation finding;
per-plant hindcast/equilibrium/tornado re-runs launched, continuation in the
FF-2C findings doc §4) —
`docs/handoffs/ff-2c-capacity-clearing-flip-execution-2026-07.md`.

Rows 1–4 are the honest extent of "fit to forecast" today. The program's own
framing stands confirmed end-to-end: *an entry/retirement loop driven by a
non-responsive capacity price cannot equilibrate* — and the backcast
dashboard's dispatch skill does not transfer to capacity evolution until the
blockers below clear.

## 5. Blocker register

| ID | Blocker | Owner / gap ID | What it blocks |
|---|---|---|---|
| **BLK-1** | `STORAGE_BASE_FLEET_MW` omits MISO → `build_default_storage` raises; **1/6 ISOs has no runnable forecast path** | P-3A ranked issue #1 (`full-horizon-findings-2026-07-12.md` §3); needs a cited EIA-860 base fleet (rules 5/24) | verdict rows — all of MISO |
| **BLK-2** | ERCOT scarcity non-monotone in load/one-pass evolution (slack hours [34,0,58] across the T1.4 ladder; [0,…,11,0,39,107] over 2026–2040) | GitHub **#2064** | row 11 (adequacy timing); any scarcity-driven exit call |
| **BLK-3** | ICAP/UCAP/FPR accreditation basis: PJM position ~18 pp too long from basis alone; anchor −22 %; payment CT/CC distortion. P-2B adopted Option A. **The anchor half is CLOSED: R1 (curve anchor 60.4→77.43 UCAP) and R4 (fixed anchor re-derived to the published basis for all four flipped ISOs) landed by FF-2C 2026-07-20 (commit `dbbae9c`) — the uniform −22 % anchor error is gone.** The requirement/position half (FPR requirement, ELCC-class supply, R2/R3/R5/R6) continues under the accreditation-basis lane. | **#1532** / P-2B memo §4; FF-2C (R4) | rows 7–12; P-2A flip prerequisite 1 (satisfied) |
| ~~BLK-4~~ | ~~`capacity_market_clearing` default-off and unflippable~~ — **RESOLVED for PJM/MISO/CAISO/NEISO (FF-2C, 2026-07-20, commit `dbbae9c`).** Flipped ON by default via `capacity_market_clearing_by_iso` (owner sign-off 2026-07-19, RC-2B flip memo §4, unblocked by the §5 D1=3 re-probe); R4 re-derived each fixed anchor to its published basis (PJM 100→77.431, MISO 80→79.8, NEISO 95→108.94, CAISO 90→88.08). NYISO remains the one exception (curve-ineligible until R5a). | P-2A §7 → **FF-2C done**; `docs/handoffs/ff-2c-capacity-clearing-flip-execution-2026-07.md` | rows 7–12 (now testable — see the row notes) |
| **BLK-5** | Retirement-screen level miscalibration, ERCOT direction (22.8 vs 1.5 GW; false-retire 96 %) | G-30/G-31 hindcast lane | rows 4–6 |
| **BLK-6** | ERCOT scarcity/AS revenue level: screens capture ~25 % of the SOM CT net-revenue anchor (17.2 vs ≈68 $/kW-yr); `as_revenue_enabled` default off | G-20/G-22 AS co-opt lane; corridor report §2 (T3.2) | rows 3, 5, 6 |
| **BLK-7** | VRE new-entry screens earn no capacity revenue anywhere (even in ISOs that pay it), and PJM wind ELCC has no published declining axis yet | audit D7; P-2C follow-ups #1/#4 | rows 6, 10 |
| **BLK-8** | Solar entry = 0 GW in BOTH hindcasts against 25.1 (ERCOT) / 13.1 (PJM) GW actual — the single largest additions miss; root cause in the entry-economics stack (cost/queue/negative-price interaction), not yet diagnosed | hindcast lane (G-30 adjacent); no dedicated gap row — **should get one** | rows 6, 10, 14 |
| **BLK-9** | Fixed capacity payment ≥ 1.3× GFC for all fossil (§2): fossil exit impossible, nuclear-only retirement inversion. **No longer the active default for PJM/MISO/CAISO/NEISO (FF-2C, 2026-07-20): they now price on the CR-1 curve, so the flat-payment arithmetic is off the default path.** Persists only for NYISO (unflipped). The curve-ON successor open item is the over-retirement wave (BLK-10). | `capacity-revenue-fom-ratio-2026-07-13.md` (PR #2160); gap-register §3.9 BLK-9; resolution = the CR chain (BLK-3+BLK-4, both now landed for the flipped ISOs via R1/R4/FF-2C), not a payment haircut (rule 13) | rows 7, 8, 11, 14 |
| ~~BLK-10~~ | ~~#2063 IRA phaseout crash~~ — **CLOSED at HEAD** (P-1C fields + regression test; verified by P-2C) | #2063 | — |

## 6. What would flip the table (ordered, no new mechanisms invented)

1. **BLK-1** is a one-session cited-data fix → unblocks MISO everywhere.
2. **P-2B Option A steps R1–R4** (anchor 60.4→77.43; FPR requirement; ELCC
   class-rating supply+payment basis; thermal-ratings intake R3) → removes
   ~2/3 of the PJM position bias and the −22 % anchor → re-run P-2A Pass 2.
   **R1 + R4 DONE (FF-2C, 2026-07-20): the −22 % anchor error is closed — PJM
   curve anchor 77.43 and every flipped ISO's fixed anchor now on its published
   basis. R2/R3 (FPR requirement + ELCC-class supply) remain.**
3. **Retirement/entry level calibration** (G-30/G-31 + BLK-8 root cause) —
   the remaining ~1/3 of the position error and the solar-entry miss. This is
   root-cause work on the screens' revenue inputs, not tuning (rules 1/13).
4. **Flip `capacity_market_clearing`** per P-2A's re-validation protocol (per
   ISO, only once its Pass-2 position lands in its curve's priced region) →
   rows 7–12 become testable; re-run T1.7 + tornado; re-run P-3A to completion
   (all six ISOs, full horizon) and P-3D re-scores.
   **DONE for PJM/MISO/CAISO/NEISO (FF-2C, 2026-07-20, commit `dbbae9c`; owner
   sign-off 2026-07-19).** The gate is ON by default via
   `capacity_market_clearing_by_iso`; R4 re-derived each fixed anchor to its
   published basis. Rows 7–12 are now *testable* rather than NO-by-construction.
   Measured post-flip behaviour so far: the fixed-mode 0-retire/nuclear-
   inversion pathology (BLK-9) is off the default path, replaced by the curve-ON
   over-retirement wave (BLK-10, e.g. NEISO 9.3 GW +880% FF-2B; PJM RC-1A
   +44%) — a successor open item root-caused in the retirement-rule + backstop
   lanes, NOT tuned. PJM's *quantitative* curve effect is still gated on the
   BLK-3 requirement/position half (its curve pays $0 past the zero-cross).
   NYISO stays unflipped (R5a). See
   `docs/handoffs/ff-2c-capacity-clearing-flip-execution-2026-07.md`.
5. **ERCOT scarcity level** stays with G-20/G-22 (structural co-opt, never a
   fitted rent) — gates rows 5–6.

Until step 4, every capacity-market entry/exit output of this model should be
labeled what it is: **a fixed-price screen, not a market equilibrium.**

---

### Sources

Program reports listed in the header; `src/market_sim/model/capacity.py`
(`capacity_revenue_per_mw_yr`, `apply_economic_retirements`,
`_NEW_ENTRY_TECHS`, `resolve_reserve_margin_build_enabled`),
`src/market_sim/config/constants.py` (`MARKET_DESIGN`, `EFORD`),
`src/market_sim/config/scenarios.py` (FOM defaults, gates);
`docs/handoffs/cross-model-corridor-2026-07-13.md` (T3.3 corridor + T3.2 SOM
tables, incl. external citations); ERCOT Potomac SOM PNM anchors as cited
there. Historical (2026-06-15) ERCOT net-revenue reconciliation: git history
of this file.
