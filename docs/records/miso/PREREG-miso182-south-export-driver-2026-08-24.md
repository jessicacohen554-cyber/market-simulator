# PREREG miso-182 — the D-3 South under-export evidence session: the firm/contract export-block driver hunt

**Session miso-182 (2026-08-24).** Registered **BEFORE any adjudicating
quantity is computed.** Executes miso-178 §7 lever 3 / §10 D-3, the queue head
after miso-181 closed D-2
(`FINDING-miso181-seam-response-refutation-2026-08-24.md` §6).

**EVIDENCE ONLY. NO LP will be solved, no `ScenarioConfig` field created,
nothing armed, no run registered** (rule 15 `[R-DASHBOARD]` not engaged; the
miso-142/…/174/176/178/181 no-LP precedent). Keeper
`2026-08-22-miso-177-rho-measured` (`miso177_rho_B`) UNCHANGED. Determination
unchanged: **NOT-YET on C3a-2025 alone**, C3c the single ledgered caveat.

## 0. What has already been looked at, and what has not

Declared for honesty about the pre-registration boundary. Before writing this
document the session read only: committed prior findings (miso-174/178/181),
the `MISO_SEAM_DIBA` / `MISO_MANITOBA_*` config, the miso-174 probe source, the
committed `_miso174_seam_overimport_decomposition.json` **aggregate and
per-seam** numbers (prior-session committed facts, cited as such), the EIA-930
DIBA **coverage counts** (rows per DIBA per year), and the schema of the zonal
LMP series. **No statistic in §2 has been computed for any counterparty, and no
gate in §3 has been evaluated.**

## 1. The object (committed; restated, not re-derived)

miso-174 §1, on the then-keeper, decomposed MISO's scarce-hour interchange gap
by seam. The **South** row (`MISO_SEAM_DIBA["South"]` =
SOCO, TVA, AECI, LGEE, SIKE):

| year | South gap (model net import − measured net import) |
|---|---:|
| 2023 | **+0.63 GW** |
| 2024 | **+0.35 GW** |
| 2025 | **+1.19 GW** — the largest single 2025 seam component |

The model's South **gross import is ≈0**, so this is an **export** gap: the
model under-exports the South seam. No import-side lever can reach it
(miso-174 §1). miso-178 §2 adds the price face: the model over-prices
MISO-South **+18.8 / +21.0 / +17.0 %** in all three years, and in 2025 the real
market ran a South **discount** (actual South 37.31, the cheapest zone) while
the model prices South at a premium.

Two adjudicated data bound the approach: the dipole does **not** resolve through
the offer stack (miso-180 — South moved AWAY from zero under a steepened Midwest
top), and **not** through the PJM-seam import side in any admissible envelope
form (miso-181).

**The admissible shape on the table is the MANITOBA PRECEDENT** — the one seam
form the model demonstrably reproduces (miso-174 §3b). Its committed form is an
**annual-flat, per-year MW block**:
`MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR = {2023: 726.0, 2024: 531.0, 2025: 224.0}`
(`model/interchange/spec.py`), grounded in firm hydro contract service — never
spread arbitrage, never a residual fit.

## 2. The instrument (frozen construction)

One read-only probe, `scripts/probes/_miso182_south_export_driver.py` →
`results/calibration/_miso182_south_export_driver.json`. Every quantity is a
measurement of committed artifacts against measured actuals.

**Hour key (frozen, no re-solve).** The keeper's **−1 h** DIBA key, already
solved and committed at miso-174 §4 / miso-175 (r = 1.0000 in 2023,
0.999998 in 2025, 0.8286 in 2024 — the disclosed EIA-930 internal
inconsistency), on the model's fixed **non-leap 8760 CST** clock. Sign
convention: **EIA-930 `mw` is + when MISO EXPORTS**; the probe reports
**net export = +`mw`** for the South seam (its dominant direction) and states
the sign on every table. No hour-key search is performed or permitted.

**Hour sets (frozen, the miso-174/178 sets).** `annual` (8760);
`summer` = Jun 1 – Sep 30; `scarce` = summer ∩ MISO RT > $200/MWh
(n = 11 / 14 / 47); reported-only: `da_foreseen` (DA > $150) and
`top47_load`.

**Per-counterparty signature (S-1 … S-6),** computed for each South DIBA and,
as the two **anchors**, for **MHEB** (Manitoba — the precedent the model
reproduces) and **PJM** (the arbitrage-like seam the model fails):

| id | statistic |
|---|---|
| S-1 | level: annual and summer mean net flow (MW) in the seam's own dominant direction |
| S-2 | seasonality: 12 monthly means; month-to-month coefficient of variation |
| S-3 | stress response: mean flow in `scarce` minus mean flow in `summer` (GW, signed) |
| S-4 | volatility: mean \|Δ/h\| (MW), and \|Δ/h\| ÷ mean level |
| S-5 | price sensitivity: Pearson r of hourly flow vs MISO-South zonal RT (and vs MISO system RT), summer |
| S-6 | blockiness: share of hours within ±25 MW of the counterparty's modal 100-MW level; count of distinct 100-MW levels covering 80 % of hours |

SOCO / TVA / AECI / LGEE carry full coverage (8,760 / 8,757 / 8,760 rows).
**SIKE carries 24 rows in 2025 and none in 2023–2024** — it is reported as
absent and excluded from every gate; disclosed, not silently dropped.

**Model side.** The per-seam model split lives only in the **pruned**
`miso169_gated_A` `unit_hourly` bundle (miso-181 §5). It is therefore **cited
from the committed `_miso174_seam_overimport_decomposition.json` record**, with
its measured vintage drift disclosed on every model-side number, exactly as
miso-174 disclosed it. **No model-side quantity is re-derived**, and none is
load-bearing for §3's gates beyond the committed per-year gap of §1.

## 3. The declared gates

### K-1 — THE FORM TEST (load-bearing, against interest)

Tests **the actual mechanism on the table**, not an abstraction: the
Manitoba-precedent **annual-flat, per-year firm export block**.

Construction, frozen: for each year *y*, let `B_y` = the block that closes the
**annual** measured-vs-model South net-export gap (the Manitoba identification:
one number per year, no hourly shape, no window). Apply `B_y` uniformly to all
8,760 hours and recompute the residual gap on the **`scarce`** set.

> **K-1 FIRES (the flat-block form is REFUTED) iff applying `B_y` makes the
> scarce-set residual WORSE — `|residual_scarce| > |gap_scarce|` — in ≥ 2 of
> the 3 years.**

Rationale (rule 1 `[R-STRUCT]`): a block that closes the annual level while
degrading the hours the lane actually cares about is a level adder wearing a
contract's name — the same costume the miso-181 kill was frozen to catch. If
K-1 fires, **no mechanism is asked for regardless of what the driver hunt
finds**.

### G-1b — the signature (supporting, thresholds derived FROM the anchors)

For each dimension *d* of S-1…S-6, the discriminating threshold is the
**midpoint of the MHEB and PJM anchor values** — measured-derived, declared in
advance, **no free parameter and no threshold of my own invention**. A
counterparty *c* is "Manitoba-side" on *d* iff its statistic falls on the MHEB
side of that midpoint.

A dimension **counts** only if the two anchors separate by ≥ 25 % of the larger
absolute anchor value; otherwise it is reported **NON-DISCRIMINATING** and
excluded, with the denominator reduced (reported explicitly, never hidden).

> **G-1b PASSES for a counterparty iff it is Manitoba-side on ≥ 3 of the
> discriminating dimensions.** The seam-level read is taken over the
> counterparties carrying ≥ 20 % of measured South gross export.

G-1b is **supporting evidence, not load-bearing**: it cannot by itself
authorize a mechanism ask, and it cannot overturn K-1.

### G-2 — THE DRIVER LADDER (load-bearing, rule 13 `[R-MEASURED]`)

A forward-regenerable firm/contract export series must clear **all four**:

1. **Exists.** A published instrument records firm/contract export service from
   the MISO-South footprint to SOCO / TVA / AECI / LGEE — legacy Entergy-region
   unit-power-sale or JOU schedules, firm point-to-point / network transmission
   service, FERC EQR firm-sale filings, or attachment/operating agreements.
2. **Placeable at our grain** without inventing an apportionment — the standing
   miso-77 §5.2 / miso-176 K-2 objection, which refused the FFE cap for exactly
   this reason. A series that needs an invented split across model zones or
   counterparties FAILS.
3. **Forward-regenerable and condition-responsive** — rule 13's own test: could
   this same quantity be produced for a forward year from forward drivers, and
   would it respond to changed conditions?
4. **Free of measured-outcome content** — it must not be, or be derived from,
   the seam's own measured hourly flow (that is the rule-13 forbidden outcome
   pin, and `measured_interface_limits` is `R` besides, miso-174).

> **G-2 PASSES iff all four clear.** Any fail is an honest close.

## 4. Verdict mapping (frozen)

The candidate mechanism-in-kind is named here so the mapping is decidable:
**`miso_south_firm_export_block`** — an annual-flat, per-year firm export block
on the South seam, the Manitoba precedent's form.

| outcome | cell verdict | session deliverable |
|---|---|---|
| **K-1 fires** | `R` (form refuted on measured evidence) | honest close; defect stays disclosed, quotable as a defect only |
| K-1 clears, **G-2 fails** | `G` (data-refused) | honest close **with the re-open condition named** (the `m2m_seam_entitlement_cap` `G` precedent) |
| K-1 clears, **G-2 passes** | **no cell minted** | the **D-3 mechanism charter ask**, with the identified series and its rule-17 window / driver / forward story |

Per rule 26(b) a cell is minted **only** in the first two rows — a mechanism
that is merely *proposed* is untested and stays `U`. In every outcome the
matrix §5.4 queue stamp and the calibration-log entry land in **this** session.

## 5. Anti-sweep and DO-NOT-REDO

**Anti-sweep (binding).** The hour key, hour sets, statistic list, anchor pair,
midpoint-threshold rule, the ≥25 % discrimination floor, the ≥3-of-N and
≥2-of-3 lines, and the `B_y` identification are **frozen by this document**. No
alternative key, set, statistic, anchor, threshold or block form may be computed
after seeing a result, and none may be quoted from this session. A result that
lands against interest is reported at full magnitude.

**DO-NOT-REDO** (the miso-181 charter list, carried forward in full, PLUS its
two additions): `measured_interface_limits` `R`; `m2m_seam_entitlement_cap` `G`;
`import_shape_lever` `G`; `internal_congestion_split` `G`; `zonal_loss_surface`
`R`; within-unit `measured_offer_surface` `R`; `gas_hub_basis_overlay` `R`;
`ramp_envelopes` `I`; `dam_availability_rebasis` `R`; the ordc/reserve families;
the dispersion family; **`miso_seam_coincident_envelope` `R`** (no variant sweep
of its frozen grid / driver / statistic); and **the `miso_offer_spread_anchored`
graft's unspent re-open clause** — not touched by this session, and this session
may not be cited as graft evidence.

## 6. Governance

Rule 22 `[R-HOLDOUT]`: **2023 / 2024 / 2025 ONLY**; MISO holds **neither**
`complete` nor `final` (fail-closed); the holdout spend freeze is **ACTIVE** and
untouched; no marker re-key is owed. Rule 15 not engaged — no solve, no run to
register. Rule 26(b): matrix stamp + calibration-log entry in-session, per §4.
Rule 27 `[R-PUSH]`: exact on-disk bytes; blobs ≥ 300 lines verified after every
push. No new `.github/workflows`.
