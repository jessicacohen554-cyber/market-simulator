# RESULT nyiso-153 — the in-city commitment obligation is REJECTED-AS-ARMED on its own pre-registered branches; the durable finding is that the downstate under-commitment is REAL and this instrument is structurally wrong for it

Session nyiso-153, 2026-08-22. Prereg
`PREREG-nyiso153-incity-obligation-2026-08-22.md` + phase-0 record
`_nyiso153_phase0.json` + gates probe committed and pushed BEFORE the arm
solved. ONE solve (ARM O = the nyiso-152 keeper recipe +
`nyiso_incity_commitment_obligation`; control = the committed keeper bundle,
no re-solve — zero solve-affecting commits since it solved, verified in the
prereg). Run `2026-08-22-nyiso-153-incity-obligation`, registered per rule 15
as a rejected probe. Gates record `_nyiso153_ab_gates.json`. Holdout freeze
ACTIVE; 2023–2025 only.

## 1. The adjudication (two independent grounds)

* **O-K3 REJECT branch, exactly as pre-registered:** the LP prefers the
  published $25 NYC RCPF shortfall to full commitment. `nyc_10min_total`
  ends in standing shortfall **5,744 / 7,458 / 7,160 h** (bar: 2,000;
  committed prediction ≥ 5,000 / ≥ 5,000 / ≥ 4,000) at a ~$23–24 dual for
  ~7,400–7,950 h/yr — a permanent locational reserve-shortfall regime the
  real market never shows (RCPF activation is an exception state). LI is
  worse than predicted: the arm **collapses** LI in-pocket online output
  (p50 203 → **1 MW**, 2023) — subsidized NYC steam energy displaces the LI
  units that previously ran, so the mechanism *fights itself* across the two
  pockets it is meant to serve.
* **O-K4 FAIL (K6′, both legs):** two **new D-4 unit-conduct convictions at
  2517 Port Jefferson** (`nyiso_gas_commitment_bridge × ST_GAS`, 2024/2025)
  and material forced-share escalation (bridge ST_GAS 1.4 % → 6.8 % in
  2024): the subsidy pushes downstate steam into P0 runs that the bridge's
  min-run/gap legs then extend into floors at plants whose meters say off —
  manufacturing exactly the scaffolding class nyiso-152 just removed.

O-K1/O-K2 PASS (single delta; families re-classed 1 → 2; the
`MEASURED online_rho=0.3014` line every year — the first solve to consume
the measured coefficient since the RHO_CLIP ruling made it admissible).
O-K5: criteria statuses identical to the keeper (C1/C2/C3a/C3b/C4/C8 PASS,
C3c FAIL at bit-identical counts 1/0/0 vs RT 10/13/42); C6
unattested-probe.

## 2. Recorded against the prediction — and it is the session's real finding

The phase-0 static flip-cross predicted near-zero commitment response
(flippable capacity covered the need in 3 %/3 %/12 % of NYC deficit hours).
The equilibrium response was much larger: **NYC in-pocket online output
rose 645 → 1,404 MW (p50, 2023)** — the $7.53/MWh effective-offer subsidy,
compounded through P0/P1 re-equilibration, committed ~750 MW of NYC steam —
and **C3a-2023 IMPROVES +5.3 % → +3.4 %**. Both prediction misses are
recorded, and neither rescues the arm (the branch bar sat far below the
landed shortfall). What they establish is durable: **the downstate
in-pocket under-commitment the mechanism targets is REAL** (committing the
steam moves the 2023 level toward actual), and the measured basis stands
(the real fleet's ρ·ΣP covered the requirement; the model's does not). The
defect is the INSTRUMENT: a $25-capped gated reserve row cannot carry a
commitment obligation, and what commitment it does induce routes through
the bridge amplifier into meter-dark floors.

## 3. Successor shape (named, not armed, needs its own prereg)

A commitment-POPULATION representation of the in-city obligation — the
DARU/SRE local-reliability commitment class: scaffolding with a declared
driver and window (rule 17), driven by the published locational requirement
and the in-pocket fleet's measured committed pattern — NOT a deeper ORDC
penalty. The $25 RCPF is the published instrument; raising it to force
commitment would be a fitted adder (rules 1/5). Any successor must also
reconcile with the existing downstate ST_GAS reliability-floor limbs and
the bridge (rule 19 — one mechanism owning the phenomenon), and with the
2517 lesson: a conduct-gated membership so induced commitment cannot land
on meter-dark plants.

## 4. The sibling: `nyiso_synchronised_reserve` U → G (no solve)

The prereg §6 disposition rule fired: path A differs from the tested form
only by a NON-published $500 penalty on a hand-scoped family (no NYC RCPF
cell prices $500 — rule 5) and a quick-only eligible set its own artifact
refutes (measured spin supply is steam-carried: steam bucket ρ 0.3283 on
6.4 GW vs quick 0.2157 on 3.1 GW). Refused as the
reach-the-number-through-an-unreal-mechanism move (rule 1); re-open only
with a published penalty instrument and a supply-matched eligible set.

## 5. Dispositions

* Matrix: `nyiso_incity_commitment_obligation` **U → R** (this record);
  `nyiso_synchronised_reserve` **U → G** (§4). Keeper unchanged
  (`2026-08-22-nyiso-152-duty-complete`); no shard swap, no re-key.
* Registration auto-pruned `2026-08-19-nyiso-146-perplant-minrun` (top-15).
* The online-rho pair queue item is CLOSED (both cells adjudicated); the
  remaining testable lane is the Flynn/Bethlehem start-conduct residual,
  after which the frontier statement is re-assessed.

## 6. Reproduction

```
python3 scripts/probes/_nyiso153_phase0.py
python3 scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso153_armO_recipe --out-dir results/calibration/nyiso153_armO
python3 scripts/legitimacy_diagnostics.py --bundle results/calibration/nyiso153_armO --iso NYISO --json-out results/calibration/nyiso153_armO/legitimacy_diagnostics.json
python3 scripts/probes/_nyiso153_ab_gates.py --arm-log <solve log>
```
