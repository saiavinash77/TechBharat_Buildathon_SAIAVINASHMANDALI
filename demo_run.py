"""
Simple demo runner to reproduce the key flows:
- create invite
- fetch join details
- join org (upsert user)
- list org members
- list action items for a meeting
- dispatch approved items for the meeting

Run with: python demo_run.py
Make sure the server is running at http://127.0.0.1:8000 and GITHUB_TOKEN is set in .env if you want GitHub dispatch.
"""
import json
import sys
import time
from urllib import request, parse

BASE = 'http://127.0.0.1:8000'

def post_json(path, payload):
    url = BASE + path
    data = json.dumps(payload).encode('utf-8')
    req = request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    with request.urlopen(req, timeout=30) as resp:
        return json.load(resp)

def get_json(path):
    url = BASE + path
    with request.urlopen(url, timeout=30) as resp:
        return json.load(resp)


def main():
    print('\n=== Demo runner starting ===')
    try:
        cfg = get_json('/config')
        print('Config:', cfg)
    except Exception as e:
        print('Failed to fetch /config, is server running? error=', e)
        sys.exit(1)

    # Create invite
    print('\n1) Creating invite for demo-org...')
    inv = post_json('/invites', {'org_id': 'demo-org', 'inviter_name': 'demo-runner'})
    print('Invite result:', inv)
    token = inv.get('invite', {}).get('token') or (inv.get('join_url') or '').split('token=')[-1]

    # Fetch join info
    print('\n2) Fetching join details...')
    join_info = get_json(f'/join?token={parse.quote(token)}')
    print('Join info:', join_info)

    # Join
    print('\n3) Posting join (upsert user) ...')
    email = f'demo.runner+{int(time.time())}@example.com'
    join_resp = post_json('/join', {'token': token, 'name': 'Demo Runner', 'email': email, 'github_handle': 'demorunner'})
    print('Join response:', join_resp)

    # List members
    print('\n4) Listing members...')
    members = get_json('/orgs/demo-org/members')
    print('Members:', members)

    # List action items for seeded meeting
    meeting = 'live-test-meeting-1'
    print(f'\n5) Listing action items for meeting {meeting}...')
    ais = get_json(f'/meetings/{meeting}/action-items')
    print('Action items:', json.dumps(ais, indent=2))

    # Dispatch
    print(f'\n6) Dispatching meeting {meeting}...')
    dispatch = post_json(f'/meetings/{meeting}/dispatch', {})
    print('Dispatch response:', json.dumps(dispatch, indent=2))

    print('\n=== Demo runner finished ===')

if __name__ == '__main__':
    main()
