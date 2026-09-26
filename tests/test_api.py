# ai-generated: 100% - Codex wrote independent HTTP acceptance and boundary tests.
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import httpx
import pytest

BASE = os.environ.get('SVCDESK_URL', 'http://svcdesk:8080')
T1 = '2026-10-14T10:00:00Z'


@pytest.fixture
def client():
    with httpx.Client(base_url=BASE, timeout=10) as c:
        yield c


def clock(value=T1):
    return {'X-Test-Clock': value}


def payload(**changes):
    return {'title': 'Synthetic test ticket', 'reporter': {'name': 'Test reporter'}, 'impact': 1, 'urgency': 1, **changes}


def create(client, when=T1, **changes):
    r = client.post('/tickets', json=payload(**changes), headers=clock(when))
    assert r.status_code == 201, r.text
    return r.json()


def action(client, ticket, name, when=T1, expected=200):
    r = client.post(f'/tickets/{ticket["id"]}/{name}', headers=clock(when))
    assert r.status_code == expected, r.text
    return r.json()


def resolved(client):
    t = create(client)
    action(client, t, 'ack')
    action(client, t, 'start')
    return action(client, t, 'resolve')


def sla(client, t, when):
    r = client.get(f'/tickets/{t["id"]}/sla', headers=clock(when))
    assert r.status_code == 200
    return r.json()


def test_health(client):
    assert client.get('/health').json() == {'status': 'ok', 'service': 'svcdesk'}


@pytest.mark.parametrize('impact,urgency,priority', [(1,1,'P1'),(1,2,'P2'),(1,3,'P3'),(2,1,'P2'),(2,2,'P3'),(2,3,'P4'),(3,1,'P3'),(3,2,'P4'),(3,3,'P4')])
def test_matrix(client, impact, urgency, priority):
    assert create(client, impact=impact, urgency=urgency)['priority'] == priority


@pytest.mark.parametrize('impact,urgency,when,ack,due', [
 (1,1,T1,'2026-10-14T10:15:00Z','2026-10-14T14:00:00Z'),
 (2,2,'2026-10-16T13:30:00Z','2026-10-19T09:30:00Z','2026-10-21T13:30:00Z'),
 (1,1,'2026-10-16T15:00:00Z','2026-10-16T15:15:00Z','2026-10-16T19:00:00Z'),
 (2,1,'2026-10-17T10:00:00Z','2026-10-19T07:00:00Z','2026-10-19T14:00:00Z'),
 (3,3,'2027-01-14T14:30:00Z','2027-01-15T14:30:00Z','2027-01-27T14:30:00Z'),
 (1,1,'2027-01-15T15:50:00Z','2027-01-15T16:05:00Z','2027-01-15T19:50:00Z'),
 (2,1,T1,'2026-10-14T11:00:00Z','2026-10-15T10:00:00Z'),
 (2,2,'2026-10-23T13:00:00Z','2026-10-26T10:00:00Z','2026-10-28T14:00:00Z'),
 (2,1,'2027-03-26T14:00:00Z','2027-03-26T15:00:00Z','2027-03-29T13:00:00Z'),
])
def test_sla_vectors(client, impact, urgency, when, ack, due):
    assert create(client, when, impact=impact, urgency=urgency)['sla'] == {'ack_due_at': ack, 'resolve_due_at': due}


@pytest.mark.parametrize('changes', [{'title':''},{'title':'x'*201},{'description':'x'*4001},{'reporter':{'name':''}},{'reporter':{'name':'x'*101}},{'impact':True},{'impact':1.0},{'impact':'1'},{'impact':0},{'urgency':4},{'reporter':{'name':'Test','vip':'true'}}])
def test_validation(client, changes):
    r = client.post('/tickets', json=payload(**changes))
    assert r.status_code == 422 and isinstance(r.json()['error'], dict)


def test_missing_title_and_bad_json(client):
    data = payload(); del data['title']
    for kwargs in [{'json':data}, {'content':'{', 'headers':{'Content-Type':'application/json'}}]:
        r = client.post('/tickets', **kwargs)
        assert r.status_code == 422 and 'error' in r.json()


def test_server_fields_ignored_and_vip_stored(client):
    t = create(client, impact=3, urgency=3, reporter={'name':'Test','vip':True,'extra':42}, priority='P1', id='chosen', state='closed', sla={}, unknown=123)
    assert t['priority'] == 'P4' and t['state'] == 'new' and t['id'] != 'chosen'
    assert t['reporter']['vip'] is True and t['sla']['ack_due_at']


def test_distinct_ids_defaults_and_related_to(client):
    a = create(client); b = create(client, related_to=a['id'])
    assert a['id'] != b['id'] and b['related_to'] == a['id']
    assert a['description'] == '' and a['reporter']['email'] is None and a['reporter']['vip'] is False
    assert client.get('/tickets/'+a['id']).json() == a


def test_combined_filters(client):
    a = create(client); b = create(client); c = create(client, impact=3, urgency=3)
    action(client,b,'ack')
    rows = client.get('/tickets',params={'state':'new','priority':'P1'}).json()
    ids = {t['id'] for t in rows}
    assert a['id'] in ids and b['id'] not in ids and c['id'] not in ids
    assert all(t['state']=='new' and t['priority']=='P1' for t in rows)


@pytest.mark.parametrize('path', ['/missing','/tickets/nonexistent','/tickets/nonexistent/sla'])
def test_unknown_routes(client,path):
    r = client.get(path)
    assert r.status_code == 404 and 'application/json' in r.headers['content-type'] and 'error' in r.json()


def test_invalid_transitions(client):
    t=create(client)
    for name in ['start','resolve','close','reopen']:
        assert 'error' in action(client,t,name,expected=409)
    action(client,t,'ack'); action(client,t,'ack',expected=409)
    action(client,t,'resolve',expected=409)
    action(client,t,'start'); action(client,t,'close',expected=409)
    assert client.post('/tickets/nonexistent/ack').status_code == 404


def test_reopen_exact_boundary_preserves_deadline(client):
    t=resolved(client)
    r=action(client,t,'reopen','2026-10-21T10:00:00Z')
    assert r['state']=='in_progress' and r['resolved_at'] is None and r['closed_at'] is None
    assert r['sla']==t['sla'] and r['acknowledged_at']==t['acknowledged_at']
    assert sla(client,r,'2026-10-21T10:00:00Z')['resolve_breached'] is True


def test_reopen_expired_and_closed_immutable(client):
    t=resolved(client)
    action(client,t,'reopen','2026-10-21T10:00:01Z',expected=409)
    closed=action(client,t,'close')
    action(client,t,'reopen',expected=409)
    assert client.get('/tickets/'+t['id']).json() == closed


def test_breach_equality_and_event_history(client):
    t=create(client)
    assert sla(client,t,'2026-10-14T10:15:00Z')['ack_breached'] is False
    assert sla(client,t,'2026-10-14T10:15:01Z')['ack_breached'] is True
    action(client,t,'ack','2026-10-14T10:15:00Z'); action(client,t,'start')
    assert sla(client,t,'2026-10-14T14:00:00Z')['resolve_breached'] is False
    action(client,t,'resolve','2026-10-14T14:00:00Z')
    result=sla(client,t,'2026-11-14T14:00:00Z')
    assert result['ack_breached'] is False and result['resolve_breached'] is False


def test_late_events_stay_breached(client):
    t=create(client)
    action(client,t,'ack','2026-10-14T10:15:01Z'); action(client,t,'start')
    action(client,t,'resolve','2026-10-14T14:00:01Z')
    r=sla(client,t,'2026-10-14T10:00:00Z')
    assert r['ack_breached'] and r['resolve_breached']


def test_pause_boundaries(client):
    t=create(client,impact=2,urgency=1)
    for when,paused in [('2026-10-17T10:00:00Z',True),('2026-10-19T06:00:00Z',False),('2026-10-19T14:00:00Z',True)]:
        assert sla(client,t,when)['paused'] is paused
    p1=create(client)
    assert sla(client,p1,'2026-10-17T10:00:00Z')['paused'] is False
    for name in ['ack','start','resolve']: action(client,t,name)
    assert sla(client,t,'2026-10-17T10:00:00Z')['paused'] is False


@pytest.mark.parametrize('value',['yesterday','2026-10-14T10:00:00','2026-99-14T10:00:00Z'])
def test_bad_clock(client,value):
    r=client.post('/tickets',json=payload(),headers=clock(value))
    assert r.status_code==422 and 'error' in r.json()


def test_offset_and_clock_isolation(client):
    t=create(client,'2026-10-14T12:00:00+02:00')
    assert t['created_at']==T1
    before=datetime.now(timezone.utc)
    real=client.post('/tickets',json=payload()).json()
    after=datetime.now(timezone.utc)
    assert before <= datetime.fromisoformat(real['created_at'].replace('Z','+00:00')) <= after
    assert create(client,'2020-01-01T00:00:00Z')['created_at']=='2020-01-01T00:00:00Z'


def test_concurrent_ack_only_one_succeeds(client):
    t=create(client)
    def ack(_):
        return httpx.post(BASE+'/tickets/'+t['id']+'/ack',headers=clock(),timeout=10).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(ack,range(2))) == [200,409]
