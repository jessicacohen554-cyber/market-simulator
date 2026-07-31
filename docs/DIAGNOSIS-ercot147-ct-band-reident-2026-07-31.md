# ERCOT-147 — the measured CT-band re-identification: REFUSED EX ANTE at Phase 0, no solve spent

**Session:** 2026-07-31 (the ERCOT-145 §4 / ERCOT-146 §4 reopen-condition
lane). **Keeper (unchanged):** `2026-07-31-ercot145-gas-daily-shape` (bundle
`ercot145_gas_daily_arm`). **Probe (committed, reproducible):**
`scripts/probes/ercot147_ct_band_phase0.py`; record
`results/calibration/ercot147_ct_band_phase0.json`. Preconditions verified:
default `cache_key` byte-stable (`603c2498bf71d21d`), `audit_keepers.py`
PASS 0/0.

**Charter.** The ONLY licensed route to retiring the fitted CT_PEAKER
`offer_curve_by_group` multipliers (econ_low 1.27 / econ_high 2.18 /
peak 13.15 vs phys 0.723/0.727/1.0 — the +$13/+$35/+$292 per MWh margins of
ERCOT-145 §1): re-identify the band levels from ERCOT's own SCED TPO conduct,
as physical HR (`campd_ct_heat_rates_ERCOT.csv`, basis decided) + start
amortization (`campd_ct_run_lengths_ERCOT.csv`) + a measured conduct margin,
zero swept parameters. Phase 0 pre-committed as no-LP corpus sufficiency with
the ex-ante-refusal exit. **Phase 0 adjudicates: the corpus cannot identify a
CT band level — REFUSED, nothing armed, nothing stamped, the fitted bands
stay as attributed DOF** (ledger row `offer_curve_by_group`, gas side;
n_residual 6 unchanged).

## 1. Coverage is NOT the blocker — record it honestly

The four on-disk extracts
(`60_DAY_SCED_DISCLOSURE_..._{2024,2025}_{tail,control}_days.parquet`) carry
an abundant CT (SCLE90/SCGT90) sample: **157 resources / 12.03 GW of max-HSL
capability appear in ALL FOUR extracts** (160 / 12.22 GW overall, vs the
curated CT_PEAKER class's 8,816 MW in 192 rows), 52–72 % of online rows carry
a submitted TPO curve (78–86 % of offline rows — the curve is standing
conduct), and the modal curve's reach spans the capability range (cap-wtd p50
reach = 1.00 of max HSL, p10 = 0.94), so committed/econ/peak capacity windows
are representable. Row counts are 41k–91k curve-carrying online
resource-intervals per extract. If the object existed, this corpus would see
it.

## 2. The adjudicating fact — the CT conduct object is not a level

The ERCOT-144 standard governs what this corpus licenses: a **LEVEL**, and
only when the submitted object is time-stable (the coal precedent: Oak
Grove's modal TPO curve repeats identically ×1436 across subsets AND years;
ERCOT-143 §3 forbids any time-shape identification off these 82 probe days).
Measured on the CT fleet, every stability leg fails:

- **Modal-curve identity (the licence test): 11 of 160 resources
  (0.47 of 12.22 GW)** hold the same modal (MW, price) curve across the four
  extracts. On the **price-tuple-only key** — so ambient HSL derating cannot
  be the explanation — still only **20 resources / 1.13 GW**. The cap-wtd
  median modal share is **0.045** (price-only 0.06): a CT resource's
  most-repeated curve covers ~5 % of its own curve-carrying intervals,
  against coal's near-total repetition.
- **Not a $ level:** the per-resource **daily-median** price at 50 % of the
  curve's own reach has cap-wtd median relative IQR **0.64** (0.66 restricted
  to online rows; 0.60/0.56 at the 10 %/90 % windows). Oak Grove's whole
  curve spread was $0.36 on $9.
- **Not a gas multiple:** normalizing by the daily Henry Hub staircase (the
  keeper's own `gas_daily_shape` series) leaves rel IQR **0.32–0.43**, and
  the daily gas correlation is only 0.64–0.70 at the cap-wtd median with a
  **p25 of 0.02** — a quarter of the capacity's conduct is essentially
  uncorrelated with HH.
- **The year pair refutes BOTH admissible zero-parameter forms at once.** On
  the extracts' own days, mean HH moves ×**1.97** 2024→2025. A fixed $ level
  predicts a per-resource y25/y24 ratio of 1.0; a fixed HR-multiple form
  predicts 1.97 for every resource. Measured cap-wtd IQR: **1.26–1.99**
  (median 1.78) — Laredo (MDANP_CT1–6, 1.68 GW) moves ×2.6–3.1
  (gas-outpacing) while HAYSEN moves ×1.6–1.9 and much of the mid-fleet
  moves ×1.3 — the two forms fail in opposite directions across resources.
- **The repricing grain is daily:** intra-day share of p50 variance is
  **0.14** cap-wtd median (p25 0.04). The submitted CT curve is a
  daily-repriced object. Identifying a daily-varying conduct is a
  **time-shape identification**, which this corpus categorically cannot
  license: 82 non-random probe days (price-tail + control selections),
  **no 2023 disclosure on disk at all**, and h0–h8 present in only one of
  four extracts (and the one all-24h subset shows the level differs by ~9 %
  across the h11-22 / h23-h10 split, so the daytime-only sampling is not
  neutral either). The within-extract subset dependence is the same fact
  from the other side: per-resource p50 across the four extracts spreads
  0.71 (relative, cap-wtd median).

## 3. Two compounding in-repo gaps, quantified

- **The conduct-vs-fuel-basis confound is unresolvable on disk.** 63–67 % of
  CT capacity's daily p50 sits **below** its own sheet-HR × HH burn
  (cap-share 0.629/0.627/0.674/0.663 across the four extracts) — either
  genuine sub-cost offering (the ERCOT-138 CC family) or sub-HH local gas
  (2024 Waha traded at/below zero; Laredo's ×2.6–3.1 year move is exactly
  what a collapsed-then-recovered local basis would produce). No Texas hub
  daily series (Waha, HSC, Katy) exists in `data/raw/gas-prices/` (the
  ERCOT-146 `winter_citygate_daily` gap), so the measured conduct margin the
  identification needs cannot be separated from local fuel cost with
  anything on disk.
- **No CT resource→plant crosswalk exists.** The per-plant resolution the
  template requires has 6 of 165 CT_PEAKER sites accepted in
  `ercot-dam-plant-crosswalk.csv` (the auto-matcher demonstrably fails on
  CTs — BRAUNIG/DANSBY/SANDHSYD rows carry capacity-coincidence garbage
  matches). A ~150-site hand crosswalk (the ERCOT-144 10-plant pattern at
  15× scale) is buildable but pointless while §2 stands. Recorded for the
  successor: Morgan Creek's six CTs (MGSES_CT1–6, ~80 MW each) ARE in the
  corpus — the target-population note from ERCOT-146 carries forward.

## 4. Adjudication and the data-intake successor

**REFUSED EX ANTE — no solve spent, nothing armed, nothing stamped.** No
ScenarioConfig field, no matrix cell verdict (no mechanism was tested; there
is no cell for a mechanism that was never built), no dashboard registration
(no run produced — the ERCOT-142/143/145/146 precedent). Keeper, DOF ledger
(n_residual 6), and all gate verdicts unchanged. Holdouts untouched (the
extracts are 2024–2025 probe days; HH daily is read only on those days;
rule 22). ERCOT-scoped (rule 25). The fitted CT_PEAKER multipliers remain
exactly what the ledger says they are: residual-identified DOF, attributed,
with no licensed measured replacement available from the data on disk.

**The reopen condition (unchanged in kind from ERCOT-145 §4, now with its
data prerequisites made precise) is a THREE-PART DATA INTAKE, each part
rule-22/owner-authorization territory:**

1. **A CT-scoped 60-Day SCED extension**: full-span (all days, all hours)
   Gen Resource Data extracts for 2023–2025 restricted to SCLE90/SCGT90
   resources — sized so the daily conduct object and its drivers can be
   measured rather than sampled on 82 selected days. (The disclosure is
   public ERCOT MIS data; the four existing extracts were day-subset fetches
   — this is a fetch+curate lane, not a new source.)
2. **A Texas hub daily gas basis series** (Waha + HSC/Katy) — the SAME
   intake the `winter_citygate_daily` ERCOT cell has been waiting on
   (licensing must be checked before promising it; the pjm-139 W1 day-scale
   bound applies to whatever it buys) — without which §3's confound survives
   any corpus size.
3. **A CT resource→plant hand crosswalk** (~150 sites; the ERCOT-144
   pattern), which also settles the Morgan Creek and 9-mixed-facility-plant
   target-population questions (ERCOT-146 §3).

Only with (1)+(2) on disk can a future lane even TEST whether a stable
conduct object exists (e.g. a margin over local daily fuel); if it does, the
identification then takes the committed physical-HR artifact (gross/net
basis decided fleet-wide, per ERCOT-146 §2) and the run-length start term as
its other legs — as one identification, never a stack (rule 19; the
ERCOT-145 G stamp stands). If it does not, the fitted bands stay attributed
DOF and the honest closure is the C6 ledger route.

**Expectation management (stated ex ante in the charter, repeated here):**
CT_PEAKER is 1.36/1.21/0.92 % of ISO load — this lane's value was DOF
retirement (C6 hygiene, rule 21), never gate movement; the C3a/C3b/C3c
residual stays attributed to RT scarcity formation (closed lane).

**Alternates assessed, both data-intake-first (surfaced, not attempted,
unchanged from ERCOT-146):** matrix §5.1 item 7 (WP-B nodal curtailment —
station→area crosswalk not in-repo); `winter_citygate_daily` ERCOT — which
§4.2 above now shows is a shared prerequisite of THIS lane's reopen, making
it the natural next intake.

**Open owner rulings carried (surfaced, not decided):** (1)
`gas_hh_monthly_shape` matrix row (26c gap); (2) per-gate dispositions of the
attributed gates (C3a/C3b/C3c tail; C7-2023 non-offer-surface); (3)
`split_coal_tranches` delete-vs-inert; (4)
`ercot_offer_hrmult_ep_rebasis`/`_bands` matrix rows (26c); (5) Martin Lake
lignite class composition (ERCOT-143 §7.3, with the ERCOT-146 mixed-facility
evidence and this session's §3 Morgan Creek corpus-presence note).
