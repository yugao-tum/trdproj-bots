"""Offline reference contract, NOT an execution of NOAA obs.js or moment."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import re

ISO = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})?$')
EVIDENCE_FIELDS = ('station_timezone_payload', 'raw_timestamp_payload',
                   'executed_source_version', 'moment_timezone_version')


def normalize(raw_time, station_timezone, browser_timezone, evidence):
    """Return explicit reference candidates; never guess UTC or choose a DST fold.

    evidence: four fields above with missing/unverified/verified state and optional
    naive_interpretation='browser_local_reference'. The latter explicitly selects
    a synthetic reference policy; it does NOT attest to moment behavior.
    Browser zone is irrelevant for offset-bearing timestamps but validated if given.
    """
    result = {'raw_time': raw_time, 'station_timezone': station_timezone,
              'browser_timezone': browser_timezone, 'implementation': 'python-zoneinfo-reference',
              'actual_viewer_proven': False, 'candidates': []}
    def stop(status, reason):
        return dict(result, status=status, reason=reason)
    if not isinstance(evidence, dict):
        return stop('rejected', 'invalid_evidence_object')
    states = {k: evidence.get(k, 'missing') for k in EVIDENCE_FIELDS}
    if any(v not in ('missing', 'unverified', 'verified') for v in states.values()):
        return stop('rejected', 'invalid_evidence_status')
    result['evidence_status'] = states
    result['unresolved_evidence'] = [k for k, v in states.items() if v != 'verified']
    if not station_timezone:
        return stop('uncertain', 'missing_station_timezone')
    zones = {}
    for label, value in (('station', station_timezone), ('browser', browser_timezone)):
        if value is None or value == '':
            continue
        # Explicit IANA names or UTC, not ambiguous abbreviations/fixed-offset aliases.
        if not isinstance(value, str) or (value != 'UTC' and '/' not in value):
            return stop('rejected', 'invalid_' + label + '_iana_timezone')
        try:
            zones[label] = ZoneInfo(value)
        except (ValueError, ZoneInfoNotFoundError):
            return stop('rejected', 'invalid_' + label + '_iana_timezone')
    if not isinstance(raw_time, str) or not ISO.fullmatch(raw_time):
        return stop('rejected', 'unsupported_timestamp_format')
    offset = re.search(r'([+-])(\d{2}):(\d{2})$', raw_time)
    if offset and (int(offset[2]) > 23 or int(offset[3]) > 59):
        return stop('rejected', 'invalid_offset_range')
    if raw_time.endswith('-00:00'):
        return stop('uncertain', 'unknown_negative_zero_offset')
    try:
        dt = datetime.fromisoformat(raw_time.replace('Z', '+00:00'))
    except ValueError:
        return stop('rejected', 'invalid_timestamp_value')
    if not 2 <= dt.year <= 9998:
        return stop('rejected', 'timestamp_outside_reference_safe_year_range')
    result['offset_present'] = dt.tzinfo is not None
    result['station_differs_from_browser'] = (station_timezone != browser_timezone
                                                if browser_timezone else None)
    instants = []
    if dt.tzinfo is not None:
        # obs.js L365 parses first, then .tz(TIMEZONE): a known instant converts.
        instants = [dt.astimezone(timezone.utc)]
        result['parse_basis'] = 'explicit_offset'
    else:
        # A reference choice only; this is not a moment default/fallback emulation.
        if 'browser' not in zones:
            return stop('uncertain', 'missing_browser_timezone_for_naive_input')
        if evidence.get('naive_interpretation') != 'browser_local_reference':
            return stop('uncertain', 'unestablished_naive_parse_context')
        result['parse_basis'] = 'explicit_browser_local_reference_policy'
        # Round-trip both folds. Reject imaginary spring wall times and preserve
        # both distinct UTC instants for an ambiguous fall wall time.
        for fold in (0, 1):
            candidate = dt.replace(tzinfo=zones['browser'], fold=fold).astimezone(timezone.utc)
            if candidate.astimezone(zones['browser']).replace(tzinfo=None) == dt:
                if candidate not in instants:
                    instants.append(candidate)
        instants.sort()
        if not instants:
            return stop('rejected', 'nonexistent_browser_wall_time')
    for instant in instants:
        local = instant.astimezone(zones['station'])
        result['candidates'].append({
            'utc': instant.isoformat().replace('+00:00', 'Z'),
            'station_time': local.isoformat(), 'station_fold': local.fold,
            'station_date': local.date().isoformat(),
            'utc_date': instant.date().isoformat(),
            'utc_station_date_differ': instant.date() != local.date(),
            'browser_time': instant.astimezone(zones['browser']).isoformat()
                            if 'browser' in zones else None})
    return stop('ambiguous' if len(instants) == 2 else 'normalized_reference',
                'two_distinct_instants' if len(instants) == 2 else 'reference_conversion_only')
