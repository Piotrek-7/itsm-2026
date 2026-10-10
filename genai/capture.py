# ai-generated: 100% - Codex captures spans from a real local inference, without manufacturing attributes.
import json
import os
from pathlib import Path
from importlib.metadata import version

from openai import OpenAI
from opentelemetry import trace
from opentelemetry.instrumentation.genai.openai import OpenAIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult


class SDKJsonExporter(SpanExporter):
    def __init__(self, destination):
        self.destination = destination
        self.spans = []

    def export(self, spans):
        self.spans.extend(json.loads(span.to_json()) for span in spans)
        self.destination.write_text(json.dumps(self.spans, indent=2) + '\n')
        return SpanExportResult.SUCCESS


output = Path(os.environ.get('GENAI_OUTPUT', '/out'))
output.mkdir(parents=True, exist_ok=True)
provider = TracerProvider(resource=Resource.create({'service.name': 'svcdesk-genai-experiment'}))
provider.add_span_processor(SimpleSpanProcessor(SDKJsonExporter(output/'spans.json')))
trace.set_tracer_provider(provider)
OpenAIInstrumentor().instrument(tracer_provider=provider)
base_url = os.environ.get('GENAI_BASE_URL', 'http://lab3-local-model:8080/v1')
client = OpenAI(base_url=base_url, api_key='local-not-a-secret', max_retries=0, timeout=120)
response = client.chat.completions.create(
    model='smollm2-135m',
    messages=[{'role': 'user', 'content': 'In one short sentence, explain why monitoring latency is useful.'}],
    max_tokens=40, temperature=0.0,
)
provider.force_flush()
provider.shutdown()
(output/'response.json').write_text(response.model_dump_json(indent=2)+'\n')
(output/'versions.json').write_text(json.dumps({name:version(name) for name in [
    'openai', 'opentelemetry-sdk', 'opentelemetry-instrumentation-genai-openai'
]},indent=2)+'\n')
print('Captured real response and automatically instrumented spans')
print(response.choices[0].message.content)
