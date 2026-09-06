# PREREG nyiso-199 — `CT_PEAKER` bands re-grounded on their OWN registered measured basis: rule-29 two-year screen

**Status at push: PENDING AN OWNER RULING (§0). Nothing is built and nothing is solved until the
ruling is recorded here as an addendum.** This document is pushed BEFORE any arm exists so that
every gate, both screen years, and the C3a-2025 exposure are on the record ahead of the first
number.

**Session:** nyiso-199, 2026-09-06. **Keeper / control:** `2026-09-06-nyiso-196-extract-basis`
(bundle `results/calibration/nyiso196_extract_basis`), rule 29(b) form 4 — **no control solve**;
G-DRIFT validated empirically, `FINDING-nyiso199-ct-peaker-band-basis-2026-09-06.md` §6.
**Phase 0 (zero LP) is complete and is that finding.**

## §0 — The ruling this pre-registration waits on

The arm is an `offer_curve_by_group` band substitution. This lane's brief gates any such change on
an explicit owner ruling. The question:

> May NYISO's `CT_PEAKER` `committed` / `econ_low` / `econ_high` be set to that class's OWN
> registered measured `phys_committed` / `phys_econ_low` / `phys_econ_high` (**0.843 / 0.661 /
> 0.658**, `nyiso_campd_marginal_hr_summary.csv` p50s, n = 70) — as a gated, registered
> `ScenarioConfig` field on the caiso-241 construction, **selecting no value**, adding **no free
> parameter and no DOF entry** — and screened on 2023 and 2025 before any span is spent?

Grounds, both ex ante and neither the residual:
1. **Rule 19 `[R-ONE-MECH]`, measured on this keeper.** `tranche_startup_amortization = True`
   already amortizes `BIN_STARTUP_COST_PER_MW["CT_PEAKER"] = $20/MW` (NREL/SR-5500-55433) over the
   measured P0 run length onto the `committed` tranche, while `_NYISO_OFFER_CURVE` calls the 1.35
   over `phys_committed` 0.843 "the start hurdle … a ~$25/MWh fixed commitment margin" on the same
   tranche. `PRECOMMIT-caiso241-ct-peaker-committed-2026-09-03.md` §1 names **NYISO 1.350 / 0.843**
   in its five-ISO census; its limb 3 binds harder here because CAISO's amortization was OFF.
2. **The config's own declared OPEN ROOT CAUSE.** `_NYISO_OFFER_CURVE`'s `CT_PEAKER` comment:
   *"econ bands DE-LEAKED from the ERCOT generic fallback (was econ_low 1.27 / econ_high 1.98) to
   neutral 1.0 … NYISO carries no independent CT part-load heat-rate spread yet. OPEN ROOT CAUSE
   (rule #1): a NYISO-grounded CT econ ramp (CAMPD CT heat-rate spread) is a later
   disciplined-calibration item."* That named input exists and is registered on the same band dict.

Rule 25 `[R-ISO-SCOPE]`: **no CAISO verdict transfers.** The values are NYISO's own, measured on
NYISO's own CAMPD conduct. The caiso-241 material is cited for the ADMISSIBILITY construction only.

**Explicitly out of scope, and not to be added later without a fresh pre-registration:** the `peak`
band (NYISO's 4.0 wall is the $1,000 offer-cap scarcity structure the config states it as, not a
physics claim); `pct_peaking` and `econ_low_share` (structural shares, rule 1 forbids them
outright); `nyiso_downstate_ct_gas_basis` (a measured input, rule 14 says keep it); every other
class and every other ISO.

## §1 — The arm, if ruled

**Field:** a new gated `ScenarioConfig` boolean, NYISO-scoped, default **off**, registered in
`_CACHE_KEY_OPTIONAL_FIELDS` with its pinned default in the same commit (rule 24), plus its base
matrix row and a cell in every shard (rule 26(c)). It resolves the three bands from the class's
own `phys_*` keys and refuses to arm if any is absent — **zero literals, zero free parameters,
zero DOF entries** (rule 21).

**Byte-inert off**, by construction: the off path reads the registered bands unchanged.

## §2 — Pre-solve gates (zero LP). ALL must pass before any solve.

* **F-1 SCOPE.** Exactly the `CT_PEAKER` `econ*` and `committed` rows move. **Predicted: 101 / 103 /
  103 rows in 2023 / 2024 / 2025, split econ 79/81/81 + committed 22/22/22, and ZERO rows in any
  other class, band or ISO.** Any other row moving is a STOP.
* **F-2 CAPACITY IDENTITY.** `pmax` and `availability` max‖Δ‖ = **0.0** exactly. Any capacity move
  is a STOP — this arm is an offer change and nothing else.
* **F-3 FUEL-INVARIANCE.** The per-band Δ is a fixed $/MWh. **Predicted −$17.41 / −$17.41 / −$17.35
  (committed) and −$13.68 / −$13.69 / −$13.68 (econ)**, i.e. the same to the cent across three
  years whose CT offers differ by $22–30/MWh. A Δ that scales with fuel means the margin
  decomposition is not what §0 says it is: STOP.
* **F-4 PEAK UNTOUCHED.** Δ on the `peak` band = **0.00** in every year.

*(All four are already MEASURED and recorded in `_nyiso199_ct_band_basis_phase0.json`; they are
restated here as gates so the built arm must reproduce them.)*

## §3 — The screen: TWO years, named before the solve

Rule 29 names the screen year by the mechanism's own measured **footprint**, never by the residual.
Footprint = newly in-the-money `CT_PEAKER` MWh (no meter, no residual in the metric):
**2023 2.627 TWh > 2024 2.173 > 2025 2.142.**

* **SCREEN YEAR A = 2023** — the footprint year, per rule 29.
* **SCREEN YEAR B = 2025** — the **exposed** year, per this lane's standing instruction after
  nyiso-198 ("if your lever moves prices, state the 2025 exposure in the PRECOMMIT and consider
  screening the exposed year too before spending the span"). 2025 is where C3a has 0.4 pp of
  margin; screening the footprint year alone is the exact mistake nyiso-198 made.

Two one-year solves, run sequentially. **Throwaway diagnostic probes** (rule 29 clause 2): never
registered, never a keeper, never quoted as a keeper number, deleted before merge (rule 29(c)).
Every number the session will ever cite from them lands in this document's addendum.

## §4 — Screen gates. S-1 to S-3 may kill; none may promote.

* **S-1 DIRECTION AND MAGNITUDE (meter-free).** `CT_PEAKER` dispatch must RISE, and by an amount
  bounded by the D-2 reachability envelope: **> 0 and ≤ (arm ITM bound − keeper ITM bound)**, i.e.
  ≤ 2.627 TWh in 2023 and ≤ 2.142 TWh in 2025. A rise outside that envelope means the mechanism is
  doing something its own arithmetic does not predict: STOP.
* **S-2 CONFINEMENT.** The energy `CT_PEAKER` gains must come from the gas family, and the six-class
  gas total must not move by more than the C1 family band. A gain drawn from hydro, nuclear,
  imports or storage is a STOP.
* **S-3 LOAD-BEARING COMPANIONS.** No non-target load-bearing criterion may flip PASS → FAIL:
  **C1** (all classes, both years), **C2**, **C3a**, **C3b**, and the protective **C6 / C8**.
  **C3a-2025 is the named risk**: the keeper reads −6.9 % against a ±10 % band and the crossing
  indicator predicts ~−9.6 %. **If C3a-2025 fails, the arm is STOPPED at the screen and the span is
  never spent** — the same discipline that killed nyiso-198, applied to the year that actually
  carries the risk.
* **C8 / D-4** must not add a forced-share or off-window-binding failure. `CT_PEAKER` carries a
  0.000 TWh forced floor today; the arm adds no floor, so any D-4 change is a STOP.

**The screen may kill the arm; it may never promote it.** It is not gated on the target residual:
S-1 is a bound from the arm's own pre-solve arithmetic, S-2 is a conservation check, S-3 is a
do-no-harm check. "Did C1 `CT_PEAKER` improve" is **not** a gate.

## §5 — If the screen clears

`--year 2023 2024 2025` in ONE invocation and ONE bundle (rule 16), registered the same session
(rule 15), with a computed attestation (G-CONTROL, G-DELTA exactly the one field, G-INPUTS pinning
the `phys_*` provenance, G-DOF **+0**, G-ENGAGE the solved fleet carrying the predicted rows).
NYISO's matrix shard updated in the same session (rule 26(b)). **Promotion is a separate question**
and is not pre-authorised by this document: nyiso-198's lesson is that a structural gain which
collapses the determination is not automatically a keeper.

## §6 — The paired arm, declared now so it cannot be added later as a surprise

`cc_duct_peaking_row_scoped` is cell **R** with the re-test condition "re-arm it PAIRED with the
merit-order repair, never alone". This arm is that repair, and the two push **opposite ways**
(nyiso-198 moved +1.1 to +1.4 TWh INTO `CC_REGULAR` out of `ST_GAS`/`CT_PEAKER`; this moves energy
out of `CC_REGULAR` into `CT_PEAKER`). They are **not additive** and must never be screened
separately and summed. If the owner wants the pairing tested, it is a **second arm on the same two
screen years** — `{this field: True, cc_duct_peaking_row_scoped: True}` — under this document's
gates unchanged, and its result is reported at full magnitude beside the single-field arm's. It is
NOT built unless the ruling asks for it.

## §7 — Governance

* **Rule 29 `[R-SCREEN]`:** phase 0 (zero LP) → pre-solve F-gates (zero LP, already measured) → TWO
  named screen years → span only if both clear. Screen bundles deleted before merge (29(c)).
* **Rule 29(b):** control = the keeper's committed bundle; **no control solve**. G-DRIFT validated
  by two empirical checks, not a hunk classification (finding §6).
* **Rules 21 / 23:** zero free parameters, no DOF entry, no derive re-run, no artifact touched.
* **Rule 25 `[R-ISO-SCOPE]`:** NYISO's own measured values only; no CAISO verdict transfers.
* **Rule 22:** 2023–2025 only. No marker requested; `complete` remains withdrawn.
* **Rule 1 `[R-STRUCT]`, boundary named not assumed:** this is a band substitution and therefore
  sits on the boundary of rule 1's carve-out. **It is not claimed to be outside it** — §0 puts the
  question to the owner and this document does not execute until the answer is recorded here.

---

*(nyiso-199, 2026-09-06. Pushed before any arm exists. Zero solves at time of push.)*
