# FINDING — ercot-230: the SECOND ADAPTATION PASS (fixed-point iteration) is MEASURED-INERT-AT-FIXED-POINT — the keeper is already the fixed point of the within-year adaptation map, and the bootstrap starvation is a property of the map, not of the one-pass truncation

**Session ercot-230, 2026-08-23, branch `claude/ercot-2023-summer-scarcity-1nx4cl`.
Keeper at open AND at close: `2026-08-20-ercot223-arm-eventrelease` (NOT-YET,
{C3a-2023 −39.7 %, C3b-2023 0.729}, C3c ledgered ×3 — untouched). Precommit
`docs/PRECOMMIT-ercot230-adaptive-fixed-point-2026-08-23.md` (304 lines, blob
`3a73cb0d`) pushed + blob-verified BEFORE any build edit and BEFORE any solve.
Committed record: `results/calibration/ercot230_probe_fixedpoint.json` +
`ercot230_gates.json` + this FINDING; probe bundles local and unregistered
(W-2, carried forward by the ercot-230 dispatch).**

## 0. The owner charter

The dispatch mandated opening with the W-1 question ("this session must NOT
re-enter Door D on its own authority"). The session presented three options —
lift the fence onto the conduct object via the second adaptation pass; keep
the fence and sweep the non-AS tightness channel; restore the Door-D rest
posture — and the owner selected **"2nd adaptation pass"**, chartering the
FINDING-ercot221 §4 first named successor (recorded verbatim, precommit §0,
signature-by-dispatch precedent). The ercot-221 card's *"exactly ONE
adaptation pass (no fixed-point iteration — rule 10 spirit, pinned)"*
convention was thereby amended for the adaptive P1 offer pass only.

## 1. What was built (armed and live in the solve)

`ercot_adaptive_fixed_point` (default off, ERCOT-gated inside the armed
adaptive block; zero new identified constants; the cap
`ERCOT_ADAPTIVE_MAX_PASSES = 8` a pre-registered operational convention).
When armed, adaptation passes continue past the incumbent pass 2, each
re-deriving the IDENTICAL floor arithmetic from the latest P1 (Amendment-4
settle basis; frozen 30 d / 3.0077; $1,000 event; h17–20 window;
event-release mask from the immediately-preceding pass) and re-solving
through the same `p1_storage_discharge_cost` seam, until the floor vector
reproduces itself exactly (**converged** — the next pass would solve the
identical LP), recurs non-adjacently (**cycle**), or hits the cap. The floor
construction was factored to ONE closure shared by the incumbent pass and
the loop; trajectory persisted as `hourly/adaptive_iteration_<year>.json`.

**G-REPRO, strongest form:** the control replay (new code, flag off, 2023)
reproduces the keeper's committed sidecars to **max|Δ| = 0.0 on every
numeric column** (system / reserve_family / storage / adaptive /
class_hourly) and the official scorer to the printed digit
(−39.7 % / 0.729 / 74 h) — the refactor is proven numerically inert, and the
A/B delta is the mechanism alone.

## 2. THE RESULT — converged after ZERO additional passes

Arm = the keeper recipe + the single delta `--set
ercot_adaptive_fixed_point=true`, 2023-only (flag verified in `run_config`
AND `meta`; the loop demonstrably RAN and logged its verdict):

| generation step | path spike days | floored window h | released window h | floor sha |
|---|---|---|---|---|
| pass-1 → F₂ (incumbent) | 7 | 768 | 9 | `44f664bd275a091a` |
| pass-2 → F₃ (candidate) | **7** | **768** | **9** | **`44f664bd275a091a`** |

`stop_reason = "converged"`, `n_adapt_passes = 0`. The pass-2 path — the
keeper's own scored path — carries **exactly the same 7 spike days and the
same 9 in-window realized hours** as the unfloored pass-1 path, so the floor
it licenses is **bitwise identical** to the floor it ran under. Pass 3 would
have solved the identical LP; none was needed. Consequently:

- **arm ≡ control at max|Δ| = 0.0 on ALL SEVEN sidecars** (system,
  reserve_family, storage, adaptive, class_hourly, network, unit_hourly);
- official 2023 identical to the keeper digits: −39.7 % / 0.729 / 74 h;
- probe basis identical (−29.99 / 3.4476 / 74, model mean 33.856);
- **every gate PASS** (G-CAP 0; G-SHED ∅ = ∅; G-SPUR 11 ↔ 11 with identical
  hour sets, lidless 11·11·0 both; G-BAT; G-D2 no new D-4 rows;
  G-SHORTFALL by equality per family);
- summer block: miss split 67/114/7 both; **`d_price_at_miss` p50 = max =
  0.0**; improved miss hours 0; calm fortnight 15.44 % both.

**Verdict: `adoption_pass` false — MEASURED-INERT-AT-FIXED-POINT** (0.00 pp
against the ≥ 1.5 pp bar; nothing to escalate — the failure is trivial, not
borderline). No combined run, no registration, no promotion; the keeper is
untouched.

## 3. WHAT THE MEASUREMENT ESTABLISHES

1. **The ercot-221 one-pass convention is measured EXACT, not approximate.**
   The card pinned "exactly one adaptation pass" as a conservatism; this
   solve shows the within-year adaptation map reaches its fixed point at the
   first application — iterating it is not a truncated approximation of a
   deeper equilibrium, it IS the equilibrium.
2. **The bootstrap starvation is a property of the map, not of the
   truncation.** The mechanism's 7-event path licenses floors bounded at
   `P_hat_max × VOLL = 0.37 × 5000 = $1,850`, and those floors set **no new
   ≥ $1,000 settle anywhere on the path** — mostly they withhold storage
   behind a thermal-set price rather than setting the price themselves. So
   the event count cannot grow: the model's conduct channel **cannot
   bootstrap itself out of the depth gap within a year**. The circle is now
   measured closed: the depth deficit starves the expectation (7 vs
   reality's 23 event days), and the expectation cannot repair the depth
   deficit because the floors it licenses create no new events.
3. **The within-year adaptive family is now COMPLETE and adjudicated at
   every member.** Static conduct: Door A, refused ×3. Dynamic within-year:
   armed (ercot-221) + guard (ercot-223) — the keeper. Cross-year memory:
   refuted (ercot-222). **Fixed-point completion: measured inert
   (ercot-230, this record).** Of the FINDING-ercot221 §4 named successors,
   only the **seasonal end-of-season term** remains un-adjudicated — and its
   identified role (the Oct→Nov off-ramp cliff one memory constant cannot
   carry, Amendment-2 G-DECAY) shapes the fall decay, not the summer event
   count, so it is not on its face a depth-count candidate either. Each
   would still need its own owner card.
4. **The 2023 residual's remaining depth requires event experience the
   model's own within-year path cannot supply.** After the 226/227 program
   (AS-procurement inputs measured unreachable: `d_price_at_miss` 0.0 under
   every armed factor) and this measurement (the conduct channel's
   self-amplification measured absent), the recorded routes to that
   experience are the ones already fenced: cross-year structure (ercot-222
   R; re-entry needs new evidence and an owner instrument) or the Door-D
   2026 SOM RTC+B-era anchors (~mid-2027). The lane state returns to the
   owner exactly as precommit §5 P-6 anticipated, in its sharpest form.

## 4. Session hygiene

- Precommit → build → control → arm strictly in that order; solves
  in-session, sequential (rule 12), 6G swapfile + `MALLOC_ARENA_MAX=2`; env
  at the keeper pins (1.15.1 / 3.0.5 / 25.0.1 / 2.4.6 / 1.17.1,
  py 3.11.15).
- Years {2023} only (rule 22, W-2 probe); ERCOT-only edits (rule 25); no CI
  solves, no workflows, no PR.
- Registrations landed with the field in one commit (cache-key optional +
  defaults + TIER_TAGS; pinned default key `603c2498bf71d21d` unmoved,
  armed key distinct; 4 hermetic tests; `check_mechanism_matrix.py` exit 0;
  601 pipeline/config + 34 scarcity tests pass).
- Every pushed file ≥ 300 lines blob-verified (rule 27).
- The stale ERCOT matrix `gates:` stamp (head carried −39.4/0.723, the
  ercot-221 numbers, against the ercot-223 keeper's −39.7/0.729) was
  repaired in passing, ercot-221 story preserved as prior stamp.
- Matrix: the `ercot_storage_adaptive_expectation` family row's `def:`
  carries the new field (built-commit, rule 28(c), ercot-223 precedent);
  the ERCOT cell carries the ercot-230 evidence stamp (rule 28(b), this
  session).
