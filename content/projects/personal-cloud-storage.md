---
title: Personal Cloud Storage
slug: personal-cloud-storage
category: infrastructure
infra_group: personal
order: 5
demo: https://cloud.rajujha.dev
stack:
  - Nextcloud
  - Docker
  - NGINX
description: Self-hosted Nextcloud deployment for private file synchronization.
---

## Problem

Commercial cloud storage providers scan files, enforce storage limits, and retain data on infrastructure outside user control.

## Solution

Nextcloud deployed in Docker behind NGINX on GCP for private file sync, calendar, and contact storage with end-to-end control over data residency.

## Key Features

- Private file synchronization across devices
- Self-hosted — full data ownership
- Calendar and contact sync support
- Encrypted transport with TLS termination

## Links

- [cloud.rajujha.dev](https://cloud.rajujha.dev)
