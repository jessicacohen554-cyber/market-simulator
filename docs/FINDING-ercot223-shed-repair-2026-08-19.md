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

- **Control** = the CURRENT keeper recipe replayed at HEAD via
  `scripts/replay_keeper.py` (per-year process chain, 2023 → 2024 → 2025
  with `--reuse-solved` byte-copies), registered
  `2026-08-20-ercot223-ctl-headbase`
  (`results/calibration/ercot223_control_replay`).
- **Arm** = the identical replay + the single delta
  `--set ercot_adaptive_event_release=true`, registered
  `2026-08-20-ercot223-arm-eventrelease`
  (`results/calibration/ercot223_release_arm`).
- **G-REPRO, both legs recorded honestly.** The precommit pinned
  "sha256-identical to the committed `ercot221_adaptive_B` sidecars". As
  measured BEFORE the arm was read:
  - **Edit-inertness leg — PASS in the strongest form:** a replay at pure
    `origin/main` 9c3e45c (no ercot-223 edit) is **7/7 hourly sidecars
    sha256-identical** to the HEAD control replay, so the guard code is
    byte-inert with the flag off.
  - **Committed-bundle byte-identity leg — FAIL on pre-existing main
    drift** (commits 41cc6f1 → 9c3e45c, which this session merged on the
    owner's instruction; NOT this session's edit, per the leg above). The
    drift's character, measured: the `adaptive_*` sidecars (pass-1 path,
    P̂, floors) are byte-identical in all three years; 2024
    slack/shed rows and every reserve-family balance reproduce EXACTLY
    (shed set {3066: 17.887106, 3067: 600.157866} to 1e-6; reserve duals
    to 1e-13); prices reshuffle within degenerate ties (2024
    demand-weighted mean 29.14 → 29.22, +0.25 %); and the OFFICIAL
    scorecard is IDENTICAL to the keeper's (C3a-2023 −39.4 %, C3b-2023
    0.723). The A/B is therefore internally coherent at HEAD with the
    keeper's exact baselines.

## 7. Gates and verdict (`results/calibration/ercot223_gates.json`)

| gate | result | verdict |
|---|---|---|
| G-CAP | 0 violations in 26,280 h | PASS |
| G-SPUR | 2023 11 (+2 vs 9), 2024 11 (+0 vs 11), 2025 1 (+0) — bar ≤ +5/yr | PASS |
| **G-SHED (tightened)** | **arm shed sets {} / {3067} / {} — the manufactured h3066 is GONE; zero new shed vs the ORIGINAL 0/1/0** | **PASS** |
| G-OWNER | C3a-2024 PASS, C3a-2025 PASS, C3b-2024 PASS on the official scorecard — all retained | PASS |
| G-BAT | within ±25 % of EIA-930 BAT at tail hours (2024/2025) | PASS |
| G-DOF | ledger delta = the ONE boolean; 9 entries both members, zero residual-sourced; `n_residual` flat | PASS |
| G-D2 | `ercot_storage_adaptive_expectation` attribution row present; D-4 rows identical | PASS |
| G-REPRO | edit-inertness 7/7 sha-identical (pure-main vs HEAD); committed-bundle leg failed on pre-existing drift, attributed §6 | PASS (as attributed) |
| LOYO / G-SAFE | zero new fitted scalars ⇒ LOYO N/A; 2025 arm ≡ control **5/5 sidecars sha256-identical** (the guard can only remove floors; 2025 has none) | as declared |

**Mask breadth realized = the Phase-0 pre-measurement exactly:** 2023
8/776 floored hours masked, 2024 5/568 (the {3065, 3066, 3067} kill window),
2025 zero. The May-8 dispatch reverts precisely as the §3 economics
predicted: the h3065 top-up charge returns (218.7 MW), h3066 discharge
1,994 → 2,189 MW, and the 17.887 MW slack is gone. h3068 keeps its floor
(pass-1 settle $675 < $1,000) so the 938 MWh h3068→h3069 re-timing
persists — priced, not shed.

**Side-effects at full magnitude (Q-B FINAL / R-A — never a gate):**
official C3a-2023 −39.4 → **−39.7 %**, C3b-2023 0.723 → **0.729** (the 8
masked 2023 hours were the ≥$1,000 evenings where the ≤$1,850 floor had
been adding level); probe basis −29.78 → −29.99 %. 2024: C3b 2.3572 →
2.3519 (slightly better), C3a +8.91 → +8.94 %. 2025 byte-identical. C3c
ledgered CAVEAT ×3 carried (74/181, 22/53, 1/31). Determination:
**NOT-YET, fail set {C3a-2023 −39.7 %, C3b-2023 0.729}** — the keeper's
determination basis exactly in kind.

**VERDICT: KEEPER-CANDIDATE, mechanical — every pre-registered gate
passes.** Unlike the ercot-221 promotion, this one carries no gate
regression to override: the repair clears the keeper's one failing kill
gate and retains everything else.

## 8. Disposition

**PROMOTED → keeper `2026-08-20-ercot223-arm-eventrelease`** on the
owner's in-session instruction ("Is this a recommended keeper candidate?
If so plz promote"), with the recommendation affirmative on the mechanical
record itself. Keeper shard re-keyed, `build_status --iso ERCOT` rebuilt,
`calibration-keeper-auditor` PASS (0 failures, 0 warnings). ERCOT holds no
`complete` marker, so no `calibration-complete.json` re-key (D-5(b) not in
scope). Matrix: the `ercot_storage_adaptive_expectation` ERCOT cell keeps
K with the ercot-223 evidence appended (no new row — the guard field is
registered on the family row's `def:`, rule 28c), keeper + §5.1 header
re-stamped. The ercot-221 REJECTED-AS-ARMED record and the ercot-222 seed
refutation stand unrewritten. The depth ceiling (bootstrap starvation, 7
vs 23 spike days) and the 117 missed-hour count half remain with Door D —
this repair changes neither; ERCOT bandwidth returns to the Door-D hold
and the R-A re-pointed queue (standing alternatives: the item-8 CME/NYMEX
basis-swap screen; the G-SPUR band-top blindness owner gate revision).
