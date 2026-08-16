# miso-160 close-out manifest — what is on this branch vs what rides the local commits

**Session outcome: MISO KEEPER PROMOTED → `2026-08-16-miso-160-wefor-shape`**
(PREREG §7(a) met; determination NOT-YET on C3a-2025 alone at −12.5 %; full
record in `results/calibration/FINDING-miso160-measured-summer-wefor-shape-2026-08-16.md`,
on this branch).

## Already on this branch (each blob byte-verified at push time)

- PREREG (blob 57d2b8b1), data-ask §9 owner decision (e4972476)
- implementation patch pieces 1–3 + BLOBS.txt + APPLY.md + matrix-base-row.txt
- FINDING (cb5599b4), both registry sidecars (7b82a7b6 / 491f4a4a),
  `scripts/gen_miso160_attestation.py` (4677926b), this file

## Riding the LOCAL commits in the authoring container (NOT yet on this branch)

The authoring container holds the full close-out as ordinary git commits on
`claude/miso-backcast-calibration-nk4zhj` — **re-signed 2026-08-16 (SSH
signatures, committer noreply@anthropic.com); trees and blobs byte-identical
to the originally-manifested ones, only the commit ids moved**:

```
918de82  implementation (== patch pieces 1-3 + matrix row + anchors; tree 72cd10f3)
9b8d5c6  transfer artifacts (tree b0b4fad1)
52905f9  control bundle miso160_wefor_A (tree 36b029cf)
92f56bc  promotion close-out (tree abf51bb8299cb516550ae55d6fa7511ff6093438)
 a06610a  close-out pointer (tip; tree ef96ab2a)
```

**Preferred delivery: resume a session in the SAME container with working
git and `git push --force-with-lease origin claude/miso-backcast-calibration-nk4zhj`.**
The local history contains BYTE-IDENTICAL copies of every file this branch's
API commits carry (all verified by blob sha at push time), plus everything
below — so replacing the API-commit history with the local history loses
nothing. If the container is gone, apply the patches per APPLY.md and rebuild
the rest (the bundles need a re-solve: replay_keeper on miso159_cod_B, no
--set for the control, --set summer_wefor_share_override=1.0599 for the arm;
the control is bit-reproducible — this session measured 0/70,080 differing
price cells against the committed keeper).

### Blob manifest of the promotion commit (verify after any delivery path)

```
4bf0a27ac2fc82e46d6e14170cd71e839d7c85bf docs/calibration-log/miso.md
5362f1e286c351185d788a788e01ad7278c7570e docs/codebase-site/data/mechanism-matrix/MISO.js
fc888bc4564f215ea764e95116915b30134a785e docs/mechanism-testing-matrix.md
b0071e369b1050d2aabd5ac5e9bc703f1d6f5482 frontend/data/backcast/keepers/MISO.json
7b82a7b60ae7a7ada2056b3778a7eb9f6269b0c8 frontend/data/backcast/registry/2026-08-16-miso-160-control.json
491f4a4a4bfe2232f78f1bcb979f4f5b5d12518b frontend/data/backcast/registry/2026-08-16-miso-160-wefor-shape.json
8b88681afa4be8fba19f97cf5a3a44ea1e9cd929 frontend/data/backcast/runs/2026-08-16-miso-160-control.js
3f14cc7be038feaf1926a7b28098f348928de04e frontend/data/backcast/runs/2026-08-16-miso-160-wefor-shape.js
c309ba5bc272ff65557a7b462be59e4b317de4b9 frontend/data/backcast/status/MISO.js
cb5599b4347707f94a3d3b2b0332bac764ba9d3d results/calibration/FINDING-miso160-measured-summer-wefor-shape-2026-08-16.md
986b5bbfb83096a878be4377661193c002dc3508 results/calibration/miso160_wefor_A/calibration_attestation.json
ca46f759273c7c21fdfc4511931f48a918034402 results/calibration/miso160_wefor_A/metrics.json
21fe9af6727dea02ee878c6d1d6e35564e87aa0a results/calibration/miso160_wefor_B/calibration_attestation.json
1c41084f4ab11d7750e2bf1f1d76f89e3051a792 results/calibration/miso160_wefor_B/hourly/class_hourly_2023.parquet
4a395c4aa96331396689b98b0afcc66e5f5f4818 results/calibration/miso160_wefor_B/hourly/class_hourly_2024.parquet
48fe5fc472bf6a4e8591e57a9178ed53f05fb830 results/calibration/miso160_wefor_B/hourly/class_hourly_2025.parquet
e17591cd8e9654fb60071172f99b99885f00d972 results/calibration/miso160_wefor_B/hourly/reserve_family_2023.parquet
826767d473f5c869168d932289d8a6e9e8d25197 results/calibration/miso160_wefor_B/hourly/reserve_family_2024.parquet
aebcdeb323602dfc4c81d348328b030eb75c30cf results/calibration/miso160_wefor_B/hourly/reserve_family_2025.parquet
9824885485d6377806d3cdc82e2313c907d557a2 results/calibration/miso160_wefor_B/hourly/storage_2023.parquet
837e010d465ffc10625d9733bcd221152a005032 results/calibration/miso160_wefor_B/hourly/storage_2024.parquet
eb9c83821096d1c4cc7e71ff65dc1a9bd9098cd9 results/calibration/miso160_wefor_B/hourly/storage_2025.parquet
ff316f1620c980e865122f7ce2f86735f62bba56 results/calibration/miso160_wefor_B/hourly/system_2023.parquet
e176feb90c432849564f1b9dc98bfdf160020c2d results/calibration/miso160_wefor_B/hourly/system_2024.parquet
294cc3ffc26e486d237b176813102b87c79588f8 results/calibration/miso160_wefor_B/hourly/system_2025.parquet
fb3bee601cb68e4a097433c8c00ef6e5e545bdbb results/calibration/miso160_wefor_B/legitimacy_diagnostics.json
797e3c82c441a2e574b4bd3d1e59ce899d01d696 results/calibration/miso160_wefor_B/meta.json
1105e2a0c6fa1296b5e8b0efb65dddc49db582fc results/calibration/miso160_wefor_B/metrics.json
83b3e97ea77d28febb5477c9be1d8e73659f6479 results/calibration/miso160_wefor_B/run_config.json
4677926be8c8353600e9cab1560297cf3751f6e2 scripts/gen_miso160_attestation.py
```

(The control bundle miso160_wefor_A's parquet/meta/run_config blobs are in
the control-bundle commit; `git diff-tree -r 52905f9` lists them. The
FINDING, both sidecars and the gen script above are ALSO directly on this
branch — same blobs, verified. APPLY.md's provenance line cites the
pre-resign commit ids f3c3f90/f8c93af; the patch bytes are identical, so
apply instructions are unaffected.)

## What the dashboard needs before the runs are LIVE

The run payloads (`frontend/data/backcast/runs/2026-08-16-miso-160-*.js`,
~1.5 MB each) and the bundle hourly parquet are in the local commits only —
a sidecar without its payload is invisible in the Run Explorer, so **the
rule-15 registration is not fully delivered until the local commits land.**
No bench/ files changed (the parts re-rendered byte-identical). After the
push, the Pages deploy rebuilds manifest/benchmark/completeness from
sidecars — no generated files need committing.
