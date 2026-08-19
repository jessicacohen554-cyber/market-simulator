# FINDING — ercot-223: the keeper's manufactured May-8-2024 shed hour — Phase-0 root cause (offer-as-cost debases the storage SOC shadow against the co-opt's floor-free reserve-headroom value) and the EVENT-REALIZED RELEASE repair

> Status: RECORD. Session ercot-223, branch
> `claude/ercot-223-keeper-shed-8iztwv`. Keeper at dispatch:
> **`2026-08-19-ercot221-arm-adaptive`** (owner-promoted over the recorded
> REJECTED-AS-ARMED G-SHED verdict; both records stand). This lane
> diagnoses and repairs the keeper's one failing kill gate — the
> manufactured 2024 h3066 load shed — under
> `docs/PRECOMMIT-ercot223-event-release-guard-2026-08-19.md` (pushed +
> blob-verified before any solve).
> Phase-0 artifacts: `scripts/probes/ercot223_shed_phase0.py` →
> `results/calibration/ercot223_shed_phase0.json` (read-only, committed
> bundles + committed measured inputs only, no LP).

## 1. The question

2024 hour 3066 (May-8-2024, inside the h17–20 floor window; actual RT
$2,451 — a real storm-evening event hour that recorded NO shed) sheds
17.887 MW under the armed adaptive-expectation floor and not under the
control, although the floor there ($523.12) is far below VOLL ($5,000).
The dispatch card asked Phase-0 to discriminate three candidate
mechanisms: (a) an SOC-path effect, (b) the measured AS carve-out, (c) a
co-opt interaction.

## 2. Verdict on the candidates

**(c) in a precise form, transmitted through (a); (b) is stage-setting
but identical across the two runs and therefore not the discriminator.**

The reserve co-optimization counts storage upward headroom
(cap − Dis + Chg) as reserve supply in the shared headroom rows
(`src/market_sim/model/lp/reserve_rows.py`, pooled spec — the keeper's
`ercot_storage_as_duration_gate` is off, so battery headroom backs every
product row). The adaptive floor enters the LP as a discharge **cost**
through the `p1_storage_discharge_cost` seam. A cost-form offer floor
does two things at once, only one of which is the intended conduct claim:

1. it raises the price at which storage discharge clears (intended —
   price formation), and
2. it **debases the model's PRIVATE value of stored energy** — the SOC
   shadow μ — one-for-one, while the reserve-side headroom value σ
   carries no floor (unintended — the operator's own arbitration).

At every margin the storage fleet then arbitrates
`λ − floor − μ/η` (energy) against `σ` (reserve-counted headroom), and
the floor is missing from exactly one side.

## 3. The measured causal chain (all identities close to numerical precision)

Committed-artifact measurements, control (`ercot221_control_A`) → arm
(`ercot221_adaptive_B`), 2024:

1. **The shed is a system-level 17.887 MW shortage at h3066**, booked in
   South only by solver placement — zonal prices are uniform at VOLL, so
   no transmission constraint separates the zones and the slack's zone is
   degenerate. The control's h3067 Northeast 600.16 MW shed is
   byte-identical in both runs.
2. **μ collapses $575.6 → $184.4/MWh** at the evening margin
   (μ = η·(λ − cost − σ); σ = NonSpin family dual + ORDC-total dual =
   4,290.2 → 4,276.9 at h3066; η = √0.85).
3. **The h3065 pre-peak top-up dies.** The control charges 218.7 MW at
   λ = $2,127 during the forced-deployment hour (refilling the hole the
   261.3 MW deployment floor opens at the measured hourly energy-capability
   cap) because the charge margin σ + μη − λ = **+78.5 $/MWh**; the arm's
   collapsed μ makes the same trade **−224.5 $/MWh** and it charges zero.
   With a ~46 MWh entering gap (per-unit allocation drift from the floor's
   re-timed neighboring days), the arm delivers **207.3 MWh less across
   the two VOLL hours** h3066–h3067.
4. **At h3066 the co-opt swaps the withheld storage into reserves.** The
   arm discharges 195.1 MW less; CT_PEAKER — the only class with headroom
   left — backfills +177.3 MW to its cap; the residual **17.887 MW is
   served by slack at VOLL, and NonSpin held rises by exactly that
   amount** (identity |ΔNonSpin − shed| = 0.0000;
   |Δstorage-headroom + Δthermal-headroom − ΔNonSpin| = 0.0001).
5. **The "arrives empty" SOC story is false.** Both runs exit h3067 with
   fleet SOC pinned at the measured AS-backing freeze — 3,091.5 MWh, the
   `ercot_storage_as_soc_reserve` award×duration floor net of the
   intra-day deployment cumulative — and the post-window discharges are
   exactly the η-scaled freeze releases: control 938.27 MWh at h3068
   (= η·(freeze₃₀₆₇ − freeze₃₀₆₈)) and 127.41 at h3069; the arm bundles
   the same 1,065.69 MWh at h3069, because at h3068 its floored energy
   margin ($794.8 − $523.1 = **$271.6**) is below σ (**$419.2**) where
   the control's unfloored margin ($663.4) is above it — the co-opt
   merit-order flip, priced not shed.
6. **The measured AS overlays — award power dock (3,234 MW at h3066),
   SOC-backing freeze, deployment floor — are identical in both runs.**
   They set the shared evening budget (both fleets drain to the same
   freeze) but discriminate nothing.

Reality check: on the real May-8-2024 evening the fleet discharged into
the $2,451 peak and ERCOT recorded no firm-load shed. The arm withholds
physically-available energy at a real event hour — the ercot-162 failure
mode at single-hour scale, now with the transmission channel measured.

## 4. The structural statement

**The conduct floor is an OFFER — a claim about the storage operator's
energy offer price — and "withhold in anticipation OF the spike" is a
claim about WHEN the fleet releases, not about the social cost of its
energy.** A cleared offer does not withhold physical energy: the real
operator holding out for $5,000 still charges at $2,127 to sell into the
spike, because their private arbitrage value tracks the price, not
(price − their own offer). Offer-as-cost conflates the two, so the LP's
storage behaves as if its own energy were worth (λ − floor) to itself —
at real event hours this manufactures shed that reality did not record.

## 5. The repair — EVENT-REALIZED RELEASE (precommit §1)

Mask the pass-2 floor at in-window hours whose **pass-1 settle basis**
(the identical `_settle_t` the mechanism's own day-max event detector
computes — pure model-path, Amendment-4 basis, zero measured content)
is ≥ `ERCOT_ADAPTIVE_EVENT_USD` ($1,000 — the mechanism's existing
frozen event constant, reused at hour granularity: the hours that MAKE a
day an event day are the release hours). Zero new fitted scalars; one
default-off boolean `ScenarioConfig` field `ercot_adaptive_event_release`
(registered at all four nyiso-119 cache-key points). Pre-measured breadth
from the committed bundles: **2023: 8 of 776** floored window-hours
exempt (the calibration signature survives ≥ 99 % intact); **2024: 5 of
568**, exactly covering the {3065, 3066, 3067} kill window; **2025:
none** (no floors — self-extinction untouched). Driver, window, forward
story and the not-a-shed-hour-patch argument: precommit §1.

## 6. Phase-1 A/B under the precommit §3 kill table

*(completed after the solves; see §7 for the gate table and verdict)*

- **Control** = the CURRENT keeper recipe replayed at HEAD via
  `scripts/replay_keeper.py` (per-year process chain), G-REPRO verified
  sha256-identical to the committed `ercot221_adaptive_B` sidecars BEFORE
  the arm was read.
- **Arm** = the identical replay + `--set ercot_adaptive_event_release=true`.

## 7. Gates and verdict

*(to be completed from `results/calibration/ercot223_gates.json`)*

## 8. Disposition

*(to be completed)*
