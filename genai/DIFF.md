---
lab3_genai_diff:
  instrumentation: opentelemetry-instrumentation-genai-openai 1.2b0; opentelemetry-sdk
    1.45.0; openai 3.19.2
  spec_ref: semantic-conventions@v1.41.1
  attributes:
  - name: gen_ai.operation.name
    emitted: true
    in_spec: true
    stability: development
  - name: gen_ai.provider.name
    emitted: true
    in_spec: true
    stability: development
  - name: gen_ai.request.max_tokens
    emitted: true
    in_spec: true
    stability: development
  - name: gen_ai.request.model
    emitted: true
    in_spec: true
    stability: development
  - name: gen_ai.request.temperature
    emitted: true
    in_spec: true
    stability: development
  - name: gen_ai.response.finish_reasons
    emitted: true
    in_spec: true
    stability: development
  - name: gen_ai.response.id
    emitted: true
    in_spec: true
    stability: development
  - name: gen_ai.response.model
    emitted: true
    in_spec: true
    stability: development
  - name: gen_ai.usage.input_tokens
    emitted: true
    in_spec: true
    stability: development
  - name: gen_ai.usage.output_tokens
    emitted: true
    in_spec: true
    stability: development
  - name: gen_ai.request.top_p
    emitted: false
    in_spec: true
    stability: development
  - name: gen_ai.request.seed
    emitted: false
    in_spec: true
    stability: development
---
<!-- ai-generated: 100% - Codex compared an actual automatically instrumented local model call with the pinned registry. -->
# Instrumentation versus semantic conventions

The trace was captured on 10 October 2026 by `capture.py`, using OpenAIInstrumentor around a real synchronous chat completion. The exporter only serializes SDK spans; it does not construct or rewrite their attributes. `response.json` retains the actual response, including usage. No API key or private user data was sent: this was a synthetic prompt to a local SmolLM2 model.

All ten emitted `gen_ai.*` attribute names occur in the [v1.41.1 registry](https://github.com/open-telemetry/semantic-conventions/blob/v1.41.1/model/gen-ai/registry.yaml), with development stability. Their names agree with that snapshot, but values need interpretation: `gen_ai.provider.name=openai` describes the instrumented client protocol, not the company hosting this inference. Our actual server is llama.cpp on this machine, running SmolLM2, and does not contact OpenAI. Grouping costs by that provider value alone would therefore misclassify this call.

The request and response model both identify `smollm2-135m`. Input and output token counts are present (42 and 26); this is usage reported by this model's tokenizer, not a currency charge or a count comparable across all tokenizers. The response finish reason is `stop`, and max_tokens is 40. The generated sentence ended naturally before that cap. Temperature 0 is recorded because the request set it explicitly. Top-p and seed are in the spec but absent from this request and export; dashboards must tolerate missing optional attributes rather than assume zero.

There are no prompt/completion text attributes or events in this export. The prompt is reproducible in the script and the output in the separate response artifact; telemetry should not need to contain user text to support latency and usage panels. The non-GenAI `openai.response.system_fingerprint` attribute and `server.address` identify protocol/server details, not additional `gen_ai.*` keys. Every emitted GenAI key is listed in the front matter, including IDs that are unsuitable as metric labels. All listed attributes remain development stability in the pinned snapshot, so upgrades need an explicit schema review and must not silently break production queries.

## Reproduce the real call

Model: `bartowski/SmolLM2-135M-Instruct-GGUF`, revision `09816acd5d99df7be770d85ea30822623dab342c`, file `SmolLM2-135M-Instruct-Q4_K_M.gguf` (105454432 bytes), downloaded from Hugging Face. Server image: `ghcr.io/ggml-org/llama.cpp@sha256:bf3da52e92c083472b3d1c9f9da081f423ab9def95a87ec4bba51940382d75fd`. Mount the model directory read-only at `/models` and start it on Docker network `lab3-genai` with container name `lab3-local-model`, arguments `--model /models/SmolLM2-135M-Instruct-Q4_K_M.gguf --alias smollm2-135m --host 0.0.0.0 --port 8080 --ctx-size 1024 --threads 2`.

```sh
docker build -t svcdesk-genai-experiment genai
docker run --rm --network lab3-genai -v "$PWD/genai:/out" svcdesk-genai-experiment
```

The model is stopped before HTTP latency measurements so inference does not compete for the VM's CPUs. The local model is an experiment, not a dependency of `svcdesk` or a fake OpenAI server with hardcoded replies.
