import time
import socket
import requests
from baselayer.app.env import load_env
from skyportal.tests import api


_, cfg = load_env()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 53))
localhost_external_ip = s.getsockname()[0]
s.close()


def test_api_rate_limiting(view_only_token):
    # In case this test gets run after those defined below
    time.sleep(5)
    n_successful_requests = 0
    status = 200
    while status == 200 and n_successful_requests < 100:
        r = requests.get(
            f'http://{localhost_external_ip}:{cfg["ports.app"]}/api/sysinfo',
            headers={'Authorization': f'token {view_only_token}'},
        )
        status = r.status_code
        if status == 200:
            n_successful_requests += 1
    assert 14 <= n_successful_requests <= 16
    r = requests.get(
        f'http://{localhost_external_ip}:{cfg["ports.app"]}/api/sysinfo',
        headers={'Authorization': f'token {view_only_token}'},
    )
    assert r.status_code == 429

    time.sleep(5)

    r = requests.get(
        f'http://{localhost_external_ip}:{cfg["ports.app"]}/api/sysinfo',
        headers={'Authorization': f'token {view_only_token}'},
    )
    assert r.status_code == 200


def test_rate_limited_requests_ok(view_only_token):
    for i in range(30):
        r = requests.get(
            f'http://{localhost_external_ip}:{cfg["ports.app"]}/api/sysinfo',
            headers={'Authorization': f'token {view_only_token}'},
        )
        assert r.status_code == 200
        time.sleep(0.2)


def test_localhost_unlimited(view_only_token):
    for i in range(30):
        status, _ = api('GET', 'sysinfo', token=view_only_token)
        assert status == 200
