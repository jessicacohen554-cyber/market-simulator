# Outage gate — is the residual still outage-side? Per-ISO diagnosis + the full-stop override (2026-06)

**Date:** 2026-06-22
**Branch:** `claude/outage-gate-iso-diagnosis-7koi50`
**Touches:** `scripts/derive_campd_outages.py` (`filter_revealed_outages`,
`FULL_STOP_OVERRIDE_DAYS/CF`), `scripts/derive_campd_unit_outages.py` (shares the
filter), `scripts/probes/_outage_gate_audit.py` (the STEP-1 audit), and the
regenerated `data/raw/campd-{,unit-}outages*.csv` for all six ISOs.

## The question

After the **local-band** net-load filter (commit `152bb99`,
`docs/ercot-outage-sensitivity-middle-ground-2026-06.md`) was rolled out to every
ISO keeper, the remaining thermal over-run: is it **still outage-gate looseness**
(true long MECHANICAL outages dropped as "economic idle" because they sit in
low-net-load windows), or is it **price-formation / fuel-cost** the outage input
cannot fix? Diagnosed per ISO, no assumption.

## STEP 1 — the audit (`scripts/probes/_outage_gate_audit.py`, no solve)

The audit replicates the unit-level detector exactly but, instead of writing the
filtered CSV, emits one row per **pre-filter** detected down-span tagged KEPT vs
DROPPED by the current local-band filter and characterised by duration, span
mean-CF (full STOP vs partial low-CF backdown), high-load overlap (the filter's
own statistic), and the annual net-load percentile band the span sits in. Keyed
only on exogenous CAMPD operation + EIA-930 net load — no LMP, no price target.

### Headline (2023–2025, dispatchable thermal = coal + CC + gas-steam)

Capacity-weighted GW-days, per ISO, with the **dropped long (≥14 d) full-stop**
layer — the mechanical-outage signature the local band still drops:

| ISO   | detected GWd | KEPT % | DROPPED % | dropped long-full-stop GWd | % of detected | character of the dropped layer |
|-------|-------------:|-------:|----------:|---------------------------:|--------------:|--------------------------------|
| PJM   | 36,435 | 85% | 15% | **988** (161 spans) | 2.7% | real baseload coal (Gavin, J E Amos, Conemaugh, Mountaineer, Rockport) + Talen gas-steam (Montour, Martins Creek) |
| MISO  | 27,022 | 88% | 12% | **322** (48 spans) | 1.2% | real baseload coal (Gibson, Monroe, Labadie, Big Cajun, Independence) |
| ERCOT | 15,891 | 84% | 16% | **203** (55 spans) | 1.3% | mostly old gas-steam (O W Sommers, V H Braunig, Handley, Lake Hubbard) + some CC |
| NYISO | 11,138 | 89% | 11% | **180** (42 spans) | 1.6% | old gas/oil steam + CC (Roseton, Northport, Bowline, Arthur Kill, Athens) |
| NEISO |  6,229 | 88% | 12% | **39** (15 spans) | 0.6% | tiny (Merrimack, Rumford, Westbrook) |
| CAISO |  5,852 | 84% | 16% | **5** (4 spans) | 0.1% | negligible |

### Two findings that frame everything

1. **The local band already fixed the gross looseness.** The very-long mechanical
   outages that *motivated* the local band (the T H Wharton 96-d / Gregory 90-d
   class) are now **kept**: pooled across all six ISOs the dropped full-stop mass
   at ≥28 d is **0 GWd**, at ≥21 d only **106 GWd**. Nothing weeks-long is being
   dropped anymore.

2. **A thin residual layer remains, and it is real.** What the local band still
   drops are **14–20 day continuous FULL STOPS** (span mean-CF ≈ 0.000) sitting
   **just below the 24-hour high-load-overlap gate** — pooled median overlap
   ~17 h, 75th-pct ~21 h (so 12–23 of the required 24). 119 of 161 PJM spans
   (740 GWd) overlap 12–23 high-load hours. A baseload coal unit does not
   economically idle *fully off* for two-to-three continuous weeks — it cycles or
   returns the moment any local peak hits — so a sustained weeks-long dead stop
   is the mechanical-outage signature regardless of net-load overlap. At ≥14 d
   the dropped spans are **98% full stops by GW-days** (1737 GWd full-stop vs only
   41 GWd partial backdown pooled), i.e. duration alone already isolates dead
   stops; depth only adds robustness.

### Per-ISO answer to QUESTION 1

- **CAISO — gate is CORRECT; residual is price-side. NEGATIVE deliverable, STOP.**
  5 GWd / 4 spans (0.1%) of dropped long full-stops — the gate keeps essentially
  every real outage. CAISO's documented body/midday **commitment** overprice is
  orthogonal to outages (see `caiso 19`). The override is a ~no-op (+4 windows).
- **NEISO — gate effectively correct; residual is price-side.** 39 GWd / 15 spans
  (0.6%), all small units; the keeper (`neiso 24`) is already a near-no-op on
  outages. Negligible.
- **ERCOT — gate ~correct; the thin dropped layer is mostly old gas-steam.** 203
  GWd, dominated by 1960s–70s gas steamers (Sommers, Braunig, Handley) whose
  weeks-long dead stops are plausibly seasonal lay-up as much as mechanical, plus
  a few real CC. Modest; the dominant ERCOT residual remains price-formation /
  scarcity (run145 RTORDPA lineage).
- **NYISO — thin REAL looseness.** 180 GWd in old NYC/Hudson-Valley steamers and
  CC (Roseton/Northport at the 70–90th net-load percentile with overlap 20–22,
  just shy of 24 → real outages dropped at the gate margin). Override helps
  modestly; the bulk residual is still the documented winter-RCPF / commitment
  class.
- **MISO — REAL dropped baseload coal, but NO keeper.** 322 GWd of Gibson/Monroe/
  Labadie-class coal full stops dropped, several at the 70–90th percentile. The
  override improves the **forward input**; there is no keeper to re-gate.
- **PJM — the largest real dropped layer (988 GWd), but the dominant residual is
  PRICE-SIDE.** Real baseload coal (Gavin/Amos/Conemaugh) + Talen gas-steam. This
  is ~2.7% of detected GW-days; the prior decomposition
  (`pjm-coal-overrun-decomp-2026-06.md`) showed the +11–22% coal over-run is
  ~92–94% take-or-pay BASE tranche, export-driven, and downstream of PJM's own
  ~$8–10-low LMP (a gas-marginal / missing-afternoon-scarcity price-formation
  problem). The override attacks the *base-coal availability* directly, so it is
  expected to help PJM more than any other ISO — but it cannot, by mass, close a
  base/export/price-driven over-run on its own.

**Bottom line:** the local band did the heavy lifting; the gate is now *mostly
correct everywhere*. A thin layer of genuinely mechanical 14–20 d full stops
remains dropped at the 24-h overlap margin (largest in PJM/MISO, real in NYISO,
mostly gas-steam in ERCOT, ~zero in CAISO/NEISO). Recovering it is the
structurally-correct thing to do (claude.md #11/#12 — keep real measured
outages), **but it is not the dominant driver of the remaining residual**, which
is price-formation. This is the sanctioned partial result: fix the outage-side
layer, hand the rest to price formation.

## STEP 2 — the shared full-stop duration+depth override

One filter for all ISOs (`filter_revealed_outages` in
`scripts/derive_campd_outages.py`, shared by the facility- and unit-level
detectors). A detected down span is kept if EITHER:

- it overlaps ≥ `MIN_INMERIT_HOURS` (24) high-NET-LOAD hours (the existing
  local-band revealed-availability test), **OR**
- it is a **sustained full stop** — span mean-CF < `FULL_STOP_OVERRIDE_CF`
  (0.02) — lasting ≥ `FULL_STOP_OVERRIDE_DAYS` (**14**) continuous days.

Keyed only on measured CAMPD operation (CF) + EIA-930 net load (the mask) — no
LMP / price / MWh-residual (claude.md #11). **No per-ISO constants** — one shared
N/depth for every ISO.

**Why N = 14, depth 0.02** (tuned on the STEP-1 audit pooled across ISOs, not on
any residual): at ≥14 d the dropped layer is 98% full stops (1737 vs 41 GWd
partial), while the offered alternatives recover almost nothing the local band
does not already keep (≥21 d → 106 GWd, ≥28 d → 0). The override and the local
band are **disjoint by construction** — economic idle returns for local peaks so
it is never a 14-day *continuous* dead stop — so the override does **not** undo
the local band's economic-idle cut.

### Recovery on regeneration (windows added vs the local-band-only files)

ERCOT +55 unit / +12 facility · PJM +166 unit / +46 facility · MISO +266 ·
NYISO +41 · NEISO +39 · **CAISO +4** (confirming its gate was already correct).
All recovered spans are measured weeks-long dead stops.

## STEP 3 — re-gate (in progress)

Per the coordinated cross-ISO rule, every keeper that consumes the shared CSVs is
re-solved byte-faithfully (only the outage input changes) and gated before the
override is promoted. **PJM** (largest layer + best-documented residual) is the
decisive test and is being re-solved first (`pjm_41`, the `pjm_40` coal-fidelity
config verbatim). CAISO/NEISO re-solves are no-ops by mass (gate already correct);
ERCOT/NYISO are modest. MISO has no keeper. Results and gate verdicts appended
below on completion.

## Reproduce

```bash
# STEP-1 audit (no solve)
python scripts/probes/_outage_gate_audit.py --all --years 2023 2024 2025

# regenerate every ISO on the override (auto picked up by the solve)
python scripts/derive_campd_outages.py      --iso ERCOT --years 2023 2024 2025
python scripts/derive_campd_outages.py      --iso PJM   --years 2023 2024 2025
for iso in ERCOT PJM CAISO NEISO NYISO MISO; do
  python scripts/derive_campd_unit_outages.py --iso $iso --years 2023 2024 2025
done
# A/B without the override: add  --no-fullstop-override
```

---

**[Archival note — 2026-07-11, docs reorg]** STEP 3's re-gate results were never
appended here. What actually landed:

- The shared full-stop override shipped in `scripts/derive_campd_outages.py`
  (`FULL_STOP_OVERRIDE_DAYS` / `FULL_STOP_OVERRIDE_CF`, shared by the facility- and
  unit-level detectors); the 14-day knee described in STEP 2 was subsequently
  re-tuned to **5 days** (`FULL_STOP_OVERRIDE_DAYS = 5`; see
  `scripts/gen_pjm90_attestation.py`: "FULL_STOP_OVERRIDE_DAYS 14->5, measured
  CAMPD"). The outage CSVs for all six ISOs were regenerated
  (`data/raw/campd-outages*.csv`, `data/raw/campd-unit-outages-*.csv`).
- The decisive PJM re-solve `pjm_41` was produced (`results/calibration/pjm_41`);
  the outage-side fix was carried forward into the then-current PJM keeper
  **`2026-07-03-pjm-76-outage-fix`** (named for exactly this workstream).
- No standalone dated `docs/calibration-log.md` entry for the 2026-06-22 re-gate
  itself was located at archival — the outcome was absorbed into the PJM keeper
  lineage rather than logged as a discrete entry.
