# PRECOMMIT — NEISO-RC REPAIR Phase B: the treatment crossover's pre-declared expectation

**Session:** NEISO-RC-R (capacity-expansion / FFP track, director r#21). Branch
`claude/neiso-rc-repair-fymtkz`. **Charter:**
`docs/handoffs/capx-director-prompt-pack-2026-08.md` §NEISO-RC-R, executing
`docs/handoffs/FINDING-capx-neiso-rc-phase0-2026-08-30.md` §6/§9.

**Committed BEFORE any solve.** The Phase A repairs (R1 registry intake, R2
curve re-derivation, R3 scorer trio, R4 diagnostic + tracked set) are landed
and pushed (commits `eabbae85`, `aa9240a2`, `63a61a24`, `0f68e035`). No Phase B
solve has been launched at this commit.

## 1. The run

ONE NEISO T1-X crossover treatment at HEAD, the capxd14 launch verbatim
(every solve-affecting flag omitted — the FFR-3A-4/D10 posture):

```
python scripts/run_capacity_hindcast.py --iso NEISO --crossover --vintage 2023 \
    --start-year 2023 --end-year 2027 \
    --out-dir results/hindcast/neiso-2023-2027-crossover-rcrepair
```

Control: the committed `neiso-2023-2027-crossover-capxd14` record —
**zero-solve on the control side** (its three committed files + the D14/Phase-0
findings are the control's record; its ledgers were never committed, which is
exactly the R4 gap). Scored with the R3 dual-basis scorer; registered on the
forecast namespace **preserve-then-overwrite** (the capxd14-era record
preserved under a suffixed key before the `neiso-t1x` verdict key is
re-emitted). The t3 verdict key and the bare `neiso-t1f` key are never
written (charter collision care). The treatment bundle commits its
`evolution_<year>.json` ledgers (the R4 tracked-set change).

## 2. The charter's pre-declared expectation (recorded verbatim, graded as primary)

From the charter: *"R2 REDUCES exits by restoring capacity revenue
(reachable-basis level moves from +20 % toward 0) while DE-CONCENTRATING the
composition (the screen discriminates; the floor returns to backstop duty);
Mystic becomes instrument-driven under R1."*

## 3. Pre-declared mechanical amendment (zero-solve, from the landed inputs; dated BEFORE the solve)

The R2 intake **refuted the Phase-0 finding's premise about the curve tail**
(recorded in the intake README and the R2 commit): the measured MRI-era curve
(five published clearing points + the published FCA 13 tail zero) sits BELOW
the old linear FCA-11 geometry throughout (1.0, 1.06] and zero-crosses at
1.0582, EARLIER than 1.083 — real FCAs cleared $2.00–3.58/kW-mo at 3.3–4.5 %
surplus, never at the ≥8 % surplus where the model's screens sit. Evaluated
$/kW-yr on the 2027-28 anchor (108.94): 1.02 → 68.9 (old 82.7) · 1.045 → 26.8
(old 45.7×… old 0.457×108.94=49.8) · 1.06 → 0 (old 30.2) · ≥1.083 → 0 (old 0).

Mechanical expectations, stated ex ante and graded alongside §2:

1. **R2 is expected NEAR-INERT to slightly exit-INCREASING on the composition
   — the OPPOSITE direction of §2's curve leg.** At the model's long
   positions (≥1.083 in the S-4b twin) both curves pay $0, so the degenerate
   bar persists; in the oscillator's reversal region (~1.02) the new curve
   pays ~17 % less, weakening reversals. The §2 curve-leg expectation was
   written before the published evidence was in hand; if it misses, the miss
   is recorded, not re-tuned (R6 — no curve parameter may respond to this).
2. **Mystic 8/9 becomes instrument-driven (R1), whatever R2 does**: the
   confirmed channel (instrument 2018-12-20 ≤ cutoff 2023-12-31) derates
   plant 1588 by ~50 % of 2,272.4 MW in 2024 (June exit, annual-average leg)
   and completes in 2025 — landing largely in `confirmed_derates` on the
   binned fleet, which only the R3(iii) scorer read makes visible. Wyman 1/2
   (~100 MW, 2023-06) applies at the base build + 2024 completion; Middletown
   2 (+10) and Waters River fire 2027 (out of the scored window).
3. **Exit LEVEL ≈ control's, channel composition shifts.** Step-0 confirmed
   exits shrink the accredited surplus before the floor sizes the economic
   wave, so the floor's admission budget shrinks ≈1:1 — total in-window exit
   MW should land near the control's 3,563 MW (reachable-basis +20 %), with
   ~2.3 GW moving economic→confirmed. De-concentration, if any, comes from
   R1's channel substitution, not from R2's screen discrimination.
4. **The scored HEADLINE changes even at identical dispatch**, because R3
   changes measurement: the dual-basis block reports the vintage-consistent
   target (~3.0 GW, exits ceasing after 2023) beside the full-window 5.0 GW
   target; D-24 excludes 1588_7 / 568_3 (gated) and the Androscoggin CTs
   (ungated) on the committed decode; `confirmed_derates` MW now counts.
   The default-basis block stays on its old basis by construction.

## 4. Grading plan (fixed now)

Read, treatment vs control, at full magnitude: (a) in-window exit level on
BOTH bases; (b) per-fuel composition (gas_cc concentration vs the actual
6-fuel spread); (c) ≥300 MW recall on the D-24 reachable member set; (d)
channel split (economic / announced / confirmed, `confirmed_derates`
included); (e) decided-in-window lag censoring (R4 block); (f) forward-year
invariants. §2 and §3 are BOTH graded; any §2 miss is recorded in the finding
update and the matrix cell — never re-tuned in-lane (R6 standing refusal).
No `ScenarioConfig` field was added by Phase A (rule 28: no new matrix row;
the NEISO shard's capacity-market / confirmed-exits cells get evidence-stamp
updates in this session).
