---
title: SyncWave
slug: syncwave
category: opensource
order: 1
repo: https://github.com/OpenCodeQuark/syncwave
demo: https://syncwave.rajujha.dev
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

Flutter host captures 48 kHz PCM audio. A FastAPI backend manages rooms, PIN-based access, and optional WAN relay. Listeners join in the browser via Web Audio API with timestamped frames and client-side buffer adjustment for jitter. LAN-first paths keep local latency low; WAN relay handles remote listeners.

## Tech stack

Flutter/Dart host · FastAPI server · WebSockets (binary PCM) · Web Audio API listeners · Docker

## Outcome

Published as a maintained open-source project with a live demo. Used for LAN events and watch-together sessions where low-latency sync matters more than platform features.

[github.com/OpenCodeQuark/syncwave](https://github.com/OpenCodeQuark/syncwave) · [syncwave.rajujha.dev](https://syncwave.rajujha.dev)
