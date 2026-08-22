---
name: Console Gateway MinIO Browser Path
description: Keep CORS preflight at 204, point the SPA at gateway :3100, and rewrite MinIO presigned URLs to a host the browser can reach
tags: [code-debug, deployment, cors, minio, nexus-console]
inclusion: manual
---

## When to Apply
- Console in the browser cannot call the API Gateway (CORS errors, wrong port)
- Artifact download URLs contain `minio:9000` or another compose-internal hostname
- Gateway OPTIONS preflight returns 200 instead of 204
- Docker-built Console still talks to `:8080` or a build-time empty `VITE_API_GATEWAY_URL`

## Approach
1. Confirm identities: browser origin (`localhost:3000` or Vite `5173`), Gateway published port (`3100`), MinIO API published port (`9000`)
2. Put CORS outermost (last `add_middleware`). Skip JWT on OPTIONS. Return **204** on preflight, not Starlette's default 200
3. Bake `VITE_API_GATEWAY_URL=http://localhost:3100` at Console **build** time. Runtime nginx cannot change Vite env
4. Set `NEXUS_GW_MINIO_PUBLIC_ENDPOINT=localhost:9000` so presigned URLs rewrite `minio:9000` → a host the browser can open
5. Set MinIO `MINIO_API_CORS_ALLOW_ORIGIN` to the same SPA origins, or the follow-up GET on the presigned URL fails even when Gateway CORS is correct
6. Prove the contract with Gateway tests (preflight 204, 401 still has CORS headers, list + download-url, host rewrite). A live compose click-through is separate

## Key Patterns
- Gateway default and Console fallback are both `:3100`. Port `8080` is athena-agents, not the Gateway
- `MinIOClient.get_presigned_url()` replaces `self._endpoint` with `self._public_endpoint` once
- `NexusCORSMiddleware.preflight_response` copies Starlette headers onto an empty 204 body
- Compose `dev.yml` already maps Console `3000:80`, Gateway `3100:3100`, MinIO `9000:9000`

## Pitfalls
- Starlette `CORSMiddleware` preflight is 200 unless subclassed. Spec Req 15.3 wants 204
- First-added FastAPI middleware is innermost. Comment the wire order, not the `add_middleware` call order
- Presigned URL signatures are over the host in the URL. Rewrite host only when the Gateway issued the URL against the internal endpoint and the public host is a published map of the same MinIO
- Empty MinIO list + intact CORS is success for the pipe. Do not treat an empty Artifacts panel as a CORS failure
- Do not commit `platform/api-gateway/.venv`

## References
- `platform/api-gateway/src/middleware/cors.py`
- `platform/api-gateway/src/clients/minio_client.py`
- `platform/nexus-console/src/config/defaults.ts`
- `platform/nexus-console/Dockerfile`
- `deploy/compose/dev.yml`
- `.kiro/specs/nexus-api-gateway/requirements.md` Req 15.3
