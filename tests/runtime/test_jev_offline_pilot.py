from __future__ import annotations

# @codebase_provenance_JEO

import socket
import urllib.request

import pytest

from scripts.jev_offline_pilot import (
    OfflineNetworkAttempt,
    load_catalog,
    offline_network_guard,
)


def test_offline_pilot_catalog_has_unique_ids_and_local_test_targets() -> None:
    catalog = load_catalog()
    scenarios = catalog["scenarios"]
    ids = [scenario["id"] for scenario in scenarios]

    assert len(ids) == len(set(ids))
    assert len(scenarios) >= 12
    assert all(scenario["test_ids"] for scenario in scenarios)
    assert all(scenario["response_provenance"] for scenario in scenarios)


def test_offline_network_guard_blocks_http_dns_and_tcp_dispatch() -> None:
    with offline_network_guard() as attempts:
        with pytest.raises(OfflineNetworkAttempt):
            socket.create_connection(("203.0.113.1", 80), timeout=0.01)
        with pytest.raises(OfflineNetworkAttempt):
            socket.getaddrinfo("example.invalid", 80)
        with pytest.raises(OfflineNetworkAttempt):
            urllib.request.OpenerDirector.open(object(), "https://example.invalid/")
    assert attempts["count"] == 3
