# ADDENDUM to the caiso-278 closure — **THE 8 % OFFER CUT WAS ALREADY SOLVED TWICE. It closes C3a exactly as expected and FAILS C4-2025.** Plus a NEW zero-LP measurement: the "over in every year" bias is **RT-basis-specific**, and after the basis reading **2025 is the whole object**

**Session caiso-278, 2026-09-12, second sitting. CAISO only (rule 25 `[R-ISO-SCOPE]`). ZERO LP,
ZERO SHARDS, no arm, no keeper change, no cell verdict moved.** Owner question: *"there's a level
issue where it's running over every year. We have space to push the offer curve down like 8 % and
still keep c3a within the gate. Why wouldn't that work?"*

---

## §1 — IT DOES WORK ON C3a. THAT IS NOT WHY IT WAS REFUSED.

The premise is **correct and measured**. Fossil bands × 0.92 through the rule 1 `[R-STRUCT]`
authorized channel was run **twice** — caiso-267 (`ADDENDUM-caiso267-fossil-offer-8pct-2026-09-09.md`,
`FINDING-caiso267-fossil-offer-8pct-2026-09-09.md`) and caiso-268 on the live keeper
(`2026-09-09-caiso-268-fossil92-span`, registered as a rejection). The two replicate each other to
**~1 MW in every hour and three decimals on every criterion**.

| criterion | keeper | × 0.92 arm | verdict |
|---|---|---|---|
| **C3a** 2023/24/25 | +4.4 / +8.9 / +8.3 % | **−0.9 / +4.3 / +3.2 %** | mean \|gap\| **7.20 → 2.80 %**, every year inside ±10 % |
| C1 / C2 / C3b / C6 / C8 | PASS | PASS | no flip |
| C5a CO2 (reported-only) | −11.0 / −5.2 / −4.3 % | −7.8 / −2.2 / +0.5 % | improves |
| **C4 gas NRMSE** | 0.287 / 0.260 / **0.298** | 0.275 / 0.254 / **0.308** | **FAIL 2025** (tol ≤ 0.300) |

All four rule-29 STOP gates passed; G-DIR Δλ landed **−2.850 / −1.580 / −1.720 $/MWh**, within
**$0.005** of the pre-solve prediction. The mechanism did exactly what its arithmetic said.
**Determination: NOT-YET on C4-2025 alone. Owner ruled DO NOT PROMOTE, 2026-09-09.**

## §2 — WHY C4-2025 BREAKS, AND WHY IT IS STRUCTURAL RATHER THAN A KNIFE EDGE

A flat multiplier is **uniformly more gas in all 8,760 hours**. It therefore helps the two years the
keeper *under*-dispatches gas (2023 −969, 2024 −489 MW fleet mean error) and **breaks the one year
the keeper was already near-unbiased** — 2025, whose fleet mean error crosses **−107.2 → +209.0 MW**:

| 2025 window | keeper gas error | × 0.92 arm |
|---|--:|--:|
| overnight h0–6 | +202.4 MW | **+764.4 MW** |
| evening | +766.1 MW | **+1,030.9 MW** |
| belly | −1,031.8 MW | −862.0 MW (improves) |

The substitution is **essentially all imports** (−2.32 / −1.97 / −2.78 TWh) against `CC_REGULAR`
(+2.12 / +1.81 / +2.59). So the arm **buys a better price by making the dispatch worse in the year
the dispatch was right** — the same fact as the C4 failure, not a coincidence beside it.

**And caiso-272 then vindicated the refusal structurally, at LP-row grain** (`mc = λ` instrument,
zero LP): in the 6,924 `econc05` hours carrying 81.79 % of 2022 load, **all CC families are
marginal at implied HR 9.235 against the market's own 9.289 — 0.05 BELOW.** The +1.105 HR bias
decomposes as **CC-marginal −0.029, non-CC thermal tail +0.383, λ-in-a-gap +0.747.** The bands the
authorized channel *can* reach are already measured-correct, and neither carrier is reachable from
`offer_curve_by_group` at all. A flat cut trims the one thing that is right.

**Matrix DO-NOT-REDO (CAISO `offer_curve_by_group`, cell stays K):** *"a third flat-multiplier arm
on an unmoved baseline buys nothing; an hour-scoped cut is a different mechanism needing its own
driver."* The hour-scoped door that note left open was **subsequently closed by caiso-272's
measurement above** — an hour-scoped cut would scope a cut to bands already at the market's own
level.

## §3 — THE SIZING QUESTION, NAMED EXPLICITLY BECAUSE IT IS THE NATURAL NEXT THOUGHT

"Then use 5 %" is the **one move the carve-out forbids by name.** Rule 1 condition (c): the factor
is set *ex ante* and **never swept against the gates** — "selecting a factor by which one makes a
criterion pass is the fitted-mechanism selection this rule exists to forbid." caiso-267 refused to
try 6 % or 10 % for exactly this reason and recorded the refusal before its solve.

So a sized cut is available **only as an owner override of condition (c)**, not as a session's
judgement. Stated so the trade is visible: the arm moved C4-2025 by +0.010 for 8 %, so holding
C4-2025 ≤ 0.300 implies roughly **≤ 2–3 %**, worth about **1 pp of C3a** — against a residual of
7.7 pp in 2025. The purchase is small and it is a declared fitted parameter in the DOF ledger.

## §4 — NEW MEASUREMENT (zero LP): "over in every year" IS RT-BASIS-SPECIFIC

caiso-272 put the DA−RT basis question to the owner on **2022 only** and left it undecided. Extended
here to all four CAISO years from the committed `bench/CAISO/<year>.json.gz` (`da_lw` / `rt_lw`, the
scorer's own gated basis) against each keeper-year's committed model load-weighted price:

| year | model | rt_lw | **gap vs RT** | da_lw | **gap vs DA** | DA−RT spread | model's position in the DA−RT band |
|---|--:|--:|--:|--:|--:|--:|--:|
| 2022 | 94.07 | 84.49 | **+11.34 %** | 92.14 | **+2.09 %** | +9.05 % | 1.25× |
| 2023 | 55.89 | 54.17 | +3.18 % | 61.68 | **−9.39 %** | +13.86 % | 0.23× |
| 2024 | 37.55 | 34.65 | +8.37 % | 37.97 | **−1.11 %** | +9.58 % | 0.87× |
| 2025 | 37.07 | 34.42 | +7.70 % | 35.40 | **+4.72 %** | **+2.85 %** | **2.70×** |
| | | | **mean \|gap\| 7.65 %** | | **mean \|gap\| 4.33 %** | | |

**Three readings, and the third is the one that matters:**

1. **The one-signed "over every year" bias is a property of the RT basis, not of the model.** On DA
   the bias is **not one-signed** — two years run under — and mean \|gap\| falls **7.65 % → 4.33 %**.
2. **DA is not a rescue.** 2023 over-corrects to **−9.39 %**, close to failing the other side of the
   same ±10 % band. Switching basis trades a consistent small over-run for two-sided scatter.
3. **2025 is not explained by basis at all, and after the basis reading it is the WHOLE object.**
   Its DA−RT spread is only **2.85 %** while the model over-runs **7.70 %** — the model sits
   **2.70×** outside the DA−RT band, the only year that does. And 2025 is simultaneously **the year
   whose gas dispatch is already unbiased** (−107.2 MW) and **the year the 8 % cut broke**. So in
   2025 the excess price is **not** gas being too dear or too scarce: gas volume is right and price
   is still 7.7 % high. Whatever sets λ in 2025 is something else.

## §5 — WHAT IS OPEN, AND WHY NO SOLVE IS RECOMMENDED **YET**

Three fresh candidates were generated and killed on committed measurement this session, none by
opinion:

| candidate | killed by |
|---|---|
| CHP/ST_GAS offer ablation | already solved at caiso-231; ~1 % of the object (this finding, §§1–5) |
| **firm-import floor reshape** (17.94 TWh forced on an `h0-23` window, 50.4 % of its class) | `caiso_firm_selfsched_floor` is **K** and reconciled (caiso-150/151: 18.856 − 0.919 clip = 17.938 exactly). Its shape basis IS acknowledged "the wrong object in kind" — but **caiso-150 §H adjudicated the direction-splitting source unreachable from the public feed**, and caiso-202 §F.3 measured the reconciliation **C3a-ADVERSE** (+0.045 / +0.626 / +0.494 pp). My hypothesis was **wrong-signed**. |
| **wider RA must-offer / commitment reach** | caiso-276 §5a: only **647.7 MW of 22,354 MW (2.9 %)** is idle-while-in-the-money in the residual window — *"a wider RA must-offer reach has almost nothing to act on"*. The 13.5 GW of headroom is not unavailable, it is **priced above λ** — which routes straight back to the offer cut and its C4 failure. |

**The loop closes**: price is high → cut offers → C4-2025 breaks; get belly gas without cutting
offers → only 2.9 % to act on; displace forced imports → wrong-signed plus a data wall; cut the
bands the channel can reach → they are already at the market's level.

**So there is no admissible in-model lever, and this session does not manufacture one** (rule 1
`[R-STRUCT]`). Two owner rulings could each unlock a spend, and both are **free**:

* **(A) Rule on the scoring basis** (§4). Bigger effect on the headline than any offer cut, zero LP.
  It is a rubric question — the rubric's own OUT-OF-REPRESENTATION row calls the DA−RT premium
  something *"the test must not demand"*, and caiso-272 measured **70.2 %** of the 2022 dollar miss
  as exactly that.
* **(B) Override rule 1 condition (c)** and authorize a sized factor (§3), accepting that it is a
  swept fitted parameter. Well-defined, ~2–3 %, buys ~1 pp.

**And one zero-LP measurement IS recommended before any solve**, because §4 just moved the target:
**re-point caiso-272's `mc = λ` LP-row instrument from 2022 to 2025.** It exists
(`scripts/probes/_caiso272_marginal_band.py`), it runs in the parent on committed sidecars, and it
has never been run on the year that is now the entire object — the year with unbiased gas volume,
a 7.7 % price excess against *both* bases, and the C4 failure. If it names a reachable carrier,
**that** earns the solve. Spending LP before it would be spending it on the wrong year.

## §6 — RULE LEDGER (delta to the closure's §11)

| rule | discharge |
|---|---|
| 1 `[R-STRUCT]` | No lever selected. §3 states the sizing question as an owner override rather than exercising it; §5 declines to manufacture an arm. |
| 15 `[R-DASHBOARD]` | Zero LP ⇒ nothing to register. The × 0.92 arm is already registered as a rejection (`2026-09-09-caiso-268-fossil92-span`). |
| 25 `[R-ISO-SCOPE]` | CAISO only. |
| 28(a) | Three candidates checked against the record before proposal; all three already adjudicated. No cell re-tested. |
| 28(b) | No verdict moves — nothing armed or tested. |
| 29 `[R-SCREEN]` | Step 0 discharged on all three candidates; each died pre-solve. |
| 31 `[R-RETAIN]` | Nothing deleted; no bundle produced. The caiso-268 arm's committed slim set means a promotion of it needs **no re-solve**. |
| 32 / 33 | Parent spent zero LP; no shard launched, none to archive. |
