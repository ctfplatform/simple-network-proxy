# Simple Network Proxy

An HAProxy-based TCP application proxy designed for Docker Compose environments to expose internal network services to external networks.

## Purpose

This proxy solves the problem of exposing services running in Docker Compose internal networks where port forwarding is not available. This proxy relies on HAProxy to forward TCP connections between the networks.

## Features

- HAProxy-powered TCP forwarding
- Multiple proxy configurations supported
- Optimized for Docker Compose environments
- Exposes internal network services externally

## Usage

### Docker Compose

```bash
docker-compose up --build
```

Default configuration exposes:

- Port 1080 → nginx:80 (internal nginx service)
- Port 13117 → nc:8080 (internal netcat service)

### Custom Configuration

Edit the `command` section in `docker-compose.yml` for the `proxy` service:

```yaml
proxy:
  command:
    - -p
    - 8080:web-service:80
    - -p
    - 3306:database:3306
```

## Network Architecture

```
External Network (eth-public) ← → Proxy ← → Internal Network (eth-internal)
                             Port 1080         nginx:80
                             Port 13117        nc:8080
```

## Requirements

- Two network interfaces:
  - `eth-public`: Connected to external network
  - `eth-internal`: Connected to internal services network

## How it Works

1. Parses proxy configurations from command line arguments
2. Generates an HAProxy configuration with matching frontends/backends
3. Runs HAProxy in the foreground to proxy traffic at the application layer
