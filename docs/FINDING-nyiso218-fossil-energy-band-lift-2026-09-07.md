# FINDING nyiso-218 — the +3.0 % fossil energy-band lift, MEASURED across the full span: **it works exactly as its own arithmetic says, and it does not reach the owner's stated motivation**

**Session:** nyiso-218, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-hr6c08`, on `main` at `bfbb0b6a`. **Date:** 2026-09-07.
**Keeper:** `2026-09-07-nyiso-213-summer-seam` — **UNCHANGED. Nothing promoted, nothing registered,
no marker moved, `final` not granted, 2020/2021 unspent.**
**Pre-registration:** `results/calibration/PREREG-nyiso218-fossil-energy-band-lift.md`, pushed at
`5e182e8a` **before any solve**, plus two addenda each pushed **before the spend it governs**
(`ADDENDUM-nyiso218-intermediate-drop`, `ADDENDUM-nyiso218-s1-gate-defect`). None was edited after.

**THERE WERE NO IN-SAMPLE RUBRIC FAILURES GOING IN, AND THERE ARE NONE COMING OUT.** This was not a
"fix a failure" session. It executed an owner-directed price-level move through the rule-1
`[R-STRUCT]` authorized channel (owner rulings R1/R2, 2026-09-07) and opened a named structural
object (§6, the hydro finding).

---

## 1. The result in one paragraph

The lift does **exactly** what its own pre-solve arithmetic said it would, and the arithmetic was
**not** the one the handoff assumed. Because the keeper arms `gas_offer_net_revenue_margin` at a
**3.9046 $/MMBtu** anchor, a band multiplier lift becomes a **fixed $/MWh margin**, not a
proportional scaling of marginal cost — so the realized passthrough is **near-constant in dollars**
(**0.2389 / 0.2278 / 0.2960 $/MWh per 1 % of band** in 2023/2024/2025) rather than ~1:1 in percent.
Every substantive screen gate passed on the pre-registered screen year and on all three span years;
**C3a moves +4.3→+6.5 %, +5.3→+7.1 %, −7.3→−6.0 %, and all three training years stay inside
±10 %**, with **zero PASS→FAIL flips on C1/C2/C4** anywhere and the price tail unchanged. **And the
owner's stated motivation is not met, exactly as §5.4 of the PREREG said before any solve:** the
2022 validation touchpoint moves **−12.5 % → −11.3 %**, still outside ±10 %, closing ~1.2 pp of a
2.5 pp gap. Four of five pre-registered predictions fire outright, **including the one written to
hurt the preferred answer (P4)**; the fifth is the session's own gate **S-1, which FAILED AS
WRITTEN on a defect in my drafting and is reported rather than rewritten.**

**Disposition: the arm is NOT a keeper on this lane's recommendation — and that is a
recommendation, not an act.** Rule 31 `[R-RETAIN]` reserves the decision to the owner; all three
bundles are retained on local disk and the promotion question is put explicitly in §7.

---

## 2. The channel, and that every carve-out condition held

Rule 1 `[R-STRUCT]`'s 2026-09-05 carve-out and rule 13 `[R-MEASURED]`'s single exception, condition
by condition:

* **(a) the band multipliers only.** `committed` / `econ_low` / `econ_high` on 10 routable fossil
  groups, **30 band values, every ratio exactly 1.03** (|ratio − 1.03| ≤ 1e-9, measured). **Every
  `peak` band frozen** — 2.25 (CC), 4.0 (CT_PEAKER), 4.2 (ST_GAS) all unmoved, so the nyiso-194 /
  nyiso-195 DO-NOT-REDO line is intact. No `phys_*`, no `econ_low_share`, no `pct_peaking`. No
  adder, offset, haircut, load proxy or fuel-price rescale of any kind.
* **(b) ONE config across every scored year** — the same 30 values solved 2023, 2024, 2025 and the
  2022 touchpoint. No per-year value exists.
* **(c) 3.0 % set ex ante, declared before the solve, NEVER SWEPT.** No 2 % / 4 % arm was built,
  scored, or considered after the fact. **The value did not move when it turned out to miss the
  motivation** — that is the condition working, and it is the whole point of it.
* **(d)** merit change across classes is the intended effect (CC_CHP −0.044, CC_REGULAR −0.052,
  ST_GAS −0.063, CT_CHP +0.054, CT_PEAKER +0.011 TWh in 2023).
* **(e)** the DOF-ledger and `authorized_price_tuning` obligations attach **only on registration**,
  which did not happen. Were the owner to promote, the attestation must carry the
  `authorized_price_tuning` block (channel, value 1.03, band scope, both owner rulings) or **C6
  FAILS**, and the multiplier is a **free parameter** whose identification source is *"price
  residual, authorized channel (rules 1/13 amendment 2026-09-05; band scope + screen order, owner
  rulings 2026-09-07)"* — not a measured source.

**Rule 22 `[R-HOLDOUT]`, held exactly.** 2022 MOTIVATED the work and was never its target: no gate
read it, no parameter was identified against it, the value was frozen before it was measured, and
the determination rests on the train tier alone (rule 30(c)). The 2022 spend is a validation-tier
touchpoint re-test — NYISO holds `complete`, and the spend freeze is scoped to the locked tier
alone — run **after** the value was frozen and reported for information.

## 3. What the mechanism actually does — the structural finding

**The handoff's ~1:1 passthrough assumption is measured false**, and the reason is structural, not
numerical. Under `gas_offer_net_revenue_margin` a tranche's cost is
`phys × HR_base × fuel(t) + markup_hr × anchor`, so lifting the registered multiplier raises only
the **anchored markup**: `Δmc = 0.03 × mult × HR_base × anchor`. The dollar effect is therefore
nearly year-invariant while the percentage effect shrinks as the price level rises.

| year | Δ load-weighted mean LMP | predicted (inzone / system) | realized ÷ predicted | **$/MWh per 1 % of band** | as % of level |
|---|---:|---:|---:|---:|---:|
| 2023 | **+0.7167** | +0.6418 / +0.6715 | 1.117 | **0.2389** | +2.13 % |
| 2024 | **+0.6834** | +0.6384 / +0.7259 | 1.071 | **0.2278** | +1.70 % |
| 2025 | **+0.8881** | +0.6609 / +0.8665 | 1.344 | **0.2960** | +1.44 % |
| *2022* | *+0.9530* | *+0.8511 / +0.8410* | *1.120* | *0.3177* | *+1.34 %* |

**This is the number the owner needs to choose a different value, if they want one.** At the 2024
level, reaching a 1-pp C3a move costs ≈ 1.7 % of band lift; closing 2022's remaining 2.5 pp from
the keeper would need roughly a **6–7 %** lift, which would push 2024 to roughly **+9 %** — inside
±10 %, but with almost no headroom, and C3b-2024 (already the tightest at 0.185 against a 0.20 bar)
would be the binding risk. **That is arithmetic offered for an owner decision, not a value I
selected or tested** — condition (c) forbids me to sweep it, and I did not.

## 4. The pre-registered predictions, adjudicated as written

* **P1 (construction) — FIRES.** Phase 0: **0** `peak`, `mustrun`, `sync` or non-fossil rows moved
  in any of four years; the moved set is exactly the three energy bands of
  `{CC_CHP, CC_REGULAR, CT_CHP, CT_PEAKER, ST_GAS}`.
* **P2 (direction) — FIRES.** Positive in every year.
* **P3 (magnitude) — FIRES.** +0.7167 on the screen year, inside the ex-ante [+0.321, +1.343]
  window at 1.117× the prediction. **The phase-0 arithmetic is confirmed to within 12 %.**
* **P4 (the prediction declared to HURT) — FIRES ON BOTH LIMBS.** I predicted the realized effect
  would be **larger in absolute dollars in 2025 than 2023** (+0.8881 vs +0.7167 ✓) and **smaller as
  a percentage** (+1.44 % vs +2.13 % ✓). This hurts the preferred answer directly: it means the
  lift buys the *least* relative correction exactly where the residual is most negative, which is
  why the motivation is not reached. Had the response instead been ≈ +3 % of level in every year,
  my whole reading of the mechanism would have been wrong.
* **P5 (confinement) — FIRES** on all three limbs in all three years: moved-class aggregate falls
  (−0.095 / −0.073 / −0.062 TWh), all-class sum ≈ 0 against a 0.74 TWh tolerance, `ST_CHP` bounded.

## 5. **S-1 FAILED AS WRITTEN, and the failure is mine** — reported, not rewritten

S-1's substantive limbs all held (30/30 bands, every ratio exactly 1.03, zero violations, no moved
frozen band, no other live field). It failed on
`{ercot_zonal_spread_ep_referenced, spp_gas_commitment_bridge}` — two `ScenarioConfig` fields that
**did not exist** when the keeper solved at `51f2fc2d`, so the "difference" is `absent → False`.
**Both were already named and classified INERT in my own PREREG §4 G-DRIFT audit before the solve**;
I simply failed to encode "absent means False", which nyiso-213's S-1 had had to encode for the same
reason. The gate was **not** rewritten to pass.

**The outcome partition has a gap, and it is a result.** PREREG §6 routed *any* S-1 failure to the
kill branch, without distinguishing "the arm is not the config I declared" from "my gate is
misdrafted". Both reach branch (A). I named the gap in an addendum and declared the disposition —
proceed to the span — **before** spending it, with the literal reading's cost stated in place. That
is the nyiso-215-P2 / nyiso-217-P3 standard: a gate that misses is reported as the defect.

## 6. The full record, reported at full magnitude

| | 2023 | 2024 | 2025 | *2022 (touchpoint)* |
|---|---|---|---|---|
| C3a keeper → arm | +4.3 → **+6.5 %** | +5.3 → **+7.1 %** | −7.3 → **−6.0 %** | *−12.5 → **−11.3 %** (FAIL both)* |
| C3b keeper → arm | 0.122 → 0.132 | 0.179 → **0.185** | 0.160 → **0.154** | *0.229 → 0.222 (FAIL both)* |
| C4 gas keeper → arm | r 0.941 / 0.124 → 0.941 / 0.124 | 0.899 / 0.133 → **0.898** / 0.133 | 0.841 / 0.187 → 0.841 / 0.187 | *n/a* |
| C1 / C2 flips | none | none | none | *n/a* |
| tail > $300 (max zonal) | 2 → 2 | 0 → 0 | 3 → 3 | *n/a* |

**Reported because it cuts against the arm:** the lift makes the price level **worse in two of the
three training years** (2023 and 2024 move further above actual) and better in one (2025). C3b
degrades in 2023 and 2024 and improves in 2025. **2024 is the tightest cell in the model**: C3b
0.185 against a 0.20 bar, 0.015 of room, and C3a at +7.1 % with ~2.9 pp of headroom.

**Instrument validation, measured not asserted.** The payload rebuild reproduces the committed
keeper payload **exactly** in 2023/2024/2025 — `lmp.p` and `gmModel` max abs diff **0.0**, and the
rebuilt `fuelRows` gas row identical to the committed one on every field. **One honest exception,
disclosed rather than absorbed:** in **2022** the `lmp` half is exact (0.0) but the `gmModel` half
is **not** — the committed payload carries an `OTHER_FOSSIL` class of 0.7567 TWh that a raw
`class_hourly` rollup does not produce, redistributed across CC_REGULAR (+0.318), CT_PEAKER
(+0.341) and ST_GAS (+0.099). C3a and C3b read only `lmp`, so the 2022 price scores above are
sound; **I therefore quote no C1 or C2 number for 2022 at all.**

## 7. Disposition, and **the promotion question, put explicitly**

**This lane's recommendation: NOT a keeper.** The reasons, stated as a recommendation:

1. It adds **no structure**. Rule 1's first half is untouched by the carve-out: *"a run is a keeper
   because it is the most structurally faithful, not because it has the lowest MAE."* This arm is
   purely a level move and would enter the DOF ledger as a **free parameter**.
2. It makes the price level **worse in 2 of 3 training years**.
3. It does **not** achieve the objective that motivated it (2022 stays outside ±10 %).
4. Nothing is broken by it either — every criterion still PASSes, and the determination would be
   unchanged at **CALIBRATED**.

**But that is a recommendation, and rule 31 `[R-RETAIN]` is explicit that the decision is the
owner's.** The owner directed this move and may well want it promoted regardless; a session may
never foreclose that by destroying the evidence.

**ALL THREE BUNDLES ARE RETAINED ON LOCAL DISK AND ARE NOT COMMITTED** (gitignored, which is what
discharges rule 29(c) — the duty is to keep them out of `main`, never to erase them):

| bundle | size | what it is |
|---|---|---|
| `results/calibration/_nyiso218_span_lift103` | 118 MB | **the promotable artifact** — full span 2023-2025, one invocation, one bundle (rule 16) |
| `results/calibration/_nyiso218_span_tp2022` | 39 MB | the 2022 validation touchpoint on the arm recipe |
| `results/calibration/_nyiso218_screen_2023` | 39 MB | the rule-29 screen arm |

**THIS CONTAINER IS EPHEMERAL: none of these survives session reclamation.** If the owner wants the
arm promoted, the remaining work is the branch-(B) package — D-5(b) artifact-only determination
re-verification **before** re-keying `complete.NYISO.keeper` (a worse determination stops the
promotion and escalates), registration, `stamp_touchpoint_holdout.py`, `build_status.py --iso
NYISO`, forecast gate (a) re-key, all in one PR. **If the bundles are gone by then, reproducing
them costs ≈ 35 min (span) + 12 min (2022) of LP** — stated before any re-solve, per rule 31.

## 8. The successor object

`docs/FINDING-nyiso218-hydro-within-month-daily-allocation-2026-09-07.md` — NYISO's hydro shape
residual is **not** a diurnal-shape defect. It is a **within-month, day-to-day allocation** defect
(within-month day-energy r **0.207–0.392** against hour-of-day r 0.975–0.989 and month-energy r
0.898–1.000), the model **over-swings** the river day to day by **1.86–2.25×**, and two of my own
readings were overturned by measurement along the way. It is flat across all four years, so it is
identifiable **entirely on the training tier with zero rule-22 exposure**. No mechanism is proposed
and no matrix cell letter moves.

**No eighth owner card is opened.** The seven pending rulings are untouched.
