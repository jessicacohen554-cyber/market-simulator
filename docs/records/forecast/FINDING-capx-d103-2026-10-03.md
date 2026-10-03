# FINDING — capx D103: forecast DOF-ledger carry census, NEISO and NYISO (zero LP)

**Lane:** capx D103, branch `claude/capx-d103-dof-carry`. **Date:** 2026-10-03. **Charter:** ledger
§0bn.2a rung 2 "ledger carry"; owner rulings Q74 (NYISO `complete`) and Q76 (T1-F re-solves for NEISO
and NYISO). **Source:** `main` at `7e6eacfde885d12981a189fec2f3cce23affe5b7` (the pinned `07f5b88e`
was not the local tip; origin fetch timed out, so this is the clone's `origin/main`). **DATA PROFILE: code.**
**What this is not:** no code change, no solve, no ledger edit. `scripts/`, `src/`, `results/`, `frontend/`
untouched; the proposed diff in §3 is for the desk to charter separately (rule 27).

## 1. What was read

| Artifact | NEISO | NYISO |
|---|---|---|
| Keeper (shard `frontend/data/backcast/keepers/<ISO>.json`) | `2026-10-02-w0-neiso` | `2026-10-02-w0-nyiso` |
| Bundle on `main` | `results/calibration/w0_neiso_span/` | `results/calibration/w0_nyiso_span/` |
| Rule-21 ledger | `calibration_attestation.json` → `free_parameters` (no separate `dof_ledger.json`); 6 entries, 4 residual | same path; 8 entries, 6 residual |
| `authorized_price_tuning` | key absent (reads `null`) | present, `null` |
| Forecast ledger builder | `scripts/build_forecast_dof_ledger.py` (`build_entries`, `_registry_identification`, `CURATED` rows) | same |
| Forecast reference run | none registered for NEISO with a ledger on `main` | `results/ff-t1f-d45r/nyiso/` (`dof_ledger.json`: 1 entry, `forecast_xyear_warmstart`) |

**How the forecast builder scopes.** It enumerates only ScenarioConfig fields whose run value differs from the
shipped default (`build_entries`); a field equal to the default is skipped, and anything outside ScenarioConfig
(`constants.py`, `interchange_config.py`, a reference CSV) is never enumerated. Registry defaults are covered by one
pointer block, `registry_identification`, which names the keeper id and asserts nothing per entry. So **no keeper
entry is carried as an entry today, for either ISO**; the carry is the pointer alone.

## 2. Census — keeper entry → forecast side

Forecast-side values are read from `ff-t1f-d45r/nyiso/run_config.json` (mode `forecast`) and the code path; NEISO
shares every shipped default named here. "Live" = the value acts in a forecast solve.

| Keeper entry (both ISOs unless marked) | Ident. | Keeper value | Live in forecast? | Forecast field / why | Carried today? |
|---|---|---|---|---|---|
| `offer_curve_by_group` (83 scalars) | residual | 12 groups, set in `pipeline/backcast_config.py` | **No** — forecast run carries `{}`; `data/offer_curves.py:391` falls back to neutral bands | `scenario_config.offer_curve_by_group` | No (pointer only) |
| `offer_curve_committed_below_floor` (NEISO ST_GAS 0.8497; NYISO CT_PEAKER 0.843) | residual | sub-0.85 committed band | **No** (same empty dict) | same | No |
| `offer_curve_smoothing` (n 6, exp 1.0) | residual | shipped default | **Yes** (forecast run n 6 / exp 1.0) | `offer_curve_smoothing_n` / `_exp` — skipped as default-equal | No |
| `wefor_multiplier` 0.7 | residual | set only by `backcast_config.py:1592` | **No** — forecast runs the ScenarioConfig default 1.0 | `wefor_multiplier` | No; n/a unless a forecast arms it |
| `reliability_floor` coefficients (CSV) | measured-physical | `reliability_floor_coeffs_<ISO>.csv` | **No** — `reliability_floor` is `False` in the forecast run | `reliability_floor` (boolean) | n/a in forecast mode |
| `IMPORT/EXPORT_TRANCHES[NEISO]` | measured-physical | seam ladders, frozen derive | **Yes** — forecast years fall back to the static ladder (`import_nodes.py:85-87`) | `interchange_config.py`, outside ScenarioConfig | No |
| `IMPORT/EXPORT_TRANCHES[NYISO]` | **residual** | fitted ladders (audit C-6/L7/L8) | **Yes** (static ladder in every forecast year) | same | No |
| `NYISO_LOCAL_SELFSUPPLY_FRAC['Long_Island']` 0.45 (NYISO) | residual | `constants.py` | **Yes** — `interchange/nyiso.py:493` gates on ISO only, not mode | `constants.py`, outside ScenarioConfig | No |
| `campd_ct_run_lengths_NYISO.csv` (NYISO) | measured-physical | frozen derive | Yes where the fast-start horizon is armed | fleet loader input, outside ScenarioConfig | No |
| `battery_dispatch_adder` (W2 list) | — | 0.0 in both keepers and the forecast run | n/a | not a NEISO/NYISO free parameter | n/a |

Counts: **NEISO** 0 of 6 carried as entries; 3 live-in-forecast and uncarried (smoothing, NEISO tranches, both
non-residual except smoothing). **NYISO** 0 of 8 carried; 5 live and uncarried, of which **3 residual**
(smoothing, fitted tranches, LI self-supply 0.45). The three offer-band entries and `wefor_multiplier` are not
live: a forecast dispatches on neutral bands and full wind EFOR. Two consequences for the desk: (a) the
`registry_identification` note says the run "inherited" the offer surfaces — for these ISOs it did not; (b)
whether a T1-F re-solve (Q76) should arm the keeper bands is a structural question (rule 1), not a ledger one.

## 3. Proposed carry (report-only block; rule 21 wording)

Add a curated keeper-carry table and one function; emit a `keeper_carry` block, never a scored entry, until FC-7's
treatment of a carried residual is chartered. `source` string: `carried residual — <keeper id>
free_parameters[<name>]; identification unchanged from the backcast keeper (rule 21); live in forecast via <field>`.

```python
# scripts/build_forecast_dof_ledger.py — proposed, NOT applied in D103
#: (iso, keeper entry) -> forecast posture; live=False rows report as not_applicable_in_forecast.
KEEPER_CARRY = {
    ("*", "offer_curve_by_group"):            {"live": False, "field": "offer_curve_by_group", "why": "forecast run carries {} -> neutral bands (data/offer_curves.py)"},
    ("*", "offer_curve_smoothing"):           {"live": True,  "field": "offer_curve_smoothing_n/_exp", "why": "shipped default equals keeper value"},
    ("*", "wefor_multiplier"):                {"live": False, "field": "wefor_multiplier", "why": "0.7 set only by pipeline/backcast_config.py; forecast default 1.0"},
    ("*", "reliability_floor coefficients"):  {"live": False, "field": "reliability_floor", "why": "boolean off in forecast runs"},
    ("NEISO", "IMPORT_TRANCHES/EXPORT_TRANCHES[NEISO]"): {"live": True, "field": "interchange_config.IMPORT_TRANCHES", "why": "static ladder in every forecast year"},
    ("NYISO", "IMPORT_TRANCHES/EXPORT_TRANCHES[NYISO]"): {"live": True, "field": "interchange_config.IMPORT_TRANCHES", "why": "static fitted ladder in every forecast year"},
    ("NYISO", "NYISO_LOCAL_SELFSUPPLY_FRAC['Long_Island']"): {"live": True, "field": "constants.NYISO_LOCAL_SELFSUPPLY_FRAC", "why": "ISO-gated, not mode-gated"},
}

def _keeper_carry(iso: str, keeper: str) -> dict | None:
    """Report each keeper rule-21 entry's forecast posture (carried residual / n/a); never scores."""
    att = REPO / "results" / "calibration" / _bundle_dir(keeper) / "calibration_attestation.json"
    entries = json.loads(att.read_text()).get("free_parameters", {}).get("entries", [])
    out = {"carried_residual": [], "carried_measured": [], "not_applicable_in_forecast": []}
    for e in entries:
        row = KEEPER_CARRY.get((iso, e["name"])) or KEEPER_CARRY.get(("*", e["name"]))
        rec = {"name": e["name"], "identification": e["identification"], "keeper": keeper,
               "forecast_field": row and row["field"], "why": row and row["why"],
               "root_cause": e.get("root_cause")}
        if row is None or not row["live"]:
            out["not_applicable_in_forecast"].append(rec)
        elif e["identification"] == "residual":
            rec["source"] = f"carried residual — {keeper} free_parameters[{e['name']}]; identification unchanged (rule 21)"
            out["carried_residual"].append(rec)
        else:
            out["carried_measured"].append(rec)
    return out
# build_ledger(): ledger["keeper_carry"] = _keeper_carry(iso, reg["backcast_keeper_at_build"])
```

Unknown to pin before the code lane: the keeper id → bundle directory map (`2026-10-02-w0-neiso` lives at
`results/calibration/w0_neiso_span/`); `_bundle_dir` must resolve it from the registry, not a name rule.

## 4. Rule-1 channel (task item 3)

Neither attestation declares `authorized_price_tuning` (NEISO: key absent; NYISO: `null`) while both ledger
`offer_curve_by_group` as residual with 83 scalars — the W4 defect the close-out plan names for MISO/CAISO applies
here too. A forecast run would **not** read those bands: `offer_curve_by_group` resolves to `{}` on the forecast
path (`ff-t1f-d45r/nyiso`), and `backcast_config.py` is imported only by `run_calibration*.py`.
