# ai-generated: 100% - Codex wrote a reproducible gaming transformation and HTTP-result capture.
"""Generate artifacts from a running service, never by copying the answer key."""
import argparse
import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
WINDOW = {'from': '2026-09-01T00:00:00Z', 'to': '2026-09-22T00:00:00Z'}


def instant(value):
    return datetime.fromisoformat(value.replace('Z','+00:00'))


def stamp(value):
    return value.astimezone(timezone.utc).isoformat().replace('+00:00','Z')


def metrics(base_url, events):
    data=json.dumps({'window':WINDOW,'events':events}).encode()
    req=Request(base_url.rstrip('/')+'/dora/metrics',data=data,headers={'Content-Type':'application/json'})
    with urlopen(req,timeout=30) as response:
        return json.load(response)


def generate(base_url):
    base=[json.loads(line) for line in (ROOT/'fixtures/events-practice.jsonl').read_text().splitlines() if line.strip()]
    after=copy.deepcopy(base)
    start,end=instant(WINDOW['from']),instant(WINDOW['to'])
    candidates=sorted([e for e in after if e['type']=='deployment' and e['environment']=='production'
                       and e['outcome']=='success' and e['commits'] and start<=instant(e['at'])<end],
                      key=lambda e:(instant(e['at']),e['deployment_id']),reverse=True)
    # Delay the seven latest substantive successful deployments until after the window.
    delayed=candidates[:7]
    for n,event in enumerate(delayed):
        event['at']=stamp(end+timedelta(hours=n+1))
    # Spend release capacity on twenty no-op deployments that count towards frequency.
    for n in range(20):
        after.append({'event_id':f'gaming-noop-{n:02}', 'type':'deployment',
                      'at':stamp(start+timedelta(days=n,hours=12)),
                      'deployment_id':f'GAMING-NOOP-{n:02}', 'environment':'production',
                      'outcome':'success','commits':[], 'unplanned':False,'caused_by':None})
    before_result,after_result=metrics(base_url,base),metrics(base_url,after)
    original_shas={e['sha'] for e in base if e['type']=='commit'}
    base_only=copy.deepcopy(after)
    base_only=[e for e in base_only if e['type']!='commit' or e['sha'] in original_shas]
    for event in base_only:
        if event['type']=='deployment':
            event['commits']=[s for s in event['commits'] if s in original_shas]
    harm=metrics(base_url,base_only)
    assert after_result['deployment_frequency_per_day'] >= before_result['deployment_frequency_per_day']*1.25
    assert harm['ground_truth']['changes_delivered'] <= before_result['ground_truth']['changes_delivered']*0.9
    # Independently check preservation, not only the calculated metrics.
    index={e['event_id']:e for e in after}
    for event in base:
        transformed=index[event['event_id']]
        if event['type']!='deployment':
            assert event==transformed
        else:
            assert all(event[k]==transformed[k] for k in ('deployment_id','environment','outcome'))
            assert instant(transformed['at'])>=instant(event['at'])
    (ROOT/'gaming').mkdir(exist_ok=True)
    (ROOT/'gaming/after.jsonl').write_text(''.join(json.dumps(e,separators=(',',':'))+'\n' for e in after))
    (ROOT/'metrics.json').write_text(json.dumps(before_result,indent=2)+'\n')
    (ROOT/'gaming.json').write_text(json.dumps({'metric':'deployment_frequency_per_day','rule':'R-11',
                                              'before':before_result,'after':after_result},indent=2)+'\n')
    evidence={'delayed_deployments':[e['deployment_id'] for e in delayed], 'added_noop_deployments':20,
              'before':before_result,'after_base_only':harm,
              'frequency_improvement_percent':100*(after_result['deployment_frequency_per_day']/before_result['deployment_frequency_per_day']-1),
              'changes_delivered_drop_percent':100*(1-harm['ground_truth']['changes_delivered']/before_result['ground_truth']['changes_delivered'])}
    (ROOT/'gaming/evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps({k:v for k,v in evidence.items() if k not in ('before','after_base_only')},indent=2))
    print('Before/after deployments:',before_result['counts']['deployments'],after_result['counts']['deployments'])
    print('Before/after original changes:',before_result['ground_truth']['changes_delivered'],harm['ground_truth']['changes_delivered'])


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--base-url',default='http://127.0.0.1:8080')
    generate(parser.parse_args().base_url)
