# RESULT xiso-8 — the year-start left-edge object

**Lane:** xiso-8 (cross-ISO: CAISO + MISO) · **Date:** 2026-09-20
**PRECOMMIT:** `docs/PRECOMMIT-xiso8-year-start-left-edge-2026-09-20.md` (bands in §5, registered before any solve)
**Registered run:** `2026-09-20-caiso-290-leftedge` — bundle `results/calibration/xiso8_leftedge_span`
**DETERMINATION: CALIBRATED** on 2022–2025, single ledgered C3c caveat.
**PROMOTION: NOT TAKEN — the owner's call, and it is open. See §7.**

---

## 1. The answer in one paragraph

`_flow_date_staircase` priced every year's opening flow days from the year's
**first January trade** — one that had not happened yet and that prices a *later*
flow day — when the function's own documented convention says the **previous
December's last trade** covered them. Repaired behind a default-off
`ScenarioConfig` gate and armed for CAISO, the fix moves 3/3/2/2 days in
2022–2025 and **every year lands inside its pre-registered band**. The
determination is unchanged at CALIBRATED, now carrying **all four years in one
bundle** instead of a three-year span plus a separately-stamped 2022 rung.
**MISO is measured and deliberately not armed**: its exposure is 0.0293 % of the
annual mean in its worst year, ~30× smaller than CAISO's, so six shards were not
spent — the shared code path is repaired for it, gated off.

---

## 2. What phase 0 found that changed the object's shape

The lane instruction expected MISO's exposure to be the open question. It was —
and the first naive measurement said MISO 2023 was worth **+$106.61/MWh**, ten
times CAISO's worst year. That number was an artifact of the harness, and running
it down produced the finding that defines the design:

> **Not every year-boundary gap is a trading package.** The flow-date convention
> licenses carrying December's trade forward across a **package**. It licenses
> nothing across an **EIA publication blackout**. CAISO's boundaries are 2–4 day
> packages; MISO's are mostly 15–19 day blackouts, and MISO 2023's last December
> print is the **Winter Storm Elliott spike at $17.69/MMBtu** against **$3.38** at
> the next measurement. An unscoped "always use prior December" repair would have
> carried a storm spike two weeks into January — **worse than the back-fill it
> replaces**.

So the seed is scoped to gaps `< _GAS_BLACKOUT_MIN_GAP_DAYS` (6), which makes it
**disjoint by construction** from `caiso_citygate_blackout_bridge` (which fills
only gaps ≥ 6). Rule 19 `[R-ONE-MECH]`, established rather than asserted:
verified inert on every MISO blackout year, 0 days moved.

Two harness defects were found and fixed in my own probe before any shard ran —
both would have mis-sized the object:

1. the first flow day must be read from **that year's own map** (what
   `_flow_date_staircase` sees), not the multi-year series, or a prior Dec-31
   print silently shortens the edge (this alone moved CAISO 2025 from "0 edge
   days" to 2);
2. the prior anchor is the prior year's last **trade**, wherever its flow day
   lands — slicing on `index < Jan 1` drops precisely the Dec-31 print that most
   often prices the edge.

After both fixes the probe reproduces caiso-289 §4's independently-measured table
**exactly** on all four CAISO years. That agreement, from a different harness, is
the cross-check the sizing rests on.

---

## 3. The bands, and where the arm landed

Construction is caiso-288's — **[no movement, full CC pass-through]** at 7.44
MMBtu/MWh, load-weighted from the outgoing keeper's **committed** hourlies —
computed and committed before any solve.

| year | edge days | Δ gas $/MMBtu | band | **landed** | % of limb |
|---|--:|--:|---|--:|--:|
| 2022 | 3 | +1.430 | [0, **+0.087** %] | **+0.054 %** | 62 % |
| 2023 | 3 | −8.350 | [0, −0.879 %] | **−0.799 %** | 91 % |
| 2024 | 2 | −0.470 | [0, −0.045 %] | **−0.036 %** | 80 % |
| 2025 | 2 | −0.220 | [0, −0.022 %] | **−0.010 %** | 47 % |

**All four inside.** The attribution is what makes that meaningful rather than
lucky — in every year the **edge-hour contribution in load-carrying zones
dominates** the total (+0.051 of +0.054; −0.791 of −0.799; −0.027 of −0.036;
−0.008 of −0.010), non-edge propagation is second-order, and the two import
nodes contribute **exactly 0.000 %**. The arithmetic predicted the solve.

---

## 4. Reported against the arm

**2022 gets slightly WORSE.** C3a vs actual RT: 2023 **+3.8 → +3.0 %**, 2024
**+7.4 → +7.3 %**, 2025 unchanged at **+7.4 %**, and 2022 **+6.85 → +6.90 %**.
That mixed direction is the signature this repair *should* have: 2022's gas delta
is **+1.430** and 2023's is **−8.350**, so the arm moves each year whichever way
that year's own source prints say, never uniformly toward the target. Rule 14
`[R-ACCURATE]` on the source convention is the whole case; rule 1 `[R-STRUCT]`
makes the residual direction evidence for nothing, in **either** direction.

**2024 carries 8,146 differing P1 price cells outside its 48 edge hours**, which
is not what a two-day gas change should do directly. Established as **degeneracy
on the PRIMAL**, not asserted:

* the swings concentrate at **WECC_PNW** (std 24.8, ±170 $/MWh) while every
  load-carrying zone shows p50 |Δ| of **0.0018 $/MWh**;
* **WECC_PNW and WECC_DSW carry ZERO load**, so their contribution to every
  load-weighted metric is **exactly 0.000 %** — they cannot touch C3a;
* the primal barely moves: **max |Δ class TWh| 0.0249 on 216 TWh**, total
  generation within **−0.0006 TWh**, with the movement in **hydro and import** —
  the two resources free to reshuffle at zero objective cost.

That is alternate optima. Worth the explicit contrast with the defect it
superficially resembles: rule 36's MISO incident moved **24.18 TWh** and ~**$500 M**
of objective. This is three orders of magnitude smaller and costs no objective.

**D-1 / D-4 / D-5 read FAIL** on this bundle — and read **FAIL identically on the
outgoing keeper** when the same diagnostics are run against it. Pre-existing, not
introduced here. (C7, the gate D-1 used to feed, was retired at rubric v3.1.)

---

## 5. What it cost, and what is owed

**Zero free parameters**, and verified rather than claimed: the DOF ledger is
**identical to the source at 9 entries / 6 residual**, and
`scripts/gen_xiso8_attestation.py` now *raises* rather than carrying the source's
ledger if the arm ever adds one. No offer-curve multiplier moves, so no
`authorized_price_tuning` block is owed. Default off, so **every existing config
in every ISO keeps its cache key** (CAISO backcast default unmoved at
`c831d560bf965030`; armed key a distinct `a8e3a7ced83ee791`).

**No control solve was spent** (rule 29 `[R-SCREEN]` (b), form 4). G-DRIFT was
audited at code level twice — against the keeper's `git_sha` and again from the
shard pin to the lane's rebased HEAD — and every changed backcast-path hunk
classifies INERT, mechanically confirmed by the byte-identical cache keys (which
since capx D79 carry the per-ISO solve-surface fingerprint).

**The `p0_*` sidecars are restored.** caiso-288 §5 recorded them as lost from the
CAISO keeper; this bundle carries `p0_dispatch_<y>.parquet` and
`p0_prices_<y>.parquet` for all four years.

---

## 6. MISO: measured, not armed

| year | class | Δ $/MMBtu | full-pass-through on the annual mean |
|---|---|--:|--:|
| 2021 | package | −0.180 | **−0.0293 %** |
| 2022 | package | +0.200 | **+0.0180 %** |
| 2020 / 2023 / 2024 / 2025 | **BLACKOUT** | — | out of scope by construction |

Two reasons it is small, both measured before any solve: only two of MISO's six
registered years are package boundaries at all, and its keeper reaches the
staircase **solely through `miso_chicago_daily_shape_factors`**, whose factors
renormalize to mean exactly 1.0 within every month — so a left-edge change
**cannot move January's level**, only its within-month shape. The level channel
(`miso_gas_marginal_commodity_pricing`) is off in the keeper.

The cut was made on **measured magnitude before any gate was consulted** (rule 1),
and §3.1(a) of the lane instruction pre-authorized it. **Stated as a cost, not
hidden:** MISO's keeper continues to carry the defect on 2021 and 2022 at the
sizes above. A MISO lane can arm it on its own cadence with no re-derivation —
the census is committed.

**Scope declared** (rule 28 `[R-MECH-MATRIX]` (d)): this lane edited **both**
CAISO's and MISO's matrix shards, a deliberate departure from the per-ISO
discipline, authorized by the owner's *"its own cross-ISO object"* + *"do a single
lane"* of 2026-09-20. No third ISO's shard was touched beyond duty (c)'s
one-cell-per-shard requirement for a new shared field.

---

## 7. THE PROMOTION QUESTION — OPEN, AND IT IS THE OWNER'S

**Nothing has been promoted and nothing has been pruned.** The run is registered
with `--no-prune`; `2026-09-20-caiso-288-citygate-recovery` is still CAISO's
designated keeper. Rule 35 `[R-PROMOTE]` (e) order — promote, verify, *then*
delete — has not been started.

**The case for promoting** `2026-09-20-caiso-290-leftedge`: same determination
(CALIBRATED) and same criterion statuses as the incumbent; one structural
correctness repair with zero free parameters; all four years inside
pre-registered bands; **all four years in one bundle**, which removes the
stamped-rung fold the incumbent needs; and the `p0_*` sidecars restored.

**The case against, stated fairly:** the price footprint is small (only 2023
exceeds a tenth of a percent), 2022's residual gets marginally worse, and the
incumbent is not broken.

**Rule 35 (b)/(c) are pre-cleared either way.** The CAISO year union is
`{2022, 2023, 2024, 2025}`, enumerated in PRECOMMIT §7 *before* any prune, and the
incoming bundle covers **all four** — so a promotion would not shrink the ISO's
year set, and the 2022 rung would no longer need
`stamp_touchpoint_holdout.py` at all.

**IF THE ANSWER IS YES, IT COSTS NOTHING NOW AND A FULL RE-SOLVE LATER.** The
composite is committed on this lane's branch, so promotion from here is a
keeper-shard edit plus a prune. The **four per-year legs are gitignored working-
tree files** whose shard branches are cut when this lane's PR merges (rule 33
`[R-SHARD-ARCHIVE]` (f)) — they are not a recovery route, and any leg-level
question asked later is costed as a **re-solve (~16 min/year, ~65 min for the
span)**.

---

## 8. Provenance

Legs solved at pin `e7091f56869d8eb190f9fb8f58e25c72aa97d405`, one year per shard
per rule 36, each pushing its full bundle including `dispatch/<y>_P1.parquet`
(rule 34 `[R-SHARD-PROMOTABLE]` (a)). Shard commits, **as provenance, not as a
recovery route** (rule 33 (d)): 2022 `fcd38961`, 2023 `054570b8`, 2024 `81174702`,
2025 `9ad71bf1`. All four shards archived after the parent fetched, checked out
and verified each bundle. Composed by `scripts/probes/xiso8_compose_span.py`,
which asserts the keeper's ten-field posture, a live `marginal_emission_rate`,
one shared solve-surface fingerprint (`0b6c20ac2fb77cee`) and
`gas_flow_date_year_start_package=True` on **every** leg.

**A prompt defect, recorded so the next lane does not repeat it.** Two of the four
shards stopped before solving because the CAISO keeper arms
`capacity_deliverability_limits`, which reads a curated partition
`hydrate_data.py` does not build. They behaved correctly — they stopped and
reported. The fix is an explicit setup step, and it needs a non-obvious
`PYTHONPATH=.`:
`PYTHONPATH=. python scripts/data/curate_capacity_deliverability.py --isos CAISO`
(386 rows). A third shard hit the same wall and self-recovered; only the strictness
of each container's permission classifier decided which stopped.
