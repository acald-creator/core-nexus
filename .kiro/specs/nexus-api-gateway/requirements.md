# Requirements Document

## Introduction

The Nexus API Gateway is a backend service that serves as the single aggregation point between the Nexus Console frontend (React SPA) and the platform's distributed backend services. It exposes a unified REST API and SSE endpoint, authenticates all requests via JWT tokens, proxies/aggregates data from Wazuh, athena-agents, MinIO, AI Inference, and other platform services, and stores no SOC data itself.

The gateway implements the API contract defined in the nexus-console-upgrade design document. It must be containerized, composable into the existing Docker Compose and Kubernetes deployment stacks, and support real-time event streaming for the OPAR agent feed.

## Glossary

- **Gateway**: The Nexus API Gateway service described in this document
- **Console**: The Nexus Console React SPA frontend that consumes the Gateway API
- **Wazuh_API**: The Wazuh Manager REST API providing alert data and security event information
- **AI_Inference**: The FastAPI-based AI triage enrichment service at `platform/ai-inference`
- **MinIO_Client**: The S3-compatible client interface for MinIO object storage
- **Athena_Agents**: The LLM-driven adversary emulation service implementing the OPAR loop
- **OPAR_Event**: An event from the Observe/Plan/Act/Reflect execution loop in athena-agents
- **JWT**: JSON Web Token used for stateless authentication between Console and Gateway
- **SSE**: Server-Sent Events protocol for unidirectional real-time streaming from Gateway to Console
- **Vault**: HashiCorp Vault service for secrets management and optional token exchange authentication
- **Service_Registry**: The configured list of platform services with health endpoint metadata
- **Approval_Action**: A pending human-approval gate from athena-agents requiring analyst decision

## Requirements

### Requirement 1: Authentication — Login

**User Story:** As an analyst, I want to authenticate with the Gateway using my credentials, so that I receive a JWT token for subsequent API requests.

#### Acceptance Criteria

1. WHEN a valid POST request with username and password is received at `/api/v1/auth/login`, THE Gateway SHALL validate the credentials against the configured authentication provider and return a signed JWT token
2. WHEN invalid credentials are provided to `/api/v1/auth/login`, THE Gateway SHALL return HTTP 401 with an error message and SHALL NOT issue a token
3. THE Gateway SHALL support two authentication provider modes: local credential validation and Vault token exchange
4. WHEN the authentication provider is unavailable, THE Gateway SHALL return HTTP 503 with a descriptive error indicating the authentication backend is unreachable
5. THE Gateway SHALL include token expiration metadata in the login response body

### Requirement 2: Authentication — Token Validation and Refresh

**User Story:** As an analyst, I want my session token to be validated on every request and refreshable before expiry, so that I maintain secure continuous access.

#### Acceptance Criteria

1. WHEN a request is received on any endpoint other than `/api/v1/auth/login`, THE Gateway SHALL validate the JWT token from the Authorization header before processing the request
2. WHEN an invalid or expired JWT token is presented, THE Gateway SHALL return HTTP 401 and reject the request
3. WHEN a valid refresh request is received at `/api/v1/auth/refresh` with a non-expired token, THE Gateway SHALL issue a new JWT token with a fresh expiration
4. THE Gateway SHALL reject refresh requests where the original token has already expired
5. THE Gateway SHALL sign all issued tokens with a secret sourced from environment configuration or Vault, and SHALL NOT hardcode signing secrets in source code

### Requirement 3: Service Registry

**User Story:** As an analyst using the Console, I want to retrieve a list of all platform services, so that I can navigate to and monitor them from the dashboard.

#### Acceptance Criteria

1. WHEN a GET request is received at `/api/v1/services`, THE Gateway SHALL return the full list of configured service entries with id, name, description, category, url, iconId, and optional healthEndpoint fields
2. THE Gateway SHALL load service entries from a configuration file or environment variable at startup
3. WHEN the service registry configuration is malformed or missing, THE Gateway SHALL return HTTP 500 with a descriptive error and log the configuration failure
4. THE Gateway SHALL categorize each service entry into one of: security, workbenches, storage, infrastructure, or agents

### Requirement 4: Health Check Proxy

**User Story:** As an analyst, I want the Console to check service health through the Gateway, so that health probes are performed server-side without CORS or network restrictions.

#### Acceptance Criteria

1. WHEN a GET request is received at `/api/v1/health/{serviceId}`, THE Gateway SHALL proxy an HTTP health check to the configured healthEndpoint of that service
2. WHEN the target service responds within 5 seconds, THE Gateway SHALL return the upstream HTTP status code to the caller
3. WHEN the target service does not respond within 5 seconds, THE Gateway SHALL return HTTP 504 with a timeout indicator
4. WHEN the serviceId does not exist in the service registry, THE Gateway SHALL return HTTP 404
5. WHEN the service entry has no configured healthEndpoint, THE Gateway SHALL return a response with status "unknown" and SHALL NOT attempt an upstream request
6. THE Gateway SHALL include response time metadata in the health check response

### Requirement 5: Agent Event Stream (SSE)

**User Story:** As an analyst, I want to receive real-time OPAR events from athena-agents through a single SSE endpoint, so that the Console can display live agent activity.

#### Acceptance Criteria

1. WHEN an authenticated GET request is received at `/api/v1/agents/events`, THE Gateway SHALL establish an SSE connection with content type `text/event-stream`
2. THE Gateway SHALL forward OPAR events from the athena-agents event source to connected SSE clients in real time
3. WHEN an OPAR event is received from the upstream source, THE Gateway SHALL serialize the event as JSON conforming to the OPAREvent interface (id, timestamp, sessionId, phase, target, toolName, outcomeStatus, payload)
4. WHEN the upstream athena-agents connection is lost, THE Gateway SHALL send an SSE error event to connected clients and attempt reconnection with exponential backoff
5. WHEN no athena-agents sessions are active, THE Gateway SHALL keep the SSE connection open and send periodic heartbeat comments to prevent timeout
6. THE Gateway SHALL support multiple concurrent SSE client connections without blocking

### Requirement 5b: Agent Event Stream (WebSocket, optional)

**User Story:** As an analyst, I want a WebSocket alternative to SSE so clients that cannot use EventSource can still receive live OPAR events.

#### Acceptance Criteria

1. WHEN an authenticated WebSocket connects to `/api/v1/agents/events/ws`, THE Gateway SHALL stream the same OPAR envelopes as SSE (`event`, `id`, `data`)
2. THE Gateway SHALL authenticate via `Authorization: Bearer` or `?token=` (browser WebSocket cannot set headers)
3. WHEN the upstream connection is lost, THE Gateway SHALL send an `error` frame with `UPSTREAM_DISCONNECTED` and retry with exponential backoff
4. THE Gateway SHALL send JSON `heartbeat` frames when no OPAR event arrives within 15 seconds
5. SSE remains the default Console transport; WebSocket is selected with `VITE_AGENT_FEED_TRANSPORT=websocket`

### Requirement 6: Agent Sessions

**User Story:** As an analyst, I want to list current and recent agent sessions, so that I can understand which autonomous operations are active.

#### Acceptance Criteria

1. WHEN a GET request is received at `/api/v1/agents/sessions`, THE Gateway SHALL return a list of agent sessions with id, status, startTime, target, and event count metadata
2. THE Gateway SHALL retrieve session data from the athena-agents service and SHALL NOT cache session state beyond a short TTL (maximum 10 seconds)

### Requirement 7: Alerts Aggregation

**User Story:** As an analyst, I want to query security alerts through the Gateway with filtering, so that I can triage threats from a single interface.

#### Acceptance Criteria

1. WHEN a GET request is received at `/api/v1/alerts`, THE Gateway SHALL retrieve alerts from the Wazuh_API and return them in the SOCAlert response format
2. THE Gateway SHALL support query parameters for filtering by severity (critical, high, medium, low, informational), source (wazuh, suricata), and time range (from, to as ISO 8601 timestamps)
3. THE Gateway SHALL support a `limit` query parameter with a default of 100 and a maximum of 500
4. WHEN an alert contains Athena traffic-labeling metadata (X-Athena-Scenario header), THE Gateway SHALL include the athenaScenario field in the response
5. IF the Wazuh_API is unreachable, THEN THE Gateway SHALL return HTTP 502 with a descriptive error message indicating the upstream alert source is unavailable
6. THE Gateway SHALL include a `total` count field alongside the alerts array to support pagination awareness in the Console

### Requirement 8: AI Triage Results

**User Story:** As an analyst, I want to retrieve AI triage analysis for a specific alert, so that I can see confidence scores and recommended actions.

#### Acceptance Criteria

1. WHEN a GET request is received at `/api/v1/alerts/{id}/triage`, THE Gateway SHALL forward the request to the AI_Inference service and return the triage result (confidenceScore, recommendedAction, reasoningExcerpt)
2. WHEN the AI_Inference service has no triage result for the given alert id, THE Gateway SHALL return HTTP 404
3. IF the AI_Inference service is unreachable, THEN THE Gateway SHALL return HTTP 502 with an error indicating the triage service is unavailable
4. THE Gateway SHALL enforce a 10-second timeout on triage requests to the AI_Inference service

### Requirement 9: Approvals List

**User Story:** As an analyst, I want to view pending approval actions from athena-agents, so that I can review and decide on autonomous operations awaiting human authorization.

#### Acceptance Criteria

1. WHEN a GET request is received at `/api/v1/approvals`, THE Gateway SHALL return pending approval actions from athena-agents with id, sessionId, proposedTool, target, argumentsSummary, submittedAt, and status fields
2. THE Gateway SHALL default to returning only pending approvals unless an explicit `status` query parameter is provided
3. THE Gateway SHALL order pending approvals by submittedAt ascending (oldest first)

### Requirement 10: Approval Decision Submission

**User Story:** As an analyst, I want to approve or reject a pending agent action, so that I can exercise human-in-the-loop control over autonomous operations.

#### Acceptance Criteria

1. WHEN a POST request with a decision body (approve or reject) is received at `/api/v1/approvals/{id}/decision`, THE Gateway SHALL forward the decision to athena-agents
2. WHEN the decision is successfully recorded by athena-agents, THE Gateway SHALL return HTTP 200 with `{ success: true }`
3. WHEN the approval id does not exist or is no longer pending, THE Gateway SHALL return HTTP 404 or HTTP 409 respectively
4. IF athena-agents is unreachable, THEN THE Gateway SHALL return HTTP 502

### Requirement 11: Skills Listing

**User Story:** As an analyst, I want to browse available skills with search and filtering, so that I can discover and review operational playbooks.

#### Acceptance Criteria

1. WHEN a GET request is received at `/api/v1/skills`, THE Gateway SHALL return skill entries from MinIO storage (nexus-memory/skills/ bucket path) with id, name, description, tags, domain, and contentUrl fields
2. THE Gateway SHALL support query parameters for filtering by search (free-text across name and description), tag, and domain (red-team, blue-team, infrastructure, general)
3. WHEN no skills match the filter criteria, THE Gateway SHALL return an empty array with HTTP 200

### Requirement 12: Skill Content Retrieval

**User Story:** As an analyst, I want to read the full markdown content of a skill, so that I can review detailed procedures and guidance.

#### Acceptance Criteria

1. WHEN a GET request is received at `/api/v1/skills/{id}/content`, THE Gateway SHALL retrieve the raw markdown content from MinIO and return it with content type `text/markdown`
2. WHEN the skill id does not correspond to an existing object in MinIO, THE Gateway SHALL return HTTP 404
3. IF MinIO is unreachable, THEN THE Gateway SHALL return HTTP 502

### Requirement 13: Artifacts Listing

**User Story:** As an analyst, I want to list stored artifacts by category, so that I can find PCAPs, SBOMs, session logs, and skill files.

#### Acceptance Criteria

1. WHEN a GET request is received at `/api/v1/artifacts` with a `category` query parameter, THE Gateway SHALL list objects from the corresponding MinIO bucket path and return them with key, name, size, lastModified, and category fields
2. THE Gateway SHALL support artifact categories: pcaps, sboms, skills, and sessions
3. WHEN an unsupported category is provided, THE Gateway SHALL return HTTP 400 with a descriptive error
4. IF MinIO is unreachable, THEN THE Gateway SHALL return HTTP 502

### Requirement 14: Artifact Download URL Generation

**User Story:** As an analyst, I want to obtain a pre-signed download URL for an artifact, so that I can download files directly from MinIO without Gateway bandwidth overhead.

#### Acceptance Criteria

1. WHEN a GET request is received at `/api/v1/artifacts/{key}/download-url`, THE Gateway SHALL generate a pre-signed MinIO URL valid for a limited duration (default 15 minutes) and return it as `{ url: string }`
2. WHEN the artifact key does not exist in MinIO, THE Gateway SHALL return HTTP 404
3. THE Gateway SHALL NOT proxy artifact file content through its own process; the Console SHALL download directly from the pre-signed URL

### Requirement 15: CORS Configuration

**User Story:** As a Console developer, I want the Gateway to handle CORS correctly, so that the browser-based SPA can communicate with the Gateway from its origin.

#### Acceptance Criteria

1. THE Gateway SHALL include appropriate CORS headers (Access-Control-Allow-Origin, Access-Control-Allow-Methods, Access-Control-Allow-Headers, Access-Control-Allow-Credentials) on all responses
2. THE Gateway SHALL restrict allowed origins to a configurable allowlist loaded from environment configuration
3. WHEN a preflight OPTIONS request is received, THE Gateway SHALL respond with HTTP 204 and the correct CORS headers without processing further logic

### Requirement 16: Error Response Format

**User Story:** As a Console developer, I want consistent error response formatting, so that the frontend can parse and display errors uniformly.

#### Acceptance Criteria

1. WHEN an error occurs on any endpoint, THE Gateway SHALL return a JSON body with `{ error: string, code: string, details?: string }` structure
2. THE Gateway SHALL use consistent HTTP status codes: 400 for invalid input, 401 for authentication failures, 403 for authorization failures, 404 for missing resources, 409 for conflict states, 502 for upstream failures, 503 for service unavailability, 504 for upstream timeouts
3. THE Gateway SHALL NOT include stack traces or internal implementation details in error responses returned to clients

### Requirement 17: Configuration and Environment

**User Story:** As a platform operator, I want to configure the Gateway via environment variables and config files, so that I can deploy it across different environments without code changes.

#### Acceptance Criteria

1. THE Gateway SHALL accept configuration for upstream service URLs (Wazuh API, AI Inference, athena-agents, MinIO) via environment variables
2. THE Gateway SHALL accept JWT signing secret, token expiration duration, and auth provider mode via environment variables
3. THE Gateway SHALL accept service registry entries via a JSON or YAML configuration file path specified by environment variable
4. THE Gateway SHALL log a startup summary showing resolved configuration (excluding secrets) and connectivity status to upstream services
5. WHEN a required environment variable is missing, THE Gateway SHALL fail to start and log a descriptive error indicating the missing configuration

### Requirement 18: Containerization and Deployment

**User Story:** As a platform operator, I want the Gateway packaged as a container image addable to the compose stack, so that it integrates with the existing deployment model.

#### Acceptance Criteria

1. THE Gateway SHALL be packaged as a multi-stage Docker container image with a minimal production runtime
2. THE Gateway SHALL expose a single configurable port (default 3100) for both REST and SSE traffic
3. THE Gateway SHALL provide a `/healthz` endpoint that returns HTTP 200 when the service is running and accepting requests
4. THE Gateway SHALL provide a `/readyz` endpoint that returns HTTP 200 only when connections to critical upstream services (Wazuh_API, MinIO) have been verified
5. WHEN added to the compose stack, THE Gateway SHALL require only network access to upstream services and configuration environment variables — no persistent volumes or privileged access

### Requirement 19: Stateless Operation

**User Story:** As a platform operator, I want the Gateway to be horizontally scalable with no shared state, so that I can run multiple instances behind a load balancer.

#### Acceptance Criteria

1. THE Gateway SHALL NOT persist any data to local storage or databases
2. THE Gateway SHALL treat each request independently using only the JWT token and upstream service responses for state
3. WHEN multiple Gateway instances run concurrently, each instance SHALL produce identical responses for the same authenticated request and upstream state
4. THE Gateway SHALL NOT maintain session affinity requirements — any instance SHALL serve any authenticated request

### Requirement 20: Request Logging and Observability

**User Story:** As a platform operator, I want structured request logging, so that I can monitor Gateway activity and troubleshoot issues.

#### Acceptance Criteria

1. THE Gateway SHALL log each request with method, path, response status, duration, and client identifier (from JWT subject) in structured JSON format
2. THE Gateway SHALL NOT log request or response bodies containing credentials or tokens
3. WHEN an upstream service call fails, THE Gateway SHALL log the failure with upstream service identifier, error type, and duration
4. THE Gateway SHALL support a configurable log level (debug, info, warn, error) via environment variable

### Requirement 21: Rate Limiting

**User Story:** As a platform operator, I want basic rate limiting on authentication endpoints, so that brute-force attacks are mitigated.

#### Acceptance Criteria

1. THE Gateway SHALL enforce rate limiting on `/api/v1/auth/login` with a configurable maximum attempts per source IP per time window (default: 10 attempts per 60 seconds)
2. WHEN the rate limit is exceeded, THE Gateway SHALL return HTTP 429 with a Retry-After header
3. THE Gateway SHALL implement rate limiting using in-memory counters suitable for single-instance deployment, with documentation noting that distributed deployments require an external rate-limit store
