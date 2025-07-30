FROM ubuntu:24.04

RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache \
    --mount=type=cache,sharing=locked,target=/var/lib/apt,id=apt-lib \
    apt-get update && apt-get install -y \
    iptables python3-minimal python3-netifaces tini

COPY proxy.py /proxy.py
COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]

