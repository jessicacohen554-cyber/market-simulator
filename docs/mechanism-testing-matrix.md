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

> **That keeper list is the 2026-07-27 BUILD SNAPSHOT — a historical record of
> what the matrix was first audited against, not the current keeper set.** All
> six ISOs have promoted since. The LIVE keeper set is the `keepers:` object in
> `docs/codebase-site/data/mechanism-matrix.js`, which the promoting session
> re-stamps under rule 28; read it there, never from this paragraph. (Header
> hygiene, FFR-3B 2026-08-02 — audit FR-21 bookkeeping desync. No cell verdict
> was touched.)

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
   extracts; holdout frozen; MISO/PJM/NYISO re-tune required). The downstream
   half is **CLOSED as of xiso-2 (2026-08-02)**: 5/6 committed extracts
   re-derive byte-identically at HEAD, MISO's mismatch is 2022-only and
   source-data-attributed, and **no ISO's keeper consumes a stale
   outage-derived artifact** (§5.7).
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

### 5.1 ERCOT — NOT-YET (keeper `2026-08-03-ercot158-pool-arm`, C6 PASSES; **keeper re-stamped at ercot-158** — the ERCOT-88 fast-start pool ARMED, `ercot_faststart_pool_offer` cell `K`, OWNER-PROMOTED on the standing standard after the pre-registered A/B measured it ENGAGED-but-INERT at the missed tail: the 91 missed 2023 >$300 hours are bit-identical between arms, so the 2023 tail is confirmed a COMMITMENT-STATE gap on the un-repriced CC offline block — the same object ERCOT-155 re-pointed item 7b at, now measured from the offline side; docs/PRECOMMIT-ercot158-faststart-pool-arm-2026-08-03.md); **LIVE QUEUE AS OF ERCOT-158 (2026-08-03): item 9 (the named successor — UNCHARTERED, owner authorization required), item 7 (data-intake first) and item 8 (data-intake first) — every other named item is struck. ERCOT-155 measured item 7b's dispersion object and RE-POINTED it: it is a COMMITMENT-STATE defect, not an offer-slope or fleet-composition one, the offer-dispersion arm is REFUSED (rules 1/13/20), and the "flat ~25 GW at 1.6 $/MWh per GW" framing is CORRECTED (item 7c) — do not quote it forward.** Open gates unchanged in kind: C3a 2023-only (−32.6%; 2024 +1.6%, 2025 −8.3% away from the edge), C3b 2023-only (0.607), C3c (58/20/0 vs 181/53/31), C7 2023-lignite cv-leg (r 0.888, cv 0.334); ~~C7 lignite, coal seasonal split~~ CLOSED; ~~items 4+5~~ EXECUTED at ERCOT-145; ~~item 6~~ CLOSED `I` at ERCOT-146; the items-5/6 reopen route REFUSED at Phase 0 by ERCOT-147 — data-intake first (item 8); ERCOT-148 (owner-directed availability audit) promoted the DAM coal event-window cap; ERCOT-149 (the §6.1 successor / owner ruling #7) measured the GAS-side collision MATERIAL, adjudicated it a defect on the gas fleet's own conduct, and was OWNER-PROMOTED (`ercot_dam_availability_gas_event_cap` cell `K`); **ercot-150 (2026-08-02, the nyiso-109 §7 cross-ISO transfer adjudicated at ERCOT per rule 25) resolved the gas-offer margin anchor PER ZONE (`gas_offer_margin_zonal_anchor` cell `K`) and was OWNER-PROMOTED under the standing in-session instruction**: ERCOT's convention is a capacity-weighted mean-zero spread PLUS a flat measured EP level correction, the anchors were identified on the keeper reconstruction's own resolved fuel_prices (the West net-load floor lift cut the West leg ~5× before anything was pushed), all five construction gates passed incl. zonal K3 liveness (max zone |ΔLMP| 0.356/0.304/0.319 $/MWh — ERCOT prices the LEVEL side its convention carries while the mean-zero spread half stays price-inert on its coupled topology, West decoupling only 6/17/2 h/yr), P1/P2/P3/P5 passed, and P4 fired on a template artifact (the keeper itself carries slack 3478.9/1114.6/0.0 MWh; true arm delta +0.97/+0.91/0.00 MWh ≈ +0.03%). The availability lane is measured-precedence-correct on COAL AND GAS and the gas offer surface is now zone-grain-identified; the un-masked residuals are the CC econ-band under-dispatch (ERCOT-138/139 object: Jack County/Guadalupe now under) and the coal LOADING-CONDUCT under-run (ERCOT-126 object); OPEN owner rulings #9 (deriver `_site()` cross-train collapse + gas crosswalk partial acceptance — the root-cause derive lane; its re-derive would also re-trigger the zone-anchor table per rule 23) and #10 (pin remove-direction over-removal)

**RULE-28(c) COLUMN CLOSED (ercot-156, 2026-08-03; no LP, no solve, keeper
UNCHANGED, no queue item touched).** The ERCOT census debt — 60 `ercot_*`
fields absent from the matrix, 7 prose-only, **31 armed on the keeper with no
cell anywhere** — is **0/0/0**: all 67 closed as literal sub-scalar
registrations on 14 existing family rows' `def`s (the nyiso-114 escape-hatch
template), ratchet baseline ERCOT 61 → 0, `matrix_gap_census` ERCOT cell
`O → K`. **Zero new rows, zero verdicts minted** — no live-but-invisible lever
surfaced (every armed field is a leg of an already-adjudicated family); the
only verdict text added transcribes recorded adjudications
(ercot83 posture probe `I`, ERCOT-89 shoulder-span rejection, ERCOT-118/119
rebasis rejections — closing the gap ERCOT-138 filed — ercot71 noncampd
keeper). The 20 remaining live-but-invisible fields are shared-stem
(cross-ISO) and filed for a cross-ISO hygiene lane, not this queue. Evidence:
`results/calibration/FINDING-ercot156-matrix-column-closure-2026-08-03.md`.
The lever queue above is UNCHANGED by this closure.

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
7. **WP-B nodal curtailment layer** — ~~*data-intake first* (station→area
   crosswalk does not exist in-repo)~~, then the under-curtailment gap
   (ERCOT-121). **▶ THE DATA PREREQUISITE IS EXECUTED AT ERCOT-160
   (2026-08-04) — the blocker was never real.** ERCOT *publishes* the
   station→area crosswalk, free and unauthenticated, as **NP4-160-SG
   "Settlement Points List and Electrical Buses Mapping"**
   (`reportTypeId=10008`, in ERCOT's own product catalog); it had simply never
   been fetched. Intaken COMMITTED to `data/raw/ercot-network-model/` (1.2 MB,
   exact published bytes + per-member sha256, ERCOT ToU §5) by
   `scripts/data/fetch_ercot_settlement_point_mapping.py`:
   `Settlement_Points` (19,287 rows) carries `SUBSTATION` →
   `SETTLEMENT_LOAD_ZONE` → `RESOURCE_NODE` → `HUB`, and
   `Resource_Node_to_Unit` (1,624 rows) carries `RESOURCE_NODE` →
   `UNIT_SUBSTATION` + `UNIT_NAME`. **VINTAGE CAVEAT THAT BINDS ANY
   CONSUMER:** MIS retention is ~31 days, so only the CURRENT network-model
   version (published 2026-07-29) is reachable — there is **no 2023–2025
   vintage and there never will be on this path** (which is why it is
   committed, not gitignored). Substation→zone is structural and slow-moving,
   but a node commissioned/retired since the backcast year will not line up:
   **report your own match rate against your target year, never inherit
   ERCOT-160's.** Item 7 is now unblocked on data and can proceed to its
   actual object, the ERCOT-121 under-curtailment gap.
   (`results/calibration/FINDING-ercot160-ct-fullspan-intake-2026-08-04.md` §4.)
7b. ~~**The measured STORAGE evening discharge-offer surface** (ercot-153's
   chartered successor to the diurnal-amplitude decomposition) + its named
   fallback **`measured_ramp_capability`**.~~
   **▶ BOTH CLOSED AT ERCOT-154 (2026-08-03) — NO ARM, NO SOLVE, KEEPER
   UNCHANGED. DO NOT RE-OPEN EITHER.**
   `docs/DIAGNOSIS-ercot154-storage-offer-surface-2026-08-03.md`; probes
   `scripts/probes/ercot154_storage_offer_surface.py`,
   `ercot154_storage_binding_check.py`, `ercot154_ramp_capability_census.py`;
   records `results/calibration/ercot154_storage_offer_surface.json`,
   `ercot154_storage_binding_check.json`,
   `ercot154_ramp_capability_census.json`.
   The storage surface **IS identified** at one rung — p30, absolute $/MWh,
   2025/2024 ratio median **0.969** rel IQR **0.143** over the 14 cells both
   years populate at ≥40 SCED intervals — and the wall's **gas-multiple basis
   is REFUTED** at every rung (median 0.31–0.62 across a ×2.17 gas move). It is
   refused on three *other* measured grounds, none of them "the residual didn't
   move": **(a) representation** — the object is a rising ladder and the LP
   carries one discharge column per storage unit, while the rungs a
   multi-tranche form needs are unidentified (p70 ratio 0.111, p90 degenerate
   at the $5,000 HCAP); **(b) the lever cannot produce the phenomenon** — the
   keeper's matched (month × hour-of-day) evening supply-curve slope is
   **1.557/1.616 $/MWh per GW**, so withholding ALL evening storage buys
   **$1.38/$3.05** against ERCOT-153's **$20–66/MWh** object; **(c) it breaks a
   measured quantity already short** — the arm withholds ~90 % of a fleet
   already **17.7 %** under EIA-930 in 2025 (4,483.3 vs 5,444.8 GWh). Rule 14's
   explicit grain-misalignment exception governs; the incumbent
   `battery_dispatch_adder` $10 stays and stays a residual DOF.
   The fallback is **`I`, inert by wiring**: `measured_ramp_capability` changes
   only `FleetArrays.ramp10`, and an AST census finds all 5 functional read
   sites behind PJM/CAISO/MISO gates with `_ercot_design` /
   `_ercot_multiproduct_design` at zero mentions — a bit-identical A/B (the
   ERCOT-146 outcome, before the solve). ERCOT's deliverable-reserve row is
   already held by the measured RTOLCAP series.
   ~~**THE NAMED SUCCESSOR OBJECT** (unowned, no lever yet): the dispatchable
   stack's price DISPERSION in the mid-merit evening region — ~25 GW of
   thermal headroom priced within 1.6 $/MWh per GW … a successor must bring a
   *slope* mechanism.~~
   **▶ MEASURED AND RE-POINTED AT ERCOT-155 (2026-08-03) — NO ARM, NO SOLVE,
   KEEPER UNCHANGED. The dispersion framing is SUPERSEDED; see item 9.**
7c. **The ERCOT-155 correction to 7b, binding on successors**
   (`docs/DIAGNOSIS-ercot155-evening-dispersion-2026-08-03.md`; probe
   `scripts/probes/ercot155_dispersion_census.py`; record
   `results/calibration/ercot155_dispersion_census.json`).
   - **7b's premise was wrong in two ways.** The evening thermal headroom is
     **15.3–17.5 GW**, not ~25 GW (that figure was annual-max thermal dispatch
     60.4–61.1 GW minus the evening mean 35.3–35.7 GW — a *cross-hour*
     difference, not headroom available in an evening hour), and the stack over
     it is **convex, not flat**: 1.1–1.2 $/MWh per GW for the first ~5 GW,
     7.8–13.4 by 60–90 % of headroom, reaching **$103–116** at the 90 % rung
     before a 38 MW West CT tail (HR 155.17) jumps to $2,797.56. The
     1.557/1.616 figure is a correctly-measured **local** slope at the
     operating point. **Do not quote the "flat 25 GW" framing forward.**
   - **An offer-side dispersion/slope arm is REFUSED** (rules 1/13/20, not on
     fit) — see item 9 for the grounds.
9. **THE NAMED SUCCESSOR (ERCOT-155): the evening object is a COMMITMENT-STATE
   defect, and the lever is an energy-side measured online-capability ceiling.**
   Matrix row `energy_online_capability_cap` (ERCOT `U`). **UNCHARTERED — needs
   owner authorization and its own precommit; it is a structural LP change, not
   a Phase-2 offer arm.**
   - **The measurement.** In the evening ERCOT holds **159–224** thermal
     resources online at **92.0–96.2 % of HSL**, leaving **0.92–2.80 GW** of
     energy headroom, with **128–196** resources / **17.05–22.94 GW** of thermal
     HSL **offline** and absent from the 5-minute stack. The model has
     **53.1–54.4 GW** of available thermal at **65.7–68.0 %** loading =
     **15.3–17.5 GW** of headroom — **5.5–19×** the real market's — all
     dispatchable from zero at marginal cost in any hour, because the LP carries
     no integer commitment. Same MWh from the same classes (C1 16/16, C2 PASS)
     by the wrong route.
   - **Why the offer arm is refused.** The MW it would re-price are MW ERCOT
     keeps **cold**; assigning event-day conduct prices to them is a fitted
     proxy for a missing physical constraint (rule 1, no forward analogue under
     rule 13, no identification source under rule 20). It could not reach the
     object anyway: the measured across-resource spread on the comparable 1 GW
     band is **$2.66–47.43** (SCED) vs **$0.71–2.18** (model) — tens of dollars
     where the C3c tail needs hundreds. On event evenings ERCOT prices
     **24–53 %** of its first marginal GW above \$100; the model prices **none**
     of it above \$75.
   - **The precedent and the instrument.** `results/scarcity.py::
     ercot_rtolcap_supply_cap_mw` already diagnoses the identical defect on the
     **reserve** side ("count every reserve-eligible thermal unit's *full
     installed* headroom … including cold slow-start units a perfect-foresight
     LP leaves idle but still scores as available") and the keeper arms
     `ercot_reserve_supply_cap=True` to fix it. Nothing constrains **energy**.
     The measured series is already committed for all three years in the same
     file: `ercot_<year>_ordc_reserves_hourly.parquet` carries **`rtolhsl`**
     (online HSL, evening mean 58.87/62.64/67.81 GW).
   - **Downstream — one gap, several standing residuals.** C3a-2023 (−32.6 %) is
     ~entirely tail wedge (capped at \$200 the model is within −5.1 %; hours
     >\$200 **63 vs 181**; wedge \$7.21 vs \$18.61/MWh). The **correctly-armed
     and correctly-dated** ECRS mechanism (`ercot_ecrs_conservative_deployment`,
     measured ASPLANNP433 onset 2023 h3839 ≈ June 9–10, published 2024-08-01
     reform at `ERCOT_ECRS_RELEASE_REFORM_HOUR = 5088`) under-delivers because
     withdrawing 1–3 GW from a 15 GW cushion cannot move a dual. ERCOT-153's
     evening-ramp premium and ERCOT-154's \$1.38/\$3.05 storage ceiling are the
     same cushion on other instruments.
   - **Before chartering:** rule 19 reconciliation against the availability lane
     (which models **outages**, not online state) and the commitment bridges
     (which own the **lower** bound) — explicit precedence, never a stacked
     layer; identification from ERCOT's own measured online state only
     (rules 13/20/23); an availability-shaped bound, since the pure-LP
     architecture forbids MIP; and the SCED corpus basis is: **full-year
     delivery-2023** (the ERCOT-157 owner re-upload at `data/raw/ercot/SCED/`,
     315 shards verified complete, all 365 delivery days — this SUPERSEDES the
     earlier "2024/2025 only, NP3-965 OWNER-DECLINED 2026-08-02" clause, which
     went stale when the re-upload landed the next day) plus the 47-day
     2024/2025 event/control sample extracts (validation only).
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
   **▶ THE THREE-PART INTAKE WAS EXECUTED AT ERCOT-160 (2026-08-04): (a) DONE,
   (b) BLOCKED, (c) RESHAPED. The lever STAYS BLOCKED — on (b) alone.**
   (`results/calibration/FINDING-ercot160-ct-fullspan-intake-2026-08-04.md`;
   no LP, no cell, keeper unchanged.)
   - **(a) DONE at 98.7 % of the training span.** The fetcher's day-list scope
     was lifted (`--resource-types` / `--delivery-range` / `--shard-by-month`);
     CT-scoping cuts a delivery day to 15.1 % of its rows (18,816/124,608,
     0.51 MB parquet), which is what makes ~700 days affordable. Delivery
     2024-01-24…2025-12-31 landed CT-only in `data/raw/ercot/SCED-CT/`
     (gitignored + README + SHA256SUMS, the pjm-zonal-lmp precedent) and joins
     the committed all-resource corpus (`data/raw/ercot/SCED/`, delivery
     **2022-12-31…2024-01-09** — note that is a DELIVERY span; its shard
     filenames are PUBLICATION months). **Gap: delivery 2024-01-10…2024-01-23
     (14 days) is UNREACHABLE** — it falls between the corpus end and the MIS
     rolling window's earliest listed publication (2024-03-24 → delivery
     2024-01-24), reported `NOT LISTED` and never interpolated; closing it is
     the owner-declined credentialed archive, and **the gap WIDENS with time**
     as the window rolls. 2026 delivery days were refused live by the rule-22
     guard, not omitted.
   - **(b) BLOCKED — the only thing still blocking the lever.** The licensing
     check ERCOT-147 §4 demanded was run and recorded reproducibly
     (`scripts/probes/ercot160_texas_hub_daily_screen.py`,
     `results/calibration/ercot160_texas_hub_screen.json`). EIA's free NGWU
     spot table carries **Waha/Katy/Agua Dulce/Carthage at ZERO mentions** on a
     real page against Chicago's 6 and Henry Hub's 10 — a row cannot exist at
     zero; the lone "Houston Ship"/"Permian" hits are narrative prose quoting a
     WEEKLY average. ERCOT's own catalog: 5,773 products, 6 mention fuel,
     **none is a price series** (FFSS/RMR/Fuel-Mix/Exceptional-Fuel-Cost); the
     settlement Fuel Index Price is not a data product. **⇒ NGI/Platts/Argus
     only = OWNER LICENSING DECISION**, compounded by the unresolved
     `docs/data-licensing.md` §5 finding. **DO-NOT-REDO:** do not re-screen the
     free EIA/ERCOT paths, and **never substitute Henry Hub** — ERCOT-147 §3's
     confound is precisely that 63–67 % of CT capacity's daily p50 sits below
     its own sheet-HR × HH burn, so a HH stand-in assumes away the object.
   - **(c) RESHAPED — and the charter's sizing was wrong in KIND.** The
     crosswalk's `site` column is not one grain: `CC_REGULAR` holds a site
     prefix (`RIONOG`/`RIONOG_CC1`), `CT_PEAKER` holds the **full resource
     name** (`VICTPORT_CTG01`) — measured **165/165 CT rows match a corpus
     RESOURCE name, 0/165 match a site prefix**. So "165 CT_PEAKER sites, 6
     accepted" counts RESOURCES and the "~150-site hand crosswalk" is not the
     job. Most CT resources (and most CT capacity) **already carry a candidate
     row** — the bulk of the work is ACCEPT/REJECT adjudication, with a small
     industrial-cogen-heavy tail (DOWGEN, FORMOSA) carrying no row at all.
     Both now stand on item 7's newly-intaken published spine (resource →
     substation → load zone, measured 186/191 and 50/50), leaving
     **substation → EIA plant code** as the single judgement step — NP4-160-SG
     carries no EIA identifier. Census:
     `scripts/probes/ercot160_ct_target_population.py`,
     `results/calibration/ercot160_ct_population.{json,csv}`. NOT built this
     session: its only consumer is the lever, which (b) still blocks.

### 5.2 CAISO — **NO failing criterion** (keeper `2026-08-04-caiso164-zonal-loss-surface`, CALIBRATED-WITH-CAVEATS)

> **caiso-164 (2026-08-04) — NEW LANE OPENED AND CLOSED IN ONE SESSION; KEEPER
> PROMOTED to `2026-08-04-caiso164-zonal-loss-surface`.** The CAISO queue was
> EMPTY of never-adjudicated items after caiso-163, so this session opened a new
> lane — and chose it from a MEASUREMENT rather than from caiso-163 §5's named
> hypothesis. Full record:
> `results/calibration/FINDING-caiso164-zonal-loss-surface-2026-08-04.md`;
> prereg `PRECHECK-caiso164-zonal-loss-surface-2026-08-04.md` pushed at
> `eda8ebe8` **before either arm solved**.
>
> **§0, no LP.** CAISO publishes the congestion/loss split directly (`LMP = MCE
> + MCC + MCL`, MCE identical at every node to `0.00e+00`), so the hub basis is
> EXACTLY `dMCC + dMCL`. NP15−ZP26 is **80.2/87.2/81.7 % congestion, 19.8/12.8/
> 18.3 % loss** (+1.176/+1.102/+1.049 of +5.947/+8.576/+5.727 $/MWh). The
> congestion majority is a **FREQUENCY-AND-DIRECTION** miss, not magnitude (freq
> 0.035–0.054× vs magnitude 0.26–0.44×): in the top decile of measured `|dMCC|`
> — **100/100/99.9 % of it S→N** — the pre-arm model separated in **0 of
> 864/879/876 hours** across the whole lag sweep, and its rare separations ran
> 99–100 % N→S, the opposite direction.
>
> **The arm.** `caiso_zonal_loss_surface` (matrix row `zonal_loss_surface`,
> CAISO `U → K`) — the model was LOSSLESS, i.e. carrying the *estimate* that
> losses are zero, so rule 14 `[R-ACCURATE]` governs. Zero free parameters: the
> frozen MISO/PJM estimator on CAISO's own committed DAM component record. Per
> rule 28(d) the PJM `K` / MISO `R` verdicts did **not** fill CAISO's cell.
> **Headline is the sign:** mean NP15−ZP26 −0.0768/−0.1086/−0.0841 →
> **+0.2362/+0.1258/+0.1113** — correct for the first time; separated hours
> 2.7/4.7/3.2 % → **38.0/28.8/27.3 %**; hours NP15 *dearer* 3/0/1 →
> **3,082/2,120/2,108**. Zero criterion flips, no new caveat spent.
>
> **TWO NEW QUEUE FACTS THIS LANE MUST CARRY FORWARD:**
>
> 1. **NEW DATA BLOCKER — CAISO intra-zonal congestion (FINDING §6).** The
>    ~80–87 % congestion majority is NOT reachable from `data/raw`. §0 attributes
>    it to an **intra-SP15** corridor: `LA_BASIN` carries 77–83 TWh of load at a
>    0.11–0.12 belly renewable/load ratio and absorbs the entire
>    ZP26+SP15_rest belly surplus (their own ratios are 2.1–3.5, local surplus in
>    ~2,850 of 2,920 belly hours) through a **never-binding 12,008 MW one-way
>    link**, so no surplus reaches Path 15 and it never binds S→N with a positive
>    dual. Needs CAISO nodal/DLAP LMP components or published intra-SP15 transfer
>    limits; `data/raw/lmp-data/CAISO/` has only the three `TH_*_GEN-APND` hubs
>    hourly (the 22 nodal `DAM_LMP_GRP` zips are single days, fetched to patch a
>    2023 hole). **NOT closable by an adder, haircut or residual-tuned value**
>    (rules 1/13). Joins C3a-2025 (non-public hourly pumped-storage) and
>    C3c-2023/24 (SoCalGas OFO record). **Do not charter an N–S topology lever
>    against this residual** — §0 measured that topology is not where the
>    recoverable component was.
> 2. **The loss surface's two interpolated zones are the same blocker.**
>    `LA_BASIN` and `SDGE` carry `interpolated=True` (they inherit the SP15
>    generation hub's deviation under rule 14's reconciliation clause, since
>    CAISO's DLAP component record is absent). A DLAP intake would close both
>    this and item 1. The three zones carrying the quantity under test (NP15,
>    ZP26, SP15_rest) each have their own measured hub.
>
> **DO-NOT-REDO additions:** `caiso_zonal_loss_surface` is now `K` — do not
> re-test it. Its S4-2023 miss (NP15−SP15_rest −1.2265 → −1.5665, away from the
> measured +2.337, while 2024/2025 move toward) is a **recorded carried caveat**,
> pre-committed in prereg §5 as a measurement rather than a promotion criterion;
> it is not an open lever.


> **Keeper id corrected at caiso-161, re-stamped at caiso-164** — this heading
> had gone stale at `2026-07-31-caiso148-nuclear-availability`, was corrected to
> `2026-08-03-caiso156-meter-screen-b`, and now reads
> `2026-08-04-caiso164-zonal-loss-surface` in step with
> `frontend/data/backcast/keepers/CAISO.json` and the matrix header. (The
> `check_mechanism_matrix.py` stamp guard covers the `.js` header only, so prose
> drift here is invisible to CI — the same class of staleness nyiso-116 fixed.)

> **CAISO MATRIX COLUMN CLOSED — caiso-161 (2026-08-03), no LP, no solve, keeper
> UNCHANGED.** `mechanism_matrix_gap_sweep.py --iso CAISO` went **31 absent / 2
> prose-only / 18 armed-on-the-keeper-with-no-cell → 0 / 0 / 0**; ratchet baseline
> `mechanism-matrix-gaps.json` CAISO **31 → 0** with no other ISO's list growing.
> All 33 fields closed as **literal sub-scalar registrations** on 10 existing
> family rows plus `lcr_tsl_published`; **zero new rows, zero mechanism verdicts**
> (rule 28(d)) — the only cell mints are the audit row `matrix_gap_census`
> CAISO `O → K` and `lcr_tsl_published` CAISO `. → U`. Full record:
> `results/calibration/FINDING-caiso161-matrix-column-closure-2026-08-03.md`.
>
> **Two findings this queue must carry forward:**
>
> 1. **Six keeper fields are armed-looking but PROVABLY INERT** — non-default in
>    all 19 CAISO bundles' `run_config.json` yet unreadable by any code path in
>    the keeper's configuration. `caiso_gas_floor_frac` 0.80 (only read inside
>    `if caiso_gas_commitment_floor:`, which is `False`);
>    `caiso_solar_deliverability_k` 0.15 + `caiso_solar_deliverability_floor` 0.50
>    (both derate call sites skip when `caiso_solar_endogenous_spill` is on, which
>    it is); `caiso_solar_shape_nl_hi_pct` 30.0 + `caiso_solar_shape_nl_lo_pct`
>    10.0 (only read by `inject_caiso_import_solar_shape`, gated on
>    `caiso_import_solar_shape`, which is `False`). **Do not read a CAISO
>    `run_config.json` as an inventory of what is armed.** The first is the rule
>    26 `[R-DELETE]` shape — the scalar of the *retired, rule-13-inadmissible*
>    NG:NG midday gas floor, still shipped at 0.80 by the standard backcast recipe
>    (`pipeline/backcast_config.py:1499`) — and is **FILED for the owner as a
>    deletion candidate**; a census lane may not remove a `ScenarioConfig` field.
> 2. **NEW QUEUE ITEMS (never adjudicated anywhere in the record; rule 14
>    `[R-ACCURATE]` measured-over-estimate candidates, surfaced NOT tested):**
>    - **`caiso_asymmetric_path_ratings`** — published WECC Path Rating Catalog
>      directional limits for the *internal* N-S paths (Path 15 3,265 MW N→S vs
>      5,400 S→N; Path 26 4,000 N→S vs 3,000 S→N) replacing the symmetric TTC
>      estimates the reduced topology ships. The loose directions let the LP
>      equalise the zones (Path 15 never binds; NP15==ZP26 byte-identical all
>      years) and ship SP15 midday solar north past the real 3,000 MW Path-26
>      limit, suppressing the measured NP15-over-SP15 premium. Registered on
>      `measured_interface_limits`.
>    - **`caiso_per_year_import_caps`** — ~~per-year published LCT pocket import
>      caps~~ **CLOSED (TESTED) 2026-08-03 by caiso-162; CAISO cell `U` → `O`.**
>      The lever was tested and works, but the headline was a **wiring defect**:
>      `apply_caiso_local_import_limits` had **no call site in the backcast
>      lane** — it was invoked only from `runner.py:1627` inside
>      `run_scenario_iso`, the *forecast* path — so the field was structurally
>      unreachable from every calibration solve, including via the
>      `ScenarioConfig` field this queue entry assumed worked. Caught because
>      the treatment arm recorded the flag `true` and came back **byte-identical
>      to its control**, with pocket flows pinned at exactly the static
>      12,008/1,436 MW. **Prices alone would have written a false `I`.** Fixed in
>      `run_calibration.py`; re-solved. Measured: 2023 byte-identical (provable
>      no-op, the zero-delta control), 2024 −0.167% and 2025 −0.124% of level,
>      C3a-2025 +12.1% → +12.0%, zero gate flips. Bounded ex ante at ≤0.22 pp of
>      the 12.2 pp C3a residual, so it **cannot** close that gate and does **not**
>      materially undermine the caiso-141 A2 attribution. Kept under rule 14
>      (published beats frozen estimate regardless of fit); **recommended for
>      promotion**, which is a separate governance act. Evidence:
>      `FINDING-caiso162-per-year-import-caps-2026-08-03.md`,
>      `PRECHECK-caiso162-per-year-import-caps-2026-08-03.md` + ADDENDUM A.
>      **Standing lesson:** a `run_config.json` recording a mechanism as armed is
>      not evidence the LP saw it — confirm a **call site exists on the lane
>      being solved**, and verify on a **flow/observable**, not on price.
>
>    **`caiso_asymmetric_path_ratings` — CLOSED (TESTED AND PROMOTED)
>    2026-08-03 by caiso-163; CAISO cell stays `K`, now on a second armed leg.**
>    This was the queue's last never-adjudicated item, so the CAISO lever queue
>    is now EMPTY of untested members. Published WECC Path Rating Catalog
>    directional ratings replace the symmetric TTC estimate on both internal
>    N–S paths (Path 15 3,265 N→S / 5,400 S→N; Path 26 4,000 N→S / 3,000
>    S→N). Rule 14 `[R-ACCURATE]`, **zero free parameters** — all four numbers
>    were already committed in `CAISO_PATH_DIRECTIONAL_RATINGS`; nothing swept,
>    no residual consulted, DOF ledger carried verbatim at 11/9.
>    **MEASURED ON FLOWS, NOT PRICES.** Against a same-HEAD flag-off control
>    the incumbent configuration moved power **past a published WECC rating in
>    1,141 path-hours** across 2023–2025 (Path 15 N→S peaking at
>    4,119/4,443/4,597 MW against the published 3,265, 294/450/380 h over;
>    Path 26 S→N at 3,514/4,000/2,946 against 3,000, 6/11/0 h over). Under the
>    keeper that count is **zero in every hour of every year**, and the paths
>    bind as real paths do (Path 15 N→S 307/489/411 h; Path 26 N→S
>    1,656/1,987/2,213 h). Path 15 binds at all for the first time — NP15
>    separates from ZP26 in 237/414/284 h, up from 3/0/1, and the 2024
>    byte-identity breaks. **Zero gate flips** on all nine criteria, C3a-2025
>    unchanged at +12.0 %, level effect nil (−0.004 % / −0.015 % / +0.010 %).
>    **PROMOTED** to `2026-08-03-caiso163-asym-path-ratings`.
>    **NO ZERO-DELTA YEAR EXISTS** for this mechanism (the ratings are
>    year-invariant), so the prereg replaced it with a pre-solve structural
>    assertion — flag-off returns the SAME OBJECT (identity, not equality) —
>    which passed before either arm solved. Wiring was checked **before**
>    solving and, unlike caiso-162's mechanism, the backcast call site already
>    existed (`interchange/spec.py:1988` inside `apply_interchange_topology`,
>    reached from `run_calibration.py:2037`); only the CLI/kwarg channel was
>    missing, wired across seven sites.
>    **IT OPENS A ROOT-CAUSE ISSUE RATHER THAN CLOSING ONE**, which is the more
>    useful result: the *real* Path 15 separates the hubs in ~100 % of hours by
>    +5.95/+8.58/+5.73 $/MWh, against the keeper's −0.077/−0.109/−0.084, and
>    the NP15-over-SP15 basis moves marginally **further** from the measured
>    +2.34/+7.99/+6.01 (the Path-15 N→S leg dominates the Path-26 S→N leg —
>    the prereg §3 registered the opposing-legs ambiguity and predicted NO
>    sign, so this is a resolved ambiguity, not a surprise). Under rules 14 and
>    1 `[R-STRUCT]` the published ratings **stay in** and the worse basis is a
>    **discovered bug**: the symmetric estimate was silently absorbing a defect
>    that lives elsewhere.
>    **NAMED OPEN SUCCESSOR (hypothesis, NOT adjudicated — no solve was spent
>    on it):** the reduced **two-link N–S topology and zonal aggregation**,
>    which cannot reproduce hourly Path-15 congestion whatever the ratings are.
>    It needs its own pre-registration and its own arm.
>    **DO-NOT-REDO:** do not re-test `caiso_asymmetric_path_ratings` itself
>    (keeper), and do **not** pitch the successor as a C3a lever — this arm
>    moved level by 0.01 %. Corrected on the record: the census's
>    "NP15==ZP26 byte-identical all years" holds for **2024 only** (2023/2025
>    differ in 3 and 1 hours), which does not change the finding that Path 15
>    essentially never bound. Evidence:
>    `FINDING-caiso163-asymmetric-path-ratings-2026-08-03.md`,
>    `PRECHECK-caiso163-asymmetric-path-ratings-2026-08-03.md`.

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
target C5a and the standing structural/offer questions. Items 1, 4, 5 and 6 are
struck through — 1, 4 and 5 were adjudicated and closed **without spending a
solve** (caiso-144, caiso-149 and caiso-136), and **6 was spent and PROMOTED at
caiso-146**. They are kept in place so the numbering stays stable and none is
re-proposed. **Live queue as of 2026-08-01: item 3, plus item 9 (new,
BLOCKING).** (Item 7 was SPENT and PROMOTED at caiso-147; **item 8 was SPENT
and PROMOTED at caiso-148**; **item 4 was REFUSED EX ANTE at caiso-149**;
**item 2 was BUILT and PROMOTED at caiso-151**.)

9. **Re-identify the CAISO measured offer surface's gas-coupling classifier**
   — **NEW at caiso-152 (2026-08-01), BLOCKING, unowned.** This is a
   prerequisite, not a price lever, and it blocks a correction the model
   demonstrably needs.
   `results/calibration/FINDING-caiso152-dam-bid-rle-parse-2026-08-01.md`.

   caiso-152 fixed the `dam-public-bids` RLE parse defect (`FINDING-caiso150`
   §E1): the parser keyed rows by their range START and never read the STOP
   columns, carrying only **47.9 %** of real GENERATOR EN curve-hours —
   dropping exactly the **stable-bid** ones — and charging **18.0 %** of
   curve-hours to the **wrong net-load bin** (tight bins under-weighted 15–16 %
   relative). The correction's effect is **MATERIAL and lands entirely on
   CT_PEAKER**: `econ_high` 1.055 → 0.912 and the ladder bin means
   +0.311/+0.277/+0.276/+0.304 against a ~0.146 tolerance — a uniform
   **+19–21 %** level shift in all four bins. CC_REGULAR is inside tolerance
   everywhere.

   **But the corrected artifact cannot be shipped**, and the blocker is not the
   parse. The derive fails its **own G1** on BOTH arms (CT bucket ratio 0.235
   old / 0.280 new against a ≥ 0.50 bound) and correctly withholds the consumed
   JSONs; rule 23 forbids retuning the gate. Worse, the OLD arm **is** the
   committed code path on the deriver's **own default corpus** (full contiguous
   1,095 days) and does **not** reproduce the committed keeper artifact: CC
   `econ_low` 1.544 vs 1.051, CT bucket 1,786 MW vs 10,785, **25 CT units vs
   102**, and G1 **failing** where the committed artifact records it **passing**
   at 1.416. Gas is byte-identical inside 2023–25 and fleet geometry round-trips
   exactly; what cannot be checked is the deriver's state at derive time (repo
   history begins 2026-07-30, eleven days *after* the artifact) or its corpus
   (no manifest is recorded).

   **The task:** re-identify the classifier so the CT bucket can be
   reconstituted, then re-derive both halves with the corrected parse.
   **Measured lead, not a diagnosis:** on the full corpus 71 resources /
   16,329 MW clear `r ≥ 0.6` but land at slope **< 4 MMBtu/MWh** — physically
   impossible for a thermal unit — which points at the body-price probe
   (`_price_at_frac` at 35 % of a p98-estimated capacity) landing off the SRMC
   body rather than at the gate thresholds. **Do not** relax G1–G4, blend
   OLD/NEW values, cherry-pick the passing CC half, or re-derive CT levels
   against a price residual (`FINDING-caiso152` §H).

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
4. ~~**`tranche_startup_amortization`** — evening-ramp start economics~~ —
   **CLOSED, cell is `G`: REFUSED EX ANTE at caiso-149 (2026-07-31, no-LP, no
   solve spent).** Three independent grounds and, unusually, **no reopen
   condition on the offer side at all**.
   - **Rule 1 `[R-STRUCT]`, dispositive alone.** The mechanism *is* the
     Order-825 **fast-start pricing** object: it folds a fast-start unit's start
     cost into the **price-setting energy bid** and changes nothing else
     (`min_run`/`min_down` stay 0 — "bid markup only, no new UC coupling").
     **CAISO does not have fast-start pricing**, and did not at any point in
     2023–2025: it recovers exactly those costs as **Bid Cost Recovery uplift
     settled outside the LMP**. CAISO's own DMM says so twice, nine years apart
     — FERC RM17-3 comments (2017): *"CAISO sets locational marginal prices
     based on marginal production costs. CAISO provides bid cost recovery
     payments made to compensate resources for any discrete commitment costs
     that are not recovered through marginal cost pricing"*; and the Body of
     State Regulators deck (2025-01-10): *"unit receives bid cost recovery (BCR)
     payments"* + *"CAISO is examining the **possibility** of some form of FSP
     in the WEIM"*, i.e. a candidate enhancement **mid-window**, still a Phase-2
     Price-Formation-Enhancements item in 2026. Fast-start BCR was 12/13/10 % of
     total CAISO BCR in 2021/22/23. This source is independent of **both**
     derives (OASIS bids, CAMPD). The four `K` cells are the four ISOs that
     **have** the rule — rule 25 in action.
   - **Rule 19 `[R-ONE-MECH]`, sufficient alone.** 92.9 % of the 7,808 MW the
     flag targets already carries an explicitly-identified fuel-invariant $/MWh
     margin, owned by `gas_offer_net_revenue_margin` (anchor 4.7964) over a
     `caiso_offer_surface_measured` **level**: CT_PEAKER econ_low/econ_high/peak
     **$22.16 / $22.69 / $8.42** on 3,289/2,964/533 MW, CT_CHP **$30.26 /
     $30.06 / $20.21** on 199/199/96 MW — **2.19–7.86×** the candidate's own
     **$3.85/MWh**, measured on CAISO's new `campd_ct_run_lengths_CAISO.csv`
     (50 plants + pooled fallback, 26,623 runs, class median 4.0 h × NREL
     $12.3–24.5/MW). The only zero-margin rows are CC_REGULAR peak (472 MW) and
     CC_CHP peak (56 MW) = 6.8 %, and they do not rescue it: CC_REGULAR peak's
     1.333 **is the measured DAM bid**, sitting *below* the 2.250 physical duct
     ratio. Every `_committed` tranche is separately already amortized by
     `compute_monthly_markup` at the **unconditional** P0→P1 seam.
   - **Rule 14 `[R-ACCURATE]`.** The incumbent is a *measurement* of CAISO's own
     submitted DAM bid, so the only rule-19-clean form swaps a measurement for a
     model — **and ERCOT-145's named reopen route (retire the fitted bands by
     measured re-identification, the start component then entering as one term
     of it) is ALREADY SPENT in CAISO**: the re-identification happened and its
     result *is* the incumbent. That is what makes CAISO's refusal strictly
     stronger than ERCOT's.

   **Direction reported, NOT the ground** (rule 1): the arm makes the CT
   econ/peak bands dearer and CT_PEAKER already sits at 1.832/0.659/0.471 vs
   actual 4.128/4.326/2.374 TWh (44/15/20 %) — the nyiso-96 signature from a
   worse base. It would not have licensed a rejection on its own, and **does not
   reopen caiso-119 R4**, whose guardrail (a real obligation-keyed mechanism with
   a cited D-4 window) is untouched — an offer markup is the wrong sign for it
   anyway. **vs NYISO:** nyiso-96's `R` was *conduct*-based in a market that
   **has** the rule; CAISO fails the prior question. **Filed not absorbed:**
   `compute_monthly_markup`'s unconditional committed-row amortization is shared
   by all six ISOs and needs an owner-scoped cross-ISO charter, never a CAISO
   lever session.
   (`results/calibration/FINDING-caiso149-tranche-startup-2026-07-31.md`.)
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
8. ~~**`nuclear_unit_availability`**~~ — **SPENT AND PROMOTED at caiso-148
   (2026-07-31); cell `U` → `K`, keeper
   `2026-07-31-caiso148-nuclear-availability`.** A rule-14 `[R-ACCURATE]`
   measured-**timing** swap with zero fitted parameters: the EIA-923 anchor
   keeps the monthly level, the NRC daily Power Reactor Status report replaces
   the within-month timing the fleet-month smear destroys. **The ex-ante wall
   check the handoff ordered cleared first** — this lever shares no input and no
   detector with the coal-only `unit_outage_short_windows` adjudicated `I` at
   caiso-136, because nuclear units carry no CO₂ and are **not CEMS reporters in
   any ISO**. No source change was needed to arm CAISO (the `arrays.py` seam and
   `outages.py` loader were already ISO-generic); the whole code delta is a
   two-row identifier crosswalk, and both the PJM and NYISO extracts still
   reproduce byte-for-byte (rule 25). Artifact: 1,886 rows / 2 reactors =
   **Diablo Canyon 1+2, 100 % of CAISO nuclear capacity and unit count**, 18
   windows including three refuels; coverage 100 % / 100 % / 58.1 % of days
   (31 of 36 months). **The five dropped 2025 months are correct, not a wall**:
   each holds a real event whose non-event pool is already saturated at 100 %,
   so the capped fixed-point cannot scale up to an anchor EIA-923 clipped at
   1.0 — cause *measured*, EIA-930 shows Diablo running up to **+3.1 % above its
   EIA-860 nameplate**, so posting the NRC level there would delete real
   capability. Unlike NYISO, the EIA-930 zero-block artifact does **not** occur
   in CISO, so 930 served as a clean independent validator (r_day 0.9807 over
   942 days). Build gates G1 +0.184/+0.145/+0.133, G2 ~100 % retention, G3
   ≤ 0.0746 %. In-solve the overlay **binds** (4,368/3,672/2,232 h) while staying
   **energy-neutral** (≤ 0.045 %), S2 closes in every year (nuclear r_day
   0.7873/0.8473/0.8550 → 0.9709/0.9921/0.9878), **every criterion verdict is
   unchanged**, and CT_PEAKER's most exposed C7 number (2025) *improves*
   0.864 → 0.866. **NOT a reserve/MSSC test** — the handoff's framing that Diablo
   "sets CAISO's entire reserve requirement" does not hold for this keeper, which
   runs `energy_reserve_coopt` / `caiso_reserve_coopt` / `as_reserve_formula` all
   `False` with a **static** 1,400 MW scarcity MCL; do not cite caiso-148 as
   reserve-floor evidence. **Open item filed, not absorbed:** the Diablo
   nameplate/uprate basis mismatch that costs 2025 its coverage is a
   fleet-representation fix outside a calibration session's scope.
   (`FINDING-caiso148-nuclear-availability-2026-07-31.md`.)

### 5.3 PJM — **NO failing criterion** (keeper `2026-08-03-pjm-147b-chp-heat`, CALIBRATED); ~~item 7~~ CLOSED at pjm-145 (REFUSED ex ante, cell `G` — no solve spent); **`state_carbon_pricing` SOLVED at pjm-146 → cell `O`, PENDING OWNER**; **`measured_chp_heat_rates` SOLVED and PROMOTED at pjm-147 → cell `K`**; **the CHP host-steam successor lane REFUSED at pjm-148 (no LP spent) — `chp_steam_following` stays `K`**; **rule-28(c) column CLOSED at pjm-151 (15 absent + 1 prose-only + 5 armed-no-cell → 0/0/0, no LP, no solve, keeper unchanged)**

**pjm-151 (2026-08-03): the PJM matrix column is CLOSED.** Ratchet
`docs/codebase-site/data/mechanism-matrix-gaps.json` PJM **15 → 0**; sweep
`scripts/mechanism_matrix_gap_sweep.py --iso PJM` returns `0 absent / 0 prose-only /
0 armed-no-cell / 0 live-but-invisible`. All 16 fields closed as **literal sub-scalar
registrations on 6 existing family rows** (`pjm_midcurve_belt`,
`measured_offer_surface`, `da_virtual_bids`, `reserve_pergen`,
`reserve_deliverability_scoping`, `seam_flow_envelopes`) — **zero new rows, zero
mechanism verdicts**, one cell mint (`matrix_gap_census` PJM `O → K`, an audit status,
the ercot-156 / caiso-161 precedent). Five of the sixteen shape the **published
keeper** and had no cell anywhere: `pjm_offer_midcurve_segments`, `pjm_seam_flow_limit`,
`pjm_seam_export_limit`, `pjm_seam_measured_ladder`, `pjm_reserve_online_rho`.

* **Mechanical cause:** the seam family sat behind the glob `pjm_seam_* :7371+` in
  `seam_flow_envelopes`' `def` — natural to a human, invisible to a checker that matches
  literals — and the `:7371` anchor was itself stale (the fields live at `:9019+`). Same
  defect caiso-161 §2 recorded. **Registrations must be full literals.**
* **PJM's instance of the caiso-161 §5 "armed-looking but dead" shape:**
  `pjm_reserve_online_rho = 1.0` is recorded in every PJM `run_config.json` and is
  **unobservable on the keeper** — sole read `reserves/spec.py:2291`, inside
  `if pjm_reserve_online_gated:` at `:2290`, which the keeper sets `False`. **NOT** a rule
  26 `[R-DELETE]` candidate (a built, reachable, default-off mechanism at its own
  documented default — not a retired mechanism's fitted residue), so **nothing is filed
  for the owner from PJM's column.**
* **Filed as an observation for a lane that may adjudicate, NOT adjudicated here:** the
  keeper arms `pjm_reserve_supply_cap=True` alongside `pjm_reserve_pergen=True`, and
  **both** of that flag's read paths are gated off by pergen —
  `reserves/spec.py` returns the pergen `ReserveDesign` at `:2280` *before* the
  `supply_cap` computation at `:2286` (its own docstring at `:2018`: "the zone-aggregate
  scoping flags are ignored in this mode"), and
  `pipeline/commitment.py::build_pjm_reserve_p1_prep` returns `(None, None)` at `:1374`
  because `pjm_reserve_commitment_scoped` is `False`. Whether that is cosmetic or a rule
  19 `[R-ONE-MECH]` question is not a census's call (rule 28(d)).
* **No armable candidate was surfaced**, consistent with the owner-declared PJM frontier
  (pjm-142). The census did not manufacture a successor.
* **MISO's ratchet moves 11 → 8 in the same commit and this is NOT a MISO census.** The
  PJM seam literals would have substring-shadowed three `miso_seam_*` fields into
  "covered" (`pjm_seam_flow_limit` contains the matched stem `seam_flow_limit`), silently
  dropping them from MISO's list with nobody having registered them. Those three are
  written out as real literals on the same row so the coverage is true; **no MISO cell or
  verdict is touched**, and MISO's remaining 8 are referenced by line number only so that
  naming them cannot count as registering them. **MISO is now the last open column.**
* **PJM's 18 shared-stem keeper-armed fields stay open** as a cross-ISO hygiene lane
  (ERCOT 14, CAISO 5, MISO 17 of the same class) — one column's session does not touch
  rows whose cells span all six.

**pjm-148 (2026-08-03): the host-steam holdout lane is REFUSED with evidence — no LP
solved, keeper untouched.** Prereg
`PREREG-pjm148-chp-host-steam-holdout-2026-08-03.md` committed before any measurement;
finding `FINDING-pjm148-chp-host-steam-refused-2026-08-03.md`. The lane pjm-147 §8 named
(`chp_btm_pct` / `chp_grid_pmin_mw` / the `chp_steam` floor **level**, to close CC_CHP
+2.49/+0.79/+0.39 TWh) has **no admissible arm**:

* **κ refutes the capacity/BTM half, harder than at pjm-131** — 0.0101/0.0404/0.0236 on
  the *current* keeper vs the inherited ≤ 0.20 rule; 2023 more than **halved** from
  pjm-131's 0.0226 because pjm-147's dearer offer moved CC_CHP further from its ceiling.
* **No measured host share exists for PJM, and the repair is bigger than pjm-131 scoped** —
  `chp-btm-share` re-curates to 35 rows, **35 degenerate AND zero CC_CHP rows** (all 35
  `ST_CHP`, because the steam-reporting CEMS unit is a **boiler**; 1,754/1,755 PJM
  steam-reporting unit-years carry zero MWh). Fixing the electrical-channel limb alone
  still leaves CC_CHP at **0 % coverage**.
* **The floor DOES bind and the keeper's own artifact under-reports it** — 0.994/0.692/
  0.815 TWh (11.0/7.9/10.4 %, the figure the handoff quoted) on a floor **verified
  unchanged** into the current keeper (436.4 MW mean, 2023), which nonetheless carries
  **no CC_CHP `chp_steam` row at all**.
* **Refused on identification, not liveness** — only a floor *reduction* helps (CC_CHP is
  over in all three years, so raising it, incl. deriving the WP-3 `steam_level_cf` PJM
  lacks, is wrong-signed by construction), and both channels are closed: `chp_pmin_cf` by
  rule 23 `[R-FROZEN-DERIVE]`, `btm_share` by the artifact. Anything else is sized by the
  gap — the neiso-71 kill, rules 21/24. Deleting the floor entirely reaches only ~0.99 of
  2.49 TWh anyway, and is separately barred by rules 1/14.

**DO-NOT-REDO:** do not re-derive a PJM CC_CHP host-steam floor or BTM share against this
residual; do not arm `chp_steam_floor_p25` for PJM (pre-WP-3 artifact ⇒ inert, and
wrong-signed regardless). **Structural reading:** κ ≈ 0.01 plus an ~11 % floor means ~89 %
of PJM CC_CHP is *voluntary economic clearing* — a merit-order residual, not a quantity one.

**Side finding, needs its own cross-ISO charter (not PJM's to land):** D-2 floor
attribution is **path-dependent**. The dispatch join at `legitimacy_diagnostics.py:2325-2327`
(predating caiso-155 — not a regression from it) uses `dispatch/*.parquet` when present,
else the dashboard **run payload**, which is CAMPD-bench-keyed and holds **none** of PJM's
14 CC_CHP plant codes (311 plants, PJM 2023). The protocol *mandates* the slim/payload
path, so CC_CHP/ST_CHP/nuclear silently lose all D-2/D-4 attribution — pjm-146 onward
dropped 10 rows vs pjm-144, incl. a **272 TWh `nuclear_mustrun`** row. Proven by running
current code over `pjm144_control_A`, whose own committed file records
`CC_CHP chp_steam 0.9938 TWh`, and getting zero CC_CHP rows. **No verdict moves** (all
three classes are C8-exempt), but rule 18 `[R-FORCED-BUDGET]` is scored entirely from this
file, so it is expected to affect **every ISO's slim-scored keeper**.

**pjm-147 (2026-08-03): the triage's rank-2 lever is BUILT, SOLVED, PROMOTED — and the
session also closes caiso-158's deferred PJM re-gate.** New keeper
`2026-08-03-pjm-147b-chp-heat` (owner instruction in-session); arms
`2026-08-03-pjm-147a-control-zerodelta` / `-147b-chp-heat`. PJM's own artifact derived for
the first time (rule 25 — MISO/CAISO/NYISO `K` and NEISO `O` transferred nothing): 65
(plant,class) rows, 21 applied, CC_CHP 74.0 % of class capacity but **82.5 % of the class's
own metered CAMPD energy**, CEMS 11/12 within 1 % at median 1.00000. **Zero fitted
parameters** and an off-registry hand factor RETIRED (DOF 18 → 19, `n_residual` unchanged
at 6). Keeper note 13 ("PJM CC_CHP runs +42 %", carried from pjm-135) is **CLOSED**:
|C1 CC_CHP error| **2.947 → 2.491, 1.427 → 0.788, 1.361 → 0.390** TWh, improving in all
three years and never crossing under — the neiso-70 overshoot kill (pre-registered as K5)
does not fire. CALIBRATED 9/9, C1 all 16/16 · free 12/12, zero fails, zero caveats.
**The pre-registration closed pjm-146's named gap**: E1d declared ex ante that no C1-gated
class may move > 1.5 TWh (largest non-CC_CHP move CC_REGULAR +0.366, PASS).

Three results binding on successors: (1) the caiso-147 seam defect is **measured SMALL** in
PJM — 4 applied rows / 182.2 MW against CAISO's 59 / 3,089 MW, correcting the triage's
expectation; (2) **CC_CHP is a PINNED class** (audit L4) excluded from the free-class score,
so this lever cannot move PJM's headline and equally cannot be gate-chasing — rule-1 work
only; (3) the **CT_CHP half is NOT identified** (32.6 % capacity / 25.1 % of its own metered
energy), NOT scored (`CT_CHP ∈ FUELMIX_EXCLUDED`) and nearly INERT at the seam (+0.36 %) —
do not cite it in either direction. **Not fully closed**: 2023 still runs +2.49 TWh over,
but the offer is now measured, so the residual is a QUANTITY question — the host-steam
holdout (`chp_btm_pct` / `chp_grid_pmin_mw`) and the `chp_steam` floor level, nyiso-105's
named successor lane. **DO NOT re-derive the heat rate against that residual** (rule 23).

**The control arm is caiso-158's follow-up item 2, now discharged.** caiso-158 §5 deferred
PJM's CT-meter-screen A/B for want of swap on a 15 GB box; this session ran it with 12 GB of
swap and the `--years`/`--reuse-solved` chain. Keeper → control: CT_PEAKER
**−0.924/−0.657/−0.899 TWh**, lw price +$0.057/+$0.044/+$0.077 — **dispatch-live and
score-neutral** (control is CALIBRATED 9/9 with a scorecard identical to the outgoing
keeper), the same shape caiso-158 measured in CAISO/NEISO/NYISO. One adverse diagnostic
row, stated: D-2 CT_PEAKER **rises** 15.2/15.4/15.8 % → 16.3/16.4/16.5 %, a GROUNDED
ABOVE BUDGET PASS throughout so no determination moves. This is why pjm-147's K2
strict-byte gate FAILED — a control on the corrected artifact cannot reproduce a keeper
built on the pre-screen one — and promoting arm B is what resolves it.
(`FINDING-pjm147-measured-chp-heat-rates-2026-08-03.md`;
`PREREG-pjm147-measured-chp-heat-rates-2026-08-03.md`;
`results/calibration/_pjm147_chp_ab.json`, `_pjm147_k2_drift.json`,
`_pjm147_flag_fidelity.json`.)

**pjm-146 (2026-08-02): the RGGI allowance adder is BUILT, SOLVED and REGISTERED —
all five pre-registered gates PASS — and LEFT PENDING, not armed.** Arms
`2026-08-02-pjm-146a-control-zerodelta` / `2026-08-02-pjm-146b-rggi-allowance`;
`pjm_rggi_allowance_pricing` stays default-**off**. Zero fitted parameters
(published auction clearing means, exact EIA-860 state membership, fleet's own
emission rates); DOF ledger 18 → 19 with `n_residual` unchanged at 6. K1 mc
identity 3.7e-13, K2 **0.0 MW** vs the keeper, K3 membership clean (VA in 2023,
out 2024/25), K4/K5 pass; load-weighted LMP **+$1.42/+$1.43/+$1.26** inside the
ex-ante band. **D-2 IMPROVES** — all three CT_PEAKER forced-share FAILs clear.
**But** determination goes CALIBRATED → NOT-YET: C3a-2023 +11.1 % (pre-declared
and licensed by E1d) and **C1 CC_REGULAR volume −16.06/−13.84 TWh (NOT
licensed — no C1 magnitude gate was pre-registered)**. Right in kind, too elastic
in magnitude: the model reproduces RGGI leakage (member CC → non-member coal/CT/
imports) but ~13–16 TWh where reality moves less. **Successor: the CC→coal
substitution elasticity, own charter, identified from PJM's own record — never a
haircut tuned onto the adder.** Two reusable results: (1) PJM's price coupling
**transmits** a one-signed level shift where it **cancelled** pjm-144's mean-zero
spread, so coupling is not a general bar on PJM zonal-cost levers; (2) score both
A/B arms' `legitimacy_diagnostics` on the **committed slim file set** — an
unregistered run has `load_share: null` and a full bundle resolves mechanisms the
gitignored committed tree cannot (the caiso-155 `diagnostics_plant_set` class).
(`FINDING-pjm146-rggi-allowance-2026-08-02.md`.)

C1 CC_REGULAR-2023 and C3a-2025 closed at pjm-135; **C3c-24/25 closed at
pjm-136** and is UNCHANGED through pjm-143 (tail counts byte-identical in both
pjm-143 A/B arms). The queue below is not gate-driven — it is ranked by
*structural* defect, per rule 1 `[R-STRUCT]`.

**CLOSED AT pjm-143 (2026-07-31, keeper promotion):** the PS-fold hydro LEVEL
defect (the old keeper-note item 11). PJM is listed in
`constants.EIA930_PS_FOLDED_INTO_WAT`; the `NG: WAT` pin is refused and the
level is EIA-923 `HY` — ~7 TWh/yr of phantom zero-MC hydro removed, CALIBRATED
9/9 in both A/B arms, `hydro_budget_nameplate_aware` provably inert (K → I).
Note for future price work: C3a-2023 is now **+2.99 %** (was +2.05) — the
phantom hydro was suppressing a real over-pricing; ~$0.29/MWh of 2023
over-pricing is newly exposed, per the untested PREREG §5.3 hypothesis that
PJM's offer calibration was fitted on the contaminated stack
(`FINDING-pjm143-hydro-level-923hy-2026-07-31.md`).

**ADJUDICATED `I` AT pjm-144 (2026-08-02): `gas_offer_margin_zonal_anchor` —
dispatch-live, price-inert; do not re-test without new evidence.** The
nyiso-109 cross-ISO transfer, tested in PJM's own lane with PJM's own derived
8-zone anchor table (capacity-weighted mean-zero convention → two-sided
defect, K6 dropped, K3 priced on the zonal grain, keeper-fleet weights via
`--weights-bundle`; capw invariant exact at 3.3483; zero fitted parameters).
A/B vs a same-HEAD control that reproduces the pjm-143b keeper to **0.0 MW on
every class-hour**: every construction gate except K3 passes and **no kill
fires** (both arms CALIBRATED 9/9, C1 16/16 free 12/12, C3c identical) — but
max zonal |Δλ| is **0.034/0.032/0.026 $/MWh** against the pre-registered
$0.10 liveness gate while dispatch moves 1.3–1.5 GW at the max class-hour
(CC_REGULAR −0.40/−0.70/−0.97 TWh → ST_GAS/CT_PEAKER): PJM's price-coupled
zones absorb the mean-zero redistribution. Verdict `I` by the prereg's own
K3 rule; **keeper unchanged**; the table stays registered in `constants` and
the flag is one `--gas-offer-margin-zonal-anchor` away. Re-open needs a
zone-decoupling mechanism under its own charter, a zone-grain scored
criterion, or an owner override of the prereg's K3 rule. NYISO's `K` is the
opposite-convention contrast (one-sided reference-zone shift → level effect
→ closed a failing C3a); neither verdict transfers to ERCOT/MISO (rule 25).
(`FINDING-pjm144-zonal-margin-anchor-2026-08-02.md`;
`PREREG-pjm144-zonal-margin-anchor-2026-08-02.md`;
`results/calibration/_pjm144_zonal_anchor_ab.json`.)

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
7. ~~**`pjm_dam_availability`** (**U**) — intaken but untested. pjm-137 measured
   that Dominion's real turbines are synchronised in 68.3 / 54.4 / 62.4 % of all
   hours, so the CT leg is **not** an availability defect; this lever now stands
   on the outage-envelope story alone. Note the ERCOT precedent before
   chartering it: the measured envelope there is *measured-correct* and was
   rejected twice on level (ERCOT-116/134).~~
   **▶ CLOSED AT pjm-145 (2026-08-02) — REFUSED EX ANTE, NO SOLVE SPENT; CELL
   STAMPED `G`. DO NOT RE-ARM the uniform class-grain form.**
   `results/calibration/FINDING-pjm145-dam-availability-2026-08-02.md`
   (PREREG + both probe instruments committed before measurement; ex-ante
   run through the real `generators_to_fleet_arrays` path). Measured: the
   armed overlay is a **+19–24 GW mean-availability net RESTORE** (remove leg
   fires 0/0/5 days in three years) and **66–68 % of the restore-day lift is
   structural-zero resurrection** — capacity the model's finer measured
   unit-grain record (CAMPD outage windows, layup, retiree CEMS caps, COD
   masking, `cc_outage_derate_from_top` tranche zeros) holds at zero, revived
   to λ by the water-fill's `_flat` branch (the ERCOT-135 §7.2 defect; the
   ercot137 pmax-ceiling fix was never ported to the PJM class-grain block).
   Model covered-class availabilities run 0.44–0.83 against the uniform
   fleet-mean target 0.867–0.887 — PJM's single whole-fleet aggregate
   (non-fossil forced MW included) is a wrong-boundary datum for a per-class
   application (rule 14 misalignment clause), and the unit-grain CAMPD stack
   is the incumbent availability owner (rule 19). The ERCOT contrast: its
   analogue was adoptable because the 60-Day disclosure is measured at
   per-class/plant grain and its restore is ceiling-composed with the
   forced-derate registry. Direction prediction (net REMOVE) scored WRONG —
   the model's availability basis is already measured, not statistical, which
   is exactly why the fleet-mean target misfits. Re-open only under a new
   charter with (1) the restore ceiling composed with the structural-derate
   registry, and/or (2) a class-/unit-resolved or fuel-split outage numerator,
   or (3) the event-window-cap form (ERCOT-148/149 shape) identified from
   PJM's own record.
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

### 5.4 MISO — target C7 COAL_PRB (non-ledgerable), the SOLE failing criterion; **rule-28(c) column CLOSED at nyiso-121 (8 absent + 4 prose-only + 7 armed-no-cell → 0/0/0, no LP, no solve, keeper unchanged at `2026-08-04-miso-122b-scope-gate`)**

> **nyiso-121 (2026-08-04) — MISO's matrix column is CLOSED, and it was the LAST one.**
> All 12 `miso_*` fields — 7 of them ARMED on the published keeper with no cell anywhere —
> are registered as **literal sub-scalar entries on 7 existing family rows**
> (`energy_reserve_coopt`, `rdt_tcdc`, `seam_flow_envelopes`, `import_hub_pricing`,
> `reference_price_interface`, `diurnal_price_amplitude`, `campd_outage_windows`).
> **Zero new rows (169 → 169); one cell mint, `matrix_gap_census` MISO `O` → `K`, an audit
> status and not a mechanism verdict; zero mechanism verdicts** — every verdict-bearing
> sentence transcribes an adjudication already on the record with its citation
> (`miso_firm_import_floor` rejected as an outcome pin under rule 13;
> `miso_pjm_lmp_import_pricing` refuted ex ante at miso-114; `miso_cc_coal_rebalance`
> licensed by nothing, premise removed at miso-115 §2; the per-Reserve-Zone Zonal ORDC
> ladder measured-refuted at miso-71). **No MISO lever is tested, chartered or queued and
> MISO's lever queue below is UNCHANGED** — the census surfaced no never-adjudicated
> armable candidate, so it did not manufacture a successor.
>
> **Mechanical cause, the caiso-161 §2 defect a third time:** `import_hub_pricing` carried
> `miso_pjm_lmp :2914` — an abbreviation that is not a `ScenarioConfig` field, on a stale
> anchor pointing at an unrelated over-generation comment block (the field is
> `miso_pjm_lmp_import_pricing` at :3872). **Plus a NEW variant no checker looks for:**
> `miso_manitoba_seam`, ARMED on the keeper, was prose-only inside `diagnostics_plant_set`
> — a row about probe plant sets. A mention on the **wrong family row** is as invisible as
> no mention, and unlike a glob or a stale anchor **it reads as correct coverage to a human**.
>
> **Census finding, measured on CONSTRUCTION (G-1; no LP, no solve, no dual):**
> `miso_pjm_border_anchor` is **PROVABLY UNOBSERVABLE** on the keeper — displaced by
> `miso_seam_measured_ladder`, which runs last and carries a full PJM band entry in all
> three keeper years. All 48 seam rows exactly equal (`np.array_equal`, float32) in
> 2023/24/25, with a positive control that separates ($0.92/$2.23/$4.78 with the ladder off,
> SPP/South untouched). A second instance: the keeper arms `miso_firm_imports` alongside
> `miso_manitoba_seam`, which drops the MHEB firm block. **Both filed as OBSERVATIONS; no
> cell moves** — whether either is a rule 19 `[R-ONE-MECH]` question belongs to a lane that
> may adjudicate MISO (rule 28(d)).
>
> **PREREG:** `results/calibration/PREREG-nyiso121-miso-matrix-column-2026-08-04.md`
> **FINDING:** `results/calibration/FINDING-nyiso121-miso-matrix-column-2026-08-04.md`
>
> **METHODOLOGICAL CORRECTION THAT BINDS THE NEXT LANE (FINDING §6.2).** A first draft
> enumerated MISO's 17 shared-stem literals, as ercot-156 / caiso-161 / pjm-151 each did.
> The pre-registered criterion 4 caught the consequence: **ERCOT went 12 → 11** because one
> field shared between the two keepers was newly counted "mentioned" — **one lane's prose
> dropping a field from BOTH lanes' live-but-invisible lists, with no ERCOT session
> registering anything.** Naming a shared field as a bare literal makes the sweep count it
> mentioned, which is exactly the "a mention is not a registration" defect the census exists
> to close, and it **leaks across columns**. The enumeration was withdrawn for a count plus
> a pointer to the committed `_matrix_gap_sweep_<ISO>.json`. **Consequence: the enumerated
> lists left in `matrix_gap_census` by the earlier column closures are PROSE, NOT
> REGISTRATIONS — trust `_matrix_gap_sweep_<ISO>.json` over the row's text.**
>
> **NAMED SUCCESSOR.** With every ISO's own-family column now closed, the **cross-ISO
> shared-stem backlog** (PJM 18, MISO 17, ERCOT 14, CAISO 5, all overlapping and all armed
> on keepers with no cell) is the **only remaining rule-28(c) debt**. That lane must
> **register these fields on rows, not enumerate them in prose**, or it will hide the very
> backlog it is closing.

*(Header refreshed 2026-07-31, miso-111: the former "C3b spread compression"
target is RETIRED — C3b PASSES on the live scorer against the
`2026-07-31-miso-109b-hy-level` keeper (miso-98 closed the 2025 breach and
deleted its ledger entry under rule 26 [R-DELETE]); the ledgered caveats are
C3a + C3c, 2/3. The diurnal-spread compression DEFECT the old target named is
still real (miso-89's measurement stands) but it no longer breaches any
criterion; the outage-grain data ask below remains its honest continuation.)*

*(Queue stamp 2026-08-03, miso-119/120: **`gas_offer_margin_zonal_anchor` is
CLOSED at MISO, cell `U` → `I`** — DISPATCH-LIVE (912.5 MW at the max
class-hour, every year) but PRICE-INERT (max zonal |ΔLMP| 0.027/0.030/0.050
$/MWh vs the pre-registered 0.10 K3 bar), adjudicated by
`PREREG-miso119-zonal-anchor-screen-2026-08-03.md` §5's own rule. K1/K2/K4/K5
PASS, no kill fires, keeper UNCHANGED, and the arm is **not** a keeper
candidate — nothing regressed and nothing was corrected at any scored grain.
MISO is inert for a **different** reason than PJM: the carried "coupled
topology" prior is FALSIFIED (zones decouple >$1/MWh in 21.3/24.4/50.1 % of
hours); the measured reason is the mean-zero applier convention + a small
surviving spread (max |anchor_z − ISO| 0.1799 vs PJM's 1.483) + repositioned
tranches that do not set price. **DO-NOT-REDO:** `max |Δoffer|` is an UPPER
bound only and must never again be read as a price-side lower bound — Phase 0's
11.54 $/MWh over-bounded the realized effect by two orders of magnitude because
the large deltas sit on rarely-marginal peaking tranches (capw p50 0.384 / p95
0.977 were the predictive statistics). Re-open needs a zone-GRAIN scored
criterion, a zone-decoupling mechanism under its own charter, or an owner
override — not a re-run and not an anchor sweep (rule 23).
`FINDING-miso119-zonal-anchor-2026-08-03.md`. **Item 5 `dual_fuel_switching`
is now the live queue head.**)*

0. ~~**Night-level min-gen FLOOR on the P0-detected committed run.**~~
   **RETIRED 2026-08-02 (miso-113 phase 2, `miso_coal_night_floor`, cell I) —
   and with it THE WHOLE REGULATED-PRB SELF-COMMITMENT FAMILY. All three
   admissible forms are spent; do not re-test any of them:** whole-band
   repricing (`coal_prb_committed_dispatchable`, miso-111, **R**), the measured
   per-plant SPLIT (`coal_prb_committed_split`, miso-112, **R**), and the
   night-level FLOOR (miso-113, **I**).
   **First, the reason this lane looked unfinished:** the mechanism never
   fired. It was wired into `pipeline/year.py` and `runner.py` only, while
   `scripts/run_calibration.py` — the orchestrator every calibration arm and
   keeper runs — builds its own `p1_fleet_prep=` chain and never constructed
   the hook. An armed run was accepted, recorded armed, solved, and the floor
   never applied. Fixed, and `_BRIDGE_BUILDERS` in
   `tests/unit/pipeline/test_p1_prep_wiring.py` now carries the builder so it
   cannot recur.
   **Wired, the floor is INERT on everything scored.** It binds legitimately —
   15.9/15.4/17.4 TWh floored, forced share 1.3/2.5/0.5 % against a 30 %
   budget, D-4 off-window 0.0 %, blocks never shorter than 24 h — and against
   its own same-HEAD control it moves class-hour L1 by 0.02 %, COAL_PRB energy
   by 0.000 TWh, D-1 not at all (cv_ratio 0.466/0.475/0.314 in BOTH arms), the
   C-series not at all, and the per-plant night level **not at all to four
   decimals** (0.4957/0.4482/0.5666 both arms vs a measured 0.4343). Two
   compounding reasons: the keeper already sits ABOVE the measured night level
   so the floor is slack in most hours, and where it binds the plant absorbs it
   internally — the eligibility gate floors only the `_committed` band, so
   `_econ`/`_peak` give back exactly what is forced. That gate also clips the
   level: 911 MW of the 4,274 MW floor, on 12 of the 18 clearing plants, sits
   above `_committed` capacity and is discarded.
   **Do NOT iterate the sizing.** Widening the floor to the full measured level
   (fill-order spread `committed → econ`) was built and tested independently in
   the same session and is WORSE: C7 cv_ratio 0.466→0.460 and 0.475→0.420
   (worse than control in the two years that had to clear 0.5), C3a
   −14.2→−15.8 %, C3b PASS→FAIL. The reason is structural, not a sizing
   question: **C7's failure is that the overnight distribution is too NARROW,
   and a lower bound can only narrow it further** — a slack floor changes
   nothing, a binding one clips the cheap hours that are the entire source of
   the model's off-peak variability.
   **What the three sessions jointly establish:** COAL_PRB's C7 failure is not
   a coal-conduct defect — the class's night level, volume (C1 16/16) and phase
   (profile_r 0.97-0.99) are all right. What is missing is the **dispersion of
   the overnight price signal** (model off-peak p10 $29.71 vs actual hub p10
   $17.95), i.e. the data-blocked miso-78/79 congestion + sub-hourly-RT lane,
   which now carries the C7 COAL_PRB residual in ALL THREE years. Any successor
   must WIDEN the overnight dispatch distribution; none of the three forms does.
   No successor is chartered — rule 19 forbids stacking a fourth coal mechanism
   on a price-formation residual.
   (`results/calibration/FINDING-miso113-night-floor-inert-2026-08-02.md`; runs
   `2026-08-02-miso-113c-control` / `2026-08-02-miso-113b-night-floor`.)
0b. **The overnight LEVEL offset — the live C7 target, DECOMPOSED at miso-114
   (2026-08-02, no LP spent).** miso-113 closed the coal-conduct family and
   routed the C7 `COAL_PRB` residual to "the data-blocked miso-78/79 congestion
   + sub-hourly-RT lane". **That routing is now narrowed by measurement:
   64 / 71 / 73 % of the model's overnight p10 gap to MINN.HUB is the
   congestion-FREE system ENERGY component** (+8.53/+7.01/+8.54) and only
   36 / 29 / 27 % is congestion (+4.89/+2.80/+3.24) — MISO publishes a
   single-reference decomposition, asserted in the probe at max cross-hub std
   0.000000/0.008345/0.000000 $/MWh. **The overnight window carries TWO
   defects, not one:** (a) a near-flat **LEVEL offset of +$4 to +$8 across
   net-load deciles 0-8** — the signature of a mispriced *marginal unit* — and
   (b) a **convexity/tail deficit in the top overnight decile** (gap flips to
   −3.11/−7.46 in 2024/2025), which is miso-89's ledgered availability object
   and stays there. (a) is what starves C7: a flat, too-dear overnight price
   gives the coal fleet nothing to cycle against, which is why repricing
   (miso-111), splitting (miso-112) and flooring (miso-113) the band all left
   `cv_ratio` unmoved. Trough anatomy at h1-3, arithmetic closing: the model
   fills a 1.5-1.7 GW import hole and a 3.4-3.9 GW gas hole with 2.6-3.7 GW of
   extra coal while keeping **1,907 / 2,415 / 2,350 MW of `CT_PEAKER` +
   `ST_GAS` online**. **NEXT STEP IS A NO-LP MEASUREMENT, not a solve:**
   CAMPD-observed MISO `CT_PEAKER` + `ST_GAS` online MW at h1-3 vs those model
   figures (EIA-930 does not split gas by prime mover, so miso-114 could
   measure only the model side). **DO NOT arm `miso_cc_coal_rebalance`** —
   its target is defined against another *model* quantity ("above the
   priced-import hurdle") with no measured identification (rules 5/21/24).
   (`results/calibration/FINDING-miso114-seam-hod-shape-2026-08-02.md`; probe
   `scripts/probes/_miso114_seam_hod_shape.py`.)
0c. **Seam hour-of-day shape — REAL, MEASURED, and SIZED OUT OF THE GATE LANE
   in the same session (miso-114).** The MISO seam reproduces annual
   net-interchange energy to **1.017 / 1.016 / 0.908** with an **hour-of-day
   correlation of +0.097 / −0.453 / −0.030** — no hourly skill, inverted in
   2024 — because the armed backcast overwrite `MISO_SEAM_LADDER_BY_YEAR` is an
   **8-band hour-INVARIANT** ladder, so bands-in-the-money run 4.4/3.5/2.9
   overnight vs 6.0/4.9/4.2 at peak, the opposite of measured flow. Signed
   mis-shape: night short 1,333/1,210/1,206 MW, peak long 1,338/1,147/746 MW.
   **Sized at the model's own local stack slope it is worth only
   −$0.32/−$0.39/−$0.44 overnight and +$0.34/+$0.43/+$0.30 at peak = 4-7 % of
   the residual** — a rule 1 `[R-STRUCT]` structural-fidelity item, **never** a
   C7/C3a instrument; do not charter it as one. **The obvious fix is REFUTED
   ex ante:** `miso_pjm_lmp_import_pricing` fails the model-independent test —
   the *actual* MISO−PJM_WEST spread is ±$1-2 overnight, night-minus-peak only
   −1.07/+2.16/+3.15 $/MWh, and actual net import correlates with the hourly
   spread at r = +0.289/+0.240/+0.286 (MISO imports 4,591 MW at h2 on a
   +$1.0/MWh spread). The seam is a firm/scheduled base, so its shape is a
   **scheduling** property, not a price property; `miso_firm_import_floor`
   stays rejected as an outcome pin (rule 13) and this does **not** re-license
   it. The one admissible successor is hour-of-day-resolved band
   **availability** at the `(month × hour-of-day)` grain `MISO_SEAM_DIBA`
   already uses — changing *when* a band may clear, not *how much* flows —
   which needs its own charter.
   **CLOSED ON MEASUREMENT 2026-08-04 (miso-123 — chartered and refused in one
   session, NO LP SPENT; `import_shape_lever` MISO `·` → `G`, minted from MISO's
   own measurement and NOT transferred from NYISO's, rule 25). The successor's
   premise was already satisfied.** The armed p90 envelope is not merely
   hod-*resolved* but hod-**shaped**: its own 24-point hour-of-day profile tracks
   the MEASURED directed flow at **r = +0.952/+0.987/+0.955** (PJM),
   +0.904/+0.973/+0.948 (SPP), +0.814/+0.837/+0.844 (South),
   +0.996/+0.992/+0.986 (Manitoba), while the model's CLEARED flow tracks it at
   **−0.638/−0.753/−0.852** (PJM). Availability already points the right way and
   the LP's flow points the wrong way — confirming this item's own attribution to
   the hour-INVARIANT price ladder *from the other direction*. The envelope is
   also **not the marginal constraint overnight** (miso-121's statistic): PJM
   marginal binding **0.6/2.4/1.4 %** of overnight hours vs 12.0/28.6/11.6 % at
   peak. Candidate C1 (per-band per-cell survival availability; same source, same
   grain, same 8-band grid, zero free parameters, zero thresholds) fails its
   pre-registered bars held-price — hod corr **+0.058/+0.031/+0.005** against a
   ≥ +0.20-in-2-of-3 bar, and annual seam energy
   **1.012/1.010/0.902 → 0.868/0.812/0.718** against a [0.85, 1.15] bar.
   **The bound generalises to the WHOLE ceiling class:** even the forbidden
   outcome pin (`min(model, measured)` hour by hour, computed as an unattainable
   bound and never armed) reaches only **+0.241/−0.289/+0.305** at energy ratios
   0.775/0.624/0.460 — a ceiling can only CUT and the model's overnight seam is
   **short** (−1,116/−972/−1,009 MW), so every availability ceiling moves the
   night limb AWAY from reality. **Do not re-derive a different envelope
   statistic and do not sweep `miso_seam_flow_percentile`** against this residual
   (rule 23 `[R-FROZEN-DERIVE]`). KILL-13 did **not** fire and the
   pre-registration predicted it would — recorded as a wrong prediction, not
   re-narrated: C1 is an **admissible** capability envelope that simply does not
   work, refused on rules 1/14 effectiveness and NOT on rule 13 admissibility, so
   the lane must not carry forward a belief that the construction is forbidden.
   **All three mechanism classes for this defect are now spent** — price
   (`miso_pjm_lmp_import_pricing`, `R` ex ante at miso-114 §4), ceiling (closed
   here), floor (`miso_firm_import_floor`, rule-13 outcome pin — still not
   re-licensed). The defect itself **remains real and unfixed** (annual energy
   1.017/1.016/0.908 at hod corr +0.094/−0.455/−0.023, independently reproduced
   on the miso-122b keeper against miso-114's +0.097/−0.453/−0.030 on miso-109b —
   two keepers, two constructions, same answer); re-opening needs a **scheduling**
   representation of the firm/JOA transfer base that can *raise* overnight flow
   on an identification that is not the measured net interchange itself.
   (`results/calibration/FINDING-miso123-seam-hod-availability-closed-2026-08-04.md`,
   `PREREG-miso123-seam-hod-band-availability-2026-08-04.md`, probe
   `scripts/probes/_miso123_seam_hod_availability.py`, transcript
   `PROBE-miso123-seam-hod-availability-2026-08-04.txt`.)
1. **Contract-period tonnage constraint — data-blocked**
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
   spread-compression driver (~10 GW 2025 summer under-derate) is
   instrument-blocked; the lever is data intake at unit/fuel grain, not a
   model change. (C3b itself now PASSES — see the header note — so this ask
   is defect-motivated, not gate-motivated.)
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
4. ~~**`measured_ct_heat_rates`** — audit-grade.~~ **EXECUTED-with-keeper at
   miso-117 (2026-08-03), cell `U` → `K`; the row is now CLOSED across all six
   ISOs** (ERCOT `I` by wiring, the other five `K`) — do not re-test any cell.
4b. ~~**The four plant-level `CC_CHP` heat-rate outliers**~~ (miso-116 §7 item 2:
   plants 10745 / 55089 / 55259 / 55088, 52.7 % of matched capacity below
   0.85× CAMPD gross). **CLOSED 2026-08-03 (miso-118): ADJUDICATED A BASIS
   ARTIFACT, no charter, NO LP SPENT, keeper UNCHANGED.** All four are one
   defect in the *comparator*, and the ratio decomposes exactly
   (`ratio = A_cems × F_family × G_gross`, closing to 2×10⁻⁶ on all 12
   plant-years): for three of the four the whole gap is **`G_gross` = CEMS
   gross load ÷ eGRID `PLNGENAN` = 0.653–0.809**, and `G_gross < 1` is
   **physically impossible** for a matched population — the steam turbines that
   convert CT exhaust into power burn no fuel, are not Part-75 monitored and
   contribute **no `grossLoad`**, while EIA-923 counts every MWh they make.
   That is the `FINDING-miso98` §6.1 defect one layer down, and
   `parasitic_load_factors.parquet` had already recorded it independently
   (net/gross 1.195–1.366, every row `out_of_band`, fallen back to the class
   default). On a basis-matched comparator from two independent meters (CAMPD
   fuel ÷ EIA-923 net MWh) all four sit inside the pre-registered
   `[0.90, 1.10]` band in 3 of 3 years. **DO NOT re-open on the CAMPD gross
   comparator, and do not quote the 0.810 / 0.653 / 0.802 / 0.817 ratios as a
   model result.** ~~One new single-plant item is NAMED BUT NOT CHARTERED and
   points the *other* way: 55088 Dearborn burns 13–17 % of its CEMS fuel in
   zero-electric-output boilers…~~ **EXECUTED at miso-122 (2026-08-04) — see
   item 4c.**
   (`results/calibration/FINDING-miso118-cchp-plant-outliers-2026-08-03.md`;
   probe `scripts/probes/_miso118_cchp_plant_outlier_basis.py`.)
4c. ~~**The 55088 Dearborn hybrid-cogen scope gate.**~~ **EXECUTED 2026-08-04
   (miso-122): the gate is BUILT and MISO's artifact re-derived; the A/B is
   DISPATCH-LIVE / PRICE-INERT; the `measured_chp_heat_rates` cell STAYS `K`.**
   eGRID's PLANT-level CHP split cannot see a **hybrid** — a topping CC/CT train
   plus a direct-fired package boiler on one ORIS code — so Dearborn's
   plant-average `thermal_share` (0.2396) passes the derive's 0.50 unfired
   ceiling while 16.6 % of its metered fuel burns in three `Other boiler` units
   with **zero gross load**, inside the rate charged to its power tranches.
   **The gate**, a third scope gate on the same footing as the other two:
   `heat_rate = (PLHTIAN + CHPCHTI) * (1 - dark_fuel_share) / PLNGENAN`, the
   share measured at CEMS **unit** grain at the artifact's own vintage year. A
   **share, not an MMBtu subtraction** — it needs CEMS's fuel *composition* to
   be representative and never CEMS's *level* to equal eGRID's, so the
   denominator stays `PLNGENAN`. Zero free parameters, **no threshold**, strict
   byte no-op where the phenomenon is absent.
   **miso-118's "it does not generalise" was too narrow.** Swept across all
   five artifact ISOs: MISO 55088 Dearborn 16.6 % (515 MW, 8.3465 → 6.9573),
   MISO 10745 MCV 0.09 % (1,479 MW), **NYISO 2493 East River 37.5 % (306 MW)**,
   NEISO 1595 Kendall 1.2 % (206 MW); PJM and CAISO none. Every dark unit found
   is a boiler `unitType` (100.0 % of dark fuel, behavioural selection — never a
   `unitType` allowlist), persistent across 2023–2025 at max/min 1.13–1.80.
   **Two measured exclusions the census forced in:** `dark_unreconciled` (the
   two meters disagree outside miso-118's [0.90, 1.10] band, or the whole CEMS
   footprint is dark — the sub-Part-75 plants 10328/55096/55799 where CEMS
   meters the boilers and MISSES the turbines, so an unguarded share runs to
   100 % and would drive the rate to ZERO) and `below_credited` (the share
   removes more than eGRID's entire CHP credit — which is what **excludes East
   River**).
   **A/B:** `CC_CHP` +0.3575/+0.2718/+0.5190 TWh and `CT_CHP`
   +0.2197/+0.2218/+0.2240 TWh displacing `CC_REGULAR`, imports and `COAL_PRB`,
   at max zonal |Δλ| **0.0491/0.0390/0.0752** $/MWh against the 0.10 bar —
   **zero of three years clear it**. All construction and protective gates pass,
   the control is byte-identical to the keeper, all nine criteria are identical
   between arms. The correction **ships under every branch** (rule 14
   `[R-ACCURATE]`).
   **SEAM OPENED, NOT CLOSED:** the keeper `2026-08-03-miso-117b-ct-heat` solved
   on the pre-gate artifact and is **no longer reproducible from HEAD**; arm B
   is the promotion candidate (nothing regresses; rule-22 LOO satisfied at year
   grain) but promotion is an owner call and was not taken in-session.
   **DO-NOT-REDO / DO-NOT-MISREAD, extending miso-119's and miso-121's:**
   `max_abs_class_hour_mw` is **not** a mechanism magnitude at MISO — it reads
   912.5 MW here and 912.5/912.5/912.500061 at miso-119, two unrelated levers to
   seven figures, because the statistic lands on the `import` class where a
   single **912.5 MW seam band** flips in or out (import delta non-zero in
   1,546 h, median 72 MW, exactly 912.5 in 7). Read the per-class **energy**
   deltas instead.
   **RULE 25 `[R-ISO-SCOPE]`: only MISO's artifact was re-derived.** NYISO
   (306 MW leaving its applied map) and NEISO (206 MW, −1.2 %) are handed to
   their own lanes with measured numbers; **no cell outside MISO is stamped.**
   (`results/calibration/FINDING-miso122-hybrid-cogen-scope-gate-2026-08-03.md`;
   prereg `PREREG-miso122-hybrid-cogen-scope-gate-2026-08-03.md`; probes
   `scripts/probes/_miso122_hybrid_cogen_scope.py`,
   `_miso122_scope_gate_ab.py`; runs `2026-08-04-miso-122a-control` /
   `2026-08-04-miso-122b-scope-gate`.)
5. ~~**`dual_fuel_switching`** — winter-event pricing candidate (Elliott-class),
   untested in MISO.~~ **CLOSED 2026-08-03 (miso-121, cell `U` → `I`): FULLY
   IDENTIFIED but PRICE-INERT.** All three legs are measured from MISO's **own**
   data with zero free parameters — capability 371/371/369 gas tranches =
   **15,827 MW = 23.3 % of MISO gas** (EIA-860 Multifuel switch flag,
   per-plant); switch price **12/12 measured MISO F923 Petroleum months every
   year** (20.36/18.22/17.21 $/MMBtu, the flat national fallback never reached,
   so rule 13's forward-regeneration test passes); event windows **observable in
   MISO's own CAMPD feed** — 90/459/452 gas-labelled unit-hours across 25/43/40
   distinct units lifting from p50 53.91 kg CO₂/MMBtu (pipeline gas) into the
   70–80 distillate band, validated against CAMPD's **own** diesel-labelled
   units at p50 73.65/73.46/73.65. The mechanism **genuinely fires** (the solve
   logs the cap on 371/371/369 tranches, matching the census exactly — the
   miso-113 "hook invisible to the calibration path" hazard is **cleared by
   measurement**) with fuel deltas to **197.8 $/MMBtu**, and still moves
   nothing: K3's price leg fails every year, max zonal |Δλ|
   **0.0000/0.0003/0.0000** vs the 0.10 bar, dispatch clearing 50 MW in 2024
   alone. **Inert for a DIFFERENT reason than the zonal anchor** (rule 25 within
   an ISO): that lever's perturbation never reached price-setting tranches;
   **this one's underlying phenomenon is negligible at MISO scale** — CAMPD's
   own meters put observed dual-fuel oil generation at 0.0023/0.0113/0.0128
   TWh/yr, **~0.002 % of ISO energy**. The pre-registered over-switching risk
   **did not materialise**: same-grain K7 gives model 0.00013/0.03757/0.01096
   TWh vs CAMPD 0.00233/0.01133/0.01284 TWh (0.06×/3.3×/0.85×, CAMPD a lower
   bound). **DO-NOT-REDO, extending miso-119's:** the binding-hour Δoffer p50
   (64.30/93.93/108.23 $/MWh) over-predicted the realized 0.0003 by **five
   orders of magnitude** — *binding is not marginality*. Only **0.00 %/1.24 %/
   0.54 %** of binding tranche-hours are also partially loaded, and 2023's exact
   0.0000 is because **no** capable tranche is ever both binding and marginal.
   The predictive ex-ante statistic is the **marginal share of binding hours**,
   never a percentile of the offer delta. Re-open needs a **winter-event-grain
   scored criterion** (the rubric has none), a chartered mechanism raising
   MISO's delivered winter gas further past parity, or an owner override — not
   a re-run, not a sweep (both legs are measured registries).
   (`results/calibration/FINDING-miso121-dual-fuel-switching-2026-08-03.md`;
   prereg `PREREG-miso121-dual-fuel-switching-2026-08-03.md`; probes
   `scripts/probes/_miso121_dual_fuel_screen.py`, `_miso121_dual_fuel_ab.py`,
   `_miso121_switched_volume.py`.)
   ~~**The live head of the MISO queue is now the 55088 Dearborn hybrid-cogen
   scope gate (item 4 above, named not chartered).**~~ **SPENT at miso-122
   (2026-08-04) — see item 4c. §5.4 now has NO named, un-adjudicated,
   non-data-blocked item left.** The two *named but unchartered* successors that
   remain are miso-114 §0c's hour-of-day-resolved seam **band availability** at
   the `(month × hour-of-day)` `MISO_SEAM_DIBA` grain — note it is the very seam
   whose 912.5 MW band quantises miso-122's K3 dispatch statistic — and
   miso-118's `CT_CHP`-side plant-level rate question. The bounded non-solve
   step remains item 1's Form 580 count.
   **QUEUE STAMP 2026-08-04 (miso-123): the seam band-availability successor is
   now CLOSED on measurement (item 0c above; `import_shape_lever` MISO → `G`,
   no LP spent), so the ONE named, un-adjudicated, non-data-blocked successor
   left in §5.4 is miso-118's `CT_CHP`-side plant-level rate at 55088 Dearborn
   (rule 14 `[R-ACCURATE]`, one eGRID rate spanning two prime movers at a mixed
   facility) — that is the live queue head. Beside it stand only the two bounded
   NON-solve steps: item 1's Form 580 tonnage COUNT (a sourcing pass, not a
   solve) and miso-114 §6's CAMPD `CT_PEAKER` + `ST_GAS` overnight-online
   measurement. A session going off-queue must say so and why.**
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

### 5.5 NYISO — target: **the compressed price DISTRIBUTION (peak half), DECOMPOSED and route-EXHAUSTED at nyiso-110 (arm solved INERT) — pending the owner amplitude-criterion call**, with C3c ledgered ahead of it; keeper `2026-08-03-nyiso-119-seny-increment`, **CALIBRATED-WITH-CAVEATS**; ~~items 6 + 10~~ CLOSED at nyiso-105, ~~item 11~~ CLOSED at nyiso-106, ~~item 12~~ CLOSED at nyiso-107, ~~item A (hydro input repair)~~ EXECUTED-with-keeper at nyiso-108, ~~the 2023 C3a breach~~ CLOSED-with-keeper at nyiso-109 (item 11b owner-DEFERRED, stays chartered), ~~item 8~~ CLOSED at nyiso-111 (classifier review ANSWERED, transfer falsified ex-ante)

**STATUS 2026-08-03 (nyiso-119) — THE PUBLISHED SENY $40 INCREMENT TIER IS
ARMED AND PROMOTED; nyiso-118's PARTIAL IS NOW COMPLETED ON CONSTRUCTION.**
Keeper `2026-08-03-nyiso-118-seny-span` →
**`2026-08-03-nyiso-119-seny-increment`**. Determination
CALIBRATED-WITH-CAVEATS, C3c the sole caveat, **UNCHANGED**. One delta
(`nyiso_seny_rcpf_increment_step`, matrix cell **`U` → `K`**, row added **with
the field** per rule 28(c)), **zero free parameters** (ledger 32 → 33,
`n_residual` 6). Two runs registered
(`2026-08-03-nyiso-119-control-zerodelta` + the keeper).

**(1) A PUBLISHED TIER THE MODEL NEVER CARRIED.** The SOM states SENY 30-minute
as a **$500/MW base over 1,300 MW PLUS a $40/MW increment above it**, and the
2023 SOM p. A-132 prints the pair as one object — **"SENY $500+$40"**. That
transcription **already existed in the codebase**
(`NYISO_RCPF_EAST_FAMILIES`' provenance block) before this session.
`nyiso_dynamic_reserve_requirements` has **always ENFORCED** the increment
(measured 1,550/1,800 MW against a 1,300 MW base for most of the day) and
**nothing ever PRICED it** — the whole shortfall was charged against the base
curve, whose first rung **$62.50** already sat above the entire measured
**$23.92/$30.37/$40.00** envelope. A rule 14 `[R-ACCURATE]` **omission** of the
nyiso-83/84 class, not a lever.

**(2) NO NEW NUMBER — it clears the NYC-precedent bar.** The $40 is the **same
ASM §6.8 item 12** already pinned for `east_30min_total`, whose clause names
**Southeastern explicitly**; the 1,300 MW breakpoint is **read from**
`NYISO_RCPF_LOCATIONAL`; the hourly requirement was already on the balance row.
The **$500 base, `critical_mw = 0` and `n_ramp = 8` are untouched** — the
posted-price instrument never reaches the base, so its shape stays
**unidentified** and keeps its ramp (nyiso-115's discipline).

**(3) RULE 19 BY SUBSTITUTION, NEVER STACKING.** The two-tier construction
carries the hourly requirement **natively**, in the increment band, so SENY takes
this branch **instead of** `nyiso_ordc_measured_step_span`'s — exactly as
`li_30min_total`'s ladder already opts itself out of the global flag. Every other
family's span behaviour is untouched.

**(4) ALL EIGHT GATES PASS, K-A…K-G SILENT.** Blast radius **exactly one
family**: the other eight are byte-identical in widths, requirement **and**
penalties at **$0.000** reachable price delta, so the rule-23 freezes on the NYC
curve and the LI ladder hold. Steps **8 → 9**, first rung **$62.50 → $40.00**,
base-ramp penalties **byte-identical**. **The nyiso-118 identity SURVIVES** —
total width == requirement at **0/0/0** violating hours in both arms. Solve-log
ORDC steps **59 → 60**, exactly +1 in one family. Zero slack, zero dump.

**(5) G4 AS PRE-REGISTERED FAILED AND IS RECORDED, NOT REDEFINED.** It demanded
exact $40.00 on the **closed** interval `(0, band]` — asymmetric, since it
excluded the lower kink (`s > 0`) but included the upper one (`s == band`). At
either kink the LP is degenerate and the dual sits legitimately between adjacent
band prices; that is why the zero-shortfall hours price $7.75/$17.31 and the
pre-registered form already tolerated **that**. Re-specified onto what K-G asks:
the **strict interior** prices at the published increment (**2/0/4** hours, every
one at exactly **$40.00**) and the band **edge** is **bracketed** (**$57.28** ∈
[$40.00, $62.50]). Same class as the nyiso-115 G2 and nyiso-117 G2a lessons.

**(6) STRUCTURAL CORROBORATION FROM THE SOLVE.** In the treatment's deepest 2025
hour the LP stops holding SENY reserve at **exactly `held_mw = 1300.0` — the
published base** — because past it the $40 tier no longer justifies more; the
control stopped at **1575.0** (= 1800 − one control band width), a number with no
market meaning. **The published curve's own breakpoint is where the dispatch now
stops.**

**(7) S-OVER NARROWED, NOT CLOSED — reported, not gated.** SENY max dual
**62.50 → 40.00** (2023), none (2024), **87.07 → 62.50** (2025). Of **10**
binding hours, those above the year's **measured** ceiling go **8 → 4** and those
above the **published $40** go **8 → 2**. **Not closed:** 2023/2024's *realized*
ceilings ($23.92/$30.37) sit **below** the published $40 cap, so pricing **at**
the cap is still above them — an **incidence/depth** question, not a
curve-construction one, and it belongs with the open peak-half lane in (3) above.
**All 18 scored numeric fields equal** the control's; the ISO-scope null was
pre-registered (SENY binds in 2/0/8 hours). **C3c UNCHANGED** — also
pre-registered; this does **not** reach nyiso-110's reserve-formation gap.
Evidence: `results/calibration/FINDING-nyiso119-seny-increment-2026-08-03.md`,
`PREREG-nyiso119-seny-increment-2026-08-03.md`, `nyiso119_gate_scores.json`,
`nyiso119_seny_increment_construction_probe.json`.

**STATUS 2026-08-03 (nyiso-118) — THE SENY ORDC SPAN FIX IS ARMED AND
PROMOTED, ON STRUCTURE, WITH THE RESIDUAL DELIBERATELY UNMOVED.** Keeper
`2026-08-03-nyiso-117-nyc-rcpf` → **`2026-08-03-nyiso-118-seny-span`**.
Determination CALIBRATED-WITH-CAVEATS, C3c the sole caveat, **UNCHANGED**. One
delta (`nyiso_ordc_measured_step_span`, matrix cell **`U` → `K`**), **zero free
parameters** (ledger 31 → 32, `n_residual` 6). Two runs registered
(`2026-08-03-nyiso-118-control-zerodelta` + the keeper).

**(1) A CONSTRUCTION-CONSISTENCY FIX, NOT A LEVER.** `nyiso_dynamic_reserve_
requirements` already put the **measured** hourly requirement on the balance row,
but the ORDC curve priced against it was still built off the **static published**
MW. The flag scales each dynamic family's width vector by `requirement[t] /
requirement_static`, restoring **total step width == the hour's requirement**.
SENY violated that identity in **6,239/6,249/6,231** hours of 2023/24/25 in the
control and **0/0/0** in the treatment. It introduces **no new number** — the
scale factor is the ratio of two already-committed measured inputs and the
published RCPF penalties are requirement-**independent** (measured unchanged).

**(2) THE ONE LIVE COUPLING WAS DISCHARGED EX ANTE, ON CONSTRUCTION.** The LI
ladder already applies this same span translation family-scoped to
`li_30min_total` without flipping the global flag, so arming it globally could
have **double-applied**. `scripts/probes/_nyiso118_span_construction_probe.py`
builds the `ReserveDesign` **twice at one HEAD** and diffs every family's
requirement, penalties and width vectors — **no LP, no dual**, because those are
solved co-optimization outputs whose byte-identity can only pass when the
mechanism does nothing (the nyiso-115 G2 error). **`li_30min_total` is
byte-identical in all three vectors: K-A did not fire.**

**(3) TWO CORRECTIONS TO THE RECORD, BOTH MEASURED.** The blast radius is
**three** families, not one — `_nyiso_design`'s docstring claimed a no-op for
NYC, which is **false** (NYC's measured requirement dips *below* static in
**185/227/120** hours); docstring corrected. **But NYC is re-REPRESENTED, not
re-PRICED**: shortfall is bounded by the hour's requirement, so width beyond it
is unreachable padding, and the frozen step curve makes that family a single flat
band — reachable price **pointwise identical ($0.000)**, so **K-B did not fire**
and the rule-23 freeze holds. That three-way split (SENY re-priced, NYC
re-represented, LI untouched) is what proves the instrument **has discriminating
power**.

**(4) ALL SIX GATES PASS, K-A…K-E SILENT.** G2c is an instrument that never
touches the parquet: the solve log's ORDC step count is **unchanged at 59/59/59
in both arms** — the flag re-spans widths and adds no steps. Zero slack and zero
dump in both arms. **All 18 scored numeric fields equal** the same-HEAD control's.

**(5) IT IS A PARTIAL, PRE-REGISTERED AS ONE — IT DOES NOT CLOSE S-OVER.** The
flag re-spans **widths only**; SENY's penalties are unchanged and its **first
rung is still $62.50**, already above the entire measured **$23.92/$30.37/$40.00**
envelope. **Measured effect: 2023 and 2024 are BIT-IDENTICAL; only 2025 moves,
downward** (SENY max dual **125.00 → 87.07**, the shallower ramp and the
pre-registered direction). Small because **SENY binds in almost no hours (2/0/8)**,
*not* because the curve barely changed — its reachable price differs in ~6,100
hours per year, but a demand curve can only price where there is a shortfall.

**(6) THE NAMED OPEN SUCCESSOR** is the **SENY LEVEL/STEP mechanism**: the
published curve is a **$500 base PLUS a $40 increment** while the model carries
only the base as a `critical_mw = 0` ramp. That is a **second mechanism** needing
its own pre-registration and its own arm (rule 19 `[R-ONE-MECH]`); nothing was
introduced, changed or fitted for it here. Promotion rested on rule 1
`[R-STRUCT]` / rule 14 `[R-ACCURATE]` — the static 1,300 MW span was an
**estimate leaking into a curve whose balance row is measured**. Evidence:
`results/calibration/FINDING-nyiso118-seny-span-2026-08-03.md`,
`PREREG-nyiso118-seny-span-2026-08-03.md`, `nyiso118_gate_scores.json`,
`nyiso118_span_construction_probe.json`.

**STATUS 2026-08-03 (nyiso-117) — THE TWO ORTHOGONAL FIXES ARE COMPOSED AND
PROMOTED, AND THE SUPERSESSION THAT ORDERED IT NEVER HAPPENED.** Keeper
`2026-08-03-nyiso160-ctmeter-screen-b` → **`2026-08-03-nyiso-117-nyc-rcpf`**.
Determination CALIBRATED-WITH-CAVEATS, C3c the sole caveat, **UNCHANGED at
3/0/14**. One delta (`nyiso_nyc_rcpf_step_curve`), **zero free parameters**
(ledger 30 → 31, `n_residual` 6). Two runs registered
(`2026-08-03-nyiso-117-control-zerodelta` + the keeper).

**(1) EVERY GATE PASSES, AND G2 IS RE-SPECIFIED ON CONSTRUCTION.** G1: the NYC
families reach exactly **$25.00** in **14/6/19** (10-min) and **2/6/8** (30-min)
hours and sit on an interior ramp rung in **zero** hours. **G2a — the scope
KILL** — all **seven** non-NYC families' `requirement_mw` (the balance-row RHS,
the one **pure input** in the sidecar) are **float32-exactly identical** to
control in all three years. That specification is nyiso-115's lesson inherited
rather than re-learned: its G2 demanded byte-identity of `dual` and `held_mw`,
which are **solved outputs of a co-optimization** and so could only be identical
when the mechanism did nothing. **G2b** corroborates from an instrument that
never touches the parquet — solve-log ORDC steps **73 → 59 in each year**, a drop
of exactly **14 = 2 families × 7 rungs**, family count unchanged at 9. `dual` and
`held_mw` are reported and **explicitly not gated**; `shortfall_mw` is demoted to
reported (**G2c**) because it too is a solved LP variable. G3/G4/G5/G6 PASS, zero
slack and zero dump in both arms, **all 18 scored numeric fields EQUAL** between
arms, K-A…K-E do not fire. Cell `nyiso_nyc_rcpf_step_curve` **`O` → `K`**.

**(2) THE NULL WAS PRE-REGISTERED AND IS NOW MEASURED DIRECTLY.** Prereg §5 said
in advance that a step and a ramp are BOTH $0 at or above the requirement, so
this moves the **level** in hours a family already binds and **cannot add binding
hours**. **K-E measures exactly that: binding hours GAINED = ZERO** in every
family and every year (the 30-min family *loses* 5 h in 2023 and 1 h in 2025 — a
shortfall crossing zero, also anticipated). C3c unchanged; it does **not** reach
nyiso-110's everyday-reserve-formation gap and is **not** reported as closing it.

**(3) THE SUPERSESSION PREMISE WAS FALSE, AND THE CONTROL IS WHAT CAUGHT IT.**
nyiso-115's arms were **already** on the POST-fix CT artifact: this session's
control is **bit-identical** to nyiso-115's control *and* to the caiso-160
keeper, and its treatment **bit-identical** to nyiso-115's treatment —
`max |ΔMW| = 0.000000`, `max |Δprice| = 0.000000`, every class-hour and
zone-hour, all three years. That is **not** "the CT fix is inert": caiso-160's
own pre-fix vs post-fix arms differ by max |ΔMW| **508.19/628.89/387.23** and
max |Δprice| **$10.50/$10.56/$9.04**. The artifact vintage had been **assumed
from commit ordering**. Precisely: in a fresh container
`git merge-base --is-ancestor` cannot see other branches' commits and **says so**
(exit **128**, `fatal: Not a valid object name`) — git *does* distinguish that
from a genuine negative (exit **1**). What collapses the two is the ordinary
`cmd && yes || no` idiom, which maps every non-zero exit to "not an ancestor".
The shortcut is unsound **as usually invoked**, the same failure mode as reading
a pipeline's exit status instead of the process's. **Compare the dispatch.**
Yielding the keeper was unnecessary. Relatedly, FINDING-nyiso114 §2's drift
caution did **not** fire: control-vs-keeper drift measured **exactly 0.0**. The
same-HEAD control was still the right design (drift is not knowable in advance);
its value here is that it turned an assumption into a number. **DO-NOT-REDO —
this composition is now solved twice, bit-identically, at two HEADs.**

**(4) SENY SCREENED EX ANTE, NO SOLVE — `S-OVER`, RECORDED NOT ACTED ON.**
Pre-registered with its **own** kill set so it is never folded into the NYC flag
(rule 19). The isolated SENY-only 30-min adder (`DUNWOD − CAPITL`) caps at
**$23.92/$30.37/$40.00**, with **52 hours of 2025 at exactly the published $40**
increment and **zero above in any year**; the modelled **$500 base is never
reached in 26,301 hours**. The model prices SENY in 2/0/8 hours at
**$62.50–$125.00** — its very first rung ($500/8) is already **above the whole
measured envelope**, so **9 of 10** binding hours are **over**-priced, the
**opposite** direction to NYC. SPAN confirmed: measured requirement mean
1,602/1,594/1,613 MW (max 1,800) against static widths of 1,300 — mis-spanned in
**69 %** of hours. `nyiso_ordc_measured_step_span` stays **`U`** (nothing armed);
it needs its own pre-registration and arm. **Instrument honesty:** the screen's
intended negative control **degenerates** on the 30-min product (the East 30-min
adder is identically **$0.00** in every hour), so it is reported as
**uninformative, not as a pass**, and the reference pair is validated instead on
the 10-min product where East does bind (**4,603/6,993/6,611** hours, max
**$27.00/$36.05/$46.22**).

**(5) CROSS-ISO: NOTHING RE-TESTED.** NYISO's transfer queue stays empty and the
shared-field ratchet still reports **0** for NYISO (40 family fields; 0 absent /
0 prose-only / 0 armed-no-cell / 0 shared-gap; the lone "live-but-invisible" row
is the declared `weather_year` exclusion). ERCOT/PJM/MISO/CAISO backlogs are
their lanes' work (rule 25 / 28(d)).
`results/calibration/FINDING-nyiso117-stepcurve-compose-2026-08-03.md`.

### 5.5 NYISO — target: **the compressed price DISTRIBUTION (peak half), DECOMPOSED and route-EXHAUSTED at nyiso-110 (arm solved INERT) — pending the owner amplitude-criterion call**, with C3c ledgered ahead of it; keeper `2026-08-02-nyiso-113-li-locational`, **CALIBRATED-WITH-CAVEATS** (header keeper id corrected at nyiso-116 — it had gone stale at the nyiso-113 promotion); ~~items 6 + 10~~ CLOSED at nyiso-105, ~~item 11~~ CLOSED at nyiso-106, ~~item 12~~ CLOSED at nyiso-107, ~~item A (hydro input repair)~~ EXECUTED-with-keeper at nyiso-108, ~~the 2023 C3a breach~~ CLOSED-with-keeper at nyiso-109 (item 11b owner-DEFERRED, stays chartered), ~~item 8~~ CLOSED at nyiso-111 (classifier review ANSWERED, transfer falsified ex-ante)

**STATUS 2026-08-03 (nyiso-116) — TWO C3c LANES CLOSED BY MEASUREMENT, AND THE
$2.46 KNIFE-EDGE RETIRED AS A TARGET.** Keeper **UNCHANGED**
(`2026-08-02-nyiso-113-li-locational`). **No lever proposed; no parameter
introduced, changed or fitted.** One diagnostic run registered
(`2026-08-03-nyiso-116-unit-layer`, CALIBRATED-WITH-CAVEATS, C3c the sole
ledgered caveat — identical to the keeper).

**(1) THE SETTLEMENT BASIS IS INERT.** C3c scores an energy-only model series
against an actual that embeds RCPF (`calibration_verdict.py`'s own G-20a comment
names "NYISO RCPF-into-LBMP"), and the post-solve overlay that would supply the
settlement basis is cell **G** under rule 19 — so NYISO sat in the gap between
two individually correct decisions. The admissible route is the **co-opt's own
locational duals**, readable from a bundle only since nyiso-114. Rebuilt that
way, C3c is **3/0/14, unchanged in every year**, and it is **proved rather than
observed**: the best settlement price attainable in *any* sub-threshold hour is
**$286.42/$297.54/$276.42** — margins **$13.58/$2.46/$23.58**. In 2024 the adder
is exactly **$0.00** in all three pinned hours. `nyiso_rcpf_postsolve_overlay`
note extended; **cell stays G**. **DO-NOT-REDO — this lane is closed.**

**(2) THE KNIFE-EDGE IS NOT THE GATE.** C3c bands at `[0.5×, 2×]`, so the model
needs **5/6/21 hours**, and the hour that must clear sits at
**$286.42/$201.69/$235.73** (**+$13.58/+$98.31/+$64.27**). C3c fails in **all
three years**; **2023 is the nearest miss, not 2024**; and closing the pin leaves
2024 at **0.25×**, still failing. Worse, the pinned hours are **not real tail
hours** (actual **$282.83/$179.20/$128.43**) while **h4526 — reality $511.30,
model $201.69 — IS one**, so a pin-sized lever books **three false positives**
and misses the true hour. That is the caiso-144 pattern and a rule 1
`[R-STRUCT]` violation by construction. nyiso-85 §7d's SRMC-roof attribution
**stands**, corroborated as a rate (model tail precision **67 % / n-a / 79 %**)
and refined: inside the June 2024 episode the model's peak is **phase-shifted
~2 h late and clipped**.

**(3) NEW INSTRUMENT ROW `unit_network_layer_sidecar` (cells `IIIKKI`).**
nyiso-114 §6's pin attribution rested on gitignored artifacts nobody could
re-derive. Both stated grounds for that exclusion measured **false**:
*"regenerable by a replay"* (nyiso-114 §2 — a P0-bridge keeper is not
replay-recoverable, so the layer is **permanently** unrecoverable) and
*"~58 MB/bundle"* (measured **3.2 MB** for a whole 3-year NYISO bundle, ~18×
overstated; the figure predates `DELTA_BINARY_PACKED`). Layer committed via
`git add -f`; default unchanged for ordinary bundles. **All four §6 claims
re-verified to the decimal** (both LI paths saturated, pin energy-side, one
part-loaded LI unit `7146_1` at 68.9346/73.8 MW, **596.9 MW** idle).

**STANDING LESSON FOR EVERY LANE: G1 is a PER-GATE property, not a bundle
property.** This arm fails G1 globally ($10.51/$10.56/$9.04) yet its C3c tail is
**bit-identical** in 2023/2024 and its C3c count identical in all three years —
so it IS the right instrument for that gate. Show it per gate; never assume it.
**And a third gate-instrument failure, disclosed:** G3/P4 first failed on a
`1e-6` MW tolerance against **float32** columns whose spacing is 7.6e-06–6.1e-05
MW — numerically unsatisfiable. nyiso-113's K3/K4 and nyiso-114's `held_mw` were
about a column's **semantics**; this one is about its **dtype**. Checking that
the writer emits the column is not enough — the column must be able to
*represent* the tolerance the gate asserts.
`results/calibration/FINDING-nyiso116-c3c-unit-layer-2026-08-03.md`.
### 5.5 NYISO — target: **the compressed price DISTRIBUTION (peak half), DECOMPOSED and route-EXHAUSTED at nyiso-110 (arm solved INERT) — pending the owner amplitude-criterion call**, with C3c ledgered ahead of it; keeper `2026-08-03-nyiso-115-nyc-rcpf`, **CALIBRATED-WITH-CAVEATS**; ~~items 6 + 10~~ CLOSED at nyiso-105, ~~item 11~~ CLOSED at nyiso-106, ~~item 12~~ CLOSED at nyiso-107, ~~item A (hydro input repair)~~ EXECUTED-with-keeper at nyiso-108, ~~the 2023 C3a breach~~ CLOSED-with-keeper at nyiso-109 (item 11b owner-DEFERRED, stays chartered), ~~item 8~~ CLOSED at nyiso-111 (classifier review ANSWERED, transfer falsified ex-ante)

**STATUS 2026-08-03 (nyiso-115) — THE NYC RESERVE DEMAND CURVE WAS THE WRONG
SHAPE, AND NYISO'S OWN POSTED PRICES SAY SO.** Keeper
`2026-08-02-nyiso-113-li-locational` → **`2026-08-03-nyiso-115-nyc-rcpf`**.
Determination CALIBRATED-WITH-CAVEATS, C3c the sole caveat, UNCHANGED at 3/0/14.
One delta (`nyiso_nyc_rcpf_step_curve`), **zero free parameters** (ledger 30 → 31,
`n_residual` 6).

**(1) SCREENED EX ANTE, NO SOLVE SPENT REACHING THE HYPOTHESIS.** nyiso-114's
per-family sidecar showed the binding constraint is the NYC pair, with 307–358 MW
shortfalls of a 500 MW requirement clearing at $15.63/$18.75 — a rule 14
`[R-ACCURATE]` question about a MEASURED input. NYISO's posted **zonal** DA
ancillary-service prices answer it: the regions nest (NYCA ⊃ East ⊃ SENY ⊃ NYC),
so zone J minus a zone sharing every region *except* NYC isolates the NYC-only
dual. All three qualifying references agree **exactly** (max $25.00, same 45/141
hours at $25.00, **zero** above); the two non-SENY controls do not ($65 = $25 NYC
+ $40 SENY). **LEVEL CONFIRMED** — never exceeds $25.00 in 26,301 hours, and the
10-min product stacks to exactly $50.00 in precisely the hours the 30-min sits at
$25.00 (5/5, 16/16, 98/98). **SHAPE REFUTED** — a smooth opportunity-cost
continuum plus ONE ATOM exactly at the ceiling (17/45/141 h) and essentially no
mass at the model ramp's interior rungs (0/1/2 of 103/167/428). The model's duals
sat on those rungs and **never reached $25.00 in 26,280 hours**, under-pricing by
1.5–2.4× (10-min) and 3.7–7.1× (30-min). Also checked and CLOSED: no NYC
locational **spin** family is enforced (continuum, max $20.91–29.72, zero hours at
$40), so the model is right to omit it. Scope is the measurement's boundary — East
($775) never approached, LI no material adder, SENY caps at the $40 #1344
increment (**reported, not acted on** — `nyiso_ordc_measured_step_span`'s lane,
rule 19). Row `nyiso_nyc_rcpf_step_curve`, cell `....K.`.

**(2) A SCOPE GATE BELONGS ON THE CONSTRUCTION, NOT THE DUALS — a general
lesson.** Pre-registered G2 demanded every non-NYC family be byte-identical in
`dual`, `requirement_mw`, `held_mw`, `shortfall_mw`. Three of those are **solved
outputs of a co-optimization**, so the gate can only pass when the mechanism does
nothing: it FAILED and was uninformative. Decomposed onto what kill K-C actually
asks, every non-NYC family's `requirement_mw` and `shortfall_mw` are
byte-identical in all three years, and the solve logs confirm it independently
(**73 → 59 ORDC steps** = 2 families × 7 lost rungs). K-C does not fire; the
mis-specification is recorded rather than quietly redefined.

**(3) THE NULL WAS PRE-REGISTERED.** Prereg §4 said in advance that a step and a
ramp are BOTH $0 at or above the requirement, so this moves the **level** in hours
a family already binds and **cannot add binding hours**. C3c unchanged; it does
**not** reach nyiso-110's everyday-reserve-formation gap and is **not** reported
as closing it. All twelve scored numeric fields EQUAL to the same-HEAD control's.
Promoted on rule 1 / rule 14, not on gate movement. **Not a DO-NOT-REDO breach:**
the June-2026 `nyiso 25 rcpf-steep` probe transferred the NYCA-30min
`critical = 0.75 × requirement` anchor (a different parameterization, different
family), had **no matrix row**, and was rejected on the C3c tail COUNT — i.e. on
fit, which rule 1 forbids as grounds for rejecting a correct mechanism.

**(4) THE SHARED-FIELD BLIND SPOT IS CLOSED FOR NYISO AND RATCHETED FOR ALL SIX.**
The ISO-scoped census only sees `<iso>_*` fields, so a shared mechanism armed on a
keeper with no row was invisible to sweep AND CI — nyiso-114 closed NYISO's
ISO-scoped column to 0/0/0 while **twelve** shared fields sat armed on its keeper
with zero matrix mention. `mechanism_matrix_gap_sweep.py` gains a keeper-keyed
shared census (`SHARED_CENSUS_EXCLUSIONS` holds the declared false positives —
only `weather_year`), and `check_mechanism_matrix.py` a shared ratchet that stays
stdlib-only by parsing defaults from source and reading each keeper's committed
`run_config.json`, **omitting whatever it cannot read as a literal** so it can
never be stricter than the sweep that writes the baseline (the failure mode that
made nyiso-114's `\b`-vs-substring ratchet unsatisfiable). **NYISO 12 → 0**: six
sub-scalars named literally on their family rows, five given honest rows
(`coal_drop_pof`, `gas_st_startup_spread`, `cc_duct_peaking`,
`cc_nameplate_summer_derate`, `cc_capacity_reconcile_path`), one false positive.
Three more surfaced by a stricter prose-only criterion, also closed — including
`historic_outage_overlay`, whose row records it is **INERT on the dispatch**
(re-verified against the tree: four references, no consumer reads it back); its
rule-26 deletion question is **raised, not acted on**. The minted rows being
ISO-neutral also closed NEISO (2 → 0) and shrank CAISO 6 → 5, MISO 18 → 17,
PJM 19 → 18, **with no other ISO's cell given a verdict** (rule 25/28(d)).

**(5) THE CROSS-ISO TRANSFER QUEUE IS EMPTY — five candidates, ZERO solves.**
`maxgen_emergency_tier_pricing` **→ I** (across 5,347 messages of NYISO's own
operational record in 2023–2025: **zero** MaxGen declarations, **zero** EEA
alerts — a declared-*window* floor with no window, rule 17 before a solve).
`cc_committed_offer_margin` **→ G** and `measured_offer_surface` **→ G** (both
derive from submitted unit-level offer curves; NYISO publishes none at any grain,
so the only route left is importing the donor's fitted level — rule 25).
`reference_price_interface` **→ G** (rule 19 — NYISO already carries this
phenomenon ARMED ON THE KEEPER as `nyiso_import_hub_prices`, whose own definition
names it "the NYISO analogue of `miso_pjm_lmp_import_pricing` and
`caiso_import_hub_prices`"). `storage_vintage_ramp` **→ I** by magnitude
(lithium-ion 200.5 → 252.7 MW across the whole window, pumped storage flat at
1,220 MW; the entire increment mis-timed by half a year is ≤ 0.057 TWh against
~150 TWh). **NOTE: this is NOT the C3c queue** — §5.5's exhausted-queue finding is
about the C3c / peak-half lane and still stands.
`results/calibration/FINDING-nyiso115-nyc-rcpf-step-curve-2026-08-03.md`.


**STATUS 2026-08-03 (nyiso-114) — THE PER-FAMILY RESERVE DUAL IS PERSISTED, THE
CENSUS RAN IN ALL SIX LANES, AND TWO DEAD KNOBS ARE GONE.** Keeper **UNCHANGED**
(`2026-08-02-nyiso-113-li-locational`); nothing promoted, demoted or re-keyed.

**(1) The all-ISO gap nyiso-113 §8 filed is CLOSED.** New write-only sidecar
`hourly/reserve_family_<year>.parquet` — `family`, `reserve_class`, `dual`,
`requirement_mw`, `held_mw`, `shortfall_mw` — so the LP row itself
(`held + shortfall ≥ requirement`, tight exactly where the family prices) is
checkable from a bundle. `held_mw` comes from the **balance row's own activity**,
not a per-family R re-sum, because that re-sum would have to re-derive five
layout-dependent coefficient structures. Instrument, not a lever: no
`ScenarioConfig` field, no CLI flag, no LP row/column, zero DOF, 46 KB/ISO-year.
Row `reserve_family_dual_sidecar`, cells `IIIIKI` — `I` is "this lane's committed
bundles still cannot answer a locational-family question", and each lane's next
solve mints the artifact with nothing to arm. **Not backfillable:** a keeper
arming a P0-run-pattern mechanism cannot be re-solved into byte-identity once
main moves (measured — see (2)).

**FIRST RESULTS, previously unobservable in any ISO.** NYISO's binding reserve
constraint is **overwhelmingly the NYC locational pair** (`nyc_10min_total`
priced in **17/6/29** hours of 2023/24/25, `nyc_30min_total` 8/6/10,
`seny_30min_total` 2/0/8), and **every NYCA-wide family is slack in every hour of
all three years** — a direct measurement of nyiso-110's inference.
`li_30min_total` binds in **exactly** the five 2025 hours (h4193–4195, h4217–4218)
nyiso-113's Zone-K headroom screen predicted *ex ante*, and nowhere else.
**It also CORRECTS nyiso-113 §7:** the two 2023 reserve-dual hours attributed
there to the LI mechanism were **`seny_30min_total`** — the LI families bind in
**zero** hours of 2023. An error in reading a summed series, not a defect in the
keeper, and precisely the error class the sidecar makes impossible.

**(2) The pre-registered kill was discharged by MEASUREMENT.** Gate G1 (replay
reproduces the keeper) **FAILED** — max |Δprice| $9.0–10.6, mean LMP
+0.012/+0.012/+0.055 %, a CT_PEAKER↔ST_GAS tie reshuffle with total conserved.
Kill K-A required attribution, so a 2024 re-solve was run at the session's
**base commit** with the entire session diff absent: it reproduces the
**identical** divergence (10.5637 $/MWh over 18,630 zone-hours, both legs). The
divergence belongs to the 58 commits between the keeper's solve basis and this
base, **not** to the instrument. **Standing lesson for every lane: G1 is a
labelling gate — a failing replay makes results "measured on the recipe", never
"measured on the keeper".**

**(3) The census, all six lanes, + a shrink-only CI ratchet.**
`scripts/mechanism_matrix_gap_sweep.py` (promoted from probe, `--iso`).
Absent-from-matrix / armed-on-keeper-with-no-cell: **ERCOT 64/35, CAISO 39/23,
PJM 21/8, NEISO 15/10, MISO 12/10, NYISO 10/9 — 161 and 95.** CI saw none of
them (the diff gate fires only on same-PR additions). **NYISO's column is now
CLOSED — 0/0/0**: its nine were `nyiso_gas_bridge_*` sub-scalars, registered
literally on the `gas_commitment_bridge` row's `def`, plus
`nyiso_iroquois_winter_spread`, which lived only in the matrix file's header
comment and now rides `gas_hub_basis_overlay`. **The other five columns are their
own lanes' work** (rule 25/28(d) — a census can mint a `U` and nothing more), but
`docs/codebase-site/data/mechanism-matrix-gaps.json` enumerates all 146 and
`check_mechanism_matrix.py` now **FAILS** any PR whose ISO-scoped field is in
neither the matrix nor that baseline. Row `matrix_gap_census`, cells `OOOOKO`.

**(4) Two dead knobs removed.** `ct_committed/econ/peak_hr_override` **DELETED**
(rule 26): armed at 1.1/1.2/1.4 on **all 119 bundles in all six ISOs** and
**reachable on none** — both readers sit inside the `else` of `if offer is not
None` gated on `CT_CHP`, and every bundle carries a truthy
`offer_curve_by_group["CT_CHP"]`. Rule 26 was made *affordable* by
`_CACHE_KEY_RETIRED_FIELDS`, which re-inserts a deleted field at its historical
default **inside `cache_key()` only** — so deleting orphans no cache and re-pins
no literal. `caiso_ra_min_load_frac` is now **CAISO-scoped** (rule 25): inert
elsewhere, but a CAISO-fitted 0.26 was riding all 119 bundles' recipes.

**(5) C3c 2024, measured not proposed.** Both LI import paths saturate together
(`NYC>Long_Island` 275/275, `NYISO_external>Long_Island` 1200/1200) while the
mainland clears $72–75. The pin is **energy-side** (`reserve_price` 0.0, no LI
family binds in 2024) and its marginal unit is **`7146_1`, an OIL tranche** —
the only part-loaded LI generator of 132 — with **596.9 MW idle** at the annual
peak-price hour. The same fleet/curves reach $503.74 (2023) and $489.62 (2025),
so **2024 is not a missing-mechanism year**; it never calls the next oil rung.
**No lever proposed.**
`results/calibration/FINDING-nyiso114-reserve-family-sidecar-2026-08-03.md`.

**STATUS 2026-08-02 (nyiso-113) — THE MATRIX-GAP SWEEP, and the queue's own
blind spot measured.** Keeper `2026-08-02-nyiso112-ramp-plus-peaker` → **`2026-08-02-nyiso-113-li-locational`**.
nyiso-112 found a promotable mechanism only because it had no matrix row; this
session made that a census. **25 `nyiso_*` fields absent from the matrix, 5
prose-only, and 17 of them ARMED ON THE KEEPER WITH NO CELL ANYWHERE** (four
declared in the keeper's own DOF ledger and still cell-less). CI never caught it:
`check_mechanism_matrix.py`'s diff gate only fires on fields **added in the same
PR**, so everything predating the gate is structurally invisible to it — a
standing blind spot in *every* ISO column. **13 rows added, 1 cell updated.**

Three cells adjudicated **with no solve spent**, each on NYISO's own data:
`nyiso_east_reserve_families` **→ I** (provably inert by domination algebra —
`east_10min_spin` 330 MW is dominated by `nyc_10min_total` 500 MW by 170 MW and
by `east_10min_total` 1,200 MW by 870 MW; `east_30min_total` 1,200 MW by
`seny_30min_total` 1,300 MW by 100 MW); `measured_ramp_capability` **U → I**
(fleet 10-min ramp 12,318.4 MW = **18.8×** the 655 MW NYCA spin requirement);
`nyiso_spin_reserve_online` **→ I** (nyiso-110's solved verdict finally has a
cell).

**`nyiso_li_locational_reserve` SOLVED, LIVE and PROMOTED — cell K, keeper `2026-08-02-nyiso-113-li-locational`.** The
published Zone-K ladder the model omits entirely (rule 14, zero DOF). It clears
the rule-19 gate on measurement: not dominated (no armed family is Zone-K
scoped), and the nyiso-110 hydro-slack refutation **cannot reach it** — NYISO
hydro is 100 % upstate and **Long Island carries exactly 0.0 MW**. K2 is
**byte-identical** (0.0 MW over 122,640 class-hours × 3 yr) and the family binds
**exactly where its own requirement says it should**: Zone-K headroom falls below
the hourly requirement in exactly 5 hours of 2025 (h4193–4195, h4217–4218 — the
June 24–25 event) and 0 hours of 2023/2024 once the on/off-peak step is honoured;
the solved dual moves in exactly those hours. Effect small (2025 LI max
483.37 → 489.62), **C3c UNCHANGED at 3/0/14**, zero slack and dump. Determination
**CALIBRATED-WITH-CAVEATS**: no kill gate fires and **every scored criterion is
identical to the same-HEAD control's** (C1 14/14 all / 10/10 free, C2, C3a, C3b,
C4, C6, C7, C8 PASS in both arms), ledger 29 → 30 with `n_residual` 6. Promoted
on rule 1 / rule 14, not on gate movement.

**C3c, item 2 of the brief — the received reading is INVERTED by measurement.**
The 2023-05-01 227-3 phase removes **203.1 MW of which 145.5 MW (72 %) is Long
Island**; the 2025 increment is **14.5 MW, all NYC, none on LI**. The 2023 phase
did *not* do nothing — 570 LI hours moved, all inside the ozone window, LI max
400.07 → 503.74, >$250 7 → 10 — it just did not cross the $300 line C3c counts.
**2024 is the genuinely inert year and its three highest LI hours are pinned at
$297.54 in both arms, $2.46 below the gate.**

**TWO METHOD CORRECTIONS THIS SESSION OWES ITS OWN RECORD, both general.**
(i) The pre-registered K3/K4 gates were specified on the per-zone
`reserve_price`, which is a **system-level `(T,)` series broadcast identically to
every zone** — 0.0 across zones by construction, incapable of observing a
locational dual. The arm's first reading ("INERT") was an artifact; this
**retracts** the screen's "no locational family has ever bound" claim (the
east-families domination verdict is untouched, being arithmetic).
(ii) **A capacity-vs-demand screen is not a headroom screen** for an importing
zone with an idle-allowed reserve class: Zone-K quick-start headroom never falls
below **3.2×** its 120 MW requirement despite LI peak demand exceeding Zone-K
thermal nameplate. **Standing gap for all six ISOs: no bundle persists a
per-family reserve dual** (`DispatchResult.reserve_price_by_family` is discarded
at persist time), so no locational family's binding is observable from a
committed bundle anywhere.
`results/calibration/FINDING-nyiso113-matrix-gap-sweep-2026-08-02.md`.

**STATUS 2026-08-02 (nyiso-112) — THE FIRST C3c MOVEMENT SINCE THE QUEUE WAS
DECLARED EXHAUSTED, from a mechanism that was never on the queue.** Keeper
`2026-08-02-nyiso112-ramp-plus-peaker`. The lever is
**`nysdec_peaker_rule_availability`** — NYSDEC 6 NYCRR Subpart 227-3, the
ozone-season NOx cap on simple-cycle turbines, applied per unit from the
curated Gold Book compliance schedule as an **availability-only** overlay
(rule 13, forward story to the 2030 NYPA phase-out). It was invisible rather
than adjudicated: **no matrix row at all** (rule 28(c) gap), armed exactly once
at nyiso-46 inside a three-mechanism probe that stayed a probe for unrelated
reasons, **no rejection anywhere in the record**, and every bundle since read
`false`. Rule 19 was checked by measurement — the CAMPD outage overlay does NOT
already zero these units (the restricted GTs run inside their own windows on
the superseded keeper's own dispatch). **Result: C3c 2025 moves 7 → 14 hours
>$300 against a measured 42** (0.17× → 0.33×; 2023/2024 unchanged at 3/0), with
C3a in band in all three years and 2025 moving *toward* band centre, K4 window
fidelity exact (out-of-window delta 0.0 MWh every year), zero slack and zero
dump. **The caveat is not retired** — the model still under-produces the tail —
but its worst year improves for the mechanism's own dated reason (the
2025-05-01 second phase removes downstate peaker availability in exactly the
hours and zones nyiso-92/94 measured the tail in), never sized to the residual.
Two arms registered: `2026-08-02-nyiso112-dec-peaker-rule` (single delta on
nyiso-109) and the keeper `2026-08-02-nyiso112-ramp-plus-peaker` (the same
delta on the nyiso-111 ramp keeper), each attributed against the same
zero-delta control. `PREREG-nyiso112-nysdec-peaker-rule-2026-08-02.md`.
**Standing lesson for every ISO lane: the exhausted-queue finding was true of
the queue, and the queue was incomplete — a solve-affecting field with no
matrix row is a mechanism nobody can see.**

**STATUS 2026-08-02 (nyiso-111) — the CROSS-ISO TRANSFER sweep: two candidates
REFUSED ex-ante on NYISO's own data, one SOLVED.** With the in-LP
reserve-formation family exhausted (nyiso-110) the queue held no peak-half
lever, so this session went to the **cross-ISO transfer candidates** — the
matrix's `U` cells where another ISO carries a `K` — and adjudicated the three
that are live at NYISO. Two die before a solve is spent, each on NYISO's own
measurement rather than on analogy (rule 25 `[R-ISO-SCOPE]`):

* **`temp_dependent_derate` `U → G`** (CAISO/MISO/NEISO keeper; PJM `R`). The
  miso-101 identification re-run on NY CAMPD **does not identify**: 2 of 15
  candidate cogens clear the floor, the capacity-weighted p50 within-day slope
  is **−0.00745/°C — the wrong sign** (capability rising with temperature),
  the near-pinned plant (loading 0.80) measures **−0.000086 at r = 0.006**,
  and the **phase validation fails at best lag −5 h** against MISO's confirmed
  lag 0. The estimator is reading NYC's air-conditioning *dispatch* shape, not
  an ambient capability response, and rule 25 forbids importing the literature
  slopes pjm-95 already refuted.
* **`hydro_ror_split` `U → G`** — this is **item 8's blocked classifier review,
  answered**. See item 8 below.
* **`ramp_envelopes` (`ramp_limits`) — PRE-REGISTERED AND SOLVED.** The pjm-140
  transfer; NYISO's artifact derives for the first time (77 rows / 48
  well-observed plants; CC up-envelope median **0.49 × pmax**, ST 0.42, CT
  0.92) and the bound-against-the-bound pre-check fires: **5,226 of 543,058
  group-transitions (0.96 %) cross the measured envelope carrying 225,117 MWh
  of infeasible ramping** in 2023, a crossing rate **2.1–3.0× PJM's** and ~6×
  PJM's relative to each fleet's own energy. Honouring pjm-140's all-ISO
  lesson, the class-aggregate test is reported as **uninformative** (1 hour of
  26,280), not as support. `PREREG-nyiso111-ramp-envelopes-2026-08-02.md`
  (committed before any solve).

**STATUS 2026-08-02 (nyiso-110).** The peak half is **DECOMPOSED, no LP**, on the
keeper's own sidecars + NYISO's own posted AS prices
(`scripts/probes/_nyiso110_peak_half_decomposition.py`): it is **dominated by
missing everyday reserve-price formation** — the keeper's co-opt reserve dual is
> $0 in **17/6/34 hours** of 8,760 while the measured DA spin price is > $1 in
**100 %** of peak-window hours (LW mean $9.72/$8.62/$17.46); the peak−trough
reserve differential covers **64–89 %** (DA) / **97–131 %** (RT, upper bound) of
the missing swing at hour-level passthrough slope ≈ 1. **The C3a PASS is a
cancellation**: strip the measured spin content and the model's energy side
over-prices BOTH ends by +$3–7 — so the level gate actively penalizes the
structural repair (full-content formation would land C3a-2023 ≈ +15 %), the
sharpest input yet to the **open owner amplitude-criterion call** (surfaced, not
decided; scorer untouched). The energy-side residual (~10–35 % of the missing
swing, DA) is the flat offer surface (peak marginal set = `econ` 83–85 %, the
trough's own family) plus the hydro over-peak-shave (model thermal at peak
0.936× measured — **item 8's territory**, not a new lane). **The lever:** the
flag-only **`nyiso_spin_reserve_online`** single-delta arm is **PRE-REGISTERED**
(`PREREG-nyiso110-spin-online-peak-formation-2026-08-02.md`, pushed before any
solve) — off-queue with cause stated (this queue holds no peak-half lever), the
nyiso-84 adjudication superseded on both its grounds by new evidence (new
target: everyday formation, not C3c depth; new supply state: the E4 census on
the repaired-hydro keeper shows hydro zero-cost headroom covering the 655 MW
spin requirement in only **36–51 %** of peak-window hours vs 82–89 % of all
hours, confining the gate's bite to the peak and dissolving the recorded
overnight-GT-forcing objection in the hours it fired in). Kill P1 is the
pre-registered **C3a-2023 un-cancellation breach** (> +10 %); P4 re-kills on the
nyiso-84 forcing signature; K3's liveness floor (500 dual-hours/yr) routes an
under-forming arm to **INERT**.
`results/calibration/FINDING-nyiso110-peak-half-decomposition-2026-08-02.md`.

**OUTCOME, same session (solved at the rebased HEAD; registered
`2026-08-01-nyiso110-control-zerodelta` / `2026-08-02-nyiso110-spin-online-inert`):
the arm is INERT by its own K3 rule** — reserve-dual hours identical to control
(17/6/34 of 8,760), C3a +0.006 pp, swing shares unchanged to 3 dp; K2 = 0.0 MW
(the ercot-150 landing is NYISO-inert). Root cause, corrected on the record
(FINDING §10): the class-2 online gate is an **aggregate** ρ·output row that
reserve-eligible hydro's own output (2–5 GW × ρ ≥ 0.5) keeps slack in every
hour, with idle quick-start capacity still admissible per-gen — the E4 census
had tested the per-gen headroom binder. The same arithmetic **refutes the
nyiso-84 class-widening successor ex-ante** (widening only adds slack; excluding
certified NYPA hydro would falsify real eligibility, rule 14). With reserve
offers unpublished (rule 13/21), withholding a rule-19 stack, MIP forbidden and
congestion G, **the in-LP reserve-formation family at NYISO is EXHAUSTED**:
`diurnal_price_amplitude` NYISO **O → G** (the PJM/MISO no-build class). The
peak half re-opens ONLY behind (i) the owner amplitude-criterion call — now
carrying both the cancellation fact and this exhaustion — (ii) an owner-funded
reserve-offer / sub-hourly data intake, or (iii) item 8's Robert Moses
resolution (the separate energy-side hydro leg). Keeper unchanged; item 4 stays
blocked (the candidate joint summer lever died with the arm).

**STATUS CHANGE 2026-08-01 (nyiso-109).** NYISO recovers **NOT-YET -> CALIBRATED-WITH-CAVEATS**,
and unlike nyiso-108 this promotion is the pre-registration's **OWN verdict** — every construction
gate (K1-K6) and every kill gate (P1-P5) passed, no owner override was needed or used. The lever is
**`gas_offer_margin_zonal_anchor`**: the gas-offer net-revenue margin's identification anchor
resolved PER ZONE, with **zero free parameters**. `apply_gas_offer_margin`'s own identity — at
`fuel == anchor` the reformed offer reduces EXACTLY to the registered band multiplier — is a
statement about a unit's OWN delivered fuel, but the ISO anchor is derived from
`data.fuel.trajectories._gas_series`, which is ISO-LEVEL and does not carry the per-zone basis the
solve applies afterwards. NYISO's zonal basis leaves the REFERENCE zone (Capital_Hudson / Iroquois
Z2) unchanged and shifts NYC (Transco Z6 NY) and Upstate_West (Tenn Z4 200L) strictly DOWN, so two
zones carrying **67.6 % of NYISO load** were pricing their markup at a fuel level they never pay.
Zone anchors (Upstate_West 2.0346, NYC 2.7612, reference 3.9046 unchanged) are the SAME measurement
as the ISO anchor evaluated per zone by the same derive script. **C3a 2023 +10.21 % -> +7.51 %**
clears the +/-10 % band; C3a PASSES in all three years; C3c is bit-unchanged and stays the SOLE
ledgered caveat; C1 stays 14/14 all-class, 10/10 free-class.

**TWO handoff premises are CORRECTED by measurement, and both are worth carrying forward.**
(1) The defect is **NOT 2023-specific**. The residual is a COMPRESSED price distribution present in
all three years — the model reproduces only **69/49/45 %** of the measured trough->peak swing, with
the trough over-priced by **+7.3/+5.5/+8.7 $/MWh** and the peak under-priced in 2024/2025. 2023
failed alone only because it is the mild year whose peak error is ALSO positive, so nothing
cancelled the trough excess. This is the same defect PJM diagnosed at pjm-141, measured
independently on NYISO's own data (rule 25). nyiso-109 corrects the TROUGH half; **the PEAK half is
open and is the named successor** (C3a 2025 moves -8.73 % -> -9.64 %, reported not hidden).
(2) The congestion route is **REFUSED ex-ante on NYISO's own measurement**, not on analogy:
`measured_interface_limits` NYISO `U -> G`. The premise is real (the model's link separates in
12.0/1.3/1.1 % of hours against a real 60.3/54.8/38.2 %), but the REAL `CENTRAL EAST - VC` sits
within 50 MW of its posted limit in only **0.8/0.1/0.2 %** of hours (TOTAL EAST / UPNY CONED /
SPR-DUN-SOUTH: 0.0 %), and the model's monthly TTC already tracks the measured monthly mean limit —
so the posted limit is not what produces the real separation (marginal losses + sub-interface nodal
constraints, neither representable at five-zone grain; rule 14's misalignment clause).
`results/calibration/FINDING-nyiso109-zonal-margin-anchor-2026-08-01.md`.

**STATUS CHANGE 2026-07-31 (nyiso-108).** NYISO regressed CALIBRATED-WITH-CAVEATS -> **NOT-YET** by an
**explicit owner override** of that session's own prereg §6 (which pre-committed no-promotion-on-new-FAIL).
The hydro input repair — a rule 14 [R-ACCURATE] correction with ZERO free parameters, arming the pair
`--hydro-backfill-year 2024` + `--hydro-eia930-monthly` that four of the six keepers already carried —
restored the 2025 LP hydro fleet from **3 plants / 21.0482 TWh to 147 / 24.0589**, and in doing so removed
~1.55 TWh of **phantom zero-MC 2023 hydro** that was **suppressing a real 2023 fossil over-pricing**.
C3a 2023 crosses **+8.6 % -> +10.2 %** against a ±10 % band. Rule 14 forbids reverting the accurate input
to restore the PASS; the miss is the **named successor, nyiso-109** (offer-stack / fuel-basis root cause,
NOT the hydro input). Same signature PJM promoted at pjm-143. **C3c is BIT-IDENTICAL** across arm and
same-HEAD control (3/0/7 h vs 10/12/42), so the nyiso-104b **C3c frontier declaration stands on its own
evidence** and no caveat slot is spent — what lapsed is its *premise* that C3c was the sole blocker.
NYISO is no longer at a frontier in the sense of 'options exhausted'; it is back in active calibration
with a concrete open item. C1 remains 14/14 all-class, 10/10 free-class.
`results/calibration/FINDING-nyiso108-hydro-input-repair-2026-07-31.md`.

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
   *nyiso-110 note (2026-08-02):* the peak-half decomposition gives this item's
   blocker a measured shape — the DJF peak miss **exceeds** the DJF reserve
   content in 2023/2025 (+8.08 vs 9.43 is within it, but +32.00 vs 18.72 in
   2025 is not), so a real winter-specific non-reserve component exists; and
   the pre-registered spin-online arm, if it lands, IS a summer-capable
   scarcity lever (measured JJA spin content 10.7–28.8 at peak), which is
   exactly the joint condition this item waits on. Sequencing stays: this
   item re-opens only AFTER the nyiso-110 arm's verdict, never beside it
   (single-delta discipline).
5. ~~**`unit_outage_short_windows`** — derive for NYISO; cheap grain test.~~
   **CLOSED 2026-07-28 (nyiso-93): INERT ex-ante, no solve.** The detector is
   coal-only and NYISO has no coal — 0 coal unit-years in NY+NJ CAMPD 2023-25
   (last NY coal MWh: Somerset/Kintigh 2020), 0.0 MW COAL `plant_group` in the
   model fleet; both extracts derive to 0 rows and both overlays return empty
   dicts. A gas-CC scope extension is the only path to a binding window here
   and needs its own charter (layup confound).
   `docs/FINDING-nyiso93-unit-availability-windows-inert-2026-07-28.md`.
6. ~~**`st_gas_mustrun_p25_level`** — re-ground the in-city ST_GAS persistent
   bases on measured levels (D-2 ST_GAS 31% forced in 2024).~~ **CLOSED
   2026-07-31 (nyiso-105): INERT ex-ante, no solve, cell `U → I`.** Four
   independent measured blockers, any one decisive. (a) The **single flag is a
   no-op by construction** — `arrays.py:1750-1753` gates the p25 block on
   `st_gas_mustrun_p25_level` **and** `st_gas_mustrun_per_plant`, and the keeper
   carries the latter `False`, so the queue's own suggested arm would have
   solved a bit-identical control. **The arm is the pair, not the flag.** (b) The
   **pair is a no-op on today's artifact**: `thermal_tranche_online_frac("NYISO")`
   returns **0 rows** because `thermal_tranches_NYISO.csv` has **no `online_frac`
   column**, so 0 of 11 ST_GAS plants clear the runtime's `level>0 AND frac>0`
   gate — the *level* is there (11 p25 rows), the *window* is not. Census: MISO
   16/16 populated, CAISO 0/3, PJM 0/10, NYISO and NEISO no column. (c) Making it
   fire is a **fleet-wide re-basing, not a mechanism arm** — re-deriving at HEAD
   adds the column but also moves `p25_cf` on 32/78 rows (max 83.6 pts),
   `committed_pct` 36/78 (max 27.2), `median_cf` 37/78, `online_hours` 46/78,
   `peaking_pct` 8/78, i.e. the tranche shares the whole NYISO offer curve is
   built from; it needs its own rule-23 charter and control arm. It also emits
   **`p25_cf > 100 %`** on two ST_GAS plants (S A Carlson 142.2, Astoria 101.7)
   against a `thermal_tranche_p25_level` accessor with **no upper clamp**
   (`committed_pct`/`mustrun_pct` *are* capped at 0.70/0.60) — **a clamp is a
   prerequisite** for any future refresh. (d) **The premise was wrong here.**
   "measured levels instead of fitted fractions" describes MISO's incumbent
   (`committed_pct` = P5-of-online LSL); NYISO's surviving NYC/LI limbs are
   **already** measured p25 — *"persistent 24h base: base_24h (when-available
   cool-day CF p25)"*, floor_pct 0.1750 / 0.2620. And rule 19 `[R-ONE-MECH]`
   independently forbids the stack: ST_GAS already carries `reliability_floor`
   (24.2/27.8/19.4 % of class) **plus** `nyiso_gas_commitment_bridge`
   (1.8/2.8/2.5 %), with D-2 already recording 2024 ST_GAS **30.6 % > 30 %**; the
   compliant replacement path is `nyiso_incity_commitment_obligation`
   (`iso_configs._INCITY_OBLIGATION_OWNED_LIMBS`), a different mechanism under a
   different charter. Successor is the chartered artifact refresh, **not** a
   lever-queue entry.
   `results/calibration/FINDING-nyiso105-stgas-inert-seam-live-2026-07-31.md` §A.
   **Its clamp PREREQUISITE is DONE (2026-07-31, nyiso-106), and nyiso-105
   understated the defect: the above-nameplate `p25_cf` is live in the
   COMMITTED artifacts, not only the refreshed one** — MISO 17 rows, NEISO 3,
   NYISO 2, PJM 3, max 150.0 (`derive_thermal_tranches.py:555` clips
   available-CF at 1.5 and `p25_cf` inherited that ceiling while
   `committed_pct`/`mustrun_pct` were capped at 0.70/0.60). Clamped at **1.0
   (nameplate)** in BOTH the deriver (`_P25_CAP`) and the accessor
   (`campd_bins.thermal_tranche_p25_level`, so a stale artifact — every
   committed one — cannot inject an impossible floor). The ceiling is 1.0 and
   NOT `_COMMITTED_CAP`: the defect is physical impossibility, and since
   p25 >= p5 a 0.70 cap would collapse p25 onto the committed level. Rule 23
   `[R-FROZEN-DERIVE]`: physical-admissibility bug fix, not a residual
   re-derivation. **Measured inert on every live keeper** — the only consumer
   is the ST_GAS floor, the sole breaching ST_GAS row anywhere (NEISO Merrimack
   150.0) is in an artifact with no `online_frac` column, and MISO (the one ISO
   arming the pair) tops out at 67.4 % over all 16 armable rows; after the clamp
   0 levels exceed nameplate in any ISO, 149 tranche tests pass. **The refresh
   itself is still NOT done and stays chartered** (control arm + solve).
   `results/calibration/FINDING-nyiso106-solar-benchmark-vintage-2026-07-31.md` §C.

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
8. ~~**`hydro_ror_split` NYISO classifier review** — blocked on answering the
   Robert Moses Niagara hybrid label (Run-of-river/Peaking, 52% of fleet MW)
   from the treaty scenic-flow schedule; never arm on the CAISO-reviewed rule
   alone.~~ **CLOSED 2026-08-02 (nyiso-111): the review is ANSWERED and the
   transfer is FALSIFIED ex-ante by NY hydro's own metered output — cell
   `U → G`, no solve.** The committed `curate_hydro_plant_modes` rule 1
   (Peaking / Intermediate Peaking → shapeable; every other label, including
   every hybrid, → flat) applied to EHA FY2024 on NYISO's own BA flat-pins
   **3,420.4 of 4,682.0 MW = 73.1 %** of conventional-hydro MW — Robert Moses
   Niagara alone 2,429.1 MW (51.9 %) — leaving a shapeable bound of
   **1,261.6 MW**. A flat-pinned plant contributes exactly **zero** diurnal
   swing by construction, so that is an upper bound on the model's achievable
   hydro swing under the arm, and **the measured swing exceeds it in every
   year**: EIA-930 `NYIS` `NG: WAT` hour-of-day mean-profile swing
   **1,291.9 / 1,396.8 / 1,792.2 MW** (1.02 / 1.11 / 1.42×) and median-**day**
   within-day range 1,496 / 1,495 / 1,929 MW (1.19 / 1.19 / 1.53×). `NG: WAT`
   is conventional-only for this BA (nyiso-107 re-verified NYISO's absence
   from `EIA930_PS_FOLDED_INTO_WAT`), so Lewiston and Blenheim-Gilboa are not
   in the series.
   **The label was never the problem — the reading of it was.** EHA itself
   records the Niagara project's peaking machinery as its **own separate
   plant** (Lewiston, EIA 2692, `Mode = Peaking`, `PS_MW` 240, same
   `Water = Niagara River`) alongside Robert Moses Niagara (EIA 2693,
   `Run-of-river/Peaking`, `CH_MW` 2,429.1). `Run-of-river/Peaking` therefore
   describes the **powerhouse's hydraulics**, not the project's shapeability,
   and rule 1's gloss ("a reregulating/RoR powerhouse cannot chase price
   whatever its upstream neighbours do") is a CAISO-reviewed reading that NY's
   own metered hydro falsifies. The treaty scenic-flow schedule the queue
   entry asked for is not needed to decide this and cannot rescue it: it would
   bound *seasonal daytime diversion*, not restore the 1.3–1.9 GW of within-day
   swing the flat pin deletes.
   **Direction is wrong too, and the real defect is an order of magnitude
   smaller.** The nyiso-110 E3 over-peak-shave is confirmed by an independent
   construction but is modest: the keeper's hydro exceeds measured at h17–19 by
   **+293 / +242 / +204 MW** (model hod swing 1,507 / 1,541 / 1,721 vs measured
   1,195 / 1,292 / 1,593 MW; phase correct — model peak h18/h19/h19 against
   measured h19; annual volumes pinned to 4 dp). Removing 3.4 GW of shaping
   capability to correct ~250 MW is not a repair. **Successor, chartered not
   armed:** a *bounded* within-day shaping constraint (a Lewiston-class
   reservoir-energy bound) — a new mechanism with its own identification, never
   this transfer.
   Probe: `scripts/probes/_nyiso111_hydro_ror_split_screen.py` →
   `results/calibration/_nyiso111_hydro_ror_split_screen.json`.
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
10. ~~**Keeper-lineage cleanup:** drop `dual_fuel_oil_reattribution` from the
    NYISO recipe metas (CLI already pins it NEISO-only; zero dispatch delta,
    removes a known recording-basis artifact from the sidecars).~~ **STRUCK AS
    WRITTEN 2026-07-31 (nyiso-105) and RE-OPENED as a *scored* cleanup.** The
    entry is half right, and the half it gets wrong is the half that mattered.
    **The CLI pin does not make it inert here:** the CLI channel really does read
    `None` (`run_calibration_full.py:10704`), but the keeper lineage carries the
    flag through the generic `prb_overrides` dict, so the solved
    `scenario_config.dual_fuel_oil_reattribution` is **`true`**. **The dispatch
    delta IS zero, now proved rather than asserted** — two lines: structurally,
    `dual_fuel_oil_mask` has exactly two consumers, `build_winter_fuel_budget`
    (gated on `neiso_winter_fuel_inventory`, `False` on this keeper) and
    `_dispatch_frame(oil_switch_mask=…)`, which only does
    `klass_col[flat] = "oil"` *after* the solve; and empirically, every LP input
    (`mc_base`, `fuel_prices`, `pmax`, `pmin`, `heat_rate`, `availability`,
    `min_gen`, `demand`) is **byte-identical** with the flag flipped in all three
    years. **But the RECORDING-BASIS delta is not zero and is material:** the
    relabel moves **0.1119 / 0.3511 / 1.1508 TWh** (53 / 155 / 715 h) into a
    recorded `oil` class — 1.6139 TWh over three years, the same order as an
    entire scored class (`CT_PEAKER` = 0.341 / 0.257 / 1.067 TWh) — and C1/C7 are
    scored from exactly those sidecars. Dropping it is still correct under rule
    14 (nyiso-99 showed the basis is wrong for NYISO: Jan-2025 parity switching
    relabels 0.80 TWh against a measured `NYIS` `NG: OIL` of 0.031 TWh), but it
    is **dispatch-neutral and scoring-basis-changing**, so it must ride a re-solve
    with its own control and be scored — not silently edited into the metas.
    `results/calibration/FINDING-nyiso105-stgas-inert-seam-live-2026-07-31.md` §C.
11. ~~**2025 `solar` +437.2 % benchmark audit** — the standing benchmark caveat.~~
    **CLOSED 2026-07-31 (nyiso-106): a SURVEY-COVERAGE ARTIFACT, falsified, root
    cause fixed forward, no solve.** The scoped premise (gap-audit `NG: SUN` the
    nyiso-98 way) is **moot**: EIA-930 `NYIS` `NG: SUN` is **identically zero**
    in every hour of every year (8,760/8,760 in 2023; 2,190/2,190 midday zeros
    every year) — structurally absent, not zero-coded-gappy, which is exactly why
    `results.calibration._EIA923_OVERRIDE` routes NYISO solar's scoring to
    **EIA-923**. The defect is in that vintage: **2025 carries 8 of 565 NYIS solar
    plants** (0.6617 TWh vs 2.9008 in 2024; the national vintage is 3,427 plants
    vs 13,210). The 8 are a **strict subset** of 2024's and on a like-for-like
    basis they **GREW** (0.2527 -> 0.6617 TWh; Morris Ridge 20,861 -> 313,307 MWh).
    **Independently falsified** against NYISO's own MIS P-63 — which publishes NO
    separate solar category (verified live: seven categories, solar inside `Other
    Renewables`), so the instrument is the per-day night-baseline/daylight-bulge
    decomposition: **0.212 / 0.577 / 0.994 TWh**, monotonic growth against a 923
    series claiming a 77 % collapse. **Two purpose-built guards both miss it:**
    `audit_eia923_completeness` audits GAS+COAL only (*"renewables are scored on
    EIA-930"* — true for every ISO except the one `_EIA923_OVERRIDE` pair, and
    `solar` is absent from the committed NYISO completeness part), and
    `_backfill_renewables_eia930` bails on `if ann930 <= 0.0: continue`, keying
    its repair on the very series that is zero. Everything ELSE in NYISO 2025 was
    repaired (wind 7.049 / hydro 24.104 via the 930 swap, biomass 0.672 via
    carry-forward) — solar 0.662 was the single unrepaired cell. **Fixed** by
    routing a class with no EIA-930 authority to the same prior-year
    carry-forward biomass already uses: zero new parameters, gated on the
    existing `_EIA923_VINTAGE_COMPLETENESS_FRACTION`, 2023/2024 exact no-ops
    (completeness 1.05/1.04), 2025 solar **0.6617 -> 2.5673 TWh** (+437.1 % ->
    +38.5 %). Blast radius measured across 6 ISOs x {wind,solar,hydro} x 2023-25:
    **NYISO solar is the ONLY zero-930-authority cell.** Forward-acting (bench
    parts are built from the bundle's solve-time `eia923` input), so no committed
    keeper moves. **Consequence for the queue: the 2025 solar statistic is BARRED
    from sizing or judging any mechanism**, and `hydro_budget_nameplate_aware` is
    re-framed before it was ever sized — NYISO hydro's 2025 actual (24.104) is the
    **EIA-930 swap** while 2023/2024 (28.031 / 27.465) are **EIA-923**, so the
    "+1.3/+1.3/−12.7 %, miss ENTIRELY in 2025" shape is measured **across a
    benchmark-basis switch**; any hydro lever must first put all three years on
    one basis and re-measure what survives.
    `results/calibration/FINDING-nyiso106-solar-benchmark-vintage-2026-07-31.md`.
11b. **NEW (nyiso-106, REPORTED not fixed) — `OTHER` is injected on one basis and
    scored on another; needs a CROSS-ISO charter.** Same family as item 11.
    `_reconciled_mustrun_class`'s docstring makes it the single source of truth
    for an injected residual class that "**both the benchmark and the must-run
    injection**" consume — but `_backfill_renewables_eia930`'s carry-forward block
    is hard-coded to `biomass`, so `OTHER` is injected at the carried-forward
    level and scored against the raw truncated vintage. NYISO 2025 is decisive:
    model OTHER **1.9483** TWh **is** the carry (2.2014 x 0.8850 = 1.9483, exact
    to 4 dp) against a benchmark of **1.7487** (10 plants vs 76) — **on a
    consistent basis the +11.4 % is exactly 0.0 %.** Fix is one line in shape
    (route the block through `_reconciled_mustrun_class` over
    `("biomass", "OTHER")`, which also gets the pumped-storage holdout right),
    but it moves **three ISOs**: CAISO +0.4173, NYISO +0.1996, NEISO +0.1618 TWh
    (ERCOT/PJM/MISO are above 0.90 completeness, so nothing fires). Left for its
    own charter rather than re-scoring CAISO and NEISO from a NYISO session.
    **Meanwhile NYISO `OTHER` 2025 is barred from sizing or judging a mechanism.**
    (`ST_CHP` 2025 +85.0 % needs nothing — already audited `incomplete`,
    retention 0.667, and C1-SKIPPED.)
    `results/calibration/FINDING-nyiso106-solar-benchmark-vintage-2026-07-31.md` §E.
    **STATUS 2026-07-31 (nyiso-107): put to the owner and DEFERRED.** A NYISO
    session asked for the cross-ISO scope and the owner declined it — the entry
    stays chartered for a session that owns re-scoring CAISO and NEISO. The bar
    on NYISO's `OTHER` 2025 statistic is unchanged.
12. ~~**`hydro_budget_nameplate_aware` NYISO transfer** — the lever item 11's
    tail re-framed before it was ever sized.~~ **CLOSED 2026-07-31 (nyiso-107):
    PROVABLY INERT, no solve, cell `U → I` — and item 11's re-framing is itself
    SUPERSEDED on its central claim.** Item B's stated kill condition was *"put
    all three years on one basis; if little of the −12.7 % survives, the lever is
    dead"*. **The miss survives every consistent basis**: all-EIA-930 gives
    **+5.76 / +3.93 / −12.68 %** (2025 bit-unchanged — it was already there — and
    2023/24 get *worse*), all-EIA-923-carry-corrected gives
    **+1.26 / +1.33 / −13.41 %**. The benchmark-basis switch is real but is **not**
    the cause, because the benchmark is the **repaired** side.
    **The defect is the INPUT.** The keeper carries `hydro_backfill_year=None`
    and `hydro_eia930_monthly=False`, so its **2025 LP hydro fleet is 3 units /
    21.0482 TWh** — against 147 / 27.8750 in 2024, a **2.0 % plant retention**,
    max MW 4,587 → 3,343 — read straight off the truncated early release, while
    the benchmark IS repaired to EIA-930 **24.1039**. The model spends its budget
    **exactly** (21.0482 dispatched = 21.0482 budgeted, 4 dp), so the scored
    −12.68 % is arithmetically the truncation (`21.0482/24.1039 − 1`) with no
    dispatch behaviour in it. **The benchmark is independently falsified as
    CORRECT**: NYISO MIS **P-63 publishes `Hydro` as its own category** (unlike
    solar, which forced nyiso-106's bulge decomposition) and reads
    **27.1845 / 26.9763 / 24.2489 TWh**, agreeing with EIA-930 to
    **+1.30 / +0.74 / +0.60 %** every year — NY hydro genuinely fell ~10 % in
    2025, and the wrong number is the 923 raw **20.5582**.
    **The kill:** the lever is inert *structurally* — `load_hydro_budget:724`
    encloses the whole allocator in `if monthly_target_mwh is not None`, and
    `build_hydro_fleet:1084` leaves `target=None` unless
    `eia930_monthly`/`forecast_budget`, both `False` here, so the flag is never
    read — and *empirically*: the hydro fleet built at the keeper's exact
    settings is **BIT-IDENTICAL off vs on in all three years**. It is the third
    ISO to reach `I` for the same structural reason (MISO miso-109, PJM
    pjm-143): **any ISO with no level target gets `I` by construction**. It stays
    trivial even after its prerequisite — under `--hydro-backfill-year 2024` the
    allocator moves 3,683.8 MWh over 10 clipped plant-months, **0.015 %** of
    budget, annual total unchanged.
    **NEW CROSS-ISO FACT, chartered not armed.** Every ISO's 2025 EIA-923 hydro
    vintage is truncated (retention ERCOT 8.3 / CAISO 16.2 / PJM 13.9 / MISO 8.8 /
    **NYISO 2.0** / NEISO 3.0 %), but **four of six keepers arm the repair**
    (CAISO/PJM/MISO/NEISO all `--hydro-backfill-year 2024`; PJM+MISO have the 930
    pin internally refused for the PS fold) **and NYISO does not**. The only other
    holdout is ERCOT, whose hydro is 0.017–0.463 TWh/yr (immaterial), so **NYISO
    is the SOLE ISO running a MATERIAL hydro class (26.5 TWh/yr, ~18 % of generation)
    on an unrepaired truncated input.** Arming the pair moves **all three years**
    (−1.5668 / −1.1287 / +3.0143 TWh), and a 930 level pin would make the hydro
    **volume** statistic near-tautological (−0.17 % by construction, budget and
    benchmark becoming the same series) — admissible under rule 13 as an inflow
    budget that regenerates forward, but it must be **declared, not banked as an
    improvement**; dispatch **shape** stays the free output. Owner decision
    2026-07-31: **report + charter, do not arm from this session.**
    Related, re-confirmed independently: NYISO's absence from
    `EIA930_PS_FOLDED_INTO_WAT` is correct — `NG: WAT`/923-`HY` = **0.9448 /
    0.9606** (*below* 923 HY, the opposite of the MISO/PJM fold signature) and
    NYIS `PS` is net **negative** (−0.372 / −0.410 / −0.490 TWh), so pumping is
    netted, not folded in gross. The 2025 ratio inverts to 1.1452 purely by
    truncation — the `hydro_level_923_hy` trap, re-verified, still not quotable.
    `results/calibration/FINDING-nyiso107-hydro-input-truncation-2026-07-31.md`.

### 5.6 NEISO — keeper `2026-08-03-neiso-caiso156-meter-screen` (**keeper id corrected at neiso-78** — the header had gone stale at `2026-07-31-neiso-72-hy-window`, which caiso-159 SUPERSEDED-NOT-RETRACTED on 2026-08-03); **rule-28(c) column CLOSED at neiso-78 (item 5d)**; target: C3c (ledgered; FRONTIER DECLARED — **C3c CHARTER WRITTEN at neiso-75, 2026-08-02; its ONE lever REFUTED at Phase-0 at neiso-76, same day**); ~~item 6~~ CLOSED at neiso-71 and its capacity prerequisite ADJUDICATED-ARTIFACT at neiso-73; ~~item 7~~ EXECUTED-with-keeper at neiso-71; ~~item 4~~ EXECUTED-with-keeper at neiso-72; ~~item 8~~ REFUSED-at-screen at neiso-74 (premise inverted — the defect is diurnal price amplitude, not storage); ~~item 1~~ **SPENT at neiso-76 — both limbs refuted, no solve spent, `da_virtual_bids` NEISO `O`→`R`**

Keeper `2026-08-03-neiso-caiso156-meter-screen` (corrected at neiso-78; the
neiso-72 hydro-window mechanism and its C3c frontier declaration are carried
forward unchanged — caiso-159 changed only the shared measured CT heat-rate
artifact's content, per `frontend/data/backcast/keepers/NEISO.json`).

**The C3c frontier charter (neiso-75, 2026-08-02 — no LP):**
`results/calibration/CHARTER-neiso75-c3c-frontier-2026-08-02.md`, decomposition
probe `scripts/probes/_neiso75_c3c_decomposition.py`. The 43-hour RT tail miss
splits: the **systemic amplitude defect closes 13/43 hours and owns the 2025
gate alone** (gain restoration prints 25 h inside [10, 40], all on the five
real event days); the **2023 gate is measured-unreachable by any DA-type
formation** (9/10 winter hours RT-only; the real DA's own ceiling is 5 h vs
the 8-h gate floor) and is **routed to the owner** (accept the ledgered
caveat / winter-fidelity lane / representation change — charter §5); **2024
already passes** on the small-count rule. ONE lever chartered: **item 1**
(below), kills K1–K5 pre-registered, Phase-0 measurement-only. Against
interest: the keeper attestation's 2024 C3c event-day names are one calendar
day early (leap-year prose slip; raw SMD verified Jun-18/Jul-8/Aug-1/Dec-3;
data and scoring unaffected).

Frontier discipline: every named admissible mechanism in the winter/summer
scarcity family is already on record. Anything below needs its **own new
charter with a new measured identification** before a solve:

1. **DA-bid offer formation / DA depth charter** (`pjm_da_virtual_bids` form)
   — the named "new identification" class in the frontier note (oil-parity /
   import / DA-bid); NEISO publishes DA cleared/bid data to derive from.
   **neiso-74 gave this item a measured target** (item 8 below): the model's
   diurnal price amplitude is 24–30 % of measured with the level and the phase
   both correct, split ≈ −26 % on the daily peak and ≈ +33–41 % on the daily
   trough, stable 2023–2025. **CHARTERED at neiso-75 (2026-08-02) → matrix
   `da_virtual_bids` NEISO `U → O`.** The ONE recommended C3c lever:
   supply-conduct limb first (within-day peak-vs-trough movement of the
   submitted `hbdayaheadenergyoffer` book's non-fast-start body band — the
   corpus is already on disk, 1,058/1,096 days, 2025 event days verified),
   DA-depth limb second behind its own existence check. Kill rules
   pre-registered (charter §4): K1 movement floor $5/$5/$8 per year (≈ 25 %
   of the measured hod-range gap $18.93/$22.14/$31.17); K2 no
   price-conditioning; K3 nyiso-94 submitted-curve existence + miso-105
   λ0-attractor kill; K4 caiso-154 Algonquin fuel-tail exclusion (15 %
   relative); K5 event-day coverage. **Phase-0 is measurement-only; a solve
   arm needs its own prereg carrying gates G1–G5** (amplitude, C3c-2025
   count AND placement, neutrality, level band, C3b hard kill, LOYO). Honest
   ceiling, stated ex ante: this lever closes 2025 + the amplitude defect;
   it does NOT close 2023 (charter §2.4/§5).
   **PHASE-0 RUN AT neiso-76 (2026-08-02, NO LP, NO solve spent) → REFUTED ON
   BOTH LIMBS; `da_virtual_bids` NEISO `O` → `R`.** The measured sign is
   **opposite** to the charter's own theory of change.
   * **Supply-conduct limb — K1 FIRES in all three years.** Within-day
     movement of the submitted non-fast-start book is **−1.926 / −1.840 /
     −2.274 $/MWh** against bars of +5/+5/+8: the body band is offered
     *cheaper* at the peak than overnight. **72.8–73.9 %** of 227,033 paired
     asset-days are bit-flat and the p25–p90 of the movement distribution is
     exactly $0.00 — the median NEISO asset submits the identical curve at
     03:00 and 18:00. The band's own hour-of-day offer profile spans
     **$2.20 / $2.51 / $3.67** and *troughs* at HE19–20, against measured DA
     hod ranges of $25.96 / $28.96 / $44.47. Corpus 1,063 day-files
     (359/351/353). **K5 passes** (all five 2025 event days present, in the
     band). **K2 cannot rescue it** — the best admissible conditioned cell is
     negative in every year, and no month or tightness bin is positive.
     **K4 fires on 2025** (+24.1 % excluding the 34 Algonquin fuel-tail days)
     but only by moving the statistic toward zero. The fast-start band moves
     **−13.7 to −15.9** — same sign, larger.
   * **Demand-depth limb — K3(i) PASSES, K3(ii) does NOT fire, the limb dies
     on MATERIALITY.** ISO-NE *does* publish a submitted priced DA
     demand/virtual book (`hbdayaheaddemandbid`: FIXED / PRICE / INC / DEC,
     ≤50 (price, MW) segments, 165–219 GWh/day priced), so the nyiso-94
     blocker does not bind and NEISO is the **third** ISO with a submitted
     curve. λ0 misses the posted DA price by a median **$5.29** (bar ≤ $2) and
     the displacement share is **12.7 %** median (bar ≥ 30 %) — admissible,
     not an attractor. But **PJM's premise is FALSE here**: net virtual is
     **−0.41 / −0.25 / −0.24 GW at the peak** vs +0.13 / +0.02 / +0.07 at the
     trough, a midday virtual-*supply* convergence play (−1.34 GW at HE13), so
     arming it faithfully **subtracts $2.76 / $1.37 / $1.60** of diurnal
     spread. Ladder semantics **identified, not assumed** (no cleared-MW
     column exists, so the readings were crossed against the published hourly
     DA cleared demand): cumulative brackets it in **0 of 900** hours,
     incremental-with-INC-netted in **898**.
   * **Four ISOs, four answers** (rule 25 doing real work): PJM `K` premise
     true, MISO `G` attractor, NYISO `G` unidentifiable, NEISO `R`
     identifiable, non-attracting, net short at the peak.
   * **No arm pre-registered.** C3c-2023 stays routed to the owner (charter
     §5); C3c-2025 keeps its neiso-75 sizing but loses its route. Evidence:
     `results/calibration/FINDING-neiso76-dabid-phase0-2026-08-02.md`; probes
     `scripts/probes/_neiso76_dabid_phase0.py`,
     `_neiso76_demand_limb.py`.
2. **Import-side scarcity identification** (HQ/NB tie behavior in tight
   hours) — second named class. **Ceiling bounded by the neiso-75
   decomposition (NOT chartered):** it is DA-type formation, and the 2023
   winter block it would target is 9/10 RT-only with the real DA's ceiling
   (5 h) below the gate floor (8 h) — it cannot close any C3c gate item 1
   doesn't. Remains an owner option for winter *fidelity* (the −$32
   Feb-4-2023 model-vs-DA day-level share), not for C3c (charter §3 L2/§5);
   `priced_interchange` NEISO stays `U` (the keeper runs fixed HQ tranches).
3. ~~**`measured_ct_heat_rates`** — audit-grade, no charter needed.~~
   **DONE at neiso-70 → `K`, PROMOTED to keeper** (2026-07-31). Same
   determination as the outgoing neiso-61 keeper (CALIBRATED-WITH-CAVEATS,
   0 FAILs, C1 all 12/12 · free 8/8, C3c bit-identical, DOF residual count
   unchanged at 5), with the CT_PEAKER `reliability_floor` forced share
   collapsing 0.396 / 0.274 / 0.068 → 0.201 / 0.074 / 0.027 — the class clears
   economically instead of leaning on its commitment floor. Evidence:
   `results/calibration/FINDING-neiso70-heat-rate-provenance-2026-07-31.md`.
4. ~~**`hydro_budget_nameplate_aware`** + `NG: PS` pin audit~~ — **EXECUTED at
   neiso-72 (2026-07-31) → `hydro_level_923_hy` NEISO `K`, PROMOTED keeper
   `2026-07-31-neiso-72-hy-window`.** The per-window treatment landed exactly
   as flagged: `EIA930_PS_SPLIT_COMPLETE_FROM` (seam measured to the hour,
   2024-11-07 00:00) refuses the `NG: WAT` pin for pre-split 2023/2024 (level
   → the units' own 923 `HY` filings) and keeps it for wholly-split 2025
   (bit-identical to control). Every criterion IDENTICAL to the neiso-71
   keeper; owner design sign-off (D over flat/splice/subtract-estimated-PS) +
   promotion authorization in-session. Named successors: storage-side PS
   cycling depth (measured 1.932 vs endogenous 0.497 TWh, 2025), bench hydro
   basis 2024 (the C1 actual is the folded 930 series), sizing the 930
   conventional under-count. Evidence:
   `results/calibration/FINDING-neiso72-hydro-ps-window-2026-07-31.md`.
   (`hydro_budget_nameplate_aware` itself stays default-off at NEISO — never
   armed, nothing to adjudicate.)
5. **STEP 3 seam disposition** (owner decision pending): carry the
   layup-vs-outage seam explicitly (recommendation (b) on record).

5b. **NEW — the stack-TRAVERSAL identification (charter REQUESTED at
    neiso-76, NOT opened).** The one route the Phase-0 measurement points at,
    and it is a different matrix family (`use_campd_bins` / `plant_level_fleet`
    / the tranche construction — **not** `da_virtual_bids`). Crossing the real
    submitted offer book at the real hourly quantity gives a hour-of-day price
    range of **$17.03 / $21.11 / $24.06** (66 / 73 / 54 % of the measured DA
    range) peaking at **HE20–21**, against the keeper's own **$7.03 / $6.82 /
    $13.30** — while *every constant-quantity read of the same book is
    INVERTED* (marginal price at fixed depth peaks overnight). So the model's
    within-day offer *surface* is not the binding constraint and the shape of
    its stack in the **quantity** dimension is the live suspect. It is a
    rule-14 `[R-ACCURATE]` comparison against a measured book, not a residual
    fit. **Reported against interest:** the traversal read is depth-sensitive
    — a flat 3 GW import allowance halves it to 36 / 34 / 31 %, only 4–7 pp
    above the keeper — so the *direction* survives and the magnitude does not.
    First task for any successor charter: reconcile the crossing quantity
    (published DA cleared demand net of scheduled imports and cleared virtual
    supply). Evidence: `FINDING-neiso76-dabid-phase0-2026-08-02.md` §D.
    **PREREQUISITE DISCHARGED AT neiso-79 (2026-08-03, NO LP, no solve, no
    cell verdict; item 5b STILL NOT OPENED — no owner green-light).** The
    crossing quantity is reconciled and the reconciliation **removes the depth
    parameter rather than re-assuming it**: imports enter ISO-NE's DA market as
    PRICED supply offers, so the probe crosses the **combined** book (internal
    offers + import offers + INC virtuals) against the published cleared-demand
    line and import depth clears **endogenously**.
    * **The DA CLEARED external series does not exist.** Verified against the
      full ISO Express Pricing / Grid / Load & Demand trees and Web Services
      v1.1: every interchange report is real-time/actual; the only DA external
      data ISO-NE publishes is the SUBMITTED import-offer/export-bid book. New
      gitignored corpus `data/raw/NEISO-AS/da-import-export/` (1,090 day-files,
      13 empty postings, 0 unpublished) + committed fetcher. **EIA-930
      interchange was NOT substituted** — actual net interchange is a different
      quantity at a different grain (rule 14 grain-misalignment trap).
    * **THE NUMBER:** crossed correctly, the real book's hour-of-day range is
      **$7.71 / $10.63 / $16.78 = 29.7 / 36.7 / 37.7 %** of the measured DA
      range — against §D's **65.6 / 72.9 / 54.1 %** at metered demand and the
      keeper's own **27.1 / 23.5 / 29.9 %**. 864 days in all three books,
      20,733 hours (300 / 288 / 276).
    * **The CONTROL makes this a statement about the QUANTITY, not the
      sample:** neiso-76's own §D read recomputed on the SAME 864 days gives
      **68.6 / 79.8 / 59.3 %** — at or ABOVE its full-corpus anchors in every
      year. §D was crossing the book **~4–5 GW too deep** (measured DA import
      depth ~4–4.4 GW plus 1.3–1.9 GW of INC), in a flatter part of the stack.
      neiso-76's own 3 GW sensitivity was the right instinct; the correct
      endogenous depth confirms its **pessimistic end**.
    * **Kill rules (pre-registered before the numbers existed):** **KQ1 does
      NOT fire** (0/3 at-or-below keeper) — the traversal lane is **NOT
      refuted**; **KQ2 FIRES** (3/3 below 40 %) — **DIRECTION-ONLY; the
      magnitude does not survive**; **KQ3 fires on 2025** ($11.12 vs a $10.00
      bar; 2023 $7.86 / 2024 $8.33 clear it) so the three-year headline share
      is **withheld** per the prereg; **KQ4 does NOT fire** — removing the
      import book recovers **49.6 / 61.0 / 49.4 %**, so the import
      reconciliation carries the bulk of the correction.
    * **Against interest:** the session's own `Must Take Energy` refinement is
      **REFUTED** (those MW are a subset of the ladder — every carrying
      unit-hour is MUST_RUN with a ladder already spanning EcoMax — and
      re-pricing them to the floor worsens the identification in all three
      years); the crossing sits a median $7.8–11.0 BELOW the posted DA
      (commitment cost, reserve co-opt, congestion, losses — reported as a
      bound, not tuned away); and a DA reserve reservation, which would have
      flattered the lane, was refused on neiso-76 §B3's measurement that ISO-NE
      cleared **no DA reserve product before 2025-03-01**.
    * **OWNER ROUTING for the 5b green-light:** the margin over the keeper is
      **+2.6 / +13.2 / +7.8 pp**, so a perfect traversal lever recovers at most
      **a third to a half** of NEISO's amplitude gap and **cannot close
      C3c-2025**; neiso-75 §2.4 already showed it cannot close C3c-2023.
      **Charter 5b only if the target is amplitude FIDELITY, not the C3c
      gate.** Evidence:
      `results/calibration/FINDING-neiso79-crossing-quantity-2026-08-03.md`;
      prereg `PREREG-neiso79-crossing-quantity-2026-08-03.md`; probe
      `scripts/probes/_neiso79_crossing_quantity.py`.

5c. **NEISO's amplitude decomposition is NOT NYISO's** (neiso-76 task (b), no
    LP; rule 25 in both directions). On NEISO's own posted AS prices — new
    gitignored intake `data/raw/NEISO-AS/reserve-prices/` (RT
    `finalhourlyreserveprice`, DA `daasreservedata`), regenerated by
    `scripts/probes/_neiso76_reserve_content.py` — reserve owns only
    **33 / 43 / 32 %** of the missing RT swing (NYISO: 97–131 %); NEISO's RT
    reserve price is **$0.00 at the median hour** and > $1 in just
    **23 / 23 / 21 %** of peak-window hours (NYISO DA spin: 100 %); and
    **ISO-NE cleared no day-ahead reserve product at all before DASI go-live
    2025-03-01** (measured: the DAAS report is header-only for Jan/Feb 2025,
    first data row 2025-03-01), so 2023–24's DA gap is 100 % energy-side by
    market design. Energy-basis restatement: the model's **peak is right to
    ±$3** and its **overnight trough is $7.6–9.9 too dear** (energy-only swing
    43 / 41 / 49 % of the reserve-stripped actual). NEISO's defect is an
    over-priced trough; NYISO's was missing reserve formation. **That
    disagreement is the material new input to the open owner
    amplitude-criterion call** — it is not one shared defect with one shared
    cause. No scorer changed.

5d. **RULE-28(c) COLUMN CLOSED (neiso-78, 2026-08-03; no LP, no solve, keeper
    UNCHANGED, no queue item touched, no cell verdict flipped).** NEISO's
    census debt — **10 `neiso_*` fields absent from the matrix, 8 of them
    ARMED ON THE KEEPER with no cell anywhere** — is **0/0/0**, making NEISO
    the **third closed column** after NYISO (nyiso-114) and ERCOT (ercot-156).
    All ten closed as literal registrations on **three existing family rows'**
    `def`s (the nyiso-114 escape-hatch template): `gas_coldsnap_derate` takes
    the three derate shape sub-scalars, `winter_fuelsec_posture` takes the six
    winter/oil fields, `dam_availability_rebasis` takes
    `neiso_operable_capacity_availability` (its `def` had carried the truncated
    stem `neiso_operable`, which no literal-match census can resolve). Ratchet
    baseline NEISO 10 → 0, shrink-only; the full six-ISO sweep confirms **no
    other column grew**. A **fourth, cross-ISO** gap was found while closing
    them and registered in the same session: the shared, solve-affecting
    `unit_partial_outage_windows` had **no matrix mention at all**, because its
    owning row `unit_outage_short_windows` named it only as a bare parenthetical
    line number. Every line number encountered in the four `def`s was **stale**
    (`:2138`→`:2878`, `:2286`→`:3026`, `:7771`/`:7796`→`:9419`/`:9444`).
    **THE LIVE DEFECT the census surfaced:** `neiso_oil_burn_budget` and its
    successor `neiso_winter_fuel_inventory` are both armed on the keeper away
    from a `False` default and both feed the **same** LP builder
    (`_build_oil_budget_rows`), so rule 19 `[R-ONE-MECH]` asks whether the
    keeper double-counts the winter oil-burn constraint. **It does not** —
    `run_calibration.py:4250` is a single `if`/`elif` (proven by `ast`, not
    read off the comment) in which the successor wins, so the superseded F923
    limb is **unreachable**: all **15/15** NEISO bundles arm both, and the limb
    is reachable in **0 of the 120** committed bundles across all six ISOs. It
    is NEISO's backcast default (`backcast_config.py:1549`), which is why it
    reads as armed, and it has **never once built a row**. Against interest:
    the field's own `scenarios.py` docstring calls it "not a keeper path",
    which is **false as written** — it is unreachable, not unarmed. **FILED NOT
    FIXED, routed to the owner:** it is a rule-26 `[R-DELETE]` candidate
    (armed-by-default *and* rule-13-inadmissible on its own docstring's
    account — EIA-923 petroleum *receipts*, a measured outcome with no forward
    analogue), and it joins nyiso-115's `campd_facility_outages` as the
    **second rule-26 candidate** in the same cross-lane queue; they should be
    decided together. Deleting it touches a NEISO backcast default and is not a
    census's call. Evidence:
    `results/calibration/FINDING-neiso78-matrix-census-close-2026-08-03.md`;
    probe `scripts/probes/_neiso78_oil_budget_reachability.py`. **Also
    corrected here:** §5.6's header and the neiso-78 prompt both named
    `2026-07-31-neiso-72-hy-window` as the NEISO keeper; the shard designates
    **`2026-08-03-neiso-caiso156-meter-screen`** (neiso-72 SUPERSEDED-NOT-
    RETRACTED at caiso-159).

6. ~~**`measured_chp_heat_rates` companion floor (the neiso-71 successor).**~~
    **CLOSED at neiso-71 (2026-07-31) with NO LP spent — the cell stays `O`,
    and NO CC_CHP floor should be built.** Screened by
    `scripts/probes/_neiso71_lever_screen.py`. Three findings, in order:
    (a) the floor this item asked for **already exists** as the committed WP-3
    statistic `steam_level_cf` (`derive_thermal_tranches.py` →
    `chp_steam_floor_p25`); NEISO just carries a **pre-WP-3 artifact vintage**
    with neither `steam_level_cf` nor `p25_allhr_cf`, so the flag is inert and
    `chp_pmin_cf` is 0.0 on all three CAMPD-visible CC_CHP plants — the
    mechanical reason the class has no `chp_steam` D-2 row. (b) Re-deriving it
    on NEISO's own CAMPD returns an **unusable** number: Kendall Square
    (EIA 1595, 42 % of the class) yields **146.1 % of nameplate**, saturating
    the 1.5 available-CF clip in **59.0 %** of online hours, because CAMPD
    facility 1595 unit "4" meters **278/299/283 MW median** against an EIA-860
    CHP nameplate of **213.4 MW (206.0 summer)**. Armed it would floor Kendall
    at **95.0 % of pmax year-round (~1.71 TWh/yr)** and MORE than close the
    0.34–0.68 TWh shortfall — a fitted parameter (rules 21/24). (c) **The
    structural answer:** NEISO's merchant CC_CHP genuinely carries **no**
    host-steam obligation — the other two CAMPD-visible plants measure 2.2 %
    and 3.6 % (real cyclers, online 5.5 %/7.0 % of hours) and the non-Kendall
    CC_CHP floor totals **15.0 MW**. That is a real fleet difference from
    CAISO's flat 43–47 % steam hosts, not a missing mechanism.
    **DO-NOT-REDO** until the prerequisite lands: the successor is now a
    **fleet/nameplate lane** (Kendall's capacity basis, inside the miso-95
    provenance-orphaned `nameplate_mw` column), not a floor lane. Evidence:
    `results/calibration/FINDING-neiso71-chp-floor-nuclear-2026-07-31.md` §1.
    **PREREQUISITE ADJUDICATED at neiso-73 (2026-07-31, NO LP spent):
    ARTIFACT, not missing capacity.** CAMPD unit-4 `grossLoad` at 1595 is not
    gross electrical MW (max 317–323 MW exceeds the 294.9 MW summed nameplate
    of every generator ever installed; implied gross HR 6.36–6.59 mmBtu/MWh is
    thermodynamically impossible; 923-net/CAMPD-gross flat at 0.654–0.687
    across 96 months; monthly net saturates the 860 winter rating at 99.5 %);
    mean gross/net 1.483 ≈ the saturated `steam_level_cf` 1.461 — the WP-3
    statistic measured the basis ratio, not a steam obligation. **The EIA-860
    basis (206.0 MW summer = the model pmax) is CORRECT; no model change was
    made and no A/B run.** The floor lane may reopen **only** on a NET-basis
    identification (923-anchored: Kendall's net loading-when-on is
    89.4/95.8/90.5 % of pmax at 94.5/91.3/94.0 % on-frequency — a genuine
    flat steam host, so neiso-71's "no obligation" claim now stands only for
    the non-Kendall cogens) with its own prereg declaring the over-closing
    hazard (~1.6–1.7 TWh floor effect vs a 0.34–0.68 TWh shortfall). Any
    derivation touching 1595 must de-base or avoid the CAMPD gross channel —
    it contaminates both `steam_level_cf` and any heat-rate derivation there
    (~32 % low). Evidence:
    `results/calibration/FINDING-neiso73-kendall-capacity-basis-2026-07-31.md`;
    probe `scripts/probes/_neiso73_kendall_capacity_screen.py`.

7. ~~**`nuclear_unit_availability` crosswalk.**~~ **DONE at neiso-71 → `K`,
    PROMOTED to keeper** (2026-07-31). The gap this item named (NEISO absent
    from `NRC_TO_EIA`) was the whole of it: adding **Millstone 2/3 → EIA 566
    and Seabrook 1 → EIA 6115** (3,355.4 MW, ~22 % of ISO energy) was the
    entire code delta — no `src/` change, since the `arrays.py` seam and
    `outages.py` loader were already ISO-generic. 3,288 rows, 365/366/365
    coverage, **all 36 months reconcile** (worst −0.70 %) so no month is
    dropped, `--check` byte-for-byte, **zero fitted scalars**. Same
    determination as the outgoing keeper (CALIBRATED-WITH-CAVEATS, 0 FAILs,
    C1 all 12/12 · free 8/8, C3c bit-identical, DOF `n_residual` unchanged at
    5) with the scored C1 total |error| improving **2.602 → 2.521 TWh** and
    liveness **1,129/1,842/1,265 MW** at energy neutrality (≤0.031 TWh/yr).
    Reported against interest: the predicted Connecticut-vs-North zonal
    separation did **not** appear (all four zones clear identically at
    annual-mean grain). Evidence:
    `results/calibration/FINDING-neiso71-chp-floor-nuclear-2026-07-31.md` §2.

8. ~~**Storage-side PS cycling depth** (the neiso-72 named successor).~~
   **REFUSED AT THE SCREEN at neiso-74 (2026-08-01) with NO LP SPENT —
   new row `pumped_storage_cycling_depth` → `G` at NEISO, and the item's
   PREMISE IS INVERTED.** Screened by
   `scripts/probes/_neiso74_ps_cycling_screen.py`. A perfect-foresight
   price-taker LP carrying the model's OWN storage physics (1,865.0 MW,
   `PUMPED_STORAGE_DURATION_HOURS` 10.0 h, `PUMPED_STORAGE_RTE` 0.80, cyclic
   SOC, the rule-9 ε) discharges **4.301 TWh on measured DA** and **4.691 TWh
   on RT** — **2.2× the 1.932 TWh actual**, not 4× below it — while the same LP
   on the model's own duals returns **0.370 / 0.339 / 0.612 TWh**, bracketing
   the keeper's endogenous **0.400 / 0.363 / 0.497**. The storage block is
   already optimal for the price signal it is shown; the constrained object is
   the model's **diurnal price amplitude**: level RIGHT (+2.8 % in 2025) and
   phase RIGHT (peak h17 in model and DA alike), amplitude **24–30 % of
   measured** — daily MAX −26.2 / −25.3 / −26.2 %, daily MIN +40.8 / +40.0 /
   +32.6 %, and **86 vs 365 of 365 days** clearing the 1.25× RTE hurdle. Every
   storage-side knob is inadmissible: the dispatch adder and an AS reservation
   are **wrong-signed** (they raise the hurdle ⇒ *less* cycling, and the adder
   map is empty everywhere precisely because PJM's $10 was retired for this
   failure mode), while `PUMPED_STORAGE_RTE` / `_DURATION_HOURS` are shared
   cross-ISO constants that cannot be fitted on one ISO's residual (rule 25).
   **DO-NOT-REDO** any storage-side PS lever at NEISO until the diurnal
   amplitude defect closes. Successor: the amplitude lane itself — attribution
   points at a constant marginal band (`CC_REGULAR` absorbs 2,045 MW of the
   4,117 MW diurnal demand swing while `CT_PEAKER` and `oil` are *already
   online at the overnight trough*), i.e. **item 1's DA-bid offer-formation
   charter**, unchanged and still owner-gated. Two carried caveats: (a) the
   real fleet realizes only **45 %** of the DA perfect-foresight optimum, so a
   successor graded on "does PS reach 1.932 TWh" is a fitted answer; (b) **no
   load-bearing criterion sees this** — C3b is a MONTHLY load-weighted NRMSE
   (`calibration_verdict.py::score_price_shape`), blind to hour-of-day, and
   C7/D-1 is SKIPPED for NEISO; whether the rubric gains a diurnal-amplitude
   criterion is an owner call. Evidence:
   `results/calibration/FINDING-neiso74-ps-cycling-price-shape-2026-08-01.md`.

### 5.7 Cross-cutting audits (not ISO levers)

- **Diurnal price-amplitude audit, all six ISOs — DONE 2026-08-01 (xiso-1), and
  the answer is SYSTEMIC.** One construction, zero LP (keeper
  `hourly/system_<year>.parquet` P1 load-weighted duals vs the committed
  `actual_lmp_hourly_<ISO>.parquet` hub DA/RT, both already on the model's
  chronological 8760 calendar), probe
  `scripts/probes/_xiso1_diurnal_amplitude_audit.py`, record
  `results/calibration/FINDING-xiso1-diurnal-price-amplitude-is-systemic-2026-08-01.md`.
  **All 36 ISO × year × benchmark cells compress with the same signature:**
  daily MAX under-priced in 36/36 (−7.5 % … −65.5 %), daily MIN over-priced in
  36/36 (+5.9 % … +146.0 %), hour-of-day amplitude **19.9–92.2 % of measured**
  (mean **40.5 %** vs DA, **43.9 %** vs RT) while the annual LEVEL is right to a
  mean absolute **7.1 %** and the PHASE is right in **34/36** rows.

  | ISO | amplitude vs DA, 2023 / 2024 / 2025 | cell |
  |---|---|---|
  | ERCOT | 52.9 / 38.2 / 36.7 % *(2023 uninterpretable — level −36.4 %)* | `U` |
  | CAISO | 46.5 / 52.9 / **75.9** % | `U` |
  | PJM | 31.6 / 36.5 / 34.2 % | `G` |
  | MISO | 34.0 / 36.3 / 25.2 % | `G` |
  | NYISO | 52.0 / 50.9 / 44.5 % | `O` |
  | NEISO | 27.1 / **23.6** / 29.9 % | `U` |

  Three consequences for every lane. (a) **The pre-existing ISO-local findings
  are this defect, not separate ones** — pjm-141's 31/33/32 %, miso-89's
  29–47 %, nyiso-109's 69/49/45 % and neiso-74's 24–30 % all reconcile
  (rule 19 `[R-ONE-MECH]`); do not re-derive them. (b) **The level passes by
  cancellation** — the trough is over-priced by about as much as the peak is
  under-priced, so judge any successor on the AMPLITUDE and pre-register its
  level effect. (c) **No criterion sees it at ANY ISO** — C3a is a level test,
  C3b is a TWELVE-MONTH NRMSE for every ISO (structurally blind to hour-of-day),
  C3c is a tail count, C7/D-1 is class *dispatch* shape; PJM's keeper is fully
  `CALIBRATED` at ~34 % amplitude. Whether the rubric gains a diurnal-amplitude
  criterion is an **OWNER CALL**, filed by neiso-74 and re-filed here; the
  scorer was NOT changed. Matrix row `diurnal_price_amplitude`.
  *nyiso-110 (2026-08-02) decomposed NYISO's cell*: on NYISO's own posted AS
  prices its face of this defect is dominated by missing everyday
  reserve-price formation (reserve differential = 64–89 % DA / 97–131 % RT of
  the missing swing; the C3a level PASS is a cancellation — the level gate
  penalizes the structural repair), NOT by the energy-side traversal, which
  owns only the DA residual. A per-ISO decomposition question the other five
  lanes have not answered (rule 25). NYISO's cell is ACTIVE behind
  `PREREG-nyiso110-spin-online-peak-formation-2026-08-02.md` (§5.5).
- **Post-guard re-derivation sweep of outage-derived artifacts, all six ISOs —
  DONE 2026-08-02 (xiso-2), and NO KEEPER IS AFFECTED.** The list's oldest open
  audit (flagged in governance.md 2026-07-26) is closed. Zero LP: the census reads
  committed bytes and re-runs frozen derive scripts. Probe
  `scripts/probes/_xiso2_outage_artifact_provenance_census.py`, record
  `results/calibration/FINDING-xiso2-outage-artifact-provenance-census-2026-08-02.md`.

  **Byte-reproduction at HEAD**, each ISO re-derived with the committed recipe
  (`--years 2018 … 2026 --merit-order-guard`) and md5-compared against the
  guard-on extract from `6a8f285c5` (2026-07-26 00:36Z):

  | ISO | extract reproduces? | verdict |
  |---|---|---|
  | ERCOT | **byte-identical** | CLEAN |
  | CAISO | **byte-identical** | CLEAN (one *inert* pre-guard hygiene item) |
  | PJM | **byte-identical** | CLEAN |
  | MISO | mismatch, **2022 only** | CLEAN in the training window |
  | NYISO | **byte-identical** | CLEAN |
  | NEISO | **byte-identical** | CLEAN |

  Four consequences. (a) **MISO's mismatch is fully attributed and
  training-clean** — a strict SUPERSET (+17 windows, 0 lost, **all 2022 COAL**),
  layup companion byte-identical, **2023–2025 identical row-for-row**, root-caused
  to commit `5cd937407` (2026-07-31) filling the MISO EIA-930 2022 hourly hole
  (7 → 8,760 rows). A **source-data** change, so re-derivation is rule-23
  admissible — non-urgent, must cite the data change, and must not ride along in a
  calibration session. Against interest: the same commit filled CISO's 2022 hole
  and **CAISO still reproduces byte-identically**, so this does not generalise
  (rule 25). (b) **The only keeper-consumed artifact downstream of an extract is
  NYISO's NYC/LI/Capital `ST_GAS` reliability-floor limbs, and nyiso-81 re-derived
  them 18 h AFTER the guard the same day** — ancestry-tested, not date-tested.
  The other ISOs' `reliability_floor_coeffs_*.csv` are **not** downstream of the
  outage extracts at all, so their 06-30…07-08 dates are not a staleness finding.
  (c) **Two artifacts are genuinely pre-guard and neither is keeper-consumed**:
  `MAINTENANCE_MONTHLY_SHAPE` (2026-06-25, forecast-mode only, default on) and
  `caiso-dam-resource-crosswalk.csv` (2026-07-19, **zero** code consumers —
  provably inert). (d) **One live code defect found and FIXED**:
  `derive_maintenance_shape.py` pooled `glob(campd-unit-outages*.csv)`, which
  since the guard also matches the six `-layup-` companions — the windows the
  guard *exists to veto*, so pooling them partially inverts it (rule 19) — plus
  the `-e923-`, `-short-` and `-maxgen-` files: **24 files / 58,744 rows drawn
  where 6 / 39,755 were intended (+47.8 %)**. The selector now enumerates
  `_STANDARD_EXTRACTS`. The constant does **not** reproduce under *either*
  selector and, against interest, the corrected one is **not uniformly closer** —
  fixing the glob does not restore it; it is genuinely stale w.r.t. the 07-24
  backfill and the guard. Re-derivation is rule-23 admissible and was
  **deliberately not done** (a census is not a sweep; it is a forecast-lane input
  whose refresh belongs to a session that can gate it). Matrix row
  `outage_artifact_provenance`, cells `IIIOII`.

  Filed, not fixed (rule 24 `[R-REGISTRY]`): `maintenance_monthly_shape` is a
  solve-affecting `ScenarioConfig` field **absent from the matrix** — CI
  grandfathers it because `check_mechanism_matrix.py` diffs new fields against the
  PR base. Its per-ISO forecast-lane verdicts have never been tested, so xiso-2
  did not invent them.
- **Rule-20 forced-share / D-4 window census, all six current keepers — DONE
  2026-08-02 (xiso-3), and ALL SIX PASS C8.** The first census of rule 20
  `[R-FORCED-BUDGET]`'s full conditional-pass logic across every keeper at once.
  Zero LP: scored through the **production rubric itself**
  (`calibration_verdict.score_forced_share` + `_d4_provenance` / `_d1_shape` /
  `_class_load_share`) on the committed `legitimacy_diagnostics.json` +
  payload/bench artifacts — never re-implemented. Probe
  `scripts/probes/_xiso3_forced_share_d4_census.py` (reads the keeper shards
  live, so it re-scores automatically on any keeper swap), record
  `results/calibration/FINDING-xiso3-forced-share-d4-census-2026-08-02.md`.

  | ISO | C8 | grounded-above-budget | latent D-4 gaps | drift | verdict |
  |---|---|---|---|---|---|
  | ERCOT | PASS | 0 | 3 | 0 | PASS |
  | CAISO | PASS | 0 | 4 | 0 | PASS |
  | PJM | PASS | **4** | 4 | 0 | **GROUNDED-PASS** |
  | MISO | PASS | **3** | 6 | 0 | **GROUNDED-PASS** |
  | NYISO | PASS | 0 | 0 | 0 | PASS |
  | NEISO | PASS | 0 | 3 | 0 | PASS |

  Zero FAILs, zero exceptions-ledger flips, zero D-4 window drift vs the HEAD
  registry. PJM (CT_PEAKER 15.2/15.4/15.8 % vs 15 %; ST_GAS-2025 40.0 % vs
  30 %) and MISO (ST_GAS 33.1/34.4/45.5 % vs 30 %) pass through the
  grounded-above-budget escalation — every binding mechanism windowed with
  **0.0 % off-window binding** and D-1 clear everywhere (worst `profile_r`
  0.897, worst `cv_ratio` 0.697) — **clean passes surfaced as report notes,
  never caveats**, per the rule. Informational yield: a five-fact **latent D-4
  coverage map** (classes below cap whose binding mechanisms hold no
  class-applicable `D4_WINDOWS` entry — `reliability_floor` on CC/COAL at
  ERCOT/PJM/MISO/NEISO; CAISO's `ra_mustoffer_bridge` with **no entry of any
  kind**, its sole non-exempt binder at 6.8–9.6 % vs 30). Nothing there is
  gated today (the provenance leg is only consulted above the cap) and **no
  entry was minted** — a rule-17 declaration needs its own per-ISO driver
  evidence. Matrix row `forced_share_d4_census`, cells `IIIIII`.
- **D-2/D-4 plant-set + floors-reconstruction fidelity audit — DONE 2026-08-02
  (caiso-155), the caiso-151 §F filed defect ADJUDICATED AND FIXED; no keeper
  verdict moved.** Zero LP registered. Probe
  `scripts/probes/_caiso155_plant_set_census.py` (fix-aware on re-run), record
  `results/calibration/FINDING-caiso155-diagnostics-plant-set-2026-08-02.md`,
  pre-registration + 2 addenda each committed before the numbers they govern.
  Three harness defects, all fixed ISO-generically in
  `scripts/legitimacy_diagnostics.py`:

  1. **The plant-set drop** — floored `plant_code <= 0` interchange tranches
     now ride D-2/D-4 as `u:<unit_id>` pseudo-plant rows under a
     pre-registered floor-energy convention (dispatch := min_gen, every
     path); class `""` + non-thermal exemptions keep C7/C8 structurally
     invariant (unit-tested).
  2. **The rebuild's dropped override channels** — `REBUILD_META_RENAMES`
     threads `coal_prb_sigmoid_overrides`/`coal_bit_*` into `run_year`;
     unthreaded, the reconstruction LOST CAISO's channel-armed firm floors
     and HALLUCINATED MISO's pre-miso-74 Manitoba block.
  3. **G-06's too-narrow bridge carve-out** — `BRIDGE_MECHS` widens the
     committed-side subtraction from the RA leg to the whole P0-pattern
     family (nyiso109 would have false-failed by 5.31/3.14 pp CC_REGULAR).

  | ISO | dropped floored tranches at the keeper | TWh/yr |
  |---|---|---|
  | CAISO | 2 firm tranches (PNW hydro base + DSW solar PV) | **17.938 / 22.684 / 22.494** (= caiso-151 §C, 2 independent reconstructions) |
  | NYISO | `NYISO_external_HQ_hydro` (900 MW flat) | **7.884** each year |
  | MISO | **none** — `miso_manitoba_seam` (miso-74) replaced the firm block; the handoff premise was stale | — |
  | ERCOT / NEISO | none (`priced_interchange: False`) | — |
  | PJM | census S3-blocked (`pjm-da-virtuals` uncommitted); static: no firm-floor config | — |

  **No committed artifact was regenerated**: the fleet-only rebuild fails the
  pre-registered A1b gate (solve-state floors — the P0 bridges,
  nuclear/hydro/CHP applications — would be silently lost), and an in-place
  caiso153 replay failed D-13 with a measured degenerate-vertex signature
  (2023 system duals byte-identical; class/storage dispatch shuffled up to
  ~2 GW), so replay floors are not keeper floors either. Committed bytes
  restored; every keeper's determination unchanged (xiso-3 baseline == exit
  state). The visibility lands automatically on every future in-session
  artifact generation. Matrix row `diagnostics_plant_set`, cells `IIOIII`.
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
  | PJM | no | **1,249–1,612** | 0 | **+52.9 % … +79.6 %** | **DEFECT, largest — FIXED (pjm-143, keeper)** |
  | MISO | no | 332–826 | 0 | +13.5 % / +18.5 % | **DEFECT — FIXED (miso-109)** |
  | NYISO | no | 0–33 (≤0.007 TWh) | 0 | −4 % … −6 % | clean; the bias is the opposite sign |
  | NEISO | **yes** (from Nov 2024) | 63–276, **0 in 2025** | 0–1 | +2.7 % … +10.1 % | **TIME SPLIT — FIXED (neiso-72, keeper, per-window)** |

  **THE AUDIT ROW IS CLOSED AT ALL SIX ISOs** (neiso-72, 2026-07-31). NEISO —
  the last open follow-on — landed as the flagged per-window treatment:
  `constants.EIA930_PS_SPLIT_COMPLETE_FROM` +
  `data/hydro.py::eia930_wat_level_folded` (seam measured to the hour,
  2024-11-07 00:00, `scripts/probes/_neiso72_ps_window_audit.py`; the probe
  adds the within-month seam test and its five-year no-seam control to the
  three-signature screen). NEISO detail worth carrying: its small +2.7 %/+10.1 %
  level gap hid a ~1.9 TWh/yr fold cancelling against a ~1.2–1.6 TWh/yr 930
  telemetry UNDER-count of the 923 census — screen on the signatures, never on
  the net gap. Standing hazard for every listed ISO: the hydro dispatch
  *envelope* and *min-flow floor* are also built from hourly `NG: WAT` and
  inherit the same contamination — both are default-off and off in the affected
  keepers today, so nothing is stacked, but arming either needs its own source
  fix first (EIA-923 is monthly and offers no hourly substitute; for NEISO the
  post-split window is the only clean hourly source and holds one water year).
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
