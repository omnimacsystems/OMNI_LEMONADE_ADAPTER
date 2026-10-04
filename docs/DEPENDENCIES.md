# Official dependency acquisition

No binaries are distributed. Do not auto-upgrade or substitute.

- Official archive: https://github.com/lemonade-sdk/lemonade/releases/download/v2026.39.1/lemonade-embeddable-2026.39.1-windows-x64.zip
  SHA-256: `235c2361be3a9729a06b92c97e40a9530ebb8e5088bd3334524472d6da7fbbca`
- Official archive: https://github.com/lemonade-sdk/llama.cpp/releases/download/b10820/llama-b10820-windows-cuda-sm_86-x64.7z
  SHA-256: `61995f6ccefee7a09a78a356518aa1923388781b22fb0e4fe53854f7a6cbe430`

- Model revision: https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/tree/96a21cbb3c5b717d3cdeffc5eed8a6e120d2a1a3
- File: `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`
- GGUF SHA-256: `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597`
- Template SHA-256: `c979e0e71a3e21b8f208e6ab120d5cb29327885f29d2a8b18fda67a723798e18`

The template is extracted at runtime from the verified GGUF, not included in the repository. Runtime lock contains 59 file hashes. Obtain Python from https://www.python.org/ and NVIDIA drivers from https://www.nvidia.com/Download/index.aspx . Obtain Jinja2 3.1.6 and MarkupSafe 3.0.3 from their official PyPI distributions. Pinning is not a malware clearance. Respect all vendor licenses; Apache-2.0 here covers only original code.
