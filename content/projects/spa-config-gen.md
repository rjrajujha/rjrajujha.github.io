---
title: spa-config-gen
slug: spa-config-gen
category: opensource
order: 2
repo: https://github.com/rjrajujha/spa-config-gen
demo: https://www.npmjs.com/package/spa-config-gen
stack:
  - TypeScript
  - Node.js
  - CLI
  - Nginx
  - Apache
description: CLI that generates SPA routing configs for Apache, Nginx, Caddy, Traefik, and HAProxy.
---

## Problem

SPAs break on direct URL access or refresh unless the reverse proxy rewrites unknown paths to `index.html`. Writing correct `try_files`, `RewriteRule`, or Traefik middleware blocks is repetitive across teams and hosting targets.

## Solution

Node.js CLI with per-server templates that emit copy-paste-ready config snippets. No runtime dependency in production — output is static config consumed by the web server.

```bash
npx spa-config-gen --server nginx --output nginx.conf
```

## Tech stack

TypeScript · Node.js · npm package · Apache, Nginx, Caddy, Traefik, HAProxy targets

## Outcome

Published on npm with semver releases. Reduces deployment misconfiguration for SPA routing across common reverse proxies.

[github.com/rjrajujha/spa-config-gen](https://github.com/rjrajujha/spa-config-gen) · [npm: spa-config-gen](https://www.npmjs.com/package/spa-config-gen)
