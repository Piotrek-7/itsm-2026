# ai-generated: 100% - Codex wrote a pytest runner reporting actual collected outcomes.
from pathlib import Path
import pytest


class Summary:
    def __init__(self):
        self.passed = 0
        self.failed = 0

    def pytest_runtest_logreport(self, report):
        if report.when == 'call' and report.passed:
            self.passed += 1
        if report.failed:
            self.failed += 1

    def pytest_collectreport(self, report):
        if report.failed:
            self.failed += 1


if __name__ == '__main__':
    summary = Summary()
    code = pytest.main(['-q', '-p', 'no:cacheprovider', str(Path(__file__).parent)], plugins=[summary])
    failures = summary.failed or (1 if code else 0)
    print(f'ITSMLAB-TESTS: passed={summary.passed} failed={failures}', flush=True)
    raise SystemExit(int(code) if code else (0 if summary.passed >= 10 else 1))
