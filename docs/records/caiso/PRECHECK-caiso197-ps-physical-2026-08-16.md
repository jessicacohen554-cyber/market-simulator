# PRECHECK — caiso-197 (lane 5): per-plant cited-physical PS parameterization — six plants, one bundled arm — parameter table FROZEN before any lane-5 solve

**Committed and pushed before the lane-5 arm solves.** Gate spec applied as
written: `GATESPEC-caiso195-ps-physical-2026-08-11.md` (authored by caiso-191
BEFORE any lane-5 measurement; owner ruling 7 **GO WITH SCOPE RESTRICTIONS**,
adjudicated `FINDING-caiso191-campaign-adjudication-2026-08-11.md` §3 — the
restrictions ARE the grant's conditions and are embedded below). Executed on
the re-anchored caiso-196 campaign base (FINDING-caiso196 §7), sharing the
campaign control `caiso197_l2_control` (BIT-ZERO vs the committed keeper,
noise floor 0.0 — `_caiso197_ctrl_tolerance.json`), disclosed here and in the
lane-2/3 FINDINGs.

## 0. Direction-hazard regime (verbatim from the GATESPEC, binding)

> The expected sign of this repair flatters C3a. C3a movement is therefore
> inadmissible as evidence for or against acceptance (rules 1, 13, 14). Acceptance is
> decided solely on the structural gates pre-registered below, authored by caiso-191
> before measurement. C3a is reported for transparency only. If gates pass and C3a
> worsens, the arm is still accepted (caiso-183 precedent). If gates fail and C3a
> improves, the arm is still rejected.

Every ambiguity below resolved toward MORE pumping capability (GATESPEC §4 —
against the flattering direction), each resolution stated in place. No price
series was read anywhere in the derivation (the probe reads EIA-860, the two
committed public-document corpora, and the loader's own fleet build — no LP).

## 1. What the arm IS (GATESPEC §1, restated)

The model runs CAISO's 2,077.6 MW PS fleet as ONE aggregate NP15
`StorageUnit` with fleet-average duration/RTE. This arm replaces the
aggregate with per-plant parameterizations for Helms, Eastwood, Gianelli,
Hyatt, Thermalito, O'Neill — **one bundled arm** (rule 19), **zero MW added**
(G-AGG measured EXACT: armed Σ power = off Σ power = 2,077.6 MW — the
aggregate's own EIA-860 rows re-attributed;
`_caiso197_ps_citations.json::g_agg`). Hyatt STAYS IN the storage block; its
mode enters ONLY as static cited parameter bounds (pump-side motor rating +
pump-back-cycle energy bound); NO energy re-allocation into conventional
hydro, NO time-profile input of any kind (G-NOSHAPE structural — the
caiso-141 §G wall untouched; owner ruling 4).

## 2. THE FROZEN PARAMETER TABLE (G-CITE; committed in
`config/constants.py::CAISO_PS_PLANT_PARAMS` with citation comments, verified
value-by-value by `scripts/probes/_caiso197_ps_citations.py`)

| plant (EIA code) | power_cap (EIA-860 np, UNCHANGED basis) | pump cap (cited) | energy bound (cited) |
|---|---|---|---|
| Helms (6100) | 1,053.0 MW | **930.0 MW** — PG&E's own deck, verbatim "1,212 MW total in generation mode, and 930 MW total in pump mode" | **200,424 MWh** = Courtright gross 123,000 AF × 1,212 MW / 9,000 cfs |
| Edward C Hyatt (437) | 293.1 MW (the 3 p-g units) | **387.0 MW** = 519,000 hp × 745.7 W/hp (DWR B132-22 p.9) — ABOVE the EIA-860 PS-unit rating, so the tighten-only channel clips it to 293.1: a DISCLOSED NO-OP (Hyatt keeps full PS pump treatment, §4.2's conservative default satisfied with an airtight citation) | **31,678 MWh** = pump-back cycle store (Thermalito Forebay 11,800 + Afterbay 57,000 AF, B132-22 Table 1-1) × 645 MW / 16,950 cfs (Table 1-4) |
| Robie Thermalito (438) | 82.5 MW | **89.5 MW** = 120,000 hp (clips to 82.5 — disclosed no-op) | **4,519 MWh** = Afterbay 57,000 AF × 114 MW / 17,400 cfs |
| W R Gianelli (448) | 424.0 MW | **375.8 MW** = 504,000 hp (BINDS: −48.2 MW pump vs incumbent) | **613,410 MWh** = San Luis gross 2,027,800 AF × 424 MW / 16,960 cfs (DWR share 1,062,183 AF recorded; gross used per §4.1) |
| O'Neill (446) | 25.2 MW | **26.8 MW** = 6 × 6,000 hp (USBR EWA EIS Ch.16; clips to 25.2 — disclosed no-op) | **4,095 MWh** = O'Neill Forebay 56,400 AF × 25.2 MW / 4,200 cfs |
| J S Eastwood (104) | 199.8 MW | **UNCITED → None**: no public pump-mode rating found (FERC P-67 narratives give 199.8 MW / 1,338 ft head / PS function only — USBR Upper San Joaquin Hydropower TA p.2-16). The component keeps the UNRESTRAINED default (charge cap = power cap) — §4.1's more-pumping direction for an uncited parameter | **UNCITED → incumbent default** (10 h × 199.8 = 1,998 MWh): Balsam Meadow forebay volume not found in a public document. The GATESPEC kill rule's "that component out" reading: the plant still splits out (G-AGG/zone accounting whole) but its uncited parameters stay INCUMBENT — nothing invented |

Source corpora committed with provenance READMEs (URL, retrieval record,
quoted rows): `data/raw/reference/pge-helms-ps-plant-2008/` (the owner's own
public deck, sha256 39b009ad…) and `data/raw/reference/dwr-b132-22-swp-plants/`
(three row-exact table extracts from DWR Bulletin 132-22 Ch.1). O'Neill's
unit specs: USBR EWA Draft EIS/EIR (July 2003) Ch.16 §16.2.7.1.1
(usbr.gov/mp/ewa/docs/DraftEIS-Vol2/Ch16.pdf, citing Reclamation 2001).
Conversion constants are fixed physics (1 hp = 745.6999 W; 1 cfs·h =
0.0826446 AF). **No value from any model output; any post-PRECHECK value
change voids the session.**

Ambiguity resolutions, each stated (GATESPEC §4): gross reservoir volumes
over usable/share volumes (more capability); Forebay+Afterbay over
Afterbay-alone for Hyatt's cycle store (more capability); uncited Eastwood
parameters → unrestrained/incumbent defaults (more capability); the three
motor ratings above the EIA-860 PS nameplate clip DOWN only through the
channel's pre-existing tighten-only invariant (never a loosening, disclosed).

## 3. The build (registered surface — rule 24/28c, all in this PR)

* `ScenarioConfig.caiso_ps_plant_params: bool = False` (default off,
  byte-identical — registered in `_CACHE_KEY_OPTIONAL_FIELDS` +
  `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`; pinned default key unmoved, checked
  by `check_cache_key_registration.py` and the persisted-identity pins).
* `constants.CAISO_PS_PLANT_PARAMS` — the cited table (no dict in a `data/`
  module, no env knob).
* `StorageUnit.charge_power_cap_mw` (additive, None = legacy) +
  `model/storage.py::caiso_ps_charge_caps` — the cited pump ratings enter as
  STATIC per-unit charge caps on the EXISTING `storage_charge_cap` LP
  channel (tighten-only vs power cap), composing with the battery shape
  anchor on DISJOINT unit rows (one channel, one bound per unit — rule 19).
  The leg fires with or without the anchor (never silently dependent on
  another gate — the caiso-98 dead-flag lesson).
* `load_eia860_pumped_storage` armed branch: per-plant units; power_cap =
  each plant's own EIA-860 nameplate rows exactly as the aggregate
  accumulated them; zones = `build_zone_lookup` geography (G-ZONE: **all six
  resolve NP15** — the zone axis is mechanically unchanged; no zone chosen
  by this lane; recorded in `_caiso197_ps_citations.json`).
* Matrix row `caiso_ps_plant_params` added to the base file + a cell line in
  every ISO shard in this same PR (28c); CAISO cell `U` until the arm
  adjudicates; other ISOs `.` (rule 25).
* Tests: `tests/unit/model/test_storage.py::TestCaisoPsPlantParams` (off-state
  legacy identity; armed split conserves the aggregate exactly; cited
  values on the right units; other ISOs ignore the flag; tighten-only
  composition). `PUMPED_STORAGE_DURATION_HOURS`/`PUMPED_STORAGE_RTE`
  byte-untouched for every other ISO (rule 25); RTE stays the fleet constant
  for all six plants (per-plant RTE is NOT in the GATESPEC's parameter list).

## 4. Gates (GATESPEC §3, status at PRECHECK time)

| gate | status |
|---|---|
| **G-CITE** | §2 table frozen, every cited value reproduced from committed public corpora by the probe (`constants_match_citations: true`); uncited components take defaults, never invented values |
| **G-ZONE** | Mechanical: `build_zone_lookup` output recorded, all six NP15 — no economic argument anywhere |
| **G-NOSHAPE** | Structural: the diff contains static bounds only — no hourly water state, no monthly-to-hourly allocation, no assumed schedule, no SOC trajectory input; Hyatt in-block |
| **G-AGG** | **MEASURED EXACT**: armed Σ 2,077.6 MW = off Σ 2,077.6 MW (zero MW added), per-month conservation by construction (same EIA-860 rows, same masks) |
| **G-DOF** | Every parameter enters identified `measured` (cited); zero fitted scalars; ledger must not increase on the built bundles (verified at FINDING time; the two uncited Eastwood defaults are the INCUMBENT constants, not new parameters) |
| **G-ENGAGE** | Fleet half measured (6 armed units built, cited bounds on the right units); LP half on the A/B: the arm must differ from control — a bit-identical arm is INERT, reported as such |

## 5. Kill criteria (GATESPEC §5, inherited whole)

* Any parameter uncited at PRECHECK time ⇒ that component out (Eastwood's
  pump/duration are OUT exactly this way — incumbent defaults, disclosed).
  Core plants (Helms/Eastwood) uncitable ⇒ arm dead: **not triggered** —
  Helms is fully cited; Eastwood's identity/capacity/zone are cited (EIA-860,
  USBR) and only its pump/duration take defaults.
* Any shape/profile input in the diff ⇒ session void (caiso-141; rule 13).
* Any zone assignment argued on anything but geography ⇒ fail.
* DOF increase or any fitted scalar ⇒ automatic fail.
* Acceptance may not cite C3a in either direction (§0).

## 6. A/B protocol (GATESPEC §6)

* **CONTROL** — `caiso197_l2_control` (shared campaign control on the
  re-anchored base; BIT-ZERO vs the committed keeper, noise floor 0.0 quoted
  before any treated delta; seam caps 16055/16452/16148 log-verified;
  `hydro_ror_split` explicitly False, disclosed).
* **ARM** (`results/calibration/caiso197_l5_psphys`) — control + ONE bundled
  mechanism:
  `python scripts/replay_keeper.py results/calibration/caiso196_e1_elsegundo
  --out-dir results/calibration/caiso197_l5_psphys --set hydro_ror_split=false
  --set caiso_ps_plant_params=true`
  The lane-2/lane-3 fields stay at their CONTROL values (one mechanism per
  arm; composition is Wave 2's job under the integration protocol).
* Rule 16: 2023+2024+2025 in one bundle; years sequential, arms sequential
  (rule 12); registered (rule 15) with `legitimacy_diagnostics.json`.
* Single-mechanism statement, required verbatim in the FINDING: "The A/B
  delta is the six-plant cited-physical PS parameterization; no other input
  differs."

## 7. Required artifacts

* This PRECHECK + `_caiso197_ps_citations.json` + the probe + the two source
  corpora (all committed before the lane-5 solve).
* Bundle `caiso197_l5_psphys` (control shared).
* `results/calibration/FINDING-caiso197-ps-physical-2026-08-16.md` — gate
  tally, §0 quoted verbatim, the caiso-140/141 fence discharge restated,
  matrix duties (b)+(c) (the row landed with the build; the CAISO cell moves
  on this arm's verdict), calibration-log entry in-session.
