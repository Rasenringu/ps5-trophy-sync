"""Reviewed publisher collection membership; never an unlock-state source.

Application/set namespaces remain distinct. Group only existing state and native
activity in the same installation profile. No matching by a game's name/region.
"""
import json
from pathlib import Path

VERIFIED_COLLECTIONS = json.loads(Path(__file__).with_suffix('.json').read_text(encoding='utf-8'))


def group_collections(rows):
    activities = {}
    for row in rows:
        data = row['data']
        application = data.get('native_observation', {}).get('application_title_id')
        if (not row['mock'] and row['kind'] == 'activity'
                and data.get('activity_source', row['source']) == 'ps5_native'
                and data.get('duration_basis') == 'native_foreground_seconds'
                and data.get('profile_binding') == 'activity_header_single_local_user'
                and application in VERIFIED_COLLECTIONS):
            activities.setdefault((row['profile_uuid'], application), []).append(row)

    for (profile, application), sessions in activities.items():
        collection = VERIFIED_COLLECTIONS[application]
        members = [row for row in rows if not row['mock']
                   and row['profile_uuid'] == profile and row['source'] == 'ps4_bc'
                   and row['kind'] == 'trophy'
                   and row['data'].get('profile_binding') == 'inner_local_user_and_foreground_path'
                   and row['data']['title_id'] in collection['trophy_sets']]
        if not members:
            continue
        # A component can also have its own logger identity. Include it only
        # after the existing exact inner-state binding resolved that activity;
        # never copy the launcher duration to each component.
        component_sessions = [row for row in rows if not row['mock']
                              and row['profile_uuid'] == profile and row['kind'] == 'activity'
                              and row['source'] == 'ps4_bc'
                              and row['data'].get('activity_source') == 'ps5_native'
                              and row['data'].get('title_binding') == 'ps4_inner_application_id'
                              and row['data']['title_id'] in collection['trophy_sets']]
        for row in members + sessions + component_sessions:
            # Preserve title_id/trophy_id for image authorization, comparisons
            # and secret metadata. The UI groups using this separate identity.
            row['data']['collection_title_id'] = application
            row['data']['collection_title'] = collection['title']
        for row in members:
            row['data']['collection_component_title_id'] = row['data']['title_id']
        for row in component_sessions:
            # A launcher session may already have a unique set alias. That is
            # membership evidence only: it cannot assign launcher time to a game.
            if row['data'].get('native_observation', {}).get('application_title_id') != application:
                row['data']['collection_component_title_id'] = row['data']['title_id']
        for row in sessions:
            row['data'].setdefault('activity_source', row['source'])
            row['source'] = 'ps4_bc'
