# CHARTER — MISO committed-CC EcoMin as price-taker while online (owner ruling, miso-285, 2026-09-29)

**Ruling:** *"Charter EcoMin price-taker build"* on the miso-285 card. Evidence:
`docs/FINDING-miso285-night-overshoot-phase0-2026-09-29.md`.

## 1. The object and the market structure

- **Object:** the MISO night price sits +$4–10/MWh (median) above ILLINOIS.HUB at h0–5, in all seven years,
  while night MW by class match CAMPD. The base (P0) offer stack reproduces it.
- **Structure (rule 1):** a committed, non-fast-start MISO unit's EcoMin energy is must-take while it is
  synchronized. Its cost sits in no-load / make-whole, not in the incremental energy curve that sets LMP
  (ELMP extends commitment-cost pricing only to fast-start resources). The LP instead offers the CC committed
  band as economic energy at 1.005 × phys, so that block can set the night price.

## 2. What to build (reuse, do not invent)

- Reuse the ISO-neutral detector `model/commitment.py::caiso_ra_mustoffer_min_gen` with **only the
  online-hours leg** (`floor_online_hours=True`, ercot141): in every hour of a **P0-detected** run, floor the
  unit at `min_load_frac × pmax × availability`. **No gap-bridge legs**: the miso-130 §5 census shows the MISO
  day-anchored night-off pool is ~empty, and this charter is not that object.
- **New MISO-exclusive field** (rule 25), default off, e.g. `miso_gas_ecomin_online_floor`, wired at the P0→P1
  seam like `build_spp_gas_bridge_p1_prep` / `build_nyiso_gas_bridge_p1_prep`. It needs:
  - its D-2 mechanism id in `data/floor_mechanisms.py`;
  - a `D4_WINDOWS` entry;
  - the cache-key default registration;
  - the CLI flag;
  - a matrix base row + a `·` / `U` line in every ISO shard (rule 28(c));
  - tests: trivial 1-gen / 24-h first.
- **Eligibility by physics (rule 18):** merchant gas_cc units with min-down ≥ 4 h (the CC table), i.e.
  CC_REGULAR / CC_INTERMEDIATE in practice. **Excluded (rule 19):** CC_CHP / CT_CHP / ST_CHP (their own host
  must-run) and ST_GAS (p25 / OOM floors). Enumerate every existing floor on the eligible units (D-2
  attribution) before arming; there should be none on CC_REGULAR at night (the keeper's night bands for
  CC_REGULAR are committed + econ only, no mustrun).
- **`min_load_frac`:** MEASURED, never fitted. Run `scripts/data/derive_campd_gas_commitment_params.py --iso MISO`
  (the ISO-generic WP-3 loading-when-on construction, frozen per rule 23). Cite the output. Use the basis the
  detector's denominator is on (see the script header's CAISO basis note).
- **Rule 17 window:** the P0 run itself (the unit is online by the model's own economic pattern). **Driver:**
  commitment non-convexity. **Forward story:** P0 regenerates the pattern in any year. **Rule 13:** no measured
  output enters; only the measured LSL fraction.

## 3. Pre-registered zero-LP pre-check (BEFORE any shard)

Size the arm on the keeper stack with `scripts/probes/_miso285_night_stack.py` extended by a CF that floors
only the eligible units, at the measured `min_load_frac`, in hours the keeper's P1 class dispatch shows them
online. The CF1 upper bound is −$0.6 / −1.0 / −1.9 / −6.3 / −1.1 / −0.6 / −0.6 (2019–2025).

**Kill rule, fixed now:** if the pre-check moves the night median by less than **$0.5 in ≥ 4 of 7 years**, STOP.
Record the result, set the new row **I** and `diurnal_price_amplitude` back to **G**, and ask the owner.
Spend no shards.

## 4. If the pre-check clears: PRECOMMIT and solve

- PRECOMMIT with G-DRIFT against the keeper leg pin `8f765fef0ed79c89687b6bf686cb65f611a9fea4` (rule 29(b)).
- Pin a full SHA. Run one shard per year 2019–2025 (rules 34(c), 36), using the miso-280 template
  (`docs/PRECOMMIT-miso280-split-remap-2026-09-28.md` §7/§8).
- **Pre-registered gates** (stated before solving; none selects a value):
  1. Night (h0–5) median model − ILLINOIS.HUB RT falls in ≥ 5 of 7 years.
  2. No C1 status flips PASS → FAIL (COAL_* and CC_REGULAR especially). Night coal falling below CAMPD is the
     measured risk.
  3. C8 / rule 20: CC_REGULAR forced share at binding floors ≤ 30 %, or a grounded pass via D-4 window + D-1
     shape.
  4. No new protective caveat; the train-tier determination does not downgrade.
- Rule 1: a structurally-correct result stays a candidate even if C3a moves the wrong way. Report at full
  magnitude and ask the owner with a card.
