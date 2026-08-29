# Compose Stacks

## Dev Stack (`dev.yml`) — Recommended for local development

Starts the full Nexus platform locally:
- **Nexus Console** (React SPA) → http://localhost:3000
- **API Gateway** (FastAPI) → http://localhost:3100 (API docs at /docs)
- **MinIO** (Object storage) → http://localhost:9001 (minioadmin/minioadmin)
- **AI Inference** (FastAPI triage) → http://localhost:8000

```bash
# Start everything
./scripts/dev-stack.sh up

# Or start with secrets exported from nexus-hashistack Vault
./scripts/dev-stack.sh up --from-vault

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

The Console runs at http://localhost:3000 with dev auth bypass enabled.
For local frontend dev with hot reload, run `npm run dev` in `platform/nexus-console/` (port 5173) instead.

### Connecting to SOC Baseline

The SOC baseline (Wazuh + Suricata) runs as a separate stack in `nexus-webtop-soc`:

```bash
cd ~/nexus-webtop-soc
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

Compose then receives JWT / MinIO / Wazuh values plus gateway AppRole ids (`NEXUS_GW_VAULT_*`) so the API Gateway can re-read `secret/nexus/dev` at startup.

### Connecting to Athena

Athena profiles run from `nexus-athena`:

```bash
cd ~/nexus-athena
./scripts/run-athena-profile.sh agent juice-shop.lab
```

## Legacy Stacks

- `baseline.yml` — Original "Olympiad" deployment (Console + Pi-hole + Portainer + nginx-proxy)
- `portainer-deploy.yml` — Standalone Portainer
- `soc-baseline.yml` — Symlink/reference to nexus-webtop-soc SOC stack
- `docker-compose.yml` — Legacy root compose (deprecated)
