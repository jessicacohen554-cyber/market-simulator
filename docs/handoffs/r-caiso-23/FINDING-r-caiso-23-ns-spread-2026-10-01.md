# FINDING — R-CAISO-23: the midday RT north–south spread. Zero LP. No admissible lever. Nothing built.

Keeper `2026-09-30-caiso-r20-overnight` (bundle `rcaiso20_A_span`, 2022–25), unchanged.
Probe: `scripts/probes/_rcaiso23_ns_spread_phase0.py`. Output: `results/calibration/_rcaiso23/ns_spread_phase0.json`
(gitignored scratch; every number cited is below).
Clock and hubs: R-CAISO-21's (`_rcaiso21_evening_phase0.measured`), fixed-PST, RTM, TH_NP15 / TH_ZP26 / TH_SP15.
Window h10–16. "Body" = hours whose 3-hub RT mean is ≤ $200 (R-CAISO-22's tail removed).

## 0. Correction to the charter: the spread is collapsed, not wrong-signed

The handoff's "wrong sign" is the sign of the *residuals* (south over, north under). The model's spread
itself has the right sign. It is about 5–10 % of measured size:

| Year | NP15 − SP15 model | measured mean | measured median |
|---|--:|--:|--:|
| 2022 | +1.3 | +16.0 | +4.3 |
| 2023 | +0.8 | +15.3 | +4.5 |
| 2024 | +0.6 | +19.5 | +9.4 |
| 2025 | +0.8 | +11.4 | +6.8 |

The Jan-2024 tail hours (§4) point the **same** way (NP15 ≫ SP15), only much larger. R-CAISO-22 §5's
"reversed sign" statement is withdrawn.

## 1. The whole step is on Path 15

Body hours, h10–16, $/MWh. "> $15" = hours with the spread above $15 (caiso-215's split statistic).

| Year | Path 15 (NP15−ZP26) model | measured | > $15 model / meas | Path 26 (ZP26−SP15) model | measured |
|---|--:|--:|--:|--:|--:|
| 2022 | +2.1 | +16.3 | 31 / 772 | −1.1 | −3.2 |
| 2023 | +1.5 | +17.1 | 67 / 815 | −0.6 | −1.8 |
| 2024 | +0.9 | +19.3 | 7 / 1,031 | −0.2 | −0.1 |
| 2025 | +0.9 | +11.6 | 11 / 733 | −0.1 | −0.2 |

Path 26 is already right. The defect is one cut.

Levels (body): the residual is a south over-price and a north under-price of similar size. In 2024:
ZP26 $21.4 model vs $10.6 measured; SP15 $21.6 vs $10.7; NP15 $22.2 vs $29.9.

## 2. What sets the split: stranded southern surplus behind an element limit

Measured Path-15 spread by measured curtailment state (CAISO Production & Curtailments, h10–16, body):

| Year | No curtailment | Local only | System | corr(spread, local MWh) |
|---|--:|--:|--:|--:|
| 2022 | +12.5 | **+26.2** | +8.8 | 0.19 |
| 2023 | +5.9 | **+27.2** | +8.4 | 0.37 |
| 2024 | +7.4 | **+26.7** | +13.3 | 0.45 |
| 2025 | +7.7 | **+16.3** | +6.2 | 0.37 |

The model's Path-15 spread is +0.9 to +2.5 in every bin.

- Real congestion sits in **local**-curtailment hours: southern solar the grid cannot move north.
  That matches caiso-219: the off-peak binding is the Gates–Midway complex at Path 15's ZP26 end.
- Measured local curtailment midday is 0.92 / 1.54 / 2.33 / 2.29 TWh. System curtailment is 0.26 / 0.51 /
  0.19 / 0.57 TWh.
- In the model the cut is one 5,400 MW aggregate link with directional ratings (caiso-163). Southern
  surplus rarely exceeds it (caiso-216: 17/234/289 h over the rating vs 1,310/1,691/1,347 measured
  split hours). The model spills pooled, not locally (caiso-232). So the LP prices one pool, gas-marginal
  or at the spill floor. The south is then too high and the north too low.
- Reality binds element by element far below 5,400 MW (caiso-218, DMM element census).

**Mechanism:** the missing price is the shadow price of element-level limits on the Path-15 / Gates–Midway
complex. The model's aggregate cut cannot reach it, and no published operating-limit series exists to
build the real one.

## 3. The seams do not set it

Body hours, h10–16:

| Year | PNW node − NP15, model | Malin DAM − NP15 RT, meas | DSW node − NP15, model | Palo Verde DAM − NP15 RT, meas |
|---|--:|--:|--:|--:|
| 2022 | −5.9 | −0.5 | −8.6 | −8.2 |
| 2023 | −6.1 | −1.0 | −6.9 | −9.8 |
| 2024 | −4.9 | +0.1 | −7.4 | −16.8 |
| 2025 | −4.9 | −0.7 | −6.1 | −12.2 |

- The model's PNW node sits at NP15 minus the $4 wheel and losses, so it follows NP15 rather than setting it.
  Malin is at NP15 parity in reality, so the north's under-price is the same object seen from the seam.
- Measured Palo Verde tracks the **south** (2024: $13.1 vs SP15 $10.7). The model's DSW node is $6.8 below its
  own SP15. A cheaper south seam would move SP15 the right way. But the gap is internal (§1), and the
  WOR / DSW import family is K / R / G (caiso-167; `import_hub_pricing` K). The DSW fold residual stays
  ledgered (R-CAISO-20).
- WEIM clean rungs land at both ends. Per-corridor model flows are not in the committed sidecars, so this
  census cannot split them. They cannot create a Path-15 shadow price either way.

## 4. The 7 Jan/Oct-2024 tail congestion hours

| PST | Measured NP15 / ZP26 / SP15 | Model | Model PNW node | Malin DAM | Local curt MWh |
|---|---|---|--:|--:|--:|
| Jan 13 19:00 | 301 / 210 / 161 | 154 / 151 / 151 | **0.0** | 195 | 0 |
| Jan 15 08:00 | 850 / 474 / 76 | 156 / 150 / 150 | **0.0** | 209 | 257 |
| Jan 15 09:00 | 1,217 / 641 / 86 | 149 / 144 / 144 | **0.0** | 177 | 377 |
| Jan 15 10:00 | 565 / 332 / 105 | 147 / 142 / 142 | **0.0** | 180 | 996 |
| Jan 16 09:00 | 709 / 182 / 79 | 150 / 145 / 145 | 149.9 | 219 | 803 |
| Oct 7 16:00 | 390 / 129 / 86 | 62 / 59 / 60 | 62.1 | 70 | 88 |
| Oct 7 18:00 | 688 / 133 / 72 | 62 / 59 / 60 | 62.1 | 116 | 0 |

- These are mostly **morning** hours (h8–10), not h10–16. Only 3 fall inside the midday window.
- **January:** the north is short while the NW is short (Malin $177–219). The south strands local surplus.
  On Jan 13 and 15 the model's PNW node prices at **$0**. The node is long: the 2.4 GW firm floor
  (R-CAISO-22 §2) arrives regardless. That is link 8's object (an NW-stress import driver), and this table
  is evidence for it.
- **Oct 7:** Malin is at $70–116, so there is no NW stress. This is an internal north constraint with no
  measured driver in the repo.

## 5. Matrix check

| Candidate | Status |
|---|---|
| Static Path-15 cap or directional rating re-measure | `measured_interface_limits` K. caiso-218: the static-limit class is measured insufficient (no single cap reproduces the non-monotone split vector). |
| Sub-zonal FSNO pocket with DMM element caps | `caiso_fsno_subzonal_topology` **R** (caiso-224, caps falsified F1/F2). Re-arm only via caiso-222 W-2/W-3 or a backcast-admissible transmission-outage derate intake. Neither exists. |
| Published Path 15/26 operating-limit series | None for 2023–25 (TTC/ATC discontinued 2018-11, caiso-218). Constraint shadow prices are an outcome, inadmissible as input (rule 13). |
| Gen-pocket export limit from deliverability studies | caiso-219: it is accreditation headroom, not a flow rating (4 misalignment axes). |
| Measured local curtailment as an input | It is a dispatch outcome. Pinning it is rule-13 forbidden. Pre-LP derate `caiso_solar_deliverability` lowers southern supply; it raises the south price and cannot create separation. |
| Zonal generation membership | `path15_load_split` K, gen-side crosswalk K (caiso-220), already armed. |
| Diurnal amplitude | `diurnal_price_amplitude` U is defect measurement (caiso-202/215/232), not a mechanism. |
| Any locational repricing as a C3a lever | Non-lever by construction (caiso-230 DO-NOT-REDO item 2). The spread is a C3b / D-A fidelity object. |
| NW-stress import response (Jan hours) | Link 8 (R-CAISO-26), queued. |

**No admissible, structural, measured lever.** No cell tested, so no cell moves.

## 6. Decision

- Nothing built, no PRECOMMIT, no shard, no solve. The keeper is unchanged.
- The midday spread is closed in this link as a data-availability limited object. Its only re-arm route is a
  measured, backcast-admissible element-limit or transmission-outage derate series for the Path-15 /
  Gates–Midway complex.
- The Jan-2024 PNW-node-at-$0 rows route to link 8.
- The next step goes to the owner as a decision card (§7).

## 7. Owner ruling

Decision card, 2026-10-01. All three options were selected:

1. **Close link 5, go to link 6.** The midday spread is ledgered as data-availability limited: a C3b / D-A
   fidelity object, not a C3a lever. Nothing built. R-CAISO-24 (battery-disaggregation scoping) is next.
2. **Route the Jan-2024 rows to link 8.** §4 (model PNW node at $0 while Malin was $177–219) is evidence for
   R-CAISO-26's NW-stress import-driver scoping.
3. **Queue a derate-data scoping**, as link 9 (R-CAISO-27), after link 8. Scoping only, no build: look for a
   measured, backcast-admissible Path-15 / Gates–Midway transmission-outage or derate record for 2022–25.
   This is the only re-arm route for `caiso_fsno_subzonal_topology`.
