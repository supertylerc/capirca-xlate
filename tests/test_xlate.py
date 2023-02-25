from ipaddress import IPv4Network
from capirca_xlate.xlate import (
    Definitions,
    Network,
    NetworkReferences,
    Protocol,
    Service,
    ServiceReferences,
)
import pytest


@pytest.mark.parametrize("port", [-65536, -65535, -1, 0, 65536, 70000, 512000])
def test_service_port_validation(port: int) -> None:
    with pytest.raises(ValueError):
        Service(name="Invalid Port Validator", protocol=Protocol("tcp"), port=port)


def test_service_port_all_valid_ranges() -> None:
    for port in range(1, 65536):
        Service(name="Valid Port Validator", protocol=Protocol("tcp"), port=port)


def test_definitions_network_references_valid() -> None:
    n = Network(name="example_net", address=IPv4Network("192.168.0.0/24"))
    nr = NetworkReferences(name="example_net_ref", networks=["example_net"])
    Definitions(
        services=[], networks=[n], service_references=[], network_references=[nr]
    )


def test_definitions_network_references_invalid() -> None:
    n = Network(name="example_net", address=IPv4Network("192.168.0.0/24"))
    nr = NetworkReferences(
        name="example_net_ref", networks=["example_net", "example_net_2"]
    )
    with pytest.raises(ValueError):
        Definitions(
            services=[], networks=[n], service_references=[], network_references=[nr]
        )


def test_definitions_service_references_valid() -> None:
    s = Service(name="example_svc", protocol=Protocol("tcp"), port=53)
    sr = ServiceReferences(name="example_svc_ref", services=["example_svc"])
    Definitions(
        services=[s], networks=[], service_references=[sr], network_references=[]
    )


def test_definitions_service_references_invalid() -> None:
    s = Service(name="example_svc", protocol=Protocol("tcp"), port=53)
    sr = ServiceReferences(
        name="example_svc_ref", services=["example_svc", "example_svc_2"]
    )
    with pytest.raises(ValueError):
        Definitions(
            services=[s], networks=[], service_references=[sr], network_references=[]
        )
