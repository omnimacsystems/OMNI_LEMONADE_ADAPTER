# Third-party boundary

Only original Python code, synthetic data, configuration manifests and documentation are
distributed here. The exact chat template is read from the operator-provided verified GGUF,
not bundled. No Lemonade, llama.cpp, CUDA, Microsoft/NVIDIA DLL or model weight is included.

Python dependencies installed separately by the operator:

| Component | Pinned version | License |
|---|---|---|
| Jinja2 | 3.1.6 | BSD-3-Clause |
| MarkupSafe | 3.0.3 | BSD-3-Clause |

Their distributions retain their own copyright/license notices. They are not vendored here.
External runtime/model licensing remains applicable to each official distribution. Our
Apache-2.0 license applies only to original project material, never to third-party components.
No conclusion about binary redistribution rights is needed or asserted by this source-only
package; in particular it does not redistribute libomp140.x86_64.dll.

Official sources: https://github.com/pallets/jinja and https://github.com/pallets/markupsafe .
Runtime/model source URLs and exact revisions are in config/runtime-lock.json.

Build-only dependency installed separately: setuptools 80.9.0, MIT license. Python 3.12 is an external prerequisite under the Python Software Foundation License; it is not bundled. The clean packaging check used Python 3.12.14; it made no inference calls and does not change the previously qualified inference configuration.
