# capirca-xlate

`capirca-xlate` is a library for writing network ACL policies in YAML
format and converting them to the [`capirca`][capirca] format for
platform-specific ACL generation.  It will take an ACL policy like this:

```yaml
---

name: "allowtointernet"
comment: |
  Denies all traffic to internal IPs except established tcp replies.
  Also denies access to certain public allocations.

  Ideal for some internal lab/testing types of subnets that are
  not well trusted, but allowing internal users to access.

  Apply to ingress interface (to filter traffic coming from lab)
targets:
  - platform: cisconx
    options:
      - extended
aces:
  - name: accept-dhcp comment: Optional - allow forwarding of DHCP requests.
    destination_ports:
      - DHCP
    protocols:
      - udp
    action: accept
  - name: accept-to-honestdns {
    comment: Allow name resolution using honestdns.
    destination_addresses:
      - GOOGLE_DNS
    destination_ports:
      - DNS
    protocols:
      - udp
    action: accept
  - name: accept-tcp-replies
    comment: Allow tcp replies to internal hosts.
    destination_addresses:
      - INTERNAL
    protocols:
      - tcp
    options:
      - tcp-established
    action: accept
  - name: deny-to-internal
    comment: Deny access to rfc1918/internal.
    destination_addresses:
      - INTERNAL
    action: deny
  - name: deny-to-specific_hosts
    comment: Deny access to specified public.
    destination_addresses:
      - WEB_SERVERS
      - MAIL_SERVERS
    action: deny
  - name: default-permit
    comment: Allow what's left.
    action: accept
```

And transform it into the `capirca` `ply` format below:

```
header {
  comment:: "Denies all traffic to internal IPs except established tcp replies."
  comment:: "Also denies access to certain public allocations."
  
  comment:: "Ideal for some internal lab/testing types of subnets that are"
  comment:: "not well trusted, but allowing internal users to access."
  
  comment:: "Apply to ingress interface (to filter traffic coming from lab)"
  
  target:: cisconx allowtointernet extended
}

term accept-dhcp {
  comment:: "Optional - allow forwarding of DHCP requests."
  destination-port:: DHCP
  protocol:: udp
  action:: accept
}
term accept-to-honestdns { {
  comment:: "Allow name resolution using honestdns."
  destination-address:: GOOGLE_DNS
  destination-port:: DNS
  protocol:: udp
  action:: accept
}
term accept-tcp-replies {
  comment:: "Allow tcp replies to internal hosts."
  destination-address:: INTERNAL
  protocol:: tcp
  option:: tcp-established
  action:: accept
}
term deny-to-internal {
  comment:: "Deny access to rfc1918/internal."
  destination-address:: INTERNAL
  action:: deny
}
term deny-to-specific_hosts {
  comment:: "Deny access to specified public."
  destination-address:: WEB_SERVERS MAIL_SERVERS
  action:: deny
}
term default-permit {
  comment:: "Allow what's left."
  action:: accept
}
```

## Usage

Using `capirca_xlate` is straightforward.  There are two functions
for loading data and three functions for generating `ply`-formatted
policies/definitions.  The below is a complete example.

```python
from pathlib import Path

import capirca_xlate.xlate

acl = capirca_xlate.xlate.load_acl(Path('example_acl.yml'))
definitions = capirca_xlate.xlate.load_def(Path('example_def.yml'))

print(capirca_xlate.xlate.xlate_net(definitions))
print(capirca_xlate.xlate.xlate_svc(definitions))
print(capirca_xlate.xlate.xlate_acl(acl))
```

You can look at the `acl_schema.yaml` and `definitions_schema.yaml`
files in this repo to get a better sense of how to structure your data.
These schemas are updated when the code is updated.

## Project State and Reasoning

At this time, all functionality should be considered **alpha**.  This
is currently a library, not an end-user CLI tool.  It can be used to
create an end-user CLI tool, but because policies can be arranged and
described in a wide variety of ways, the focus for now is on providing
the library to manage your own policies the way you want/need.

This library very heavily leverages types.  It does this to ensure
definitions and policies will be rendered to something valid.  For
example, it will prevent you from generating the following:

```
DNS = 53/udp
HTTP = 80/tcp
ALL = DNS
      HTTP
      SSH
```

This is _technically_ valid syntax, but because there is no definition
of `SSH`, `capirca` will ultimately fail to generate the ACL.
Additionally, IPv4 and IPv6 addresses must be valid network addresses in
CIDR notation, because this is what `capirca` expects.  Other
validations exist, too, such as ensuring you don't typo
`tcp-established` as an `options`.  Finally, it is opinionated in the
its data is structured.  The structure of the data is not a 1:1 mapping
of `capirca`.  For example, in the `capirca` `ply` format, multiple
references to addresses are simply separated by a blank space (` `).
However, this library expects multiple addresses to be unique items in a
list.

Everything in this library is exposed for the developer.  Althougth the
primary intent is to allow for translating between a YAML-based spec and
the official `ply` spec, the data is modeled with classes exposed in
such a way that the original source of the data is largely irrelevant.
For example, you could write code that fetched the source data from a
SQL data base, then created the necessary objects (`ACL` and
`Definitions`) with the appropriate fields, then pass those objects to
the template rendering functions (`capirca_xlate.xlate.xlate_acl()`, 
`capirca_xlate.xlate.xlate_net()`, and
`capirca_xlate.xlate.xlate_svc()`) and get the `ply`-formatted string
back.

The `xlate_*` functions return the `capirca` `ply` format back as a
string.  They do not write to disk.  This is to enable flexibility for
developers to programmatically leverage tools such as `capirca_xlate`,
`capirca`, and `nornir` or `netmiko` for full end-to-end ACL automation
without needing to repeatedly read from and write to disk.

## Feature Support

`capirca` has a wide variety of options and features, some of which are
platform-specific.  `capirca_xlate` does not support all of these.  It
currently supports common features and options, but not vendor- or
platform-specific features, such as `from-zone` and `to-zone`.

## TODO

* Add a license
* Add tests
* Add more examples
* Show examples of non-YAML source data
* Show examples of integrating with [`nornir`][nornir]

[capirca]: https://github.com/google/capirca
[nornir]: https://github.com/nornir-automation/nornir