# ai-generated: 100% - Codex tests specification edge cases independently of the published practice fixture.
import copy
import unittest
from bakeoff import measure


def finding(uri='set/app/x.py', line=7, rule='r', **extra):
    r={'ruleId':rule,'locations':[{'physicalLocation':{'artifactLocation':{'uri':uri},'region':{'startLine':line}}}], 'properties':{'class':'injection'}}
    r.update(extra)
    return r


def document(results, name='Semgrep CE', rules=None):
    return {'runs':[{'tool':{'driver':{'name':name,'rules':rules or []}},'results':results}]}


class MatchingRules(unittest.TestCase):
    def setUp(self):
        self.labels={'set':'set','defects':[{'id':'D1','file':'set/app/x.py','class':'injection','start_line':7,'end_line':9}]}

    def count(self, results, **kwargs):
        return measure(self.labels,[document(results,**kwargs)])['tools']

    def test_overlap_and_last_root_after_percent_decoding(self):
        r=finding('FILE:///set/ignored/set%2Fapp%2Fx.py',8)
        self.assertEqual(self.count([r])['semgrep']['tp'],1)
        self.assertEqual(self.count([finding('set\\app\\x.py')])['semgrep']['tp'],0)
        self.assertEqual(self.count([finding('sets/app/x.py')])['semgrep']['fp'],0)

    def test_only_first_location_matters(self):
        r=finding();r['locations'].insert(0,{'logicalLocations':[]})
        self.assertEqual(self.count([r])['semgrep']['fp'],0)
        self.assertEqual(self.count([r])['semgrep']['fn'],1)

    def test_integer_lines_and_end_fallback(self):
        for line in [None,0,-1,7.0,'7',True]:
            c=self.count([finding(line=line)])['semgrep'];self.assertEqual((c['tp'],c['fp']),(0,1))
        for end in [None,True,7.0,'8',1]:
            r=finding();r['locations'][0]['physicalLocation']['region']['endLine']=end
            self.assertEqual(self.count([r])['semgrep']['tp'],1)
        r=finding(line=6);r['locations'][0]['physicalLocation']['region']['endLine']=7
        self.assertEqual(self.count([r])['semgrep']['tp'],1)

    def test_kinds_and_suppressions(self):
        for suppression in [None,[],{},False,0,'']:
            self.assertEqual(self.count([finding(suppressions=suppression)])['semgrep']['tp'],1)
        for suppression in [[None],{'status':'rejected'},True,'anything',1]:
            self.assertEqual(self.count([finding(suppressions=suppression)])['semgrep']['tp'],0)
        for kind in ['FAIL','pass','informational',False,0,[],{}]:
            self.assertEqual(self.count([finding(kind=kind)])['semgrep']['tp'],0)
        self.assertEqual(self.count([finding(kind=None)])['semgrep']['tp'],1)

    def test_dedupe_after_matching_not_before(self):
        good=finding()
        bad=finding();bad['properties']['class']='weak-crypto'
        result=self.count([good,bad,copy.deepcopy(bad)])['semgrep']
        self.assertEqual((result['tp'],result['fp'],result['fn']),(1,1,0))
        a=finding(line=99,rule=None);b=finding(line=99,rule='')
        self.assertEqual(self.count([a,b,a])['semgrep']['fp'],2)

    def test_class_priority_first_rule_and_cwe_boundaries(self):
        r=finding();r['properties']={'tags':['XCWE-89','CWE 89']}
        self.assertEqual(self.count([r])['semgrep']['tp'],0)
        r['properties']['tags']=['KCWE-000089','CWE-502']
        self.assertEqual(self.count([r])['semgrep']['tp'],1)
        rules=[{'id':'r','properties':{'tags':['CWE-327']}},{'id':'r','properties':{'tags':['CWE-89']}}]
        r['properties']={}
        self.assertEqual(self.count([r],rules=rules)['semgrep']['tp'],0)
        r['properties']['class']='injection'
        self.assertEqual(self.count([r],rules=rules)['semgrep']['tp'],1)

    def test_trivy_tag_overrides_cwe_but_own_class_overrides_tool(self):
        r=finding();r['properties']={}
        rules=[{'id':'r','properties':{'tags':['VULNERABILITY','CWE-89']}}]
        self.assertEqual(self.count([r],name='Trivy',rules=rules)['trivy']['tp'],0)
        r['properties']['class']='injection'
        self.assertEqual(self.count([r],name='Trivy',rules=rules)['trivy']['tp'],1)
        r['properties']={};rules[0]['properties']['tags']=[' vulnerability ','CWE-89']
        self.assertEqual(self.count([r],name='Trivy',rules=rules)['trivy']['tp'],1)

    def test_package_matching_without_lines_and_pep503(self):
        labels={'set':'custom','defects':[{'id':'a','file':'custom/requirements.txt','class':'vulnerable-dependency','package':'My_Package'},{'id':'b','file':'custom/requirements.txt','class':'vulnerable-dependency','package':'other'}]}
        r=finding('file:///custom/requirements.txt',None,message={'text':"Package 'my.package@1.0' also affects other."})
        r.pop('properties')
        c=measure(labels,[document([r],name='OSV-Scanner')])['tools']['osv-scanner']
        self.assertEqual((c['tp'],c['fn'],c['fp']),(2,0,0))
        r['message']={'markdown':'my-package other'}
        c=measure(labels,[document([r],name='OSV-Scanner')])['tools']['osv-scanner']
        self.assertEqual((c['tp'],c['fn'],c['fp']),(0,2,1))

    def test_tool_merging_invalid_runs_and_empty_labels(self):
        docs=[document([finding()],name=' Semgrep OSS '),document([finding(line=100)],name='SEMGREP PRO'),{'runs':[None,3,{'tool':{'driver':{'name':{}}}},{'tool':None}]}]
        r=measure(self.labels,docs)
        self.assertEqual(set(r['tools']),{'semgrep','unknown'})
        self.assertEqual((r['tools']['semgrep']['tp'],r['tools']['semgrep']['fp']),(1,1))
        empty=measure({'set':'set','defects':[]},[document([],name=' AI Reviewer!! ')])['tools']['ai-reviewer']
        self.assertIsNone(empty['precision']);self.assertIsNone(empty['recall']);self.assertIsNone(empty['f1'])

    def test_non_arrays_and_malformed_entries(self):
        for member in [None,{},'',3]:
            self.assertEqual(self.count(member)['semgrep']['fn'],1)
        self.assertEqual(self.count([None,3,False,{}])['semgrep']['fp'],0)


if __name__=='__main__':
    unittest.main()
