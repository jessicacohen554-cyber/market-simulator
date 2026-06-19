# context/

Reference knowledge for the **Expert Reviewer** agent (SA-2 in
[`market-sim-build-plan.md`](../market-sim-build-plan.md)). That agent reviews
the LP formulation, capacity-evolution, storage and calibration design against
established production-cost / capacity-expansion models, and reads its
background material from this folder.

**Status: placeholder.** The reviewer agent's reference summaries have not been
populated yet. The folder is intentionally kept (rather than removed) so the
build-plan's documented structure stays valid and the material has a home when
it is written.

When populated, this folder is intended to hold one methodology summary per
reference model, plus a cross-model comparison:

| File                   | Contents                                                                  |
|------------------------|---------------------------------------------------------------------------|
| `aurora.md`            | Aurora methodology: dispatch, transmission, capacity expansion            |
| `plexos.md`            | PLEXOS: MILP/LP modes, transmission, storage, pricing                     |
| `reeds.md`             | NREL ReEDS: capacity expansion, time slices, renewable supply curves      |
| `ipm.md`               | EPA IPM/NEEDS: regulatory focus, multi-pollutant, retirement logic        |
| `genx.md`              | MIT GenX: configurable LP, representative periods, multi-stage investment |
| `regen.md`             | EPRI US-REGEN: economy-wide, capacity expansion + dispatch                |
| `cambium.md`           | NREL Cambium: marginal emission rates, Scope 2 accounting                 |
| `egrid.md`             | EPA eGRID: emission-factor methodology, subregion definitions             |
| `comparison-matrix.md` | Cross-model comparison table                                              |
