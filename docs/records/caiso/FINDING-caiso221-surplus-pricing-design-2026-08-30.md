# FINDING — caiso-221: THE SOUTH-BELLY SURPLUS-PRICING DESIGN PHASE (caiso-215 §F H4, ranked item 1) — the object is KILLED WITH MEASUREMENT, on two independent grounds: (1) the rule-13-admissible quantity class is ALREADY FULLY CONSUMED — the keeper's renewable potential IS delivered + the full reported curtailment record (HSL, recon/parquet ratio 1.000–1.003), and every remaining admissible instrument's ceiling is ≤ 2 % of the required move (re-placement −$0.02, AS reservation $0.00 + rule-19 barred, gen-pocket ≤ −$0.15 at the whole-ZP26 bound); and (2) the regime itself is UNDERSIZED FOR 2025 — perfect conversion of every convertible south-negative cell yields −$1.17 vs the −$1.90 requirement, so NO surplus-pricing representation, admissible or otherwise, can close C3a-2025. NOT-YET stands; the residual is attributed and closed at this grain. NO LP, NO SOLVE — committed bytes + the licensed fleet-only input assembly (2026-08-30)

**Keeper `2026-08-26-caiso-220-c1-crosswalk` UNCHANGED. No mechanism armed, no
`ScenarioConfig` field added, no LP built, no solver called, nothing
registered.** This session executes the owner's 2026-08-30 handoff — the
caiso-215 §F H4 design phase ("DESIGN/INTAKE FIRST, NO SOLVE unless the design
passes the rule-13 test and gets its own precommit"), deliverable (a) an
admissible representation + funding ask, or (b) "kills the object honestly
with measurement — 'the residual is attributed and no admissible
representation exists' is an acceptable answer." **The answer is (b)**, and it
is stronger than the pre-registered fallback: not only does no admissible
representation exist — for 2025 no representation of this regime AT ALL is
sized to close the gap. Off-queue statement: the in-model queue is EMPTY
(caiso-185/200); this design phase is the owner-funded caiso-215 §G item 1.

## THE ONE-SCREEN OWNER SUMMARY

* **The admissible class named by the rule-13 test is already spent.** The
  test (caiso-215 §F H4, verbatim) admits "measured curtailment/surplus
  QUANTITIES entering as reproducible physical/market inputs with a forward
  analogue." The keeper already consumes exactly that: every CAISO backcast's
  wind/solar upper bound is the HSL analogue `delivered + reported
  curtailment` (`scripts/data/build_caiso_hsl.py`, committed
  `data/raw/caiso-hsl/` 2019–2025; consumed via
  `renewables._hsl_cf_profile`). Control: the keeper-recipe recon's ISO
  potential reproduces the HSL parquet at ratio **1.000–1.003** in every
  year-fuel, and the HSL add-back equals the workbook record exactly
  (2.66 / 3.40 / 3.77 TWh). The LP is already handed the full measured
  surplus and re-curtails endogenously (`caiso_solar_endogenous_spill`,
  armed). There is no un-consumed curtailment quantity left to intake.
* **What was still free — the add-back's zonal PLACEMENT — is measured at a
  −$0.02 ceiling.** The distributor smears the ISO-wide series
  capacity-pro-rata, placing 14.7–16.1 % of the curtailed MW (0.43–0.59
  TWh/yr) north of Path 15, against a record that is 78–92 % Local-class
  with its off-peak constraint mass at PG&E Kern/Fresno (caiso-219 census).
  Re-placing ALL of it south adds only **+41/+52/+48** static
  hours-over-path; at the caiso-220 empirical static→scored transfer that is
  **−$0.020/−$0.021/−$0.007** against required −$0.85 (2024) / −$1.90
  (2025). Dead by 40×.
* **The absorption side is already measured-conduct-bounded, and the one
  admissible reduction is rule-19 barred.** The keeper's belly charge is
  capped by the armed measured dispatch-shape envelope
  (`caiso_storage_shape_anchor`, caiso-99 Mechanism B), which **embeds the
  AS holdback** — `scenarios.py` hard-errors the
  `caiso_storage_as_reservation` combination (rule 19, one mechanism per
  phenomenon). And even ignoring that bar, a generous 2 GW reservation
  leaves **zero** static hours in any year where the south's surplus exceeds
  path + storage. Dead twice.
* **The gen-pocket class dies on load-share arithmetic, independent of the
  CEII wall.** A gen-pocket export limit floors prices only INSIDE the
  pocket; the Gates–Midway Kern/Fresno pocket is a generation-heavy subset
  of ZP26 (demand share **5.0–5.2 %**), and pricing the WHOLE of ZP26 at
  the −$20 floor through every south-negative hour moves the scored mean
  only **−$0.11/−$0.15/−$0.11** — while the limit's effect on the remaining
  56 % of load (the south outside the pocket) is weakly UPWARD (supply
  withheld). Even with a published rating, the pocket cannot close C3a.
* **And the object is undersized for 2025 regardless of instrument.**
  Perfect conversion — model λ set to the hub actual in every convertible
  south-negative cell — yields **−$0.95 / −$2.00 / −$1.17** (2023/24/25).
  2024 clears its −$0.85 at 42 % capture; **2025's entire regime carries
  only 62 % of its −$1.90 requirement**. The remaining 2025 mass sits in
  sub-$60 POSITIVE-price hours (the caiso-202 §B level structure), where
  surplus pricing is not the mechanism and the offer-object fences stand.
  2023 safety is confirmed better than estimated: full conversion costs
  −$0.95 of the −$7.56 headroom.
* **The ask: NOTHING.** NOT-YET stands on `2026-08-26-caiso-220-c1-crosswalk`
  and the lane returns to the caiso-201 rest. The C3a residual attribution
  is final at this representation grain (§E). Re-opening requires one of:
  a CAISO publication change (internal element ratings/flowgate limits),
  CEII access, or an owner-chartered sub-zonal/nodal topology program —
  each an owner decision, none recommended here.

Instruments (committed, no LP, no solve):

* `scripts/probes/_caiso221_surplus_design.py` — sections A0–A5; imports the
  committed caiso-215/216 probes for the hub actuals, workbook loader,
  EIA-930 series and zone-row matching, so every series is provably the
  same construction re-used. The only reconstruction is the licensed
  caiso-105/131 `run_year(fleet_only=True)` input assembly rebuilt from the
  caiso-220 keeper bundle's own `meta.json`.
* `results/calibration/_caiso221_surplus_design.json` — every number below,
  committed (deterministic: sorted keys, rounded floats, no timestamps).
* Controls (§A): demand row-match **0.0 MW** in all zones × years; recon
  potential = HSL parquet at 1.000–1.003; add-back = workbook total at
  1.000; model endogenous spill 482/1,184/849 GWh (the caiso-216
  measurement, reproduced on this keeper); base cut-15 L2 exceedance
  **121/480/742 h** — the committed caiso-217 realized-membership numbers,
  reproduced EXACTLY at HEAD.

Reproduction: `pip install numpy pandas pyarrow pydantic pyyaml scipy
highspy openpyxl tzdata` then `PYTHONPATH=.:src python3
scripts/probes/_caiso221_surplus_design.py` (first run rebuilds the
fleet-only assembly per year, minutes each; cached thereafter; requires the
regenerated `data/clean` tree).

---

## §A — Instrument and controls

Inputs: the caiso-220 keeper's `hourly/` sidecars (per-zone λ/demand, class
MW, storage flows); the fleet-only recon (per-zone renewable bounds cf×cap
as the LP receives them, nuclear, hydro floors, per-zone storage power); the
committed HSL parquets (`caiso_<year>_hsl_hourly.parquet`); the curtailment
workbooks (5-min, Local/System reason, via the caiso-216 loader mapped to
the fixed clock with the `build_caiso_hsl.py` month/day/hour arithmetic);
the trading-hub RTM CSVs (caiso-215 loader); the EIA-930 CISO parquet
(D/NG/TI); the caiso-219 deliverability census JSON.

All §A controls pass (values above). The exact reproduction of the
caiso-217 realized L2 exceedance (121/480/742) doubles as a byte-stability
witness for the crosswalk-active recon at this HEAD.

## §B — The consumption discovery: the admissible class is already an input

The rule-13 test's admissible class — measured curtailment/surplus
*quantities* as reproducible inputs — turns out to be the keeper's existing
construction, not a new intake:

| year | HSL add-back (wind/solar TWh) | = workbook total | Local share | belly (hod 10–15) share | placed north of Path 15 |
|---|---|---:|---:|---:|---:|
| 2023 | 0.151 / 2.509 | ratio 1.000 | 77.9 % | 75.5 % | **16.1 %** (0.43 TWh) |
| 2024 | 0.229 / 3.170 | ratio 1.000 | 92.0 % | 70.0 % | **14.7 %** (0.50 TWh) |
| 2025 | 0.283 / 3.482 | ratio 1.000 | 83.5 % | 71.6 % | **15.7 %** (0.59 TWh) |

The dispatch is handed the full uncurtailed potential and re-curtails
endogenously (`caiso_solar_endogenous_spill` armed — the pre-LP
`caiso_solar_deliverability` derate is SKIPPED by design, `runner.py`). The
model's own spill (482/1,184/849 GWh at the −$20 floor) is the endogenous
re-curtailment this input feeds. **Design consequence:** the only
curtailment-quantity object left open is the add-back's zonal placement —
the ISO-wide series is distributed capacity-pro-rata across all five zones
(`_distribute_by_eia860` / `_redistribute_preserving_total`, system total
preserved), i.e. ~15 % of the measured curtailed MW is placed in NP15
against a census whose off-peak constraint mass is Kern 7/10 + Fresno 14/19
(ZP26-side) and a record that is 78–92 % Local. That object is C-A below,
and it is measured dead.

## §C — Regime decomposition: where the convertible mass lives, and the depth witness

Reality's south-negative hours (TH_SP15 RT < 0: **688 / 1,230 / 964**),
cross-classified against the model's own state on this keeper. Gap-$ =
Σ_south4 demand × (model λ_z − own-hub actual), expressed in scored
lw-$ (directly comparable to the required moves):

| cell (2024) | hours | south gap | lw-$ | model λ p50 |
|---|---:|---:|---:|---:|
| s-neg total | 1,230 | $412 M | **+1.94** | $1.4 |
| model ALREADY floored | 575 | $93 M | +0.44 | −$19.3 |
| model above floor (convertible) | 655 | $319 M | **+1.50** | $24.7 |
| … of which Local-curtailment-active | 630 | $308 M | +1.45 | $24.5 |
| … of which NO curtailment active | 22 | $10 M | +0.05 | $31.9 |

2025: s-neg total +1.10 lw (964 h; floored 456 h/+0.16; convertible 508
h/+0.94, of which **496 Local-active**). 2023: +0.88 lw (688 h; floored
252/+0.01; convertible 436/+0.87, 431 Local-active). Three structural
readings:

1. **The model already reproduces the floor regime in ~37–47 % of reality's
   s-neg hours** (at the −$20 offer floor; reality prices deeper, so even
   the floored cells carry +$1.7/$93/$34 M — the "floor-depth" channel,
   C-I below, bounded at +0.01/+0.44/+0.16 lw).
2. **The convertible mass IS the Local-strandedness regime, measured:**
   96–99 % of the convertible hours have Local-class curtailment active;
   hours with no curtailment at all are 1/22/7 per year. The caiso-215 §F
   H4 attribution is confirmed on the arm itself at hour grain.
3. **The depth witness:** in convertible hours the sidecar charge runs p95
   4.9/7.4/9.5 GW against 9.6/13.2/17.5 GW fleet power — and the binding
   charge bound is not the nameplate but the armed **measured dispatch-shape
   envelope** (`caiso_storage_shape_anchor`, caiso-99 Mechanism B: measured
   p95 hod rate per MW of fleet, EIA-930 NG:OTH ÷ EIA-860, rule-23
   derivation), which **embeds the AS holdback** ("the measured NG:OTH
   rates are net of awarded capacity" — `scenarios.py`, which hard-errors
   the reservation combination under rule 19). The model's belly absorption
   is already reality-shaped on the storage side; what the pool grants that
   reality denies is frictionless *access* — any southern MW can reach any
   southern absorber, because no sub-zonal constraint exists in the
   topology.

## §D — Candidate adjudication (kill-before-solve, each against 2024 −$0.85 / 2025 −$1.90 / 2023 headroom −$7.56)

The candidate space over the named evidence bases is spanned by how a
measured *quantity* can enter an LP: as a supply bound, an absorption
bound, or topology. Every branch is adjudicated:

| # | candidate | class | ceiling (2023/24/25 lw-$) | verdict |
|---|---|---|---|---|
| C-A | re-place the north-placed add-back south (census-informed) | supply placement | −0.020 / −0.021 / −0.007 (Δstatic +41/+52/+48 h × the caiso-220 transfer) | **DEAD — 40–270× short**; the static delta itself overstates scored reach (742 static h → 17 scored >$15 h in 2025) |
| C-B | measured AS-award charge reservation (1–2 GW) | absorption | 0 static hours over path+storage at either size, every year | **DEAD twice** — rule-19 barred on this keeper (the armed shape envelope embeds the AS holdback; `scenarios.py` guard) AND sizing-zero |
| C-C | represent Local-curtailed MW as curtailed (delivered cap) | supply | — | **FORBIDDEN** — the self-labelled `caiso_solar_cap_at_delivered` outcome pin (caiso-216 §F.3d); also wrong direction (λ up) |
| C-D | import-stack belly availability | absorption | — | adjudicated ≈ 0 / adverse (caiso-216 §F.2b); removing supply raises λ |
| C-E | gen-pocket behind an export limit (Gates–Midway, per census) | topology | −0.107 / −0.147 / −0.114 at the GENEROUS whole-ZP26-at-floor bound (ZP26 demand share 5.0–5.2 %) | **DEAD on load-share arithmetic, independent of the CEII wall** (caiso-218/219); the limit weakly RAISES the 56 %-load south outside the pocket |
| C-F | perfect regime conversion (the benchmark, not a candidate) | — | −0.95 / **−2.00** / **−1.17** | 2024 clears at 42 % capture; **2025 cannot clear at 100 %** — the regime holds 62 % of the requirement |
| C-G | export/absorption column (EIA-930 TI as input) | absorption | — | R-cells stand (`caiso_p1_export_sink_seam`, `caiso_corridor_export_path`); absorption RAISES λ; the §F.3c contingency is gated on a C3b trip that has not fired (caiso-220: 0.100/0.177/0.180, tripwire silent) |
| C-H | hub MCC / any measured-price overlay | price | — | **FORBIDDEN** verbatim by the rule-13 test; MCC components serve as attribution evidence only |
| C-I | deeper renewable offer floors (reality < −$20 in floored cells) | price/offer | +0.01 / +0.44 / +0.16 lw available in the floored-cell channel | **DEAD** — an offer-side object (the armed floors are measured PTC/REC economics, rule-23 frozen); even full capture is < 2024's requirement and 8 % of 2025's; C3b left-tail adverse |

C-F + C-I partition the regime's whole mass exactly (2024: 1.50 + 0.44 ≈
1.94 lw = the s-neg total; 2025: 0.94 + 0.16 = 1.10), so the table is
complete over the regime — there is no un-adjudicated channel inside it,
and for 2025 the whole of it is smaller than the required move.

**The 2025 sizing correction to the charter.** The handoff's sizing line
("removing ~46 % of the measured south-belly error closes 2025") traces to
caiso-215 §G, where the 46 % is of the south's **all-hours** error ($894 M,
only $316 M of it belly). Measured at the surplus-regime grain, 2025's
convertible mass is $193 M (+$34 M floor-depth) against a ≈$390 M
requirement — the object was never sized to close 2025 alone; the balance
sits in sub-$60 positive-price hours (hub < $20 skirt: 2,150 h, ceiling
−$2.67 — but model p50 there is ~$25–32 against POSITIVE actuals, which is
the caiso-202 §B level structure, not surplus pricing, and the §F
offer-object fences stand). This is a *sharpening* of caiso-215, not a
contradiction: the zonal decomposition measured WHERE the error lives; this
probe measures what the surplus-*regime* subset of it can pay.

## §E — The residual attribution, final form at this representation grain

C3a-2024/25 on the caiso-220 keeper decomposes into, and is closed as:

1. **The Local-strandedness convertible mass** — 655/508 h (96–99 %
   Local-curtailment-active), +1.50/+0.94 lw. Faithful representation
   requires the sub-zonal constraint between southern supply and southern
   absorbers. At pool grain that structure is load-share-dead (C-E); below
   pool grain it needs internal element ratings that are CEII (caiso-218/219,
   filed item 9). No admissible instrument reaches it (C-A/C-B ≤ $0.02).
2. **The floor-depth channel** — +0.01/+0.44/+0.16 lw where the model's
   measured −$20 offer floor is shallower than reality's deepest negatives.
   An offer-side object, rule-23 frozen, undersized (C-I).
3. **(2025 only) the sub-$60 positive-price level structure** — the
   ≈ +0.7 lw balance outside the surplus regime, already attributed by
   caiso-202 §B/§F with the per-year/per-zone offer objects fenced.

Re-opening the lane requires an owner decision on one of: (i) a CAISO
publication change putting internal element ratings/limits in the public
record; (ii) CEII access; (iii) a sub-zonal/nodal topology program (a
representation-grain change, not a lever). None is recommended by this
FINDING; NOT-YET stands.

## §F — Record changes (rule 28b — CAISO shard only)

* This FINDING; `scripts/probes/_caiso221_surplus_design.py`;
  `results/calibration/_caiso221_surplus_design.json`.
* Matrix §5.2: caiso-221 block added above caiso-220's; CAISO shard `gates`
  stamp prepended; `updated` bumped. **NO cell verdict moves from this
  session's own testing** (nothing was armed or solved). Two chartered
  housekeeping edits land with it:
  * **Filed item 6 DISCHARGED** — `zonal_gas_basis` re-adjudicated
    caiso-203-style (a bookkeeping adjudication on existing evidence):
    cell **K → R**. The K was unsupported by any committed artifact —
    `caiso_zonal_gas_basis: false` in every committed CAISO
    `run_config.json` at HEAD (caiso200_h1_memberpanel, caiso205_control_A,
    caiso205_adaptive_B, caiso220_c1_crosswalk), no registry sidecar, log
    or FINDING records an arming, and the cell's blame terminates at the
    history-rewrite boundary. The standing evidence is caiso-215 §F H3's
    measurement (differential sign-flipping +0.539/−0.184/−0.491 $/MMBtu;
    mean-zero as a C3a instrument; the real split 80–90 % congestion) —
    an ex-ante rejection on the caiso-185 pattern. The caiso-215 §I
    carve-out stands: a NP15-winter-scoped fuel-fidelity case with monthly
    measured basis data is NEW evidence and is not barred.
  * **Filed item 7 DISCHARGED** — the `solar_deliverability` K-text leg
    note resolved: the K rides the **endogenous-spill leg**
    (`caiso_solar_endogenous_spill` armed on keeper caiso-220; the pre-LP
    `caiso_solar_deliverability` derate is skipped by design, `runner.py`).
* `docs/calibration-log/caiso.md`: caiso-221 entry.
* Filed items after this session: **6 and 7 DISCHARGED**; 3 (caiso-205 pair
  sites) and 4 (promoting sessions re-measure the whole scorecard) carried;
  **9 stands, strengthened** — both lever routes remain CEII-blocked AND
  the design phase now shows the pocket is load-share-dead at pool grain
  and the regime undersized for 2025, so the wall is no longer the only
  thing standing between the lane and a 2025 close. Cross-lane items
  carried unchanged.

## §G — DO-NOT-REDO (new, binding; the caiso-202 §I / 215 §I / 216 §I / 218 §F / 219 §F / 220 §E chain carries whole)

1. **Never propose "measured curtailment/surplus quantities as an input" as
   a NEW C3a lever** — the class is consumed: the keeper's potential IS
   delivered + the full reported record (HSL ratio 1.000–1.003, §B). The
   one free margin (zonal placement) is measured at a −$0.02 ceiling (C-A).
2. **Never arm `caiso_storage_as_reservation` alongside the keeper's
   `caiso_storage_shape_anchor`** — rule 19, enforced by the `scenarios.py`
   guard: the envelope embeds the AS holdback. The absorption side is
   already measured-conduct-bounded; there is no admissible absorption
   reduction left (C-B, 0 static hours at 2 GW).
3. **The gen-pocket class is dead on load-share arithmetic independent of
   the CEII wall** (C-E: ≤ −$0.15 at the whole-ZP26 bound, 5.0–5.2 % demand
   share, sign-adverse outside the pocket). A published rating would not
   revive it at pool grain.
4. **Never charter a C3a-2025 close through the surplus-pricing regime** —
   the regime's perfect-conversion ceiling is −$1.17 vs the −$1.90
   requirement (C-F). Any future 2025 object must reach the positive-price
   sub-$60 band, where the caiso-202 §F offer-object fences apply.
5. **Never quote the caiso-215 "46 % closes 2025" sizing without its
   all-hours basis** (§D) — at regime grain the number is > 100 %.

Keeper, markers, holdout freeze, DOF ledger, every matrix cell verdict
other than the two chartered housekeeping edits (§F), every bench part, and
every source file other than the additions listed in §F: UNCHANGED. Next
number: caiso-222.
