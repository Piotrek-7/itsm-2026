# ai-generated: 100% - Codex wrote synthetic rule tests independent of the practice answer key.
import copy
import json
import os
from datetime import datetime
from pathlib import Path

import httpx
import pytest

BASE = os.environ.get('SVCDESK_URL', 'http://svcdesk:8080')
WINDOW = {'from': '2026-09-01T00:00:00Z', 'to': '2026-09-22T00:00:00Z'}


@pytest.fixture
def api():
    with httpx.Client(base_url=BASE, timeout=30) as client:
        yield client


def commit(sha='a', at='2026-09-01T00:00:00Z', change='change-a', branch='main', reverts=None):
    return {'event_id': 'commit-'+sha, 'type': 'commit', 'at': at, 'sha': sha,
            'branch': branch, 'change_id': change, 'reverts': reverts}


def deploy(id='d', at='2026-09-01T00:00:01Z', commits=('a',), outcome='success', environment='production', unplanned=False, caused_by=None):
    return {'event_id': 'deploy-'+id, 'type': 'deployment', 'at': at, 'deployment_id': id,
            'environment': environment, 'outcome': outcome, 'commits': list(commits),
            'unplanned': unplanned, 'caused_by': caused_by}


def incident(id='i', phase='opened', at='2026-09-01T00:00:02Z', deployments=('d',)):
    return {'event_id': 'incident-'+id+'-'+phase, 'type': 'incident', 'at': at,
            'incident_id': id, 'phase': phase, 'deployments': list(deployments)}


def score(api, events, window=None):
    r = api.post('/dora/metrics', json={'window': window or WINDOW, 'events': events})
    assert r.status_code == 200, r.text
    return r.json()


def test_practice_all_fields_and_purity(api):
    root = Path(__file__).resolve().parents[1] / 'fixtures'
    expected = json.loads((root/'metrics-practice.json').read_text())
    events = [json.loads(line) for line in (root/'events-practice.jsonl').read_text().splitlines() if line.strip()]
    assert score(api, events) == expected
    assert score(api, list(reversed(events))) == expected
    assert score(api, events + events) == expected
    assert score(api, events) == expected


def test_empty_log_nulls(api):
    r = score(api, [])
    assert r['deployment_frequency_per_day'] == 0
    for field in ('change_lead_time_seconds_p50','failed_deployment_recovery_time_seconds_p50','change_fail_rate','deployment_rework_rate'):
        assert r[field] is None
    assert set(r['counts'].values()) == {0}
    assert set(r['anomalies'].values()) == {0}
    assert r['ground_truth'] == {'changes_delivered': 0, 'true_change_lead_time_seconds_p50': None}


def test_first_duplicate_wins_even_if_later_payload_invalid(api):
    events = [commit(), deploy()]
    expected = score(api, events)
    assert score(api, events + [{'event_id': 'commit-a', 'type': 'invalid'}]) == expected
    assert score(api, events + [deploy(outcome='failure')]) == expected


def test_window_only_filters_deployments_and_offsets_are_instants(api):
    window = {'from':'2026-09-01T02:00:00+02:00', 'to':'2026-09-02T00:00:00Z'}
    events = [commit(at='2026-08-31T23:59:00Z'),
              deploy('before','2026-08-31T23:59:59Z'),
              deploy('opening','2026-09-01T00:00:00Z'),
              deploy('closing','2026-09-02T00:00:00Z'),
              deploy('staging','2026-09-01T00:00:00Z',environment='staging')]
    r = score(api, events, window)
    assert r['counts']['deployments'] == 1 and r['change_lead_time_seconds_p50'] == 60
    assert r['deployment_frequency_per_day'] == 1
    assert r['window']['from'] == WINDOW['from']


def test_failed_deployment_does_not_deliver_and_redeployment_counts_once(api):
    events = [commit(), deploy('failed',outcome='failure'),
              deploy('first','2026-09-01T00:00:10Z'), deploy('repeat','2026-09-01T00:01:00Z')]
    r = score(api, events)
    assert r['counts']['lead_time_pairs'] == 1 and r['change_lead_time_seconds_p50'] == 10
    assert r['counts']['open_failures'] == 1 and r['change_fail_rate'] == 0.333333


def test_negative_pairs_are_counted_and_clamped(api):
    r=score(api,[commit(at='2026-09-01T00:00:02Z'),deploy()])
    assert r['change_lead_time_seconds_p50'] == 0
    assert r['anomalies']['negative_lead_time_pairs'] == 1
    assert r['ground_truth']['true_change_lead_time_seconds_p50'] == 0


def test_revert_of_revert_and_earliest_change_commit(api):
    events=[commit(at='2026-08-31T23:59:00Z'),
            commit('b','2026-09-01T00:00:00Z',None,reverts='a'),
            commit('c','2026-09-01T00:00:01Z',None,reverts='b'),
            deploy(at='2026-09-01T00:00:11Z',commits=('c',))]
    r=score(api,list(reversed(events)))
    assert r['counts']['changes']==1 and r['anomalies']['revert_chains_collapsed']==2
    assert r['change_lead_time_seconds_p50']==10
    assert r['ground_truth']=={'changes_delivered':1,'true_change_lead_time_seconds_p50':71}


def test_long_revert_chain_is_not_recursive(api):
    events=[commit()]
    prev='a'
    for n in range(1100):
        sha='r'+str(n)
        events.append(commit(sha,change=None,reverts=prev)); prev=sha
    events.append(deploy(commits=(prev,)))
    r=score(api,list(reversed(events)))
    assert r['counts']['changes']==1 and r['anomalies']['revert_chains_collapsed']==1100


def test_off_main_counts_distinct_shas_on_failures_too(api):
    events=[commit(branch='hotfix'),deploy(outcome='failure'),deploy('again',outcome='failure'),
            commit('unused',branch='feature'),deploy('staging',commits=('unused',),environment='staging')]
    r=score(api,events)
    assert r['anomalies']['commits_never_on_main']==1
    assert r['counts']['lead_time_pairs']==0 and r['counts']['changes']==1


def test_empty_deployments_count_and_rework_requires_both_conditions(api):
    events=[deploy('a',commits=(),unplanned=True),deploy('b',commits=(),caused_by='i'),
            deploy('c',commits=(),outcome='failure',unplanned=True,caused_by='i'),
            incident(deployments=('c',))]
    r=score(api,events)
    assert r['anomalies']['deployments_without_commits']==3
    assert r['change_fail_rate']==r['deployment_rework_rate']==0.333333
    assert r['counts']['rework_deployments']==1 and r['counts']['open_failures']==1


def test_earliest_covering_incident_wins_even_if_open(api):
    events=[deploy(commits=(),outcome='failure'),incident('a'),
            incident('b',at='2026-09-01T00:00:03Z'),
            incident('b','resolved','2026-09-01T00:00:04Z')]
    r=score(api,events)
    assert r['counts']['open_failures']==1 and r['failed_deployment_recovery_time_seconds_p50'] is None


def test_incident_tie_break_and_recovery_after_window(api):
    events=[deploy(at='2026-09-21T23:59:59Z',commits=(),outcome='failure'),
            incident('z',at='2026-09-22T00:00:00Z'),
            incident('a',at='2026-09-22T00:00:00Z'),
            incident('z','resolved','2026-09-22T00:00:20Z'),
            incident('a','resolved','2026-09-22T00:00:10Z')]
    r=score(api,list(reversed(events)))
    assert r['failed_deployment_recovery_time_seconds_p50']==11
    assert r['counts']['recovered_failures']==1


def test_one_incident_two_failed_deployments_and_negative_recovery(api):
    events=[deploy('a',at='2026-09-01T00:00:00Z',commits=(),outcome='failure'),
            deploy('b',at='2026-09-01T00:00:20Z',commits=(),outcome='failure'),
            incident(at='2026-09-01T00:00:01Z',deployments=('a','b')),
            incident(phase='resolved',at='2026-09-01T00:00:10Z',deployments=('a','b'))]
    r=score(api,events)
    assert r['counts']['recovered_failures']==2
    assert r['failed_deployment_recovery_time_seconds_p50']==5


def test_overlaps_are_unordered_pairs_and_touching_is_not_overlap(api):
    events=[incident('a',at='2026-09-01T00:00:00Z',deployments=()),
            incident('a','resolved','2026-09-01T00:00:10Z',()),
            incident('b',at='2026-09-01T00:00:05Z',deployments=()),
            incident('b','resolved','2026-09-01T00:00:10Z',()),
            incident('c',at='2026-09-01T00:00:10Z',deployments=()),
            incident('d',at='2026-08-30T00:00:00Z',deployments=()),
            incident('d','resolved','2026-08-31T00:00:00Z',())]
    r=score(api,events)
    assert r['anomalies']['overlapping_incident_pairs']==1


def test_half_up_median_and_fractional_window_rate(api):
    events=[commit(),commit('b'),deploy(commits=('a',),at='2026-09-01T00:00:02Z'),
            deploy('b',commits=('b',),at='2026-09-01T00:00:03Z')]
    r=score(api,events,{'from':WINDOW['from'],'to':'2026-09-01T12:00:00Z'})
    assert r['change_lead_time_seconds_p50']==3 and r['deployment_frequency_per_day']==4
    r=score(api,[commit(),deploy(at='2026-09-01T00:00:00.500000Z')])
    assert r['change_lead_time_seconds_p50']==1


def test_pair_median_differs_from_change_median(api):
    events=[commit('a','2026-09-01T00:00:00Z','X'),commit('b','2026-09-01T00:00:09Z','X'),
            commit('c','2026-09-01T00:00:09Z','X'),commit('d','2026-09-01T00:00:00Z','Y'),
            deploy(at='2026-09-01T00:00:10Z',commits=('a','b','c','d'))]
    r=score(api,events)
    assert r['change_lead_time_seconds_p50']==6
    assert r['ground_truth']=={'changes_delivered':2,'true_change_lead_time_seconds_p50':10}


@pytest.mark.parametrize('body',[[],{}, {'events':[]}, {'window':WINDOW}, {'window':WINDOW,'events':{}},
 {'window':{'from':WINDOW['from'],'to':WINDOW['from']},'events':[]},
 {'window':{'from':'2026-09-01T00:00:00','to':WINDOW['to']},'events':[]},
 {'window':{'from':'2026-09-01T00:00:00+00:99','to':WINDOW['to']},'events':[]}])
def test_invalid_requests(api,body):
    r=api.post('/dora/metrics',json=body)
    assert r.status_code==422 and isinstance(r.json()['error'],dict)


@pytest.mark.parametrize('events',[
 [commit(reverts='missing',change=None)], [deploy()],
 [commit(),{**commit(),'event_id':'duplicate-sha'}],
 [commit(change=None)], [commit('a',change=None,reverts='b'),commit('b',change=None,reverts='a')],
 [incident(phase='resolved',deployments=())], [incident()],
 [deploy(commits=(),caused_by='missing')], [deploy(commits=(),unplanned='true')],
 [commit(),{**commit('b'),'at':'yesterday'}],
 [incident(deployments=()),{**incident(deployments=()),'event_id':'second-open'}],
])
def test_invalid_logs(api,events):
    r=api.post('/dora/metrics',json={'window':WINDOW,'events':events})
    assert r.status_code==422 and isinstance(r.json()['error'],dict)


def test_ticket_stream_historical_states_order_and_reopen(api):
    def ticket():
        r=api.post('/tickets',json={'title':'Lifecycle export test','reporter':{'name':'Synthetic'},'impact':1,'urgency':1},headers={'X-Test-Clock':'2026-09-01T10:00:00.100000Z'})
        assert r.status_code==201
        return r.json()['id']
    first, second=ticket(),ticket()
    for name,at in [('ack','2026-09-01T10:00:00Z'),('start','2026-09-01T10:00:01Z'),('resolve','2026-09-01T10:00:02Z'),('close','2026-09-01T10:00:03Z')]:
        assert api.post(f'/tickets/{first}/{name}',headers={'X-Test-Clock':at}).status_code==200
    rows=api.get('/dora/ticket-events').json()
    keys=[(datetime.fromisoformat(e['at'].replace('Z','+00:00')),e['ticket_id']) for e in rows]
    assert keys==sorted(keys)
    mine=[e for e in rows if e['ticket_id']==first]
    assert [e['phase'] for e in mine]==['acknowledged','created','resolved','closed']
    assert [e['state'] for e in mine]==['acknowledged','new','resolved','closed']
    assert all(e['priority']=='P1' for e in mine)
    assert [e['phase'] for e in rows if e['ticket_id']==second]==['created']
    for name in ('ack','start','resolve','reopen'):
        assert api.post(f'/tickets/{second}/{name}',headers={'X-Test-Clock':'2026-09-01T10:00:04Z'}).status_code==200
    rows=api.get('/dora/ticket-events').json()
    assert {e['phase'] for e in rows if e['ticket_id']==second}=={'created','acknowledged'}
