# © 2020-2026 Danial Behzadi <dani.behzi@ubuntu.com>
# © 2026 KDE Farsi Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
this module creates tractorrc file
"""

import os
import shutil
import tempfile

from . import config, db, proxy, transport


def _get_upstream_line() -> str:
    """
    set upstream proxy if available
    """
    mode, host, port = proxy.get_proxy()
    match mode:
        case "socks":
            return f"Socks5Proxy {host}:{port}\n"
        case "https" | "http":
            return f"HTTPSProxy {host}:{port}\n"
    return ""


def _get_port_lines() -> str:
    """
    Get torrc lines for different ports
    """
    if db.get_val("accept-connection"):
        my_ip = "0.0.0.0"
        socks_line = f"SocksPort {my_ip}:{str(db.get_val('socks-port'))}\n"
        socks_line += "SocksPolicy accept *\n"
    else:
        my_ip = "127.0.0.1"
        socks_line = f"SocksPort {my_ip}:{str(db.get_val('socks-port'))}\n"
    http_line = f"HTTPTunnelPort {my_ip}:{str(db.get_val('http-port'))}\n"
    dns_line = f"DNSPort {my_ip}:{str(db.get_val('dns-port'))}\n"
    dns_line += "AutomapHostsOnResolve 1\n"
    dns_line += "AutomapHostsSuffixes .exit,.onion\n"
    return f"{socks_line}{http_line}{dns_line}"


def _get_path_lines() -> str:
    """
    Get torrc lines for different pathes
    """
    data_dir = db.get_data_directory()
    path_line = f"DataDirectory {data_dir}\n"
    path_line += f"ControlSocket {data_dir}/control.sock\n"
    return path_line


def _get_exit_lines() -> str:
    """
    Get torrc lines for exit nodes
    """
    exit_node = db.get_val("exit-node")
    if exit_node != "ww":
        return f"ExitNodes {'{'}{exit_node}{'}'}\nStrictNodes 1\n"
    return ""


def _fill_bridge_lines(transport_name: str, my_bridges: list[str]) -> str:
    """
    Build the bridge section for the generated torrc
    """
    my_transport = transport.registry.get_transport(transport_name)
    bridge_lines = "".join(f"Bridge {line}\n" for line in my_bridges)
    return f"{my_transport.render_bridge_prelude()}{bridge_lines}"


def _get_bridge_lines() -> str:
    """
    Resolve and render the bridge configuration block
    """
    transport_name = db.get_val("bridge-type")
    if transport_name != "none":
        my_bridges = config.get_bridges(transport_name)
        if not my_bridges:
            raise OSError("No relevant bridges given")
        bridge_lines = _fill_bridge_lines(transport_name, my_bridges)
        return bridge_lines
    return ""


def _get_hidden_service_lines() -> str:
    """
    Build torrc hidden-service directives from keyfile configuration.

    Hidden services are enabled only when the `hidden-services` setting is true
    Port mappings are read from `config.get_hidden_ports()`, which is expected
    to return a dict of `{name: "PORT HOST:TARGET_PORT"}` from the keyfile.

    Returns:
        A torrc snippet containing:
        - `HiddenServiceDir <data_dir>/hidden_service`
        - one `HiddenServicePort <mapping>` line per configured mapping

        Returns an empty string if hidden services are disabled or no mappings
        are configured.
    """
    if not db.get_val("hidden-services"):
        return ""
    hidden_services = config.get_hidden_ports()
    if not hidden_services:
        return ""
    data_dir = db.get_data_directory()
    service_dir = os.path.join(data_dir, "hidden_service")
    os.makedirs(service_dir, exist_ok=True)
    os.chmod(service_dir, 0o700)
    port_lines = "".join(
        f"HiddenServicePort {line}\n" for line in hidden_services.values()
    )
    return f"HiddenServiceDir {service_dir}\n{port_lines}"


def build() -> str:
    """Build the complete torrc content without creating a temporary file."""
    sections = [
        _get_upstream_line(),
        _get_port_lines(),
        _get_path_lines(),
        _get_exit_lines(),
        _get_bridge_lines(),
    ]
    if db.get_val("fascist-firewall"):
        sections.append("FascistFirewall 1\n")
    sections.append(_get_hidden_service_lines())
    return "".join(sections)


def create() -> tuple[str, str]:
    """
    main function of the module
    """
    content = build()
    tmpdir = tempfile.mkdtemp(prefix="tractor-")
    path = os.path.join(tmpdir, "tractorrc")
    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)
        os.chmod(path=path, mode=0o600)
    except OSError:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise
    return tmpdir, path
