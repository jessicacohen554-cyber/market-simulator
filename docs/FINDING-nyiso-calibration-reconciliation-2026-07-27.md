# NYISO calibration reconciliation — what "calibrated" actually requires (nyiso-86)

**Date:** 2026-07-27 · **Session:** nyiso-86 (adjudication; **no LP was run**,
keeper unchanged: `2026-07-26-nyiso-81-floor-rederive`, determination NOT-YET)
· **Basis:** the keeper's committed bundle (hourly sidecars,
`legitimacy_diagnostics.json`, dashboard payload + bench parts), the committed
actuals (EIA-930 NYIS frame, EIA-923 bench, NYISO pal zonal load,
`actual_lmp_hourly_NYISO.parquet`, measured neighbor DA LMPs), and one
`run_year(fleet_only=True)` fleet rebuild (no solve) for the CHP heat-rate
audit — all scoring-side, rule 14. · **Premise:** nyiso-85's C3c attribution
(`docs/FINDING-nyiso-c3c-scarcity-formation-2026-07-26.md` §7), merged to main.

**The question this answers:** NYISO's LMP criteria all PASS while most of the
fleet fit is bad and mostly UNGATED. Which of the bad parts are (i) gated and
failing, (ii) ungated but structurally wrong, (iii) by construction? And what,
concretely, stands between NYISO and a determination that could carry a
calibration-complete marker?

**TL;DR.** Two FAILs block everything, and both now have a named root cause:

1. **C1 (load-bearing)** is dominated by a **demand-basis wedge**, not a
   dispatch defect: the model serves the EIA-930/pal metered-load basis
   (147.0 TWh in 2023) while C1's actuals sit on the EIA-923 plant-metered
   basis (126.66 gen + 23.45 net imports = 150.1) — a **+2.1–2.9 %-of-load
   wedge that exceeds C1's entire ±2.0 %-of-load band** and lands wholly on
   the one free family (gas), mostly on the marginal class (CC_REGULAR).
   The existing, default-off `td_loss_factor` (scenarios.py:4412) is the
   registered instrument for exactly this. A secondary ~1 TWh within-gas
   misallocation (CC_CHP over on sub-physical steam-credited heat rates;
   CT/ST_CHP under with no steam-host floor) accounts for the rest (§2, §4).
2. **C3c (supporting)** stays as nyiso-85 attributed it — no above-SRMC summer
   price formation, mainland roof ~$258 — and this session adds that the same
   flat-SRMC pathology **also drives the biggest unscored defect**: the
   interchange hourly shape (§3). The model's internal diurnal price swing is
   $7–17 against the real $22–43, so the seam spread inverts and the pinned
   monthly import volume is bought overnight and starved at the peak.

Everything else in the charter's defect list is either by-construction/pinned
(name it, never quote it as skill) or a representation limit the rubric
correctly leaves ungated (§5). The realistic near-term determination is
**still NOT-YET** until BOTH FAILs close; neither is ledgerable (§6). The C1
lane is concrete and likely one session; the C3c lane (§7g-1 of nyiso-85)
remains the long pole (§7).

---

## 1. The gate board vs. the fleet reality

`scripts/calibration_verdict.py 2026-07-26-nyiso-81-floor-rederive`,
reproduced this session on current main:

| criterion | tier | verdict | content |
|---|---|---|---|
| C1 fuel-mix | LOAD | **FAIL** | one cell: 2023 CC_REGULAR −4.11 TWh / −2.6 pp; all six 2025 classes SKIP on preliminary-923 vintage |
| C2 system volume | LOAD | PASS | complete-vintage years defer to C1's per-class gate; 2025 gas fallback −2.3 % |
| C3a / C3b | LOAD | PASS | 2023 +2.6 % / 2024 −5.5 % / 2025 −6.7 % vs DA (diagnostic) |
| C3c price tail | SUPP | **FAIL** | 3/0/9 vs RT 10/12/42 h >$300 — attributed, nyiso-85 §7 |
| C4 dispatch corr | SUPP | PASS | gates gas+coal only; gas r 0.887/0.854/0.803 declining |
| C5a CO2 | LOAD | CAVEAT | 2025 +8.1 %, commercial band |
| C6/C7/C8 | PROT | PASS | C8 note: 2024 ST_GAS 36.2 % forced, grounded (D-4 + D-1) |

What the board does not score: interchange hourly shape (r 0.38–0.44 on
19–24 TWh of net imports), nuclear hourly shape (2025 r 0.562 — a pinned
class), CT_CHP/ST_CHP diurnal shape (profile_r 0.13–0.73), CT_PEAKER
volatility (cv_ratio 2.4–5.1, 48–86 % floor-forced, 1.4–2.0 % of load). §5
classifies each.

---

## 2. Task 4 — C1 2023 CC_REGULAR −4.11 TWh: a basis wedge plus a CHP misallocation

**Not a vintage artifact.** 2023 (and 2024) are final-vintage EIA-923 years;
the completeness SKIP machinery only touches 2025. The cell is real — but it
decomposes into two parts, only one of which is dispatch.

**2.1 The demand-basis wedge.** Full per-class table, 923-grid `classFull`
(bench) vs payload `gmModel`, TWh:

| 2023 class | model | actual | Δ | | 2024 class | model | actual | Δ |
|---|--:|--:|--:|---|---|--:|--:|--:|
| CC_REGULAR | 31.19 | 35.30 | **−4.11** | | CC_REGULAR | 36.19 | 38.04 | −1.85 |
| CC_CHP | 13.17 | 11.30 | +1.87 | | CC_CHP | 15.11 | 13.47 | +1.64 |
| ST_GAS | 9.87 | 8.70 | +1.16 | | ST_GAS | 8.71 | 11.07 | −2.36 |
| CT_CHP | 1.43 | 2.49 | −1.07 | | CT_CHP | 1.19 | 2.30 | −1.12 |
| CT_PEAKER | 1.42 | 2.26 | −0.84 | | CT_PEAKER | 1.33 | 2.13 | −0.81 |
| ST_CHP | 0.76 | 0.94 | −0.19 | | ST_CHP | 0.74 | 0.78 | −0.04 |
| **gas family** | **57.84** | **61.00** | **−3.16** | | gas family | 63.27 | 67.80 | −4.53 |
| TOTAL (all classes) | 123.39 | 126.66 | −3.27 | | TOTAL | 130.03 | 134.54 | −4.51 |

The energy balance that explains the family row:

| year | model load (= EIA-930 NYIS Demand) | 923-grid gen + measured NI | wedge | wedge % of load | gas family Δ |
|---|--:|--:|--:|--:|--:|
| 2023 | 147.05 | 126.66 + 23.45 = 150.11 | **+3.06** | 2.08 % | −3.16 |
| 2024 | 150.46 | 134.54 + 20.35 = 154.89 | **+4.43** | 2.94 % | −4.53 |
| 2025* | 151.55 | 133.95 + 19.09 = 153.04 | +1.49 | 0.98 % | −1.63 |

*2025 actuals are preliminary-923 (understated), so the 2025 wedge is a lower
bound; expect it to reopen to full size when the final vintage lands (and the
model's own hydro budget input, currently 21.05 vs 24.10 TWh, to rise with it).

The chain of custody for the wedge, verified this session:

- The model's demand input is the **EIA-930 `NYIS hourly` Demand** series
  (`data/eia930/demand.py:366`), which is internally the balance
  `Demand = Net generation − Total interchange` (gap 0.00 in every year) and
  **tracks NYISO's own pal zonal metered load month-by-month to ±0.01 TWh**
  (annual: 147.05 vs 147.04 in 2023). So model demand = NYISO-visible metered
  load. The raw NYIS by-fuel columns are separately unreliable (NUC reads 0
  for Apr-2023 against four operating units; SUN reads 0.0 all year) — the
  930 *generation* basis is derived/loss-exclusive, not plant-metered.
- The model's own balance closes (gen 123.39 + NI 23.82 ≈ load 147.05 +
  storage losses): a **lossless LP serving metered load**.
- C1's actuals are **plant-metered EIA-923** (grid-delivered). Plant-bus
  generation + tie-metered imports exceed delivered metered load by
  transmission losses plus any NYISO-invisible generation — the measured
  +2.1–2.9 % wedge above. NYISO can only be scored on the 923 basis while
  *serving* the 930/pal basis by under-generating the difference.
- Every non-gas class is pinned (nuclear monthly-CF must-run, hydro monthly
  budgets, wind/solar delivered CF, imports monthly recon band), so **the free
  gas family absorbs ~100 % of the wedge every year** (−3.16 vs −3.27 total;
  −4.53 vs −4.51). In 2023 it concentrated in the marginal class and broke
  C1's band (±min(2 % load, 8) ≈ ±2.94 TWh); in 2024 it happened to split
  across CC_REGULAR (−1.85) and ST_GAS (−2.36), both inside the band — a pass
  by distribution luck, not by fit.

**The instrument already exists and is registry-clean:** `td_loss_factor`
(ScenarioConfig, default 0.0, keeper 0.0) grosses demand up to the generation
level the fleet must actually serve. Identification is the measured
reconciliation above (~2.1–2.9 % on final vintages; use a multi-year mean,
cite the reconcile, re-derive only when the source vintages update — rule 23),
NOT the C1 residual. Rule 13 admissibility: transmission losses are physics;
the factor regenerates for a forward year (fraction of forecast load) and
responds to changed conditions. Left open for the lane: pin the wedge's
decomposition (losses vs. NYISO-invisible small generation — the Gold Book
NYCA energy line is the cross-check) before choosing the value.

**2.2 The within-gas misallocation (~1 TWh of the 2023 cell).** With the
wedge closed (+3.06 to the family, overwhelmingly the marginal CC_REGULAR),
2023 CC_REGULAR lands ≈ −1.05 TWh — in band — with the remainder explained by
CC_CHP +1.87 / ST_GAS +1.16 over-dispatch displacing CC_REGULAR merit energy,
and CT_CHP −1.07 / CT_PEAKER −0.84 under-dispatch. The CC_CHP overshoot has a
named cause (§4.2: sub-physical steam-credited heat rates on 27.8 % of CHP
capacity). Note CT_CHP is C1-EXCLUDED, but its shortfall still redistributes
into gated cells through the family total.

---

## 3. Task 2 — interchange r ≈ 0.40: the monthly pin is fine; the within-month economics are inverted

Verdict on the charter's (a)/(b)/(c): **(c) price-formation error at the
seams is the dominant defect**, framed by (a) — the observed r is exactly what
a correct monthly pin plus wrong-signed hourly economics produces — with a
real but secondary (b) capacity clip. Measured from the keeper's sidecars vs
the EIA-930 hourly schedule:

- **The headline r is the pin, not skill.** Within-month hourly r (per-month,
  12 values/yr): mean **0.01 / 0.13 / 0.21** (2023/24/25), range −0.30…+0.44.
  The annual r of 0.404/0.441/0.383 is almost entirely month-level variation,
  which the reconciliation band supplies by construction. (D-10 already
  declares NYISO `imports` a pinned class; the r must never be quoted as
  forecast skill.)
- **The diurnal shape is inverted (2023 profile r = −0.43).** Model
  hour-of-day means peak overnight (hod 1–3 ≈ 3,400–3,500 MW) and trough at
  the evening peak (hod 16–18 ≈ 2,090–2,140); the actual is mildly
  load-following (hod 15–19 ≈ 2,790–2,880 vs overnight ≈ 2,410–2,690).
  2024 profile r = −0.09, 2025 = +0.51.
- **Mechanism, quantified.** With `nyiso_import_hub_prices` on (keeper), the
  deep tranches price at the measured neighbor hourly DA LMP + $1
  (`model/interchange/nyiso.py:54`), so the LP allocates the pinned monthly
  quota to the hours with the largest internal-minus-neighbor spread. The
  model's internal load-weighted price swings only **$7.4 / $8.2 / $16.5**
  hod-max-to-min (flat CC-stack SRMC), while real PJM DA swings $23.5 / $27.9
  / $41.2 — so the model spread is +$10–23 overnight and ~$0 to −$3 at hod
  16–18, and the quota goes overnight. The REAL NYISO DA price swings
  **$22.5 / $25.1 / $43.3** — same steepness as its neighbors — and the real
  NYISO−PJM DA spread never inverts by hour of day (2023 −$0.9…+$4.1; 2024
  +$4.9…+$8.9; 2025 +$12.7…+$22.0). The defect is not the seam plumbing; it
  is that **the model's internal diurnal price formation is ~3× too flat** —
  the same at-SRMC pathology nyiso-85 §7d attributed for C3c, now measured
  outside the tail. This also *is* nyiso-85's §7g item 3 (imports at 46–49 %
  of max in the actual tail hours): the peak-starved allocation is the
  seam-side face of the missing peak price formation.
- **(b) is real but secondary:** the aggregate clearable depth is the
  `NYISO_simultaneous_import` cap 4,350 MW (`model/interchange/spec.py:1356`,
  a Gold Book / IRM-study *planning* figure). The measured net import exceeds
  it in **287 / 314 / 145 hours** (max 5,929 / 5,662 / 5,872 MW) — the model
  is structurally unable to reproduce the deepest import hours, which are
  exactly the tight ones. Rule 14: the measured operating envelope
  contradicts the planning limit; reconcile (a measured simultaneous
  operating limit, or per-seam ties) rather than keep the estimate.

**Coupling warning (rule 14 dynamics):** fixing the import shape alone would
*worsen* C3c — peak-shifted imports depress peak duals — because the current
peak-starved imports are silently compensating for the missing above-SRMC
price formation. Conversely the §7g-1 offer-stack lane automatically
re-shapes imports toward the peak through the existing hub-priced seam. These
must land as one lane (§7), with the roof fix leading.

---

## 4. Task 3 — the small classes: one boxcar, two out-of-representation hosts, one offer-curve defect

Rule 19 inventory (D-2, keeper): CT_PEAKER is floored by `reliability_floor`
only (h14–21); CT_CHP by `chp_steam` only (12/25/6 % of class energy); ST_CHP
carries **no floor at all** (most NYISO cogens have `chp_pmin_cf = 0` in
`thermal_tranches_NYISO.csv`); CC_CHP's `chp_steam` forcing is ~0 (it runs
economically above any floor). `chp_export_floor_measured` and
`chp_steam_floor_p25` are both default-off and off in the keeper; the NYISO
tranche artifact predates WP-3 (no `steam_level_cf` column).

**4.1 CT_PEAKER — right window, boxcar edges; formally rule-17 compliant.**
Hour-of-day means (2023, MW): model ≈ **1–33 off-window, 453–494 in h14–21**;
actual ramps smoothly 58 → 659 → 111 across the day. The floor's driver
(design-cooling afternoon AC peak), window (h14–21) and forward story
(temperature-ramp coefficients) exist and D-4 reads 0 % off-window binding —
the defect is the step edges: reality has a morning ramp (h6–13: 198–359 MW)
and evening decay the model zeroes. That is what cv_ratio 2.4–5.1 measures;
profile_r 0.82–0.92 is fine. The class is 1.4–2.0 % of load (ungated), and
even if the final 2025 vintage tips it over the 2 % floor it would score as a
grounded over-budget pass (D-4 clean + D-1 gates pass: r 0.923, cv_ratio 2.37
≥ 0.5). **Verdict: real mis-shape, cosmetic priority** — if touched at all,
re-shape the existing floor onto its own temperature-ramp driver (no new
mechanism).

**4.2 CC_CHP / CT_CHP / ST_CHP — the driver (host steam) is out of
representation, and the offers are miscosted.** Two distinct facts:

- **Shape:** the CEMS-measured class profiles are nearly flat (actual
  off-peak CV 0.006–0.114 — host-steam-driven around-the-clock operation).
  On a flat profile, profile_r is statistically degenerate — 2024 CT_CHP
  r = 0.132 is noise on a ±1 MW wiggle, **not a shape defect to chase**. The
  model instead gives these classes merit-order evening humps. This is a
  representation limit the rubric correctly leaves ungated for level-small
  classes.
- **Level (grid basis):** CC_CHP **+1.87/+1.64/+4.07** over; CT_CHP
  −1.07/−1.12/−0.90 under; ST_CHP −0.19/−0.04/+0.54 (small). The CC_CHP
  overshoot has the exact signature that added PJM to the steam-credit
  heat-rate correction (`data/fleet/arrays.py:166` — CAISO/PJM only, "other
  ISOs join as audited"): this session's fleet rebuild audit finds **27.8 %
  of NYISO CHP capacity carries physically impossible power-only heat rates**
  (min 3.82; e.g. 209 MW @ 4.84, 325 MW @ 5.16, 226 MW @ 5.98 MMBtu/MWh),
  which at $2.5–3.5 gas clear as the cheapest thermal in every hour and
  displace CC_REGULAR. The under-run side (CT/ST_CHP) is the missing
  steam-host operating-level floor; the rule-13-clean instrument already
  exists (`chp_steam_floor_p25`, the caiso-89/WP-3 multi-year host-level
  statistic) and needs only the NYISO artifact re-derived with
  `steam_level_cf` (rule 23: method/source extension, CAISO precedent).
  MISO's audit precedent applies verbatim: correct the HRs only together with
  the floor, since the correction alone pushes the under-running classes
  further under.

Net effect of the §4.2 pair is a within-gas reallocation of ~2–3 TWh — the
other half of the C1 2023 cell (§2.2). It must be probed **jointly** with
`td_loss_factor`: the floors add gas energy (pushing CC_REGULAR down), the
wedge adds demand (pulling it up); only the joint A/B tells the 2023 cell.

---

## 5. The classification the charter asked for

| defect | class | disposition |
|---|---|---|
| C1 2023 CC_REGULAR −4.11 TWh | **(i) gated+failing** | ~3.1 TWh demand-basis wedge (§2.1, instrument exists) + ~1 TWh CHP allocation (§4.2). Must fix; lane nyiso-87 (§7). |
| C3c 3/0/9 vs 10/12/42 | **(i) gated+failing** (supporting) | Attributed (nyiso-85 §7d): no above-SRMC summer formation, $258 mainland roof. NOT ledgerable — a proven model gap, not a measured-input limitation. Lane §7g-1. |
| Interchange hourly r 0.38–0.44 | **(ii) ungated, structurally wrong** | Within-month allocation inverted by the flat internal price shape (§3) — the seam-side face of the C3c root cause; secondary SIL clip (287/314/145 h). Biases nothing gated today (C4 gates gas/coal only; monthly level is pinned), but flatters C3c by keeping peaks import-starved. Rides the §7g-1 lane; SIL reconcile is a rule-14 item. |
| CC_CHP over / CT_CHP–ST_CHP under | **(ii) ungated, structurally wrong** | Real defects with named causes (§4.2): sub-physical steam-credited HRs (27.8 % of CHP capacity) and a missing host-level floor. DOES bias a gated criterion (the C1 2023 cell, via the family total). Part of lane nyiso-87. |
| CT_CHP/ST_CHP profile_r 0.13–0.73 | **(ii)→representation limit** | Degenerate statistic on ~flat actual profiles; correctly ungated; do not chase r. Level handled above. |
| CT_PEAKER cv_ratio 2.4–5.1, 48–86 % forced | **(ii)→cosmetic** | Boxcar edges on a correctly-windowed floor (§4.1); ungated by materiality and would score grounded even if material. |
| ST_GAS 2024 36.2 % forced | adjudicated grounded | C8 conditional pass per rule 20 (D-4 clean + D-1 pass), surfaced as a note. Its h0–23 window is driver-defensible (24 h in-city voltage/reliability commitment) but makes D-4 vacuous for this floor — a rubric-sharpness observation, not a defect. |
| nuclear hourly r 0.562–0.817 | **(iii) by construction** | ~100 % `nuclear_mustrun` pinned to measured monthly CF; hourly r reflects within-month outage timing granularity. Never quote as skill. |
| wind/solar r = 1.0 | **(iii) by construction** | D-10 `delivered_pinned`; excluded from skill claims. |
| hydro, imports (levels) | **(iii) by construction** | Monthly budgets / EIA-930 recon band. 2025 hydro −3.06 TWh is a preliminary-vintage artifact in the budget *input*, self-healing when the final 923 lands. |

D-10 free-class C1 stands at 9/10 — the pinned-class inflation is visible and
bounded.

---

## 6. The determination adjudication

Per the rubric §2 decision table, **any criterion FAIL forces NOT-YET**, and a
beyond-commercial-band criterion can only be reclassified by a ledger entry
naming a *measured-input limitation rather than a model defect*.

- **C1** is a genuine mixed case — the dominant term is an input-basis
  mismatch, not dispatch — but the honest disposition is to **fix it, not
  ledger it**: the registered instrument exists (`td_loss_factor`), the
  identification is measured, and the residual CHP term is a real model
  defect in any case.
- **C3c** is **not ledgerable at all**: nyiso-85 §7b explicitly closed the
  ceiling-note escape hatch ("the gap is real and reachable, and it is a
  model gap"). There is no path to CALIBRATED-WITH-CAVEATS around it.
- C5a's 2025 +8.1 % is an auto commercial-band caveat (unbudgeted,
  compatible with CALIBRATED-WITH-CAVEATS). Watch item: the C1 lane adds
  ~2–3 % gas burn, which moves CO2 toward the +10 % band edge — score C5a in
  every lane probe.
- The 2025 SKIPs (preliminary vintage) cap the best attainable determination
  at CALIBRATED-WITH-CAVEATS regardless — which is therefore **the realistic
  target determination**, and it is blocked today by exactly two criteria.

**Answer to the framing question:** what stands between NYISO and a
calibration-complete marker is (1) the C1 closure lane — concrete, admissible,
plausibly one session of joint probes + a keeper re-solve with LOYO; (2) the
C3c / §7g-1 summer-peak offer-formation lane — the long pole, structural, now
carrying the interchange shape as a second quantified payoff; then (3) a
re-solved all-years keeper, re-scored determination, and the owner's
calibration-complete call. The ungated fleet defects do not independently
block: they either ride lane (1) (CHP), ride lane (2) (interchange shape), or
are correctly-ignored representation limits (flat-profile r, CT_PEAKER
edges).

---

## 7. Prioritized lanes (evidence → instrument → gate flipped)

1. **nyiso-87 — C1 closure (load-bearing; highest priority).** Joint A/B
   probes vs a same-HEAD zero-delta control, then a full 2023–2025 keeper
   candidate:
   - `td_loss_factor` for NYISO, identified from the measured 923+NI-vs-load
     reconciliation (2.08 % / 2.94 % on final vintages; decide the value from
     a cited multi-year mean, cross-checked against the Gold Book NYCA
     energy/losses line — never from the C1 residual). Expected: closes ~3 of
     the 4.11 TWh 2023 cell, ~4.4 into 2024's spread.
   - CHP allocation pair (§4.2): audit-in NYISO to
     `CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` + re-derive
     `thermal_tranches_NYISO.csv` with the WP-3 `steam_level_cf` and arm
     `chp_steam_floor_p25`. Probe jointly (MISO precedent: correction alone
     worsens the under-runners).
   - Score C1/C2/C3a/C5a on every arm; LOYO within 2023–2025 before any
     keeper swap (rule 22). Watch C5a 2025 (+8.1 % → +10 % edge risk) and
     C3a 2023 (+2.6 % will rise with load).
2. **C3c / §7g-1 — summer-peak offer formation above oil parity (long
   pole).** Unchanged charter from nyiso-85, now with two additions from this
   session: (a) the target is measurable outside the tail — the internal
   diurnal price swing must roughly triple ($7–17 → $22–43) before the roof
   even matters; (b) the interchange within-month shape comes along for free
   through the existing hub-priced seam, and any import-shape "fix" attempted
   *before* the roof is rule-14-backwards (§3 coupling warning).
3. **SIL reconcile (rule 14, small).** Replace the 4,350 MW planning figure
   with a measured simultaneous operating envelope (the schedule exceeds it
   287/314/145 h/yr, max 5,929 MW). Small, independent, and it feeds both
   lanes (peak import depth). Document the planning-vs-operating boundary in
   the constant's comment.
4. **CT_PEAKER edge shaping (cosmetic; only if touched).** Re-shape the
   existing reliability floor onto its temperature-ramp driver instead of the
   h14–21 boxcar. No determination impact under the current rubric.

**Do not chase:** CT_CHP/ST_CHP profile_r (degenerate on flat actuals, §4.2);
nuclear hourly r (pinned); anything in the nyiso-85/84/83 closed list (J/K
ladders, East ladder, spin gate as C3c lever, RT-transient framing, LI steam
OOM as C3c route, winter-spread arm — both nyiso-84 flags stay default-off).

---

## 8. Reproducibility notes

- All numbers derive from committed artifacts: the keeper bundle
  (`results/calibration/nyiso81_floor_rederive/`), its dashboard payload
  (`frontend/data/backcast/runs/2026-07-26-nyiso-81-floor-rederive.js`,
  gzip+base64 `runGz`) and bench parts
  (`frontend/data/backcast/bench/NYISO/<year>.json.gz`), the EIA-930 NYIS
  frame (`data/eia930/frames._eia_hourly_frame_filled`), NYISO pal load
  (`data/raw/zone-specific-demand/NYISO/`), measured neighbor DA LMPs
  (`data/neighbor_price.neighbor_lmp_hourly`), and
  `actual_lmp_hourly_NYISO.parquet`.
- The CHP heat-rate audit rebuilt the keeper fleet via
  `run_year(fleet_only=True)` with the bundle's `meta.json` flags (the
  `legitimacy_diagnostics.load_or_rebuild_floors` pattern) — no LP solve.
- Keeper flag states verified from `meta.json`: `priced_interchange`,
  `nyiso_firm_imports`, `nyiso_import_reconciliation`,
  `nyiso_import_hub_prices` all True; `td_loss_factor` 0.0;
  `chp_export_floor_measured` False.
- No out-of-training year was touched (NYISO carries no calibration-complete
  marker; 2022/2019/≤2021/H1-2026 remain quarantined). No run produced, so
  nothing was registered on the dashboard (per the charter's pure-adjudication
  outcome).
