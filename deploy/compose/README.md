# Compose Stacks

## Dev Stack (`dev.yml`) — Recommended for local development

Starts the full Nexus platform locally:
- **Nexus Console** (React SPA) → http://localhost:3000
- **API Gateway** (FastAPI) → http://localhost:3100 (API docs at /docs)
- **MinIO** (Object storage) → http://localhost:9001 (minioadmin/minioadmin)
- **AI Inference** (FastAPI triage) → http://localhost:8000

```bash
# Preferred — secrets from nexus-hashistack
./scripts/dev-stack.sh up --from-vault

# Offline defaults only
./scripts/dev-stack.sh up

# Seed MinIO with skills (after stack is running)
./scripts/seed-minio-skills.sh

# Check status
./scripts/dev-stack.sh status

# View logs
./scripts/dev-stack.sh logs

# Stop
./scripts/dev-stack.sh down
```

### Console Access

The Console runs at http://localhost:3000. Compose builds with
`VITE_DEV_AUTH_BYPASS=true` so the SPA auto-logins against the gateway (lab only).
Published images should build with `VITE_DEV_AUTH_BYPASS=false` via
`./scripts/build-platform-images.sh`.

Optional stricter gateway login:

```bash
NEXUS_GW_LOCAL_USERS='analyst:changeme' ./scripts/dev-stack.sh up --from-vault
```

For local frontend hot reload, run `npm run dev` in `platform/nexus-console/` (port 5173).

### Connecting to SOC Baseline

The SOC baseline (Wazuh + Suricata + webtop) lives in **nexus-webtop-soc** — do not
vend a second copy in this repo:

```bash
cd ../nexus-webtop-soc
docker compose -f deploy/compose/soc-baseline.yml up -d
```

Set `NEXUS_GW_WAZUH_API_URL` to point at the Wazuh manager.

### Connecting to HashiStack (Vault)

[nexus-hashistack](https://github.com/acald-creator/nexus-hashistack) provides local Vault on `:8200`. After exporting AppRoles:

```bash
cd ../nexus-hashistack
./scripts/nexus-dev-up.sh && ./scripts/admin-bootstrap-approle.sh
./scripts/export-core-nexus-env.sh
cp .env.core-nexus ../core-nexus/.env.vault
cd ../core-nexus && ./scripts/dev-stack.sh up --from-vault
```

Compose then receives JWT / MinIO / Wazuh values plus gateway AppRole ids (`NEXUS_GW_VAULT_*`) so the API Gateway can re-read `secret/nexus/dev` at startup. Wazuh stays on the exported env (gateway AppRole cannot read `secret/soc/*`). Prefer `up --from-vault`; set `NEXUS_REQUIRE_VAULT=1` to refuse bare `up`.

### Connecting to Athena / Agent Feed

Athena profiles run from `nexus-athena`. The compose gateway defaults
`NEXUS_GW_ATHENA_AGENTS_URL` to `host.docker.internal:8080`, but **compose does not
start athena-agents**. For Console Agent Feed until the real HTTP API exists:

```bash
NEXUS_ENABLE_DAY9_BRIDGE=1 ./scripts/start-day9-dev-stack.sh
```

That temporary bridge mocks `:8080` (`scripts/day9-console-bridge.py`). Replace it when athena-agents exposes `/sessions` and `/events`.

```bash
cd ../nexus-athena
./scripts/run-athena-profile.sh agent juice-shop.lab
```

### Platform images

Compose services use `phoenixvlabs/nexus-*:latest` tags (with local `build:` contexts).
Kubernetes SOC base uses the same registry. Build/push with:

```bash
./scripts/build-platform-images.sh
./scripts/build-platform-images.sh --push
```

## Legacy Stacks

- `baseline.yml` — Original "Olympiad" deployment (Console + Pi-hole + Portainer + nginx-proxy)
- `portainer-deploy.yml` — Standalone Portainer
- `docker-compose.yml` — Legacy root compose (deprecated)
- SOC baseline compose → sibling `nexus-webtop-soc/deploy/compose/soc-baseline.yml`
