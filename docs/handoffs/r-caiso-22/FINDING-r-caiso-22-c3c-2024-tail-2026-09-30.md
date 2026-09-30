# FINDING — R-CAISO-22: the C3c 2024 RT price tail. Zero LP. No admissible lever. Nothing built.

Keeper `2026-09-30-caiso-r20-overnight` (bundle `rcaiso20_A_span`, 2022–25), unchanged.
Probe: `scripts/probes/_rcaiso22_tail_phase0.py` (part A: tail census; `--stack`: zero-LP offer-stack
bound via `reconstruct_bundle_fleet`, the caiso-272 route). Scratch outputs (gitignored):
`results/calibration/_rcaiso22/tail_phase0.json`, `stack_bound_2024.json`.
Clock and hubs: R-CAISO-21's (`_rcaiso21_evening_phase0.measured`), fixed-PST hour-of-year; tail hour =
3-hub (TH_NP15 / TH_ZP26 / TH_SP15) RTM mean > $200. EIA-930 CISO, UTC hour-end − 1.

## 0. The scored miss

C3c = model hours with max-zone price > $200 vs the committed RT actual count (`score_price_tail`,
band [0.5×, 2×]).

| Year | Model | RT actual | Status |
|---|--:|--:|---|
| 2022 | 513 | 510 | PASS (1.01×) |
| 2023 | 60 | 47 | PASS (1.28×) |
| **2024** | **0** | **35** | **FAIL (0.00×) — ledgered** |
| 2025 | 0 | 8 | PASS (small count) |

The model's 2024 annual maximum is **$191.6**, and it reaches $175 in only 26 hours of the year. A pass needs ≥ 18 hours
above $200.

## 1. The 2024 tail has three parts

These are the 33 hours on this probe's clock (35 on the scorer's series; the dates shift by one day on
that series, the count does not).

| Class | Hours | Dates | Measured | Model | NP15−SP15 meas / model |
|---|--:|---|--:|--:|--:|
| Gas event | 21 | Jan 13, 15, 16 (MLK cold snap); Dec 12 | $222 | $168 | +11 / 0 |
| North congestion | 7 | Jan 13/15/16 midday; Oct 7 | $357 | $126 | **+579** / +4 |
| Transient | 5 | May 27, Jul 23–24 (evening) | $488 | $55 | +60 / 0 |

- **Gas event.** On the day's measured CA composite citygate print ($17.34, the MLK weekend package), the
  measured price implies a heat rate of **15.5**. The model's implies **10.3**.
- **Transient.** These hours imply heat rates above 200. They are RT scarcity spikes that no
  energy-cost mechanism can reach at $2.5 gas. caiso-144 found the reserve pool slack in every such hour.
- **North congestion.** Midday Path-15 congestion with NP15 at $500–850 and SP15 near $0. That is the
  midday N–S object, link 5.

## 2. Supply stack vs measured: the event-hour imports

This is model minus EIA-930, in GW. "Event-specific" means tail-hour delta minus the delta in the
same month×hod on non-tail days.

| 2024 class | Demand | Gas | Net import | Model storage net |
|---|--:|--:|--:|--:|
| Gas event, tail | −1.00 | −4.58 | **+2.22** | 1.63 |
| Gas event, event-specific | −0.33 | −2.65 | **+2.29** | +0.48 |
| Transient, event-specific | −1.12 | −2.55 | **+3.89** | +0.93 |

Evenings (h17–22) of Jan 15–16, in GW:

| Source | Net import | Gas | Demand |
|---|--:|--:|--:|
| Measured | 0.6–0.8 | 17.4 | 26.1–26.6 |
| Model | 2.4 | 12.3–12.4 | 24.4–24.9 |

The 2.4 GW is the self-scheduled firm floor, which is identical on non-event days. Measured Malin was
$230–255 in those hours, against a model λ of $175–180, so the Pacific NW was short and the real
import collapsed. **The model's firm floor does not respond.**

**This is 2024-specific, not a tail mechanism.** In the 2022 and 2023 gas events, the event-specific
import delta is **negative** (−1.2 / −0.75 GW): the model imported *less* than its standing offset.
A lever built on it would fix one year's event and move the other two the wrong way.

## 3. The bound that decides it: the offer stack

The keeper's 2024 offer surface was rebuilt with no LP, as in-state CC/CT/ST/oil (`mc_base` × pmax ×
availability). The stack reproduces the solved λ (Jan 15 evening: stack $177.2 vs λ $179.5; Jan 13:
$154.5 vs $155.0).

| Jan 15–16 event hours | At dispatch | +1 GW | +2.3 GW | +4 GW |
|---|--:|--:|--:|--:|
| Stack price | $177 | $190 | **$194–195** | $201–206 |
| Measured RT | $207–286 | | | |

- **Removing the whole event-specific import excess (+2.3 GW of gas) gives ~1 hour above $200** (Jan 16
  h07). Adding the demand and storage deltas (~3.1 GW) still stays below $200.
- Only **+4 GW** crosses $200, and only by $1–6. Measured is $207–286.
- The model's whole CA gas stack at $17.34 tops out near the measured *floor* of the event.

The measured event price is **above the in-state gas stack's own cost at the day's print**. It sits
at import parity with the NW (Malin $230–255). An input that could close it would be:

- a same-day RT gas cost above the next-day weekend-package print, which the repo does not hold (the
  ICE daily index already failed as a hub print, R-CAISO-12); or
- the model exporting into the NW's shortage at Malin. That is the corridor/export family, closed at
  caiso-167 (`caiso_p1_export_sink_seam` R, `caiso_corridor_export_path` R,
  `caiso_node_export_constraint` G).

## 4. Matrix check (before any lever)

Every candidate touches a cell that is already adjudicated, or has no measured state variable:

| Candidate | Status |
|---|---|
| Firm-import floor response to neighbour stress | Same family as `caiso_firm_selfsched_clip` K and `caiso_firm_selfsched_floor` K. caiso-150 §H forbids re-measuring the self-schedule ceiling. caiso-253 already ruled that an import object "needs a state variable neither construction carries, identified from market structure". No measured, forward-regenerating NW-stress driver is in the repo, and the delta is sign-inconsistent across years (§2). **Bounded at ≤ 1 tail hour anyway (§3).** |
| Scarcity / reserve pricing | `energy_reserve_coopt` I, `reserve_pergen` I (caiso-144: reserves slack in the tail hours); `ordc_scarcity_overlay` K, bounded at $0.006/MWh in 2024 (caiso-229). |
| Storage expectation | `ercot_storage_adaptive_expectation` I (caiso-204/205: 0/1/0 spike days). |
| Gas deliverability (SoCalGas OFO) | Killed at gate D1 (caiso-228). |
| Zonal gas basis | `zonal_gas_basis` R. The event evenings are not locational (NP15 ≈ SP15), so it is not the object. |
| Offer basis (RTM bids) | RTM-FLAT (caiso-283): CC peak is bid *lower* in RTM. |

**No admissible, structural, measured lever exists.** No cell was tested, so no cell moves.

## 5. Decision

- Nothing built, no PRECOMMIT, no shard, no solve.
- The keeper is unchanged, and C3c 2024 stays a lone ledgered caveat (rule 22 `[R-C3C]`, non-downgrading).
- The 7 north-congestion hours route to link 5 (R-CAISO-23, the N–S spread). There the sign is
  **reversed** from the chronic midday object: winter-event NP15 ≫ SP15. R-CAISO-23 should include
  these hours in its Path-15 census.
- The next step goes to the owner as a decision card (§6).

## 6. Owner ruling

Decision card, 2026-09-30. All three options were selected:

1. **Close link 4, go to link 5.** C3c 2024 stays a ledgered, non-downgrading caveat. R-CAISO-23 (the
   midday N–S spread) takes the 7 Jan-2024 north-congestion tail hours into its Path-15 census.
2. **Scope same-day gas data.** Scoping only, no solve (queued as link 7, R-CAISO-25): look for a
   measured same-day/intraday CA citygate series for the winter event days.
3. **Scope an NW-stress import driver.** Scoping-only PRECOMMIT, no build (queued as link 8,
   R-CAISO-26): find a measured, forward-regenerating state variable for firm-import delivery when the
   NW/DSW is short. It must state the §2 sign inconsistency and the §3 ≤ 1-hour C3c bound up front.
