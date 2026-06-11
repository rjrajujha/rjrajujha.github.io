---
title: Custom DNS Security Deployment
slug: custom-dns-security-deployment
category: work
order: 5
stack:
  - BIND9
  - Pi-hole
  - Ubuntu
  - DoH
  - DoT
description: DoH/DoT-ready DNS deployment with observability and secure zone management.
---

## Problem

A home lab and small-office network needed encrypted DNS resolution, ad/malware blocking, and query visibility — without sending all traffic to a third-party resolver.

## Solution

BIND9 for local authoritative zones. Pi-hole as recursive resolver with blocklists. DoH and DoT termination on Ubuntu with internal CA certificates. Split-horizon rules keep local names resolvable while upstream queries use encrypted transport.

## Tech stack

BIND9 · Pi-hole · Ubuntu Server · DoH · DoT · systemd

## Outcome

Encrypted, filterable DNS for the network with query logging for troubleshooting and a fast override path for blocklist false positives during development.

Infrastructure configuration — not published as a standalone repository.
