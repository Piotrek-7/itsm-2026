# ai-generated: 100% - Codex tested the course contract at boundary values with an independent minute-step oracle.
from datetime import datetime, timedelta
import math
import pytest
import slaclock


def minute(moment):
    return moment.replace(second=0, microsecond=0)


def open_minute(moment):
    return moment.weekday() in (0, 1, 2, 3, 4) and 8 <= moment.hour < 16


def oracle_add(start, count):
    current = minute(start)
    while not open_minute(current):
        current += timedelta(minutes=1)
    for _ in range(count):
        while not open_minute(current):
            current += timedelta(minutes=1)
        current += timedelta(minutes=1)
    return current


def oracle_between(start, end):
    current, end = minute(start), minute(end)
    answer = 0
    while current < end:
        answer += open_minute(current)
        current += timedelta(minutes=1)
    return answer


def test_all_priority_cells_and_vip():
    rows = [('P1', 'P2', 'P3'), ('P2', 'P3', 'P4'), ('P3', 'P4', 'P4')]
    vip_rows = [('P1', 'P2', 'P2'), ('P2', 'P2', 'P2'), ('P2', 'P2', 'P2')]
    for i in range(3):
        for u in range(3):
            assert slaclock.priority_of(i+1, u+1) == rows[i][u]
            assert slaclock.priority_of(i+1, u+1, False) == rows[i][u]
            assert slaclock.priority_of(i+1, u+1, True) == vip_rows[i][u]
    for value in [0, 4, -1, 99, 1.0, 2.0, True, False, '1', None]:
        for impact, urgency in [(value, 1), (1, value)]:
            with pytest.raises(ValueError):
                slaclock.priority_of(impact, urgency)


def test_exact_targets():
    for priority, expected in [('P1', (15, 240)), ('P2', (60, 480)), ('P3', (240, 1440)), ('P4', (480, 4320))]:
        assert slaclock.targets(priority) == expected
    for invalid in ['p1', ' P1', 'P1 ', 'P0', 'P5', '', 'P11']:
        with pytest.raises(ValueError):
            slaclock.targets(invalid)
        with pytest.raises(ValueError):
            slaclock.escalation_tier(invalid, False, 0)


def test_sla_thresholds_without_rounding():
    for target in range(1, 122):
        warning = math.ceil(target * 3 / 4)
        for elapsed in sorted({0, max(0, warning-1), warning, target, target+1, target*2}):
            expected = 'breached' if elapsed > target else 'warning' if elapsed >= warning else 'ok'
            assert slaclock.sla_state(elapsed, target) == expected
    for elapsed, target in [(-1, 15), (-500, 1), (0, 0), (1, -1)]:
        with pytest.raises(ValueError):
            slaclock.sla_state(elapsed, target)


def test_business_hours_every_weekday_and_boundary():
    monday = datetime(2026, 11, 16)
    for day in range(7):
        for h, m in [(0, 0), (7, 59), (8, 0), (8, 1), (15, 59), (16, 0), (16, 1), (23, 59)]:
            moment = monday + timedelta(days=day, hours=h, minutes=m, seconds=59, microseconds=999999)
            assert slaclock.is_business_time(moment) == open_minute(moment)


def test_add_business_minutes_against_independent_oracle():
    monday = datetime(2026, 11, 16)
    for day in range(7):
        for h, m in [(7, 59), (8, 0), (15, 59), (16, 0)]:
            start = monday + timedelta(days=day, hours=h, minutes=m, seconds=47, microseconds=50)
            for count in [0, 1, 15, 479, 480, 481, 960]:
                due = slaclock.add_business_minutes(start, count)
                assert due == oracle_add(start, count)
                assert slaclock.business_minutes_between(start, due) == count
    with pytest.raises(ValueError):
        slaclock.add_business_minutes(monday, -1)
    assert slaclock.add_business_minutes(datetime(2026, 11, 16, 8), 480) == datetime(2026, 11, 16, 16)
    assert slaclock.add_business_minutes(datetime(2026, 11, 20, 15, 59), 2) == datetime(2026, 11, 23, 8, 1)


def test_business_interval_clipping_and_minute_resolution():
    cases = [
        (datetime(2026, 11, 16, 7, 59), datetime(2026, 11, 16, 8, 1)),
        (datetime(2026, 11, 16, 15, 59), datetime(2026, 11, 16, 16, 1)),
        (datetime(2026, 11, 20, 15, 59), datetime(2026, 11, 23, 8, 1)),
        (datetime(2026, 11, 21, 0), datetime(2026, 11, 23, 7, 59)),
        (datetime(2026, 11, 16, 8), datetime(2026, 11, 19, 16)),
        (datetime(2026, 12, 31, 15, 59), datetime(2027, 1, 4, 8, 1)),
    ]
    for start, end in cases:
        assert slaclock.business_minutes_between(start, end) == oracle_between(start, end)
        assert slaclock.business_minutes_between(start, start) == 0
        with pytest.raises(ValueError):
            slaclock.business_minutes_between(end, start)
    assert slaclock.business_minutes_between(datetime(2026, 11, 16, 8, 0, 59), datetime(2026, 11, 16, 8, 1, 1)) == 1
    assert slaclock.business_minutes_between(datetime(2026, 11, 16, 8, 0, 59), datetime(2026, 11, 16, 8, 0, 1)) == 0


def test_calendar_span_limit_inclusive_and_due_limit():
    # Wednesday to Friday exactly 366 dates later: the final day must still count.
    start = datetime(2025, 1, 1, 8)
    end = start + timedelta(days=366, hours=8)
    expected = sum(480 for day in range(367) if (start + timedelta(days=day)).weekday() < 5)
    assert slaclock.business_minutes_between(start, end) == expected
    assert slaclock.add_business_minutes(start, expected) == end
    with pytest.raises(ValueError):
        slaclock.add_business_minutes(start, expected+1)
    with pytest.raises(ValueError):
        slaclock.business_minutes_between(start, start + timedelta(days=367))


def test_escalation_truth_table_and_caps():
    table = {'P1': ((1, 1, 2), (3, 3, 3)), 'P2': ((1, 1, 2), (2, 2, 3)),
             'P3': ((0, 0, 1), (1, 1, 2)), 'P4': ((0, 0, 1), (1, 1, 2))}
    for priority, (normal, breached) in table.items():
        for reopens in [0, 1, 2, 3, 50]:
            index = min(reopens, 2)
            assert slaclock.escalation_tier(priority, False, reopens) == normal[index]
            assert slaclock.escalation_tier(priority, True, reopens) == breached[index]
        with pytest.raises(ValueError):
            slaclock.escalation_tier(priority, False, -1)


def test_duration_grammar_and_units():
    valid = {'1m': 1, '90m': 90, '60m': 60, '4h': 240, '1h30m': 90,
             '2d': 2880, '1d4h': 1680, '1d0h5m': 1445, '0h60m': 60,
             '0d90m': 90, '1h59m': 119, '24h': 1440, '1d24h': 2880,
             '01h01m': 61, '  2h5m\t': 125, '1d0h0m': 1440}
    for text, expected in valid.items():
        assert slaclock.parse_duration(text) == expected
    for invalid in ['', ' ', '0m', '0h', '0d0h0m', '1.5h', '30m1h', '-5m', '1 h',
                    '1H', '1h60m', '1d60m', '1d0h99m', '1h1h', '3mm', '1m junk',
                    '+1m', '1d 2h', 'd', 'h', 'm', '1h\n2m', '1h0mextra']:
        with pytest.raises(ValueError):
            slaclock.parse_duration(invalid)
