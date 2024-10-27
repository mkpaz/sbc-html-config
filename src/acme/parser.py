from enum import Enum
from traceback import print_exc
from typing import Any

__all__ = ["to_json"]

_TOP_LEVEL_CFG: set[str] = {
    "access-control",
    "account-config",
    "account-group",
    "allowed-elements-profile",
    "audit-logging",
    "auth-params",
    "authentication-profile",
    "authentication",
    "bfd-config",
    "bootparam",
    "capture-receiver",
    "cert-status-profile",
    "certificate-record",
    "class-policy",
    "class-profile",
    "codec-policy",
    "data-flow",
    "diameter-manipulation",
    "dns-alg-constraints",
    "dns-config",
    "dnsalg-constraints",
    "dpd-params",
    "dtls-srtp-profile",
    "enforcement-profile",
    "enum-config",
    "ext-policy-svr",
    "factory-accounts",
    "filter-config",
    "fraud-protection",
    "fxo-profile",
    "h323",
    "home-subscriber-server",
    "host-route",
    "http-alg",
    "http-client",
    "http-server",
    "ice-profile",
    "ike-access-control",
    "ike-certificate-profile",
    "ike-config",
    "ike-interface",
    "ike-sainfo",
    "ims-aka-profile",
    "ipsec",
    "ipt-config",
    "iwf-config",
    "ldap-cfg-attributes",
    "ldap-config",
    "ldap-transactions",
    "license",
    "local-accounts",
    "local-address-pool",
    "local-policy",
    "local-response-map",
    "local-routing-config",
    "media-manager-config",
    "media-manager",
    "media-policy",
    "media-profile",
    "media-sec-policy",
    "media-security",
    "msrp-config",
    "net-management-control",
    "network-alarm-threshold",
    "network-interface",
    "network-parameters",
    "npli-profile",
    "ntp-config",
    "ntp-sync",
    "password-policy",
    "phy-interface",
    "playback-config",
    "policy-group",
    "public-key",
    "q850-sip-map",
    "qos-constraints",
    "radius-servers",
    "realm-config",
    "realm-group",
    "redundancy-config",
    "response-map",
    "rph-policy",
    "rph-profile",
    "rtcp-policy",
    "S8HR-profile",
    "sdes-profile",
    "security-config",
    "service-health",
    "service",
    "session-agent-group",
    "session-agent-id-rule",
    "session-agent",
    "session-constraints",
    "session-group",
    "session-recording-group",
    "session-recording-server",
    "session-router-config",
    "session-timer-profile",
    "session-translation",
    "sip-advanced-logging",
    "sip-config",
    "sip-feature-caps",
    "sip-feature",
    "sip-interface",
    "sip-isup-profile",
    "sip-manipulation",
    "sip-monitoring",
    "sip-nat",
    "sip-profile",
    "sip-q850-map",
    "sip-recursion-policy",
    "sip-response-map",
    "sipura-profile",
    "snmp-address-entry",
    "snmp-community",
    "snmp-group-entry",
    "snmp-user-entry",
    "snmp-view-entry",
    "spl-config",
    "ssh-config",
    "static-flow",
    "static-vars",
    "steering-pool",
    "sti-config",
    "sti-server-group",
    "sti-server",
    "surrogate-agent",
    "survivability",
    "system-access-list",
    "system-config",
    "tcp-media-profile",
    "tdm-config",
    "tdm-profile",
    "test-policy",
    "test-sip-manipulation",
    "test-translation",
    "threshold-crossing-alert-group",
    "tls-global",
    "tls-profile",
    "translation-rules",
    "trap-receiver",
    "tscf-address-pool",
    "tscf-config",
    "tscf-data-flow",
    "tscf-interface",
    "tscf-protocol-policy",
    "tunnel-orig-params",
    "two-factor-authentication",
    "web-server-config",
}


class _CfgLine:
    def __init__(self, line: str):
        self.line: str = line.rstrip().replace("\t", " ")
        self.offset: int = -1
        self.left: str | None = None
        self.right: str | None = None

        if len(self.line) > 0:
            pair_line: str
            self.offset: int
            pair_line, self.offset = _get_line_offset(line)

            pair: list[str] = pair_line.split(" ", 1)
            self.left = pair[0].strip()
            if len(pair) == 2:
                self.right = pair[1].strip()

    def is_garbage(self) -> bool:
        return self.offset == -1 or (self.is_top() and self.left not in _TOP_LEVEL_CFG)

    def is_top(self) -> bool:
        return self.offset == 0

    def is_pair(self) -> bool:
        return self.left is not None and self.right is not None


class _LineType(Enum):
    UNKNOWN = -1
    BRANCH = 0
    KEY_VALUE = 1
    LIST_VALUE = 2


def _get_line_offset(line) -> tuple[str, int]:
    tidy_line: str = line.lstrip(" ")
    offset: int = len(line) - len(tidy_line)
    return tidy_line, offset


###############################################################################


def to_json(src: str) -> dict[str, Any]:
    tree: dict[str, Any] = {}
    path: list = [(tree, -1)]
    line: _CfgLine
    line_type: _LineType = _LineType.UNKNOWN
    prev_type: _LineType = _LineType.UNKNOWN
    next_offset: int = 0
    prev_offset: int = 0
    last_key = ""

    lines: list[str] = src.splitlines()

    for idx, raw_line in enumerate(lines):
        line = _CfgLine(raw_line)
        line_type = _LineType.UNKNOWN

        next_offset = 0
        if idx < len(lines) - 1:
            _, next_offset = _get_line_offset(lines[idx + 1])

        if line.is_garbage():
            print(f"ignore line {idx}: '{raw_line}'")
            continue

        try:
            if line.is_pair():
                line_type = _LineType.KEY_VALUE
            else:
                if next_offset <= line.offset:
                    line_type = _LineType.KEY_VALUE  # empty value

                    if (
                        line.offset > prev_offset and prev_type != _LineType.BRANCH
                    ) or (
                        line.offset == prev_offset and prev_type == _LineType.LIST_VALUE
                    ):
                        line_type = _LineType.LIST_VALUE
                else:
                    line_type = _LineType.BRANCH

            parent, _ = path[-1]

            match line_type:
                case _LineType.KEY_VALUE:
                    parent[line.left] = line.right
                case _LineType.BRANCH:
                    branch = {}
                    if line.left in parent:
                        existing_node = parent[line.left]
                        if isinstance(existing_node, list):
                            existing_node.append(branch)
                        else:
                            del parent[line.left]
                            parent[line.left] = [existing_node, branch]
                    else:
                        parent[line.left] = branch
                    path.append((branch, line.offset))
                case _LineType.LIST_VALUE:
                    list_value = line.left
                    existing_value = parent[last_key]
                    if isinstance(existing_value, list):
                        existing_value.append(list_value)
                    else:
                        del parent[last_key]
                        parent[last_key] = [existing_value, list_value]
                    pass
                case _:
                    print(f"unknown line type {idx}: '{raw_line}'")
                    pass

            if next_offset < line.offset:
                path = [item for item in path if item[1] < next_offset]
                pass

            prev_offset = line.offset
            prev_type = line_type
            if line.is_pair():
                last_key = line.left
        except Exception:
            print_exc()
            print(f"error at line {idx}: '{raw_line}'")

    return tree