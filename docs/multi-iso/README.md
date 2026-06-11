# Multi-ISO Expansion — Planning Set

Planning documents for expanding the simulator from ERCOT to a faithful
backcast across **CAISO, PJM, ISO-NE (NEISO), MISO, SPP, and NYISO**. No code
has changed yet; these define *how* to do it, piece by piece.

| Doc | Covers |
|-----|--------|
| `00-iso-addition-protocol.md` | **Start here.** Baseline state per ISO, the 8-stage addition protocol, copyable per-ISO checklist, sequencing, non-negotiables. |
| `01-data-needs-and-upload-manifest.md` | The six data families, sources, repo locations, and exactly what to upload per ISO (EIA-930 hourly, CEMS gaps, gas basis, zonal load, hydro). |
| `02-market-design-modules.md` | LP modularity assessment, the capacity-market revenue gap, per-ISO module profile, toggleable module catalogue. |
| `03-prompt-pack-plan.md` | Self-contained build prompts (Packs A–J) with files, tests, acceptance criteria, and ERCOT regression guard. |
| `04-transmission-zones-and-congestion.md` | Per-ISO zone topology, congestion corridors, TTC sourcing (binding-frequency method), renewable HSL sourcing. |
| `05-backcast-playbook.md` | **Canonical process reference (v2).** The end-to-end recipe at ERCOT/PJM parity; copy doc 06's pack structure per new ISO. |
| `06-caiso-prompt-pack.md` | CAISO instantiation — the template prompt pack (P0–P14 waves). |
| `07-nyiso-prompt-pack.md` | **NYISO** instantiation — hydro (Niagara/St-Lawrence), downstate congestion, dual-fuel winter, HQ/PJM imports, RGGI, ICAP. Topology/zone-assignment/outage-windows already landed; starts at Stage E. |
| `08-neiso-prompt-pack.md` | **NEISO (ISO-NE)** instantiation — Algonquin winter basis + dual-fuel (the headline), HQ Phase II imports, Northfield PS, FCM, RGGI. Best CEMS coverage of the new ISOs; starts at Stage E. |

## At-a-glance roadmap

1. **Prove the pipeline:** run Pack A→B→J for **CAISO** (single zone + existing
   WECC import node) to get one non-ERCOT ISO backcasting end-to-end.
2. **Add reusable modules** as the ISO that first needs each one arrives:
   imports (C), capacity revenue (D), hydro budgets (E), fuels (F/G), policy (H).
3. **Scale topology:** PJM → MISO → SPP (zonal builds, congestion corridors).
4. **Deepen the LP last:** reserve co-optimization (Pack I), an additive
   refinement once an energy-only ISO calibrates.

## Ground rules (see doc 00 §4)

Every module defaults **off** so ERCOT's calibrated behaviour is unchanged;
every per-ISO parameter carries a citation; the dispatch LP stays vectorized,
struct-of-arrays, full 8760 hours, prices = energy-balance duals.
