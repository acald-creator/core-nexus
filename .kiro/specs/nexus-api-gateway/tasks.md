# Implementation Plan: Nexus API Gateway

## Overview

Build a stateless Python/FastAPI API Gateway service at `platform/api-gateway/` that aggregates all Nexus platform backend services behind a unified REST + SSE interface. Implementation follows an incremental approach: project scaffolding → configuration → middleware → upstream clients → route modules → SSE streaming → containerization → wiring. Each step produces runnable, testable code that builds on prior work.

## Tasks

- [ ] 1. Project scaffolding and core infrastructure
  - [ ] 1.1 Create project structure, dependencies, and application factory
    - Create `platform/api-gateway/` directory structure as defined in design (src/, src/middleware/, src/clients/, src/models/, src/routes/, tests/, tests/properties/, config/)
    - Create `requirements.txt` with pinned dependencies: fastapi>=0.115.0, uvicorn[standard]>=0.30.0, httpx>=0.27.0, minio>=7.2.0, PyJWT>=2.9.0, sse-starlette>=2.0.0, structlog>=24.0.0, slowapi>=0.1.9, pydantic>=2.9.0, pydantic-settings>=2.5.0
    - Create `requirements-dev.txt` with: pytest, pytest-asyncio, httpx (test client), hypothesis, pytest-cov
    - Create `src/__init__.py`, `src/main.py` (uvicorn entrypoint), and `src/app.py` (application factory with `create_app()`)
    - Create `tests/conftest.py` with shared fixtures (test client, mock settings, mock JWT token generation)
    - _Requirements: 17.1, 17.2, 17.3, 18.1_

  - [ ] 1.2 Implement configuration module with pydantic-settings
    - Create `src/config.py` with `GatewaySettings` class using `env_prefix = "NEXUS_GW_"`
    - Define all fields per design: port, debug, log_level, jwt_secret, jwt_algorithm, jwt_expiration_minutes, auth_provider, vault_url, wazuh_api_url, wazuh_api_user, wazuh_api_password, ai_inference_url, athena_agents_url, minio_endpoint, minio_access_key, minio_secret_key, minio_secure, minio_bucket, cors_allowed_origins, login_rate_limit, service_registry_path
    - Ensure required fields (jwt_secret, wazuh_api_url, minio_access_key, minio_secret_key) cause startup failure with descriptive error when missing
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

  - [ ]* 1.3 Write property test for configuration startup validation
    - **Property 12: Configuration startup validation**
    - Test that arbitrary env var combinations missing any required variable raise a descriptive error
    - Use hypothesis strategies to generate env var sets with selective omissions
    - **Validates: Requirements 17.5**

  - [ ] 1.4 Implement structured logging configuration
    - Create `src/logging_config.py` with `configure_logging(log_level)` using structlog
    - Configure processors: merge_contextvars, add_log_level, TimeStamper(fmt="iso"), JSONRenderer
    - Call from `create_app()` during startup
    - _Requirements: 20.1, 20.4_

- [ ] 2. Authentication middleware and JWT handling
  - [ ] 2.1 Implement JWT authentication middleware
    - Create `src/middleware/auth.py` with `JWTAuthMiddleware` extending `BaseHTTPMiddleware`
    - Define `PUBLIC_PATHS` set: /api/v1/auth/login, /healthz, /readyz, /docs, /openapi.json
    - Skip auth for OPTIONS requests (CORS preflight)
    - Extract token from `Authorization: Bearer <token>` header or `token` query param (SSE fallback)
    - Decode with PyJWT, set `request.state.user` on success
    - Return 401 with appropriate error code for missing, expired, or invalid tokens
    - _Requirements: 2.1, 2.2, 2.4, 2.5_

  - [ ]* 2.2 Write property test for JWT round-trip integrity
    - **Property 1: JWT round-trip integrity**
    - For arbitrary username/role combinations, encode then decode with same secret produces identical sub, role, iat, exp
    - Use hypothesis text() and sampled_from() strategies
    - **Validates: Requirements 1.1, 2.5**

  - [ ]* 2.3 Write property test for expired token rejection
    - **Property 2: Expired token rejection**
    - For any JWT with exp in the past, middleware returns 401 regardless of other payload contents
    - Use hypothesis to generate arbitrary past timestamps and payload contents
    - **Validates: Requirements 2.2, 2.4**

  - [ ] 2.4 Implement auth routes (login and refresh)
    - Create `src/models/auth.py` with LoginRequest and LoginResponse Pydantic models
    - Create `src/routes/auth.py` with POST `/login` and POST `/refresh` endpoints
    - Login: validate credentials, issue signed JWT with configurable expiration
    - Refresh: validate current token not expired, issue new token
    - Return 401 for invalid credentials, 503 if auth provider unavailable
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.3, 2.4_

  - [ ] 2.5 Implement rate limiting on login endpoint
    - Integrate slowapi with in-memory storage
    - Apply rate limit decorator to `/api/v1/auth/login` using configurable `login_rate_limit` setting
    - Return HTTP 429 with Retry-After header when exceeded
    - _Requirements: 21.1, 21.2, 21.3_

  - [ ]* 2.6 Write property test for rate limit enforcement
    - **Property 13: Rate limit enforcement**
    - For any source IP, after N login attempts within the window, subsequent requests receive 429 with Retry-After
    - Use hypothesis to generate sequences of requests from arbitrary IPs
    - **Validates: Requirements 21.1, 21.2**

- [ ] 3. Checkpoint - Core infrastructure verified
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Error handling and request logging middleware
  - [ ] 4.1 Implement global error handler
    - Create `src/middleware/error_handler.py` with global exception handler
    - Create `src/models/errors.py` with ErrorResponse Pydantic model: `{ error: str, code: str, details: str | None }`
    - Handle StarletteHTTPException, map to consistent JSON format
    - Catch unhandled exceptions, log full traceback, return generic 500 without stack traces
    - Register as exception handler in `create_app()`
    - _Requirements: 16.1, 16.2, 16.3_

  - [ ]* 4.2 Write property test for error response format consistency
    - **Property 11: Error response format consistency**
    - For any error (4xx or 5xx), response conforms to `{ error: string, code: string, details?: string }` and contains no stack traces
    - Generate arbitrary HTTP exceptions and verify format
    - **Validates: Requirements 16.1, 16.2, 16.3**

  - [ ] 4.3 Implement request logging middleware
    - Create `src/middleware/request_logger.py` with structured request logging
    - Log: method, path, status, duration_ms, client_ip, user_sub (from JWT state)
    - Exclude logging of request/response bodies on auth endpoints
    - Log upstream failures with service identifier, error type, and duration
    - _Requirements: 20.1, 20.2, 20.3, 20.4_

- [ ] 5. Service registry and health check proxy
  - [ ] 5.1 Implement service registry route
    - Create `src/models/services.py` with ServiceEntry Pydantic model (id, name, description, category, url, iconId, healthEndpoint)
    - Create `src/routes/services.py` with GET `/services` endpoint
    - Load service entries from JSON config file at startup (path from settings.service_registry_path)
    - Create `config/services.json` with default service registry entries
    - Return 500 with descriptive error if config is malformed
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ]* 5.2 Write property test for service registry categorization completeness
    - **Property 3: Service registry categorization completeness**
    - For any set of service entries, grouping by category produces no loss/duplication, every category is valid
    - Use hypothesis to generate lists of service entries with valid categories
    - **Validates: Requirements 3.1, 3.4**

  - [ ] 5.3 Implement health check proxy route
    - Create `src/models/health.py` with HealthCheckResponse Pydantic model (serviceId, status, statusCode, responseTimeMs)
    - Create `src/routes/health.py` with GET `/health/{service_id}` endpoint
    - Proxy HTTP GET to configured healthEndpoint with 5-second timeout
    - Return 504 on timeout, 404 for unknown serviceId, status "unknown" for services without healthEndpoint
    - Include response time in response
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ]* 5.4 Write property test for health check timeout determinism
    - **Property 4: Health check timeout determinism**
    - For any service with a configured health endpoint, if upstream doesn't respond within 5s, gateway returns 504
    - Mock httpx to simulate timeouts; verify deterministic 504 response
    - **Validates: Requirements 4.2, 4.3**

- [ ] 6. Upstream clients implementation
  - [ ] 6.1 Implement Wazuh API client
    - Create `src/clients/wazuh.py` with WazuhClient class
    - Implement: authenticate() for Wazuh token, get_alerts() with severity/source/time/limit filtering, close()
    - Use httpx.AsyncClient with connect=5s, read=10s timeouts, verify=False for self-signed certs
    - _Requirements: 7.1, 7.2, 7.3, 7.5_

  - [ ] 6.2 Implement MinIO client wrapper
    - Create `src/clients/minio_client.py` with MinIOClient class
    - Implement: list_objects(prefix), get_presigned_url(key, expires_minutes=15), get_object_content(key)
    - Wrap minio Python SDK; handle bucket verification
    - _Requirements: 11.1, 12.1, 13.1, 14.1_

  - [ ] 6.3 Implement athena-agents client
    - Create `src/clients/athena.py` with AthenaClient class
    - Implement: get_sessions(), get_event_stream() as AsyncIterator, get_approvals(status), submit_decision(approval_id, decision), close()
    - Use httpx.AsyncClient with connect=5s, read=10s timeouts
    - _Requirements: 5.2, 6.1, 9.1, 10.1_

  - [ ] 6.4 Implement AI Inference client
    - Create `src/clients/ai_inference.py` with AIInferenceClient class
    - Implement: get_triage(alert_id) returning dict or None, close()
    - Enforce 10-second timeout on triage requests
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 7. Checkpoint - Clients and middleware verified
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Alert and triage routes
  - [x] 8.1 Implement alerts route with filtering
    - Create `src/models/alerts.py` with SOCAlert, AlertsResponse, TriageResponse Pydantic models
    - Create `src/routes/alerts.py` with GET `/alerts` endpoint
    - Support query params: severity, source, from (alias from_ts), to (alias to_ts), limit (default 100, max 500)
    - Clamp limit to [1, 500] range
    - Include athenaScenario field when X-Athena-Scenario metadata present
    - Return total count alongside alerts array
    - Return 502 if Wazuh unreachable
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [x]* 8.2 Write property test for alert filter correctness
    - **Property 5: Alert filter correctness**
    - For any set of alerts and any filter combination, all returned alerts satisfy all predicates, no matching alert excluded
    - Use hypothesis to generate alert lists and filter parameter combinations
    - **Validates: Requirements 7.1, 7.2, 7.3**

  - [x]* 8.3 Write property test for alert limit clamping
    - **Property 6: Alert limit clamping**
    - For any limit value, gateway clamps to [1, 500]; response has at most limit items; default is 100
    - Use hypothesis integers() with wide range including negatives and large values
    - **Validates: Requirements 7.3**

  - [x]* 8.4 Write property test for Athena scenario tagging preservation
    - **Property 7: Athena scenario tagging preservation**
    - For alerts with X-Athena-Scenario: field present; for alerts without: field absent/null
    - Use hypothesis to generate alerts with and without scenario metadata
    - **Validates: Requirements 7.4**

  - [x] 8.5 Implement alert triage route
    - Add GET `/alerts/{alert_id}/triage` endpoint to alerts router
    - Forward to AI Inference client, return TriageResponse
    - Return 404 if no triage result, 502 if inference unreachable, 504 if timeout >10s
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 9. Agent routes (sessions and SSE streaming)
  - [ ] 9.1 Implement agent sessions route
    - Create `src/models/agents.py` with OPAREvent and AgentSession Pydantic models
    - Create `src/routes/agents.py` with GET `/agents/sessions` endpoint
    - Return list of sessions from athena-agents client
    - _Requirements: 6.1, 6.2_

  - [ ] 9.2 Implement SSE event streaming for OPAR events
    - Add GET `/agents/events` endpoint to agents router
    - Implement `_event_generator()` with heartbeat (15s ping) and exponential backoff reconnection (1s base, 30s max)
    - Authenticate via query param token (SSE fallback)
    - Forward OPAR events as JSON with event type "opar"
    - Send error event on upstream disconnect, then reconnect
    - Use sse-starlette EventSourceResponse
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ] 10. Approvals routes
  - [ ] 10.1 Implement approvals list and decision routes
    - Create `src/models/approvals.py` with ApprovalAction, DecisionRequest, DecisionResponse models
    - Create `src/routes/approvals.py` with GET `/approvals` and POST `/approvals/{id}/decision` endpoints
    - Default filter to pending approvals; support status query param
    - Order pending approvals by submittedAt ascending
    - Forward decisions to athena-agents client
    - Return 404/409 for not found/conflict, 502 if unreachable
    - _Requirements: 9.1, 9.2, 9.3, 10.1, 10.2, 10.3, 10.4_

  - [ ]* 10.2 Write property test for approval ordering invariant
    - **Property 8: Approval ordering invariant**
    - For any set of pending approvals, response is ordered by submittedAt ascending regardless of insertion order
    - Use hypothesis to generate approval lists with random timestamps
    - **Validates: Requirements 9.3**

- [ ] 11. Skills and artifacts routes
  - [ ] 11.1 Implement skills routes
    - Create `src/models/skills.py` with SkillEntry Pydantic model
    - Create `src/routes/skills.py` with GET `/skills` and GET `/skills/{skill_id}/content` endpoints
    - Support query params: search (free-text), tag, domain
    - Return skill content as text/markdown
    - Return empty array for no matches, 404 for missing skill, 502 if MinIO unreachable
    - _Requirements: 11.1, 11.2, 11.3, 12.1, 12.2, 12.3_

  - [ ]* 11.2 Write property test for skills search filter consistency
    - **Property 9: Skills search filter consistency**
    - For any skill set and filter combination, all returned skills match every criterion, no matching skill excluded
    - Use hypothesis to generate skill lists and filter combinations
    - **Validates: Requirements 11.1, 11.2, 11.3**

  - [ ] 11.3 Implement artifacts routes
    - Create `src/models/artifacts.py` with ArtifactCategory, ArtifactObject, DownloadUrlResponse models
    - Create `src/routes/artifacts.py` with GET `/artifacts` and GET `/artifacts/{key:path}/download-url` endpoints
    - Validate category against allowed set (pcaps, sboms, skills, sessions); return 400 for invalid
    - Generate pre-signed MinIO URLs with 15-minute expiry
    - Return 404 for missing key, 502 if MinIO unreachable
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 14.1, 14.2, 14.3_

  - [ ]* 11.4 Write property test for artifact category validation
    - **Property 10: Artifact category validation**
    - For any category string not in ["pcaps", "sboms", "skills", "sessions"], gateway returns 400
    - Use hypothesis text() to generate arbitrary strings
    - **Validates: Requirements 13.2, 13.3**

  - [ ]* 11.5 Write property test for pre-signed URL generation correctness
    - **Property 15: Pre-signed URL generation correctness**
    - For any valid artifact key, returned URL contains the key path and includes signature/expiration params, no raw credentials exposed
    - Use hypothesis to generate valid key strings
    - **Validates: Requirements 14.1, 14.3**

- [ ] 12. Checkpoint - All routes implemented and tested
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. CORS, probes, and application wiring
  - [x] 13.1 Configure CORS middleware
    - Add CORSMiddleware to app factory with configurable allowed origins from settings
    - Allow methods: GET, POST, PUT, DELETE, OPTIONS
    - Allow headers: Authorization, Content-Type
    - Allow credentials: true
    - Ensure OPTIONS preflight returns 204 with correct headers
    - _Requirements: 15.1, 15.2, 15.3_

  - [ ] 13.2 Implement health and readiness probes
    - Create `src/routes/probes.py` with GET `/healthz` (liveness) and GET `/readyz` (readiness)
    - `/healthz` returns 200 `{ status: "ok" }` unconditionally
    - `/readyz` checks Wazuh and MinIO connectivity; returns 200 if all ok, 503 if any unreachable
    - Include per-service check results in response
    - _Requirements: 18.3, 18.4_

  - [ ] 13.3 Wire all routers and middleware in application factory
    - Register all route modules with correct prefixes in `create_app()`
    - Initialize upstream clients on startup, store on `app.state`
    - Register shutdown handlers to close all clients
    - Log startup configuration summary (excluding secrets)
    - Ensure middleware order: CORS → Auth → Rate Limiting → Request Logger
    - _Requirements: 17.4, 18.5, 19.1, 19.2, 19.3, 19.4_

  - [ ]* 13.4 Write property test for stateless response determinism
    - **Property 14: Stateless response determinism**
    - For any authenticated request with identical JWT and upstream state, two handler invocations produce identical responses
    - Use hypothesis to generate request parameters; call handler twice with same mocked upstream state
    - **Validates: Requirements 19.1, 19.2, 19.3, 19.4**

- [ ] 14. Containerization and compose integration
  - [ ] 14.1 Create Dockerfile and compose integration
    - Create `platform/api-gateway/Dockerfile` with multi-stage build (python:3.11-slim)
    - Stage 1: install dependencies from requirements.txt
    - Stage 2: copy site-packages, src/, config/; expose 3100; CMD uvicorn
    - Create `platform/api-gateway/docker-compose.override.yml` for local dev with mock upstreams
    - Add api-gateway service definition to `deploy/compose/baseline.yml` per design
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [ ] 15. Final checkpoint - Full integration verified
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at logical boundaries
- Property tests validate universal correctness properties defined in the design document
- Unit tests validate specific examples and edge cases
- All upstream services are mocked in tests — no live service dependencies for test execution
- Implementation language: Python 3.11 (explicitly specified in design)
- The service is stateless — no database migrations or persistent storage setup required

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.4"] },
    { "id": 2, "tasks": ["1.3", "2.1", "4.1"] },
    { "id": 3, "tasks": ["2.2", "2.3", "2.4", "4.2", "4.3"] },
    { "id": 4, "tasks": ["2.5", "5.1", "6.1", "6.2", "6.3", "6.4"] },
    { "id": 5, "tasks": ["2.6", "5.2", "5.3"] },
    { "id": 6, "tasks": ["5.4", "8.1", "9.1", "10.1", "11.1", "11.3"] },
    { "id": 7, "tasks": ["8.2", "8.3", "8.4", "8.5", "9.2", "10.2", "11.2", "11.4"] },
    { "id": 8, "tasks": ["11.5", "13.1", "13.2"] },
    { "id": 9, "tasks": ["13.3"] },
    { "id": 10, "tasks": ["13.4", "14.1"] }
  ]
}
```
