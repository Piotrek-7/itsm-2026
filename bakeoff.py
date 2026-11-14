# ai-generated: 100% - Codex implemented CI-SPEC P-14 through P-24 using only the standard library.
"""Measure scanner detections under the published course matching rules."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote

CWES = {
    'secret': {259, 260, 321, 798},
    'injection': {74, 77, 78, 79, 80, 88, 89, 90, 91, 94, 95, 96, 611, 776, 917, 943, 1336},
    'deserialization': {502},
    'weak-crypto': {261, 326, 327, 328, 330, 331, 338, 759, 760, 916},
    'insecure-transport': {295, 297, 319, 322, 757},
    'path-traversal': {22, 23, 35, 36, 73},
    'ssrf': {918},
    'vulnerable-dependency': {937, 1035, 1104, 1395},
    'misconfiguration': {16, 215, 250, 489, 668, 732, 1188},
    'access-control': {284, 285, 639, 862, 863},
}
SEMGREP_NAMES = {'semgrep', 'semgrep oss', 'semgrep ce', 'semgrep community edition', 'semgrep pro'}


def obj(value):
    return value if isinstance(value, dict) else {}


def array(value):
    return value if isinstance(value, list) else []


def tool_id(run):
    name = obj(obj(run.get('tool')).get('driver')).get('name')
    if not isinstance(name, str):
        return 'unknown'
    name = name.strip().lower()
    if name in SEMGREP_NAMES:
        return 'semgrep'
    return re.sub('[^a-z0-9]+', '-', name).strip('-') or 'unknown'


def tags(value):
    return [x for x in array(obj(obj(value).get('properties')).get('tags')) if isinstance(x, str)]


def result_classes(result, driver, tool):
    own = obj(result.get('properties')).get('class')
    if isinstance(own, str) and own in CWES:
        return {own}
    rule = next((r for r in array(driver.get('rules'))
                 if isinstance(r, dict) and r.get('id') == result.get('ruleId')), {})
    if tool == 'gitleaks':
        return {'secret'}
    if tool in ('grype', 'osv-scanner'):
        return {'vulnerable-dependency'}
    if tool == 'trivy':
        names = {'vulnerability': 'vulnerable-dependency', 'secret': 'secret',
                 'misconfiguration': 'misconfiguration'}
        matched = {names[t.lower()] for t in tags(rule) if t.lower() in names}
        if matched:
            return matched
    numbers = set()
    for tag in tags(result) + tags(rule):
        for number in re.findall(r'(?<![A-Za-z0-9])CWE-([0-9]+)', tag, re.IGNORECASE):
            try:
                numbers.add(int(number))
            except ValueError:
                pass
    return {name for name, cwes in CWES.items() if numbers & cwes} or {'other'}


def normalize_file(uri, root):
    path = unquote(uri)
    if path[:7].lower() == 'file://':
        path = path[7:]
    if path.startswith('./'):
        path = path[2:]
    parts = path.split('/')
    indices = [i for i, part in enumerate(parts) if part == root]
    return '/'.join(parts[indices[-1]:]) if indices else None


def lines(physical):
    region = obj(physical.get('region'))
    start = region.get('startLine')
    if type(start) is not int or start < 1:
        return None, None
    end = region.get('endLine')
    return start, max(start, end) if type(end) is int else start


def package_name(value):
    return re.sub(r'[-_.]+', '-', value.lower())


def matches(result, classes, file, start, end, defect):
    if file != defect['file'] or defect['class'] not in classes:
        return False
    if defect['class'] == 'vulnerable-dependency':
        text = obj(result.get('message')).get('text')
        if not isinstance(text, str):
            return False
        tokens = re.findall('[A-Za-z0-9._-]+', text)
        return package_name(defect['package']) in {package_name(t.strip('._-')) for t in tokens}
    return start is not None and start <= defect['end_line'] and defect['start_line'] <= end


def measure(labels, documents):
    root, defects = labels['set'], labels['defects']
    tools = {}
    for document in documents:
        for run in array(obj(document).get('runs')):
            if not isinstance(run, dict):
                continue
            tool = tool_id(run)
            found, false_positives = tools.setdefault(tool, (set(), set()))
            driver = obj(obj(run.get('tool')).get('driver'))
            for result in array(run.get('results')):
                if not isinstance(result, dict):
                    continue
                if result.get('kind') not in (None, 'fail') or result.get('suppressions'):
                    continue
                locations = array(result.get('locations'))
                physical = obj(obj(locations[0]).get('physicalLocation')) if locations else {}
                uri = obj(physical.get('artifactLocation')).get('uri')
                if not isinstance(uri, str) or not uri:
                    continue
                file = normalize_file(uri, root)
                if file is None:
                    continue
                start, end = lines(physical)
                classes = result_classes(result, driver, tool)
                hit = {index for index, defect in enumerate(defects)
                       if matches(result, classes, file, start, end, defect)}
                if hit:
                    found.update(hit)
                else:
                    rule = result.get('ruleId')
                    false_positives.add((rule if isinstance(rule, str) else None, file, start, end))
    output = {'set': root, 'defects': len(defects), 'tools': {}}
    for tool, (found, false_positives) in sorted(tools.items()):
        tp, fp, fn = len(found), len(false_positives), len(defects) - len(found)
        def fraction(numerator, denominator):
            return round(numerator / denominator, 4) if denominator else None
        output['tools'][tool] = {'tp': tp, 'fp': fp, 'fn': fn,
                                'precision': fraction(tp, tp + fp),
                                'recall': fraction(tp, tp + fn),
                                'f1': fraction(2 * tp, 2 * tp + fp + fn)}
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--labels', required=True)
    parser.add_argument('sarif', nargs='+')
    args = parser.parse_args()
    labels = json.loads(Path(args.labels).read_text(encoding='utf-8-sig'))
    documents = [json.loads(Path(path).read_text(encoding='utf-8-sig')) for path in args.sarif]
    print(json.dumps(measure(labels, documents), indent=2))


if __name__ == '__main__':
    main()
