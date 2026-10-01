# DIAGNOSIS — ERCOT-125: the jointly-owned-unit offer split FAILS the rule-13 forward test, and is not expressible on the model's plant grain; no mechanism is licensed and no probe is built

**Date** 2026-07-27 · **ISO** ERCOT · **Lane** ercot125-coal-owner-split ·
**Keeper under audit** `2026-07-26-ercot115-coal-marginal-hr` (bundle
`results/calibration/ercot115_coal_floor_only`) — **unchanged by this session** ·
**Chartered by** `docs/DIAGNOSIS-ercot124-coal-offer-uppertail-2026-07-27.md` §5.3
(which CLOSED the coal offer-curve lane and named this as the one surviving
measured coal mechanism, explicitly carrying the live rule-13 question forward) ·
**Method** Phase 1 only — the rule-13 `[R-MEASURED]` forward-test gate, plus a
channel-expressibility audit read directly from the solve path.
**No LP was built. No year was solved. No arm was registered. No `ScenarioConfig`
field, cache-key surface or solve path was touched. No keeper file was touched.**

**Outcome: Phase 1 FAILS the forward test on four independent grounds, and fails
channel expressibility on two more. Phase 2 was not run, and the default-off
diagnostic probe is recommended AGAINST as well.** The conduct ERCOT-124 §2
isolated is real, persistent and correctly measured; what it is not is a quantity
any forward year can regenerate, and there is nothing on the model's plant grain
for it to attach to. §1 settles the forward test, §2 the channel, §3 the
recommendation.

---

## 0. What is inherited, re-verified from the committed artifacts

Every number below is read from `origin/main` at `e14f7b4`, not assumed:

| claim | source, verified |
|---|---|
| the two resources and their offers | `offer_curve_sced_coal_uppertail.json` `_provenance.owner_split_resources`; ERCOT-124 §2 table |
| `FPPYD1_FPP_G1_J02` \$150.10 (2024) → \$116.00 (2025); `_G2_J02` \$150.10 → \$113.15 | ERCOT-124 §2 |
| co-owner shares of the SAME machines: `_G1_J01` \$18.74 → \$17.35, `_G2_J01` \$18.41 → \$16.24, `FPPYD2_FPP_G3` \$19.66 → \$17.52 | ERCOT-124 §2 |
| 2023 cross-instrument corroboration, `FPPYD1_FPP_G1_J02` \$114.00 on the DAM disclosure | `DIAGNOSIS-ercot122-…` §1(b) line 57–58 — and note it also records "**most of Fayette contributing nothing**" to that band, i.e. the co-owner shares do not reach it in 2023 either |
| 68–71 % of the measured tail; 3.48 pp (2024) / 3.75 pp (2025) of HASL | ERCOT-124 §1–§2 |
| the model has ONE Fayette plant | `data/raw/reference/master-plant-registry.csv:330` — code **6179**, **1690.0 MW**, `Fayette Power Project`, SUB/ST |
| the keeper forces ZERO coal energy | ERCOT-124 §3 #8 (D-2 has no COAL row in any year) — inherited, not re-derived, per the charter |

**Sampling bound, carried on every SCED number in this document: 82 probe days,
2024–2025 only.** No 2023 SCED exists. Nothing here is an annual statistic.

**The premise is an inference, not a measurement — and this matters to §1.** ERCOT-124
§2 is explicit: *"the disclosure carries no ownership field, so the attribution is
an inference from the capacity arithmetic and the offer split, not a measured
fact."* What is measured is that a registration suffixed `_J02` offers ~8× its
same-machine sibling. That the two are ownership shares, and which entities hold
them, is nowhere in our committed data.

## 1. The rule-13 `[R-MEASURED]` forward test — settled explicitly and ex ante

The test, verbatim from CLAUDE.md rule 13: **could this same quantity be produced
for a forward year from forward drivers, and would it respond to changed
conditions?**

### 1.1 The steelman for admission, stated first

It deserves one, because the charter is right that this is the hardest case in the
rulebook. Rule 13 admits **unit outage windows** — "a physical availability
event" — even in backcast mode. An owner who will not run its share is
*functionally* an availability restriction: 616 MW of Fayette really does not
respond to a \$20–100 price, and that is as physical in its effect as a boiler
being out. The conduct is measured, it is persistent across two SCED years, and it
is corroborated on a second instrument in a third year. On the "is it real?" axis
it is stronger evidence than most things the model already carries.

**It fails anyway, and not narrowly.** Rule 13's test is not "is it real"; it is
"does it regenerate forward from forward drivers." The four findings below are
independent — any one is sufficient.

### 1.2 (a) The forward driver cannot be named from committed data — and if named, it is an announcement, not an instrument

An outage window has a generative forward model: maintenance seasonality and
forced-outage rates are class/technology properties the model derives from
multi-year history conditioned on operation, so "Oak Grove is out in March"
regenerates for 2035 as "coal of this age and type carries this EFOR and this
maintenance season." **There is no analogous generative model here.** The two
shares are slices of the *same two boilers* — identical heat rate, identical
delivered fuel, identical emissions rate, identical node. Every physical and
market variable the model carries is, by construction, equal across them. The
quantity is therefore a pure function of *who holds which share and what that
holder wants* — a governance fact, and one our data does not even contain (§0).

If the driver is named anyway as "the co-owner's stated exit policy," then measure
it against the standard CLAUDE.md step 0 already sets for exactly this class of
claim — an **enforceable public instrument**: RTO deactivation acceptance, consent
decree, statute, regulatory order, RMR end. A board or council resolution to stop
participating in a plant is an **announcement**, not an instrument. And the
registry that would carry it is present and empty: **`data/raw/confirmed-retirements/ercot.csv`
contains no Fayette row** (grepped for `6179` and `fayette`, zero hits across all
six ISO files). The model's own instrument bar is currently *not met* for this
plant.

### 1.3 (b) The only registered offer-height form responds to a driver that demonstrably does not drive the quantity

This is the sharpest finding, and it is measurable rather than argued.

The registered way to raise a band's offer is a **heat-rate multiplier**
(`offer_curve_by_group`, `offer_curve_deltas`, the per-plant sheet's `hr_*`
columns). Such a channel's *entire* forward responsiveness is to the delivered
fuel price it multiplies. Fayette is PRB (`coal_supply_class(6179) == "prb"`), and
the delivered PRB price the model dispatches on is **flat across the measured
window**:

```
COAL_PRICE_PRB_BY_YEAR: 2023 $2.15 → 2024 $2.00 → 2025 $2.00 /MMBtu
```

So over 2024→2025 an hr-mult channel is, by construction, **constant**. The
measurement over exactly that period:

| resource | 2024 | 2025 | change |
|---|---|---|---|
| `FPPYD1_FPP_G1_J02` | \$150.10 | \$116.00 | **−22.7 %** |
| `FPPYD1_FPP_G2_J02` | \$150.10 | \$113.15 | **−24.6 %** |
| `FPPYD1_FPP_G1_J01` (co-owner, same machine) | \$18.74 | \$17.35 | −7.4 % |
| `FPPYD1_FPP_G2_J01` (co-owner, same machine) | \$18.41 | \$16.24 | −11.8 % |
| `FPPYD2_FPP_G3` (single-owner) | \$19.66 | \$17.52 | −10.9 % |

On flat fuel the mult form predicts **0 %** movement and the quantity moved
**−23 to −25 %** — two to three times the movement of the cost-based shares of the
*same boilers*, which is itself the measurement's own noise floor on 82 probe days.
The channel's sole forward driver explains **none** of the variation. A mechanism
whose one responsiveness is to a variable the measurement shows is not the
variable would not respond to changed conditions in a forecast; it would respond
**spuriously**, moving with coal price for a quantity that visibly ignores coal
price.

*(Two-point observation, 82 probe days, 2024–2025 — labelled as such, and not
extrapolated. It is not offered as an elasticity estimate; it is offered as a
falsification of the one functional form the registry provides, and for that
purpose two points on a flat-fuel window are sufficient.)*

A fuel-invariant \$/MWh form (the `gas_offer_margin` shape) would at least not
respond to the wrong driver — but it would then be a **frozen measured constant**
carried to 2050 with no driver at all, which is the other half of the same
failure.

### 1.4 (c) What falsifies it, and what a forecast year does after the ownership changes — the charter's question (b)

**Falsifiers**: the share is sold or bought out; the joint-ownership agreement is
renegotiated; the holder reverses its position; the plant retires; ERCOT
re-registers the resource. **Under every one of them the measured quantity
collapses to the co-owner's ~\$17–19 — and the model would carry \$150 regardless,
because there is no state variable for any of them.** The mechanism has no
ownership dimension, no instrument date (contrast step 0's `instrument_date`
vintage gate), and no expiry. It would apply to every forecast year 2026–2050 as
an assertion.

### 1.5 (d) A verified forward side effect: the height would enter the retirement screen as a physical cost

Traced in code, not asserted:

1. `assembly.py:897` — the peak tranche is emitted as `("peak", peak_cap, peak_hr, …)`,
   and `assembly.py:998` sets that generator's `heat_rate=tr_hr`. Band multipliers
   **become per-tranche heat rates** on real LP units.
2. `runner.py:1198` — `mc_cost = assemble_mc(fleet_arrays, fuel_prices, carbon_price, …)`,
   documented in place as the "full variable cost … computed even on cached years
   because next year's economic retirement screen nets it against price
   (inframarginal margin, not gross revenue)."
3. `evolve.py:263` — `mc_cost = _prior_attr(prior_results, "mc_cost")`, consumed by
   the step-3 economic-retirement screen.

So a per-plant offer-height lift is **not** confined to the bid basis. It would
enter `mc_cost` as if 616 MW of Fayette had a ~6× physical heat rate, depress that
plant's screened attainable inframarginal margin, and push it toward **economic
retirement in forecast years** — the model retiring a plant because of a
governance disposition, through the door step 0 exists to guard, and with none of
step 0's evidence.

The codebase already states the governing principle at exactly this seam.
`runner.py:1251-1253`, on the gas net-revenue margin:

> "Applies to the BID basis only, never to `mc_cost` (the retirement screen's full
> variable cost above — **margins are offer components, not costs**)."

A withholding offer is the purest possible instance of "an offer component that is
not a cost." The multiplier surface carries no such exemption, so adopting this
there would violate the principle the adjacent mechanism was built to honour.

### 1.6 Verdict on the forward test

**FAILS.** The quantity cannot be produced for a forward year from forward drivers
(§1.2), the one registered form responds to a driver the measurement falsifies
(§1.3), nothing in the model can represent its falsifiers (§1.4), and carrying it
would misroute a governance fact into the physical-cost path that drives
retirement (§1.5).

Per rule 13 the honest ceiling for such a quantity is a backcast-only,
explicitly-labelled, **default-off** diagnostic probe, never enabled in a keeper
and never quoted as forecast skill. §2 shows it does not reach even that ceiling
cleanly, and §3 recommends against building it.

## 2. Is a per-registered-share channel expressible at all? — No, on two independent counts

The charter's second Phase-1 question. The model fleet has **one** Fayette plant
(`master-plant-registry.csv:330`, code 6179, 1690.0 MW). Enumerating the sanctioned
per-plant channels:

| channel | what it carries | can it carry an offer height? |
|---|---|---|
| `thermal_tranches_<ISO>.csv` (`coal_mustrun_per_plant`, `cc_committed_per_plant`, `online_frac`) | per-plant **capacity shares** | **No** — shares only |
| `cc_duct_peaking_pct` | per-plant **capacity share**, CC/CHP groups only | **No** — shares only, and coal-ineligible (`offer_curves.py:860`, `assembly.py:507-509` gate on `CC_REGULAR`/`CC_CHP`) |
| `COAL_MUSTRUN_BY_PLANT` | per-plant must-run **share** (6179 → **30.0 %**) | **No** — a share, and it moves the *bottom* of the curve |
| `plant_tranche_config_path` | per-plant 5 shares **+ 5 HR multipliers** | **Yes — the only one.** See below |

**Count 1 — the only height-carrying channel is an all-or-nothing override sheet
that would replace five live mechanisms at that plant.** `assembly.py:195-201`
states its precedence in its own comment: *"when set, each listed plant's tranche
shares + per-band HR multipliers come straight from the sheet, **bypassing the
offer curve and the per-plant committed/peaking dicts**."* Adopting it at Fayette
would therefore displace, at that plant, the `COAL_PRB` class bands, the keeper's
`offer_curve_deltas`, the bin sheet's `Pct_*` split and `coal_mustrun_per_plant`
(30.0 %) — replacing four-to-five of ERCOT-124 §3's eight enumerated coal
mechanisms in order to express one. Rule 19 `[R-ONE-MECH]` requires replace-or-
reconcile rather than stack, and this is technically a replace — but a *blind*
one, silently overriding mechanisms whose identification is unrelated to this
lane. It is also a **hand-edited what-if sheet reached by a file path**, not a
derived, committed, registered measured artifact, which is the only admissible
form rule 26 `[R-REGISTRY]` leaves open.

**Count 2 — and this is the deeper one — the model's tranches are an economic
merit ordering, while an owner split is a partition orthogonal to merit.**
Fayette's bands (`custom-bin-assignments.csv:67`) are
`Pct_Must_Run 25.0 / Pct_Committed 20.0 / Pct_Economic 50.0 / Pct_Peaking 5.0`,
i.e. a peak band of **5.0 % = 84.5 MW**. The withheld block is
**308.0 + 308.0 = 616 MW = 36.4 %** of nameplate — **7.3× the plant's entire peak
band**. Expressing it is not a re-shape of the top of the curve; it requires
asserting that the co-owner's 616 MW *is* the top 616 MW of the plant's economic
stack. **The measurement does not say that.** It says one registration's own curve
is high. Physically the two owners hold interchangeable slices of the same two
boilers; there is no measured basis for mapping an ownership partition onto a
merit ordering, and the model has no dimension in which the two could be held
distinct. Any implementation would have to *choose* that mapping — and rule 21
`[R-DOF]` is explicit that a quantity closable only by choosing a value is an open
root-cause issue, not a parameter.

## 3. Recommendation — recommend-and-STOP (keeper untouched; owner decides)

1. **Phase 2 is NOT run**, and per the charter's own stop condition this session
   stops at the Phase-1 gate. The forward test fails on four independent grounds
   (§1.2–§1.5) and channel expressibility fails on two more (§2).
2. **The default-off backcast-only probe is recommended AGAINST as well.** The
   charter offers it as the honest fallback, and it would be the right call if the
   only defect were the forward test. It is not: §2 shows there is no clean channel
   to build it in, so the probe would have to (a) ride a hand-edited override sheet
   that blindly displaces four-to-five unrelated coal mechanisms at Fayette, and
   (b) hard-code a merit-ordering assumption the measurement does not support.
   Building it means touching `ScenarioConfig`, the cache key and the offer path —
   real core-infrastructure surface, under rule 27 `[R-PUSH]` — to install a
   mechanism that can never be armed in a keeper and whose one output would be a
   number we already know by hand calculation (~0.4–0.8 TWh/yr, ERCOT-124 §5.3).
   **The measurement is already committed and already tells us the answer**
   (`offer_curve_sced_coal_uppertail.json`, whose `_provenance.owner_split_resources`
   names the two registrations); a probe would add solve-path risk and no
   knowledge. If the owner wants it anyway, §2 Count 2 is the design question to
   settle first, and it should be settled by measurement, not by choice.
3. **What WOULD reopen this lane** — recorded so a future session does not
   re-litigate §1 from scratch:
   (a) an **enforceable public instrument** for the share (deactivation notice,
   consent decree, order) — which routes it to **step 0 confirmed exits**, its
   correct home, with `instrument_date` doing the vintage gating and the reliability
   floor correctly bypassed; **not** to the offer surface;
   (b) an **ownership dimension in the fleet representation**, which would make the
   §2 Count 2 mapping a measurement rather than a choice — a large structural change
   with no other current customer;
   (c) a **forward driver with a generative model** — e.g. if divergent-co-owner
   conduct at jointly-owned units were characterized across many plants and ISOs as
   a class property, it could regenerate forward the way EFOR does. One plant is
   not a class.
4. **The successor lane is the ERCOT-116/121 availability envelope, and this
   session does NOT start it** (charter directive). It is now the dominant open coal
   residual at **+6.8 / +9.2 / +12.9 TWh** — **10–30×** this lane — and
   ERCOT-122/123/124 have jointly eliminated the entire coal offer surface (level,
   reach and tail) as its cause, which sharpens it considerably. It deserves its own
   charter.
5. **Three inherited owner decisions, surfaced once and NOT decided here** (carried
   forward unchanged from ERCOT-124 §5.5):
   (a) the **ERCOT-122 offer-LEVEL arm** as a registered controlled refutation —
   ERCOT-122 recommended against, ERCOT-123 §5 and ERCOT-124 §5.5(a) each
   independently strengthened that; one `replay_keeper` away, `DIAGNOSIS-ercot122`
   §5.1 is its pre-commit, separate bundle if run. **This session adds no new
   argument for or against it.**
   (b) the **committed-band data gap** — SCED carries `Min Gen Cost` (29–31 % of
   online coal resource-intervals) but is the RT instrument on 82 probe days, not
   the DAM committed band. Flagged; **not** fetched, transformed or approximated.
   (c) whether the **December-2025 SCED schema revision** warrants a re-fetch
   intake lane. This session inherits the drop unchanged.
6. **ERCOT-120 and ERCOT-117 §5.3 remain separate, un-renumbered lanes**, unaffected.

## 4. Scope, rules honoured, environment

**Diff against `origin/main` is this document and one calibration-log entry.** No
`ScenarioConfig` field, constant, cache-key surface, derive script, artifact or
solve path was touched, so no config pin moved and no existing run can change. No
run was registered; `frontend/data/backcast/keepers/ERCOT.json` untouched
(rule 20 `[R-DASHBOARD]` is not engaged — no run was produced).

Rule 22 `[R-HOLDOUT]`: no LP ran and no year was solved, so no holdout year was
touched; the only data read is the already-committed 2023–2025 in-window artifacts
and reference sheets. Rule 23 `[R-FROZEN-DERIVE]`: no derive script was run or
modified — `scripts/data/derive_sced_coal_uppertail.py` and
`scripts/data/derive_dam_offer_hrmults.py` are **untouched**, so their artifacts
(`offer_curve_sced_coal_uppertail.json`, `offer_curve_dam_hrmults_coal_yearly.json`,
`..._ep_yearly.json`) remain byte-identical to their committed state and no
re-derivation was required. Rule 25 `[R-ISO-SCOPE]`: nothing was fitted, so nothing
crosses an ISO boundary. No GitHub Actions workflow was added; no CI job was used.

**Closed lists honoured.** Nothing here reopens the coal offer-REACH question or
any of the four ERCOT-123 buckets; the coal offer-LEVEL lane and the pooled
`econ_high` 2.856; the coal offer-curve upper tail as a CLASS mechanism or any
`COAL_PRB`/`COAL_LIGNITE` `peak_ladder` (§2 confirms this lane's per-registered-share
successor is *also* closed, on different grounds); the EP-rebasis lane as a C3c fix
and the peak-p50/quantile-ladder legs; age/temp coal derates; the pooled HH-0.50
artifacts; `ercot_zonal_gas_basis` ablations; the West/Panhandle topology split.

**Environment.** Container built to the charter's spec (`pip install -e .`; pinned
`highspy==1.14.0` / `pandas==3.0.3` / `pyarrow==24.0.0`; `tzdata`, `pytest`).
Python 3.11.15, 4 cores / 15 GB. No solve was run, so the gtc-limits
"static TTC kept" clean-partition fallback and the hydro-plant-modes clean-partition
warning that every ercot115–124 baseline ran under were **not** exercised this
session and are recorded as not-applicable rather than matched.

**Test state (measured, reported, not chased; pins untouched).** Re-measured on
this session's container per the charter:
`tests/regression/test_persisted_identity.py` **passes 11/11** (0.94 s). This
**reproduces the ERCOT-124 container's result** and again contradicts the
ERCOT-122/123 sessions' "2 failed, 9 passed on clean `origin/main`" — two
consecutive containers now pass it, so the failing state should be treated as not
current. No pin was updated either way. This session's diff contains no Python, no
config surface and no cache key, so no test outcome is attributable to it; the
other pre-existing failures listed in the charter were not re-run, per its
instruction to report-not-chase.
