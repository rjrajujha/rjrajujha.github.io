---
title: Secure DNS Infrastructure
slug: secure-dns-infrastructure
category: infrastructure
infra_group: public
order: 1
stack:
  - GCP
  - NGINX
  - AdGuard Home
  - DNS-over-HTTPS
  - DNS-over-TLS
  - DNS-over-QUIC
description: Self-hosted encrypted DNS using NGINX and AdGuard Home.
endpoints:
  - label: DNS-over-HTTPS
    value: https://dns.rajujha.dev/dns-query
  - label: DNS-over-TLS
    value: tls://dns.rajujha.dev
  - label: DNS-over-QUIC
    value: quic://dns.rajujha.dev
---

## Problem

Public DNS resolvers expose query metadata and offer limited control over filtering. A production-grade resolver was needed with encrypted transport, ad/malware blocking, and full query visibility.

## Solution

AdGuard Home runs as the filtering resolver behind NGINX for TLS termination and reverse proxy. DoH, DoT, and DoQ endpoints serve encrypted DNS on GCP with certificate-managed TLS and upstream forwarding.

## Key Features

- Encrypted DNS over HTTPS, TLS, and QUIC
- Ad and malware filtering with custom blocklists
- Privacy-first — no third-party resolver dependency
- Production deployment with TLS termination and reverse proxy
- Query logging for troubleshooting and audit

## Links

- DoH: `https://dns.rajujha.dev/dns-query`
- DoT: `tls://dns.rajujha.dev`
- DoQ: `quic://dns.rajujha.dev`
