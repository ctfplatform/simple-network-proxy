#!/usr/bin/env python3

import argparse
import logging
import os
from pathlib import Path
import re
import subprocess
from textwrap import dedent


logging.basicConfig(level=logging.INFO)

LOGGER = logging.getLogger(__name__)

CONFIG_PATH = Path("/etc/haproxy/haproxy.cfg")


def parse_args() -> list[tuple[int, str, int]]:
    parser = argparse.ArgumentParser(
        description="Generate an HAProxy configuration for simple TCP proxying.",
    )
    parser.add_argument(
        "-p",
        "--proxy",
        dest="proxies",
        action="append",
        help="Proxy mapping in the form local-port:remote-host:remote-port",
    )
    parsed = parser.parse_args()

    if not parsed.proxies:
        parser.error("At least one --proxy mapping is required")

    proxies: list[tuple[int, str, int]] = []
    for raw in parsed.proxies:
        parts = raw.split(":", maxsplit=2)
        if len(parts) != 3:
            parser.error(f"Invalid proxy definition '{raw}'")
        local_port, remote_host, remote_port = parts
        if not local_port.isdigit() or not remote_port.isdigit():
            parser.error(f"Ports must be numeric in definition '{raw}'")
        local = int(local_port)
        remote = int(remote_port)
        if local <= 0 or local > 65535 or remote <= 0 or remote > 65535:
            parser.error(f"Ports must be within 1-65535 in definition '{raw}'")
        if not remote_host:
            parser.error(f"Remote host is missing in definition '{raw}'")
        proxies.append((local, remote_host, remote))

    return proxies


def sanitize_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", name)
    return cleaned.strip("_") or "target"


def render_config(proxies: list[tuple[int, str, int]]) -> str:
    sections = [
        dedent(
            """
            global
                log stdout format raw local0
                maxconn 4096

            defaults
                log global
                mode tcp
                option tcplog
                timeout connect 10s
                timeout client 10m
                timeout server 10m

            resolvers system
                parse-resolv-conf
                resolve_retries 3
                timeout retry 1s
                hold valid 10s
            """
        ).strip()
    ]

    for index, (local_port, remote_host, remote_port) in enumerate(proxies, start=1):
        backend_name = f"be_{index}_{sanitize_name(remote_host) or index}"
        frontend_name = f"fe_{index}_{local_port}"
        sections.append(
            dedent(
                f"""
                frontend {frontend_name}
                    bind :{local_port}
                    mode tcp
                    default_backend {backend_name}

                backend {backend_name}
                    mode tcp
                    balance roundrobin
                    default-server check resolvers system init-addr libc,none
                    server target {remote_host}:{remote_port}
                """
            ).strip()
        )

    return "\n\n".join(sections) + "\n"


def write_config(content: str) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(content, encoding="utf-8")


def run_haproxy(config_path: Path) -> None:
    subprocess.run(["haproxy", "-c", "-f", str(config_path)], check=True)
    os.execvp("haproxy", ["haproxy", "-f", str(config_path), "-db"])


def main() -> None:
    proxies = parse_args()
    for local, host, remote in proxies:
        LOGGER.info("Proxy %s -> %s:%s", local, host, remote)

    config = render_config(proxies)
    write_config(config)
    LOGGER.info("Wrote HAProxy configuration to %s", CONFIG_PATH)
    run_haproxy(CONFIG_PATH)


if __name__ == "__main__":
    main()
