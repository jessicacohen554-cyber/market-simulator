# Retirement-grain design note — zone re-aggregation cliffs (G-31)

*Diagnosis only, per the L-7 scope. No implementation this session; `capacity.py`'s
retirement/aggregation path is unchanged. This note scopes the 94%-false-retire grain
problem the ERCOT capacity hindcast surfaced and proposes candidate mechanisms for a later
capacity-fleet-representation pass. Rules 1/11/14 throughout: the fix targets the
retirement **grain**, never the screen decision, and nothing here is tuned to a residual.*

**Owner-facing headline:** the ERCOT hindcast's +534% cumulative over-retirement is
**grain-driven, not screen-driven**. The economic screen's *decision* is roughly right at
per-plant grain; the end-of-year re-aggregation into zone×efficiency bins turns "retire the
worst coal plant" into "retire a 4 GW zone aggregate at once." The remedy is a
fleet-representation change (preserve retirement granularity or allow partial-bin
retirement), scoped below; picking one is the owner/next-session decision this note exists
to support.

---

## 1. The evidence (capacity hindcast ERCOT 2021→2025, s2/s3 bundles)

From `docs/hindcast-reports/ercot-2021-2025-realized-s3-2026-07-05.md` (identical to s2 on
every retirement metric — the scarcity-footing flip is a no-op in this regime, G-30):

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired (cum.) | 1.534 | 9.725 | +534% | ❌ FAIL |
| unit recall >300 MW | 3 units | 1 matched | 33% | ❌ FAIL |
| false-retire GW (share of model) | — | 9.13 | **94%** | ❌ FAIL |
| coal retired GW | 0.932 | 9.204 | +888% | ❌ FAIL |

**The tell that it is grain, not the screen:**

- The **2022 evolution step, still at per-plant grain**, retired **1.71 GW vs 1.53 GW
  actual** — inside the magnitude the market actually saw. At per-plant grain the screen
  decision is approximately correct.
- The **2024 step, after re-aggregation to zone bins**, retires **two whole zone-level coal
  aggregates (≈ 4.1 + 3.4 GW) in a single year**. A single bin that clears the going-forward
  bar takes its entire multi-GW MW with it. That one step is most of the 9.2 GW coal
  over-retirement.

So the screen is deciding "this coal bin is below its FOM bar" correctly; the damage is that
after re-aggregation *one bin is 4 GW of physically-heterogeneous plants*, only ~1 GW of
which the real market retired.

## 2. Root cause in code

The evolution loop (`capacity.py::evolve_fleet`) applies the retirement/retrofit/entry
screens on the fleet at its **current** granularity, then unconditionally re-collapses the
survivors into ~36 efficiency-bin representative units for the next LP solve:

```
# capacity.py:2654-2657
# Retirements, retrofits and new entry have reshaped the fleet;
# re-collapse it into efficiency-bin representatives so the next LP solve
# gets ~36 thermal columns rather than one per physical unit.
fleet = aggregate_fleet(fleet, n_bins=config.heat_rate_bin_count)
```

Two properties combine into the cliff:

1. **`aggregate_fleet` is lossy on identity and lumpy in MW.** After the base year, the
   per-plant CAMPD coal units are merged into a handful of zone×vintage-efficiency
   representative units, each carrying multi-GW `pmax`. Per-plant heterogeneity (heat rate,
   FOM, age, actual-market fate) inside a bin is gone.
2. **`apply_economic_retirements` is all-or-nothing at the unit's grain.** It retires a
   *whole* generator row when its loss-year count crosses the fuel threshold. On a per-plant
   row that removes one plant; on a post-aggregation zone bin that removes the entire
   zone's coal aggregate. There is no partial-retirement path — a bin is either fully in or
   fully out.

This is the same identity-loss surface as the confirmed-exit `plant_code` matching gap
(G-28, `capacity.py:2392-2400`): "preserving per-plant identity through aggregation needs
the dispatch/economic-screen pipeline to accept un-aggregated coal tranches." A grain fix
that preserves per-plant retirement rows would also close G-28's forecast reach — the two
should be scoped together.

## 3. Candidate mechanisms

Three options, cheapest-to-most-invasive. Each keeps the screen decision untouched (rule 1);
they differ only in the granularity at which a retirement is *executed*.

### Candidate A — Intra-bin partial retirement (derate a share, not the whole bin)

Let `apply_economic_retirements` retire a **fraction** of a bin's `pmax` rather than the
whole row, sized to the sub-bin capacity that actually fails the bar. Mechanically: keep a
per-bin ledger of the underlying per-plant heat-rate/FOM distribution (carried as bin
metadata through `aggregate_fleet`), and when a bin crosses its loss threshold, retire only
the MW whose per-unit going-forward margin is negative, as a partial derate of the bin's
`pmax`.

- **Pro:** smallest change to the LP layout (bins stay ~36 columns; only `pmax` shrinks);
  directly removes the cliff (a 4 GW bin can shed 1 GW); no dispatch-side cost.
- **Con:** needs the per-plant sub-distribution to be carried as bin metadata so the derate
  MW is grounded (not an arbitrary fraction) — else it becomes a tuned knob (rule 14
  hazard). The derate fraction must be a *measured* per-plant split, not fitted to the
  residual.
- **Effort:** M. Touches `aggregate_fleet` (attach sub-bin ledger) + `apply_economic_
  retirements` (partial-derate branch) + tests.

### Candidate B — Preserve per-plant grain for retirement-eligible thermal through the re-bin

Exempt retirement-eligible fossil classes (coal first; optionally gas_st) from
`aggregate_fleet`'s zone collapse, carrying them as per-plant (or per-CAMPD-tranche) rows
through the evolution loop and into the next LP. Dispatch continues to bin the rest.

- **Pro:** structurally the most faithful — the screen retires physical plants at the grain
  the real market retires them (the 2022 step proves this grain is accurate); simultaneously
  closes G-28 (confirmed exits match on `plant_code` because identity survives).
- **Con:** grows the LP thermal column count for coal-heavy ISOs (per-plant coal instead of
  ~a dozen bins) → more memory/runtime; interacts with the offer-curve tranche machinery
  (coal take-or-pay/PRB sigmoid is defined per-bin). Largest blast radius on the solve core.
- **Effort:** L. Overlaps the "solve core accepts un-aggregated coal tranches" follow-up
  already named for G-28; should be co-scoped with the orchestrator/fleet-unification lane.

### Candidate C — Finer retirement sub-binning (a middle grain, dispatch unchanged)

Keep dispatch at coarse zone×efficiency bins, but split retirement-eligible coal into finer
sub-bins **for the retirement decision only** — e.g. bin by (zone × heat-rate decile × FOM
tercile) so a marginal retirement removes a plant-scale sub-bin (~0.5–1 GW), not a
zone-scale bin (~4 GW). The dispatch LP re-aggregates the surviving sub-bins back to coarse
bins each year.

- **Pro:** bounds the cliff to sub-bin size without carrying full per-plant rows into
  dispatch (cheaper than B); the grain is a declared, data-derived binning (rule 17 —
  re-derives only when the underlying fleet data updates), not a residual knob.
- **Con:** introduces a second binning grain (retirement vs dispatch) that must stay
  reconciled; the sub-bin count is a modelling choice that needs a documented basis so it
  isn't a covert tuning axis.
- **Effort:** M–L. New sub-bin builder + a retire-then-reaggregate seam in `evolve_fleet`.

## 4. Recommendation for the implementing session (not executed here)

- **Co-scope with G-28.** Candidate B closes both G-31 and G-28 but is the heaviest; if the
  orchestrator/fleet-unification lane is already opening the solve core to un-aggregated
  coal tranches, B rides on that and is the right structural answer.
- **If a standalone, lower-risk fix is wanted first,** Candidate A (partial-bin derate) is
  the smallest change that removes the cliff and is independently testable
  (1-gen/1-bin/24 h: a bin with a known sub-distribution sheds exactly the failing MW).
- **Guardrail (rule 14):** whichever is built, the derate MW / sub-bin split must be a
  *measured* per-plant quantity (heat rate, FOM, vintage from EIA-860/CAMPD), never a
  fraction fitted to bring the hindcast recall to 1.53 GW. The acceptance test is the 2022
  per-plant step (1.71 vs 1.53 GW) reproduced at every scored year, not a residual minimized.

## 5. Scope & status

- **Diagnosis only.** No `capacity.py` change this session.
- Evidence: `docs/hindcast-reports/ercot-2021-2025-realized-s3-2026-07-05.md` §"Zone-bin
  re-aggregation grain"; `docs/hindcast-reports/ercot-2021-2025-realized-s2-2026-07-05.md`.
- Cross-refs: G-28 (`plant_code` identity loss, `capacity.py:2392-2400`); the
  fleet-representation/solve-core follow-up named in both.
- Implementation deferred to a later capacity-fleet-representation session (owner picks A/B/C).

*Produced 2026-07-06, L-7 (capacity economics & hindcast closure), G-31.*
