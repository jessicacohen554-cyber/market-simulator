# FINDING — C1 candidate 3 (WP-B overnight CC two-shift): REFUTED by the who-serves-the-night precondition — the overnight CC over-run is an IMPORT-PRICING phenomenon, not a commitment one; the lane redirects to the import side (no build this session)

**Session 2026-07-17 (C1 CC-overnight lane, WP-B precondition). Basis: the
same-machine caiso-92 keeper repro (`results/calibration/caiso92_repro_A`,
via `scripts/probes/_caiso92_repro_A.py main`) vs full-8760 CAMPD CEMS
(`campd-facility-level/CA_{2023,2024,2025}.parquet`, model-klass_map basis with
the LA-Basin repowering crosswalk, non-CAISO CA plants excluded) and EIA-930
CISO wide-hourly (`eia-930-hourly/CISO hourly.parquet`). Decomposition harness:
`scripts/probes/_caiso_who_serves_night.py`. The precondition
FINDING-caiso91c §3 demanded before ANY WP-B build.**

## 1. The precondition the charter required: WHO SERVES THE NIGHT

FINDING-caiso91c chartered WP-B (a P1-native overnight two-shift screen to
de-commit the model's overnight CC over-run) but gated it on decomposing the
model-vs-measured overnight (hod 0-5) supply split — because disclosed
tension #1 was that removing overnight CC RAISES overnight λ (already +2..+4
over) unless the displaced 1.3–2.5 TWh/yr is served by cheaper overnight
IMPORTS. This session ran that decomposition.

## 2. The decomposition (overnight hod 0-5, TWh, 2023/2024/2025)

| source | MODEL | MEASURED | Δ (model − meas) |
|---|---|---|---|
| **CC_REGULAR** | 15.16 / 14.76 / 13.78 | 13.77 / 12.65 / 11.17 (CEMS) | **+1.39 / +2.11 / +2.61** |
| **imports** | 10.03 / 9.87 / 10.30 | 11.39 / 11.57 / 13.33 (−interchange) | **−1.36 / −1.70 / −3.03** |
| CC_CHP | 2.34 / 2.04 / 1.99 | 1.89 / 1.51 / 1.59 (CEMS) | +0.45 / +0.53 / +0.40 |
| CT_PEAKER | 0.09 / 0.06 / 0.07 | 0.24 / 0.51 / 0.30 (CEMS) | −0.15 / −0.45 / −0.23 |
| hydro | 6.73 / 6.64 / 6.99 | 6.44 / 6.63 / 6.50 | ≈ match |
| nuclear | 4.41 / 4.55 / 4.37 | 4.44 / 4.59 / 4.40 | ≈ match |
| wind | 4.37 / 5.59 / 5.69 | 4.68 / 5.88 / 5.79 | ≈ match |

**The overnight CC over-run ≈ the overnight import UNDER-run, all three years.**
The model serves the overnight residual with domestic CC where reality serves
it with IMPORTS. CC_CHP is slightly OVER (not the gap); CT_PEAKER is a tiny
overnight class (not the gap); hydro/nuclear/wind match measured within noise.

**Robust to the demand basis:** model overnight demand (~47.3 TWh) is below the
EIA-930 CISO Demand row (~51.7 TWh) — a known demand-basis difference, not an
error — so the comparison is made on the CC-vs-import SHARE, which is
basis-invariant: model CC share of (CC+imports) = 60 / 60 / 57 % vs measured
55 / 52 / 46 %. The model over-allocates the overnight CC+import block to CC,
every year.

## 3. Why the model prefers CC to imports overnight — the CARBON WEDGE at parity

The model's south corridor has HEADROOM overnight yet does not use it:

* Overnight import by corridor (TWh): `WECC_PNW→NP15` 3.56 / 4.18 / 4.53
  (avg ~1.6–2.1 GW, at/above its ~1.3 GW median cap — MAXED; the PNW hub is
  negative, −$26 at p10–25, so the model already takes all the cheap north);
  `WECC_DSW→SP15_rest` 6.47 / 5.69 / 5.77 (avg ~2.6–3.0 GW of the ~5.2 GW
  median cap — SUBSTANTIAL HEADROOM left).
* But the DSW import is priced AT PARITY with domestic CC overnight: 2023
  overnight zonal-price medians — CA zonal $54.4, `WECC_DSW` $55.1 (p10/25/50/
  75/90 = 38.3/45.3/55.1/60.8/65.9). The model has no economic reason to import
  more via DSW because the incremental DSW MW costs the same as the CC it would
  displace.
* That parity IS the FINDING-caiso86b §3-4 CARBON WEDGE: beyond ~5.2 GW of
  clean-priced supply, every incremental model import MW pays the +$13–19
  unspecified/fossil CARB rung (~$40 hub + ~$15 wedge ≈ $55). Reality's
  marginal import in surplus-West hours carries NO wedge (WEIM/EDAM GHG
  attribution assigns clean resources to CAISO transfers). caiso-87
  (`caiso_dsw_surplus_clean`, IN the keeper) adds clean import DEPTH — but only
  in CAISO-surplus (midday solar) TRIGGER hours. Overnight (no solar) is
  UNCOVERED, so the wedge still applies overnight and the model runs CC.

## 4. The price direction — disclosed tension #1 resolved AGAINST WP-B

Overnight demand-weighted λ (model) = $60.6 / $40.9 / $44.0 = **+3.4 / +1.8 /
+3.6 OVER actual RT** (reproduces the caiso-91c baseline exactly). The marginal
overnight resource is CC at carbon-wedge parity (~$55–61).

* **WP-B (force CC off)** imports the displaced MW at the SAME $55 wedge parity
  → overnight λ stays OVER (fixes the volume by force but NOT the +2..+4
  over-price). The disclosed tension resolves in the UNFAVORABLE direction: the
  displaced energy's home is imports, but the model's imports are not currently
  cheaper than the CC they'd replace.
* **An import-side fix** that lowers the overnight incremental import price to
  reality's clean level makes imports marginal at a LOWER price → overnight λ
  falls toward actual AND the CC over-run closes economically. One structural
  fix, BOTH symptoms (the CC volume over-run and the overnight over-price) —
  rule 19.

## 5. Why WP-B is not buildable honestly (doctrine)

* The keeper ALREADY runs the full CC commitment bridge (`caiso_ra_mustoffer` +
  `caiso_ra_startup_bridge` + `caiso_ra_bridge_decommit`, `min_load_frac` 0.26).
  FINDING-caiso91c measured only 0.16 TWh of overnight CC at binding RA floors
  (2024) — ≥92 % is FREE in-merit economic dispatch. There is no commitment
  scaffolding to remove.
* The ERCOT-63 "bridge template" is a min-gen FLOOR (raises dispatch — wrong
  direction). Reducing free in-merit CC requires either a fitted cap/adder
  (rule 11/25 forbidden) or an economic de-commit (the archived-P2 family,
  CLI-locked behind `--enable-legacy-p2`). WP-B collapses to one of those.

WP-B is refuted on all three grounds: it is an import phenomenon not a
commitment one (§2-3); forcing CC off does not fix the over-price (§4); and it
cannot be built as a legitimate P1-native mechanism (§5).

## 6. Disposition

* **Candidate 3 / WP-B is CLOSED — refuted by the precondition, no build.**
  With candidate 1 (online-scoped reserve co-opt, `caiso-91`, inert),
  candidate 2 (Panoche committed-tranche gate, FINDING-caiso91b, no-LP refuted),
  and now candidate 3, the CC-overnight lane's commitment-mechanism family is
  exhausted.
* **The CC-overnight lane REDIRECTS to the import side:** extend the caiso-86b/
  87 clean-import attribution to the OVERNIGHT surplus-WEST regime (the same
  family, sliced by hour-of-day instead of by month). This is a NEW admissible
  sub-lane — caiso-86b closed only the measured-ladder-PRICE form (fitted $/MWh
  rungs failing LOYO), NOT the clean-attribution/carbon-wedge composition;
  caiso-87's surplus-clean depth fires only in midday CAISO-surplus hours, so
  overnight is genuinely uncovered.
* **Precondition before that build (derive-first, NO LP — the load-bearing
  admissibility gate):** does the MEASURED overnight (hod 0-5) CAISO−hub spread
  show NO carbon wedge (clean attribution) in overnight surplus-West hours,
  specifically for the DSW/Palo Verde SOUTH corridor (the PNW negatives already
  say yes for the north)? If YES, derive an overnight clean-depth/no-wedge
  trigger with caiso-86b-style estimation gates (CV ≤ 0.20 year-stability +
  LOYO ≤ 25 % held-out). If NO (overnight DSW is fossil-marginal → the wedge is
  correct overnight), the redirect is wrong and the lane is an owner checkpoint.
  Do NOT build before this gate passes (the caiso-86b "don't tune the method to
  the gate" prohibition).

**Owner checkpoint before further solves.** Keeper unchanged (caiso-92);
nothing registered this session (the repro is a same-machine reproduction of
the existing keeper, not a new run).

## 7. Caveat on rigor

An adversarial 4-lens verification (numbers / price-direction / doctrine /
redirect-admissibility) was designed but not run (owner redirected the session
to preservation). The four load-bearing facts (§2 numbers, §3 DSW parity, §4
price resid, §5 bridge state) are each directly measured or documented; the
build/no-build call is grounded judgment, not independently cross-checked.
