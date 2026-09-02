---
title: SyncWave
slug: syncwave
category: opensource
order: 1
repo: https://github.com/OpenCodeQuark/syncwave
stack:
  - Dart
  - Flutter
  - FastAPI
  - WebSockets
  - Docker
description: Local-first synchronized audio rooms with LAN/WAN hosting and browser listeners.
---

## Problem

Multiple devices need to play the same audio stream in sync — party rooms, watch-together sessions, or LAN events — without a commercial streaming platform. Latency and clock drift must stay within perceptible limits.

## Solution

Flutter host captures 48 kHz PCM audio. A FastAPI backend manages rooms, PIN-based access, and optional WAN relay. Listeners join in the browser via Web Audio API with timestamped frames and client-side buffer adjustment for jitter.

## Key Features

- LAN-first paths for low local latency
- WAN relay for remote listeners
- PIN-based room access control
- Maintained open-source project with live demo

## Links

- [GitHub](https://github.com/OpenCodeQuark/syncwave)
