FROM ubuntu:24.04

RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache \
    --mount=type=cache,sharing=locked,target=/var/lib/apt,id=apt-lib \
    apt-get update && apt-get install -y \
    haproxy python3-minimal python3-netifaces tini && \
    mkdir -p /etc/haproxy /var/lib/haproxy

COPY proxy.py /usr/local/bin/proxy
RUN chmod 755 /usr/local/bin/proxy && \
    chown -R haproxy:haproxy /etc/haproxy /var/lib/haproxy

USER haproxy:haproxy

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/bin/python3", "/usr/local/bin/proxy"]
