# E7 staleness memo — keeper vs newer registry run (2026-07-06)

**Status: DRAFT for owner sign-off. No keeper swap or sidecar edit has been made.**
**Gap:** G-04 (`docs/gap-register-2026-07.md` §3.1). **Owner decision required.**

## What E7 is

`scripts/audit_keepers.py` check **E7** (WARN-only, never a FAIL) flags a keeper
when a *newer-dated* run for the same ISO exists in
`frontend/data/backcast/registry/`. It is a truth-in-labeling prompt, not a
correctness gate: a newer run *might* be a better keeper, or it might be a
diagnostic probe that was never a keeper candidate. E7 already excludes
`*-ablation` twins and any sidecar carrying `"keeper_candidate": false`; the four
warnings below are runs that carry **neither** marker yet.

The register lists ERCOT/CAISO/PJM/NYISO. (MISO's newer run is the miso-41 keeper
itself; NEISO is clean.) Each newer run's own `definition` prose is quoted as the
primary evidence.

## Per-ISO adjudication

| ISO | Keeper | Newer run | Newer run is… | Recommendation |
|---|---|---|---|---|
| **ERCOT** | `2026-07-03-ercot32-ordc-total-rtolcap` | `2026-07-05-ercot40-rtolcap-forward` | WS-A forward-supply-cap **probe** (P1-only): ercot32 recipe with `ercot_reserve_supply_forward=True` swapping the *measured* RTOLCAP cap for the WS-A *forward formula* cap, to validate the forward analogue. Isolates one forecast-path delta; not a backcast keeper candidate. | **KEEP ercot32.** Mark ercot40 `keeper_candidate: false`. |
| **CAISO** | `2026-07-03-caiso-51-firm-base` | `2026-07-05-caiso-statmode-d7-r2` | D-7 statistical-mode A/B **probe**: byte-faithful keeper replay with every per-hour/per-year overlay off. Its own text: "Probe only — not a keeper, per CLAUDE.md #1/#13." | **KEEP caiso-51.** Mark the statmode probe `keeper_candidate: false`. |
| **PJM** | `2026-07-05-pjm-77-ct-relfloor` | `2026-07-05-pjm-78-demand-regate` | Demand-repair re-gate **probe** (PR #1426). Its own text: "(PROBE, not a keeper swap)"; Twin A reproduces the pjm-77 verdict criterion-for-criterion (NOT-YET, same FAIL/PASS pattern). | **KEEP pjm-77.** Mark pjm-78 `keeper_candidate: false`. |
| **NYISO** | `2026-07-03-nyiso-41-hub-prices` | `2026-07-05-nyiso-statmode-d7-r2` | D-7 statistical-mode A/B **probe**, re-solved at HEAD for the R2 CO2 basis. Diagnostic A/B, not a keeper candidate. | **KEEP nyiso-41.** Mark the statmode probe `keeper_candidate: false`. |

## Recommendation summary

**No keeper swap is warranted for any of the four ISOs.** Every newer run is a
diagnostic probe (forward-supply validation, D-7 statistical-mode A/B, or a
demand-repair re-gate that reproduces the incumbent verdict), none of which is a
structurally-more-faithful backcast keeper (CLAUDE.md #1/#11). The four E7
warnings are therefore false-positives of the "newest-dated run" heuristic.

**Proposed cleanup (owner sign-off):** set `"keeper_candidate": false` on the four
probe sidecars
(`2026-07-05-ercot40-rtolcap-forward`, `2026-07-05-caiso-statmode-d7-r2`,
`2026-07-05-pjm-78-demand-regate`, `2026-07-05-nyiso-statmode-d7-r2`). The E7
logic (`_registry_dates_by_iso`, audit_keepers.py) already excludes such
sidecars, so this clears all four WARNs without touching any keeper, and it is
the same marker already used for prior probes (rule 15: mark, don't prune — the
probes stay on the dashboard, they just stop competing for newest-run
staleness).

## Addendum 2026-07-06 — MISO resolved by keeper promotion

The MISO E7 WARN that appeared when `2026-07-06-miso-42-coal-econ` registered
against the `2026-07-05-miso-41-ct-evening` keeper is resolved by the owner's
2026-07-06 promotion decision: **miso-42 IS the new MISO keeper** (the E7
heuristic was a true positive this time — the newer run was a genuinely
more-structurally-faithful candidate, promoted per rule 1). Same-date MISO
probes (`2026-07-06-miso-41-v2rescore-probe`, the miso-41/miso-42 ablation
twins) are probes/twins, not contenders; the v2rescore probe sidecar carries
`keeper_candidate: false` semantics in its "(PROBE)" definition. No other ISO
row in this memo is changed by the MISO promotion; the ERCOT/NYISO rows above
are superseded by their own 2026-07-06 promotion lanes.

**Caveat / why this is a *draft*:** marking a run `keeper_candidate: false` is a
judgment that the run was never a keeper contender. That is defensible from each
run's own definition prose, but it is the owner's call to make — hence this memo
records the recommendation rather than enacting it. The two new ablation twins
registered in this lane (`…pjm-77-ct-relfloor-ablation`,
`…miso-41-ct-evening-ablation`) are `*-ablation`-named and so are already E7-exempt;
they add no new warnings.
