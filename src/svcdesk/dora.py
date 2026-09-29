# ai-generated: 100% - Codex implemented the Lab 2 rules; arithmetic is independent of fixtures.
"""Pure delivery metric calculation under METRIC-SPEC.md version 1.0.0."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from itertools import combinations

from .clock import parse_instant, stamp


class InvalidLog(ValueError):
    """The request cannot represent a well-formed event log."""


def require(condition, message):
    if not condition:
        raise InvalidLog(message)


def text(value, name, nullable=False, empty=False):
    if nullable and value is None:
        return
    require(isinstance(value, str) and (empty or bool(value)), f'{name} must be a string')


def instant(value):
    text(value, 'timestamp')
    try:
        # datetime.fromisoformat normalizes out-of-range offset minutes; RFC 3339 does not.
        if len(value) >= 6 and value[-6] in '+-' and value[-3] == ':':
            require(int(value[-5:-3]) < 24 and int(value[-2:]) < 60, 'Invalid timezone offset')
        return parse_instant(value)
    except (ValueError, OverflowError) as exc:
        raise InvalidLog('Expected an RFC 3339 instant with explicit timezone') from exc


def strings(value, name):
    require(isinstance(value, list), f'{name} must be an array')
    for item in value:
        text(item, name)


def elapsed(end, start):
    delta = end - start
    return Decimal(delta.days * 86400 + delta.seconds) + Decimal(delta.microseconds) / 1000000


def median_seconds(values):
    if not values:
        return None
    values = sorted(values)
    size = len(values)
    mid = values[size // 2] if size % 2 else (values[size // 2 - 1] + values[size // 2]) / 2
    return int(mid.quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def ratio(numerator, denominator):
    if not denominator:
        return None
    return float((Decimal(numerator) / Decimal(denominator)).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))


@dataclass
class Log:
    start: object
    end: object
    commits: dict
    deployments: dict
    incidents: dict
    changes: dict


def read_log(body):
    require(isinstance(body, dict), 'Body must be an object')
    window = body.get('window')
    require(isinstance(window, dict), 'window must be an object')
    start, end = instant(window.get('from')), instant(window.get('to'))
    require(end > start, 'window.to must be after window.from')
    require(isinstance(body.get('events'), list), 'events must be an array')
    commits, deployments, incidents, seen = {}, {}, {}, set()
    for raw in body['events']:
        require(isinstance(raw, dict), 'Each event must be an object')
        event_id = raw.get('event_id')
        text(event_id, 'event_id')
        require(len(event_id) <= 64, 'event_id is longer than 64 characters')
        if event_id in seen:
            continue  # R-05: ignore later copies before validating their other fields.
        seen.add(event_id)
        kind = raw.get('type')
        require(kind in ('commit', 'deployment', 'incident'), 'Unknown event type')
        event = {**raw, '_at': instant(raw.get('at'))}
        if kind == 'commit':
            require(all(k in raw for k in ('sha', 'branch', 'change_id', 'reverts')), 'Missing commit field')
            text(raw['sha'], 'sha')
            text(raw['branch'], 'branch', empty=True)
            text(raw['change_id'], 'change_id', nullable=True)
            text(raw['reverts'], 'reverts', nullable=True)
            require((raw['change_id'] is None) == (raw['reverts'] is not None), 'A revert inherits change_id; a normal commit needs one')
            require(raw['sha'] not in commits, 'Duplicate sha')
            commits[raw['sha']] = event
        elif kind == 'deployment':
            require(all(k in raw for k in ('deployment_id','environment','outcome','commits','unplanned','caused_by')), 'Missing deployment field')
            text(raw['deployment_id'], 'deployment_id')
            text(raw['environment'], 'environment', empty=True)
            require(raw['outcome'] in ('success', 'failure'), 'Invalid deployment outcome')
            require(type(raw['unplanned']) is bool, 'unplanned must be boolean')
            text(raw['caused_by'], 'caused_by', nullable=True)
            strings(raw['commits'], 'commits')
            require(raw['deployment_id'] not in deployments, 'Duplicate deployment_id')
            deployments[raw['deployment_id']] = event
        else:
            require(all(k in raw for k in ('incident_id','phase','deployments')), 'Missing incident field')
            text(raw['incident_id'], 'incident_id')
            require(raw['phase'] in ('opened','resolved'), 'Invalid incident phase')
            strings(raw['deployments'], 'deployments')
            incident = incidents.setdefault(raw['incident_id'], {})
            require(raw['phase'] not in incident, 'Duplicate incident phase')
            incident[raw['phase']] = event

    for event in commits.values():
        require(event['reverts'] is None or event['reverts'] in commits, 'Unknown reverted sha')
    for event in deployments.values():
        require(all(sha in commits for sha in event['commits']), 'Unknown deployed sha')
        require(event['caused_by'] is None or event['caused_by'] in incidents, 'Unknown caused_by incident')
    for incident in incidents.values():
        require('opened' in incident, 'An incident resolution needs an opening')
        for event in incident.values():
            require(all(dep in deployments for dep in event['deployments']), 'Unknown incident deployment')

    # Iterative resolution handles forward references and long revert chains, without recursion limits.
    changes = {}
    for sha in commits:
        path, visiting, current = [], set(), sha
        while current not in changes:
            require(current not in visiting, 'Cyclic revert chain has no original change')
            visiting.add(current)
            path.append(current)
            commit = commits[current]
            if commit['reverts'] is None:
                changes[current] = commit['change_id']
                break
            current = commit['reverts']
        for visited in path:
            changes[visited] = changes[current]
    return Log(start, end, commits, deployments, incidents, changes)


def compute_metrics(body):
    log = read_log(body)
    scoped = [d for d in log.deployments.values() if d['environment'] == 'production' and log.start <= d['_at'] < log.end]
    successful = sorted((d for d in scoped if d['outcome'] == 'success'), key=lambda d: (d['_at'], d['deployment_id']))
    failed = [d for d in scoped if d['outcome'] == 'failure']
    first_change_commit = {}
    for sha, commit in log.commits.items():
        change = log.changes[sha]
        first_change_commit[change] = min(commit['_at'], first_change_commit.get(change, commit['_at']))

    paired, delivered, leads = set(), {}, []
    negative = 0
    for deployment in successful:
        for sha in deployment['commits']:
            if sha not in paired:
                lead = elapsed(deployment['_at'], log.commits[sha]['_at'])
                negative += lead < 0
                leads.append(max(Decimal(0), lead))
                paired.add(sha)
            delivered.setdefault(log.changes[sha], deployment['_at'])

    covering, intervals = {}, []
    for iid, incident in log.incidents.items():
        opened = incident['opened']['_at']
        resolved = incident.get('resolved', {}).get('_at')
        intervals.append((opened, resolved if resolved is not None else log.end))
        # Either event can carry the link; identity is the incident_id, not an event row.
        linked = {dep for event in incident.values() for dep in event['deployments']}
        for dep in linked:
            candidate = (opened, iid.encode('utf-8'), resolved)
            if dep not in covering or candidate[:2] < covering[dep][:2]:
                covering[dep] = candidate
    recoveries = []
    for deployment in failed:
        incident = covering.get(deployment['deployment_id'])
        if incident is not None and incident[2] is not None:
            recoveries.append(max(Decimal(0), elapsed(incident[2], deployment['_at'])))
    overlaps = sum(a[0] < b[1] and b[0] < a[1] for a, b in combinations(intervals, 2))
    off_main = {sha for d in scoped for sha in d['commits'] if log.commits[sha]['branch'] != 'main'}
    rework = sum(d['unplanned'] and d['caused_by'] is not None for d in scoped)
    return {
        'spec_version': '1.0.0',
        'window': {'from': stamp(log.start), 'to': stamp(log.end)},
        'deployment_frequency_per_day': ratio(len(scoped) * 86400, elapsed(log.end, log.start)),
        'change_lead_time_seconds_p50': median_seconds(leads),
        'failed_deployment_recovery_time_seconds_p50': median_seconds(recoveries),
        'change_fail_rate': ratio(len(failed), len(scoped)),
        'deployment_rework_rate': ratio(rework, len(scoped)),
        'counts': {'deployments': len(scoped), 'successful_deployments': len(successful),
                   'failed_deployments': len(failed), 'recovered_failures': len(recoveries),
                   'open_failures': len(failed) - len(recoveries), 'rework_deployments': rework,
                   'lead_time_pairs': len(leads), 'changes': len(first_change_commit)},
        'anomalies': {'negative_lead_time_pairs': negative,
                      'deployments_without_commits': sum(not d['commits'] for d in scoped),
                      'commits_never_on_main': len(off_main),
                      'revert_chains_collapsed': sum(c['reverts'] is not None for c in log.commits.values()),
                      'overlapping_incident_pairs': overlaps},
        'ground_truth': {'changes_delivered': len(delivered),
                         'true_change_lead_time_seconds_p50': median_seconds([
                             max(Decimal(0), elapsed(at, first_change_commit[change]))
                             for change, at in delivered.items()])},
    }
