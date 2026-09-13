# Multi-ISO Expansion — Planning Set

Planning documents for expanding the simulator from ERCOT to a faithful
backcast across **CAISO, PJM, ISO-NE (NEISO), MISO, NYISO, and SPP** — seven
ISOs with ERCOT. (SPP was registered 2026-09-06 by lane SPP-20 under the SPP
addition program, `spp-addition-plan-2026-09.md`; before that it appeared only
as a MISO RDT wheeling path.)

> **Status (largely executed):** these started as forward plans, but all seven
> ISOs are now registered multi-zone in `config/iso_configs.py`, and several
> (ERCOT, NEISO, NYISO, PJM, CAISO) have backcasts on the calibration dashboard.
> Treat these as the *rationale and process* record; for current topology and
> behaviour the code and `docs/codebase/` are authoritative. The dated
> per-ISO/`*-2026-06` notes here are point-in-time investigation logs.

| Doc | Covers |
|-----|--------|
| `00-iso-addition-protocol.md` | **Start here.** Baseline state per ISO, the 8-stage addition protocol, copyable per-ISO checklist, sequencing, non-negotiables. |
| `01-data-needs-and-upload-manifest.md` | The six data families, sources, repo locations, and exactly what to upload per ISO (EIA-930 hourly, CEMS gaps, gas basis, zonal load, hydro). |
| `02-market-design-modules.md` | LP modularity assessment, the capacity-market revenue gap, per-ISO module profile, toggleable module catalogue. |
| `03-prompt-pack-plan.md` | Self-contained build prompts (Packs A–J) with files, tests, acceptance criteria, and ERCOT regression guard. |
| `04-transmission-zones-and-congestion.md` | Per-ISO zone topology, congestion corridors, TTC sourcing (binding-frequency method), renewable HSL sourcing. |
| `05-backcast-playbook.md` | **Canonical process reference (v2).** The end-to-end recipe at ERCOT/PJM parity; copy doc 06's pack structure per new ISO. |
| `06-caiso-prompt-pack.md` | CAISO instantiation — the template prompt pack (P0–P14 waves). |
| `07-nyiso-prompt-pack.md` | **Moved → `docs/sessions/multi-iso/07-nyiso-prompt-pack.md`** (archived, 2026-07 triage). NYISO instantiation — hydro (Niagara/St-Lawrence), downstate congestion, dual-fuel winter, HQ/PJM imports, RGGI, ICAP; P0–P13 merged + P14 doc-sync done. |
| `08-neiso-prompt-pack.md` | **Moved → `docs/sessions/multi-iso/08-neiso-prompt-pack.md`** (archived, 2026-07 triage). NEISO (ISO-NE) instantiation — Algonquin winter basis + dual-fuel, HQ Phase II imports, Northfield PS, FCM, RGGI; P0–P13 + P14 Stage G/H sign-off done. |
| `09-ercot-propagation-prompt-pack.md` | **Reverse direction.** Audit of ERCOT's accumulated changes + a sequenced pack to perpetuate the *generic* engine improvements across all ISOs while leaving the *energy-only-specific* ones (ORDC, AS revenue, RTC+B) in ERCOT. |
| `spp-addition-plan-2026-09.md` | **SPP addition program (chartered 2026-09-06).** Definition of done, the eight owner cards (P1–P8), wave graph W1–W6, lane table with `[FABLE]`/`[OPUS]` labels, fetch/upload manifest, hard gates, and the prompt pack. Director: the SPP addition desk (`docs/handoffs/spp-desk-handoff-2026-09-06.md`, ledger `spp-desk-ledger-2026-09.md`). SPP stays unregistered until its W2 lane lands. |
| `soco-addition-plan-2026-09.md` | **SOCO addition program (chartered 2026-09-12).** Adds the **Southern Company balancing authority** (Alabama Power / Georgia Power / Mississippi Power) as the eighth registered region — the footprint the Hillabee Energy Center (EIA plant 55411, Tallapoosa County AL) sits in. SOCO is a **BA, not an RTO**: no LMP, no day-ahead market, no capacity market, so the plan's load-bearing owner card (S2) is what the price benchmark and the determination class are at all. Ten owner cards (S1–S10), wave graph W1–W6, lane table, fetch manifest, hard gates and the prompt pack. Director: the SOCO addition desk (`docs/handoffs/soco-desk-handoff-2026-09-12.md`, ledger `soco-desk-ledger-2026-09.md`). SOCO stays unregistered until its W2 lane lands. |
| `nwpp-addition-plan-2026-09.md` | **NWPP addition program (chartered 2026-09-13).** Adds the **Northwest Power Pool / Western Power Pool footprint** — ~17 WECC balancing authorities (BPAT, PACE, PACW, PGE, PSEI, AVA, IPCO, NWMT, CHPD, DOPD, GCPD, SCL, TPWR, AVRN, GRID, WAUW, NEVP) — as a registered region: the footprint the **Hermiston Generating Plant** (EIA plant 54761, Umatilla County OR, BA `PACW`) sits in. It is the first region that is a **pool of many BAs** rather than one BA or one RTO, and it is **36.3 % conventional hydro** with eight ≥1 GW plants on one hydraulic chain. There is no NWPP LMP, but unlike SOCO there *are* measured prices (CAISO WEIM 15-minute LMPs; the Mid-C traded index), so card **N2** is what the benchmark and the determination class are. Ten owner cards (N1–N10), wave graph W1–W6, lane table, fetch manifest, hard gates and the prompt pack. Director: the NWPP addition desk (`docs/handoffs/nwpp-desk-handoff-2026-09-13.md`, ledger `nwpp-desk-ledger-2026-09.md`). NWPP stays unregistered until its W2 lane lands. |

> **Archived session notes → `docs/sessions/multi-iso/`.** The 2026-07 triage
> (`docs/handoffs/multi-iso-triage-2026-07.md`) moved **27** dated, point-in-time
> investigation / backcast notes (including docs 07–08 above) out of this
> directory to `docs/sessions/multi-iso/`; see `docs/sessions/README.md` for the
> index. This directory now keeps only the living, still-authoritative references.

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
