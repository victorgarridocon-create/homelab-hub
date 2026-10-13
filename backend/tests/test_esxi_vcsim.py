"""Integration test against VMware's vSphere API simulator (vcsim). Skipped unless it's running:

    docker run -d -p 8989:8989 vmware/vcsim -l 0.0.0.0:8989 -esx -username lector -password secret
    VCSIM_HOST=127.0.0.1:8989 VCSIM_USER=lector VCSIM_PASSWORD=secret pytest tests/test_esxi_vcsim.py
"""
import os

import pytest

from app.integrations import IntegrationError, esxi

HOST = os.environ.get("VCSIM_HOST")
USER = os.environ.get("VCSIM_USER", "user")
PASSWORD = os.environ.get("VCSIM_PASSWORD", "pass")

pytestmark = pytest.mark.skipif(not HOST, reason="set VCSIM_HOST to run against vcsim")


def test_reads_hosts_and_vms():
    data = esxi.fetch_inventory(HOST, USER, PASSWORD, verify_ssl=False)
    assert data["hosts"] and data["guests"]
    host = data["hosts"][0]
    assert host["os"].startswith("VMware ESXi") and host["cpu_cores"] and host["ram_gb"]
    vm = data["guests"][0]
    assert vm["node"] in {h["name"] for h in data["hosts"]}
    assert vm["mac_address"] and vm["disk_gb"] and vm["status"] == "running"


def test_rejects_self_signed_certificate_when_verifying():
    with pytest.raises(IntegrationError, match="SSL"):
        esxi.fetch_inventory(HOST, USER, PASSWORD, verify_ssl=True)
