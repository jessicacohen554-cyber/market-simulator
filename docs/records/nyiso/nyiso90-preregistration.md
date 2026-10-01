# nyiso-90 pre-registration — CT_PEAKER block-commitment arm

Written **before** deriving the CT class row or running any arm, so the
parameter choice provably cannot have been made by looking at what it does
(rule 24 [R-FROZEN-DERIVE], rule 13 [R-MEASURED]).

## 1. The mechanism (pre-registered)

Give the NYISO `CT_PEAKER` class a **minimum run duration** in the existing
P1-native gas commitment bridge (`nyiso_gas_commitment_bridge`), via the
`min_run_hours` extension leg already shipped by nyiso-87.

**This does NOT widen the fast-start physics gate.** In
`model/commitment.py::caiso_ra_mustoffer_min_gen`, a unit with min-down 1 h:

* can never trip the *physical* bridge (`gap < min_down` is unreachable when
  `min_down = 1` and `gap >= 1`);
* is blocked from the *economic* bridge by
  `RA_BRIDGE_ECON_MIN_DOWN_HOURS = 4.0`, which stays at 4.0 and is not touched.

So the **only** leg that can fire on a CT is the `min_run_hours` extension.
nyiso-87's reasoning ("a fast-start CT restarts within the hour, so it is never
*held across a gap*") is preserved exactly. The two properties are physically
distinct: minimum-**down** governs how fast a unit can come back; minimum-**run**
governs how long a started unit must stay on. A 10-minute-start GT can carry a
multi-hour minimum run (permit/warranty/DAM block granularity) — the NREL class
table already assigns `min_run_hours` independently of `min_down_hours` for
every other fuel.

## 2. The parameter (pre-registered, before the value is known)

`min_run_hours(CT_PEAKER) = run_hours_p25_capwtd`, from the frozen measured
artifact `campd_gas_commitment_params_NYISO.csv` extended to the CT class.
`min_load_frac(CT_PEAKER) = min_load_frac` (cap-weighted p50) from the same row,
the same statistic the CC and ST_GAS legs already use.

Reasons, all identification, none residual:

1. **A low order statistic is the correct estimator.** Every observed run is
   `>= the constraint`, so the observed distribution bounds the constraint from
   ABOVE. The artifact's own docstring says this: "a unit that ran 60 h because
   it was economic does not prove a 60 h commitment floor — so the low
   percentiles (p10/p25) bound the constraint from the side the constraint lives
   on." p50 is known to overstate.
2. **Capacity-weighted**, per the artifact's own "identification column"
   argument: a min-run constraint floors committed MW, not committed unit-count,
   and it matches `min_load_frac`'s weighting.
3. **p25 rather than p10**, fixed in advance: runs are computed WITHIN a year,
   so every run spanning a year boundary is split into two spurious short runs.
   p10 of a discrete hour-valued distribution absorbs that truncation artifact
   (the committed ST_GAS row shows p10 = 1 h); p25 is the standard robust lower
   quartile and the tightest estimator that is not dominated by it.

**Known inconsistency, deliberately not folded in.** The keeper's CC and ST_GAS
legs use `run_hours_p50_capwtd` (21 h / 13 h). This arm uses p25 for CT on the
reasoning above. Reconciling the two conventions would change the keeper's CC
and ST_GAS floors — a second delta, and a keeper regression risk — so it is a
named follow-up, not part of this arm.

## 3. Success criterion (pre-registered)

Judged against the **measured run-length distribution**, not the volume gap
(`campd_ct_run_lengths_NYISO.csv`: median 4 h, mean 6.5-7.6 h, p90 14 h; class
fallback row median 4.0 / mean 6.85). The arm SUCCEEDS if the model's CT_PEAKER
per-unit run-length distribution moves materially toward the measured one, even
if the TWh level still misses. It FAILS if the distribution does not move.

## 4. Gates to re-score and report on the arm, whatever they do

* **C1 fuel-mix** — 2023 CC_REGULAR is the load-bearing cell, -2.784 TWh of a
  +/-2.94 band (0.156 TWh headroom). Any CC_REGULAR displacement is reported.
* **C5a CO2** — 2025 is +7.62 % of a +/-10 % band. Peaker volume enters at
  10-16 MMBtu/MWh; the sign is measured, not assumed.
* **C8 forced-share budget** — CT_PEAKER is a peaker class (>15 % cap) and
  currently carries 0.0 % forced share. A min-run floor puts it on the board,
  so it needs a cited `D4_WINDOWS` entry.
