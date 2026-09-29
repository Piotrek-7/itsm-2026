# ai-generated: 100% - Codex wrote a reproducible public GitHub receipt capture and calculation.
"""Capture all receipted submissions using gh api; no access to private data is needed."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

ROOT = Path(__file__).resolve().parents[1]
QUERY = 'repos/swasik/itsm-2026-submissions/issues?state=all&labels=receipted,kind:submission&per_page=100'


def capture(gh='gh'):
    # Use the anonymous scheme accepted by the public API, rather than a personal token.
    args = [gh, 'api', '--paginate', '--slurp', '-H', 'Authorization: anonymous', QUERY]
    env = dict(os.environ)
    env['GH_TOKEN'] = 'public-read-only'
    payload = subprocess.check_output(args, env=env)
    captured_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    pages = json.loads(payload)
    issues = [issue for page in pages for issue in page if 'pull_request' not in issue]
    count, rework = 0, 0
    attempts = {}
    for issue in issues:
        labels = {label['name'] for label in issue['labels']}
        if not {'receipted','kind:submission'} <= labels:
            continue
        # GitHub issue forms keep the submitted tag in its own Markdown section.
        tag = re.search(r'^### Tag\s*\n+([^\n]+)', issue['body'] or '', re.MULTILINE)
        match = re.fullmatch(r'lab\d+/v([1-9]\d*)', tag[1].strip()) if tag else None
        if not match:
            raise ValueError(f'Cannot determine attempt tag for issue {issue["number"]}')
        version = int(match[1])
        attempts[version] = attempts.get(version, 0) + 1
        count += 1
        rework += version >= 2
    if not count:
        raise ValueError('No submissions captured')
    path = ROOT/'evidence/class-submissions.json'
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(payload)
    metadata = {
        'source': shlex.join(['gh'] + args[1:]),
        'captured_at': captured_at,
        'capture_path': 'evidence/class-submissions.json',
        'sha256': hashlib.sha256(payload).hexdigest(),
        'deployments': count, 'rework_deployments': rework,
        'deployment_rework_rate': float((Decimal(rework)/count).quantize(Decimal('0.000001'),rounding=ROUND_HALF_UP)),
    }
    (ROOT/'rework-class.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(metadata,indent=2))
    print('Counts by attempt:',attempts)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--gh',default='gh')
    capture(parser.parse_args().gh)
