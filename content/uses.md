---
title: Uses
description: Hardware, software, and workflow defaults.
---

## Development

| Tool | Role |
|------|------|
| VS Code / Cursor | Editor |
| Linux | Primary OS |
| Docker | Local services and deployment parity |
| Git + GitHub | Version control and CI |
| Node.js (nvm) | Runtime for apps and CLI tools |
| PostgreSQL / MongoDB | Local database targets |

## Infrastructure & ops

Nginx or Caddy for reverse proxy and TLS termination. Environment variables via `.env` files locally; secrets managed per deployment target. Health endpoints and structured logging on services I maintain.

## Writing & docs

Markdown for specs, READMEs, and this site. I keep architecture notes close to the code — short ADRs, sequence diagrams when behavior is non-obvious, and runbooks for operational tasks.

## This site

Django renders Markdown from the `content/` directory. Tailwind CSS for layout. Command palette and section navigation are client-side — no SPA framework on the public page.
