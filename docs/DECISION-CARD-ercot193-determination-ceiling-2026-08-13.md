> Status: OPEN — for the owner sitting. Nothing here is decided in-session.

# DECISION CARD — ercot-193: the determination ceiling — why no amount of C3b-2023 work can move ERCOT off NOT-YET

**For the owner sitting. Session ercot-193, 2026-08-13, HEAD `9c52ea8`. NOTHING IS
DECIDED HERE.** No rubric constant is touched — the v3.0 tier guard,
`LEDGERABLE_CRITERIA` and `MAX_LEDGERED_CAVEATS` are owner-only and stay
byte-unchanged in this session. This card performs exactly ONE new measurement — a
**read-only counterfactual re-scoring** of the keeper's registered dashboard payload
against the committed bench actuals, using the rubric's own `_wmean`/`_nrmse`
(`scripts/probes/ercot193_c3b_decomposition.py`, output
`results/calibration/ercot193_c3b_decomposition.json`). Actuals enter only
counterfactual *scoring*, never any model input (rule 13 `[R-MEASURED]` clean; the
ercot-189 footing). Every other number is read off committed artifacts.

Scope: ERCOT only (rule 25 `[R-ISO-SCOPE]`). ERCOT holds **no `complete` and no
`final` marker**; every year referenced is inside {2023, 2024, 2025} (rule 22
`[R-HOLDOUT]`).

**Keeper at assembly:** `2026-08-12-run192-arm-coal-peak` — determination
**NOT-YET**, fail set **{C3a-2023, C3b-2023}**, C3c the single ledgered CAVEAT
(`ACCEPTED MODEL-CLASS LIMITATION`) ×3 at 58/181, 22/53, 1/31 — re-verified
in-session with `scripts/calibration_verdict.py --run-id` (committed artifacts only,
no solve).

---

## 0. THE BOARD

| card | decision | blocking? | recommendation |
|---|---|---|---|
| **R** | What is ERCOT's public determination posture now that BOTH remaining fails are one closed model-class object — hold NOT-YET, or an owner act on C3a-2023/C3b-2023's status? | blocks the framing of every future ERCOT calibration charter | **(R-A) hold NOT-YET as the honest public claim; re-charter ERCOT sessions off the 2023 price criteria** |

One signable card. Sections 1–2 are its evidence; section 3 is the card.

---

## 1. THE ARITHMETIC — the ceiling is already fixed, before any C3b work

Four committed facts compose, none of them new:

1. **Any FAIL on any tier forces NOT-YET** (rubric v2 rule, unchanged;
   `scripts/calibration_verdict.py` `CRITERIA`/determination basis). ERCOT carries
   TWO fails: C3a-2023 (`price_mean`, −33.2 %) and C3b-2023 (`price_shape`, NRMSE
   0.604 vs ≤0.20). Both are **load-bearing** tier.
2. **Ledgering cannot reach either.** `LEDGERABLE_CRITERIA = {"price_tail"}` — C3c
   and nothing else (v3.1) — and `MAX_LEDGERED_CAVEATS = 1`, a slot the C3c entry
   already spends. The v3.0 tier guard additionally refuses `model-class`
   classification on any load-bearing criterion, fail-closed. There is no
   rubric-legal route by which C3a or C3b becomes a caveat.
3. **C3a-2023 is closed as unreachable.** Signed ruling **Q-B** (ercot-190 card Q,
   executed at ercot-191): the coverage licence FAILED on the repaired deriver, so
   *"no further ERCOT C3a-2023 spend; ERCOT stands at NOT-YET on C3a-2023 as a
   model-class limit"* — automatic and final. Item 11 CLOSED.
4. Therefore the determination is **NOT-YET regardless of C3b-2023**. A session
   that drove C3b-2023 from 0.604 to 0.000 would change the fail set from
   {C3a-2023, C3b-2023} to {C3a-2023} and the public claim not at all.

That much is arithmetic. What is *new* in this card is the measurement that the
C3b-2023 criterion itself is not independently reachable either — §2.

## 2. THE MEASUREMENT — C3b-2023 is the same object as C3a-2023, and it is 96 % of the criterion

From `results/calibration/ercot193_c3b_decomposition.json` (the rubric's own C3b
arithmetic, keeper payload vs bench `rt_lw_mon`):

| | Jan | Feb | Mar | Apr | May | Jun | Jul | **Aug** | **Sep** | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| model | 25.0 | 21.2 | 23.2 | 23.5 | 27.3 | 57.0 | 37.2 | **117.3** | **58.6** | 27.8 | 28.5 | 22.4 |
| actual | 26.4 | 21.9 | 30.3 | 23.9 | 32.2 | 74.5 | 48.4 | **220.6** | **109.8** | 31.7 | 31.3 | 23.2 |
| resid | −1.4 | −0.7 | −7.1 | −0.4 | −4.9 | −17.5 | −11.2 | **−103.3** | **−51.1** | −3.9 | −2.8 | −0.8 |

- **Aug+Sep 2023 carry 96.2 % of the squared monthly residual** (Jun–Sep: 99.3 %).
- Counterfactual **"Aug+Sep scored perfect, all else as-is": NRMSE 0.604 → 0.118 —
  a PASS**. The other ten months are *already* inside commercial shape tolerance.
- Counterfactual **"every month EXCEPT Aug+Sep scored perfect": 0.604 → 0.592** —
  still 3× the 0.20 bar. **The best case of ANY lever that does not move Aug/Sep
  2023 is a criterion that still fails at ~0.59.**
- The same months are the C3a-2023 miss: the Jun–Sep monthly gaps sum to
  ≈ $15.3/MWh of annual-mean equivalent, ~72 % of the $21.35 C3a-2023 gap
  ($42.97 model vs $64.32 actual); ercot-189 measured the >$200-tail hours alone at
  two-thirds of the C3a gap by dollars and ~97 % by distance-to-gate.

August–September 2023 scarcity formation is precisely the object the record has
adjudicated **model-class**: the C3c ledger entry (realized RT tail formed on
ERCOT's energy offer stack at measured RTORPA ≈ $1–5, un-formable by a
competitive-offer LP; exhaustion record ercot-95→163), the ercot-181 offer-family
exhaustion, ercot-173's refutation of any supply-curve-crossing route, and Q-B's
closure of the last quantity/capability face. **C3a-2023, C3b-2023 and the C3c
caveat are one physical object counted by three criteria.** The rubric is not
double-counting by accident — an annual mean −33 % off IS a load-bearing miss for
the intended use, three times over — but chartering "C3b-2023 lever rounds" as if
C3b were an independently movable criterion is now measured to be false framing.

## 3. CARD R — the options and the recommendation

**(R-A) Hold NOT-YET as the honest public claim — RECOMMENDED.** The model, on its
most structurally faithful recipe, does not reproduce summer-2023 ERCOT scarcity
pricing, and the two load-bearing 2023 price criteria say so. That is the claim a
NOT-YET makes, and it is true. Consequences to adopt with it:
  - **Stop chartering C3b-2023-targeted lever rounds as determination work.** By
    §1 they cannot move the claim; by §2 they cannot even move the criterion past
    ~0.59 without re-opening the Q-B-closed object. C3b-2023 work is admissible
    only as a side-effect report of structurally-motivated mechanisms (rule 1),
    with the ceiling stated up front.
  - ERCOT session bandwidth re-points to: protective/hygiene defects (the two
    ercot-192-filed defects, one fixed this session), the 2024/2025 shape queue,
    standing re-gates, and forecast-lane readiness — where session work can still
    change something the program reports.
  - The dashboards keep reporting the misses at full magnitude; the keeper's
    market_story carries the one-object finding.

**(R-B) An owner act on the 2023 price criteria's status.** The only routes are
owner-only rubric amendments this session may not draft: widening
`LEDGERABLE_CRITERIA` beyond C3c, raising `MAX_LEDGERED_CAVEATS`, or relaxing the
v3.0 tier guard to admit model-class on load-bearing criteria. **RECOMMENDED
AGAINST**, on the rubric's own reasoning: the guard exists precisely so that a
model that misses its central intended-use quantity by a third in a scored year
cannot present as CALIBRATED-WITH-CAVEATS; C3c's ledger was accepted as the narrow,
supporting-tier exception and the record repeatedly relies on its guards being
real. A determination bought by widening the ledger would be a worse public claim
than the honest NOT-YET. If the owner nevertheless wants the one-object structure
reflected, the smallest act is **reporting text, not rubric**: a standing note on
the ERCOT keeper/status pages that the three 2023 price criteria fail on one
adjudicated model-class object (this card as citation), with the determination
unchanged.

**(R-C) An out-of-model-class program decision** (a scarcity-formation
representation beyond competitive/measured offers — e.g. an equilibrium-conduct
layer). Named for completeness because it is the only route that could ever flip
the 2023 criteria on the merits. It is a *program* decision (new model class, new
charter, its own rule-1/13 adjudication — the measured RTORPA ≈ $1–5 record means
there is no administrative-scarcity mechanism to "add"; what is missing is bidder
conduct), not a calibration lever, and nothing in the current queue reaches it.
Not recommended as a calibration-lane act; recorded so its absence from the queue
is a decision rather than an oversight.

**Recommendation: R-A**, with R-B's reporting-text variant offered if the owner
wants the one-object finding surfaced on the public pages.

---

*Fences honoured in the session that wrote this card: no C3a-2023 spend (the probe
re-scores committed artifacts; card Q / item 11 stay closed), no C3c ledger change,
no rubric amendment, no holdout marker granted or spent, no keeper change. The
ercot-188/E2 P0 bit-identity forfeiture is inherited unexpired and untouched.*
