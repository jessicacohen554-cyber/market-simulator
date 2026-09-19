# ADDENDUM — pjm-h10: the PJM replay SETUP CHAIN, and why four shards died on it (2026-09-19)

**Session:** pjm-h10 · **Parent finding:** `docs/FINDING-pjm-h10-the-energy-identity-2026-09-19.md`
**Why this is a separate document:** it is not about PJM's calibration. It is about **rule 32
`[R-SHARD]` (c)'s documented launch recipe being incomplete**, which cost this session four shard
containers and is going to cost every other lane the same until it is written down.

---

## 1. What happened

Four shards were launched to replay the two committed PJM bundles at a pinned SHA. None produced a
bundle. The failures were **not** model failures, **not** memory, and **not** the emissions dual —
they were environment setup, and **two of the four were caused by an instruction I wrote.**

| # | session | outcome |
|---|---|---|
| 1 | `session_01GVm2g4rPYhEHZT6kRmiB3S` | ended its turn after preflight, mid-solve; later resumed into env setup; archived |
| 2 | `session_01WiG8kSC7zZRG9R6xb85HJp` | began regenerating the clean tree (**correctly**), ended its turn; archived |
| 3 | `session_01FKXs8PaaohGkVSsYJTp6gK` | solve **died at 59 s on missing `data/clean`** — which my prompt had forbidden it to rebuild — and separately reported an **OOM at 23.4 / 24 GiB**. It then stopped and asked for authorization, correctly. |
| 4 | `session_01HSskC9q1YEKBMcv9RydYHr` | cleared every blocker itself, **OOM-killed in the 2020 P0->P1 seam**, and pushed a finding instead of a bundle — a SUCCESS by the rule's own definition (`claude/pjm-h10-mer-tp2`, `0bcb1a3c6265cdb253e5447b08288e4aa030bdf7`) |
| 5 | `session_013WuzZpNy1yBLDuXVVN8AcT` | relaunched with the clean-tree step required; **yielded mid-rebuild and stalled** — no bundle |
| 6 | `session_01DG8713GuWS33fC7aJybGoW` | same; got as far as the DA-virtuals fetch and **yielded mid-fetch** — no bundle |

**Shard 2 was right and my prompt overrode it.** It independently decided to regenerate the clean
tree; generation 2's prompt then explicitly forbade exactly that, on my assumption that the raw tree
was sufficient. It is not.

---

## 2. The complete chain a PJM keeper replay actually needs

Rule 32 `[R-SHARD]` (c)(2) documents **one** setup step — *"the prompt names the `DATA PROFILE` so the
shard hydrates only its own ISO's subtree"*. For a PJM per-plant replay there are **four**, and each
one is load-bearing:

### (a) `python3 scripts/hydrate_data.py --profile pjm`
Documented, and necessary. In a **full** clone it is a no-op and says so.

### (b) Install the Python dependencies — with a PyYAML workaround
A bare `pip install -r requirements.txt` **fails** on this image:

    ERROR: Cannot uninstall PyYAML 6.0.1, RECORD file not found. Hint: The package was
    installed by debian.

The working form is `pip install --ignore-installed PyYAML -r requirements.txt`. Worth naming in the
prompt, because the failure looks like a broken requirements file rather than a Debian-packaged
distribution without install metadata.

### (c) **`python3 scripts/regenerate_clean.py`** — REQUIRED, and this is the one that killed shards 3 and 4
`data/clean` is gitignored, derived and disposable, so **it is never in a fresh clone**. The script's
own docstring is unambiguous:

> *"The `data/clean` tree is gitignored (derived and disposable), so it must be rebuilt from
> `data/raw` before the model — or CI — can read it through `scripts.lib.clean_io.read_clean`."*

`MARKET_SIM_USE_CLEAN` is a red herring. It is default-OFF and unset, and the keeper's own
`run_config.json` records no value for it — but that switch governs only the *optional* clean-backed
read paths (`campd`, `zone_assignment`). **Several loaders read `read_clean(...)` unconditionally**,
with no env gate at all: `data/ramp_capability.py`, `data/maxgen_events.py`,
`data/reserve_requirements.py`, `data/capacity_deliverability.py`, `data/nyiso_seam_envelope.py`,
`data/confirmed_retirements.py`. And `scripts/lib/clean_io.py:548/579` raises with the instruction to
*"regenerate from raw — via `scripts/regenerate_clean.py`"*.

So: **the clean tree is a hard prerequisite of any solve, on every ISO, and rule 32(c) does not say
so.** A failure in one datatype does not stop the others (the script is per-datatype and independent),
so a partial failure is not automatically fatal — read it and continue.

### (d) **`python scripts/fetch_pjm_da_virtuals.py`** — REQUIRED for PJM, and it re-downloads
The keeper runs `pjm_da_virtual_bids = True`, which reads
`data/raw/pjm-da-virtuals/hrl_da_incs_decs_<year>_<month>.parquet`. **That directory is gitignored for
licensing reasons** — PJM DataMiner2 carries a non-member redistribution restriction
(`docs/data-licensing.md` §4) — so only its `README.md` is tracked and **the payload is in no clone, in
no container, ever.** Recovery is re-fetch only.

Two traps in it:

* the default fetch is **2023–2025**, so a **2020–2022** replay needs
  `--years 2020 2021 2022` explicitly, and whether DataMiner2 still serves those months is
  **unverified** — nobody has tested it, and a holdout-span replay may simply not be reproducible
  from a cold container;
* `hrl_da_incs_decs` is posted monthly on a **four-month delay**, so the newest months of a current
  year may be absent regardless.

Shard 1 discovered this on its own ("fetching PJM DA virtuals (36mo)") — 36 months is the 2023–2025
default, i.e. it had the training span and would still have been short for the holdout span.

### (e) TWO MORE clean partitions the shard found that I had not
The TP shard (`0bcb1a3c6265cdb253e5447b08288e4aa030bdf7`) hit two further hard raises before the LP,
each from a mechanism the keeper arms, and each fixed by a **narrow per-datatype curate script**
rather than the full regeneration:

| blocker | armed by | resolved by |
|---|---|---|
| `transfer-interface-limits` clean partition absent | `pjm_measured_interface_limits = True` | `scripts/data/curate_transfer_interface_limits.py --isos PJM` → 7 partitions (2019–2025), 87,600 rows each |
| `ramp-capability` clean partition absent | `measured_ramp_capability = True` | `scripts/data/curate_ramp_capability.py --isos PJM` → 749 rows |

Neither "silently no-ops" — both hard-raise, which is the correct behaviour and is why the failure is
legible at all.

### MEASURED: the full regeneration is ~42 minutes, so prefer the narrow curates
Run in this parent container for the record: `scripts/regenerate_clean.py` over all datatypes took
**~42 minutes**, wrote **1.6 GB**, and completed **57 of 58** datatypes (1 failed, non-fatal — the
script is per-datatype and independent). That is a real slice of a 120-minute shard budget, and it is
why the TP shard's approach is the better pattern: it ran **only the two narrow per-datatype curate
scripts the runtime log itself named** (`curate_transfer_interface_limits.py --isos PJM`,
`curate_ramp_capability.py --isos PJM`), taking seconds rather than tens of minutes. **Recommended
recipe: let the runner hard-raise, read which datatype it names, and curate that one** — reserve the
full regeneration for a container that will be reused.

### (f) Dependencies: `uv sync --no-dev` is the better route
The shard's container shipped **no Python dependencies at all** (`numpy` absent). `uv sync --no-dev`
installed the `uv.lock` pins, and they **match the source bundle's recorded environment exactly** —
highspy 1.14.0, numpy 2.4.6, scipy 1.17.1, pandas 3.0.3, pyarrow 24.0.0, pydantic 2.13.4, Python
3.11.15. That is strictly better than the `pip install -r requirements.txt` route in (b), because it
reproduces the environment the bundle was solved in rather than merely a working one.

### THE OPEN QUESTION IS ANSWERED: DataMiner2 DOES still serve 2020–2022
This document originally asked whether `hrl_da_incs_decs` is still available for the holdout span, and
flagged that if not, the PJM 2020–2022 touchpoint would not be reproducible from a cold container.
**It is available.** The shard ran
`scripts/data/fetch_pjm_da_virtuals.py --years 2020 2021 2022 --feeds hrl_da_incs_decs` and got
**36 files, 15 MB, in 577 s**. So the touchpoint's inputs *are* re-obtainable; the corpus stays
gitignored and nothing was committed, so PJM's non-member redistribution restriction is respected.
Two corrections that go with it: `build_pjm_da_virtual_units`
(`src/market_sim/data/virtual_bids.py:335`) has **no fallback and no year gate**, so the committed
touchpoint's own container demonstrably held these parquets — the fetch restores the control's input
rather than adding a new one; and the curate docstring's "committed 2023–2025 raw drops" is **stale**
(the PJM raw feed on disk covers 2019–2026).

### What is NOT needed, checked so nobody over-fetches
Six other PJM-relevant corpora are also README-only at tip, and **none is required to solve**:
`pjm-energy-offers` (only to *re-derive* the midcurve surface; the surface itself,
`_validation-source/pjm_offer_midcurve_condbinned.json`, is committed), `pjm-zonal-lmp`,
`pjm-binding-constraints`, `pjm-ehv-lmp`, `lmp-components`, `PJM/`. The loss surface reads
`data/raw/iso-specific-transmission/PJM_loss_surface.csv`, which **is** committed.

---

## 3. The other failure mode, which is about how CCR shards yield

Shards 1 and 2 ended their turns **mid-task** — one right after printing "starting the LP solve". A
CCR session that yields mid-solve does not reliably resume: both sat `IDLE` with `updated_at` frozen
for ~25 minutes.

**And the parent cannot steer them.** There is **no cross-session messaging route from a CCR parent to
a CCR shard** in this environment:

* `SendMessage` with the session id → *"No agent named '…' is reachable"*; with the session title →
  the same; `ListAgents` → *"No reachable agents — no other Claude session is running on this
  machine"* (a CCR shard runs on its **own** container, so it is never "on this machine");
* the `Claude_Code_Remote` MCP surface exposes `create_session`, `interrupt_session`,
  `archive_session` — and **no `send_message`**, although `create_session`'s own description says
  *"Combine with send_message for fan-out orchestration"*. `ToolSearch` for it returns nothing.

**Consequence for rule 32 `[R-SHARD]` (c): a shard prompt is the ONLY channel there will ever be.** It
cannot be corrected, extended or nudged after launch. Two concrete duties follow:

1. **Say that the turn must not end while the solve is running** — background job plus an in-turn poll
   loop (`sleep`; `tail` the log; `kill -0` the pid) until it exits. Clause (c)(5) already says to
   report in numbers *because* the parent may never read the shard's disk; this is the same fact one
   step earlier.
2. **Do not put a setup step on the FORBIDDEN list unless you have verified it is unnecessary.** A
   forbidden-list entry is unappealable from inside the shard. Mine ("do not regenerate the clean
   data tree", `scripts/regenerate_clean.py` named under FORBIDDEN) converted a 30-second setup step
   into two dead containers.

---

## 3b. THE MEMORY FINDING, which is governance-relevant and is NOT about the emissions dual

Shard 4 was **OOM-killed by the binding memcg**, and its numbers contradict a premise rule 32
`[R-SHARD]` (c)(8) rests on. Full record: `docs/FINDING-pjm-h10-shard-mer-tp-oom-2026-09-19.md`.

```
oom-kill:constraint=CONSTRAINT_MEMCG, task=python
total-vm:31045096kB  anon-rss:13949260kB
```

* **Container ceilings VARY between shards and must be read, never assumed**: this shard's binding cgroup was **13.36 GiB**, while shard 3's own report named **24 GiB** (it reported an OOM at 23.4/24). Rule 32(c)(8)'s instruction to read the binding cgroup rather than `free` is therefore doing real work — but the *value* it quotes is this environment's, not a constant.
* **13,949,260 kB = 13.30 GiB against a 13.36 GiB ceiling** — the *identical* 13.30 GiB figure rule
  32(c)(8) already records for the miso-252/253 incident. PJM per-plant across 8 zones needs
  **>13.3 GiB anon in the P0→P1 seam alone**.
* It died **after** 2020 P0 completed and printed its objective (`Solve 574.607 s`, 382,243 simplex
  iterations), during the P0→P1 seam. The python process held essentially the whole ceiling; other
  processes in the cgroup were under 2 MB, so shard tooling did not cause it.
* **THE RUNNER'S SWAP MITIGATION WAS INERT.** A 5.0 GiB swapfile was active and `/proc/swaps` showed
  **Used = 0** at the moment of the kill; the kernel OOM-killed under `constraint=CONSTRAINT_MEMCG`
  rather than swapping (`memory.memsw.limit_in_bytes` unreadable in this cgroup). Preflight had
  *already said so*, verbatim: *"ceiling+swap 18.4 GiB is below the 24 GiB target; a per-plant ISO-year
  LP (MISO, PJM) may be OOM-killed here"*, and disk had only 7.0 GiB free so a larger swapfile was not
  available. **Rule 32(c)(8) states that provisioning a swapfile is what lets a per-plant PJM/MISO year
  fit here. On this container it did not, and the runner predicted its own failure and ran anyway.**
* **The MER attribution is CONFOUNDED and stays open, and the shard said so itself.** The dual cannot
  be toggled at this HEAD without a code edit the shard was forbidden to make; the container was
  flagged under-provisioned before the dual was reached. **Nobody may cite this as evidence that the
  emissions dual is too expensive at per-plant scale** — it is equally consistent with PJM per-plant
  simply not fitting in a 13.36 GiB cgroup, with or without the dual. No retry was spent, correctly:
  the failure is deterministic and an identical re-run would only reproduce it.
* One thing it *did* confirm — the 2020 build logged `year table 2020`, i.e. 2020 now draws its own
  PJM midcurve offer table instead of the pooled 2023–2025 fallback, **exactly the HEAD change the
  parent's zero-LP drift audit predicted** (PRECOMMIT §3). No scored number survived to quantify it.

---

## 4. Proposed amendment to rule 32 `[R-SHARD]` (c) — for the owner, not self-applied

Not written into `CLAUDE.md` by this session: rule 32 is governance and the owner amends it.
Recommended, as a new clause (c)(9) or an extension of (c)(2):

> **(c)(9) A SHARD PROMPT CARRIES THE WHOLE SETUP CHAIN, NOT JUST THE DATA PROFILE, AND NAMES NO
> SETUP STEP AS FORBIDDEN.** Hydration is necessary and not sufficient. A solve also needs the
> dependency install, **`scripts/regenerate_clean.py`** (the `data/clean` tree is gitignored and
> several loaders read it with no env gate, so it is never present in a fresh container), and any
> **licensing-gitignored corpus the run's own config reads** — for PJM with
> `pjm_da_virtual_bids` armed that is `scripts/fetch_pjm_da_virtuals.py`, with `--years` matching the
> bundle's span, since the default covers 2023–2025 only. **A shard's turn may not end while its
> solve is running**, and the prompt says so: background job plus an in-turn poll loop, because the
> parent has no way to message it afterwards.

**A SECOND amendment the memory finding argues for, also the owner's call:** rule 32(c)(8) tells a
lane to run the runner unmodified and report the preflight and memory-peak lines, on the premise that
the runner's swapfile is what makes a per-plant PJM/MISO year fit. §3b shows a container where the
swapfile was active, unused, and irrelevant — and where **preflight printed a warning predicting the
OOM and the run proceeded anyway**. Worth considering: when preflight's own `ceiling+swap` falls short
of its target for a per-plant ISO, the runner should **refuse to start** and say so, rather than
spending ~10 minutes of setup and ~10 minutes of P0 to be killed. That converts a wasted container
into an immediate, legible stop — which is what rule 32's "a shard that stops with a clear report is a
SUCCESS" is for.

**The open question this document originally raised is ANSWERED and no longer open:** DataMiner2 still
serves `hrl_da_incs_decs` for 2020–2022 (36 files, 15 MB, 577 s), so the PJM holdout touchpoint's
inputs *are* re-obtainable from a cold container. See §2's DA-virtuals subsection.

---

## 5. What this cost, stated plainly

Four containers and roughly 45 minutes of wall clock produced **no MER bundle**. The zero-LP
reconciliation this session was chartered for is complete and committed regardless — it needed no
solve. The MER series PJM owes the marginal-abatement page, and the empirical check on the G-DRIFT
form-4 verdict, **remain outstanding**, and the generation-3 shards may or may not clear step (d).
Cost to reproduce from here: one shard per span, ~10–20 min of setup plus the span's solve, **provided
the DA-virtuals fetch works for that span.**
