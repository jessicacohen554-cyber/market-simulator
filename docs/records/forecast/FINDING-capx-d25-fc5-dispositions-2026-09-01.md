# FINDING — capx D25: the FC-5 dispositions are authored, and FC-5 can now grade a golden (78 rows, 0 UNEXPLAINED, five keys re-scored SKIPPED → CAVEAT)

**Session:** D25 (capacity-expansion / Forecast Finalization track), branch
`claude/capx-d25-fc5-dispositions-knmp05`, the disposition-authoring charter that closes the
FC-5 half of the t3 ceiling (owner ruling Q16, 2026-08-31: the FC-5/FC-6 ceiling is fixed
BEFORE any second golden campaign; Q19 ordered FC-6 first — lane D21 — then FC-5 — lane D22
intake, this lane's judgment step).
**Date:** 2026-09-01 · **HEAD at launch:** `6c7f82da`; the r#22-close batch (D19 board
reconcile, **D23 P1 carbon-sign re-attribution**, D24, D17, miso-196, caiso-230, audit lanes)
landed on main mid-session, so per the collision discipline the work was rebuilt on
`7b085947` with D19's board writes left intact and **D23's re-attribution incorporated into
the affected CO2/CCS rows before anything was pushed** (§4.3 mechanism 5). · **Zero solves**
— every input read and every score produced from committed artifacts only.

**Headline.** The per-row disposition table rubric §FC-5 requires a scoring session to author
now exists and is committed: **78 rows** across the five bundles with committed model
snapshots — **37 IN CORRIDOR / 41 EXPLAINED DIVERGENCE / 0 UNEXPLAINED** — each explanation
naming its mechanism with a citation. All five verdict keys re-score **FC-5 SKIPPED → CAVEAT**
(control-first: every committed verdict reproduced byte-for-byte before the corridor inputs
were added), **no determination moves**, and on `neiso-t3` nothing reads SKIPPED-required any
more: **the t3 ceiling Q16 named is lifted** (§7). The honest count of UNEXPLAINED rows is
**zero** — and §5 subjects that number to the adversarial audit the charter demanded, naming
the two weakest explanations in the set and their falsifiers, so a reviewer knows exactly
where to push.

---

## 1. Charter discipline (what this lane did and did not do)

- **Authored** `results/ff-corridor/dispositions/{neiso-t3,pjm-t1f,miso-t1f,nyiso-t1f,neiso-t1f}.json`
  — values machine-extracted from the committed D22 anchor table
  (`results/ff-corridor/benchmark-corridor-anchors.json`) and the committed bundle summaries
  (never typed); verdicts and explanations authored by this session. The convention is the
  corridor memo's, imported whole (`cross-model-corridor-2026-07-13.md` §1): divergence
  **> 15 % or opposite sign/direction** requires a written ours-vs-theirs explanation naming
  the mechanism; any UNEXPLAINED row ⇒ FC-5 FAIL.
- **Re-scored** the five keys through `scripts/forecast_verdict.py` on committed artifacts
  only, adding exactly two inputs (`--corridor`, `--benchmark-corridor`).
- **Benchmarks stayed context, never fit targets** (rule 13 `[R-MEASURED]`, plan §7.6): no
  numeric conformance band exists or was added, no ISO is ranked by corridor distance, and no
  model quantity, input, or threshold moved. The deliverable is the disposition, not the
  closeness.
- **Not done, by charter:** no solve; no mechanism, no `ScenarioConfig` field, no matrix cell
  (rule 28 duties do not fire); nothing in the backcast namespace; no holdout year; no new
  workflow; no hand-edit of any scorer output (the stale `ercot-t1f`/`caiso-t1f` FC-5 detail
  strings stand — §4). The cross-lane re-grade rule was checked live: no committed
  determination flips (§3), so the STOP does not bite.

## 2. What was dispositioned against what

**Model side (the binding constraint — committed snapshots only):**

| verdict key | bundle | window | anchor years used |
|---|---|---|---|
| `neiso-t3` | `results/ff-t3-neiso-golden/bau` (the golden) | 2026–2050 | **2030 / 2035 / 2040** |
| `pjm-t1f` | `results/ff-t1f-s6-pjm/ledger` (capx-S6) | 2026–2030 | 2030 |
| `miso-t1f` | `results/ff-t1f-s123/verify` (S-123-V) | 2026–2030 | 2030 |
| `nyiso-t1f` | `results/ff-t1f-extcap/nyiso` (capx-D2) | 2026–2030 | 2030 |
| `neiso-t1f` | `results/ff-t1f-s4b-ara/neiso` (capx-S4b) | 2026–2030 | 2030 (byte-identical to the golden's 2030 row — asserted at build time) |

**ERCOT and CAISO cannot be dispositioned**, and the reason is model-side, not anchor-side:
their live t1f verdicts are the FFR-3A-2 vintage whose summaries were **never committed**
(the board's own PATH CORRECTION note; `git log --all` confirms no committed
`full_horizon_summary.json` for either at any t1f vintage). A disposition is model-vs-anchor;
with no committed model value there is nothing to disposition, and re-scoring those keys is
impossible from committed artifacts at all (the same reason D8-V's FC-7 pass skipped them).
The ERCOT CDR anchors D22 landed therefore sit unused — **ready and waiting** for the first
ERCOT bundle that commits its summary. The committed `tests/golden/ercot_2026_2040.json`
fixture was considered and rejected as a substitute: it is a regression pin of the reference
scenario at a different vintage, not the scored bundle — authoring rows against it and
registering them under `ercot-t1f` would mix vintages, i.e. manufacture coverage.

**Anchor mapping (the classification traps, resolved before any verdict was written).** Four
AEO series required reconciliation to avoid blaming the model for mapping artifacts — each
documented in every table's `standing_caveats`/row bases (rule 11 pattern):
AEO **"Fossil Steam" = oil + gas steam** (compared against model `gas_ct+gas_st+oil` as one
fossil-peaker/steam block — naive per-tech comparison flips signs, e.g. NEISO gas_st reads
−98 % naive but the block is −4.7 % IN CORRIDOR at 2030); AEO **wind splits onshore vs
offshore** (compared against model generic wind as `wind_total`); AEO **"Wood and Other
Biomass" excludes MSW** (summed with Municipal Waste); AEO **"Diurnal Storage" vs the model's
storage fleet**, which `capacity_by_fuel_mw` structurally excludes (generator fuels only) — the
model value quoted is the registry base fleet (`STORAGE_BASE_FLEET_MW`, EIA-860 2025 ER) plus
the window's `builds_storage_mw` ledger (zero everywhere). CO2 converts MMst → Mt at
0.90718474. AEO's 252 generation anchors are **not dispositioned** — the committed summaries
carry no generation-by-fuel (routed, §6).

## 3. The scores, and the control-first proof

| key | tier | FC-5 before | FC-5 after | rows (IC/EX/UN) | determination |
|---|---|---|---|---|---|
| `neiso-t3` | t3 (**required**) | SKIPPED-required | **CAVEAT** | 33 (16/17/**0**) | HOLD → **HOLD** (unchanged) |
| `pjm-t1f` | t1f (report-only) | SKIPPED | **CAVEAT** | 12 (6/6/**0**) | HOLD → HOLD |
| `miso-t1f` | t1f (report-only) | SKIPPED | **CAVEAT** | 11 (5/6/**0**) | HOLD → HOLD |
| `nyiso-t1f` | t1f (report-only) | SKIPPED | **CAVEAT** | 11 (5/6/**0**) | PROMOTE → PROMOTE |
| `neiso-t1f` | t1f (report-only) | SKIPPED | **CAVEAT** | 11 (5/6/**0**) | PROMOTE → PROMOTE |
| `ercot-t1f` | t1f (report-only) | SKIPPED | SKIPPED (§2 reason) | — | HOLD (untouched) |
| `caiso-t1f` | t1f (report-only) | SKIPPED | SKIPPED (§2 reason) | — | HOLD (untouched) |

Protocol per key (the D8-V pattern): (1) **control** — the scorer run with exactly the
committed inputs reproduces the committed `forecast_verdict.json` **byte-for-byte on every
scorer field** (provenance stamp excluded), all five keys; (2) **treatment** — the same
command plus the two corridor inputs; (3) assertion — **only FC-5 moved**: on `neiso-t3` the
reasons list drops `FC-5 external corridor SKIPPED (required, unscored)` and the caveats list
gains `FC-5 external corridor`; on the t1f keys the only movement is the notes line
`FC-5 external corridor (report-only): CAVEAT` (report-only FC-5 never gates — the scorer's
own applicability test asserts a corridor FAIL cannot move a t1f determination). Registered:
bundle sidecars replaced in place; `ff-verdicts.json` merged (the golden's prior verdict
preserved **in full** at `neiso-t3-pre-fc5`, the D21 precedent; the four t1f priors preserved
in their session chains with stamps, the D8-V precedent); `program-status.json` stamped
(`d25_fc5_dispositions` + the four fc-map FC-5 keys + the NEISO golden append — every other
block asserted byte-identical before write; D19's surfaces untouched).

## 4. The per-row verdict record

Full tables with per-row explanations, bases, citations and standing caveats are the
committed artifacts (`results/ff-corridor/dispositions/*.json`); this section is the reading
view. Divergence = (model − anchor)/|anchor|.

### 4.1 `neiso-t3` — the golden, the t3-required table (33 rows)

| quantity | 2030 | 2035 | 2040 |
|---|---|---|---|
| capacity:total (native) | 32.6 vs 41.3 GW, −20.9 % **EX** | 41.2 vs 42.4, −2.7 % IC | 47.7 vs 49.7, −3.9 % IC |
| capacity:coal | 0 vs 0 IC | 0 vs 0 IC | 0 vs 0 IC |
| capacity:gas_cc (incl CCS) | 11.8 vs 12.8, −8.1 % IC | 12.1 vs 12.8, −5.7 % IC | 13.1 vs 12.8, +2.1 % IC |
| capacity:fossil_peaker_steam | 6.7 vs 7.0, −4.7 % IC | 7.2 vs 7.0, +2.9 % IC | 5.5 vs 8.2, −33.0 % **EX** |
| capacity:nuclear / hydro | +1.0 / −1.4 % IC | IC | IC |
| capacity:solar | 4.7 vs 3.6, +30.3 % **EX** | 9.8 vs 3.6, +171 % **EX** | 14.7 vs 3.6, +307 % **EX** |
| capacity:wind_total | 2.4 vs 8.0, −69.9 % **EX** | 5.1 vs 9.0, −43.5 % **EX** | 7.4 vs 14.7, −49.8 % **EX** |
| capacity:storage | 0.77 vs 1.76, −56.2 % **EX** | **EX** | **EX** |
| capacity:biomass_waste | 1.05 vs 0.86, +22.1 % **EX** | **EX** | **EX** |
| co2 | 14.7 vs 9.3 Mt, +58.4 % **EX** | −2.0 % level, opposite slope **EX** | 4.5 vs 10.5 Mt, −57.4 % **EX** |

The co2@2035 row is deliberately EXPLAINED rather than IN CORRIDOR despite the −2.0 % level:
the trajectory **directions are opposite** (model falling ~0.9 Mt/yr through 2035, AEO
rising), the levels merely cross there, and the convention's opposite-direction trigger binds
regardless of level agreement.

### 4.2 The t1f tables (2030)

| quantity | PJM | MISO | NYISO | NEISO |
|---|---|---|---|---|
| capacity:total | −10.4 % IC | −14.1 % IC | −22.4 % **EX** | −20.9 % **EX** |
| capacity:coal | 31.6 vs 13.1, **+140 % EX** | 41.2 vs 18.6, **+121 % EX** | 0 vs 0 IC | 0 vs 0 IC |
| capacity:gas_cc | −6.6 % IC | +3.2 % IC | 12.2 vs 9.9, **+23.4 % EX** | −8.1 % IC |
| capacity:fossil_peaker_steam | 43.5 vs 51.4, **−15.4 % EX** | 37.5 vs 64.9, **−42.2 % EX** | +7.3 % IC | −4.7 % IC |
| capacity:nuclear | +2.4 % IC | −11.6 % IC | +0.6 % IC | +1.0 % IC |
| capacity:hydro | +3.8 % IC | +8.1 % IC | +1.0 % IC | −1.4 % IC |
| capacity:solar | **−1.9 % IC** | 7.0 vs 22.4, **−68.7 % EX** | 3.3 vs 6.6, **−49.4 % EX** | +30.3 % **EX** |
| capacity:wind_total | 12.5 vs 32.5, **−61.6 % EX** | −6.6 % IC | 3.4 vs 8.1, **−58.1 % EX** | −69.9 % **EX** |
| capacity:storage | 0.5 vs 6.4, **−92 % EX** | 0.8 vs 4.7, **−83 % EX** | 0.25 vs 6.5, **−96 % EX** | −56 % **EX** |
| capacity:biomass_waste | +99 % **EX** | +122 % **EX** | +73 % **EX** | +22 % **EX** |
| co2 | 388 vs 232 Mt, **+67 % EX** | 387 vs 217 Mt, **+79 % EX** | **+8.1 % IC** | +58 % **EX** |
| peak_demand (PJM_LOAD_2026) | 172.7 vs 183.0 GW, **−5.6 % IC** | — | — | — |

Notable agreements, for the record: PJM solar (−1.9 %), PJM peak against PJM's own load
forecast (−5.6 %, with the corridor memo's D7 compensating-omission caveat carried — the
model's demand path has no explicit data-center block while PJM's forecast embeds contracted
large loads), NYISO co2 (+8.1 %), MISO wind (−6.6 %), and gas-CC aggregates everywhere but
NYISO.

### 4.3 The mechanism index — every explanation's named mechanism, once

1. **Coal retention (PJM +140 %, MISO +121 %, and the dominant term of both co2 rows).**
   Ours: exits are step-0 confirmed instruments only — S6 §7.3 *measured* the economic screen
   retiring nothing in PJM 2026–2030 (every exit Bruce-Mansfield-class/p602 instrument rows);
   S-123-V's measured MISO exit list is oil/gas_st/nuclear/biomass with no economic coal.
   Theirs: AEO2025 retires coal on CAA §111 compliance dates frozen into its Dec-2024 law
   baseline (pre-OBBBA) — a regulation the model deliberately does not hard-code (corridor
   memo D4/D8 precedent: a policy-input divergence, not evidence of retirement skill either
   way; D14's exit-recall caveat rides).
2. **Zero storage entry (all four ISOs, −56 % to −96 %).** Golden §6.3.1: under curve-ON the
   arbitrage+RA value stack never clears storage in any of 25 years; every bundle's
   run_config records the pre-R-A unarmed posture (`storage_entry_availability_gate=false`,
   `storage_entry_cost_normalized_rank=false`) and owner ruling R-A armed both **after** these
   solves — the routed re-solve question (golden §5.1(b)/§8.1), which this corridor now shows
   is a cross-ISO divergence family, not a NEISO curiosity.
3. **No state-procurement build channel for offshore wind (NEISO/NYISO/PJM wind_total −50 %
   to −70 %).** OSW is an available entry tech (`offshore_wind_available_year=2030`) that the
   merchant CONE screen has never selected in any committed bundle through 2050; AEO carries
   the contracted OREC pipelines (6.4/4.4/16.2 GW by 2030). The divergence is which
   *instrument* builds clean capacity — procurement (theirs, unrepresented) vs merchant screen
   + capped RPS (ours).
4. **ACP-pinned RPS duals redirect the model's clean build into utility PV (NEISO solar +30
   → +307 %).** The committed `rps_dual` sits at every ISO's ACP ceiling in every committed
   year (NEISO $50, PJM $45, NYISO $40, MISO $30) — the constraint escapes to its cap; the
   entry machinery answers with the cheapest eligible VRE (PV, in the golden's alternating
   anti-cobweb cadence) while AEO satisfies the same New England policy with OSW. Mechanisms 3
   and 4 are the same divergence seen from opposite sides.
5. **The CCS retrofit wave under 45Q plus the resolved carbon signal (every ISO's ~9.0 GW
   gas_cc_ccs by 2030; the NEISO co2 sign flip).** The spec-§5.6 screen converts at its
   3 GW/yr/ISO cap from 2028 under the 45Q window (`ira_ccus_45q_last_year=2032`). The
   carbon leg is per-ISO and D23-corrected: the `carbon_price` **field** is 0.0 everywhere,
   but for NEISO/NYISO it **resolves to the armed RGGI program's projection** — for NEISO
   $26.05/t (2026) escalating at the published 7 %/yr CCR rate to $132.16/t (2050)
   (D23 §2) — while PJM (partial-footprint registry gated off) and MISO (no program) resolve
   to zero, so there 45Q alone carries the retrofit. The wave reaches 100 % of the NEISO CC
   fleet by 2033 and drives model CO2 down −80 % while AEO's NE CO2 *rises* — AEO also
   carries RGGI, at a far lower allowance-price path, and retrofits nothing. D21 measured
   the wave in its paired arms; **D23 attributed the P1 FAIL to the arm construction** (a
   nonzero `carbon_price` override *replaces* the resolved signal, so the $25 arm *cut* it
   by up to $107/t) — the screen's carbon response is sign-correct, and the corridor
   divergence is a divergence in carbon-price paths and retrofit response, each leg
   checkable, not a model defect claim.
6. **Rate-limited backstop vs AEO's gas build wave (PJM peaker block −15.4 %, MISO −42 %,
   NEISO@2040 −33 %).** Ours: PJM's only CT builder is the adequacy backstop at the BLK-10
   ladder budget (measured 843/1,686/1,371 MW, S6 §7.2), seeded at PJM's smallest historical
   CT build rate; MISO's window has *measured zero* economic entry and zero backstop
   (S-123-V §6); NEISO's economic entries are 100 % gas-CC. Theirs: AEO's national gas revival
   (CT 44.5→85.1 GW in Midcontinent, 38.9→71.3 in PJM across 2030→2040 — committed anchor
   slopes; corridor memo D3).
7. **Measured-registry base vs AEO baseline (NYISO gas_cc +23.4 %).** Split quantitatively:
   +1.0 GW is the D2-extcap-measured economic CC entry; the remaining ≈1.3 GW is AEO's 2030
   value sitting *below* the measured EIA-860 operable NYCA CC fleet the model starts from —
   attributable to EMM plant-assignment and/or AEO's NY state-policy (CLCPA/CES) attrition
   handling. The Gold Book (missing source 5) is the named arbiter.
8. **Entry-screen solar economics (MISO −68.7 %, NYISO −49.4 %).** MISO: measured zero
   economic entry of any tech and zero planned solar in the committed-status pipeline, *with*
   `entry_vre_capacity_revenue=true` — so the gap is screen economics, not revenue plumbing;
   the known zero-solar-entry family (BLK-8 was the ERCOT measurement; the MISO evidence here
   is this bundle's own). NYISO: +1.8 GW measured additions vs AEO's CES-program build, the
   procurement-channel divergence again.
9. **Sector-boundary basis (biomass_waste rows, +22 % to +122 %).** AEO's Electric Power
   Sector capacity excludes end-use/CHP wood; the model fleet is the EIA-860 grid registry
   including IPP/CHP units. Documented basis mismatch on classes ≲2 % of fleet (rule 11,
   the D22 CDR precedent).
10. **Component-sum totals (NEISO@2030 −20.9 %, NYISO −22.4 %).** Each total-row deficit
    closes as the sum of this table's own named component gaps (storage + OSW + solar/CT ±
    offsets) — no residual is unaccounted.

## 5. The adversarial audit of "zero UNEXPLAINED" (the charter's own trap, faced)

The charter warned the failure mode is not fudging a number but writing a vague explanation
that sounds like one. Standard applied to every row: the explanation must name a specific
checkable object — a config field, a measured ledger entry, a screen, a committed dual, a
source-side assumption with its citation — on *both* sides of ours-vs-theirs. Rows that
survive weakest, named so a reviewer knows where to push:

- **NYISO gas_cc (+23.4 %, mechanism 7).** The model-side leg is measured; the AEO-side leg
  names two candidate mechanisms without committed evidence discriminating between them
  (AEO's regional detail is not on disk). Falsifier: the 2026 Gold Book's CC fleet table —
  if it shows the NYCA CC fleet at ~12 GW with no announced exits, the AEO-side attribution
  stands; if it shows contracted attrition, the row should be re-authored. This is the
  single row a landed source could flip, and the strongest concrete argument for source 5.
- **MISO fossil_peaker_steam (−42.2 %, mechanism 6).** Two of three legs are measured
  (zero entry; the oil exit); the third — a residual base-fleet offset attributed to
  EMM-footprint/classing — is bounded by the committed AEO slope but not decomposable
  without AEO's (un-intaken) base-year value. Falsifier: intaking AEO's 2024/2026 rows, or
  MISO Futures' capacity outlook.
- **NEISO co2@2030 (+58.4 %, mechanism 4/5).** The dispatch split behind it is inferred from
  capacity + cost parameters because no generation-by-fuel is committed — stated in the row.
  Falsifier: the §6 reporting extension; the row's mechanism would then be directly readable.

None of the three fails the convention — each names its mechanism and its check — but a
reviewer auditing this corridor should start there. Everything else in the table rests on a
measured ledger entry, a committed dual/config field, or a documented source assumption.

## 6. Routed to the director (none actioned here)

1. **Trajectory reporting grain** (blocks 252 anchors): `run_full_horizon.extract_trajectory`
   carries no generation-by-fuel, and `capacity_by_fuel_mw` excludes LP storage resources
   (`storage_mw` is `cap.get("storage")` over generator fuels — 0.0 by construction even for
   a 17 GW ERCOT battery fleet). Extending the summary (gen-by-fuel + a real storage column)
   makes the energy-mix corridor dispositionable and removes a standing basis caveat. A
   reporting change, no mechanism.
2. **ERCOT/CAISO t1f committed-summary gap** (blocks their FC-5 forever until cured): their
   next solve/re-score lane should commit `full_horizon_summary.json` + `run_config.json`
   (the other four bundles' pattern) and inherit the corridor inputs; ERCOT's CDR anchors —
   including the reserve-margin row FC-5 can uniquely use — are landed and waiting.
3. **The R-A storage re-solve question, strengthened:** the golden already routed it
   (§5.1(b)); this corridor shows the zero-storage-entry divergence is the largest
   cross-ISO family in the table (−56 % to −96 %, four ISOs). Whatever the owner decides on
   the second campaign, the armed-posture arms would move the corridor's biggest row family.
4. **The 45Q CCS wave is cross-ISO and carbon-price-independent in two ISOs** (~9 GW in every
   ISO by 2030, mechanism 5): with D23 having cleared the model's carbon-response sign, the
   remaining corridor question is the conversion *pace* — the screen retrofits at its 3 GW/yr
   cap even where the resolved carbon signal is zero (PJM/MISO, 45Q alone), reaching fleet
   fractions AEO2025 reaches nowhere. Explained here (named revenue legs), but whether that
   pace is the intended reading of spec §5.6's economics is a question for a mechanism lane —
   as a divergence-vs-every-external-view, not a sign defect.
5. **Missing sources, ranked by how much each would change this picture** (charter question):
   - **(5) NYISO Gold Book 2026 — first.** It arbitrates the weakest authored explanation in
     the set (§5), anchors the ISO with the largest AEO-only divergences (storage −96 %,
     wind −58 %), and its Table V-1 is already the repo's own extcap source — vintage-aligned.
   - **(6) ISO-NE CELT 2026 — second.** The only t3-**required** FC-5 table is currently
     single-source (AEO alone); CELT's energy/peak rows plus the D12 winter-flip shape anchor
     would put the ISO's own view under the golden's corridor, where it matters most.
   - **(2) NREL StdScen 2024 — third.** The only possible second *outlook* opinion: every
     AEO-side mechanism claim (its CT wave, its coal exit) currently has no independent
     model-to-model triangulation. Unreachable in-session (egress policy); needs an
     out-of-session download.
   - **(8) MISO Futures — fourth** (would triangulate the corridor's largest-magnitude
     divergences: coal +121 %, solar −69 %, CT block −42 %); **(7) CAISO IEPR — last**, moot
     until item 2 gives CAISO a committed bundle.

## 7. The answer to the director: is the t3 ceiling lifted?

**Yes.** Q16's ceiling was that FC-5 and FC-6 — both REQUIRED at t3 — could not be scored on
any golden for want of instruments, so no ISO could grade better than HOLD *regardless of
model quality* (golden finding §8.3: "a rubric-level ceiling, not a NEISO finding"). D21
built and executed FC-6 (graded: FAIL on P1 — which D23 has since attributed to the arm
construction rather than the model's sign; the committed FC-6 FAIL stands as scored, per
D23's own charter, and its repair is instrument-side). D25 authored the FC-5 dispositions
and scored them (graded: CAVEAT, 0 UNEXPLAINED). On the re-scored
`neiso-t3`, **no required category reads SKIPPED any more** — a golden campaign can now be
graded on all required categories, end-to-end, from committed artifacts.

What the lifted ceiling reveals is the instrument working as designed: the golden's
determination is **HOLD on six FAILing gates** (FC-1 I3 dump, FC-2 cobweb, FC-3 hindcast
bands, FC-4 crossover, FC-6 P1 as scored (D23: instrument-side repair), FC-7 unattested)
**plus** the FC-7 golden attestation — all model-quality, instrument-repair and attestation
blockers now, with **zero instrument-absence debt**. FC-5 itself reads CAVEAT, not PASS, and
its 41 explained divergences concentrate in exactly the families the program has already
routed (storage entry / R-A; the 45Q-plus-RGGI CCS wave / D23; the procurement-channel gap;
coal-policy divergence). Divergence was not failure; there was no
unexplained divergence to fail on; and the one instrument that could have been defeated by
hand-waving instead carries 78 rows a reviewer can check, each against a named mechanism.

---

*Produced 2026-09-01 (D25, Fable, zero solves). Committed deliverables: the five disposition
tables under `results/ff-corridor/dispositions/`; five re-scored bundle
`forecast_verdict.json` sidecars; `ff-verdicts.json` (prior golden verdict preserved at
`neiso-t3-pre-fc5`); `program-status.json` (`d25_fc5_dispositions` stamp, four fc-map FC-5
keys, NEISO golden append); this finding. Scoring commands and the control/treatment diffs
are reproducible from the committed inputs named in §3.*
