from capirca_xlate.xlate import Protocol, Service
import pytest


@pytest.mark.parametrize("port", [-65536, -65535, -1, 0, 65536, 70000, 512000])
def test_service_port_validation(port: int) -> None:
    with pytest.raises(ValueError):
        Service(name="Invalid Port Validator", protocol=Protocol("tcp"), port=port)


def test_service_port_all_valid_ranges() -> None:
    for port in range(1, 65536):
        Service(name="Invalid Port Validator", protocol=Protocol("tcp"), port=port)
