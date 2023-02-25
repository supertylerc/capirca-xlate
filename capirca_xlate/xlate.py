from enum import Enum
from ipaddress import IPv4Network, IPv6Network
import pathlib
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape, Template
from pydantic import BaseModel as PydanticBaseModel, validator, Field
from ruamel.yaml import YAML


class BaseModel(PydanticBaseModel):
    class Config:
        use_enum_values = True


class Platform(str, Enum):
    """A list of supported Capirca Platforms."""

    arista = "arista"
    aruba = "aruba"
    brocade = "brocade"
    cisco = "cisco"
    ciscoasa = "ciscoasa"
    cisconx = "cisconx"
    ciscoxr = "ciscoxr"
    cloudarmor = "cloudarmor"
    gce = "gce"
    gcp_hf = "gcp_hf"
    ipset = "ipset"
    iptables = "iptables"
    juniper = "juniper"
    juniperevo = "juniperevo"
    junipermsmpc = "junipermsmpc"
    junipersrx = "junipersrx"
    k8s = "k8s"
    nftables = "nftables"
    nsxv = "nsxv"
    packetfilter = "packetfilter"
    paloaltofw = "paloaltofw"
    pcap = "pcap"
    speedway = "speedway"
    srxlo = "srxlo"
    windows_advfirewall = "windows_advfirewall"


class TargetOptions(str, Enum):
    """A list of extra options supported by Capirca's ``target`` param."""

    extended = "extended"
    object_group = "object-group"
    inet6 = "inet6"
    mixed = "mixed"


class Target(BaseModel):
    """A combination of `Platform` and `TargetOptions` for defining a target platform."""

    platform: Platform
    options: list[TargetOptions] | None


class Protocol(str, Enum):
    """A list of IP protocols supported by ACLs."""

    tcp = "tcp"
    udp = "udp"
    icmp = "icmp"


class Action(str, Enum):
    """A list of actions an ACL can take that are supported by Capirca."""

    accept = "accept"
    deny = "deny"
    reject = "reject"
    next = "next"
    reject_with_tcp_rst = "reject-with-tcp-rst"


class Option(str, Enum):
    """A list of protocol-level additional options supported by Capirca."""

    tcp_established = "tcp-established"
    established = "established"


class ACE(BaseModel):
    """Parameters that can be used when defining an individual Access Control Entry."""

    source_addresses: list[str] | None = Field(
        description="A list of Capirca-defined network objects for filtering the source address."
    )
    source_excludes: list[str] | None = Field(
        description="A list of Capirca-defined sources to exclude from `ACE.source_addresses`."
    )
    destination_addresses: list[str] | None = Field(
        description="A list of Capirca-defined network objects for filtering the destination address."
    )
    destination_excludes: list[str] | None = Field(
        description="A list of Capirca-defined sources to exclude from `ACE.destination_addresses`."
    )
    source_ports: list[str] | None = Field(
        description="A list of Capirca-defined ports to filter source ports."
    )
    destination_ports: list[str] | None = Field(
        description="A list of Capirca-defined ports to filter destination ports."
    )
    comment: str | None = Field(
        description="An ACE comment, usually rendered as a ``remark``."
    )
    action: Action = Field(description="A Capirca-supported `Action`.")
    protocols: list[Protocol] | None = Field(
        description="A list of IP protocols against which to filter."
    )
    options: list[Option] | None = Field(
        description="A list of additional filtering options, such as TCP Established, for filtering traffic."
    )
    ticket: str | None = Field(
        description="A ticket/reference number for tracking/auditing.  This is not used in the final rendered ACL."
    )
    name: str = Field(
        description="A reference name for the ACE, usually rendered as a ``remark``."
    )


class ACL(BaseModel):
    name: str = Field(description="The name of the ACL.")
    comment: str | None = Field(
        description="A comment explaining the purpose of the ACL, usually rendered as a ``remark``."
    )
    aces: list[ACE] = Field(description="A list of Access Control Entries.")
    targets: list[Target] = Field(
        description="A list of Capirca Targets for which to render the ACL."
    )


class Service(BaseModel):
    name: str = Field(
        description="The human-friendly, Capirca-referenced name of a service."
    )
    protocol: Protocol = Field(
        description="A list of IP protocols against which to filter."
    )
    port: int = Field(
        description="A valid layer 4 port number.  Must be between 1 and 65535."
    )

    @validator("port")
    def port_must_be_between_1_and_65535(cls, v: int) -> int:
        """Ensure the port is between 1 and 65535."""
        if v < 1 or v > 65535:
            raise ValueError(
                f"Port must be between 1 and 65535: {v} is outside of range"
            )
        return v


class Network(BaseModel):
    name: str = Field(
        description="The human-friendly, Capirca-referenced name of a CIDR."
    )
    address: IPv4Network | IPv6Network = Field(
        description="The IPv4 or IPv6 network.  Must be a valid IPv4 or IPv6 network in CIDR notation."
    )


class ServiceReferences(BaseModel):
    name: str = Field(
        description="The human-friendly, Capirca-referenced name of a list of services."
    )
    services: list[str] = Field(
        description="A list of service names which will be recursively resolved by Capirca."
    )


class NetworkReferences(BaseModel):
    name: str = Field(
        description="The human-friendly, Capirca-referenced name of a list of networks."
    )
    networks: list[str] = Field(
        description="A list of service names which will be recursively resolved by Capirca."
    )


class Definitions(BaseModel):
    services: list[Service] = Field(description="A list of Capirca Services.")
    networks: list[Network] = Field(description="A list of Capirca Networks.")
    service_references: list[ServiceReferences] = Field(
        description="A list of references to Services.  The referenced names must all exist."
    )
    network_references: list[NetworkReferences] = Field(
        description="A list of references to Networks.  The referenced names must all exist."
    )

    @validator("network_references", each_item=True)
    def network_must_exist(
        cls, v: NetworkReferences, values: dict[str, Any]
    ) -> NetworkReferences:
        """Check all defined Networks to ensure that referenced networks exist."""
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
        """Check all defined Services to ensure that referenced networks exist."""
        service_names = [s.name for s in values["services"]]
        service_name_references = [s for s in v.services]
        for service_name_reference in service_name_references:
            if service_name_reference not in service_names:
                raise ValueError(
                    f"Service Must Exist: {service_name_reference} definition not found"
                )
        return v


def load_yaml(fpath: pathlib.Path) -> dict[str, Any]:
    """Parse a YAML file into a Python dict."""
    yaml = YAML(typ="safe")
    return yaml.load(fpath)


def load_acl(fpath: pathlib.Path) -> ACL:
    """Create an ACL object from a YAML definition."""
    return ACL(**load_yaml(fpath))


def load_template(template_name: str) -> Template:
    """Retrieve a Jinja2 Tempalate."""
    env = Environment(
        loader=PackageLoader("capirca_xlate"), autoescape=select_autoescape()
    )
    return env.get_template(template_name)


def xlate_acl(acl: ACL) -> str:
    """Translate from a Python-native ACL object to a Capirca-native policy."""
    return load_template("acl.pol.j2").render(acl=acl)


def load_def(fpath: pathlib.Path) -> Definitions:
    """Create a Definitions object from a YAML definition."""
    return Definitions(**load_yaml(fpath))


def xlate_net(definitions: Definitions) -> str:
    """Translate from a Python-native Definitions object to a Capirca-native network definition."""
    return load_template("def.net.j2").render(
        networks=definitions.networks,
        network_references=definitions.network_references,
    )


def xlate_svc(definitions: Definitions) -> str:
    """Translate from a Python-native Definitions object to a Capirca-native service definition."""
    return load_template("def.svc.j2").render(
        services=definitions.services,
        service_references=definitions.service_references,
    )
