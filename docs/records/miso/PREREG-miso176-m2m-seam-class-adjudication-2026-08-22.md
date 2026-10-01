# PREREG miso-176 — the M2M/CMP seam-class binding-reality measurement and the `m2m_seam_entitlement_cap` adjudication

**Session miso-176, 2026-08-22.** Executes miso-174 §7 item 3 (the charter's
scope items 2–3): with the `miso-m2m-flowgates` intake landed (this branch,
commit `9d4681c`), measure — in the 72 scarce hours and the miso-174 hour
sets — which seam-class flowgates were binding or at-entitlement, whether the
measured binding pattern explains the seam's negative response to MISO
stress, and adjudicate whether a rule-13-admissible, zero/low-DOF seam-class
mechanism exists. **This file is committed BEFORE any hour-set-conditioned
quantity is computed** (the miso-167/171/174 K-PRE discipline). NO LP is
planned; the keeper `2026-08-22-miso-175-hourkey` is not touched.

## 1. The object

miso-174 §3 measured (and this prereg takes as given, not re-adjudicated):
in MISO's scarce hours the MEASURED PJM seam moves AWAY from MISO
(−0.77/−0.54/−1.03 GW vs its own summer mean) while the model's priced seam
moves toward it (+0.89/+0.48/+1.34 GW); capability is not the binder
(K-PRE-1: 0/72 bucket-max exceedance) and the border spread
(+$315/+$317/+$331) went unarbitraged. Something bound that is neither price
nor the seam's own ceiling. The M2M/CMP record is the public data that can
NAME it — or show it was not seam-class congestion management at all.

The mechanism-in-kind under adjudication — matrix cell
**`m2m_seam_entitlement_cap`** (new row, minted this session): an M2M/CMP
entitlement-derived directional seam-response mechanism (e.g. an
FFE-derived cap on the priced seam that regenerates for a forward year).
Distinct from every adjudicated cell it neighbours: NOT
`measured_interface_limits` (R, miso-174 — a seam-aggregate MW capability
ceiling; refuted because capability is not violated), NOT
`import_shape_lever` (G, miso-123 — hour-of-day price shape), NOT the
internal-congestion family (`internal_congestion_split` G,
`zonal_loss_surface` R), and NOT the C3a-2025 scarcity lane (CLOSED,
miso-163 owner ruling).

## 2. Known at registration (disclosed so nothing below can be retro-fit)

From committed artifacts: every number in miso-174
(`_miso174_seam_overimport_decomposition.json` and the finding §§1–5) and
miso-175. From THIS session's intake validation, **whole-file/annual grain
only** — no hour-set-conditioned statistic has been computed:

* rows 124,821 / 162,394 / 181,989 (2023/24/25); flowgates 309/385/401;
  every hour of the year carries rows for some flowgates; no
  (flowgate, hour) duplicates.
* Monitoring splits (2025 rows): MISO-monitored vs PJM 32,735 / vs SWPP
  58,449; PJM-monitored 8,870; SWPP-monitored 81,516; "NO RTO" 419.
* Shadow prices are non-negative; 13.7–17.5 % of rows carry a nonzero
  MISO-side shadow (p50 of nonzero ≈ $76–84, max $2,000–2,795).
* PJM-seam (`seam_rto == "PJM"`) rows exist in 8,608 of 8,760 hours of
  2025 (115 flowgates); SWPP-seam in 8,759.
* The M2M record covers ONLY the PJM and SWPP seams. The South
  (SOCO/TVA/AECI/LGEE/SIKE) and Manitoba seams have no M2M/CMP construct;
  nothing here reaches them.

## 3. Instruments

* Probe: `scripts/probes/_miso176_m2m_seam_binding.py` (read-only; no LP;
  nothing feeds a solve — rule 13).
* Record: `results/calibration/_miso176_m2m_seam_binding.json`.
* Inputs: the `miso-m2m-flowgates` clean partitions; keeper
  `miso175_hourkey` hourly sidecars (`system_<y>`, `class_hourly_<y>`);
  `miso169_gated_A/hourly/unit_hourly_<y>` for the per-seam model split
  (the ONLY MISO bundle carrying `unit_hourly`; its aggregate scarce-hour
  drift vs the miso-173-era keeper was measured at −0.099/−0.034/−0.089 GW
  by miso-174 §5 and is re-disclosed against the CURRENT keeper in the
  record); `actual_lmp_hourly_MISO.parquet`; `MISO_region.parquet` (BALANCE
  D/TI); `MISO interchange hourly.parquet` (DIBA, keyed −1 h hour-ending
  per the miso-175 keeper convention); the gitignored
  `2025_rt_bc_HIST.csv.gz` mirror (V-KEY comparator, re-fetched via the
  sanctioned `fetch_miso_bc_hist.py`).

## 4. Fixed conventions

* **Hour sets** — verbatim miso-174: model fixed non-leap 8760 CST clock;
  `summer` = Jun 1–Sep 30; `summer_scarce_rt200` = summer & actual RT >
  $200 (n = 11/14/47); `summer_top47_load` = top-47 summer hours by model
  demand; `scarce_da_foreseen` / `scarce_rt_only` split at DA $150.
* **M2M clock mapping** — the source stamp is hour-ENDING 1..24 on fixed
  EST (curated to hour-beginning EST); model CST hour-beginning =
  EST hour-beginning − 1 h; Feb 29 dropped with the standard leap
  day-of-year shift.
* **Binding (primary)** — monitoring-side shadow price > 0 (the
  monitoring RTO's constraint actually bound): `miso_shadow` when
  MISO monitors, `cp_shadow` when PJM/SWPP monitors, `max(both)` for the
  tiny "NO RTO" class. **Sensitivity**: either-side > 0.
* **Intensity per (seam s, model hour h)** — `N_bind(s,h)` = count of
  seam-s flowgate rows binding at h; `SSP(s,h)` = Σ monitoring-side shadow
  over those rows.
* **Entitlement state per row** — `D = mkt_flow − ffe` per party
  (meaningful only where both are non-null; signed in the flowgate's
  defined direction). "At/over entitlement" = D > 0.
* The verdict keys on the **PJM seam** (the component that is
  sign-opposite in all three years); the SWPP seam is measured in parallel
  and reported.

## 5. Validity gates (scored before any A-gate is interpreted)

* **V-KEY (the settlement file's clock, verified not assumed).** The
  structural evidence at intake: hour-ending labels 1..24 with HE 24
  posted "24:00:00" and full 24-label days all year (8,760/8,784 distinct
  hours — a fixed-offset clock, i.e. EST market time, the repo-documented
  convention for this channel). Measured leg: MISO-monitored M2M
  flowgates with ≥ 300 annual binding hours in 2025 are token-matched by
  name against `2025_rt_bc_HIST` constraints; for matched pairs, the
  hourly M2M `miso_shadow` series is correlated against the bc_HIST
  hourly-mean |SP| (zeros filled, EST hour-beginning → model clock) under
  M2M key shifts −3..+3 h. **PASS**: shift 0 maximizes the pooled r and
  pooled r(0) ≥ 0.8. **Fallback** (pre-registered): if fewer than 3
  matched pairs with ≥ 100 shared binding hours exist, V-KEY rests on the
  structural evidence alone, and every A-gate conclusion must then be
  stable under key shifts {−1, 0, +1} or the verdict reports
  key-sensitivity. V-KEY FAIL (a shift ≠ 0 wins decisively) → STOP:
  repair the curation first; no adjudication this session.
* **V-VINTAGE** — the `unit_hourly` per-seam model split's aggregate
  drift vs the CURRENT keeper is measured per hour set and disclosed with
  every model-side number (the miso-174 §5 treatment).
* **V-SETS** — the probe's hour sets must reproduce miso-174's n
  (11/14/47 scarce) exactly; the scarce-set definition is actual-based and
  keeper-invariant.

## 6. The measurements (gated quantities — none computed yet), with pre-declared readings

* **A-1 coordination presence.** Share of scarce hours with ≥ 1 PJM-seam
  row in coordination; same for binding (≥ 1 binding row). Reported.
  If < 80 % of scarce hours carry any PJM-seam coordination row, the
  record's reach is partial and the verdict says so.
* **A-2 binding elevation at MISO stress (the load-bearing gate).**
  `R_cnt = mean N_bind(PJM,h) over scarce hours ÷ mean over all summer
  hours`; `R_ssp` likewise for SSP. Pre-declared readings:
  - **CO-MOVES** if `R_cnt ≥ 1.5` OR `R_ssp ≥ 2.0` in ≥ 2 of 3 years;
  - **REFUTED** (binding does not intensify at MISO stress) if
    `R_cnt < 1.2` AND `R_ssp < 1.5` in ≥ 2 of 3 years;
  - anything between: adjudicated on the full pattern, the judgment
    disclosed as such in the finding.
* **A-3 association with the measured seam flow.** Over summer hours:
  (a) Pearson r between measured PJM-seam net import (DIBA, −1 h key) and
  `N_bind(PJM,h)` / `SSP(PJM,h)`; (b) **the directional split**: mean
  measured PJM-seam net import over the top-quartile-binding summer hours
  (by SSP, among hours with any binding) vs over the zero-binding summer
  hours. Pre-declared: **RESTRICTION-CONSISTENT** if the top-binding mean
  import sits ≥ 0.3 GW BELOW the zero-binding mean in ≥ 2 of 3 years;
  **RESTRICTION-INCONSISTENT** if it sits at or ABOVE the zero-binding
  mean in ≥ 2 of 3 years. Both causal channels are stated now: binding
  can restrict imports (negative association), and heavy imports can
  cause binding (positive association); the split (b) is the reading that
  matters, r is context.
* **A-4 entitlement headroom.** Per seam per hour set: the distribution
  (mean/p90/max) of MISO's `D = mkt_flow − ffe` and the share of binding
  rows with `D > 0` (MISO at/over entitlement); the CP side likewise on
  MISO-monitored rows; the count of DISTINCT binding flowgates. The
  model's gross seam import (GW, vintage-disclosed) is reported alongside
  as context. **Fixed now: no MW-to-MW comparison between flowgate MW and
  seam MW is claimed in either direction — that conversion is exactly the
  apportionment no published data supports (miso-77 §5.2).**
* **A-5 scarce-hour flowgate census.** For each of the 72 scarce hours:
  binding PJM-seam flowgates (id, name, monitoring RTO, monitoring-side
  SP, MISO D). Written to the record verbatim — the finding's naming
  evidence.

## 7. The kills (mechanism adjudication; fixed before measurement)

* **K-1 rule-13 conditioning (logic gate, unoverridable).** Any
  construction whose solve-time behaviour is conditioned on the measured
  M2M binding state, shadow prices, market flows or credits is REFUSED —
  the charter's fixed line; no measurement below can re-open it.
* **K-2 placement (the standing M1/miso-77 §5.2 refutation).** A seam-MW
  bound derived from per-flowgate FFE/rating MW requires a
  flowgate→seam-aggregate mapping; no distribution-factor/PTDF series is
  published anywhere in the family. Unless the finding can state a
  construction whose mapping is the IDENTITY (the input-class quantity is
  already a seam-aggregate MW at the model link's grain), the
  entitlement-cap reading is REFUSED in kind. No apportionment may be
  invented, however plausible.
* **K-3 forward story (rule 17).** Any surviving construction must state
  its driver, its binding window, and how its FFE-class input regenerates
  for a forecast year (the JOA entitlement process as a market-design
  constant), BEFORE it can be chartered. Absent that story it is not a
  candidate.

## 8. Verdict mapping (fixed)

| measured outcome | cell `m2m_seam_entitlement_cap` (MISO) |
|---|---|
| V-KEY FAIL | no verdict — curation repair first |
| A-2 REFUTED (binding does not co-move with MISO stress), or A-3 RESTRICTION-INCONSISTENT | **R** — the record itself refutes the premise that seam-class congestion management is what bound; the miso-174 §3 object stands as CONDUCT unexplained by M2M, and owner item 5(i) (the coincident-peak envelope ruling) inherits that sharpening |
| A-2 CO-MOVES and A-3 RESTRICTION-CONSISTENT, but no construction survives K-1/K-2/K-3 | **G** — phenomenon real and named by the record; every admissible zero-DOF encoding is refused on the rule-13 / apportionment grounds; the evidence transfers to owner item 5(i) |
| A-2 CO-MOVES and A-3 RESTRICTION-CONSISTENT and a K-1/K-2/K-3-surviving construction can be stated | **O** — open: the construction is written into the finding and a lever charter with its own prereg + `replay_keeper` control/arm pair is the successor; NOTHING is armed this session |
| A-gates split (one CO-MOVES leg, one INCONSISTENT leg) | adjudicated on the full pattern; the judgment and both legs disclosed; default to **R** unless the pattern coherently supports G |

## 9. The honest ceiling (charter item 4, restated before measuring)

**C3a-2025 is CLOSED end to end as a model-class limit** (miso-163 owner
ruling; FINDING-miso171 §6). The over-import this lane addresses is worth
≤ +3.3/+7.7/+3.9 $/MWh at the model's own slope even at its inadmissible
upper bound (miso-174 §5) — 1–2.5 % of the scarce-hour miss. This lane
repairs a second-order structural defect on rule-1/rule-14 grounds and **NO
number it produces may be quoted against C3a-2025**, whatever the verdict.

## 10. Governance

Rule 22: 2023–2025 only; MISO holds neither `complete` nor `final`; the
spend freeze is untouched. Rule 15: engaged only if a solve is spent (none
planned). Rule 28: the `m2m_seam_entitlement_cap` base row + a cell line in
every ISO shard land with the verdict commit (the row is minted BY this
adjudication); verdicts are MISO-only (rule 25 — PJM's side of the same JOA
record is PJM's lane's call and enters its shard as `U`). DO-NOT-REDO
honoured: nothing here re-opens `measured_interface_limits`,
`import_shape_lever`, the C3a lane, the congestion cells, the copper-plate
topology reading, or the miso-175 hour-key convention.
