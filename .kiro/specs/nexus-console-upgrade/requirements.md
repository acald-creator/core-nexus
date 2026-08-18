# Requirements Document

## Introduction

Nexus Console is the unified web launchpad and operational dashboard for the Underground Nexus platform. The current implementation is a minimal React/Vite scaffold providing static link cards to external services. This upgrade transforms it into a fully operational dashboard that surfaces agent workflow status, SOC alert feeds, approval queues, skill browsing, system health, and service navigation — effectively bringing the nexus-tui panel functionality to the browser while adding richer visualizations and interactions.

## Glossary

- **Console**: The Nexus Console React/Vite web application at `platform/nexus-console/`
- **Service_Registry**: A configuration structure within the Console that defines all navigable platform services (URLs, health endpoints, display metadata)
- **Agent_Feed_Panel**: A real-time scrollable view of OPAR execution events sourced from the agent log endpoint
- **Alerts_Panel**: A view displaying Wazuh and Suricata alerts with severity coloring and filtering
- **Approvals_Panel**: A view showing pending `needs_review` agent actions with approve/reject controls
- **Skills_Panel**: A browsable catalog of skill files with metadata, tags, and content preview
- **Health_Monitor**: A component that polls configured service endpoints and reports availability status
- **Navigation_Hub**: The section of the Console providing categorized links to external service UIs
- **Dashboard_Layout**: The responsive grid/panel system organizing operational widgets on the main view
- **API_Gateway**: The backend endpoints (or proxied services) providing agent logs, alerts, approvals, skills, and health data to the Console
- **OPAR_Event**: A structured JSON record emitted by the athena-agents OPAR loop (Observe/Plan/Act/Reflect phases)
- **Approval_Action**: A user decision (approve or reject) on a pending `needs_review` agent action

## Requirements

### Requirement 1: Service Navigation Hub

**User Story:** As a SOC analyst, I want a categorized navigation hub with all platform service links, so that I can quickly access any Underground Nexus component from a single page.

#### Acceptance Criteria

1. THE Console SHALL display a Navigation_Hub with categorized service cards grouped by domain (Security, Workbenches, Storage, Infrastructure, Agents)
2. WHEN a service card is clicked, THE Console SHALL open the target service URL in a new browser tab
3. THE Service_Registry SHALL define each service entry with a name, description, category, URL, icon identifier, and optional health endpoint
4. WHEN the Service_Registry contains services across multiple categories, THE Navigation_Hub SHALL render category headers and group services under their respective category
5. THE Navigation_Hub SHALL include entries for: Wazuh Dashboard, Grafana, MinIO Console, Jupyter Workbench, Portainer, Pi-Hole, Vault UI, and AI Inference API docs

### Requirement 2: System Health Overview

**User Story:** As a platform operator, I want to see the live health status of all platform services at a glance, so that I can identify outages or degraded components without checking each service individually.

#### Acceptance Criteria

1. THE Health_Monitor SHALL poll each configured service health endpoint at a configurable interval (default: 30 seconds)
2. WHEN a service responds with an HTTP 2xx status within 5 seconds, THE Health_Monitor SHALL display that service as "healthy"
3. WHEN a service fails to respond or returns a non-2xx status, THE Health_Monitor SHALL display that service as "degraded" or "offline" based on consecutive failure count
4. THE Console SHALL display a summary status bar showing the count of healthy, degraded, and offline services
5. IF a service transitions from healthy to degraded or offline, THEN THE Health_Monitor SHALL visually highlight the affected service card with a warning indicator
6. WHEN a service has no configured health endpoint, THE Health_Monitor SHALL display that service with an "unknown" status and skip polling for that entry

### Requirement 3: Agent Feed Panel

**User Story:** As a SOC analyst, I want to observe the OPAR agent execution feed in real time, so that I can monitor adversary emulation progress and catch anomalies during active campaigns.

#### Acceptance Criteria

1. THE Agent_Feed_Panel SHALL display OPAR_Events in a scrollable, chronologically ordered list with newest events at the top
2. WHEN a new OPAR_Event is received, THE Agent_Feed_Panel SHALL append the event to the list without requiring a page refresh
3. THE Agent_Feed_Panel SHALL display each OPAR_Event with: timestamp, phase (Observe/Plan/Act/Reflect), target identifier, tool name (for Act phase), and outcome status
4. WHEN the user selects an OPAR_Event, THE Agent_Feed_Panel SHALL expand an inline detail view showing the full event payload
5. THE Agent_Feed_Panel SHALL support filtering events by phase, target, and outcome status
6. WHILE no agent session is active, THE Agent_Feed_Panel SHALL display a "No active agent sessions" placeholder message
7. IF the data connection to the agent log source fails, THEN THE Agent_Feed_Panel SHALL display a connection error banner with a retry option

### Requirement 4: SOC Alerts Panel

**User Story:** As a SOC analyst, I want to view and triage security alerts from Wazuh and Suricata directly in the Console, so that I can perform initial triage without switching to the full Wazuh Dashboard.

#### Acceptance Criteria

1. THE Alerts_Panel SHALL display alerts in a sortable table with columns: timestamp, severity, source (Wazuh or Suricata), rule name, and affected host
2. THE Alerts_Panel SHALL color-code alert rows by severity level (critical: red, high: orange, medium: yellow, low: blue, informational: gray)
3. WHEN the Alerts_Panel loads, THE Console SHALL fetch the most recent 100 alerts from the API_Gateway
4. THE Alerts_Panel SHALL support filtering by severity level, source system, and time range
5. WHEN the user clicks an alert row, THE Alerts_Panel SHALL expand an inline detail view with the full alert payload and a link to the corresponding Wazuh Dashboard event
6. THE Alerts_Panel SHALL display a badge in the sidebar navigation showing the count of unacknowledged critical and high alerts
7. WHEN alerts originate from Athena-labeled traffic (identified by `X-Athena-Scenario` header in metadata), THE Alerts_Panel SHALL display a "Simulated" tag on those alerts

### Requirement 5: Approvals Panel

**User Story:** As a SOC analyst, I want to review and act on pending agent approval requests from the Console, so that I can authorize or reject `needs_review` agent actions without requiring terminal access.

#### Acceptance Criteria

1. THE Approvals_Panel SHALL display all pending `needs_review` Approval_Actions in a list ordered by submission time (oldest first)
2. THE Approvals_Panel SHALL display each pending action with: agent session ID, proposed tool, target, proposed arguments summary, and time pending
3. WHEN the analyst clicks "Approve" on a pending action, THE Console SHALL send an approval decision to the API_Gateway and remove the item from the pending list
4. WHEN the analyst clicks "Reject" on a pending action, THE Console SHALL send a rejection decision to the API_Gateway and remove the item from the pending list
5. THE Approvals_Panel SHALL display a badge in the sidebar navigation showing the count of pending approvals
6. IF the approval submission fails, THEN THE Console SHALL display an error message and retain the item in the pending list for retry
7. WHEN a new approval request arrives while the panel is open, THE Approvals_Panel SHALL prepend the new request to the list without requiring a page refresh

### Requirement 6: Skills Browser Panel

**User Story:** As a SOC analyst, I want to browse the agent skill library from the Console, so that I can understand what capabilities are available and review skill content.

#### Acceptance Criteria

1. THE Skills_Panel SHALL display a searchable list of all skills with: name, description, and tags
2. WHEN the user selects a skill from the list, THE Skills_Panel SHALL display the full skill markdown content in a rendered preview pane
3. THE Skills_Panel SHALL support filtering skills by tag and by free-text search across name and description
4. THE Skills_Panel SHALL group skills by domain tag (red-team, blue-team, infrastructure, general)
5. WHEN no skills match the current filter criteria, THE Skills_Panel SHALL display a "No matching skills" message

### Requirement 7: Dashboard Layout and Responsive Design

**User Story:** As a SOC analyst, I want a responsive panel layout that adapts to my screen size, so that I can use the Console effectively on both large monitors and smaller displays.

#### Acceptance Criteria

1. THE Dashboard_Layout SHALL organize panels in a configurable grid where each panel occupies a resizable tile
2. WHILE the viewport width is 1200px or greater, THE Dashboard_Layout SHALL display panels in a multi-column grid (2 or more columns)
3. WHILE the viewport width is less than 1200px, THE Dashboard_Layout SHALL stack panels in a single column
4. THE Console SHALL persist the user's selected panel arrangement in browser local storage
5. WHEN the Console loads, THE Dashboard_Layout SHALL restore the previously saved panel arrangement from local storage
6. IF no saved arrangement exists, THEN THE Dashboard_Layout SHALL display a default arrangement with Navigation_Hub and Health_Monitor visible

### Requirement 8: Sidebar Navigation with Panel Switching

**User Story:** As a SOC analyst, I want sidebar navigation to switch between panel views and see badge counts for actionable items, so that I can navigate the Console efficiently and notice when items need attention.

#### Acceptance Criteria

1. THE Console SHALL display a persistent sidebar with navigation items: Overview, Agent Feed, Alerts, Approvals, Skills, and Settings
2. WHEN the user clicks a sidebar navigation item, THE Console SHALL display the corresponding panel view in the main content area
3. THE sidebar SHALL display badge counts next to Alerts (unacknowledged critical + high count) and Approvals (pending count)
4. WHEN badge counts change, THE sidebar SHALL update the displayed counts without requiring a page refresh
5. THE sidebar SHALL visually indicate which navigation item is currently active
6. WHILE the viewport width is less than 768px, THE Console SHALL collapse the sidebar into a hamburger menu

### Requirement 9: Configuration and Environment Adaptability

**User Story:** As a platform operator, I want the Console to be configurable via environment variables, so that service URLs and API endpoints can be customized per deployment without code changes.

#### Acceptance Criteria

1. THE Console SHALL read service configuration from environment variables exposed at build time (via Vite `import.meta.env`)
2. THE Console SHALL support a runtime configuration file (`/config.json`) that overrides build-time defaults when present
3. WHEN the runtime configuration file is not found, THE Console SHALL fall back to build-time environment variable values
4. THE Service_Registry SHALL derive all service URLs from the configuration source rather than hardcoded values
5. THE Console SHALL expose a `VITE_API_GATEWAY_URL` environment variable for configuring the backend API endpoint

### Requirement 10: Authenticated API Communication

**User Story:** As a platform operator, I want all Console-to-backend communication to use authenticated channels, so that sensitive SOC data is not exposed to unauthenticated clients.

#### Acceptance Criteria

1. THE Console SHALL include an authentication token in all requests to the API_Gateway
2. WHEN the authentication token is missing or expired, THE Console SHALL redirect the user to a login view
3. THE Console SHALL store the authentication token in memory (not local storage) during the active session
4. IF an API request returns HTTP 401 or 403, THEN THE Console SHALL clear the session state and redirect to the login view
5. THE Console SHALL support token-based authentication compatible with the platform's Vault-issued tokens or a configurable OAuth2/OIDC provider

### Requirement 11: AI Inference and Triage Integration

**User Story:** As a SOC analyst, I want to see AI triage results alongside alerts, so that I can leverage LLM-driven analysis to accelerate triage decisions.

#### Acceptance Criteria

1. WHEN an alert has an associated AI triage result, THE Alerts_Panel SHALL display a triage summary (confidence score, recommended action, reasoning excerpt) inline with the alert detail view
2. THE Console SHALL fetch AI triage results from the AI Inference API endpoint configured in the Service_Registry
3. WHEN no AI triage result exists for an alert, THE Alerts_Panel SHALL display a "No AI triage available" indicator in the detail view
4. THE Navigation_Hub SHALL include a link to the AI Inference API documentation (FastAPI /docs endpoint)

### Requirement 12: MinIO Artifact Browsing

**User Story:** As a SOC analyst, I want to browse key artifact categories stored in MinIO directly from the Console, so that I can quickly access PCAPs, SBOMs, session logs, and skill files without navigating to the MinIO UI.

#### Acceptance Criteria

1. THE Console SHALL provide an Artifacts view listing object categories from the configured MinIO `nexus-bucket` (PCAPs, SBOMs, skills, sessions)
2. WHEN the user selects an artifact category, THE Console SHALL display the list of objects in that category with name, size, and last-modified date
3. WHEN the user clicks an artifact, THE Console SHALL generate a pre-signed download URL and initiate the download
4. IF the MinIO connection is unavailable, THEN THE Console SHALL display a connection error with a link to the MinIO Console UI as fallback

### Requirement 13: Dark Theme and Visual Design

**User Story:** As a SOC analyst working in a darkened operations center, I want the Console to use a dark theme by default, so that the interface reduces eye strain during extended monitoring sessions.

#### Acceptance Criteria

1. THE Console SHALL render with a dark color theme by default (dark backgrounds, light text, muted accent colors)
2. THE Console SHALL use consistent color semantics: red for critical/error, orange for high/warning, green for healthy/success, blue for informational, gray for inactive
3. THE Console SHALL use a monospace font for log entries, event payloads, and code content in the Agent_Feed_Panel and Skills_Panel
4. THE Console SHALL maintain WCAG 2.1 AA contrast ratios (minimum 4.5:1 for normal text, 3:1 for large text) across all theme colors
