# ADDENDUM 2 to PRECOMMIT-miso263 — a SECOND defect: `replay_keeper.py` replays a PARTITIONED composite on ONE leg's config

```
SESSION : miso-263        ISO: MISO        PARENT LP: ZERO.
FOUND   : after the first wave of six repair shards reported. The 2025 shard
          flagged it in its own report ("confounded with reserve flags"); this
          addendum verifies the claim, finds it is TRUE and BROADER than the
          shard said, and records the correction before the re-run lands.
COST    : 2 of the 6 first-wave bundles (2024, 2025) are DISCARDED and re-solved;
          2023 never landed. 2020 / 2021 / 2022 are UNAFFECTED and VALID.
```

---

## 1. THE DEFECT

`scripts/replay_keeper.py` builds its recipe with `run_year_kwargs(meta)` — and
`meta` is the bundle's **single, span-wide `meta.json`**. It has no per-year
dimension. MISO's keeper, however, is **two configs partitioned at 2023, and the
partition is FORCED BY DATA** (`_miso260_compose_span.py`'s own header):

| field | 2020–2022 | 2023–2025 |
|---|---|---|
| `miso_measured_reserve_requirements` | `False` | **`True`** |
| `miso_reserve_online_gated` | `False` | **`True`** |

because `load_miso_reserve_requirements` hard-errors before 2023 (the measured
cleared-reserve parquet starts there).

The composite's `meta.json` and base `run_config.json` carry the **2020 leg's**
values — `[False, False]`. So **replaying any train-tier year of this bundle
silently solves it on the validation leg's reserve configuration.** Measured,
composite base config against each committed per-year `run_config_<y>.json`:

| year | fields differing from the composite base |
|---|---|
| 2020 | none |
| 2021 | `gas_price_override`, `weather_year` |
| 2022 | `gas_price_override`, `weather_year` |
| **2023** | those two **+ both reserve flags** |
| **2024** | those two **+ both reserve flags** |
| **2025** | those two **+ both reserve flags** |

`gas_price_override` and `weather_year` are **not** affected: `bundle_gas_price`
falls back to `_henry_hub_actual(year)`, which reproduces every year's own
recorded price exactly (2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52), and the
runner sets `weather_year` per year. Verified in every landed bundle. **The two
reserve flags are the entire exposure.**

## 2. WHAT IT COST, AND WHAT IT DID NOT

**Discarded:** the first-wave 2024 (`4b30d39c…`) and 2025 (`c64a50c9…`) bundles.
Both recorded `[False, False]` where the keeper's own per-year config says
`[True, True]`, so they are not the keeper's recipe for those years. They are
**not deleted** (rule 31 `[R-RETAIN]`) — they remain at their SHAs — they are
simply not composable.

**Unaffected and valid:** 2020, 2021, 2022. Their own per-year flags *are*
`[False, False]`, identical to the composite base, so the replay applied the
right configuration. **The session's headline finding rests entirely on these
three years** — the 2022 object above all — and is untouched.

**The guard worked.** `_miso260_compose_span.py::check_recipes` enforces the
partition (`PARTITIONED[field][tier]`) and would have ABORTED the composition
rather than silently produce a mixed-config span. Nothing wrong could have
reached the dashboard through it.

## 3. THE CORRECTION

Three re-run shards (2023, 2024, 2025), same pinned SHA, adding to the replay:

```
--set miso_measured_reserve_requirements=true \
--set miso_reserve_online_gated=true
```

These are the keeper's **own declared per-year values**, read from its committed
`run_config_<y>.json` — a provenance repair, not a tuning choice. **Zero free
parameters** (rule 21 `[R-DOF]`), and no criterion was consulted to pick them
(rule 1 `[R-STRUCT]`). Each shard carries a hard stop requiring all five of
`coal_fuel_inventory` / both reserve flags / gas / weather year to read correctly
in its own output bundle before it pushes.

## 4. CREDIT, AND THE READING OF IT

The first-wave **2025 shard flagged this itself** — "coal ceiling confound
identified; −5.5945 TWh coal / +1.3805 $/MWh confounded with reserve flags;
awaiting governance decision on which record is authoritative." That was right,
and it was right about something its siblings missed. It was also **narrower than
the truth**: the same confound hits 2024 and would have hit 2023, and the
"governance decision on which record is authoritative" it asked for is not
actually open — the per-year `run_config_<y>.json` is authoritative by
construction, because `run_config` is written from what the solve ran, whereas
the composite's base `meta.json` is a copy of one leg made by the composer. The
claim was verified against the artifacts rather than accepted on report.

## 5. THE STANDING LESSON, NAMED FOR THE SUCCESSOR

**`replay_keeper.py` is unsafe on a PARTITIONED composite bundle and does not say
so.** It will silently apply one leg's configuration to every year. That is the
same family as this session's primary finding — *a run whose recorded provenance
does not match what solved* — and it is now the second instance found in one
session, in the same bundle.

Two candidate repairs, neither taken here (this session is not chartered to
change `replay_keeper`, and a solve-path change mid-flight would invalidate the
shards pinned to `bb6e266e`):

1. **Make it per-year**: when `run_config_<y>.json` exists, overlay it on the
   meta-derived recipe for that year. Strictly better provenance, and it would
   make the `--set` flags above unnecessary.
2. **Make it refuse**: detect a partitioned composite (any field differing across
   the committed per-year configs) and hard-error unless the caller acknowledges
   the partition — the fail-fast discipline `input_completeness` already applies
   to missing inputs.

Recommended to the owner as a follow-up, with (1) preferred and (2) as the
minimum. Either would have caught this before a single LP was spent.
