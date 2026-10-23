"""Present console observations without inventing dates or foreground counters.

Original observations stay in records. Server receipt times bound candidate
console dates independently of the browser's timezone and later syncs.
"""
from datetime import datetime, timedelta, timezone

TIME_FIELDS = ('started_at', 'ended_at', 'unlocked_at')
EPOCH = datetime(1, 1, 1, tzinfo=timezone.utc)


def native_locked_observation(flags, first_raw, second_raw):
    """Exact supported PS5 shapes; the flags-16 shape was console-menu checked."""
    try:
        first, second = int(first_raw), int(second_raw)
    except (TypeError, ValueError):
        return False
    return ((flags == 0 and first == second == 0)
            or (flags == 16 and first == 0 and 62135596800000000 <= second <= 315537897599999999))


def _time_key(data, field):
    if data.get(field):
        return data[field]
    observation = data.get('native_observation', {})
    if (field == 'unlocked_at' and data.get('unlocked') is True
            and observation.get('raw_flags') == 17 and observation.get('first_raw') not in (None, '0')):
        return ('native_first', observation['first_raw'])
    return None


def stamp_receipt(data, previous, received, previous_received=None):
    previous = previous or {}
    earlier = previous.get('timestamp_received_at', {})
    data['timestamp_received_at'] = {
        field: earlier.get(field, previous_received or received) if _time_key(data, field) == _time_key(previous, field) else received
        for field in TIME_FIELDS if _time_key(data, field)
    }


def present_observation(raw, kind, source, upper_bound):
    data = dict(raw)
    if kind == 'trophy':
        observation = data.get('native_observation', {})
        if (source == 'ps5_native' and data.get('unlocked') is None
                and native_locked_observation(observation.get('raw_flags'), observation.get('first_raw'), observation.get('second_raw'))):
            data['unlocked'] = False
            data['observed_unlock_state'] = False
        if data.get('unlocked') is None:
            data['state_reason'] = ('unsupported_native_flags' if source == 'ps5_native'
                                    else 'unsupported_trophy_state')
        # The native PS5 epoch/first field was independently corroborated against
        # a console-displayed unlock minute. Never apply it to PS4 or unknown flags.
        if (source == 'ps5_native' and data.get('unlocked') is True
                and not data.get('unlocked_at') and observation.get('raw_flags') == 17):
            try:
                value = int(observation['first_raw'])
                stamp = EPOCH + timedelta(microseconds=value)
                if value > 0 and stamp.year >= 1970:
                    data['unlocked_at'] = stamp.isoformat().replace('+00:00', 'Z')
                    data['clock'] = 'uncertain'
            except (KeyError, ValueError, OverflowError, TypeError):
                pass
    elif kind == 'activity' and data.get('duration_seconds') is None:
        event = data.get('native_observation', {}).get('event')
        data['duration_reason'] = ('missing_session_end' if event == 'ApplicationSessionStart'
                                   else 'session_crashed' if event == 'ApplicationSessionCrash'
                                   else 'missing_foreground_counter')
    bounds = raw.get('timestamp_received_at', {})
    for field in TIME_FIELDS:
        value = data.get(field)
        if not value:
            continue
        try:
            if not isinstance(value, str):
                raise ValueError('Invalid source time')
            stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if stamp.utcoffset() is None:
                raise ValueError('Unspecified timezone')
            # Receipt times have whole-second precision; allow that exact second.
            limit = min(bounds.get(field, upper_bound), upper_bound)
            if stamp.timestamp() >= limit + 1:
                data[field] = None
                data['timestamp_status'] = 'after_observation'
        except (ValueError, TypeError, OverflowError, OSError):
            data[field] = None
            data['timestamp_status'] = 'invalid_source_time'
    # A missing start/end does not invalidate the independently recorded counter.
    return data
