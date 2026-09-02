---
title: Private Search Engine
slug: private-search-engine
category: infrastructure
infra_group: public
order: 2
demo: https://search.rajujha.dev
stack:
  - SearXNG
  - Docker
  - NGINX
description: Self-hosted SearXNG instance providing privacy-focused web search.
---

## Problem

Mainstream search engines track queries, build profiles, and inject personalized results. A self-hosted alternative was needed that aggregates results without storing user data.

## Solution

SearXNG deployed in Docker behind NGINX on GCP. Aggregates results from multiple engines while stripping tracking parameters and blocking referrer leakage.

## Key Features

- No query tracking or user profiling
- Open-source SearXNG engine
- Self-hosted on private infrastructure
- Aggregated results from multiple search providers

## Links

- [search.rajujha.dev](https://search.rajujha.dev)
