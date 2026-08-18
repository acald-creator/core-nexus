# Implementation Plan: Nexus Console Upgrade

## Overview

Transform the minimal React 19 + Vite 8 scaffold into a fully operational SOC dashboard. Implementation proceeds bottom-up: dependencies and infrastructure first (config, auth, API client, theme), then shared components (sidebar, layout), then individual feature panels (health, navigation, agent feed, alerts, approvals, skills, artifacts), and finally integration wiring. All code is TypeScript. The API Gateway is contract-only — this plan covers frontend implementation exclusively.

## Tasks

- [ ] 1. Project setup, dependencies, and core infrastructure
  - [ ] 1.1 Install dependencies and configure tooling
    - Add `react-router`, `@tanstack/react-query`, `react-markdown`, `remark-gfm` to dependencies
    - Add `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `fast-check` to devDependencies
    - Configure Vitest in `vite.config.ts` and add `test` script to `package.json`
    - Create `src/test/setup.ts` with testing-library jest-dom matchers
    - _Requirements: 9.1_

  - [ ] 1.2 Create theme and global CSS foundation
    - Create `src/theme/variables.css` with CSS custom properties for dark theme (backgrounds, text, accents, severity colors)
    - Create `src/theme/global.css` with reset, typography (monospace for code), and base dark theme application
    - Ensure WCAG 2.1 AA contrast ratios (4.5:1 normal text, 3:1 large text)
    - Import theme CSS in `src/main.tsx`
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

  - [ ] 1.3 Create configuration system types and loader
    - Create `src/config/types.ts` with `NexusConfig`, `ServiceEntry`, `ServiceCategory` interfaces
    - Create `src/config/defaults.ts` with build-time defaults reading from `import.meta.env`
    - Create `src/config/loader.ts` that fetches `/config.json` and merges over build-time defaults
    - Create `src/config/ConfigContext.tsx` providing `NexusConfig` via React context
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 1.4 Write property test for configuration merge precedence
    - **Property 15: Configuration merge precedence**
    - Verify runtime config overrides build-time for matching keys, preserves build-time for absent keys
    - **Validates: Requirements 9.2, 9.3**

  - [ ] 1.5 Create authentication layer
    - Create `src/api/types/auth.ts` with `AuthState`, `LoginCredentials` interfaces
    - Create `src/auth/AuthContext.tsx` with in-memory token storage (useRef), login/logout methods
    - Create `src/auth/AuthGuard.tsx` that redirects unauthenticated users to `/login`
    - Create `src/auth/LoginView.tsx` with username/password form
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ] 1.6 Create typed API client
    - Create `src/api/client.ts` with `ApiClient` interface and `createApiClient` factory
    - Implement typed `get`, `post`, `put`, `delete` methods wrapping native `fetch`
    - Inject auth token from context and base URL from config
    - Throw typed `ApiError` on non-2xx responses
    - Handle 401/403 by clearing auth state and redirecting to login
    - Create `src/api/endpoints.ts` with endpoint path constants
    - _Requirements: 10.1, 10.4_

- [ ] 2. Checkpoint - Ensure infrastructure builds and tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 3. Shared components and layout system
  - [ ] 3.1 Create common UI components
    - Create `src/components/common/Badge.tsx` — numeric badge with color variants
    - Create `src/components/common/ErrorBanner.tsx` — dismissable error/warning banner
    - Create `src/components/common/StatusDot.tsx` — colored status indicator dot
    - Create `src/components/common/Spinner.tsx` — loading spinner
    - Style each with CSS Modules; use theme CSS custom properties
    - _Requirements: 13.1, 13.2_

  - [ ] 3.2 Create sidebar navigation component
    - Create `src/components/Sidebar/types.ts` with `NavItem` interface
    - Create `src/components/Sidebar/NavItem.tsx` rendering a single nav link with icon and optional badge
    - Create `src/components/Sidebar/Sidebar.tsx` with navigation items: Overview, Agent Feed, Alerts, Approvals, Skills, Artifacts, Settings
    - Create `src/components/Sidebar/Sidebar.module.css` with dark theme, active state indicator, hamburger collapse at <768px
    - Badges wired to TanStack Query cache (alerts count, approvals count)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ] 3.3 Create dashboard layout system
    - Create `src/components/Layout/types.ts` with `PanelArrangement`, `PanelConfig` interfaces
    - Create `src/hooks/useLayoutPersistence.ts` — read/write layout to localStorage key `nexus-console:layout`
    - Create `src/components/Layout/DashboardLayout.tsx` — responsive CSS Grid: multi-column ≥1200px, single-column <1200px
    - Create `src/components/Layout/DashboardLayout.module.css`
    - Implement default arrangement (NavigationHub + HealthMonitor visible)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [ ]* 3.4 Write property tests for layout and responsive logic
    - **Property 13: Layout persistence round-trip** — serialize/deserialize PanelArrangement via localStorage
    - **Property 14: Responsive breakpoint determinism** — viewport width → layout mode mapping
    - **Validates: Requirements 7.2, 7.3, 7.4, 7.5, 8.6**

  - [ ] 3.5 Create router and App shell
    - Create `src/routes.tsx` with route definitions mapping paths to panel views
    - Rewrite `src/App.tsx` to wrap with ConfigContext, AuthContext, QueryClientProvider, React Router
    - Wire AuthGuard at the top level; login route excluded from guard
    - Create global error boundary component
    - _Requirements: 8.2, 10.2_

- [ ] 4. Checkpoint - Ensure layout, routing, and shared components work
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Service navigation and health monitoring
  - [ ] 5.1 Create utility functions (formatters and filters)
    - Create `src/utils/formatters.ts` — date formatting, file size formatting, duration formatting
    - Create `src/utils/filters.ts` — shared filter logic for alerts, skills, events (used by property tests)
    - _Requirements: 3.5, 4.4, 6.3_

  - [ ] 5.2 Implement Navigation Hub panel
    - Create `src/api/types/services.ts` with `ServiceEntry` type
    - Create `src/components/panels/Navigation/NavigationHub.tsx` — renders service cards grouped by category
    - Create `src/components/panels/Navigation/ServiceCard.tsx` — card with icon, name, description, health dot; opens URL in new tab on click
    - Create `src/components/panels/Navigation/Navigation.module.css`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ]* 5.3 Write property test for service registry categorization
    - **Property 1: Service Registry categorization completeness** — grouping by category produces all entries without loss/duplication
    - **Validates: Requirements 1.1, 1.4**

  - [ ] 5.4 Implement Health Monitor panel
    - Create `src/api/types/health.ts` with `HealthStatus` interface
    - Create `src/hooks/useHealthMonitor.ts` — TanStack Query with refetchInterval, 5s timeout, consecutive failure tracking
    - Create `src/components/panels/Health/HealthMonitor.tsx` — main panel view
    - Create `src/components/panels/Health/HealthSummaryBar.tsx` — counts of healthy/degraded/offline/unknown
    - Create `src/components/panels/Health/ServiceHealthCard.tsx` — individual service health card with visual highlight on degraded/offline
    - Create `src/components/panels/Health/Health.module.css`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ]* 5.5 Write property tests for health status derivation
    - **Property 2: Health status derivation from failure count** — consecutiveFailures → status mapping
    - **Property 3: Health summary counts are consistent** — sum of all status counts equals total services
    - **Validates: Requirements 2.2, 2.3, 2.4, 2.6**

- [ ] 6. Agent Feed panel (SSE)
  - [ ] 6.1 Implement SSE client and Agent Feed hook
    - Create `src/api/types/opar-events.ts` with `OPAREvent` interface
    - Create `src/api/agentFeedSSE.ts` — EventSource wrapper with exponential backoff reconnection
    - Create `src/hooks/useAgentFeed.ts` — manages SSE connection, event array (newest first), connection state, filters
    - _Requirements: 3.1, 3.2, 3.5, 3.7_

  - [ ] 6.2 Implement Agent Feed panel components
    - Create `src/components/panels/AgentFeed/AgentFeedPanel.tsx` — scrollable list with filter controls, connection error banner, empty state placeholder
    - Create `src/components/panels/AgentFeed/EventRow.tsx` — displays timestamp, phase, target, tool name, outcome status
    - Create `src/components/panels/AgentFeed/EventDetail.tsx` — expandable inline detail view with full payload
    - Create `src/components/panels/AgentFeed/AgentFeed.module.css` — monospace font for payloads
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [ ]* 6.3 Write property tests for agent feed
    - **Property 4: Agent feed chronological ordering** — events sorted by timestamp descending regardless of arrival order
    - **Property 5: Agent feed filter consistency** — filtered results satisfy all active predicates, no valid event excluded
    - **Validates: Requirements 3.1, 3.5**

- [ ] 7. Alerts panel with AI triage integration
  - [ ] 7.1 Implement Alerts hook and data layer
    - Create `src/api/types/alerts.ts` with `SOCAlert`, `AITriageResult`, `AlertFilters` interfaces
    - Create `src/hooks/useAlerts.ts` — TanStack Query fetching latest 100 alerts, filtering, badge count computation
    - _Requirements: 4.1, 4.3, 4.4, 4.6_

  - [ ] 7.2 Implement Alerts panel components
    - Create `src/components/panels/Alerts/AlertsPanel.tsx` — sortable table with severity coloring, filter controls (severity, source, time range)
    - Create `src/components/panels/Alerts/AlertRow.tsx` — color-coded row; "Simulated" tag for Athena-labeled alerts
    - Create `src/components/panels/Alerts/AlertDetail.tsx` — expandable detail with full payload, Wazuh Dashboard link, AI triage section
    - Create `src/components/panels/Alerts/TriageSummary.tsx` — confidence score, recommended action, reasoning excerpt (or "No AI triage available")
    - Create `src/components/panels/Alerts/Alerts.module.css`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 11.1, 11.2, 11.3_

  - [ ]* 7.3 Write property tests for alerts
    - **Property 6: Alert severity color mapping completeness** — every severity has exactly one color, no gaps
    - **Property 7: Alert filtering correctness** — filtered alerts satisfy all active criteria, no valid alert excluded
    - **Property 8: Athena-labeled alert tagging** — alerts with athenaScenario show "Simulated" tag, others don't
    - **Validates: Requirements 4.2, 4.4, 4.7**

  - [ ]* 7.4 Write property test for badge count accuracy
    - **Property 16: Badge count accuracy** — alerts badge equals unacknowledged critical+high count; approvals badge equals pending count
    - **Validates: Requirements 4.6, 5.5, 8.3**

- [ ] 8. Checkpoint - Ensure navigation, health, agent feed, and alerts panels work
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Approvals panel
  - [ ] 9.1 Implement Approvals hook and data layer
    - Create `src/api/types/approvals.ts` with `ApprovalAction`, `ApprovalDecision` interfaces
    - Create `src/hooks/useApprovals.ts` — TanStack Query with 5s refetchInterval, optimistic approve/reject mutations, pending count
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [ ] 9.2 Implement Approvals panel components
    - Create `src/components/panels/Approvals/ApprovalsPanel.tsx` — list of pending actions ordered by submittedAt ascending
    - Create `src/components/panels/Approvals/ApprovalCard.tsx` — session ID, proposed tool, target, arguments summary, time pending, approve/reject buttons, inline error on failure
    - Create `src/components/panels/Approvals/Approvals.module.css`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6_

  - [ ]* 9.3 Write property tests for approvals
    - **Property 9: Approval list ordering** — pending list ordered by submittedAt ascending (oldest first)
    - **Property 10: Approval decision removes from pending** — after successful decision, action no longer in list
    - **Validates: Requirements 5.1, 5.3, 5.4**

- [ ] 10. Skills browser panel
  - [ ] 10.1 Implement Skills hook and data layer
    - Create `src/api/types/skills.ts` with `Skill`, `SkillFilters` interfaces
    - Create `src/hooks/useSkills.ts` — TanStack Query fetching skills list, filtering by search/tag/domain, content loading
    - _Requirements: 6.1, 6.3, 6.4, 6.5_

  - [ ] 10.2 Implement Skills panel components
    - Create `src/components/panels/Skills/SkillsPanel.tsx` — search input, tag/domain filter controls, split list/preview layout
    - Create `src/components/panels/Skills/SkillList.tsx` — grouped by domain tag with skill name, description, tags
    - Create `src/components/panels/Skills/SkillPreview.tsx` — renders markdown with `react-markdown` + `remark-gfm`, monospace font for code
    - Create `src/components/panels/Skills/Skills.module.css`
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 13.3_

  - [ ]* 10.3 Write property tests for skills
    - **Property 11: Skills search filter correctness** — filtered skills match all active criteria, no valid skill excluded
    - **Property 12: Skills domain grouping completeness** — grouping by domain produces all skills without loss/duplication
    - **Validates: Requirements 6.3, 6.4**

- [ ] 11. MinIO Artifacts panel
  - [ ] 11.1 Implement Artifacts hook and data layer
    - Create `src/api/types/artifacts.ts` with `ArtifactObject`, `ArtifactCategory` types
    - Create `src/hooks/useArtifacts.ts` — TanStack Query fetching objects by category, pre-signed download URL generation
    - _Requirements: 12.1, 12.2, 12.3, 12.4_

  - [ ] 11.2 Implement Artifacts panel components
    - Create `src/components/panels/Artifacts/ArtifactsView.tsx` — category selector (PCAPs, SBOMs, skills, sessions), error fallback with MinIO Console link
    - Create `src/components/panels/Artifacts/ArtifactList.tsx` — object list with name, size, last-modified; click triggers download
    - Create `src/components/panels/Artifacts/Artifacts.module.css`
    - _Requirements: 12.1, 12.2, 12.3, 12.4_

- [ ] 12. Integration wiring and final assembly
  - [ ] 12.1 Wire all panels into router and sidebar
    - Update `src/routes.tsx` to register all panel routes (/, /agent-feed, /alerts, /approvals, /skills, /artifacts, /settings, /login)
    - Connect sidebar badge counts to `useAlerts` and `useApprovals` hooks
    - Ensure active nav item highlights based on current route
    - Wire NavigationHub AI Inference link (Req 11.4)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 4.6, 5.5, 11.4_

  - [ ] 12.2 Wire dashboard layout with panel arrangement
    - Connect `DashboardLayout` to `useLayoutPersistence` for the Overview route
    - Implement default arrangement showing NavigationHub + HealthMonitor
    - Implement reset-to-default functionality
    - _Requirements: 7.4, 7.5, 7.6_

  - [ ] 12.3 Add accessibility attributes and keyboard navigation
    - Add semantic landmarks (`<nav>`, `<main>`, `<aside>`) to layout
    - Add ARIA labels to badges, status dots, expandable sections
    - Ensure keyboard navigation for sidebar, tables, cards, and panel switching
    - Verify focus management on route changes
    - _Requirements: 13.4_

- [ ] 13. Final checkpoint - Full build and test verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties defined in the design document (16 properties total)
- Unit tests validate specific examples and edge cases
- The API Gateway is contract-only — all hooks use TanStack Query against the endpoint contract; mock responses in tests
- The design prescribes CSS Modules with CSS custom properties — no component library or Tailwind
- All token storage is in-memory (React context with useRef) per Requirement 10.3

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["1.4", "1.5"] },
    { "id": 3, "tasks": ["1.6"] },
    { "id": 4, "tasks": ["3.1", "5.1"] },
    { "id": 5, "tasks": ["3.2", "3.3", "3.5"] },
    { "id": 6, "tasks": ["3.4", "5.2", "5.4"] },
    { "id": 7, "tasks": ["5.3", "5.5", "6.1"] },
    { "id": 8, "tasks": ["6.2", "7.1"] },
    { "id": 9, "tasks": ["6.3", "7.2", "9.1"] },
    { "id": 10, "tasks": ["7.3", "7.4", "9.2", "10.1"] },
    { "id": 11, "tasks": ["9.3", "10.2", "11.1"] },
    { "id": 12, "tasks": ["10.3", "11.2"] },
    { "id": 13, "tasks": ["12.1", "12.2"] },
    { "id": 14, "tasks": ["12.3"] }
  ]
}
```
