> Status: ACTIVE — the cross-ISO mechanism testing matrix (rule 28 `[R-MECH-MATRIX]`).

# Cross-ISO mechanism testing matrix — methodology, lever queues, glossary

**The canonical data lives in ONE place:**
`docs/codebase-site/data/mechanism-matrix.js` (rendered at
`docs/codebase-site/mechanism-matrix.html`, nav → Backcast → Mechanism Matrix).
This doc is the methodology and the *actionable* layer on top of it: how the
matrix is maintained, how similar the six ISO configs actually are, and the
per-ISO **lever queues** — ranked untested candidates tied to each ISO's
currently-failing calibration gates. The glossary is on the HTML page (and
summarized in §6).

Built 2026-07-27 from a five-way audit: the full `ScenarioConfig` inventory
(634 fields), all six keeper `run_config.json`s, the per-ISO calibration logs
(`docs/calibration-log/<iso>.md` + archive), the forecast program board
(`docs/forecast-development-plan-2026-07.md`, FF-2C/2D/3E), and the site
conventions. Keeper snapshot at build: ercot115 / caiso-130 / pjm-133 /
miso-88 / nyiso-89 / neiso-61.

---

## 1. What the matrix is for, and the update protocol (binding)

The matrix answers three questions no single doc answered before:

1. **Usage** — which mechanisms are armed in each ISO's backcast keeper and in
   its forecast default (they are NOT the same set — see §3.3).
2. **Testing** — for each mechanism × ISO, has it been tested *in that ISO*,
   and with what verdict (`K` keeper / `R` rejected / `I` inert / `G`
   governance-refused / `O` open / `U` untested / `·` n/a).
3. **Transfer** — which mechanisms proven in one ISO are plausible, untested
   candidates in another (the `U` cells), so lanes stop rediscovering each
   other's work — and stop re-testing each other's already-adjudicated dead
   ends.

**Duties (normative text is CLAUDE.md rule 28; this is the working recipe):**

- **(a) Handoff prompts cite the matrix.** Any prompt that opens a calibration
  or forecast session for an ISO includes: a pointer to this doc + the matrix,
  and the target ISO's lever queue (§5). The session picks its lever from the
  queue or states why it is going off-queue. It never re-tests a cell already
  marked `R`/`I`/`G` without new evidence (the DO-NOT-REDO discipline —
  e.g. caiso-129's explicit list, ERCOT-122…126's exhausted coal enumeration).
- **(b) Test ⇒ update the cell, same session.** Probe, candidate, or keeper —
  the session that produces a verdict edits the mechanism's row in
  `mechanism-matrix.js` (cell char + `ev` citation + note if the story
  changed), in the same commit series as its rule-15 dashboard registration.
  Rejected probes update the matrix too; a rejection that isn't recorded will
  be re-run by someone else.
- **(c) New mechanism ⇒ new row, same PR.** A PR that adds a solve-affecting
  `ScenarioConfig` field/flag adds its matrix row (all six cells — mostly `U`
  and `·` at birth). A mechanism absent from the matrix is an off-registry
  tuning channel in spirit (rule 24).
- **(d) Verdicts are per-ISO** (rule 25). `K` in PJM says *nothing* about
  MISO. Transfers enter the target ISO as `U`, and the target session derives
  its own parameters from its own fleet/market data — never imports the source
  ISO's fitted values.
- **(e) Keeper swaps re-stamp the header.** When a keeper changes, refresh the
  `keepers`/`gates` header block and re-check that ISO's column (a promotion
  usually flips 1–2 cells).

**Mechanical enforcement.** `scripts/check_mechanism_matrix.py` (stdlib-only)
runs as the `mechanism-matrix-guard` CI job on every PR: it validates matrix
integrity (unique ids, well-formed 6-char cells), **fails** a PR that adds a
new `ScenarioConfig` field not mentioned anywhere in the matrix (duty c —
mention-anywhere is the escape hatch for sub-scalars that belong on an
existing family's row), and **warns** when a new backcast registry sidecar or
calibration CLI flag lands without a matrix touch (duty b — advisory, since
re-runs of recorded recipes legitimately change no cell). In-session, the
`.claude/hooks/mechanism-matrix-reminder.sh` SessionStart hook injects the
duties and pointers at the start of every session, local and web.

## 2. How similar are the six ISO configs? (the up-front answer)

Quantitatively, from the keeper `run_config.json`s (true non-default counts,
excluding JSON round-trip artifacts): **ERCOT 73, PJM 80, CAISO 77, MISO 69,
NYISO 60, NEISO 50** non-default fields.

**Three layers:**

1. **A shared backbone all six run (~30 mechanisms).** One ISO-agnostic LP;
   CAMPD per-plant binning; P0→P1 two-pass pricing; `reliability_floor`
   engine; per-plant coal/CC must-run + CHP steam-following;
   `offer_curve_by_group`; measured annual HH pin + per-plant monthly coal
   pricing; CAMPD outage windows; v2 emission rates; and — the flagship —
   **`gas_offer_net_revenue_margin`, the only calibrated mechanism adopted in
   all six keepers** (per-ISO measured anchors 2.25→4.80 $/MMBtu; precedent
   chain NEISO→CAISO→ERCOT→NYISO→PJM→MISO).
2. **A five-ISO plant-level standard with ERCOT as the deliberate holdout.**
   `plant_level_fleet`, `gas_offer_curve` tranches, `gas_monthly_actuals`,
   `gas_plant_monthly_fuel_pricing` + fallbacks, `gas_daily_shape`,
   `cc_peaking_per_plant`. ERCOT instead runs its own CAMPD-bin + 60-Day
   disclosure stack (DAM availability at plant grain, cleared-share offer
   ladder, GTC limits, storage-AS credits). Whether any of the five-ISO fuel
   mechanisms would move ERCOT's 2023 residual is **untested** (§5.1).
3. **Large ISO-exclusive families encoding each market's real design**
   (armed flag counts: ERCOT 24 `ercot_*`, CAISO 21, MISO 16, NYISO 14,
   PJM 10, NEISO 4). These are *structural*, not drift: RA must-offer exists
   only in CAISO; ORDC/ASDC co-optimization only in ERCOT; RDT/TCDC only in
   MISO; LCR/TSL localities only in NYISO; winter fuel security only in
   NEISO; DA virtual depth + star-node congestion only in PJM. Rule 25 makes
   the fitted *values* non-transferable — but the *mechanism shapes* transfer,
   and that is what the `U` cells track.

**Where the six genuinely disagree on the same phenomenon** (each a deliberate,
logged choice, not an accident): coal offer economics (sigmoid passthrough
everywhere coal matters *except* MISO, which refuted the SOM deep-discount
premise and runs near-cost + take-or-pay committed bands); scarcity price
formation (in-LP co-opt: 5 of 6; CAISO alone runs a post-solve overlay and has
**never tested the in-LP co-opt** — its pergen builder is incomplete);
commitment scaffolding (three per-ISO bridges off one shared detector vs
floor-limb registries vs NEISO's legacy-P2 exception); interchange (priced
node CAISO/PJM/MISO/NYISO vs fixed tranches NEISO vs n/a ERCOT); outage
re-basis (ERCOT measured-DAM keeper; NEISO/MISO tested-and-rejected theirs;
PJM's is intaken-but-untested); `wefor_multiplier` 0.7 five ISOs vs 1.0 MISO.

**Forecast-lane similarity is much higher than backcast** — by design the
forecast reference config is bare `ScenarioConfig` defaults + `mode`, so the
six differ only through registries: capacity-curve clearing (PJM/MISO/CAISO/
NEISO on; NYISO deliberately excluded pending re-calibration; ERCOT
energy-only), the reserve-margin backstop (off for ERCOT), the ERCOT-only
correlated-outage curve, and per-ISO PRM/ELCC/net-CONE tables.
**Keeper-only mechanisms whose global default is False never reach the
forecast lane** (verified for `coal_econ_marginal_hr_bound`,
`measured_ct_heat_rates`, `hydro_budget_nameplate_aware`,
`carry_operating_mothballs`, and CAISO's `capacity_deliverability_limits`
part (a)) — a structural inheritance gap the matrix's `fc` fields track; the
G4 mode-aware seam (forward analogues like `ercot_reserve_supply_forward`,
`caiso_corridor_atc_forward`, `--hydro-forecast-budget`) is the sanctioned
closure path, mechanism by mechanism.

## 3. Reading the matrix

- **Categories** (14) follow production-cost-modeling practice: market
  structure; price formation & scarcity; reserves/AS co-optimization;
  commitment & floors; offer curves; fuel; outages/availability;
  renewables & hydro; storage; network/seams; demand; capacity evolution & RA
  (forecast); policy; emissions.
- **`mode`** tags the lane: `B` backcast-only overlay (measured artifact, no
  forward analogue), `F` forecast-only, `BF` both. Rule 13's admissibility
  test decides `B` vs `BF`.
- **`fc`** appears where the forecast-lane posture differs from the backcast
  cells (capacity rows; `correlated_forced_outage`;
  `capacity_deliverability`).
- **Row-level notes carry the adjudication one-liners** with calibration-log
  ids — the log entry remains the evidence of record.

## 4. Cross-ISO patterns the matrix makes visible

1. **Reserve/scarcity dormancy is one problem, not four.** Reserve duals sit
   at ~$0 in NEISO (all 26,280 h), PJM (max $211), MISO (0/6/2 h); CAISO
   models zero C3c hours. Shared root cause: LP-vs-MIP under the no-MIP
   mandate. ERCOT is the exception (its measured envelopes bite — and
   over-fire when placed in-LP). Any C3c lever queue below inherits this
   ceiling; PJM/NYISO/NEISO adjudications say the *reserve-tier* route is
   closed and the live candidates are *offer/DA-depth-side*.
2. **`hydro_budget_nameplate_aware` is the template transfer** (CAISO →
   PJM, promoted in both; MISO/NYISO/NEISO cells `U`), and it surfaced the
   **PS-inclusive hydro pin defect** — audit every hydro ISO whose BA omits
   `NG: PS` from EIA-930 `NG: WAT`.
3. ~~**`pjm_da_virtual_bids` is the highest-value untested transfer.**~~
   **Downgraded 2026-07-29 — it has now been refused at both ends it was tried**
   (NYISO nyiso-94 on identification, MISO miso-105 on a fully measured book),
   and miso-105 surfaced a question the family had never been asked: the measured
   net virtual curve's crossing price λ0 *is* the price the book cleared at
   ($0.09–$1.80 in MISO), so a stiff curve blends a measured clearing price into
   the dual at weight `N ÷ (S+N)` — 31–34 % in MISO on the annual mean, ~63 % in
   its tight summer hours. **This does not move PJM's `K`** (rule 25: PJM's
   premise is genuinely different — it has +7–11 GW of real net depth that MISO
   does not), but PJM's lane should measure its own λ0-gap and its own
   `N ÷ (S+N)` before this is transferred anywhere else, and CAISO/NEISO should
   answer that question in the same breath as the identification one.
4. **The CAMPD economic-layup defect is upstream of everything** (all six
   extracts; holdout frozen; MISO/PJM/NYISO re-tune required; downstream
   derived artifacts not yet re-derived post-guard — an open cross-ISO audit).
5. **Topology splits are dead at both tested ends** (ERCOT-117, MISO-79):
   missing congestion is sub-zonal; the path forward is data intake (nodal/
   station crosswalks), not invented interfaces.
6. **Registry hygiene items the audit surfaced** (file separately, not levers):
   `--ramp-limits` is a dangling CLI flag (no `ScenarioConfig` field — should
   `TypeError` if passed); `historic_outage_overlay` defaults True but has
   been inert since 2026-07-17; `correlated_forced_outage` defaults True with
   an ERCOT-only curve registry (silently inert ×5);
   `PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO` is empty; every
   `thermal_tranches_<ISO>.csv` is provenance-orphaned (miso-95); the forecast
   board's gate-(a) keeper names are stale vs HEAD.

## 5. Per-ISO lever queues (untested candidates → failing gates)

Ranked; each entry names the gate it targets and the identification that must
be derived **from that ISO's own data** before any solve (rules 23/25). Queue
order is a prior, not a mandate — a session with a better-identified lever
goes off-queue and says so. Entries already adjudicated elsewhere are *not*
repeated here; the matrix `R`/`G`/`I` cells are the DO-NOT-REDO list.

### 5.1 ERCOT — NOT-YET (keeper `2026-07-31-ercot145-gas-daily-shape`, C6 PASSES); open gates C3a/C3b/C3c/C7; ~~C7 lignite, coal seasonal split~~ CLOSED; ~~items 4+5~~ EXECUTED at ERCOT-145; ~~item 6~~ CLOSED `I` at ERCOT-146; the items-5/6 reopen route (measured CT-band re-identification) REFUSED at Phase 0 by ERCOT-147 — data-intake first (item 8)

**QUEUE ITEM 2 IS PARTIALLY EXECUTED (ERCOT-144, 2026-07-31).** The DOF half
landed: the ERCOT-144 lane retired the residual-identified coal offer DOF onto
measured PER-PLANT levels (`coal_perplant_offer_level` — every CAMPD coal
committed/econ tranche on its own plant's merged modal SCED TPO curve; DOF
ledger `n_residual` **8 → 6**, COAL_SIGMOID_DEFAULTS[ERCOT] +
coal_take_or_pay_tranches retired), which unblocked the **C6 governance
attestation — C6 now PASSES**. The LEDGER half was attempted and **REVERSED by
owner ruling the same session** ("not calibrated with caveats with 4 fails"):
C3a/C3b/C3c and C7-2023 stand as honest FAILs. A ledger disposition of the
attributed RT scarcity-formation object (or of C7's non-offer-surface cell) is
an explicit per-gate OWNER act — the caiso-145 pattern: one gate, one
dedicated disposition, on its evidence — never a session's own judgment.
Attribution evidence on the ercot144 keeper's own bytes, recorded for any such
future disposition: capped at the $200 tail threshold the model's mean is
within **−5.1/+0.5/−4.5 %** of the capped actual (2023/24/25) while the actual
>$200 tail wedge is **$18.61/$2.50/$0.63 per MWh** of annual mean vs the
model's $7.21/$0.51/$0.00; the load-weighted official C3a miss
(−36.4/−14.8/−14.3 %) exceeds the unweighted (−26.7/−6.9/−6.4 %) because the
miss concentrates in high-load hours. **A ledger records a limit, it does not
license a fit** (rules 1/13): no successor may close these gates with an
adder, haircut or residual-tuned value. Remaining live in-model work: the
un-chartered audit-grade item 7 below (item 5 CLOSED `G` and item 4
EXECUTED-with-keeper at ERCOT-145; item 6 CLOSED `I` at ERCOT-146 — see the
struck items; the C3b shoulder/winter residual ERCOT-145 measured now points
at the LOCAL daily gas basis, `winter_citygate_daily`, data-intake first —
no HSC/Katy daily series is on disk yet).

The lane is heavily enumerated; the honest top of the queue is closure work,
not a new sweep:

**THE C7 LIGNITE + COAL-SEASONAL-SPLIT TARGET IS CLOSED (ERCOT-142 Phase 1 →
ERCOT-143 Phase 2, both no-LP, keeper unchanged).** The seasonal split is
refuted in its level form, the floor reading is exonerated, the offer-slope
re-route has no measured object behind it, and the AS-reservation successor is
refuted in advance. See queue item 3 below — it is DONE, not open. **With it,
the last named LIVE ERCOT target is gone**: what remains is item 2 (the C6
governance attestation of the C3c tail) plus the un-chartered audit-grade items
4–7. C7's ERCOT cell stays failing at `2023 COAL_LIGNITE profile r 0.769`, 0.031
short, with its cause attributed **outside the offer surface** and no
rule-13-admissible mechanism available to carry it.

**CLOSED AT ercot138, binding on successors — do not re-open
(no LP solved; `docs/DIAGNOSIS-ercot138-coal-gas-ranking-2026-07-29.md`):**

- **The COAL side of the coal-vs-gas ranking.** A matched-band, matched-hour,
  denominator-free bid comparison against each class's OWN 60-Day SCED TPO
  conduct puts the model's coal committed/econ bands at **−1.6..+3.9 $/MWh**
  through the crossing band while the CC bands run **+2.8..+6.6 dear**; the gas
  leg carries **78–99 %** of the 2024 ranking gap and 50–78 % at p25–p50 in
  2025, and the verdict survives restricting both sides to identical
  crosswalked plants (2024: a flat **+$6/MWh** CC overpricing at p10–p75 with
  coal running $1–2.8 *cheap*). **No further coal offer lever is licensed** —
  touching coal to close a gas residual is the compensating-error pattern rules
  1/14 forbid. Coal's remaining signal is at p90 only (model tops out
  9.6–15.5 $/MWh UNDER measured), which is the near-tail/C3c lane and is
  OPPOSITE in sign to the crossing band.
- **`gas_offer_net_revenue_margin` as the lever for this defect.** §J measures
  its own delta on the ERCOT CC committed+econ band at **0.00 $/MWh at p50** —
  it is inert there. The level is set by the `offer_curve_by_group`
  CC_REGULAR multipliers underneath it (1.101× physical heat rate), which
  account for only ~29 % of the gap; the remaining ~71 % is that the real CC
  fleet offers a large share of its above-LSL MW **below its own fuel cost**
  and the model has no mechanism that can produce such an offer.

0. **ERCOT-138's successor — the CC committed offer SHAPE, on the SCED TPO
   instrument. BUILT AND SOLVED at ERCOT-139 (2026-07-30); KEEPER CANDIDATE
   awaiting the owner.** `cc_committed_offer_margin`, run
   `2026-07-30-ercot139-cc-committed-offer` (bundle `ercot139_cc_committed_arm`,
   full span 2023-25, single delta off the ercot137 keeper). The §7.3 open
   question was decided in favour of a **below-cost committed block** over a
   band-multiplier re-identification (the multipliers cap at ~29 % of the gap,
   have the wrong shape, and have the wrong year behaviour — precommit §0). The
   pre-registered C3c falsifier **HELD exactly**: 47/6/0 → 47/6/0, bit-unchanged,
   because the repriced block is deep inframarginal in every scarcity hour and
   the 118/119 drain channel was the *econ* legs plus a peak rebasis this arm does
   not touch. Coal gives back **−3.81/−3.49/−3.00 TWh** (61/40/35 % of the
   keeper's over-run), CC_REGULAR takes **+5.22/+5.07/+4.49**; the rubric fail
   set is EXACTLY the keeper's with no flips either way, at a pre-registered and
   pre-quantified C3a cost (−$1.082/−0.695/−0.906, all inside the predicted band).
   **Do not re-test the level or re-derive it** — it is measured and committed
   (`derive_cc_committed_offer_margin.py` over
   `ercot136_coal_headroom_conduct.json` B1_curve_bottom CC rows). **The named
   successor is the STATE, not another price lever:** with the bid now measured
   correct, the remaining CC dearness is the *econ* band and the remaining price
   deficit is top-of-curve (ERCOT-138 §5.6, opposite in sign) — the near-tail/C3c
   lane. See precommit §4.1's forward story if the owner declines promotion.
0b. **(historical framing of item 0, retained)** The best-identified open lever, and the direct gas-side
   analogue of the ERCOT-136→137 template this lane just validated end-to-end.
   The instrument is admissible for CC on the same grounds it was for coal
   (ERCOT-136 §A, committed: CC offers **95.3–98.5 %** of RT-dispatchable
   headroom into SCED, price-taking bucket 0.008–0.035). The measured target is
   ERCOT-138 §2.3: the real fleet offers **34.5 % / 64.7 %** of its
   above-min-load CC MW at ≤\$10 / ≤\$15 against the model's **0.9 % / 23.1 %**
   (2024 tail). Rule-19 clean as a REPLACEMENT of the band multipliers, never a
   fourth surface. **Two pre-registered failure modes are mandatory:**
   ERCOT-119's C3c drain (72→49, 13→3 — deflating the CC curve is exactly what
   caused it) and the p90 finding above, which runs opposite in sign. **Do NOT**
   re-test `ercot_offer_hrmult_ep_rebasis` / `_bands` (ERCOT-118/119 ordinary
   rejections; rule 26(a)) or `measured_ct_heat_rates` on this defect (the
   model's physical CC HR 6.915 is already reasonable and a heat-rate lever
   cannot reach a below-cost offer).
1. **Coal tranche-1 take-or-pay REPRICE — CLOSED, EXECUTED as ERCOT-137.**
   Lineage only: `docs/PRECOMMIT-ercot136-coal-minload-reprice-2026-07-29.md`
   (superseded) → `docs/PRECOMMIT-ercot137-coal-margin-offer-2026-07-29.md`.
   ERCOT-136 read the SCED TPO instrument and settled the
   self-scheduled/withheld/telemetered-down fork (none of the three fires);
   ERCOT-137 replaced the fitted \$4.50 with the measured net-margin form
   (`coal_offer_net_revenue_margin`, level 15.8807 / anchor 1.7387) and it is
   the ERCOT keeper. The ERCOT-116 adoption block that gated it is DISCHARGED
   (owner ruling R2). Do not re-open, and do not re-derive the identification —
   it is measured and committed
   (`results/calibration/ercot136_coal_headroom_conduct.json`).
2. **C6 governance attestation of the C3c tail** as an attributed
   measured-input limitation (ERCOT-101/107/108 adjudication) — the named
   closure route; blocked only by the 8 residual-identified DOF entries.
3. **Coal dispatch-band mechanism** (ERCOT-117 §5.3 named successor): real
   fleet works 0.54–0.72 of its range, model rides ceilings (43–50% of energy
   within 0.5% of plant-month max vs 3.6–6.9% actual) → C7 COAL_LIGNITE-2023
   + the ±1.5 GW coal seasonal split. Needs a measured band identification
   (CAMPD loading distributions), not a floor. **ERCOT-138 caution:** this is a
   dispatch-SHAPE lever and is NOT closed by ERCOT-138's coal-offer exoneration
   — but it is *adverse* to the C1 over-run (the model's coal price-taking base
   is 0.28 of capability vs a measured RT 0.49–0.52, so re-grounding it raises
   coal further). Charter it on C7, never as an over-run fix.
   **PHASE 1 DONE AT ERCOT-142 (2026-07-30, no LP built, no year solved, keeper
   unchanged) — the object is RE-ROUTED from a dispatch BAND to an offer SLOPE,
   and Phase 2 is chartered:**
   `docs/DIAGNOSIS-ercot142-lignite-shape-2026-07-30.md`, probe
   `scripts/probes/ercot142_lignite_shape_probe.py`. C7's ERCOT failure is ONE
   cell and ONE leg (`2023 COAL_LIGNITE: profile r 0.769 < 0.8`; the `cv_ratio`
   leg PASSES at 0.535/0.50, 2024-25 pass both), carried by ONE plant — Oak
   Grove (6180, 70 % of the class) in fall 2023. **The named ±1.5 GW coal
   SEASONAL SPLIT is REFUTED in its level form**: neutralising the seasonal
   level mix moves annual r **0.769 → 0.738**, i.e. worse. **The floor reading
   is closed**: `COAL_MUSTRUN_BY_PLANT[6180]=45.0` ⇒ 808 MW is *exactly* the
   measured overnight floor, and it is not the pin (model sits ~730 MW above
   it). **The cause is offer-curve REACH**: Oak Grove's entire modelled curve
   tops at **$21.19**, below the $24.34 overnight price, so no LP can back it
   down. **The measured identification exists** — `B2_supply_grid`
   (`results/calibration/ercot136_coal_headroom_conduct.json`) puts **35.7 pp
   of coal capacity between $17.5 and $25**, straddling that price. Two
   hypotheses are now DO-NOT-REDO: daily **unit commitment** (refuted at unit
   grain — both units stay online and back down together, so this is continuous
   turndown and the ERCOT-127/128 pure-LP blocker does *not* apply) and **"not
   price-following"** (a Pearson-on-levels artifact; robust Spearman within-day
   gives REAL ρ 0.446 in 2023 vs 0.208/0.217 in 2024-25). Phase 2 must identify
   the slope with **zero swept parameters** and carries a pre-registered **hard
   kill: 2025 `profile_r` ≥ 0.80** (the ex-ante sweep shows too much backdown
   drives 2025 from 0.964 → 0.769).
   **▶ CLOSED AT ERCOT-143 (2026-07-30) — NO ARM, NO SOLVE, KEEPER UNCHANGED.
   THIS QUEUE ITEM IS DONE; DO NOT RE-OPEN IT.**
   `docs/DIAGNOSIS-ercot143-lignite-offer-slope-2026-07-30.md`, probe
   `scripts/probes/ercot143_lignite_offer_slope.py`. Phase 2 ran the
   identification and it **does not exist**, which is the outcome ERCOT-142 §8.2
   pre-registered. Resolved **per plant** instead of fleet-pooled, Oak Grove
   submits a **near-horizontal** SCED curve — `(0 MW @ $9.28) → (880 MW @ $9.64)`,
   a **$0.36** spread, 98.2 % of capability at or below **$10** — while the
   model's Oak Grove spans **$13.14 → $38.94** (spread $25.80, cap-wtd $16.10),
   so the model's lignite is already **22–72× steeper** (against the plant's own
   $1.16/$0.36 spreads) and **$4–7/MWh dearer** than the real plant, and the
   premise is backwards. The cited 35.7 pp segment belongs to **other plants** (Martin Lake
   0.535, Parish 0.539, Limestone 0.455 vs Oak Grove **0.016**, Major Oak
   **0.001**) and is **not slope at all** — every plant but Parish offers a flat
   curve and the fleet's smooth rise is **cross-plant level dispersion**, already
   carried by per-plant fuel/HR and already calibrated on LEVEL by
   ERCOT-137/138/140. The corpus also **cannot see the window** (h0–h8 is 8.4 %
   of it, all from the one year with no turndown; no 2023 SCED exists), and in
   the full-24-h **DAM** disclosure Oak Grove submits **no energy curve and holds
   no AS award in any of 2023/2024/2025** — which additionally **refutes the
   AS-reservation successor in advance**. Also **supersedes ERCOT-142 §6's
   `$21.19`**: on the current ercot140 keeper Oak Grove's top is **$38.94**
   (2023), already above the overnight price. The residual cause is **outside the
   offer surface** (intra-zonal North congestion — not representable in a 7-zone
   network, and ERCOT-117 closed the topology family — or QSE self-schedule,
   which fails rule 13). **No successor is chartered**; C7's ERCOT cell is left
   failing at 0.769 with its cause attributed.
4. ~~**Five-ISO fuel stack on ERCOT** (`gas_daily_shape`,
   `gas_monthly_actuals`, `gas_plant_monthly_fuel_pricing`) — consistency
   audit + candidate for 2023 winter-volatility C3b; cheap A/B, zero new DOF.~~
   **▶ EXECUTED AT ERCOT-145b (2026-07-31) — audit + one A/B, PROMOTED
   KEEPER `2026-07-31-ercot145-gas-daily-shape`.** Precommit
   `docs/PRECOMMIT-ercot145-gas-daily-shape-2026-07-31.md` (pushed before
   the solve). The audit stamped the two already-adjudicated cells from the
   record (`gas_monthly_actuals` ERCOT `G` on the Run-77 +$1/MMBtu reporter
   bias, with the MISO drift corrected K→n/a; `gas_plant_monthly_fuel_pricing`
   ERCOT `G` on the documented ~12 %-coverage design refusal) and solved the
   single live cell: `gas_daily_shape` armed as a single-delta A/B off
   ercot144 and promoted under the owner's in-session standard (structural
   improvement outranks gate regression; two ±1-hour threshold-straddle
   guard trips recorded honestly in the promotion note; C3a-2024/25 and
   C3b-2024 improved un-targeted; n_residual 6 unchanged). The 2023
   winter-volatility premise was WEAK on the HH side (2023 factor std 0.076)
   — the honest remaining winter lever is the LOCAL daily basis
   (`winter_citygate_daily`, ERCOT cell untested, data-intake first:
   Houston Ship Channel / Katy daily). `gas_hh_monthly_shape` still carries
   no matrix row (26c gap, owner ruling open).
5. ~~**`tranche_startup_amortization`** (PJM/MISO/NEISO form) vs ERCOT's
   season-spread ST startup — mid-merit/trough price formation candidate.~~
   **▶ CLOSED AT ERCOT-145 (2026-07-31) — REFUSED EX ANTE, NO SOLVE SPENT;
   CELL STAMPED `G`. DO NOT RE-OPEN without first retiring the fitted CT
   bands.** `docs/DIAGNOSIS-ercot145-tranche-startup-2026-07-31.md`, probe
   `scripts/probes/ercot145_tranche_startup_phase1.py`. Three measured
   grounds: (1) rule 19 — the target rows (CT_PEAKER econ/peak) are already
   occupied by fitted `offer_curve_by_group` multipliers carrying
   +$13.1/+$34.9/+$292 per MWh over their own recorded physical basis (2024
   gas) — 3–60× the measured fuel-invariant component ($20/MW ÷ the
   CAMPD-measured 5–7 h ERCOT plant-median run = **$2.9–4.0/MWh**;
   `campd_ct_run_lengths_ERCOT.csv` derived and committed this session,
   rule-23 frozen), so arming is stacking and the rule-19 replacement
   (physical + amortization) LOWERS the curve $10–50/MWh — the wrong
   direction everywhere; (2) the charter's target is not a level object —
   the sub-$200 load-weighted gap is −0.21/**+0.72**/−1.64 $/MWh
   (2024 POSITIVE) and within the top load quintile the residual is signed
   BOTH ways (act<$30 overpriced +5.7..+7.9, act $50–200 underpriced
   −11..−66): an under-dispersion/near-tail-frequency signature in the
   attributed scarcity-formation family that a near-uniform CT adder cannot
   re-disperse; (3) the C3b monthly residual (2024 shoulder −, summer +;
   2025 worst Apr/May) is item 4's outage-season/fuel-shape object, not the
   amortization signature. The season-spread ST form is row-disjoint (ST_GAS
   committed row) and was never the incumbent; the fitted multipliers are.
   Reopen only as one term of a measured CT-band re-identification (item 6 /
   SCED TPO on the CT fleet), never a stack. **The reopen route was attempted
   and REFUSED AT PHASE 0 by ERCOT-147 (2026-07-31, no solve;
   `docs/DIAGNOSIS-ercot147-ct-band-reident-2026-07-31.md`): the on-disk SCED
   TPO corpus cannot identify a CT band level (daily-repriced object, modal
   identity 11/160, both zero-parameter forms refuted by the year pair) —
   the reopen is now gated on item 8's three-part data intake.**
6. ~~**`measured_ct_heat_rates`** (NYISO form) on ERCOT's CT fleet — audit-grade.
   **Not** a candidate for the ERCOT-138 gas-dearness defect (see the closure
   note above); the CT fleet is its own question.~~
   **▶ CLOSED AT ERCOT-146 (2026-07-31) — INERT BY WIRING, NO SOLVE SPENT;
   CELL STAMPED `I`. DO NOT RE-TEST THE FLAG.**
   `docs/DIAGNOSIS-ercot146-measured-ct-heat-rates-2026-07-31.md`, probe
   `scripts/probes/ercot146_ct_heat_rates_phase1.py`. The flag's consumer is
   the `load_fleet_from_csv` path; under `use_campd_bins` ERCOT's thermal
   fleet comes from the curated sheet (`load_campd_bins`), which never
   receives it — base fleet flag-on vs flag-off is **byte-identical**
   (609 generators), so the A/B would produce a bit-identical bundle.
   ERCOT's own artifact was derived and committed anyway
   (`campd_ct_heat_rates_ERCOT.csv`, 34 plants, 99.2 % of metered class CT
   energy, no adverse selection): it **confirms** the CAMPD-derived curated
   sheet on its own basis (loaded gross −1.0 % cap-wt) — the +6.5 % net
   delta is entirely the gross→net parasitic conversion, a fleet-wide sheet
   basis convention, not per-plant noise. The artifact is the physical-HR
   term of the licensed successor: the measured CT-band re-identification
   (item 5's reopen condition — SCED TPO CT levels + this HR + the run-length
   start term) that retires the fitted CT multipliers. Mixed-facility CT
   rates at 9 uncurated-CT plants (1,708 MW) recorded as evidence for the
   Martin Lake-family class-composition ruling. **That successor was run and
   REFUSED AT PHASE 0 by ERCOT-147 — see item 8; the two committed artifacts
   stay ready for the post-intake lane.**
7. **WP-B nodal curtailment layer** — *data-intake first* (station→area
   crosswalk does not exist in-repo), then the under-curtailment gap
   (ERCOT-121).
8. **The CT-band re-identification reopen intake** (ERCOT-147, 2026-07-31 —
   Phase 0 REFUSED ex ante, no solve spent, keeper unchanged;
   `docs/DIAGNOSIS-ercot147-ct-band-reident-2026-07-31.md`, probe
   `scripts/probes/ercot147_ct_band_phase0.py`). Coverage was NOT the
   blocker (157 CT resources / 12.0 GW in all four extracts, reach 1.00 of
   HSL); the object is: the CT fleet's submitted TPO curve is
   **daily-repriced** (intra-day variance share 0.14), fails the ERCOT-144
   modal-identity licence (11/160 full-key, 20/160 price-only vs coal's
   ×1436), holds no stable $ level (daily rel IQR 0.64) and no stable gas
   multiple (0.32–0.43 HH-normalized; year pair ×1.26–1.99 vs gas ×1.97 —
   both forms refuted in opposite directions across resources), and 63–67 %
   of capacity's daily p50 sits below sheet-HR × HH burn — conduct vs local
   fuel basis unresolvable with no Texas hub daily series on disk.
   *Data-intake first, three parts, each owner-authorized:* (a) CT-scoped
   full-span 60-Day SCED extension 2023–2025 (all days/hours,
   SCLE90/SCGT90); (b) Texas hub daily gas basis (Waha + HSC/Katy — the SAME
   intake `winter_citygate_daily` needs; licensing check first, pjm-139 W1
   day-scale bound applies); (c) a ~150-site CT resource→plant hand
   crosswalk (6/165 accepted in `ercot-dam-plant-crosswalk.csv`; Morgan
   Creek MGSES_CT1–6 confirmed in-corpus). DO NOT re-run Phase 0 on the
   existing four extracts.

### 5.2 CAISO — **NO failing criterion** (keeper `2026-07-31-caiso147-chp-heat-rates`, CALIBRATED-WITH-CAVEATS)

**BOTH former blockers were DISPOSITIONED BY THE OWNER at caiso-145
(2026-07-30) and are now ACCEPTED MEASURED-INPUT LIMITATIONS** — ledgered in
the keeper's `calibration_attestation.json`, spending 2 of the 3 non-protective
ledger slots (protective 0/1, FAILs 0): **C3c-2023/24** on caiso-131 §9 **A4**
with the caiso-144 evidence, and **C3a-2025** on the caiso-141 **A2 data wall**.
The evidence and the standing limits stay exactly as written below — a ledger
records a limit, it does not license a fit — so the two subsections that follow
remain the binding reference for anyone tempted to reopen either gate.

**Neither caveat is ever closable by an adder, haircut or any value tuned to the
residual** (rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`). The only routes that
reopen either are owner-funded intakes, both unfunded at adoption: the
**SoCalGas OFO declaration record** (C3c — the one path to an unfitted C3c-2024
trigger) and **non-public hourly pumped-storage data** (C3a). A successor
proposing a lever for either gate must bring **new evidence against a named
caiso-140/141/142/143/144 DO-NOT-REDO cell**, not a re-framing of a closed one.
CALIBRATED-WITH-CAVEATS is a rubric determination, **not** the rule-22
calibration-complete marker — CAISO holds no marker, so every out-of-training
year stays quarantined. (caiso-145; `docs/calibration-log/caiso.md`.)

Items 2–8 below are the live lever queue and are **not** blocked-gate work: they
target C5a and the standing structural/offer questions. Items 1, 5 and 6 are
struck through — 1 and 5 were adjudicated and closed **without spending a solve**
(caiso-144 and caiso-136), and **6 was spent and PROMOTED at caiso-146**. They
are kept in place so the numbering stays stable and none is re-proposed.
**Live queue as of 2026-07-31: items 2, 3, 4, 8.** (Item 7 was SPENT and PROMOTED at caiso-147.)

**C3a-2025 IS DIAGNOSED-UNCLOSED WITH AN EMPTY IN-MODEL LEVER QUEUE (caiso-142);
LEDGERED at caiso-145.**
All three of `FINDING-caiso140` §E's asks are resolved *against*, so no successor
should open a C3a-2025 candidate without new data or an owner decision:

- **A1** (per-plant own-p25 committed-gas ride-through floor) delivers **< half**
  the −0.31 the gate needs (+757/+304 MW belly/night ≈ −0.13 upper bound);
  DO-NOT-REDO standalone (caiso-140 §D/§G).
- **A2** (hourly PS ↔ conventional-hydro split) is **WALLED** — no public source
  separates them, Helms + Eastwood = 60.3 % of the fleet is uninstrumented
  (caiso-141; re-open conditions are probe-checked, `_caiso141_water_source_survey.py`).
- **A3** (the P1 export-sink seam) is the **wrong sign**: an absorption column can
  only ADD demand, so it can only weakly RAISE λ, and the export leg is priced
  *below* the plateau's own marginal-import λ by the corridor's OATT wheel + 2ε.
  The seam's **infrastructure defect is real and now fixed** (flag-gated,
  default-off, `caiso_p1_export_sink_seam`); the mechanism is rejected ex ante
  as a price lever (caiso-142 §C/§D/§H), and the solved A/B under the owner's
  structural grant then confirmed the R by measurement — the restored outlet is
  **node-level resale, not export** (caiso-142 §J). **caiso-143 closes the
  follow-on lane too:** both prerequisites that arm named are refused (no
  node-level constraint exists — the soundness set is non-convex; no export
  price basis is identifiable without a fitted value), leaving caiso-138 §C
  firm-block elasticity as the only live prerequisite.

What remained for C3a-2025 was owner-level: land non-public hourly PS data, or
accept it as diagnosed-unclosed (the nyiso-97 C3c disposition). **The owner
accepted it at caiso-145** (ledgered, 2026-07-30); the non-public PS intake is
the only route that reopens it. **Do not propose any export / absorption /
"somewhere to put the surplus" mechanism for it** — caiso-142 §H generalises the
sign argument to every basis and bound.

1. ~~**`energy_reserve_coopt` + completing `caiso_reserve_coopt`**~~ —
   **DISCHARGED EX ANTE at caiso-144 (2026-07-30, no-LP).** The "complete the
   builder first" premise was stale: storage RS + hydro were already completed
   in `_caiso_design` (issue #1492 constraints 2/3; only Regulation stays
   walled as a build). On the caiso-139 keeper's committed hourlies the
   completed design's requirement is covered with strictly positive
   family-level slack in every hour of 2023–25 (min +854/+1,485/+2,114 MW,
   storage RS excluded; +max-measured-RegUp sensitivity still 0/2/0 short
   hours with 2.6–3.0 GW of excluded storage RS covering the 2), so the armed
   LP is EXACTLY inert — matrix cells `energy_reserve_coopt`/`reserve_pergen`
   CAISO → `I`, DO-NOT-SOLVE. Decisively for C3c: in reality's RT >$200 hours
   the pool is slack by 1.6–10.5 GW. **The rule-19 scarcity-owner question is
   fully adjudicated:** the in-LP route is closed, and the caiso-137b overlay
   charter is ANSWERED NEGATIVE by measurement in the same finding (timing
   overlap with the actual tail ≤ 1/90 hours over three years — the actual
   C3c tail is WINTER-MORNING fuel/cold-snap, not model-state scarcity).
   **C3c's in-model queue is now EMPTY on every route** (offer rungs closed
   caiso-131 §10, reserve tiers closed caiso-144 §B/§C, overlay refused §D,
   fuel grain already armed to its measured daily ceiling §E). **Dispositioned
   at caiso-145 (2026-07-30): the owner ADOPTED A4** — C3c-2023/24 is ledgered
   as an ACCEPTED MEASURED-INPUT LIMITATION on the MISO/NEISO precedent
   (CAISO now spends 2 of 3 non-protective slots, C3c + C3a together). **A3**
   (the SoCalGas OFO declaration-record intake) stays unfunded and is the one
   path to an unfitted C3c-2024 trigger — the only route that reopens the cell.
   (`FINDING-caiso144-coopt-dormancy-c3c-frontier-2026-07-30.md`.)
2. **Corridor/export-path congestion family** — the *selected* open family for
   C5a (59–101% of the belly wedge is DSW→CA congestion, caiso-120/121);
   surplus-regime import pricing is the specific defect. **Scope narrowed by
   caiso-142:** the *export* half of this family is closed — the export-direction
   envelope is armed and correct (it is each corridor group's `limit_dn`), the P1
   seam that made it unreachable is fixed flag-gated, and no absorption mechanism
   can lower a λ. The remaining live question is the **import** side's price
   basis, and the shared-headroom release channel is dead (the simultaneous
   interface group binds in 0 of 26,280 corridor-hours). **Scope narrowed again
   by caiso-143 — the export half is now closed with NOTHING unbuilt.** The two
   prerequisites caiso-142 §J named are both refused at the design gate: the
   node-level export constraint is algebraically redundant with the corridor
   group's `limit_dn` *and* a sound sink is not LP-representable at all (the
   soundness set is non-convex; the tightest linear surrogate reduces to
   `F + I_econ ≤ 0`, infeasible while the must-flow block forces 11.7 + 15.6 TWh),
   and the export **netback price** — the one item caiso-142 §E left specified —
   is **not identifiable without a fitted value** (PNW p50 range $4.74 vs the
   import basis's $1.25, $7.70–10.48 season/depth cell range, 2023 sign flip;
   DSW stable but **wrong sign**, since CA clears *above* the raw hub in 62–72 %
   of real DSW net-export hours, so `hub − ε` under-prices that outlet by ~$4.4).
   The only live prerequisite left is **caiso-138 §C firm-block elasticity**, and
   with the forced injection removed no new export constraint is needed at all
   (caiso-143 §F).
3. **S2: DA/RT two-settlement separation charter** for the evening/overnight
   storage spread (caiso-129's only surviving candidate; a real charter, not a
   shaped floor — the S1 family is DO-NOT-REDO).
4. **`tranche_startup_amortization`** — untested; evening-ramp start economics.
5. ~~**`unit_outage_short_windows` / `unit_partial_outage_windows`** — derive
   for CAISO~~ — **CLOSED, cell is `I`: ADJUDICATED INERT ex ante at caiso-136
   (no solve spent).** Nothing to derive. The detector is coal-only and CAISO's
   coal class is **CEMS-invisible**: the fleet carries 2 coal units / 50.0 MW
   (0.16 % of capacity, 0.04–0.07 % of keeper energy) at one facility (10684
   Argus Cogen), and that facility is **absent from CAMPD entirely** — the CA
   extract holds 108–109 facilities with zero coal-fuelled rows in 2023/24/25
   and no 10684 row in the facility-level extract either. Both derives return
   0 windows; no guard setting can change that, because there is no input
   series to measure. Re-open **only** if CAISO gains a CEMS-reporting coal
   unit. (`FINDING-caiso136-unit-availability-windows-2026-07-28.md`.)
6. ~~**`measured_ct_heat_rates`**~~ — **SPENT AND PROMOTED at caiso-146
   (2026-07-31); cell `U` → `K`, keeper
   `2026-07-31-caiso146-ct-heat-rates`.** A rule-14 `[R-ACCURATE]`
   measured-input swap with zero fitted parameters, single-flag A/B against a
   same-HEAD zero-delta control. CAISO's own artifact (rule 25): 43 plant rows,
   all `flag=="ok"`, 76.8 % of class capacity but **99.9 % of the class's own
   metered CAMPD CT energy**; **one-sided** unlike both precedents (41 plants /
   5,649 MW cheaper vs 2 / 198 MW dearer, cap-wt −1.159 MMBtu/MWh = −10.7 %).
   CT_PEAKER moves 26→42 / 10→15 / 11→19 % of actual; every criterion verdict
   unchanged; C7 CT_PEAKER 2025 `profile_r` **improves** 0.837 → 0.864 and C8
   forced share falls. **The heat-rate route to caiso-119 R4 is now CLOSED by
   measurement** — a mispriced offer was *part* of the CT priced-out defect but
   only part, and the residual 2.4–3.7 TWh is not a heat-rate defect (same
   conclusion as nyiso-89, derived independently on CAISO's data). R4's
   guardrail still binds: any successor lever must be a real obligation-keyed
   mechanism with a cited D-4 window, never an offer markdown sized to the gap.
   The **CHP** half of this item is untouched and remains live — see item 7.
   (`FINDING-caiso146-measured-ct-heat-rates-2026-07-31.md`.)
7. ~~**`measured_chp_heat_rates`**~~ — **SPENT AND PROMOTED at caiso-147
   (2026-07-31); cell `U` → `K`, keeper `2026-07-31-caiso147-chp-heat-rates`.**
   A rule-14 `[R-ACCURATE]` *and* rule-21/24 swap with zero fitted parameters:
   CAISO is the **first hand-factor ISO** to take this lever, so the delta was
   not eGRID-credited → measured (as in MISO) but **off-registry hand factor →
   published measurement**. **A derive defect was found and fixed before any
   solve:** the basis gate compared eGRID's credited rate against the *shipped*
   rate, which in a hand-factor ISO **is** credited × 1.8 / × 1.15 — so **59 of
   65 excluded rows (3,089 of 3,186 MW) were excluded by the hand factor alone**,
   i.e. the gate was excluding precisely the population the mechanism exists to
   fix. Fixed ISO-generically at the replacement seam; MISO re-derives identical
   on every applied value (**this defect is latent in PJM too**). Artifact: 30
   applied rows / 2,371.8 MW, CC_CHP at **100.0 %** of the class's metered CAMPD
   energy, CEMS validation **13/13** at median 1.00000. The correction is
   **two-sided and opposite** — CC_CHP +19.6 % dearer, CT_CHP −14.6 % cheaper.
   CC_CHP falls **117→108 / 120→108 / 108→102 %** of actual, the energy landing
   on CC_REGULAR (93→94 / 93→95 / 90→91 %); **no class moves away from actual**.
   Every criterion verdict unchanged, C7 shape improves markedly on the repriced
   classes (CT_CHP `profile_r` 0.393 → 0.852 in 2025), and the binding CT_PEAKER
   gates are unchanged. **Protective framing corrected for all future CHP work:**
   CC_CHP/CT_CHP are exempt from **both** C7 and C8 by *explicit class list*
   (host-steam-pinned duty), **not** by the 2 % materiality floor — a CHP class
   above 2 % of load is still ungated.
   (`FINDING-caiso147-measured-chp-heat-rates-2026-07-31.md`.)
8. **`nuclear_unit_availability`** — `K` in ERCOT and NYISO, CAISO `U`. Diablo
   Canyon is the 2,240 MW MSSC that sets CAISO's entire reserve requirement
   (caiso-144 §B).

### 5.3 PJM — **NO failing criterion** (keeper `2026-07-30-pjm-140-rampenv`, CALIBRATED)

C1 CC_REGULAR-2023 and C3a-2025 closed at pjm-135; **C3c-24/25 closed at
pjm-136** and is UNCHANGED by pjm-137. The queue below is not gate-driven — it
is ranked by *structural* defect, per rule 1 `[R-STRUCT]`.

**READ ITEMS 12–13 FIRST (pjm-141, 2026-07-30; item 13 CLOSED at pjm-142,
2026-07-31).** PJM's remaining structural defect is diagnosed and named: the
model has **no hour-varying offer conduct** (every thermal LP row's within-day
offer σ is **$0.000000**), so its whole intra-day price amplitude comes from
merit-order traversal and it delivers only **31 / 33 / 32 %** of the measured
overnight→evening-peak swing — too dear overnight, too cheap at peak, with the
**annual level passing by cancellation**. The overnight
bottom-of-distribution miss and the winter morning ramp are **one defect**.
Its lever queue is **EMPTY WITH NO OPEN SUCCESSOR**: every in-model route is
`R`, owner-closed, spent, or barred by rule 23, and the one non-adjudicated
successor (the overnight gas commitment bridge) was **killed at pjm-142's
pre-registered no-LP pre-check** (item 13). The limitation stands as a
disclosed LP-representation boundary; it fails no gate. **Judge any PJM price
lever on the AMPLITUDE, never on the annual mean.**

**CLOSED AT pjm-137, binding on successors — do not re-open:**

- **The zonal-congestion route to the Dominion CT leg.** PJM's own day-ahead
  binding-constraint record (new intake `data/raw/pjm-binding-constraints/`,
  228,795 constraint-hours) puts only **6.34 / 3.06 / 6.19 %** of its congestion
  rent on a named zonal-scale interface and **80.0–87.8 %** on monitored
  facilities rated ≤ 230 kV; **`AEP-DOM` carries 0.041 / 0.071 / 0.236 %**. The
  constraints that dominate the DOM-separation hours are PLEASNTV TX3 500 kV,
  GOOSECRE TX1 500 kV, PLEASNTV-ASHBURN 230 kV, ASHBURN-GOOSECRE 230 kV and
  BRAMBLET-EVRGREEN — every one `zone = DOM` in PJM's own pnode registry, i.e.
  **both ends inside `PJM_Dominion`**. PJM's 500 kV EHV nodes (new intake
  `data/raw/pjm-ehv-lmp/`) measure **more** dispersion inside Dominion
  ($6.18/$8.68/$16.78) than across the whole DOM–AEP boundary
  ($4.76/$6.13/$14.42). This is the ERCOT/MISO `internal_congestion_split`
  refusal class. **No successor may propose another zonal congestion mechanism
  for this defect.**
- **`measured_ct_heat_rates` → K** (pjm-137 keeper). Adjudicated on PJM's own
  artifact; see the matrix cell.

**The queue:**

1. **The system-energy-price half of the Dominion CT deficit — the successor's
   target.** In the hours Dominion's real turbines run, the model's zonal price
   is **$17.72 / $26.69 / $54.61 /MWh** short; netting the measured congestion
   component out leaves **$8.63 / $14.37 / $26.88** (49 / 54 / 49 %) that a
   zonal model *could* produce. Measured DOM **MEC** alone runs at a p50 of
   $35.94 / $41.35 / **$58.86** in those hours against the model's whole
   Dominion dual at $32.07 / $32.28 / **$42.72**. This is an ISO-wide
   marginal-unit question and it joins item 5 below.
2. **The defect is ~1.9× smaller than every prior note said.** The Dominion
   `CT_PEAKER` actual is **3.066 / 4.048 / 5.218 TWh** on the benchmark's own
   unit-split per-plant record — not the 7.38 / 8.68 / 9.64 carried forward,
   which is the nine roster plants' *whole-plant* energy and counts Doswell's
   combined-cycle blocks as peaker output. After pjm-137 the gap is
   **−2.345 / −2.600 / −2.056 TWh**, i.e. the model is at **24 / 36 / 61 %** of
   actual. Take a zonal class actual from
   `frontend/data/backcast/bench/<ISO>/<year>.json.gz` (which carries
   `split: "unit_hourly"` at mixed sites), never by summing CAMPD over a plant
   roster.
3. **A `PJM_Dominion` NoVA/Loudoun split** is the structurally correct fix and
   is **blocked on one measured input**: PJM's metered-load feed stops at the
   transmission zone, so a sub-zonal load share would be a fitted scalar
   (rules 5/24). Refused until a measured sub-zonal load basis exists.
4. **C8 `CT_PEAKER` forced share** rose to 16.3 / 16.9 / 17.1 % at pjm-137 (all
   GROUNDED — D-4 clear, profile r 0.923–0.973, CV ratio 0.703–1.083) on a class
   whose ISO-wide volume fell 2.6–2.9 TWh. A clean pass under rule 20, but worth
   watching.
5. **G-20b guard false-negative lead — now PRICED, and the price is material.**
   pjm-138 §4.2 sized what
   `FINDING-guard-falseneg-audit-2026-07-27` §7 said no instrument could:
   removing the guard's own 2.8–5.0 GW from the tightest decile's offer stack
   moves the clearing price **+$4–23/MWh** on the mean (3 GW: +$3.97 / +$8.02 /
   +$14.95; 5 GW: +$7.45 / +$12.46 / +$23.36), i.e. **28–59 %** of that decile's
   system-energy gap, as a LOWER bound. The **verdict is unchanged** — that
   audit's D2 population test is clean 3/3 for PJM and its D3 exceedance is
   mostly a window-LENGTH effect — so this is a change of stakes, not of
   evidence. Route stays its §7.2: a within-window tight-hour treatment memo,
   owner sign-off, its own charter, LOYO within 2023–2025. **Do not arm anything
   on the price alone.**
6. **C3c margin** — still passes by **1 h** (2024) and **2.5 h** (2025) against a
   0.5× floor, untouched by pjm-137 and by pjm-138 (which solved nothing). Any
   delta must report its C3c effect explicitly.
7. **`pjm_dam_availability`** (**U**) — intaken but untested. pjm-137 measured
   that Dominion's real turbines are synchronised in 68.3 / 54.4 / 62.4 % of all
   hours, so the CT leg is **not** an availability defect; this lever now stands
   on the outage-envelope story alone. Note the ERCOT precedent before
   chartering it: the measured envelope there is *measured-correct* and was
   rejected twice on level (ERCOT-116/134).
8. **`st_gas_mustrun_p25_level`** (**U**, MISO form) — re-ground the six
   overnight ST_GAS floor limbs on measured operating levels (D-2 ST_GAS
   42–55 % forced). ~~**Newly motivated by pjm-138**: the model runs
   **$1.6–7.3/MWh too DEAR at h01–h04**~~ — **the overnight motivation is
   WITHDRAWN at pjm-139 on a size measurement.** The over-pricing is real, but
   `ST_GAS` cannot be its owner: in the keeper's own overnight hours (h01–h04)
   `ST_GAS` carries **0.9 / — / 1.9 %** of thermal energy (0.44 / 1.04 GW) at a
   night/peak ratio of **0.22 / 0.35** and cv **1.18 / 1.00** — i.e. it is a
   small, peak-following class, not an overnight floor-dominated one. The
   overnight stack is **`CC_REGULAR` 69 / 66 %** (32.3 / 35.2 GW, cv 0.19) and
   **`COAL_BIT` 23 / 26 %**, so a class 35× smaller cannot move a $3.4–6.9/MWh
   overnight gap. The keeper's ST_GAS forcing mechanism is also **`st_netload_drag`**
   (D-2: 54.7 / 51.3 / 42.5 % of class), a net-load-conditioned drag — not the
   "six overnight floor limbs" this item describes, which is the MISO form. The
   lever may still be defensible as a rule-23 re-derivation on its own source
   data; it is **not** an overnight-price lever. (`FINDING-pjm139` W4.)
9. ~~**`gas_daily_shape`**~~ — **STRUCK AT pjm-139. It is `K`, not `U`, and it is
   not a winter-ramp lever.** This item was wrong on both its premises and is
   recorded here rather than deleted so the error is not re-made. (a) The
   mechanism is **already armed in the keeper** —
   `pjm137_ctheatrate_B::run_config.json::scenario_config.gas_daily_shape = True`
   (carried on the `prb_overrides` channel) — adopted at **pjm-107**
   (2026-07-14), where it passed every gate and became the
   `2026-07-14-pjm-107-gas-daily` keeper. The matrix cell has read **`K`** since.
   The winter cell pjm-138 measured was measured *with the mechanism on*. (b) It
   could not reach an hour-of-day defect even if it were off: the factors are
   one-per-calendar-day, repeated across 24 hours (`hubs.py`,
   `np.repeat(day_factor, 24)`), so their within-day σ is **≤ 4e-16** and their
   hour-of-day mean profile is **flat to 0.000** — while the DJF system-energy
   gap swings **+$3.18 overnight → +$26.94 at h06–h07 → +$1.69 midday**
   (load-weighted 2025). A zero-intra-day-variation mechanism cannot move an
   intra-day differential, and its sign is wrong on the overnight half.
   (`FINDING-pjm139-winter-morning-ramp-is-a-ramp-rate-deficit-2026-07-30.md`
   W0/W1; the stale `DIAGNOSIS-pjm-dof-scarcity-tail` §B.3/§B.4 text that
   produced this item is corrected in place.)
10. **TETCO-M3 winter daily citygate** (`winter_citygate_daily` form, **U**) —
    own hub derivation, PJM cell genuinely untested. **But note what pjm-139
    measured before chartering it: a daily citygate series has the same
    calendar-day resolution as item 9**, so it inherits the same W1 objection
    against the *morning-ramp* cell. It remains defensible as a rule-14 accuracy
    correction to the winter *level* (PJM's delivered winter basis is a real
    quantity the model currently proxies with the HH+zonal-basis construction),
    and as a candidate for the **day**-scale winter tail — not for the intra-day
    ramp. Charter it on the level story or not at all. **Bound TIGHTENED at
    pjm-141:** the objection is now measured on the *whole* offer rather than
    inferred from the gas leg — every thermal LP row's within-day offer σ is
    **$0.000000** (item 12), so no calendar-day series can move an intra-day
    differential in this model. Item 10 is **not** a candidate for the overnight
    cell or the amplitude defect; it survives on the winter-**level** story
    alone.
11. **`ramp_envelopes`** — **SOLVED, PROMOTED and CLOSED at pjm-140 (2026-07-30).
    PJM cell `U` → `K`**, and it is the **first keeper in any ISO** to carry
    `ramp_limits=True` (`2026-07-30-pjm-140-rampenv`, superseding
    `2026-07-29-pjm-137-ctheatrate`). **Do not re-test it.**
    - **What it bought, and it is real:** with the flag off the LP asserts every
      thermal plant can move from any output to any other in one hour, and the
      model *acts* on it — the superseded keeper's own dispatch crosses the
      measured envelope in **0.393 / 0.463 / 0.319 %** of 1,699,246
      group-transitions, carrying **555,882 / 587,079 / 536,940 MWh a year** of
      ramping the real PJM fleet's measured maxima say those machines could not
      deliver. Arming it cuts that to **51,161 / 64,048 / 82,425 MWh** — a
      **90.8 / 89.1 / 84.6 %** reduction, ~0.5 TWh/yr of infeasible dispatch
      removed. Coverage: **194 live groups = 124.1 GW = 90.1 %** of ramp-eligible
      thermal capacity. Zero fitted DOF; ledger 17 → 18 with `n_residual`
      unchanged at 6.
    - **What it did NOT buy:** the chartered DJF h04→h07 model price rise moves
      only **+3.933→+4.004 / +4.554→+4.600 / +6.512→+6.546** — **+$0.07 / +$0.05
      / +$0.03**, i.e. **0.6 / 0.2 / 0.1 %** of the gap to PJM's own
      +$15.28/+$21.63/+$35.45, against a pre-registered ceiling of
      **+$5.55/+$13.44**. Dispatch is near-inert (worst class
      +0.262/−0.184/−0.219 %, every material class under 0.06 %). PREREG
      secondary 1 is refuted too: `CC_REGULAR` moves **up** and `CT_PEAKER`
      **down**, the opposite of the prediction. Every gate is unchanged — C1
      16/16 free 12/12, **C3c identical at 3/10/32 h**, C8 CT_PEAKER unchanged
      at 16.3/16.9/17.1 % all GROUNDED, zero slack and dump.
    - **THE TRANSFERABLE LESSON, and it is an all-ISO scope bound: a MAX-based
      envelope cannot be pre-checked with a p99-based excess statistic.** pjm-139
      W7 compared the model's p99 1-h move to the real fleet's **p99** (1.4–1.7×)
      and inferred that per-plant rows would bind. But the derive writes each
      plant's **MAX** pooled over 26,280 hours, and the model's own p99 sits at
      just **0.281 / 0.293 / 0.289** of that max (its own max at 1.415/1.478/1.361).
      A p99-vs-p99 excess of 1.7× is therefore fully consistent with binding in
      0.3–0.5 % of transitions. **Pre-check a bound against the bound.** This is
      the ERCOT-127 property ("the real fleet violates the envelope 0–10 times a
      year") now measured on PJM's own fleet.
    - **There is no second version of this lever.** PREREG §5's no-feedback
      ceiling forbids any multiplier, scale, haircut, blend, floor, cap,
      widening, tightening, per-plant override or **quantile swap** — so "re-derive
      it at p95 so it binds" is inadmissible. A binding ramp representation needs
      a **different mechanism with its own charter**.
    - **Operational cost now carried by the keeper:** 1,699,246 LP rows, ~23.3 M
      nonzeros, peak RSS 15.18 → 15.55 GB, so **swap is a requirement** for a PJM
      per-plant solve on a 15 GB box.
    (`FINDING-pjm140-ramp-envelopes-remove-infeasible-ramping-but-not-the-price-shape-2026-07-30.md`;
    `PREREG-pjm140-ramp-envelopes-2026-07-30.md`.)

12. **CLOSED AT pjm-141 (2026-07-30) — the instrument ran, and the answer
    RE-FRAMES the item.** Its named instrument (the committed `--with-fleet` W6
    census, plus the new tranche census
    `scripts/probes/_pjm141_overnight_tranche.py`) is run, no LP solved. Kept
    rather than deleted so the re-framing is not undone.
    - **The chartered question is answered and the tranche is NOT the defect.**
      The marginal rung at h01–h04 is **`econ` 78.7 / 78.4 / 77.5 %** of the
      marginal set at **100.0 %** detection (dominant pair `CC_REGULAR:econ`
      40.2 / 38.5 / 35.4 %; `committed` only 14.4 / 15.3 / 14.9 %), and the
      **evening-peak control is statistically identical** (`econ` 77.3 / 79.5 /
      80.7 %). No floor rung, no part-load artifact, no pinning at the margin.
      The model's overnight thermal requirement also matches PJM's own CAMPD
      actual to **+0.9 / −2.0 / +2.5 %** (CC within ±1.4 %), so it is not simply
      standing deeper in its stack.
    - **§W4's "no offer cheap enough" clause is CORRECTED.** The model's cheapest
      thermal offer is **$4.50** (coal `mustrun`, fuel sunk) — *below* PJM's
      overnight p05 in all three years. What it lacks is **depth**: only
      **6.65 / 4.43 / 6.40 GW** of 95.9 / 94.4 / 96.5 GW available offers price
      below the target (**4.7–6.9 %** of the stack, the same order as ERCOT-136's
      measured 5.8–8.4 %) against 46–53 GW of thermal to serve. The clearing
      rung's own p05 is only **+$3.51 / +$5.14 / +$3.33** above target.
    - **Marginal ≠ energy, and `CT_PEAKER` is the surprise.** Marginal shares are
      `CC_REGULAR` 44.5 / 42.3 / 40.0 %, **`CT_PEAKER` 17.4 / 20.7 / 27.0 %**,
      `COAL` 21.0 / 19.9 / 15.3 % — `CT_PEAKER` is a fifth to a quarter of who
      sets the overnight price on **0.6–1.0 GW** of output, invisible in §W4's
      energy view. (Item 8's `ST_GAS` closure is confirmed on this second,
      independent measure: 1.8 / — / 1.9 % of the marginal set.)
    - **THE STRUCTURAL FINDING, and it is bigger than the overnight cell: nothing
      in the model's offer varies by hour.** Measured on the keeper's own
      offers, **every one of the 2,034–2,044 thermal LP rows posts the SAME
      offer in every hour of a calendar day** — within-day σ **$0.000000**,
      h01–h04 offer = h16–h18 offer to **$0.0000**, all three years. The startup
      markup is amortized per calendar **month**; the mid-curve conduct surface
      is the only hour-varying element and its `[0.80,0.90,0.97]` bins put
      **99.0 / 97.2 / 94.4 %** of h01–h04 *and* **61.3 / 61.1 / 63.7 %** of
      h16–h18 in the **same bin 0** (a ~20 GW net-load swing inside one conduct
      level). So the model's entire intra-day price amplitude comes from
      merit-order traversal alone.
    - **ONE DEFECT, TWO WINDOWS.** The model reproduces **31 / 33 / 32 %** of the
      measured overnight→evening-peak swing, against pjm-139's **26 / 21 / 18 %**
      of the DJF h04→h07 rise — the same flat-stack defect at two points. The
      error is sign-symmetric: **+$6.82 / +$5.78 / +$3.40** overnight,
      **−$7.62 / −$11.37 / −$22.19** at peak. **PJM's annual price level
      therefore passes by CANCELLATION, not correctness** — judge any successor
      lever on the AMPLITUDE, never on the mean, and pre-register its
      annual-level effect.
    - **The peak half is already owner-closed; only the overnight half is open.**
      The peak under-pricing is substantially pjm-138's reserve/opportunity-cost
      lane (owner-closed 2026-07-11). Overnight PJM's reserve price is small and
      the model's is zero, so that credit does not touch the overnight half.
    - **`import_hub_pricing` REFUTED as the overnight owner** (cell stays `U`):
      PJM is genuinely a net exporter overnight and the model tracks EIA-930
      `Total interchange` to ~1 GW with a sign that flips across years
      (+0.83 / +1.09 / **−1.29** GW), wrong-signed for the defect in 2023–24.
    (`FINDING-pjm141-overnight-marginal-tranche-is-correct-the-defect-is-a-flat-offer-stack-2026-07-30.md`.)

13. **PJM's diurnal amplitude deficit is a DIAGNOSED, UNCLOSED structural
    limitation, and the lever queue for it is EMPTY.** The mechanism the
    diagnosis names is **hour-varying offer conduct on the marginal rung**, and
    every in-model route is adjudicated — do not re-charter any of them:
    - `measured_offer_surface` PJM = **R** under BOTH conditioning definitions
      (pjm-123 pre-check, pjm-126/127 season, **pjm-132 "Lane 2 ENDS"**, which
      solved it and measured C3a moving −0.011 $/MWh with dispersion *narrowing*).
    - **Re-binning that surface's edges is barred independently of the verdict**:
      with unchanged source data it is a re-derivation against a residual, which
      **rule 23 `[R-FROZEN-DERIVE]`** forbids. There is no admissible "re-bin it
      so it binds".
    - The reserve/scarcity route is **owner-closed** (pjm-138 §6) and does not
      reach overnight; `ramp_envelopes` is **spent** (pjm-140 §6); **any daily
      gas series** — including item 10 — is barred by the zero within-day σ.
    This is the state NYISO's C3c lane reached at nyiso-96/97, and it is a
    legitimate terminal state under rule 1 `[R-STRUCT]`: the alternative is an
    adder tuned to the residual, which rule 13 forbids. **It fails no gate** —
    the keeper is CALIBRATED on every criterion.
    ~~**The one non-adjudicated successor** (`FINDING-pjm141` §8 lead 1): a **PJM
    overnight gas commitment bridge**.~~ **ADJUDICATED AND KILLED AT pjm-142
    (2026-07-31) — `gas_commitment_bridge` PJM `U → R` at the pre-registered
    no-LP pre-check** (`PRECHECK-pjm142`, thresholds committed before
    measurement; `FINDING-pjm142`). pjm-141's partial ex-ante refutation
    (volume already correct ±2.6 %; `committed` already loaded preferentially)
    is completed with the other half measured on the keeper's own fleet: the
    bridge-eligible idle pool — merchant gas-CC committed tranches, rule-18
    physics via `CC_COMMITMENT_PARAMS`, day-anchored, **net of the 1.0–1.5 GW
    the incumbent `cc_mustrun_per_plant` already floors** (rule 19) — is
    **0.65–0.95 GW** (1.36–1.60 GW even at 0.574 × plant capacity, the largest
    min-load fraction any ISO ever measured), against a measured
    **2.57–3.37 GW-per-$1** merit-curve slope. Forcing the ENTIRE pool moves
    the overnight dual **$0.52 / $0.41 / $0.64** vs the $1.00 K-A bar (FAIL all
    three years; 7.6–18.7 % of the overnight error), and `CC_REGULAR:econ`
    keeps plurality marginal ownership even at full forcing — the ownership
    shift the lever was chartered for does not occur. K-B (volume) would have
    passed; the kill is pure materiality. The restart screen confirms the
    commitment *story* is real (94–100 % of the pool holds vs restart) — the
    model already delivers it economically (19.5–22.2 GW of eligible committed
    in merit overnight). Port prerequisite recorded and mooted: PJM's
    CAMPD-bin tranches carry no commitment physics (`min_run`/`min_down` = 0),
    so any future PJM commitment mechanism must wire the heat-rate table
    first. **With this, the amplitude defect's queue is empty with NO open
    successor** — do not re-open without new evidence that the pool itself was
    mismeasured (a different min-load value or a different threshold is not
    new evidence).

**CLOSED AT pjm-138, binding on successors — do not re-open (no LP solved;
`FINDING-pjm138-system-energy-is-reserve-opportunity-cost-2026-07-29.md`):**

- **The RESERVE/SCARCITY route to the Dominion CT leg, and to PJM price
  formation generally.** PJM's own published day-ahead reserve market prices
  synchronized reserve **above zero in 84.2 / 96.7 / 47.6 %** of all hours
  (Primary 45.1 / 64.0 / 30.8 %) at a cover ratio of **1.00–1.11**; the model's
  reserve dual is above zero in **0 / 2 / 28** hours of 8,760. That dormancy
  correlates with the model's system-energy price gap at **r = +0.79 / +0.60 /
  +0.66** and accounts for **82 / 52 / 57 %** of it in the Dominion CT-running
  hours. **It is not a missing mechanism**: the requirement is PJM's own
  measured series, the demand curve is PJM's published two-step ORDC
  (`pjm_ordc_curve.csv`, m11 §4.3.3), and the in-LP per-generator joint-headroom
  co-optimization that is *designed* to price the opportunity cost is armed and
  is its sole owner under rule 19. It clears at $0 because the model's reserve
  supply is 5–10× the requirement — the **LP-vs-MIP boundary** pjm-82 named,
  which the no-MIP mandate makes a **disclosure, not a defect**. The lane was
  owner-closed 2026-07-11 and this measurement confirms that closure on PJM's
  own numbers. **Requirement-side dynamic reserves (the old queue item 9) is
  adjudicated INERT by measurement** and the matrix cell moves `.` → `K`.
- **The size of what is left.** Of the CT-hour price deficit
  (**$17.97 / $26.44 / $54.06**, restated on the corrected hour key), pjm-137
  closed **54.6 / 51.8 / 54.2 %** as intra-zonal congestion and pjm-138
  attributes **37.3 / 25.2 / 26.2 %** to the reserve opportunity cost. **Only
  8.1 / 23.1 / 22.1 % is reachable by any energy-stack mechanism**, and on an
  annual load-weighted basis the model already reproduces PJM's own system
  energy price to **+$0.47 / +$2.62 / +$8.48** — so the residual is a
  *dispersion* defect, not a level one, and any successor lever must raise tight
  hours **without** raising slack ones (the gradient test the measured offer
  surface failed at pjm-123).
- **Keeper root cause (6) — "fitted coal rungs own the $40–150 region the
  measured corpus assigns to the CC top belt and `CT_FAST`" — is CLOSED.** On
  the current keeper's own fleet (no LP), `COAL` is **12.7–18.2 %** of the
  marginal set across all hours and **11.1–17.6 %** in that band, against
  pjm-122's **44–79 %** on the `pjm-121` bundle; `CC_REGULAR` + `CT_PEAKER` hold
  **68.4 / 72.6 / 75.5 %** of it and `CT_PEAKER` alone is **60.7 / 65.9 /
  67.1 %** of the tightest net-load decile. The intervening keeper line (CC
  mid-curve belt, net-position cut, loss surface, measured CT heat rates) is the
  plausible cause. It should be retired from `keepers/PJM.json` — a
  promotion-lane edit pjm-138 reports rather than performs.
- **An hour-key correction to pjm-137's shape statistics.** Its measured-side
  loader indexes on Eastern *Prevailing* time against a model and a CAMPD record
  that are both Eastern *Standard*. Levels move ≤ $0.38/MWh and every pjm-137
  conclusion stands, but **no diurnal statistic may be quoted from
  `_pjm137_dominion_ct_congestion.py`** — use `_pjm138_mec_gap_shape.py`'s
  UTC-keyed loader.

**Representation limits, measured at pjm-137 and ISO-wide (not EMAAC-only):**
intra-zone EHV dispersion in 2025 runs **West_APS $18.58, Dominion $16.78,
Central_PA $12.38, AEP_Ohio $9.40, SWMAAC $7.35** against an inter-zonal
DOM–AEP spread of $14.42 — six of seven measurable model zones carry as much
separation inside them as the model is chartered to reproduce between them.
ComEd ($1.93) is the exception, which is why pjm-136 §3's hub-based test read
clean: PJM publishes multiple hubs only inside its two most internally-uniform
zones. The external star node remains lossless while internal wheeling pays a
loss.

### 5.4 MISO — targets C7 COAL_PRB (non-ledgerable), C3b spread compression (instrument-blocked), C3a-2024

1. **Coal minimum-take tonnage data ask**
   (`miso-coal-contract-tonnage-data-ask-2026-07.md`) — **the LP constraint is
   NOT the lever any more; the RHS is.** The constraint itself (contract-period
   tonnage priced by its dual, the named miso-96 successor) stays the only
   identified route to C7 COAL_PRB that doesn't break C1/C5a, but miso-103
   adjudicated its only forward-regenerable RHS candidate — receipts-derived
   tonnage in any window/lag/smoothing — inadmissible (log R² 0.87–0.94 vs
   same-year burn), and miso-104's sourcing pass found **no** ex-ante
   contractual series at plant grain across the 39-plant target set for
   2023–2025. Do NOT charter the constraint until a source clears that ask's
   §4; do NOT re-test any receipts variant. Bounded next step is the ask's §8
   Form 580 count, not a solve.
2. **Outage-grain data ask** (`miso-outage-grain-data-ask-2026-07.md`) — the
   C3b driver (~10 GW 2025 summer under-derate) is instrument-blocked; the
   lever is data intake at unit/fuel grain, not a model change.
3. ~~**DA virtual depth** (`pjm_da_virtual_bids` form, own derivation).~~
   **CLOSED 2026-07-29 (miso-105): REFUSED ex-ante, no solve** — and refused on
   the *opposite* evidence from NYISO's. MISO **does** publish the submitted
   priced curve (`bids_cb`, its FERC-Order-719 masked archive,
   `docs.misoenergy.org/marketreports/YYYYMMDD_bids_cb.zip`, ~90-day lag,
   2023-01-01→2026-01-01 and 404 on every holdout year), its incremental ladder
   semantics were **identified from the file** (99.36 % reproduction of the
   published cleared MW vs 93.49 % cumulative), and the mechanism was measured
   across all 26,304 training hours. Three measured grounds: (a) **premise
   false** — summer-peak net cleared virtual **+1.09/+2.47/−0.34 GW** against
   PJM's **+7–11 GW**, negative in 2025 (the year C3b fails), and −158/+1,336/−62
   MW in the RT>$300 tail; MISO's book is 2.7× PJM's as a share of load *gross*
   (15.8/14.5 % vs 5.9/5.6 %) and ≈0 *net* — the IMM's own convergence/congestion
   instrument, 1,694 MW/h of it explicitly energy-neutral **matched** pairs;
   (b) **immaterial where admissible** — the peak-minus-night net differential
   priced at the keeper's own stack slope buys **+$0.75/+$0.72/+$0.27** of
   diurnal spread against a $14.6/$15.9/$20.5 gap = **5.1/4.5/1.3 %**, shrinking
   as the miss grows; (c) **the material channel is inadmissible** — the curve's
   crossing price λ0 reproduces the price its own book cleared at to
   $0.09/$1.80/$0.17, and at 0.93/0.93/0.69 GW per $/MWh against the model
   stack's 1.85/1.79/1.56 GW/$ it would supply **31–34 % of every hour's price
   displacement and ~63 % at the steepest 2025 summer ventile**. Evidence:
   `results/calibration/FINDING-miso105-da-virtual-attractor-2026-07-29.md`.
   Do not re-open on this data; the DO-NOT-REDO list is that finding's §10.
4. **`measured_ct_heat_rates`** — audit-grade.
5. **`dual_fuel_switching`** — winter-event pricing candidate (Elliott-class),
   untested in MISO.
6. **`hydro_budget_nameplate_aware`** + the `NG: PS` pin audit — **CLOSED
   2026-07-30 across two sessions: the pin defect was confirmed (miso-108), the
   LEVEL was fixed (miso-109), and the mechanism is then `I` — provably INERT at
   MISO.** Audit: MISO's keeper ran `hydro_eia930_monthly=True`, pinning the
   monthly level to EIA-930 `NG: WAT`, while `data/hydro.py` builds the LP units
   from EIA-923 `HY` only — and MISO files **no `NG: PS` column**, so its
   `NG: WAT` carries pumped-storage discharge. Proof: `NG: WAT` exceeds MISO's
   entire 2,478 MW conventional-hydro nameplate in 332–827 h/yr (peak **+1,486
   MW**, 2024) against a **2,417 MW** PS fleet (Ludington 1,979 / Taum Sauk 408
   / Degray 30), with **zero** negative-`WAT` hours, so the contamination is
   one-way gross discharge (923 PS net is −0.7 to −1.0 TWh/yr, the opposite
   sign). Gap vs the 923 `HY` budget: **+1.190 TWh / +13.5 %** (2023),
   **+1.669 TWh / +18.5 %** (2024). **2025 is not quotable** — its 923 filing is
   an early release with 14 plants vs 165, so the naive +918 % is a source
   coverage artifact. Fix (miso-109): the level now comes from EIA-923 `HY`
   directly, so level and units are the same population — the `NG: WAT` pin is
   refused for any BA in `constants.EIA930_PS_FOLDED_INTO_WAT`. **No
   reconciliation factor** was used: none is identifiable from the source data
   (MISO's conventional share of `NG: WAT` drifts 0.9937 → 0.8442 over 2019–2024
   and the monthly gap changes sign by month in 4 of 5 complete years), so the
   "rescale the 930 shape to the 923 level" alternative is refused on measured
   evidence, not preference. **Then the mechanism itself:** with no level
   *target* there is nothing for the nameplate-aware allocator to re-distribute,
   so the budgets are byte-identical with it on and off in all three years
   (L1 = 0.000 GWh) — `U` → **`I`**, adjudicated without a solve. On the
   *contaminated* level it had moved 259 / 454 / 171 GWh, i.e. its entire
   apparent MISO signal was the allocator shuffling PS contamination off
   plant-months pushed above their own nameplate×hours ceiling. Evidence:
   `results/calibration/FINDING-miso108-hydro-ps-pin-audit-2026-07-30.md`,
   `results/calibration/FINDING-miso109-hydro-level-923hy-2026-07-30.md`,
   probe `scripts/probes/_miso109_hydro_level_audit.py`.
   **FORECAST HALF CLOSED 2026-07-31 (miso-110)** — miso-109 fixed only the
   *backcast* level and left the forward analogue WARNING-only. The forecast
   level was the mean of that same PS-inclusive `NG: WAT` series over
   `HYDRO_CLIMATOLOGY_YEARS`, so it was contaminated exactly as each year was;
   it now comes from `data/hydro.climatological_monthly_hydro_923` (EIA-923
   `HY`, coverage-gated), same 12-vector contract, same window constant, same
   wet/dry lever, still no scale factor. MISO forward level **10.244 →
   9.3116 TWh**. Verification is **no-LP** (the level is a 12-vector) and no
   solve was spent: MISO equals the gated 923 mean exactly, all five
   non-registry ISOs are byte-identical across dry/normal/wet, and the
   nyiso-forecast-2035 census-collapse guard is re-asserted at 2026 and 2035.
   **Do not requote the naive climatology delta (+10.0 %) as the fold** — it
   mixes the fold with a WINDOW MISMATCH (923 realises 2021–2024, 930 realises
   2021+2023–2025); the fold numbers remain +13.5 % / +18.5 %. CAISO is the
   control that proves the trap: +15.5 % naive, yet clean on all three
   signatures. `HYDRO_CLIMATOLOGY_YEARS` deliberately **not** extended — the
   2022 hole is an extract-build gap in the two wide per-BA hourly parquets
   (7 and 9 rows vs 8760) while the per-year source files are complete, so the
   remedy is a data-intake rebuild, not a window move (rule 23). Evidence:
   `results/calibration/FINDING-miso110-forecast-hydro-level-923hy-2026-07-31.md`,
   probe `scripts/probes/_miso110_forward_level_audit.py`.

### 5.5 NYISO — target: C3c (sole blocker, roof-blocked)

The J/K-commitment and reserve-tier routes are closed IN FULL (nyiso-83/84);
the tail is blocked by an SRMC roof (~$258 mainland). nyiso-92 dated the
actual RT tail: it is **summer** (2025 Jun 23–25 alone = 18 of 42 h; the
Jan-2024 storm produced zero >$300 hours), so the winter-fuel lane caps out
at ~4–5 h/yr and the queue stays offer/DA-side.

**THE C3c QUEUE IS NOW EMPTY (2026-07-29, nyiso-96/97).** Every candidate is
adjudicated: items 1/1b closed ex-ante on identification (nyiso-94/95), item 2
characterised and item 3 tested by nyiso-96 (verdict commitment/obligation, not
start economics; the amortization arm adjudicated R on rule 1, then
owner-promoted to keeper 2026-07-29 for its C1 PASS with the CT_PEAKER trade on
the record), and the last surviving candidate — **SCUC load-pocket security
commitment + BPCG (NYC/LI sub-zonal)** — closed **ex-ante, no solve** by
nyiso-97: the owner authorized sub-zonal scoping data-first, and identification
failed on *content*, not only access (the as-enforced AORR is MyNYISO-walled;
the public 2008-vintage Appendix B carries no derivable NYC parameter — every
Con Ed in-city commitment row is condition-triggered on TO contingency analysis
with parameters in unpublished SO procedures). **NYISO C3c is recorded as a
DIAGNOSED, UNCLOSED structural limitation of the five-zone representation**
(`docs/FINDING-nyiso97-load-pocket-identification-2026-07-29.md`, re-open
conditions §5). Remaining live NYISO work is the dispatch-matching lane (items
7–10) and the D-2 hygiene item 6; item 4 stays blocked on its joint-lever
condition.

1. ~~**DA virtual depth / DA demand formation** (`pjm_da_virtual_bids` form,
   NYISO derivation).~~ **CLOSED 2026-07-28 (nyiso-94): REFUSED ex-ante, no
   solve.** PJM's lever is admissible because `hrl_da_incs_decs` is the
   **submitted** curve; NYISO publishes no submitted-curve equivalent. Four
   independent blockers: (a) P-59 `zonalBidLoad` carries **no price axis** — one
   MW per zone-hour, so `net(λ)` needs an assumed price distribution = a fitted
   scalar (rule 21); (b) those columns are **cleared, not submitted** — they
   reproduce the IMM's published cleared MW/h to within 1–2 MW (rule 13), and
   the priced P-27 masked archive cannot separate virtual from physical
   price-capped load; (c) the **premise is false here** — net virtual is
   *negative* in the mean hour (−230/−186/−277 MW) and only +580/+293/+917 MW
   in the measured tail vs PJM's +7–11 GW, with NYISO's whole DA book ~0.85 GW
   *below* RT load (IMM: DA net scheduled load ≈96 % of actual peak load);
   (d) **roof-blocked** — all five mainland zones share one max dual
   (149.9/194.5/255.1), 0 h >$258, zero load-shed slack, and every model >$300
   hour is Long Island. **Successor lever identified — see item 1b.**
   Evidence: `docs/FINDING-nyiso94-da-virtual-not-identifiable-2026-07-28.md`.
1b. ~~**TSA (Thunderstorm Alert) downstate transfer derate.**~~ **CLOSED
   2026-07-28 (nyiso-95): REFUSED ex-ante, no solve.** The event set was never
   the problem — and two premises in the original queue entry were wrong, both
   in the model's favour. (i) A TSA history **does** exist in-repo: MIS **P-35
   Real-Time Events**, intaken 2026-07-10 under owner authorization, clean
   datatype `nyiso-operating-events` (`event_type=thunderstorm_alert`);
   reconstructed windows 32/30/18 spans = 187/272/477 h, h13–21 share 61/55/42 %,
   May–Sep 75/90/97 % — independently corroborating the IMM's stated window.
   (ii) The model **already** represents TSA's one published, quantified
   consequence: the LRR `tsa_reduced_to_zero` rule feeds
   `derive_nyiso_reserve_requirements_hourly.py::build_tsa_windows` →
   `nyiso_dynamic_reserve_requirements`, **armed on the nyiso-92 keeper**.
   What is unidentifiable is the **magnitude**. (a) It is **not in the published
   limits**: a declaration-instant event study on MIS P-32 across all 18
   interfaces (83 pooled starts) gives **exactly +0.0 MW** on SPR/DUN-SOUTH and
   TOTAL EAST (0 % of events |Δ|>100 MW) and **−23.9 MW** on UPNY CONED (median
   exactly 0.0 every year) — against a feed that resolves 835–1,565 MW
   hour-over-hour steps, so the null is well-powered. (b) The SOM's "1–2 GW" is
   defined *"relative to day-ahead scheduled levels"* — a range, not a rating;
   selecting a point inside it and scoring it on C3c **is** the fitted scalar
   (rules 21/5). (c) It sits **off our boundary** — the constraint carrying 71 %
   of July-2025 TSA uplift is the **Lovett-Buchanan 345 kV** line under
   multi-contingency **CE40**, which the IMM explicitly distinguishes from the
   UPNY-Con Ed interface; it is one of six parallel paths our five-zone network
   collapses into one link (rule 14's named misalignment clause), and
   reconciling it needs ratings/OTDFs NYISO does not publish. (d) Even the IMM
   has **no magnitude model** — Appendix III.J predicts *P(occurrence)* only.
   The one real measured signal (DiD flow response at onset: UPNY CONED
   −57/−412/−326 MW, SPR/DUN-SOUTH −36/−330/−279 MW, CENTRAL EAST placebo n.s.)
   is a **validation target, never an input** (rule 13) — and at ~280–410 MW it
   is ~¼ of the IMM's low end, confirming the 1–2 GW is mostly the **DA-vs-RT
   schedule gap**, which has no analogue in a formulation with no DA/RT split.
   Evidence: `docs/FINDING-nyiso95-tsa-derate-not-identifiable-2026-07-28.md`.
2. ~~**CT start-frequency lane** (nyiso-89 successor).~~ **CLOSED 2026-07-29
   (nyiso-96 characterisation + nyiso-97 identification).** The
   characterisation chose the commitment/obligation family over start
   economics (below-SRMC energy spread FLAT; 82–88 % of missing online-hours
   priced below the plant's own SRMC; run lengths already right — start COUNT
   is the defect), every commitment-side candidate is adjudicated
   (nyiso-83/84/90/91), and the surviving load-pocket candidate died on
   identification (nyiso-97). The defect is carried on the nyiso-96 keeper
   attestation as an owner-accepted misrepresentation (`_open_items (0)`).
3. ~~**`tranche_startup_amortization`**~~ **TESTED 2026-07-29 (nyiso-96,
   registered A/B): adjudicated R on rule 1 (C1 flips to PASS but CT_PEAKER
   degrades 27–39 % and C3c is bit-unchanged), then OWNER-PROMOTED to keeper
   the same day for the C1 PASS with the trade on the record (cell K;
   keeper `2026-07-29-nyiso-96-ctamort`). Do not re-test; do not read the
   cell K as a structural endorsement — the finding's §5 adjudication
   stands.**
4. **`nyiso_iroquois_winter_spread` re-arm** — decisive winter fix, but ONLY
   jointly with a summer scarcity lever (its construction conserves the annual
   spread; re-arming alone just moves the miss to summer — adjudicated).
5. ~~**`unit_outage_short_windows`** — derive for NYISO; cheap grain test.~~
   **CLOSED 2026-07-28 (nyiso-93): INERT ex-ante, no solve.** The detector is
   coal-only and NYISO has no coal — 0 coal unit-years in NY+NJ CAMPD 2023-25
   (last NY coal MWh: Somerset/Kintigh 2020), 0.0 MW COAL `plant_group` in the
   model fleet; both extracts derive to 0 rows and both overlays return empty
   dicts. A gas-CC scope extension is the only path to a binding window here
   and needs its own charter (layup confound).
   `docs/FINDING-nyiso93-unit-availability-windows-inert-2026-07-28.md`.
6. **`st_gas_mustrun_p25_level`** — re-ground the in-city ST_GAS persistent
   bases on measured levels (D-2 ST_GAS 31% forced in 2024).

Dispatch-matching lane (hourly r, opened by the nyiso-92 charter; the hydro
capability envelope/floor pair is now the keeper — cells K above):

7. ~~**`nuclear_unit_availability`** (NYISO derivation).~~ **TESTED 2026-07-29
   (nyiso-98, registered A/B): all gates PASS — cell K, OWNER-PROMOTED to
   keeper `2026-07-29-nyiso-98-nucavail` the same day.**
   **The queue entry's own premise was wrong.** "r_day drops 0.84 → 0.50/0.51
   in 2024–25" is scored against EIA-930 `NYIS` `NG: NUC`, which posts exactly
   0.0 MW in contiguous blocks (1,179 h 2023 / 380 h 2024 / 117 h 2025 — zeros
   in the source parquet, not NaN). Falsified against NRC on **all 81 gap days,
   zero survivors**: every one has ≥1 NY reactor at 100 % licensed thermal
   power. Gap-masked the ordering **inverts** — 0.446/0.833/0.534, so **2023 is
   the worst year** and the "2024–25 drop" does not exist as described. (Same
   artifact: nyiso-92's 2023 nuclear level reads +14.5 % over-produced; clean
   it is −2.1 %.) Target re-based onto gap-clean r_day in the pre-registration
   **before** the arm was built. The PJM failure mode does **not** repeat, for
   the pre-registered reason: PJM's target was the *level at near-full pool
   days* (what the 923 anchor moves), NYISO's is *within-month timing* (what it
   preserves). Build-time gates: G1 raw-NRC lift **+0.304** (≥ +0.10), G2
   reconciled retention **104 %** (≥ 70 %; PJM's was negative), G3 max annual
   |ΔTWh| **0.14 %** (< 0.5 %). In-solve: gap-clean r_day **0.446/0.833/0.534 →
   0.885/0.960/0.917**, r_hr 0.418/0.819/0.502 → 0.834/0.941/0.836, every
   criterion verdict identical to the same-HEAD zero-delta control. Reported
   adverse (rule 14, not patched): 2023 `CC_REGULAR` −2.76 → −2.79 of ±2.94,
   in band. Zero fitted scalars.
   `docs/FINDING-nyiso98-nuclear-availability-2026-07-29.md`.
8. **`hydro_ror_split` NYISO classifier review** — blocked on answering the
   Robert Moses Niagara hybrid label (Run-of-river/Peaking, 52% of fleet MW)
   from the treaty scenic-flow schedule; never arm on the CAISO-reviewed rule
   alone.
9. ~~**Import hourly shape** (nyiso-86 §3): r_hr 0.45–0.61.~~ **CLOSED
   2026-07-29 (nyiso-99): REFUSED ex-ante, no solve — an attributed C3c
   symptom, not an import lever.** Unlike item 7, **the queue's premise
   survived the audit**: the nyiso-98 falsification was re-run on this target
   and *cleared* it. EIA-930 `NYIS` `Total interchange` carries **0 / 6 / 14**
   suspect hours (vs `NG: NUC`'s 1,179 / 380 / 117), all falsified against the
   independent NYISO MIS **P-32** external schedules (which validate at hourly
   r 0.910/0.908/0.882 on the clean hours); gap-masking leaves the statistic
   **bit-unchanged** (r_hr 0.598/0.624/0.454 → 0.598/0.624/0.458) and scoring
   against P-32 instead reproduces it (0.612/0.611/0.495). `NG: WAT` is clean
   too (0/1/1); `NG: OIL`'s many zeros are *confirmed* genuine by P-63 (3,074 /
   6,285 / 7,343) and its weak instrument agreement is the dual-fuel recording
   basis — item 10's territory.
   **The defect is real and it is not the seam's.** The import node tracks the
   spread *it is shown* at r = **+0.673 / +0.686 / +0.772**, so
   `inject_nyiso_import_hub_prices` is faithful; but that spread is
   phase-inverted against the real one (r = **−0.401 / −0.236 / −0.600**; model
   peaks h21/h02/h22 vs real h17/h16/h17) for a purely arithmetic reason with
   one bad term. The seam side is measured and correct (neighbor DA LMP, hod
   swing 19.8/24.1/32.1 — it *is* reality); NYISO's **internal** price swing is
   12.95/13.17/19.75 against a real 22.45/25.13/43.27, a ratio of
   **0.58/0.52/0.46**. Subtracting a correctly-peaked seam price from a
   too-flat internal price drives the spread to its **minimum** at the peak
   (model spread at the real peak hour −0.1/+1.8/+5.3 $/MWh vs real
   +5.6/+9.7/+27.0), so the LP stops importing in the hour NY imports most and
   buys its reconciled monthly quota overnight. **That deficit is C3c.**
   Refused on three grounds: identification (the only series saying "import
   more at h17" is the scored outcome — rule 13), sign (nyiso-86 recorded that
   forcing peak imports *depresses* peak duals, moving C3c the wrong way —
   rule-14-backwards), and rule 19 (the phenomenon already has a mechanism).
   **Reported, not armed:** the 4,350 MW `NYISO_simultaneous_import` cap is a
   hand-set estimate measurement contradicts (model import tops out at exactly
   4,350 MW, never above it in any hour of any year, and sits on the cap in
   548/689/177 h/yr, vs a measured schedule exceeding it in 287/314/145 h at
   max 5,929 MW and published P-32 limits summing to a minimum of
   5,805/6,090/6,680 MW) — a live rule-14 reconcile item needing a *reconciled*
   identification (the P-32 sum is parallel paths our five-zone network
   collapses, rule 14's misalignment clause) and its own charter; and 2,970 MW
   of the 6,580 MW ladder (45 %) carries a per-year *constant* price with no
   hourly signal, five of seven rungs sitting at their own cap or at zero in
   most hours. Neither can be the lever: a finer ladder or a higher cap cannot
   fix a spread that peaks at the wrong hour. *(Correcting this entry's first
   draft: `import_scarcity` is NOT unreachable — 1.182 TWh in 2023, at its
   2,230 MW cap in 27 h; the hourly repricer reorders the merit list, clearing
   it while `eastern_mid` is below cap in 1,209 h.)*
   Evidence: `docs/FINDING-nyiso99-import-shape-attributed-to-c3c-2026-07-29.md`.
9b. **EIA-930 zero-dropout repair on metered demand** — the by-product of item
   9's audit, and the one thing nyiso-99 armed. Extending the falsification
   from benchmarks to **inputs** found the same exactly-0.0 artifact in `NYIS`
   `Demand`: 2024 h403/6760/6761 and 2025 h354/355, each bracketed by ~17–22 GW
   and each reproduced 1:1 in the keeper's solved sidecar as **0 MW of served
   load**. `_screen_demand_dropouts` is the low-side twin of the existing
   `_screen_demand_spikes`, zero DOF, demand-only (ERCO's interchange
   legitimately reads 0.0 on idle ties), byte-identical on 16 of 18 ISO-years.
9c. ~~**G-J locality Bulk Power Transmission Limit on its own boundary** — the
   follow-on nyiso-100 chartered when it retired the mis-attributed external
   scalar. The limit is real, published every capability year (3,425 / 3,425 /
   4,350 / 4,500 MW for 2022/23–2025/26) and represented nowhere; it belongs in
   the `nyiso_nyc_lcr_tsl` / `nyiso_li_lcr_tsl` family.~~ **CLOSED 2026-07-30
   (nyiso-101): REFUSED ex-ante, no solve, no flag.** The premise survives — the
   limit *is* real and *is* unrepresented — but it has **no representable
   boundary**. `Capital_Hudson` = F+G **straddles** the G-J locality (G inside,
   F outside), so the mechanical cutset test returns no valid import-direction
   edge: two links have a straddling end, `Lower_Hudson->NYC` is *interior* to
   G-J (capping it is category-wrong, and it already hosts the NYC 2,875 MW
   cap), and `NYC->Long_Island` is an edge only *reversed* and already carries
   the LI cap in the same window. Two of the four real boundary legs are not LP
   quantities: the **F→G cutset** (interior to `Capital_Hudson`) and the
   **external ties landing in Zone G** (PJM Ramapo ~1,000 MW + ISO-NE ~600 MW,
   lumped into the 1,600 MW `Capital_Hudson` node link whose F/G split
   `interchange/spec.py` itself calls "a modelling choice inside the topology").
   Leg 2 is decisive — the endogenous subset-sum workaround dissolves leg 1 but
   not leg 2. And unlike its two accepted siblings there is **no posted G-J
   series in principle**: P-32 carries seven internal interfaces, none G-J, so
   the admissibility evidence the NYC cap has (2,875 MW sitting at the p95 of
   `SPR/DUN-SOUTH` in-window flow, exceeded 1.8/5.0/6.9 % of HB14-21 hours) is
   unavailable — placed on `UPNY CONED` the G-J limit would sit at pctile
   74.1/90.6/95.6 and be exceeded 25.9/9.4/4.4 %. A static reconciled cap is
   *unidentified*: the translation needs `gen_G`, bounded only by [0, Zone-G
   capability], pinning the cap to an interval 105–137 % as wide as the limit.
   Refused **against its own incentive** — a binding G-J limit would raise
   downstate peak prices, the direction C3c wants (rule 1, both directions).
   **Re-opens only behind a `Capital_Hudson` → Zone-F/Zone-G topology split**,
   which needs its own owner charter (ERCOT West/Panhandle class, CLOSED) — not
   a lever-queue entry, and never as a mechanism flag.
   Evidence: `docs/FINDING-nyiso101-gj-locality-boundary-2026-07-30.md`.
10. **Keeper-lineage cleanup:** drop `dual_fuel_oil_reattribution` from the
    NYISO recipe metas (CLI already pins it NEISO-only; zero dispatch delta,
    removes a known recording-basis artifact from the sidecars).

### 5.6 NEISO — target: C3c (ledgered; FRONTIER DECLARED — charter required first)

Frontier discipline: every named admissible mechanism in the winter/summer
scarcity family is already on record. Anything below needs its **own new
charter with a new measured identification** before a solve:

1. **DA-bid offer formation / DA depth charter** (`pjm_da_virtual_bids` form)
   — the named "new identification" class in the frontier note (oil-parity /
   import / DA-bid); NEISO publishes DA cleared/bid data to derive from.
2. **Import-side scarcity identification** (HQ/NB tie behavior in tight
   hours) — second named class.
3. **`measured_ct_heat_rates`** — audit-grade, no charter needed (input
   accuracy, not a scarcity mechanism).
4. **`hydro_budget_nameplate_aware`** + `NG: PS` pin audit — cheap, flagged.
5. **STEP 3 seam disposition** (owner decision pending): carry the
   layup-vs-outage seam explicitly (recommendation (b) on record).

### 5.7 Cross-cutting audits (not ISO levers)

- Post-guard re-derivation sweep of outage-derived artifacts, all six ISOs
  (flagged in governance.md 2026-07-26, unaudited).
- `NG: PS` hydro-pin audit — **ALL SIX ISOs NOW SCREENED** (miso-108 audited
  MISO; miso-109 fixed it and ran the same three-signature screen across the
  rest, `scripts/probes/_miso109_hydro_level_audit.py`). The check is
  mechanical and portable: no `NG: PS` column → `NG: WAT` exceeding
  conventional-hydro nameplate → zero negative-`WAT` hours (a series that
  netted pumping would go negative). Rule 25 — a screen result is evidence for
  that ISO's own lane, never a transferred verdict.

  | ISO | `NG: PS` col | h/yr above conv. nameplate | neg. `WAT` h | 930 vs 923 `HY` | verdict |
  |------|---|---|---|---|---|
  | ERCOT | no | 0 | 0 | — | clean (no PS fleet) |
  | CAISO | no | **0** | 1–121 | — | clean; negatives show pumping IS netted |
  | PJM | no | **1,249–1,612** | 0 | **+52.9 % … +79.6 %** | **DEFECT, largest — own lane owes the fix** |
  | MISO | no | 332–826 | 0 | +13.5 % / +18.5 % | **DEFECT — FIXED (miso-109)** |
  | NYISO | no | 0–33 (≤0.007 TWh) | 0 | −4 % … −6 % | clean; the bias is the opposite sign |
  | NEISO | **yes** (from Nov 2024) | 63–276, **0 in 2025** | 0–1 | +2.7 % … +10.1 % | **TIME SPLIT** — pre-Nov-2024 vintages only |

  Open follow-ons: **PJM** (a live defect on a live keeper — the fix is the
  same one-line registry entry plus its own A/B and re-gate) and **NEISO**
  (needs a per-window treatment, not a switch, since its own filing changes
  mid-series). Standing hazard for every listed ISO: the hydro dispatch
  *envelope* and *min-flow floor* are also built from hourly `NG: WAT` and
  inherit the same contamination — both are default-off and off in the affected
  keepers today, so nothing is stacked, but arming either needs its own source
  fix first (EIA-923 is monthly and offers no hourly substitute).
- `thermal_tranches_<ISO>.csv` provenance re-derivation (blocked at HEAD,
  miso-95).
- Registry hygiene fixes from §4.6 (dangling `--ramp-limits`, inert-default
  flags).
- Forecast-lane inheritance review: for each keeper-only `BF` mechanism,
  decide arm-in-forecast vs G4 forward-analogue vs backcast-only, and record
  it in the row's `fc` field (start: CAISO `capacity_deliverability_limits`
  part (a)).

## 6. Glossary

The full grouped glossary (≈80 terms: LP/duals, gates C1–C8 and
D-diagnostics, ORDC/RCPF/ASDC, commitment bridges and floor limbs, offer
tranches and passthrough sigmoids, EFOR/WEFOR, TTC/GTC/seams, ELCC/PRM/
net-CONE/VRR, RPS/REC/ACP, CAMPD/CEMS/eGRID/EIA-923/930/860, …) is rendered
with search on the matrix page: `docs/codebase-site/mechanism-matrix.html#glossary`.
It is maintained there (single source); this doc deliberately does not
duplicate it.

---

*Maintenance: this doc changes when the protocol or queues change; the matrix
data file changes every time a verdict lands. If they disagree, the data file
(+ the calibration log it cites) wins — fix this doc.*
