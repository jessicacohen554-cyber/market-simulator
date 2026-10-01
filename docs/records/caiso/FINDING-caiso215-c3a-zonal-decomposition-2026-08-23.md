# FINDING — caiso-215: the C3a 2024/2025 overrun is NOT spatially uniform and NOT one bad zone — it is a **north–south split at Path 15**: the south (LA_BASIN + SDGE + SP15_rest + ZP26, ~61 % of load) carries **~100 % of the net ISO gap** (+19–27 % per zone in 2024/25) while **NP15 UNDER-prices** (−6.6 % / −0.8 %), the model's N–S spread has the **wrong sign** (model −$1.9 to −$2.3 vs actual +$5.6 to +$9.1), and reality's split is **80–90 % congestion** the model never develops (0 h of NP15−SP15 > $15 vs 1,310–1,691 h actual). Every zonal redistribution **nets to ≈ 0 ISO-wide** (bridge terms ±$0.15), so **no zonal lever closes C3a directly** — the scored failure remains the common level term — but the error is now **localized to the southern solar belly** (35–64 % of the south's gap in hod 10–15), which **changes the admissibility arithmetic**: a south-belly-scoped surplus-pricing object needs only ~½ of the measured south-hour error to close C3a-2025 and is **2023-SAFE even at full size**, unlike §G's broad level-down. NO LP, NO SOLVE — committed bytes only (2026-08-23)

**Keeper `2026-08-17-caiso-200-h1-memberpanel` UNCHANGED. No mechanism armed, no
`ScenarioConfig` field added, no LP built, no solver called, nothing registered,
NO matrix cell verdict moved.** This is the owner's caiso-214 charter
(2026-08-22, "I really really need you to address the 2024 and 2025 overprice —
identify WHERE it stems from") executed as **caiso-215**: the caiso-214
shorthand was consumed the same day by the forecast-lane T1-H hindcast session
(`docs/calibration-log/caiso.md` "caiso-214 (2026-08-22) — FORECAST-FAMILY
LANE", commit `bca0fa9`, closing "Next number: caiso-215"), so per lane
numbering protocol this session takes caiso-215 and maps to the charter by this
note (precedent: the caiso-213 numbering-consistency note; caiso-203's
charter-duplicate adjudication).

**THE ONE-SCREEN OWNER SUMMARY.**

* **One zone or the whole ISO?** Neither. It is a **two-region split at
  Path 15**: all four southern-pricing zones (the three SP15-split zones AND
  ZP26, which reality prices with the south — actual MCC −$3.7 to −$6.0 —
  while the model ties it to NP15) over-run together at +13.5–27.1 %, and
  NP15 (~39 % of load) sits **at or below** actual (−6.6 % 2024, −0.8 % 2025,
  −5.3 % 2023). LA_BASIN's headline share (86.5 % / 71.3 % of the ISO gap) is
  its 39 % load weight on the common southern error, not a pocket-specific
  defect: the three SP15 zones carry nearly identical gaps (+22–27 % in 2024),
  so there is **no single-zone input defect to fix**.
* **All hours or some?** South-belly concentrated. 35–64 % of the south's
  annual gap sits in hod 10–15 alone; the south's sub-$20 actual-price hours
  are ~3× as numerous as NP15's and carry the largest unit gaps (+$15–28/MWh).
  In those same belly hours reality splits NP15 **+$12–21 above** SP15
  (S→N congestion, 1.3–1.7 kh/yr above $15) and the model splits **$0.00**.
  This is caiso-202's compression seen in its spatial dimension: the missing
  regime is the south's surplus/curtailment price formation and the S→N
  congestion it drives.
* **What is newly admissible?** **Nothing is armed-admissible today** — the
  zonal cut surfaced no measured in-model instrument, and every mean-zero
  zonal redistribution (incl. the measured `caiso_zonal_gas_basis`) leaves
  C3a unchanged by construction. What changed is the **arithmetic envelope**:
  (i) §G's blocker was a broad ~$2–3/h all-hours level-down with no admissible
  carrier; a **south-belly-scoped** object needs to remove only ~46 % of the
  measured south-hour error to close C3a-2025, ~25 % for 2024, and even
  **full** removal of the south-belly error moves 2023 by only ≈ −$1.5
  (headroom −$7.4) — 2023-safe, which the broad object never was by this
  margin; (ii) the two standing owner-packet objects (PS water-state; import
  spot capacity) should be **re-scored against the south-belly target** rather
  than the ISO-wide move — their 62.1 %/10.4 % coverage was computed CA-wide;
  (iii) a third owner-fundable object is now specified with measured evidence:
  the **south surplus-pricing regime** (§F H4), whose evidence base
  (`data/raw/caiso-curtailment/`, the hub MCC components, EIA-930 corridor
  flows) is committed, and whose rule-13 test is stated in §F. Funding any of
  these is an **owner decision — this session stops here**. NOT-YET stands.

Instruments (committed, no LP, no solve):

* `scripts/probes/_caiso215_c3a_zonal_decomp.py` — §A–§E below (sections Z0–Z6
  of its stdout). Imports the committed caiso-202 probe for the CA-wide
  machinery (`sidecars`/`ca_lambda`/`rubric_weights`/`month_of_hour`), so the
  control is provably the same construction re-sliced.
* `results/calibration/_caiso215_c3a_zonal_decomp.json` — every table below,
  committed (deterministic; sorted keys, no timestamps).
* Controls: (i) the unmodified `_caiso202_c3a_decomp.py` re-run reproduces
  FINDING-caiso202 §A/§B exactly (2023 55.60/54.17 +2.6 %, basis +7.55; 2024
  38.57/34.65 +11.3 %, DA +1.6 %; 2025 39.02/34.42 +13.3 %); (ii) the per-hub
  actual series used here, collapsed with the deriver's own stale hub weights
  (0.3969/0.0646/0.5385), reproduce the committed scalar
  `actual_lmp_hourly_CAISO.parquet` to float32 rounding (max |Δ| ≤ 2.6e-05,
  NaN masks identical) — the per-hub actuals are the committed scalar's own
  constituents on the committed hour clock.

Reproduction: `pip install numpy pandas pyarrow pydantic pyyaml scipy` then
`PYTHONPATH=.:src python3 scripts/probes/_caiso215_c3a_zonal_decomp.py`.
Inputs: the keeper's `hourly/system_<year>.parquet` sidecars, the committed
`data/raw/lmp-data/CAISO/CAISO_{rtm,dam}_hourly_<year>.csv` (trading hubs +
2024/25 DLAPs, with MCC/MCE/MCL components), the committed
`wecc_intertie_lmp_hourly_CAISO.parquet`, and the committed scalar actual.

---

## §A — per-zone C3a: the south carries the whole net gap, NP15 subtracts from it

Zone-demand-weighted model λ vs the zone's own trading-hub RT actual (the
market's own zone resolution: NP15→TH_NP15, ZP26→TH_ZP26, the three SP15-split
zones→TH_SP15). `share` = the zone's contribution to the ISO-wide per-hub gap;
shares sum to 100 %.

| zone (2024) | model | actual | gap $ | gap % | share |
|---|---:|---:|---:|---:|---:|
| NP15 | 38.04 | 40.71 | **−2.68** | **−6.6 %** | **−27.3 %** |
| ZP26 | 37.87 | 32.43 | +5.44 | +16.8 % | 7.3 % |
| LA_BASIN | 39.89 | 31.38 | +8.50 | **+27.1 %** | **86.5 %** |
| SDGE | 40.90 | 33.50 | +7.40 | +22.1 % | 16.6 % |
| SP15_rest | 38.93 | 31.44 | +7.50 | +23.8 % | 17.0 % |
| SP15 (all 3) | 39.89 | 31.71 | +8.18 | +25.8 % | — |

| zone (2025) | gap $ | gap % | share |  | zone (2023 control) | gap $ | gap % | share |
|---|---:|---:|---:|---|---|---:|---:|---:|
| NP15 | −0.31 | −0.8 % | −2.6 % |  | NP15 | −3.03 | −5.3 % | −95.0 % |
| ZP26 | +4.65 | +13.5 % | 5.2 % |  | ZP26 | +3.76 | +7.4 % | 15.5 % |
| LA_BASIN | +8.10 | +25.0 % | 71.3 % |  | LA_BASIN | +4.26 | +8.1 % | 128.4 % |
| SDGE | +6.37 | +18.6 % | 12.6 % |  | SDGE | +3.41 | +6.3 % | 23.2 % |
| SP15_rest | +6.98 | +21.5 % | 13.5 % |  | SP15_rest | +4.25 | +8.1 % | 27.9 % |
| SP15 (all 3) | +7.66 | +23.4 % | — |  | SP15 (all 3) | +4.12 | +7.8 % | — |

The 2023 control behaves exactly as §B of caiso-202 predicts: the same
south-over/north-under structure exists in the PASSING year — 2023's C3a pass
is the south's +7.8 % cancelling against NP15's −5.3 % *plus* the tail-hour
credit. **The C3a year-ordering is not a southern regression**; the split is
year-invariant and only its cancellation partners change.

**The weight bridge (kills the collapse-artifact hypothesis).** Scored-style
gap → realised-weight gap → per-hub gap: 2023 +1.43/+1.36/+1.27; 2024
+3.92/+3.78/+3.81; 2025 +4.59/+4.32/+4.46. The rubric-vs-sidecar weight term
is −$0.07/−$0.14/−$0.28 and the stale-hub-collapse term −$0.09/+$0.03/+$0.15.
**C3a is not a weighting or collapse artifact** — and per rule 13 neither term
would be a lever even if it were material (scoring-side).

## §B — per-zone × actual-RT price bucket: the sub-$60 overprice is 2× larger in the south, and the south has 3× the low-price hours

caiso-202 §B re-cut per zone (identical edges, bucketed on each zone's own hub
actual; cells are hours / model−actual $/MWh). 2024:

| bucket | NP15 | ZP26 | LA_BASIN | SDGE | SP15_rest |
|---|---:|---:|---:|---:|---:|
| < $0 | 442 h +15.7 | 1,201 h +28.3 | 1,230 h +28.1 | +26.2 | +27.9 |
| 0–10 | 311 h +6.9 | 455 h +21.0 | 386 h +20.9 | +18.6 | +20.2 |
| 10–20 | 603 h +6.8 | 666 h +16.1 | 684 h +17.8 | +16.2 | +17.0 |
| 20–30 | 1,405 h +5.8 | 1,330 h +9.2 | 1,385 h +11.9 | +11.7 | +10.9 |
| 30–40 | 2,428 h +2.0 | 2,230 h +4.5 | 2,164 h +7.6 | +7.8 | +6.6 |
| 40–60 | 2,717 h **−4.2** | 2,332 h −1.5 | 2,315 h +2.4 | +2.4 | +1.1 |
| 60–100 | 688 h −17.7 | 432 h −14.3 | 488 h −10.4 | −10.0 | −11.9 |
| > $100 | 166 h −109.9 | 114 h −76.7 | 108 h −70.7 | −65.3 | −73.1 |

2025 repeats the pattern (south sub-$20 buckets +12.5 to +20.5, NP15 40–60
bucket −2.1; full tables in the JSON). Two structural facts: (a) the south's
sub-$20 hour count is ~2.7–3× NP15's (2024: 2,300 h vs 1,356 h; the < $0
bucket alone 1,230 h vs 442 h) — reality's negative/surplus regime **lives in
the south**; (b) NP15's mid-band (40–60) is already **under**-priced — the
caiso-202 CA-wide "+$6–15 every sub-$60 bucket" is the south's error diluted
by a north that is at-or-below actual. The measured offer stack (caiso-202 §H)
prices the north correctly with the same machinery — **independent
corroboration that the offer levels are not the defect**.

## §C — the seam: parity holds, the MIC cannot bind on this keeper, and the northern corridor node runs cheap vs its own measured hub

* **caiso-188's no-MIC-bind expectation VERIFIED on this keeper, structurally:**
  the resolved seam MIC (16,055/16,452/16,148 MW, `run_config.json →
  resolved_inputs.seam_import_cap`) **exceeds the sum of the two corridor TTCs
  it spans** (COI 4,800 + WOR 10,623 = 15,423 MW), so the simultaneous limit
  is non-binding by arithmetic in every hour of every year. The corridor-zone
  λ separation medians are 0.00 in all six corridor-years (parity ≥ half of
  all hours) — consistent with caiso-142's measured 0-of-26,280 h bind.
* Corridor decoupling hours (Δ = λ_CA-zone − λ_corridor > median + $1: the
  per-corridor measured p95 envelopes / directional ratings, NOT the MIC)
  exist — PNW 1,863 h, DSW 2,955 h in 2024 — and sit inside positive-gap
  hours (88 %/83 % overlap), but they are import-limit signatures that RAISE
  CA λ relative to the corridor; they cannot be recruited to lower it.
* **New witness:** the model's WECC_PNW node λ runs **$11.16 / $8.13 / $3.57
  below** measured MALIN (2023/24/25) while WECC_DSW tracks PALOVRDE
  (−$4.32 / +$0.03 / +$2.15). The northern import stack is cheap at its node
  in exactly the years NP15 under-prices. This is measured evidence FOR the
  standing owner-packet item 2 (import spot-capacity/pricing derivation) and
  localizes it: the derivation matters at the **northern** corridor.

## §D — congestion split: the model's spread has the wrong sign, and the scored failure is the common term

gap_z = common (CA-wide λ vs scalar actual, ≈ zone-invariant) + spread
mismatch (model zonal spread − actual hub spread). 2024:

| zone | model spread | actual spread | mismatch | common | gap_z |
|---|---:|---:|---:|---:|---:|
| NP15 | −1.39 | **+4.95** | **−6.34** | +3.66 | −2.68 |
| ZP26 | −1.55 | −3.34 | +1.78 | +3.66 | +5.44 |
| LA_BASIN | +1.32 | −3.26 | +4.58 | +3.92 | +8.50 |
| SDGE | +0.91 | −2.87 | +3.79 | +3.61 | +7.40 |
| SP15_rest | +0.34 | −3.23 | +3.57 | +3.93 | +7.50 |

2025 identical in structure (NP15 mismatch −4.54, south +2.10 to +3.70, common
+4.24 to +4.40); 2023 likewise (NP15 −4.39, common +1.22 to +1.38). Three
consequences:

1. **The load-weighted mismatch column nets to ≈ 0** (+$0.03 2024, +$0.15
   2025 — the bridge's hub-collapse term). The C3a failure **is the common
   term**; fixing the spread alone moves the scored mean by cents. This is
   the §F-style kill for every mean-zero zonal instrument *as a C3a lever*.
2. The model carries a small **south premium** (loss-surface direction — the
   caiso-164 mechanism working as designed on internal links) where reality
   carries a large **north premium**. The actual split is measured to be
   **80–90 % congestion** (caiso-164 §1.1: dMCC on NP15−ZP26 = $4.77/$7.48/
   $4.68 of $5.95/$8.58/$5.73 totals; MCE identically zero) — corroborated
   here by the hubs' own MCC means (2024: NP15 **+1.95**, ZP26 **−6.03**,
   SP15 **−6.03**; same signs 2023/2025).
3. **ZP26 prices with the south in reality** (its MCC ≈ SP15's; actual level
   32.43 vs SP15 31.71 in 2024) while the model ties it to NP15 through a
   rarely-binding Path 15. The real cut point is Path 15, not Path 26.

## §E — when and where: the southern solar belly, plus a distinct NP15 winter under-price

* **Belly localization (Z6):** hours with actual NP15−SP15 > $15: 1,310 /
  1,691 / 1,347 (2023/24/25); model: **0 / 0 / 0**. Actual belly-mean
  NP15−SP15 = +$17.8 / +$21.2 / +$12.2; model −$0.2 to +$0.2. The hod-10–15
  belly alone carries **64 % / 45 % / 35 %** of the south's annual gap-$
  (+$302 M / +$442 M / +$316 M of +$469 M / +$971 M / +$894 M).
* **Monthly:** the south's worst months are the belly seasons — 2024
  Mar–May (+$10.6 to +$16.4 on the SP15 zones) and 2025 Sep–Oct (+$10.8 to
  +$15.5); ZP26 tracks them. NP15 is different in kind: its 2024 error is a
  **winter under-price** (Jan −$16.4, Oct −$8.8, Nov −$6.2 — the citygate
  gas-event months) that nearly vanishes by 2025 (Jan −$6.4, most months
  within ±$2.5).
* **Pocket DA cross-check (2024/25, the only committed pocket-resolution
  actuals; C3a's RT basis is untouched — caiso-203 ruling 1 CLOSED):** vs its
  own DLAP DA, the model's SDGE is **on the nose** (−0.2 % / −0.6 %),
  LA_BASIN +8.4 % / +13.3 %, SP15_rest vs hub DA +10.0 % / +17.7 %, NP15
  −12.2 % / −3.1 %. The real pockets price **above** TH_SP15 (caiso-165: SCE
  belly dMCC +0.70→+1.91, SDGE +3.92→+6.42 $/MWh 2024→25), so ~$2–5 of the
  south zones' apparent hub-RT overrun is settlement geography the LCT-pocket
  structure already anticipates — a reporting nuance, **not** a lever and not
  a basis re-litigation; the south's belly overrun survives it whole.

---

## §F — hypothesis adjudication (kill-before-propose, each sized against 2024 −$0.97 / 2025 −$1.96 / 2023 headroom −$7.4)

**H1 — "one zone's input is broken" (fleet/load/limit mis-assignment): CLEAN
NEGATIVE.** All four southern-pricing zones over-run together with near-equal
per-zone gaps (+22–27 % across the SP15 split in 2024) and near-identical
common terms; LA_BASIN's share is its load weight, not a pocket defect; the
2023 control shows the same structure in the passing year. No single-zone
instrument exists because no single-zone anomaly exists.

**H2 — zonal redistribution as a C3a lever: KILLED ON ARITHMETIC.** Any
mean-preserving zonal instrument — and every admissible one measured here is
mean-preserving — moves C3a by the netting residual, measured at ±$0.15
(§D.1). Even a PERFECT spread repair (model reproduces the actual +$9 N–S
split) leaves the scored C3a within $0.15 of today. This kill is
construction-level and transfers to every future zonal candidate.

**H3 — `caiso_zonal_gas_basis` (measured PG&E vs SoCal citygate split,
capacity-weighted mean-zero, `data/raw/caiso_zonal_gas_hub.csv`): NOT
PROPOSED.** Admissible in kind (measured weekly prints, forward analogue,
NYISO keeper precedent nyiso-109, zero free parameters) but (a) mean-zero ⇒
C3a Δ ≈ 0 (H2); (b) the measured N−S basis differential is small and
**sign-flipping** — +0.539 (2024), −0.184 (2025), −0.491 (2023) $/MMBtu — so
it repairs the spread's direction only in 2024 (~+$3.9 on northern gas rungs)
and moves it the WRONG way in 2023/2025; (c) the real split is 80–90 %
congestion, not fuel (§D.2). It may have a small truth-value for NP15's
winter under-price (the basis is a winter phenomenon the annual mean hides),
but as measured it is not the N–S mechanism and not a C3a instrument.
*Shard hygiene finding (filed, not moved): the CAISO shard carries
`zonal_gas_basis: { cell: "K" }`, yet every committed CAISO `run_config.json`
has `caiso_zonal_gas_basis: false`, no CAISO log/FINDING records an arming,
and the cell's blame terminates at the history-rewrite boundary. The K is
unsupported by any committed run; a future session should re-adjudicate it
caiso-203-style (this session moves no verdicts).*

**H4 — the south-belly surplus-pricing regime (reality's mechanism): REAL,
MEASURED, AND NOT ARMABLE FROM THE CURRENT LEVER SET — an owner-funding
object, now sized and localized.** Reality clears the southern belly at ≤ $0
in 964–1,230 h/yr (2024/25 south hubs), splits N–S by +$12–21 through S→N
congestion, and curtails the residual; the model holds the same hours at the
CC/charge band (caiso-202 §C.2) with zero N–S separation. Every in-model
route to this regime is adjudicated and none is re-opened by geography alone:
`caiso_p1_export_sink_seam` R (an absorption column can only RAISE λ —
caiso-142 §0, unchanged by localization), `caiso_corridor_export_path` R,
`caiso_da_rt_two_settlement` R (the measured fleet already operates within
~2 pp of perfect foresight — caiso-170 §0), `negative_renewable_offers`
default-off (probe-refuted family), and the wedge instruments (caiso-140 §C:
the whole 2.3–2.6 GW at once, unfunded). **What the zonal cut changes is the
target geometry, not the adjudications:** the required C3a move now fits
inside a *scoped* object — removing 25 % of the measured south-belly error
closes 2024 (needed ≈ $206 M-gap-$ vs $442 M measured), removing ~46 % of the
south's all-hours error closes 2025 (needed ≈ $403 M vs $894 M measured, $316 M
of it belly), and **full** removal of the south-belly error costs 2023 only
≈ −$1.5 of its −$7.4 headroom. The rule-13 test any candidate representation
must pass, stated now: measured curtailment/surplus **quantities** (CAISO's
published curtailment record, `data/raw/caiso-curtailment/`; EIA-930 corridor
flows; the hubs' own MCC split) entering as reproducible physical/market
inputs with a forward analogue are admissible; any overlay of measured
**prices**, or any adder/floor tuned to the residual, is an outcome pin and
is not. Designing that representation — or declining to — is an owner
decision; nothing here arms it.

**H5 — the northern corridor / import-pricing half (owner-packet item 2):
EVIDENCE STRENGTHENED, LOCALIZED NORTH.** The PNW node runs $8–11 below
measured MALIN in 2023/24 (§C) precisely where NP15 under-prices and winter
months carry −$6 to −$16 monthly gaps. Direct λ share stays < 5 % (caiso-202
§C, unchanged), so it still cannot close C3a alone; but its re-scoring should
note the north-scoped action (it raises NP15, i.e. moves the *distribution*
toward truth while slightly RAISING the mean — C3a-adverse in sign, bounded
small).

## §G — the packet

Ranked, with the pre-registered gate table any future funded arm must carry
(MUST-NOT-REGRESS: C3b ≤ 0.098/0.179/0.182 measured baseline — the 2025
composition watch is live at margin 0.018; C8; C6; DOF ledger 10/7 with any
new mechanism's identification row added; LOYO within 2023–2025 for any
mechanism-driven verdict flip; C3a-2023 stays in band):

1. **The south-belly surplus-pricing object (H4)** — the only object sized to
   close C3a-2024/25 that is 2023-safe. Owner funding required on two counts:
   an intake/design phase (curtailment record → representation passing the
   rule-13 test above) and a solve. **Partial-close worth:** a partial that
   removes half the belly error moves 2024 into band and 2025 to ≈ +12 %
   (short); a partial is therefore worth a 2024 pass but NOT a determination
   flip on its own — pre-register the partial verdict as NOT-YET with reduced
   magnitude unless 2025 clears.
2. **Re-score the two standing owner-packet objects against the south-belly
   target** (no new solve implied): PS water-state's 62.1 %/10.4 % coverage
   and the import-derivation's < 5 % share were computed CA-wide; a
   south-scoped re-read may move either object's worth materially (up for
   anything acting on southern belly absorption; down for north-scoped
   action). Desk exercise on committed bytes; fundable as part of the H4
   design phase.
3. **Clean negatives to retire permanently:** the single-zone hypothesis
   (H1), the weighting/collapse artifact (§A bridge), zonal redistribution as
   a C3a lever (H2), and `caiso_zonal_gas_basis` as the N–S mechanism (H3).
   These close the zonal hypothesis in its charter form: **if the owner funds
   nothing, NOT-YET on C3a stands and the residual is attributed** — south
   surplus-pricing regime (model-class exclusion, localized), not offer
   levels, not one zone, not weights.

**Explicitly NOT proposed:** any per-year or per-zone offer/band/anchor
multiplier (§F.1/§F.2 of caiso-202 stand); any C3a-basis change (caiso-203
ruling 1 CLOSED — the DLAP nuance in §E is reported context only); any re-arm
of the R/G-adjudicated export/two-settlement family without a
mechanism-reality argument (geography alone is insufficient, §F H4).

## §H — record changes (rule 28b, CAISO shard only; no verdict moves)

* Matrix §5.2: caiso-215 block added above caiso-213's. Shard `gates` stamp
  prepended (2026-08-23, session caiso-215); `updated` bumped. Evidence
  strings appended on `zonal_loss_surface` (Z4/Z6 re-measurement on the
  caiso-200 keeper), `import_hub_pricing` (the PNW-node-vs-MALIN witness),
  `diurnal_price_amplitude` (per-zone bucket structure), and
  `capacity_deliverability` (the MIC ≥ Σ-corridor-TTC structural no-bind
  verification). **No cell or fc verdict moved** — nothing was tested.
* `docs/calibration-log/caiso.md`: caiso-215 entry.
* Filed items (carried from caiso-213, plus one): (1) stale
  `offer_curve_by_group` DOF text (identification:"residual" vs measured
  since 2026-08-02); (2) keeper `legitimacy_diagnostics.json` regeneration at
  HEAD (chp_steam plant 10034 D-4 vintage drift); (3) caiso-205 pair site
  retention; (4) promoting sessions re-measure the whole scorecard; (5) three
  CAISO bench parts unstamped (HARD STALE flag; discharge as by-product of
  the next funded solve); **(6, NEW)** the unsupported
  `zonal_gas_basis: K` CAISO shard cell (§F H3) — re-adjudicate
  caiso-203-style at a future session.
* Open cross-lane items (NOT CAISO's): three remain — `check_bench_freshness`
  D1+D2; five-ISO bench regeneration + CI gate; cccc911 forecast-sidecar
  citations. Item 4 (the 239 unresolvable matrix anchors, caiso-213 §3) is
  **VERIFIED DISCHARGED at this HEAD**: ercot-227's `14ce4ce` ("anchor
  repair") landed and `check_mechanism_matrix.py` now prints 0 unresolvable
  beyond the ratchet, integrity OK, keeper stamps and §5.x headers matching —
  re-run by this session after its own matrix edits.

## §I — DO-NOT-REDO (new, binding; adds to caiso-202 §I which carries whole)

* **Re-measuring the per-zone C3a split, the per-zone bucket tables, the
  congestion/common split, the N–S separation witness, or the weight bridge**
  — `_caiso215_c3a_zonal_decomp.py` reproduces all of it from committed bytes
  in minutes; the JSON artifact carries every number.
* **Proposing any mean-zero zonal redistribution as a C3a lever** — killed on
  construction (§F H2, netting residual ±$0.15).
* **Attributing the overrun to a single zone or to the hub-collapse/rubric
  weights** — §A: the split is two-region and the bridge terms are ≤ $0.28.
* **Arming `caiso_zonal_gas_basis` as the N–S spread mechanism** — §F H3: the
  measured differential is sign-flipping and the split is 80–90 % congestion.
  (A NP15-winter-scoped fuel-fidelity case would be NEW evidence and is not
  barred — but it must present monthly measured basis data first.)
* **Re-opening caiso-142/143/170 on geographic evidence alone** — their kill
  reasons are mechanism-reality, not attribution (§F H4).

Keeper, markers, holdout freeze, DOF ledger, every matrix cell verdict, the
§5.2 header, every bench part, and every source file other than the additions
listed in §H: UNCHANGED. Next number: caiso-216.
