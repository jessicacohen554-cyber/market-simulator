# FINDING — caiso-139: the dump-cost guard was an **incomplete enumeration**, not a wrong price — `build_cost_vector`'s "no row may generate purely to dump" invariant was taken over the renewable/storage credit set only, so every measured-hub import tranche priced below −dump_cost slipped under it. Widened to its own stated domain (`dump_cost_full_offer_domain`), the 0.531 TWh (2024) / 0.035 TWh (2025) of phantom tranche revenue is eliminated exactly, the CA-side LP is byte-identical, and the WECC nodes reprice from the −$26.001 dump optimum to **hub + wheel + ε — the marginal delivered import offer, exact to $0.0000 in 100 % of all 212 former dump hours.**

Charter: the caiso-139 session brief (the caiso-138 §B β filing, handed to its
own charter there). All D-gates (D1–D4) plus the cross-ISO census were passed on
committed bytes before any solve. Instrument (committed, no LP, no solver):
`scripts/probes/_caiso139_dump_cost_blindspot.py` (§A–§E). A/B scorer:
`scripts/probes/_caiso139_dumpguard_ab.py`. Pre-registration (committed and
pushed before either arm solved):
`PREREG-caiso139-dump-cost-offer-domain-2026-07-29.md`.

Keeper at session start: `2026-07-29-caiso138-envelope-clip`
(`results/calibration/caiso138_envclip_B`, NOT-YET, fail {C3a-2025, C3c}).

---

## §A — D1: the defect, quantified on the NEW keeper

The caiso-138 clip removed the α (firm-vs-cap) component, so what remains at the
WECC pseudo-nodes is β and nothing else:

| year | WECC_PNW dump | WECC_DSW dump | dominant tranche output inside those hours |
|---|---|---|---|
| 2023 | 0.0000 TWh / 0 h | 0.0000 TWh / 0 h | — (no dump at all) |
| 2024 | 0.0088 TWh / 5 h | **0.5218 TWh / 175 h** | `DSW_surplus_clean` 0.8157 TWh, `DSW_CCGT` 0.0582, `WECC_scarcity` 0.0500, `DSW_CT` 0.0302 |
| 2025 | 0.0141 TWh / 8 h | 0.0208 TWh / 24 h | `DSW_surplus_clean` 0.1214 TWh, `DSW_solar_PV` 0.0075; PNW `PNW_midC` 0.0141 |

Node λ is the −$26.001 dump optimum in the median of every dump-hour set.

## §B — D2: the attribution is exact in BOTH directions

The objective's guard was `dump_cost = 26.001` in all three years (wind −26.000 /
solar −20.000 / −storage_eac −0.000). Against the LP's own reconstructed offer
array (`run_year(fleet_only=True)` → `mc_base`, the assembled P0 objective with
every pricing overlay applied):

| year | rows below −dump_cost | PNW dump hrs WITH a gamed offer | DSW dump hrs WITH one | dump hrs WITHOUT one |
|---|---|---|---|---|
| 2023 | **0** | — (0 dump hrs) | — (0 dump hrs) | **0** |
| 2024 | 7 (`PNW_midC`, `DSW_CCGT`, `DSW_CT`, `WECC_scarcity`, `DSW_surplus_clean`, `DSW_overnight_clean`, `DSW_daytime_clean`) | **5/5** | **175/175** | **0** |
| 2025 | 4 (`PNW_midC`, `DSW_surplus_clean`, `DSW_overnight_clean`, `DSW_daytime_clean`) | **8/8** | **24/24** | **0** |

Every dump hour carries a producible offer below −dump_cost; **no** dump hour
lacks one; and 2023 — the one year with no row below the guard — has no dump.
Deepest offers −29.693 / −58.239 (2024 PNW/DSW) and −31.437 / −36.261 (2025),
i.e. **$3.69–32.24/MWh of pure generate-to-dump profit**. The converse census
(DSW 2024: 241 gamed-offer hours, of which 175 dump) shows a gamed offer forces
a dump only where the corridor is already cap-bound — the mechanism, not a
coincidence.

**The defect is an enumeration bug, not a mispriced dump.** `build_cost_vector`'s
own comment states the invariant — the dump cost "must also exceed the magnitude
of any production credit… otherwise the LP would overgenerate … and dump the
surplus" — but the minimum ran over `(wind_mc, solar_mc, −storage_eac)` only.
The CAISO per-hub tranches are priced at their own measured hub
(`inject_caiso_per_hub_intertie_prices`: `mc = hub + wheel + carbon + ε`), and
Palo Verde crashes to −$58.24/MWh in the desert-SW solar glut.

## §C — D3: the CA-side invariance is provable, not estimated

Three facts off the committed sidecars:

* **CA zones never dump** — 0.000000 MWh total, 0 zone-hours > 0, all years.
* **CA λ never reaches the guard** — min CA λ **−20.0000** vs −dump_cost
  −26.0010 (repaired −58.2397 / −36.2618); zone-hours at λ ≤ −dump_cost+0.01: 0.
* **The corridor is at cap in 100 %** of every affected hour (PNW 5/5 and 8/8,
  DSW 175/175 and 24/24, flow ≡ group cap to 1e-3).

The Dump column's reduced cost is `dump_cost + λ_z`. **Raising** dump_cost can
only *raise* it, so a column already at its lower bound stays there: the CA
primal and every CA dual are unchanged, and the delivered corridor flow in the
affected hours is the cap before and after. The E1/E2 prediction was therefore
analytic. The caiso-134 SSB replacement-ladder was **not invoked, and could not
be**: its trigger (corridor flow changing in any hour) cannot fire when the flow
is cap-bound in every hour the delta touches.

## §D — D4: zero DOF, and why the mask is load-bearing

| year | current | repaired | driver row | row min mc | sink rows | sink mc min |
|---|---|---|---|---|---|---|
| 2023 | 26.0010 | **26.0010** | `WECC_DSW_DSW_overnight_clean` | −18.4721 | 2 | −18.5587 |
| 2024 | 26.0010 | **58.2397** | `WECC_DSW_DSW_overnight_clean` | −58.2387 | 2 | −58.2407 |
| 2025 | 26.0010 | **36.2618** | `WECC_DSW_DSW_overnight_clean` | −36.2608 | 2 | −36.4392 |

No threshold, percentile, margin or residual-derived value enters — the bound is
read off the offer arrays the LP already carries, per solve. The producible mask
(`pmax > 0`) is a structural row property, and it is **load-bearing**: the export
sinks (`import_nodes.build_export_sinks` — `pmax 0`, `pmin −cap`) sit *below* the
producible minimum (2024: −58.2407 vs −58.2387), so dropping the mask would
inflate the guard off a **withdrawal** price that is a willingness-to-pay, not a
production credit.

**The rejected alternative (rule 14).** The other repair — floor the offending
offers at −dump_cost, which is exactly what `data/virtual_bids.py::_inc_offer_floor`
does for the PJM DA virtual INC rungs — is refused here. That treatment is
"representation-exact" *because on PJM's measured corpus it never binds* (minimum
rendered INC rung ≈ −$1.3/MWh against a ≈ −$27 floor). On this corpus it would
actively rewrite measured hub prices (2024 DSW: −58.24 → −26.00). Burying an
incomplete guard inside a measured input is precisely what rule 14
[R-ACCURATE] forbids; the guard is the thing that was wrong, so the guard is
what moves.

## §E — cross-ISO reach (rule 25), settled ex ante

`dump_cost` is ISO-agnostic LP infrastructure, so the charter's ask was answered
before the change was written — every ISO keeper's own fleet reconstructed, all
three years:

| ISO | keeper bundle | min producible mc (2023/24/25) | verdict |
|---|---|---|---|
| CAISO | `caiso138_envclip_B` | −18.47 / **−58.24** / **−36.26** | guard widens in 2024–2025 |
| ERCOT | `ercot137_margin_arm` | −2.84 / +1.40 / +1.40 | **UNCHANGED (byte-identical)** |
| MISO | `miso101_tempgrain_B` | +1.40 / +1.40 / +1.40 | **UNCHANGED** |
| NEISO | `neiso61_netrev_margin` | +1.40 / +1.40 / +1.40 | **UNCHANGED** |
| NYISO | `nyiso96_ctamort` | +1.40 / +1.40 / +1.40 | **UNCHANGED** |
| PJM | `pjm137_ctheatrate_B` | +1.40 / +1.40 / +1.40 | **UNCHANGED** |

No non-CAISO keeper carries an injectable offer within **$24/MWh** of the guard,
so the repair is **CAISO-only in effect**. PJM's row is measured with
`pjm_da_virtual_bids` disabled (its raw source is not in this container); the
virtual layer is settled **analytically and more strongly than by measurement**:
DEC rows are built `pmax 0 / pmin −peak` (outside the injectable mask by
construction) and INC rungs are floored at `_inc_offer_floor` = `min_credit + ε`,
i.e. `≥ −dump_cost + ε` in every hour by construction — the same invariant this
session repairs, already enforced there on the offer side.

It nevertheless ships **flag-gated, default off**: each ISO's lane arms it on its
own evidence (rule 25), and the gate keeps every pre-existing cache key
byte-stable (registered in the `scenarios.py` cache-key drop list — the pinned
default stays `603c2498bf71d21d`; an armed run enters as `f08e14ff498bfa03`).
The caiso-138 field was the SIXTH miss of that one line, so it was checked here.

## §F — the A/B (arms solved AFTER the prereg was pushed)

Arms: `caiso139_control_A` (keeper recipe, run id `2026-07-29-caiso139-control`)
and `caiso139_dumpguard_B` (+ the flag, run id
`2026-07-29-caiso139-dump-guard-offer`), both `--year 2023 2024 2025` in one
invocation, arms sequential, **both on the same pushed HEAD**.

**Control integrity:** arm A is **byte-identical** to the committed caiso-138
keeper on prices and dumps in all three years (max |Δ| = 0.0) — which also proves
the flag-**off** code path byte-identical on the full solve path.

**Every pre-registered gate passed:**

| gate | prediction | result |
|---|---|---|
| P1 β-dump eliminated | dump ≤ 0.001 TWh, 0 hours, both nodes, all years | **EXACT**: 0.5218 → 0.0000 TWh / 175 → 0 h (DSW 2024); 0.0088 → 0.0000 / 5 → 0 and 0.0141 → 0.0000 / 8 → 0 (PNW); 0.0208 → 0.0000 / 24 → 0 (DSW 2025) |
| P2 E1/E2 | +$0.00 / +$0.00 (±$0.02); stronger form max CA per-zone-hour \|Δ\| = 0 | **+0.0000 all three years**; max CA per-zone-hour \|Δprice\| = **0.0000** — CA-side LP byte-identical, as D3 required |
| P3 rubric | identical to control | **IDENTICAL**: NOT-YET, fail {price_mean (C3a), price_tail (C3c)} both arms |
| P4 2023 null control | byte-identical (guard unchanged in 2023) | **PASS**: max \|Δprice\| 0.000000, max \|Δdump\| 0.000000 across ALL zones incl. WECC |
| P5 node print (reported) | degenerate corner, no longer −26.001 | **an exact identity, not a corner** — see below |

**P5 is the structural confirmation.** In every former dump hour the node now
clears at the marginal tranche's own **delivered** import offer:

    λ_B  =  measured hub  +  OATT wheel  +  ε

verified to **0.0000, max |Δ| = 0.0000, in 100.0 % of all 212 former dump hours**
across both corridors and both years — with wheel = $4.00 (DSW) / $5.00 (PNW)
from `CAISO_IMPORT_DELIVERY_BASIS` and ε = $0.001. Medians: DSW 2024 −26.001 →
**−32.550** vs measured PALOVRDE −36.551 same hours; PNW 2024 −26.001 →
**−26.928** vs MALIN −31.929; PNW 2025 −26.001 → **−30.308** vs MALIN −35.309;
DSW 2025 −26.001 → **−27.729** vs PALOVRDE −31.730. The residual gap to the raw
hub is *exactly* the published point-to-point delivery basis — i.e. it is not a
residual at all, it is the model's delivered-import price by construction. The
phantom energy removed reconciles to the dump exactly (DSW 2024:
`DSW_surplus_clean` −0.3834, `DSW_CCGT` −0.0582, `WECC_scarcity` −0.0500,
`DSW_CT` −0.0302 TWh = −0.5218 TWh).

**Status: keeper CANDIDATE.** All four gates pass, the CA-side series are
byte-identical to the current keeper, and the rubric is unchanged
(NOT-YET, fail {C3a-2025, C3c}) — so this is a pure structural-integrity gain
with zero fit cost. Promotion is an owner act and is **not** claimed here.
Rule-22 LOYO note: the mechanism carries no fitted parameter and its CA-side
effect is exactly zero in every year — nothing to overfit; the criterion is
satisfied degenerately, as for caiso-138.

## §G — DO-NOT-REDO (new, binding)

* **Re-measuring the β dump, its per-node/per-tranche split, the offer-below-guard
  attribution, the CA-dump/CA-λ census, or the cross-ISO guard census.** The
  committed probe carries all of them from committed bytes in minutes.
* **Re-proposing the offer-floor repair** (flooring import tranches at
  −dump_cost, the `_inc_offer_floor` treatment) **as a CAISO lever.** §D: it
  binds on measured hub prices here and is refused under rule 14. The PJM
  precedent does not transfer — there it is a measured no-op.
* **Dropping the `pmax > 0` producible mask** "because the guard should cover
  every negative mc". §D: the export sinks sit BELOW the producible minimum, and
  their negative price is a willingness-to-pay on a withdrawal. Dropping the mask
  inflates the guard off a non-existent production credit.
* **Re-testing the widened guard in ERCOT / MISO / NYISO / NEISO / PJM as a
  fit lever.** §E: measured inert ex ante in all five (nearest offer is $24/MWh
  from the guard). Arming it there is a no-op, not a mechanism.
* **Quoting the remaining WECC node-vs-hub gap ($4–5/MWh) as a pricing defect.**
  §F: it is exactly the published OATT wheel + ε — the delivered-import price by
  construction, verified to $0.0000 in 100 % of hours.
* **Treating the P1 export-sink deletion seam as settled by this lane.** It is
  untouched here and remains the cross-ISO infrastructure lane of
  FINDING-caiso138 §D.

Carried forward unchanged: everything in `FINDING-caiso138` §G, `FINDING-caiso137b`
§6, caiso-137 §7 first bullet, `FINDING-caiso136` §5, caiso-135 §10, caiso-134
§9, caiso-133 §9, caiso-132 §10, caiso-131 §10, caiso-130 §7, caiso-129 §6,
caiso-127 §7.

Next number: caiso-140.
