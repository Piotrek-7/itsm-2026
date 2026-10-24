# ai-generated: 100% - Codex records real calls to the unmodified course MCP server.
"""Record the tools used interactively by Codex, not a fabricated autonomous-model run."""
import asyncio
import json
import os
import sys
from pathlib import Path
from mcp import Client, StdioServerParameters

async def main():
    config = json.loads(Path(sys.argv[1]).read_text())
    transcript = Path('ai-rca/second/transcript.md')
    env = {**os.environ, 'PROMETHEUS_URL': 'http://127.0.0.1:19090'}
    server = '/materials/agent/prom_mcp.py'
    async with Client(StdioServerParameters(command=sys.executable, args=[server], env=env)) as client:
        for call in config:
            result = await client.call_tool(call['name'], call['arguments'])
            output = '\n'.join(c.text for c in result.content if getattr(c, 'type', '') == 'text')
            event = {**call, 'result': output, 'error': result.is_error}
            with transcript.open('a') as f:
                f.write(f'\n### Tool `{call["name"]}`\n\n```json\n{json.dumps(call["arguments"],indent=2)}\n```\n\n```json\n{output}\n```\n')
            with transcript.with_suffix('.jsonl').open('a') as f:
                f.write(json.dumps(event)+'\n')
            print(json.dumps(event), flush=True)
            if result.is_error:
                raise RuntimeError(output)

if __name__ == '__main__':
    asyncio.run(main())
