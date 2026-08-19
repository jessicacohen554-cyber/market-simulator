# FINDING — caiso-204: CAISO's storage fleet IS an adaptive expecter — the evening offer surface tracks trailing $200-spike experience with daily corr **0.704** and a 2023-only fit predicts 2024/2025 months 19/24 within ±50 % (BOTH identification gates PASS, where ERCOT's failed) — but the mechanism is **INFEASIBLE ON THIS KEEPER BY BOOTSTRAP**: the armed path reads only the model's own scored price, and the keeper's committed path holds **0 / 1 / 0** event days (the C3c-ledgered tail deficit), so `P_hat` ≈ 0 everywhere and the floor tops out at **$14.5** — the adaptive lever can only AMPLIFY a model tail that exists, never create the one that is missing. Phase-0 verdict **FAIL (G-BOOT, sole structural fail)** recorded unrewritten; cell stamped **I**; NO SOLVE SPENT; keeper unchanged (2026-08-19)

**Keeper `2026-08-17-caiso-200-h1-memberpanel` UNCHANGED. No LP, no solve, no
`ScenarioConfig` field added, nothing registered (rule 15 applies to completed
runs — the caiso-178/202/203 disposition).** Phase-1 entry over this recorded
FAIL requires EXPLICIT owner instruction (the ercot-188/213/215/221 pattern);
the lane returns to its resting state (caiso-201 Q1) per the charter.

Pre-registration: `results/calibration/PRECHECK-caiso204-adaptive-phase0-2026-08-19.md`
(pushed b6da910, before any bid value was read; all six gates and both
committed-bytes expectations declared ex ante).
Instruments: `scripts/probes/caiso204_fetch_subset.py` (the pre-registered
585-date balanced subset re-fetch — the caiso-203b zero-cost-re-fetch reading,
stated up front in the PRECHECK; 585/585 dates landed, zero rate-limit
failures, zero archive holes) and `scripts/probes/caiso204_adaptive_phase0.py`.
Record: `results/calibration/caiso204_adaptive_phase0.json` (unrewritten).

---

## §A — The verdict, gate by gate (PRECHECK §3 bars, none moved)

| gate | result | detail |
|---|---|---|
| G-DRIVER | **PASS** | measured $200 event days 22 / 9 / 5 (36 total, 9 quarters with ≥ 2); the $1,000 soft-cap diagnostic series is 0 / 0 / 0 — degenerate exactly as the PRECHECK said, which is why ERCOT's absolute threshold was never usable here |
| G-COV | **PASS** | 585/585 parsed; admissible by quarter-of-year 179/155/121/130; classifier finds 76/123/163 members vs caiso-178's full-corpus 77/121/167; fidelity legs 0.62 / 0.80 / 4.65 pp vs the committed `share_p_hi_gt_15` references (bar ±10 pp) |
| G-ID | **PASS** | daily corr(implied_P, P_hat) = **0.7035** (bar 0.6 — ERCOT v2 failed this leg at 0.447); monthly reconstruction 26/36 cells within ±35 % (72 %, bar 60 %); base (quiet-day standing ask) = **$53.2**, 31 quiet days |
| G-DECAY | **PASS** | 2023-only fit (λh 45 d, β 0.560) predicts the 2024+2025 monthly cells 19/24 within ±50 % (79 %, bar 60 %); base-only ablation fails the corr leg by construction — the trailing term does the identified work |
| G-BOOT | **FAIL — the pre-declared wall, measured exactly** | the keeper's committed scored path (CA demand-weighted λ + its own scarcity overlay, the same series C3c gates on) yields **0 / 1 / 0** model event days at $200 (leg i needs ≥ 3); with the fitted constants the implied in-window floor reaches ≥ $200 in **0** window-hours (leg ii needs ≥ 12); max floor anywhere = **$14.5** (2024, the ~30 days after its single event day) |
| G-SAFE | **PASS (trivially)** | floors ≤ $100 in 100 % of hours on the keeper's 2023 and 2025 paths — self-extinction holds for the same reason G-BOOT fails: the two gates are the two sides of the one committed-path fact |

**Phase-0 verdict: FAIL** (G-BOOT sole structural fail). Per the pre-registered
rule: conduct present + armed path infeasible on this keeper → cell **I**, wall
recorded.

## §B — The identified CAISO conduct (the transferable knowledge, recorded whatever the cell says)

`P_hat(d) = clip(β · P_trail(d; λh), 0, 1)` on CAISO's own regime ($200 event =
its frozen scarcity-tail threshold AND 20 % of its $1,000 soft cap; window
h18–21 PT; park cap $1,000):

- **λh = 30 days, β = 0.5945** (SSE-optimal on the pre-registered grid; the
  2023-only fit lands λh 45 d / β 0.560 — same order, stable).
- **CAISO's fleet is an UNDER-reactor (β ≈ 0.6): it prices scarce-SOC evening
  discharge at ~60 % of the trailing spike frequency × cap.** ERCOT's identified
  β was 3.0 — a 5× conduct difference between the two markets' storage fleets,
  which is rule 25 made empirical: the ERCOT constants would have been badly
  wrong here.
- The evening standing ask on quiet days is **$53.2** p50 — consistent with the
  caiso-131/202 evening CC-level clearing; the surface swings to $1,000-parked
  cap mass through event episodes (Jan/Aug 2023, Jan/Jul 2024) and decays back
  over ~a month, which is what the trailing term identifies.
- Why CAISO identifies where ERCOT did not: ERCOT's daily evening response is a
  cap-or-cheap switching series (61 fit-span days at ≥ $4,999 vs 79 at ≤ $500 —
  the corr leg died at 0.447); CAISO's response moves smoothly because the
  cheap-mass/cap-mass MIX shifts gradually. The conduct phenomenon is real in
  both markets; it is *identifiable* at daily grain only in CAISO.

## §C — The wall, stated precisely (why I and not R, and why no Phase-1 on this keeper)

The mechanism is a **conduct amplifier with a model-side trigger**: pass-1 must
produce spike days before pass-2 can floor anything (the armed path reads ONLY
the model's own λ + its own scarcity-overlay mirror — zero measured content,
rule 13, the ercot-221 Amendment 3/4 discipline; and unlike ERCOT's
Amendment-4 case there is NO further model-side scarcity term left to add:
CAISO's scored price already contains its LOLP overlay). The keeper's committed
path holds 0 / 1 / 0 event days — the very tail deficit C3c ledgers (model
0h/1h/0h ≥ $200 vs actual 47/35/8). So:

- 2023 and 2025: `S_m ≡ 0` → `P_hat ≡ 0` → floor ≡ 0 → **byte-identical A/B by
  construction**.
- 2024: one event day → max floor $14.5 on the decay window's evening hours —
  below even the quiet-day standing ask ($53), i.e. below the level the LP
  already clears: predicted zero dispatch effect.

This is the caiso-202 §B compression read from the storage side: the model's
missing >$60 tail is the missing driver. **The adaptive lever attacks C3c only
in a model that already spikes sometimes** (ERCOT's keeper: 7 model spike days
in 2023, G-BOOT floor $899). A CAISO Phase-1 would need the tail-formation
root cause fixed FIRST — and that object is the adjudicated model-class
RT/supply-state limitation (caiso-202 §C/§G) whose admissible instruments the
owner has adjudicated or declined to fund (caiso-203b). Arming it anyway and
scoring the A/B would spend two 3-year solves to reproduce the control
byte-for-byte in two of three years — recorded here so the owner can order it
knowingly if desired (the ercot-221 pattern), but not assumed.

## §D — Honest notes against interest

1. **The identification is in-sample stronger than ERCOT's, and it is not a
   pass of the mechanism.** Rule 1: conduct being real does not make the armed
   mechanism reachable; the cell verdict is about the mechanism on THIS keeper.
2. **The winter composition caveat**: 14 of 2023's 22 events are Jan–Mar
   gas-price days, not net-load scarcity evenings. The fit does not distinguish
   drivers; the corr survives across both compositions (2024's events split
   Jan/Jul and the 2023-fit transfers at 79 %), but a driver-specific
   identification was not attempted and is NOT claimed.
3. **β < 1 weakens the C3c upside even in a bootstrap-capable model**: at
   CAISO's identified conduct, a model path with the ACTUAL event frequency
   (22 events, best case) yields P_trail ~ 0.2–0.4 in episodes → floors
   ~$120–240 — enough to build $200-tail hours, but nowhere near the
   cap-parking ERCOT's β = 3 implies. The lever's reachable C3c effect in
   CAISO is modest by measurement, not just blocked by bootstrap.
4. The G-SAFE vom convention (vom taken as 0, the strictest bar) made no
   difference: shares read 1.000 exactly.

## §E — Record changes

- `results/calibration/caiso204_adaptive_phase0.json` committed unrewritten.
- Matrix (rule 28b, CAISO shard only): `ercot_storage_adaptive_expectation`
  CAISO cell **. → I** with this evidence; §5.2 caiso-204 block added. NO new
  matrix row (no `ScenarioConfig` field was built — rule 28c not triggered).
- `docs/calibration-log/caiso.md`: caiso-204 entry.
- Dashboard: nothing to register — no run produced.
- Keeper, markers, holdout freeze, resting state: UNCHANGED.

## §F — DO-NOT-REDO (new, binding; carried lists of caiso-202 §I / caiso-203 §G unchanged)

- **Re-running this Phase-0 identification on this corpus** — the probe
  reproduces it from the fetched zips in ~9 min; the verdict JSON is the
  record. New evidence = a different keeper whose scored path spikes, or a
  different instrument, not more of this one.
- **Arming a CAISO adaptive floor with a measured event series** (actual LMP
  driving the armed path) — that is the rule-13 line the ercot-221 owner
  question ("You're not letting it see actual 2023 price right?") drew
  explicitly; the identification/armed split is the mechanism's whole
  admissibility.
- **Lowering the model-side event threshold below $200 to manufacture
  bootstrap feasibility** — a two-threshold asymmetry tuned to the residual
  (the PRECHECK's symmetric-threshold convention is the declaration).
- **Quoting the β = 0.59 conduct fit as calibration skill or a C3a/C3c
  result** — it is an identification of bidder conduct from public bids; no
  model price was scored against anything in this session.

Next number: caiso-205.
