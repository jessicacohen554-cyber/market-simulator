# FINDING — caiso-265: the "winter gas passthrough regime" hypothesis is **FALSIFIED**. 2022 is not a new regime — it is the training window's own shoulder-month over-pricing, plus one real gas month, plus a **7.8 pp benchmark-basis artifact** that has a zero-DOF repair.

**Session caiso-265, 2026-09-08**, branch `claude/caiso-backcast-2022-hvh9xz`.
Pre-registered in `PRECOMMIT-caiso265-winter-gas-regime-2026-09-08.md`, pushed
before any number was computed (commit on this branch, ahead of every
measurement below).

Keeper **`2026-09-06-caiso-260-b1-demand`** UNCHANGED — **CALIBRATED**, audit
0/0. Touchpoint `2026-09-07-caiso-262-2022-touchpoint` unchanged, still
NOT-YET. Rule 30(c): nothing here moves the ISO determination, and nothing
below was fitted to 2022.

**Zero LP solved.** Every number is computed from committed artifacts: the
keeper's and touchpoint's run payloads, the committed `bench/CAISO/<y>.json.gz`
parts, the committed `actual_lmp_hourly_CAISO.parquet`, and the committed CA
citygate daily print.

---

## §1 — The result

`FINDING-caiso262` §2 proposed that 2022's winter miss is **full measured gas
passthrough into a price regime the training window never contained**, and
labelled it a hypothesis. **The hypothesis is falsified.** Three independent
lines, any one of which is sufficient:

**(a) Two of the three "winter" months had ordinary gas.** The miss was built
on Jan **+28.5 %**, Feb **+31.4 %**, Dec **+27.7 %**. But measured CA composite
citygate was **$4.96/MMBtu in Jan-2022 and $4.79 in Feb-2022** — *below* 2022's
own $7.63 mean across the other nine months. Only December was a spike
($30.63 monthly mean, $53.59 daily max on 2022-12-21). The two **largest**
2022 errors are in the two months with the **cheapest** gas of the year. A
$54/MMBtu mechanism cannot explain them.

**(b) The training window DOES contain a gas spike, and the model prices it
almost exactly.** **Jan-2023: citygate $16.13 monthly mean, $24.29 daily max** —
a genuine western gas spike, in-sample. The model's error that month is
**+0.3 %** (load-weighted basis), its **best month of the 36**. The claim that
full passthrough at extreme gas breaks the model is directly contradicted by
the one extreme-gas month inside the training window.

**(c) In the training window the error moves the WRONG WAY with gas.** Over the
36 training months, `corr(err, gas) = −0.337`, slope **−2.69 pp per $/MMBtu**.
The error is *largest* where gas is *cheapest*.

## §2 — M1: the pre-registered measurement, 48 months

Model = the scorer's own basis (zone demand-weighted `pMon`×`dMon` from the
committed payloads). Actual = the committed bench monthly vectors. Gas =
measured CA composite citygate monthly mean — the series the runs consumed.
Full 48-row table in §9; the structure is:

| | corr(err, gas) | slope (pp per $/MMBtu) | corr(err, actual price) | mean err |
|---|--:|--:|--:|--:|
| **train 2023–25** (36 mo, lw basis) | **−0.337** | −2.69 | **−0.575** | +12.2 % |
| **2022 excl. December** (11 mo) | **−0.619** | — | **−0.555** | +18.4 % |
| 2022 incl. December (12 mo) | +0.160 | +0.21 | +0.083 | +19.2 % |

**Read the first two rows together — that is the finding.** Once the single
genuine gas-spike month is set aside, **2022 behaves like the training years**:
same sign, same relationships, comparable magnitude. The third row's near-zero
correlations are December alone reversing the sign of an 11-month pattern.

The extremes make it concrete:

| | gas | error |
|---|--:|--:|
| 2024-May | $1.62 | **+88.1 %** |
| 2024-Apr | $1.64 | +51.5 % |
| 2023-May | $2.58 | +62.3 % |
| 2023-Jan | **$16.13** | **+0.3 %** |

## §3 — What the object actually is

The model carries a **positive price bias that is proportionally largest when
prices are low** — the shoulder/spring months. `corr(err, actual price)` is
**−0.575** in the training window and **−0.555** in 2022-excl-December: the
same relationship, measured independently in both.

**This is why 2023–2025 pass C3a and 2022 fails, and the reason is arithmetic,
not physics.** C3a is a load-weighted annual mean, so it is dominated by
high-price hours — exactly where the model is accurate. In 2023–2025 the large
shoulder-month errors are diluted to +4.4/+8.9/+8.25 %. In 2022 the error
**never changes sign in any month**, so nothing offsets, and the annual number
fails. **A criterion that passes on a year whose monthly structure is this
wrong is a criterion being carried by its weighting**, and that is the honest
reading of the CAISO C3a pass.

**Rule 22 is therefore SATISFIABLE for this object**: the defect is present,
large and identifiable inside 2023–2025 (a +88 % month is not subtle). Nothing
would need to be fitted to 2022. **Rule 19 `[R-ONE-MECH]`:** this is very
likely the *same* object as the standing CC-side under-dispatch / over-import
lane (`caiso-121` surplus-belly, `caiso-131` belly decomposition, `caiso-140`
§B) seen on a seasonal axis rather than an hourly one. It should be worked
**there**, not as a new mechanism — I did not test one, and none is proposed.

**December is a separate, smaller question.** It contributes **36 %** of 2022's
annual $ gap on its own, and its implied heat rate is the one place the
passthrough story survives (model IMHR 9.99 vs actual 7.79). Whether the market
clears below full passthrough at $30+/MMBtu is a real question — but it is a
**one-month, out-of-sample** question that rule 22 forbids identifying against,
and Jan-2023 is the only in-sample evidence, where the model is already right.

## §4 — The unplanned discovery: 2022 is scored on a **different benchmark basis** than the years it is read against

**This was not pre-registered.** I found it while assembling M1's actual side
and I report it as an unplanned result.

The scorer's C3a/C3b basis ladder (`calibration_verdict.score_price_mean`,
rubric v2.4) prefers the **load-weighted** actual `rt_lw` and falls back to the
**legacy equal-hour** `rt` with an explicit label. The committed bench parts:

| year | `rt` (equal-hour) | `rt_lw` (load-weighted) | basis used |
|---|--:|--:|---|
| 2023 | 52.27 | **54.17** | load-weighted |
| 2024 | 32.94 | **34.65** | load-weighted |
| 2025 | 33.63 | **34.42** | load-weighted |
| **2022** | **79.07** | **absent** | **LEGACY equal-hour** |

So 2022's +21.1 % is model-vs-**equal-hour**, while every year it is compared
against is model-vs-**load-weighted** — and load-weighting raises CAISO's actual
by 2.3–5.2 % in every training year, because price correlates with load. The
2022 rung was scored against a benchmark that is systematically **low**.

`rt_lw` is absent for 2022 only because the retrofit predates the year: CAISO
2022's hourly RT parquet did not exist until caiso-262 landed it (2026-09-07).

**Measured, not estimated.** Running the committed, **unmodified** derive
(`derive_actual_lmp._lw_fields`) reproduces the committed 2023/2024/2025
`rt_lw` **exactly** — 54.17 / 34.65 / 34.42 — which validates the function, and
yields for 2022:

```
CAISO 2022:  rt_lw 84.49   da_lw 92.14   (legacy rt 79.07  da 86.31)
```

Re-scored with the scorer's own `score_price_mean` / `score_price_shape`:

| criterion | as scored (legacy) | like-for-like (`rt_lw`) | Δ |
|---|---|---|---|
| **C3a** mean LMP | FAIL **+21.1 %** | FAIL **+13.3 %** | **−7.8 pp** |
| **C3b** shape NRMSE | FAIL **0.286** | FAIL **0.242** | −0.044 |

**Both still FAIL, the rung stays NOT-YET, and the ISO stays CALIBRATED.** The
repair is not self-serving — it flips nothing. It moves roughly **a third of
the headline 2022 miss** out of "model error" and into "benchmark coverage",
which changes what the remaining residual is, and is why it belongs in the
record before anyone works the object in §3.

### §4.1 — What I landed, and what I deliberately did not

**LANDED:** the scoped, purpose-built retrofit, source-data citation per
rule 23 `[R-FROZEN-DERIVE]` (the source data updated — caiso-262 landed the
2022 hourly parquet):

```
python3 scripts/data/derive_actual_lmp.py --lw-retrofit --isos CAISO --years 2022
```

Verified surgical against a pre-change copy: **exactly 1 of 48 ISO-years
changed**, fields **added only** (`rt_lw`, `rt_lw_mon`, `da_lw`, `da_lw_mon`,
`src_lw`), **zero existing fields modified**, 47 ISO-years byte-identical. No
derive code was changed; no parameter exists to tune. This is rule 14
`[R-ACCURATE]` and rule 22's "inputs applied consistently across all years".

**NOT LANDED — and this is a decision for the owner, not for me.** The scorer
reads the **bench part** (`frontend/data/backcast/bench/CAISO/2022.json.gz`),
not the reference directly, and a part is rewritten only by *rendering a run*,
which needs the **full** bundle. The committed touchpoint bundle is slim
(rule 15 commits slim files + `hourly/` only), so **propagating this repair to
the dashboard requires re-solving CAISO 2022** (~30–60 min LP) and
re-registering the rung.

I did not do that, so **the repair is currently INERT**: verified above, the
keeper still scores CALIBRATED and the touchpoint still scores +21.1 %.
Everything is consistent today; the reference is simply more complete than the
part, which is the ordinary state until the next render.

**The one thing a future reader must not be surprised by:** the next CAISO run
that covers 2022 will rewrite that part and 2022's C3a will move +21.1 % →
+13.3 % **with no code change in its diff**. That is the NYISO-148 silent-part
failure mode (`check_bench_freshness.py`'s docstring), which is exactly why it
is stated here, in the calibration log, and in the queue.

## §5 — D-1 / D-2: **neither fired as written.** My decision rules inherited a false premise

The PRECOMMIT fixed a binary: **D-1** (error rises with gas ⇒ identifiable
in-sample, proceed) or **D-2** (error only at 2022's extreme ⇒ STOP, build
nothing).

**Neither antecedent is true.** D-1 requires a *positive* slope; the measured
slope is **negative** (−2.69). D-2 requires that the training window show no
relationship and the error appear only in 2022; the training window shows a
**strong** relationship and carries errors up to **+88 %**.

The binary was mis-specified because it took caiso-262 §2's framing as given,
and the measurement falsified the framing itself. I record this rather than
retro-fitting a rule to the outcome. **The substance of the rule-22 question the
PRECOMMIT said was logically prior is nonetheless answered, and answered
clearly: YES, the object is identifiable in-sample** (§3) — so the STOP branch
does not apply, and equally, no licence to tune 2022 has been created, because
the identification would happen entirely on 2023–2025.

## §6 — DISCLOSURES AGAINST INTEREST

1. **§4 was not pre-registered.** It is an unplanned discovery made while
   building M1's actual side. It is the most consequential result in this
   document, and it was found by accident, not by design.
2. **My decision rules failed (§5).** A pre-registration whose branches both
   miss is a weak pre-registration. It did do its job in one respect — it fixed
   the measurement and the basis before any number existed, so the falsification
   in §1 cannot be an artifact of choosing the statistic afterwards.
3. **caiso-262 §2's "$54.05/MMBtu" and my "$53.59" are different numbers.** Mine
   is the CA composite daily max in the committed citygate print (2022-12-21);
   theirs is from the run log after the hub-basis overlay. I did not reconcile
   them and I do not claim theirs is wrong — the $0.46 is immaterial to every
   conclusion here, and §1(a) rests on Jan/Feb being ~$5, not on December's max.
4. **§3's "same object as caiso-121/131/140" is an inference, not a
   measurement.** I matched it on the seasonal signature and on the belly
   location caiso-131 reports; I did not run an hourly attribution to prove
   identity. Anyone acting on it should verify before assuming rule 19 is
   satisfied.
5. **December's passthrough question is left genuinely open.** I falsified it as
   an explanation for Jan/Feb — the months it was actually built on — and I did
   **not** falsify it for December, which is a real gas month with a real IMHR
   gap and 36 % of the annual gap. §3 says why it cannot be pursued against 2022.
6. **The +88 % / +108 % shoulder-month figures are on low denominators**
   ($12–17/MWh actuals). They are large in ratio and modest in $/MWh (~$7–11).
   C3a is a ratio criterion so the ratio is the relevant statistic, but anyone
   reading these as the dominant term in the annual mean would be wrong — the
   whole point of §3 is that load-weighting makes them nearly invisible annually.
7. **I installed the solve stack into this container** (absent at session start).
   No solve was run; it was needed to read parquet.

## §7 — QUEUE

1. **The §3 object — shoulder-month over-pricing — is the real C3a lane**, and
   it is in-sample identifiable. It should be worked inside the standing
   caiso-121/131/140 belly lane (rule 19), on the seasonal axis this session
   adds, **not** as a new mechanism.
2. **The §4 repair needs a 2022 re-solve to reach the dashboard.** Owner
   decision: it costs ~30–60 min of LP and re-registration, moves C3a
   +21.1 % → +13.3 % and C3b 0.286 → 0.242, and **changes no determination**.
   Until then the reference and the bench part differ, benignly and documented.
3. **December-2022 passthrough** stays open and is *not* pursuable against 2022
   (rule 22). It needs an in-sample high-gas case; Jan-2023 is the only one and
   the model already prices it correctly.
4. **`FINDING-caiso262` §2 should be read with this document beside it** — its
   monthly table and its C3c inversion (§3 there) stand; its *mechanism* does
   not.
5. Carried unchanged: the 2021 rung is blocked (`CAISO_PARTIAL_YEARS` amendment
   + a 60-day RTM gap, 2021-08-02..09-30); Panoche (permanent residual); the
   hod 22–23 import object (closed as data-intake); S2.

**No keeper change. No `ScenarioConfig` field. No offer-curve channel. No
mechanism was tested, so no mechanism-matrix verdict moves (rule 28(b) is not
engaged). No determination changed. Next number: caiso-266.**

## §8 — Reproduction

Every figure: `results/calibration/_caiso265_m1.json` (the 48-row table and the
statistics), regenerable from committed artifacts with no LP.

## §9 — The 48-month table

See `_caiso265_m1.json`. Columns: year, month, model (scorer basis), actual
equal-hour, actual load-weighted (2023–25), error on each basis, citygate gas
monthly mean, model IMHR, actual IMHR.
