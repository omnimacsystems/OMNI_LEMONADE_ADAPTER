# OMNI_LEMONADE_ADAPTER

**A bounded local-agent qualification harness for Lemonade.**

A good answer is not enough. A local agent also needs to stop when its budget is insufficient or its actions repeat. This source-only demonstration tests both correct completion and correct refusal to continue.

Open [Human demo](https://omnimacsystems.github.io/OMNI_LEMONADE_ADAPTER/) for the rendered overview, or [Technical evidence](https://omnimacsystems.github.io/OMNI_LEMONADE_ADAPTER/reports/) for the qualification reports.

## Results, with scope

| Scenario | Observed result | Expected behavior verified |
|---|---|---|
| NORMAL_SUCCESS | Exact sourced answer; verifier and finish gate PASS | 5/5 |
| BUDGET_PROTECTION (`TRUNCATION_OR_BUDGET_HOLD`) | HOLD before generation | 5/5 |
| LOOP_PROTECTION (`LOOP_OR_FAILURE_SIGNATURE`) | HOLD before repeating a tool action | 5/5 |

15 runs, 20 generations, zero retries. Human acceptance of the technical demonstration: PASS.
**Functional success** means a correct supported answer. **Expected HOLD** means execution was correctly blocked, not that an answer succeeded. **Qualification** applies only to this exact configuration and these synthetic scenarios. Five runs with the same seed on one machine are not independent random trials and do not establish general model reliability.

## Architecture

Frozen configuration → synthetic corpus → exact GGUF template → prefill budget → Lemonade tokenize/completions → local actions → loop signature → candidate or HOLD → independent deterministic verifier → finish gate → sealed run report.

Lemonade is the sole inference/API gateway. The client contacts only an explicit loopback endpoint. There is no direct backend bypass, remote API or fallback. Only `list_documents` and `read_document(document_id)` are exposed; document IDs never become arbitrary paths. Operator report writing is not an agent tool.

## Qualified configuration

- Lemonade **2026.39.1**.
- llama.cpp **b10820**, CUDA **sm_86**, Windows x64; fingerprint `b10820-74a7c897f`.
- `unsloth/Qwen3-4B-Instruct-2507-GGUF`, revision `96a21cbb3c5b717d3cdeffc5eed8a6e120d2a1a3`.
- File `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`, Q4_K_M.
- Template SHA-256 `c979e0e71a3e21b8f208e6ab120d5cb29327885f29d2a8b18fda67a723798e18`.
- Seed 4242, temperature 0.2, top_p 0.9, top_k 20, min_p 0.05.
- Context 4096; output reservation 512, termination included; margin 256.
- Maximum 3 model calls, 2 tool calls, 120 seconds per trajectory; retry 0.

Exact executable/data hashes are in [runtime-lock.json](config/runtime-lock.json). [FROZEN_FILES.json](configuration/FROZEN_FILES.json) pins the accepted code, corpus, verifier, scenarios and configuration. Packaging does not change them. Any change requires a new configuration and qualification.

## Dependencies and installation

Prerequisites: Windows x64, Python 3.12, an NVIDIA sm_86-compatible GPU and official driver (qualified host: RTX 3060 Ti, 8 GiB). Cross-machine performance is not established.

1. Obtain the **exact official archives and GGUF** listed in [dependencies](docs/DEPENDENCIES.md).
2. Verify their SHA-256 **before extraction/use**, e.g. `Get-FileHash -Algorithm SHA256 <file>`.
3. Extract to dedicated operator-owned directories outside this source tree. Keep the complete backend distribution together. Do not copy individual DLLs from other installations.
4. Create an isolated Python environment and install the pinned requirements:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Optional package installation uses `pyproject.toml`: `.\.venv\Scripts\python.exe -m pip install .`. Its build tool is pinned separately; it does not change agent settings. No dependency is bundled.

**Hash divergence or unavailable exact version → STOP. Never substitute automatically.** No antivirus exclusion is required or created by this project.

Follow [runtime operations](docs/RUNTIME_OPERATIONS.md) to start the dedicated Lemonade instance, set the offline/no-fetch configuration and explicitly load the pinned model. The harness itself does not start, install or update servers. Its runtime preflight verifies files, model/template hash, health, loaded identity and context before inference.

## Run a scenario

From the source directory, set paths to your own separately acquired dependencies:

```powershell
$ld = '<extracted Lemonade directory>'
$bd = '<extracted backend directory>'
$model = '<model directory>/Qwen3-4B-Instruct-2507-Q4_K_M.gguf'
.\.venv\Scripts\python.exe -B -m adapter run NORMAL_SUCCESS --endpoint http://127.0.0.1:13315/v1 --lemonade-dir $ld --backend-dir $bd --model $model --output ./new-runs
```

Use `TRUNCATION_OR_BUDGET_HOLD` or `LOOP_OR_FAILURE_SIGNATURE` as the scenario argument for the other cases. The friendlier names on the demo page are labels only. No qualified scenario has been renamed.

## Reproduce the 5×3 campaign

Explicit operator action; creates new runs and never overwrites the published evidence:

```powershell
foreach ($s in @('NORMAL_SUCCESS','TRUNCATION_OR_BUDGET_HOLD','LOOP_OR_FAILURE_SIGNATURE')) {
  foreach ($trial in 1..5) {
    .\.venv\Scripts\python.exe -B -m adapter run $s --endpoint http://127.0.0.1:13315/v1 --lemonade-dir $ld --backend-dir $bd --model $model --output ./new-runs
    if ($LASTEXITCODE -eq 2) { throw 'Runtime preflight HOLD: stop campaign' }
  }
}
```

Do not retry failed trials. Retain every report, inspect all exit codes and expected outcomes. Exit 0 means the **scenario** behaved as expected; negative cases still have final verdict HOLD. Runtime preflight failure is exit 2. Other failed scenarios are exit 1.

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m adapter verify-seal '<run directory>'
```

The exact prompt P is locally rendered, sent unchanged to tokenize and completions, and saved with its hash. Any accounting divergence or truncated output yields HOLD. The deterministic verifier never calls a model. Every result retains raw output, functional candidate, verifier verdict and final verdict separately.

## Evidence and limitations

[Campaign summary](reports/STATUS.json), [15 run index](reports/CAMPAIGN_RUNS.json), [qualified configuration snapshot](reports/QUALIFIED_AGENT_CONFIGURATION_V1.json), individual trajectory and raw response files are available under reports. Original synthetic evidence bytes and run seals are unchanged. Private machine logs and operator paths are excluded; [provenance](reports/PROVENANCE.json) records the selection.

- Budget scenario tests **prefill refusal**, not live output truncation during this 5×3 campaign.
- Loop scenario deliberately induces repetition; it does not measure natural loop frequency.
- Same seed, same machine/build; no cross-hardware determinism claim.
- Deadline is cooperative HTTP timeout, not guaranteed server-side cancellation or hard OS confinement.
- Hash seals are unsigned integrity checks, not immutable storage or trusted attestation.
- Local operator/server are trusted. No supply-chain safety or challenge eligibility verdict is claimed.
- Archived run `mode=TECHNICAL_SINGLE_RUN` and source configuration status retain their original wording. The campaign index and qualification snapshot provide the later 5×3 classification without rewriting history.

This project contains no private agent data and needs no parent platform installed. The directory names `harness/`, `verifier/`, `scenarios/`, `configuration/` are navigation surfaces pointing to the frozen implementation, not duplicated or moved code.

## License and publication

Original code: Apache-2.0; see LICENSE and THIRD_PARTY_NOTICES.md. No Lemonade, llama.cpp, CUDA, Microsoft/NVIDIA DLLs or model weights are redistributed. Third-party licenses still apply when obtaining those dependencies.

This is a publication **candidate** only. No repository or submission has been published. See the [video storyboard](docs/VIDEO_STORYBOARD.md). Shut down only your owned test server with `POST /internal/shutdown` when finished; preserve all run evidence.
