> Historical technical-run guide, preserved as documentation. The later human acceptance and completed 5×3 campaign are recorded in the root README and reports. Commands/runtime setup remain applicable.

# OMNI_LEMONADE_ADAPTER

Standalone synthetic qualification demonstrator, version 0.1.0. **Not a qualified agent product.**
No parent application, private data, persistent memory, or external service is required.
Original code: Apache-2.0. No third-party binaries or model weights are distributed.

## What the demonstration proves

An explicitly pinned Lemonade configuration renders the exact template from its verified GGUF,
tokenizes the UTF-8 prompt, and sends the identical string to completions. A bounded local action
protocol permits only `list_documents` and `read_document(document_id)` over synthetic documents.
A separate deterministic verifier checks the exact answer, supporting quote, source ID and proof
that the document was actually read. The finish gate alone permits PASS.

`HOLD` is a preserved failure, not success. A successful negative scenario means the guard worked;
the agent's final verdict remains HOLD. No automatic retry, memory write, shell, browser, arbitrary
file access, remote endpoint or agent execution capability is exposed.

## Requirements and acquisition

Windows x64, NVIDIA CUDA GPU supporting sm_86 (technical canary: RTX 3060 Ti), Python 3.12,
Jinja2 3.1.6 and MarkupSafe 3.0.3. Install Python dependencies in your own virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Obtain the two official distributions and exact model revision linked in
`config/runtime-lock.json`. Compare archive SHA-256 before extracting with your chosen archive
utility; never replace a missing version with a newer version. Obtain CUDA/driver/system
prerequisites from their official suppliers. Do not disable antivirus or create exclusions.
The adapter does not download, install, launch or replace runtime dependencies.

Extract distributions outside this source directory. Keep the complete backend together.
The runtime lock verifies all 58 files from that backend distribution plus `lemond.exe`, and
the entire GGUF before a run. A missing or changed artifact produces preflight HOLD.

## Start an isolated Lemonade instance (operator action)

Create separate cache/config directories outside any other application's runtime. Use the
sample `config/lemonade.example.json`, replacing the three `REPLACE_...` values with absolute
local paths. Put only the pinned GGUF in that model directory. Save it as `config.json` in
your isolated configuration directory. Execute the pinned `lemond.exe` with positional arguments
`<isolated-cache-directory> <isolated-config-directory>`.

The fixed example endpoint is `http://127.0.0.1:13315`; never share an occupied endpoint or
adopt an unknown existing process. Through this Lemonade endpoint, explicitly POST `/v1/load`:

```json
{"model_name":"extra.Qwen3-4B-Instruct-2507-Q4_K_M","ctx_size":4096,"llamacpp_backend":"cuda","llamacpp_args":"--no-context-shift --fit off --parallel 1 --seed 4242 -ngl 99 -lv 4"}
```

Check `/v1/health`, GPU offload in the runtime log, and the expected process paths. This adapter
does not claim that health metadata is cryptographic process attestation: the local operator
and local server are trusted. Its client has no access to backend port 8001.

## One explicit technical run

From this directory (or a copy at any other location):

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m adapter run NORMAL_SUCCESS --endpoint http://127.0.0.1:13315/v1 --lemonade-dir "<extracted Lemonade directory>" --backend-dir "<extracted backend directory>" --model "<model directory>/Qwen3-4B-Instruct-2507-Q4_K_M.gguf" --output "<report directory>"
```

Replace only the scenario argument to explicitly run `TRUNCATION_OR_BUDGET_HOLD` or
`LOOP_OR_FAILURE_SIGNATURE`. The program never runs another scenario automatically.

* NORMAL_SUCCESS: read DOC_A, answer the cube color with the exact supporting sentence.
* TRUNCATION_OR_BUDGET_HOLD: oversized synthetic prompt; tokenizer may run, generation must not.
  Output truncation is additionally covered by injected component tests and the runtime canary.
* LOOP_OR_FAILURE_SIGNATURE: deliberately instruct the model to repeat the same read action.
  The second identical action must be rejected before tool execution. This is fault injection,
  not an estimate of naturally occurring model loops.

## Budgets and reports

4096 context, 512 output tokens including provider-accounted termination, 256 margin;
maximum 3 generations, 2 local tool executions, 120 seconds per trajectory, zero retries.
Runtime hash preflight occurs before the trajectory clock. Every call receives the remaining
timeout and the deadline is checked after response receipt. This is a cooperative application
deadline, not OS process isolation or a guaranteed server-side cancellation mechanism.

Stop/length is checked before parsing any action. Token count discrepancy produces HOLD even
if the answer looks correct. Provider output-token usage is authoritative: retokenizing only
visible text can omit termination tokens. Hidden non-default sampling is avoided by explicitly
passing seed, temperature, top_p, top_k and min_p; the complete runtime build remains locked.

Each new UUID run directory preserves prompt bytes, requests, raw output, response objects,
token counts, attributed tool results, verifier result, final verdict and monotonic trajectory.
`SEAL.json` hashes the report and evidence. It detects accidental edits; it is **not** a digital
signature or a write-once store. Never overwrite a run to hide a failure.

```powershell
.\.venv\Scripts\python.exe -B -m adapter verify-seal "<run directory>"
```

Public reports contain synthetic content only. Machine-specific command transcripts and paths
belong outside the distribution. Review artifacts before public publication.

## Explicit resume and acceptance

HOLD has no automatic resume or continuation. An operator can inspect the preserved reason,
correct a configuration in a separately versioned candidate, and explicitly start a new run.
No failed response is promoted to a successful result. V1 does not implement an autonomous agent.

The official 5 runs × 3 scenarios campaign is **not authorized until human acceptance**.
`verified_success_rate` stays null. Technical runs do not establish model reliability, challenge
eligibility, supply-chain safety, hard OS confinement, cross-device determinism or GPU portability.
No public repository has been published.

Rollback: stop the adapter; shut down only your owned isolated Lemonade via
`POST /internal/shutdown`; retain reports and source snapshot. No host product is changed.
