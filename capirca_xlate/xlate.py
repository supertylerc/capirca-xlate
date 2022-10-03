from enum import Enum
from ipaddress import IPv4Network, IPv6Network
import pathlib
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape, Template
from pydantic import BaseModel as PydanticBaseModel, validator
from ruamel.yaml import YAML


class BaseModel(PydanticBaseModel):
    class Config:
        use_enum_values = True


class Platform(str, Enum):
    cisconx = "cisconx"


class TargetOptions(str, Enum):
    extended = "extended"
    object_group = "object-group"
    inet6 = "inet6"
    mixed = "mixed"


class Target(BaseModel):
    platform: Platform
    options: list[TargetOptions] | None


class Protocol(str, Enum):
    tcp = "tcp"
    udp = "udp"
    icmp = "icmp"


class Action(str, Enum):
    accept = "accept"
    deny = "deny"
    reject = "reject"
    next = "next"
    reject_with_tcp_rst = "reject-with-tcp-rst"


class Option(str, Enum):
    tcp_established = "tcp-established"
    established = "established"


class ACE(BaseModel):
    source_addresses: list[str] | None
    source_excludes: list[str] | None
    destination_addresses: list[str] | None
    destination_excludes: list[str] | None
    source_ports: list[str] | None
    destination_ports: list[str] | None
    comment: str | None
    action: Action
    protocols: list[Protocol] | None
    options: list[Option] | None
    ticket: str | None
    name: str


class ACL(BaseModel):
    name: str
    comment: str | None
    aces: list[ACE]
    targets: list[Target]


def load_yaml(fpath: pathlib.Path) -> dict[str, Any]:
    yaml = YAML(typ="safe")
    return yaml.load(fpath)


def load_acl(fpath: pathlib.Path) -> ACL:
    return ACL(**load_yaml(fpath))


def load_template(template_name: str) -> Template:
    env = Environment(
        loader=PackageLoader("capirca_xlate"), autoescape=select_autoescape()
    )
    return env.get_template(template_name)


def xlate_acl(acl: ACL) -> str:
    return load_template("acl.pol.j2").render(acl=acl)


class Service(BaseModel):
    name: str
    protocol: Protocol
    port: int

    @validator("port")
    def port_must_be_between_1_and_256(cls, v: int) -> int:
        if v < 1 or v > 65535:
            raise ValueError(
                f"Port must be between 1 and 65535: {v} is outside of range"
            )
        return v


class Network(BaseModel):
    name: str
    address: IPv4Network | IPv6Network


class ServiceReferences(BaseModel):
    name: str
    services: list[str]


class NetworkReferences(BaseModel):
    name: str
    networks: list[str]


class Definitions(BaseModel):
    services: list[Service]
    networks: list[Network]
    service_references: list[ServiceReferences]
    network_references: list[NetworkReferences]

    @validator("network_references", each_item=True)
    def network_must_exist(
        cls, v: NetworkReferences, values: dict[str, Any]
    ) -> NetworkReferences:
        network_names = [n.name for n in values["networks"]]
        network_name_references = [n for n in v.networks]
        for network_name_reference in network_name_references:
            if network_name_reference not in network_names:
                raise ValueError(
                    f"Network Must Exist: {network_name_reference} definition not found"
                )
        return v

    @validator("service_references", each_item=True)
    def service_must_exist(
        cls, v: ServiceReferences, values: dict[str, Any]
    ) -> ServiceReferences:
        service_names = [s.name for s in values["services"]]
        service_name_references = [s for s in v.services]
        for service_name_reference in service_name_references:
            if service_name_reference not in service_names:
                raise ValueError(
                    f"Service Must Exist: {service_name_reference} definition not found"
                )
        return v


def load_def(fpath: pathlib.Path) -> Definitions:
    return Definitions(**load_yaml(fpath))


def xlate_net(definitions: Definitions) -> str:
    return load_template("def.net.j2").render(
        networks=definitions.networks,
        network_references=definitions.network_references,
    )


def xlate_svc(definitions: Definitions) -> str:
    return load_template("def.svc.j2").render(
        services=definitions.services,
        service_references=definitions.service_references,
    )
