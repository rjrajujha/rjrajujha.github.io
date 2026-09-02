---
title: Personal Automation Stack
slug: personal-automation-stack
category: infrastructure
infra_group: personal
order: 4
demo: https://n8n.rajujha.dev
stack:
  - n8n
  - Docker
  - NGINX
description: Private workflow automation using n8n.
---

## Problem

Cloud automation platforms store credentials and workflow data on third-party servers. A self-hosted alternative was needed for personal integrations without exposing sensitive tokens.

## Solution

n8n deployed in Docker behind NGINX on GCP with authenticated access. Workflows connect APIs, webhooks, and scheduled tasks in a private automation environment.

## Key Features

- Self-hosted workflow automation
- Integrations with external APIs and webhooks
- Credential storage on private infrastructure
- Scheduled and event-driven task execution

## Links

- [n8n.rajujha.dev](https://n8n.rajujha.dev)
