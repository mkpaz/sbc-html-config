from base64 import b64encode
from pathlib import Path
from typing import Any

import util as u
from acme.context import ConfigElement, Context
from env import ROOT_DIR
from jinja2 import Environment, FileSystemLoader, Template

__all__ = ["render"]

ASSETS_DIR: Path = ROOT_DIR / "acme/assets"
ENV: Environment = Environment(loader=FileSystemLoader(ASSETS_DIR))
TAB_SIZE: int = 8
KEY_PAD_SIZE = 48


def render(json_cfg: dict[str, Any], file_name: str = "sbc-html-config") -> str:
    ENV.filters.update(
        {
            "is_dict": u.is_dict,
            "is_list": u.is_list,
            "tree_item_name": _get_tree_item_name,
            "realm_ids": _get_realm_ids_or_empty,
        }
    )

    ctx: Context = Context(json_cfg)

    template: Template = ENV.get_template("index.html")
    output: str = template.render(
        file_name=file_name,
        cfg=json_cfg,
        cfg_text=_to_text_config(json_cfg, ctx),
        ctx=ctx,
        css_content=_load_css(),
        js_content=_load_js(),
        font=_load_font(),
    )

    return output


def _to_text_config(json_cfg: dict[str, Any], ctx: Context) -> str:
    buffer: list[str] = []

    for name, value in json_cfg.items():
        buffer.append(_to_text_node(name, value, 0, True, ctx))

    return _join_code_tags(buffer)


def _load_css() -> str:
    with open(ASSETS_DIR / "static/main.css", "r") as f:
        return f.read()


def _load_js() -> str:
    with open(ASSETS_DIR / "static/main.js", "r") as f:
        return f.read()


def _load_font() -> str:
    with open(ASSETS_DIR / "static/FiraMono.ttf", "rb") as f:
        return b64encode(f.read()).decode("ascii")


###############################################################################


def _to_text_node(
    node_name: str, node_value: Any, depth: int, is_print_name: bool, ctx: Context
) -> str:
    buffer: list[str] = []
    indent: int = depth * TAB_SIZE

    # list of any level or leaf value (string list)
    if u.is_list(node_value):
        if not u.is_string_list(node_value):
            for idx, item in enumerate(node_value):
                name = node_name
                if depth == 0:
                    buffer.append(
                        f'<code data-realms="{_get_realm_ids_or_empty(item, node_name, ctx)}">'
                    )
                    name = f'<div id="{name}_{idx}" class="scroll-marker"></div><b>{name}</b>'

                buffer.append(u.rpad(name, indent))
                buffer.append(_to_text_node(node_name, item, depth, False, ctx))

                if depth == 0:
                    buffer.append("</code>")
        else:
            for idx, s in enumerate(node_value):
                if idx == 0:
                    buffer.append(
                        u.rpad(
                            node_name.ljust(KEY_PAD_SIZE)
                            + _wrap_to_link_if_needed(node_name, s, ctx),
                            indent,
                        )
                    )
                else:
                    buffer.append(
                        u.rpad(
                            _wrap_to_link_if_needed(node_name, s, ctx),
                            KEY_PAD_SIZE + indent,
                        )
                    )
    # dict of any level
    elif u.is_dict(node_value):
        name = node_name
        if is_print_name:
            if depth == 0:
                buffer.append(
                    f'<code data-realms="{_get_realm_ids_or_empty(node_value, node_name, ctx)}">'
                )
                name = f'<div id="{name}" class="scroll-marker"></div><b>{name}</b>'
            buffer.append(u.rpad(name, indent))

        for item in node_value.items():
            buffer.append(_to_text_node(node_name, item, depth + 1, True, ctx))

        if is_print_name and depth == 0:
            buffer.append("</code>")
    # dict value
    elif u.is_tuple(node_value):
        key, val = node_value
        if val is None:
            buffer.append(u.rpad(key.ljust(KEY_PAD_SIZE), indent))
        elif u.is_string(val):
            buffer.append(
                u.rpad(
                    key.ljust(KEY_PAD_SIZE) + _wrap_to_link_if_needed(key, val, ctx),
                    indent,
                )
            )
        else:
            buffer.append(_to_text_node(key, val, depth, True, ctx))

    return _join_code_tags(buffer)


def _get_tree_item_name(value: dict[str, Any], param_name: str, idx: int) -> str:
    result: str | None = None

    match param_name:
        case "access-control":
            result = f'from {value.get("source-address")}'
        case "codec-policy":
            result = value.get("name")
        case "host-route":
            result = f'to {value.get("dest-network")}'
        case "local-policy":
            source_realm_raw: str | list[str] = value.get("source-realm", "*")
            source_realm: str = (
                f'({", ".join(source_realm_raw)})'
                if u.is_list(source_realm_raw)
                else str(source_realm_raw)
            )
            next_hop: str = ";".join(Context.get_local_policy_next_hop(value))
            result = f"from {source_realm} to {next_hop or '?'}"
        case "network-interface":
            result = (
                f'{Context.get_network_interface_id(value)} {value.get("ip-address")}'
            )
        case "phy-interface":
            result = value.get("name")
        case "realm-config":
            result = value.get("identifier")
        case "response-map":
            result = value.get("name")
        case "session-agent":
            result = value.get("hostname")
        case "session-constraints":
            result = value.get("name")
        case "session-translation":
            result = value.get("id")
        case "sip-advanced-logging":
            result = value.get("name")
        case "sip-feature":
            result = value.get("name")
        case "session-group":
            result = value.get("group-name")
        case "sip-interface":
            result = value.get("realm-id", "")
            sip_port: str | None = Context.get_first_sip_port(value)
            if sip_port:
                result = f"{result} [{sip_port}]"
        case "sip-manipulation":
            result = value.get("name")
        case "snmp-community":
            result = value.get("community-name")
        case "steering-pool":
            result = value.get("realm-id")
        case "translation-rules":
            result = value.get("id")
        case "trap-receiver":
            result = value.get("ip-address")

    if not result and "id" in value:
        result = value.get("id")

    if not result and "name" in value:
        result = value.get("name")

    return f"{str(idx)}: {result}" if result else str(idx)


def _get_realm_ids_or_empty(
    value: dict[str, Any], param_name: str, ctx: Context
) -> str:

    match param_name:
        case "access-control":
            return value.get("realm-id", "")
        case "local-policy":
            return " ".join(Context.get_local_policy_realms(value))
        case "realm-config":
            return value.get("identifier", "")
        case "session-agent":
            return value.get("realm-id", "")
        case "sip-interface":
            return value.get("realm-id", "")
        case "steering-pool":
            return value.get("realm-id", "")
        case "network-interface":
            net_id: str = Context.get_network_interface_id(value)
            return " ".join(ctx.get_realms(ConfigElement.NETWORK_INTERFACE, net_id))
        case "sip-manipulation":
            name: str = value.get("name", "")
            return " ".join(ctx.get_realms(ConfigElement.SIP_MANIPULATION, name))
        case "codec-policy":
            name: str = value.get("name", "")
            return " ".join(ctx.get_realms(ConfigElement.CODEC_POLICY, name))
        case "response-map":
            name: str = value.get("name", "")
            return " ".join(ctx.get_realms(ConfigElement.RESPONSE_MAP, name))
        case "session-constraints":
            name: str = value.get("name", "")
            return " ".join(ctx.get_realms(ConfigElement.SESSION_CONSTRAINTS, name))

    return ""


def _wrap_to_link_if_needed(param_name: str, value: str, ctx: Context) -> str:
    element_name: str = ""
    pos: tuple[int, int] = (-1, -1)

    match param_name:
        case "codec-policy":
            element_name = "codec-policy"
            pos = ctx.get_element_pos(ConfigElement.CODEC_POLICY, value)
        case "network-interfaces" | "network-interfaces":
            element_name = "network-interface"
            pos = ctx.get_element_pos(ConfigElement.NETWORK_INTERFACE, value)
        case "realm" | "realm-id" | "egress-realm-id" | "source-realm":
            element_name = "realm-config"
            pos = ctx.get_element_pos(ConfigElement.REALM, value)
        case "response-map":
            element_name = "response-map"
            pos = ctx.get_element_pos(ConfigElement.RESPONSE_MAP, value)
        case "constraint-name":
            element_name = "session-constraints"
            pos = ctx.get_element_pos(ConfigElement.SESSION_CONSTRAINTS, value)
        case "in-manipulationid" | "out-manipulationid":
            element_name = "sip-manipulation"
            pos = ctx.get_element_pos(ConfigElement.SIP_MANIPULATION, value)

    if pos[0] < 0:
        return value

    # see .scroll-marker#id (len == 1 -> dict, otherwise list)
    href: str = element_name if pos[1] <= 1 else f"{element_name}_{str(pos[0])}"

    return f'<a href="#{href}">{value}</a>'


# Since we are using <pre>, the <code> tag isn't rendered and leaves
# blank lines. This method inserts a newline character after any string
# that isn't an opening or closing <code> tag.
def _join_code_tags(list: list[str]) -> str:
    result = []
    for item in list:
        if item.startswith("<code") or item.startswith("</code"):
            result.append(item)
        else:
            result.append(item.rstrip() + "\n")

    return "".join(result)
