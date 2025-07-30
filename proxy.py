#!/usr/bin/env python3

import logging
import argparse
import socket
import subprocess
import time

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--proxy",
        type=str,
        action="append",
        help="Proxy configuration (format: local-port:remote-host:remote-port)",
    )
    args = parser.parse_args()

    if not args.proxy:
        logger.error("No proxy configuration provided")
        parser.print_help()
        return

    proxies = []

    for proxy in args.proxy:
        local_port, remote_host, remote_port = proxy.split(":")
        if not local_port.isdigit() or not remote_host or not remote_port.isdigit():
            logger.error(f"Invalid proxy configuration: {proxy}")
            parser.print_help()
            return

        local_port = int(local_port)
        remote_port = int(remote_port)
        logger.info(f"Proxy: {local_port} -> {remote_host}:{remote_port}")
        proxies.append((local_port, remote_host, remote_port))

    hostname = socket.gethostname()
    local_address = socket.gethostbyname(hostname)
    logger.info(f"Local address: {local_address}")

    last_resolved_ips = {}

    # main loop
    while True:
        for local_port, remote_host, remote_port in proxies:
            # resolve remote host
            try:
                remote_ip = socket.gethostbyname(remote_host)
            except socket.gaierror:
                logger.error(f"Failed to resolve remote host: {remote_host}")
                continue

            last_ip = last_resolved_ips.get((remote_host, remote_port), None)
            if last_ip == remote_ip:
                continue
            if last_ip is not None:
                subprocess.run(
                    [
                        "iptables",
                        "-t",
                        "nat",
                        "-D",
                        "PREROUTING",
                        "-p",
                        "tcp",
                        "--dport",
                        str(local_port),
                        "-j",
                        "DNAT",
                        "--to-destination",
                        f"{last_ip}:{remote_port}",
                    ],
                    check=True,
                )
                subprocess.run(
                    [
                        "iptables",
                        "-t",
                        "nat",
                        "-D",
                        "POSTROUTING",
                        "-p",
                        "tcp",
                        "-d",
                        last_ip,
                        "--dport",
                        str(remote_port),
                        "-j",
                        "SNAT",
                        "--to-source",
                        local_address,
                    ],
                    check=True,
                )
                logger.info(
                    f"Proxy: {local_port} -> {remote_host}({last_ip}):({remote_port}) removed"
                )

            last_resolved_ips[(remote_host, remote_port)] = remote_ip

            # Configure iptables
            subprocess.run(
                [
                    "iptables",
                    "-t",
                    "nat",
                    "-A",
                    "PREROUTING",
                    "-p",
                    "tcp",
                    "--dport",
                    str(local_port),
                    "-j",
                    "DNAT",
                    "--to-destination",
                    f"{remote_ip}:{remote_port}",
                ],
                check=True,
            )
            subprocess.run(
                [
                    "iptables",
                    "-t",
                    "nat",
                    "-A",
                    "POSTROUTING",
                    "-p",
                    "tcp",
                    "-d",
                    remote_ip,
                    "--dport",
                    str(remote_port),
                    "-j",
                    "SNAT",
                    "--to-source",
                    local_address,
                ],
                check=True,
            )
            logger.info(
                f"Proxy: {local_port} -> {remote_host}({remote_ip}):({remote_port}) configured"
            )
        time.sleep(1)


if __name__ == "__main__":
    main()
