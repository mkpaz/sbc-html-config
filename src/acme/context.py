from enum import Enum
from typing import Any

import util as u


class ConfigElement(Enum):
    CODEC_POLICY = 0
    NETWORK_INTERFACE = 1
    REALM = 2
    RESPONSE_MAP = 3
    SESSION_CONSTRAINTS = 4
    SIP_MANIPULATION = 5


class Mapping:
    def __init__(self) -> None:
        self._map: dict[str, set[str]] = {}

    def get(self, key: str) -> set[str]:
        return self._map.get(key, set())

    def add(self, key: str, value: str, is_create_key: bool = True) -> None:
        if not key or not value:
            return

        values = self._map.get(key)
        if values:
            values.add(value)
        elif is_create_key:
            self._map[key] = set([value])


class Context:
    def __init__(self, json_cfg: dict[str, Any]) -> None:
        maps: dict[ConfigElement, Mapping] = {
            ConfigElement.CODEC_POLICY: Mapping(),  # realm
            ConfigElement.NETWORK_INTERFACE: Mapping(),  # realm
            ConfigElement.REALM: Mapping(),  # not used
            ConfigElement.RESPONSE_MAP: Mapping(),  # sip-interface, session-agent
            ConfigElement.SESSION_CONSTRAINTS: Mapping(),  # realm, sip-interface
            ConfigElement.SIP_MANIPULATION: Mapping(),  # realm, sip-interface, session-agent
        }
        self.realm_mappings = maps

        registry: dict[ConfigElement, dict[str, int]] = {
            ConfigElement.CODEC_POLICY: {},
            ConfigElement.NETWORK_INTERFACE: {},
            ConfigElement.REALM: {},
            ConfigElement.RESPONSE_MAP: {},
            ConfigElement.SESSION_CONSTRAINTS: {},
            ConfigElement.SIP_MANIPULATION: {},
        }
        self.index_registry = registry

        for idx, realm in enumerate(u.ensure_list(json_cfg.get("realm-config"))):
            realm_id: str = realm.get("identifier")
            registry.get(ConfigElement.REALM, {})[realm_id] = idx

            for net in u.ensure_list(realm.get("network-interfaces")):
                self._enum_map(maps, ConfigElement.NETWORK_INTERFACE).add(net, realm_id)

            if u.contains_not_empty(realm, "in-manipulationid"):
                self._enum_map(maps, ConfigElement.SIP_MANIPULATION).add(
                    realm.get("in-manipulationid"), realm_id
                )

            if u.contains_not_empty(realm, "out-manipulationid"):
                self._enum_map(maps, ConfigElement.SIP_MANIPULATION).add(
                    realm.get("out-manipulationid"), realm_id
                )

            if u.contains_not_empty(realm, "codec-policy"):
                self._enum_map(maps, ConfigElement.CODEC_POLICY).add(
                    realm.get("codec-policy"), realm_id
                )

            if u.contains_not_empty(realm, "constraint-name"):
                self._enum_map(maps, ConfigElement.SESSION_CONSTRAINTS).add(
                    realm.get("constraint-name"), realm_id
                )

        for sip_interface in u.ensure_list(json_cfg.get("sip-interface")):
            realm_id: str = sip_interface.get("realm-id")

            if u.contains_not_empty(sip_interface, "in-manipulationid"):
                self._enum_map(maps, ConfigElement.SIP_MANIPULATION).add(
                    sip_interface.get("in-manipulationid"), realm_id
                )

            if u.contains_not_empty(sip_interface, "out-manipulationid"):
                self._enum_map(maps, ConfigElement.SIP_MANIPULATION).add(
                    sip_interface.get("out-manipulationid"), realm_id
                )

            if u.contains_not_empty(sip_interface, "response-map"):
                self._enum_map(maps, ConfigElement.SESSION_CONSTRAINTS).add(
                    sip_interface.get("response-map"), realm_id
                )

            if u.contains_not_empty(sip_interface, "constraint-name"):
                self._enum_map(maps, ConfigElement.SESSION_CONSTRAINTS).add(
                    sip_interface.get("constraint-name"), realm_id
                )

        for agent in u.ensure_list(json_cfg.get("session-agent")):
            realm_id: str = agent.get("realm-id") or agent.get("egress-realm-id")

            if u.contains_not_empty(agent, "in-manipulationid"):
                self._enum_map(maps, ConfigElement.SIP_MANIPULATION).add(
                    agent.get("in-manipulationid"), realm_id
                )

            if u.contains_not_empty(agent, "out-manipulationid"):
                self._enum_map(maps, ConfigElement.SIP_MANIPULATION).add(
                    agent.get("out-manipulationid"), realm_id
                )

            if u.contains_not_empty(agent, "response-map"):
                self._enum_map(maps, ConfigElement.SESSION_CONSTRAINTS).add(
                    agent.get("response-map"), realm_id
                )

        for idx, policy in enumerate(u.ensure_list(json_cfg.get("codec-policy"))):
            name: str = policy.get("name", "")
            if name:
                registry.get(ConfigElement.CODEC_POLICY, {})[name] = idx

        for idx, net in enumerate(u.ensure_list(json_cfg.get("network-interface"))):
            net_id: str = Context.get_network_interface_id(net)
            if net_id:
                registry.get(ConfigElement.NETWORK_INTERFACE, {})[net_id] = idx

        for idx, resp_map in enumerate(u.ensure_list(json_cfg.get("response-map"))):
            name: str = resp_map.get("name", "")
            if name:
                registry.get(ConfigElement.RESPONSE_MAP, {})[name] = idx

        for idx, constr in enumerate(
            u.ensure_list(json_cfg.get("session-constraints"))
        ):
            name: str = constr.get("name", "")
            if name:
                registry.get(ConfigElement.SESSION_CONSTRAINTS, {})[name] = idx

        for idx, manip in enumerate(u.ensure_list(json_cfg.get("sip-manipulation"))):
            name: str = manip.get("name", "")
            if name:
                registry.get(ConfigElement.SIP_MANIPULATION, {})[name] = idx

    # returns the list of realms associated with the configuration element
    def get_realms(self, type: ConfigElement, key: str) -> set[str]:
        return self._enum_map(self.realm_mappings, type).get(key)

    # returns the configuration element index in list and the list length
    def get_element_pos(self, type: ConfigElement, key: str) -> tuple[int, int]:
        registry: dict[str, int] | None = self.index_registry.get(type)
        if not registry:
            return (-1, -1)

        return (registry.get(key, -1), len(registry))

    def _enum_map(self, map: dict[ConfigElement, Mapping], elem: Enum) -> Mapping:
        return map.get(elem)  # type: ignore

    ###########################################################################

    @staticmethod
    def get_network_interface_id(net: dict[str, Any]) -> str:
        return f'{net.get("name")}:{net.get("sub-port-id")}'

    @staticmethod
    def get_first_sip_port(sip_interface: dict[str, Any]) -> str | None:
        if "sip-port" in sip_interface:
            sip_port: dict[str, Any] | None = None
            if u.is_list(sip_interface.get("sip-port")):
                sip_port = sip_interface.get("sip-port", [])[0]
            if u.is_dict(sip_interface.get("sip-port")):
                sip_port = sip_interface.get("sip-port", {})

            if sip_port:
                return f'{sip_port.get("address")}:{sip_port.get("port", "5060")}'

        return None

    @staticmethod
    def get_local_policy_realms(local_policy: dict[str, Any]) -> list[str]:
        realms: list[str] = []

        source_realm: str | list[str] | None = local_policy.get("source-realm")
        if isinstance(source_realm, str):
            realms.append(source_realm)
        elif isinstance(source_realm, list):
            realms.extend(source_realm)

        target_realm: str | None = local_policy.get("realm")
        if target_realm:
            realms.append(target_realm)

        attributes: Any = local_policy.get("policy-attribute")
        if attributes:
            for attr in u.ensure_list(attributes):
                attr_realm: str | None = attr.get("realm")
                if attr_realm:
                    realms.append(attr_realm)

        return realms

    @staticmethod
    def get_local_policy_next_hop(local_policy: dict[str, Any]) -> list[str]:
        hops: list[str] = []

        next_hop: str | None = local_policy.get("next-hop")
        if next_hop:
            hops.append(next_hop)

        attributes: Any = local_policy.get("policy-attribute")
        if attributes:
            for attr in u.ensure_list(attributes):
                attr_hop: str | None = attr.get("next-hop")
                if attr_hop:
                    hops.append(attr_hop)

        return hops
