---
name: Go Charmbracelet TUI Application Pattern
description: Building multi-panel terminal UIs with Bubble Tea, Bubbles, and Lipgloss for SOC/security tooling
tags: [code-debug, architecture, go, tui, charmbracelet]
inclusion: manual
---

## When to Apply
- Building terminal-based dashboards or consoles in Go
- Creating tabbed/paneled interfaces for SOC analyst workflows
- Needing a TUI that works in SSH/air-gapped environments without browser dependencies
- Extending nexus-tui with new panels or data sources

## Approach
1. Structure: separate files per concern — `main.go` (entry), `app.go` (root model with tabs), `config.go`, `styles.go`, `panel_*.go` (one per panel)
2. Root model (`App`) owns tab state and delegates Update/View to the active panel
3. Each panel is its own model struct with `Init()`, `Update()`, `View()`, `SetSize()` methods
4. Data loading uses Bubble Tea commands (return `tea.Cmd` from `Init()` or on key press)
5. Styles centralized in `styles.go` — define color palette once, create reusable `lipgloss.Style` vars
6. Config via environment variables for file paths — no network dependencies required
7. Build: `go build ./cmd/nexus-tui` — single binary, zero runtime deps

## Key Patterns
- Tab switching: `tea.KeyMsg` handler in root model routes to `(activeTab + 1) % tabCount`
- Size propagation: `tea.WindowSizeMsg` in root, call `panel.SetSize(width, panelHeight)` on each panel
- Async data loading: return a `tea.Cmd` closure that reads a file and returns a custom message type
- Viewport for scrollable content: `viewport.New(width, height)` + `SetContent()` + delegate scroll keys
- JSONL parsing: iterate lines, `json.Unmarshal` each, skip empty/invalid — resilient to partial files
- Status bar: left-align info, right-align label, fill gap with spaces based on terminal width
- .gitignore the binary name in the package directory

## Pitfalls
- Don't forget to import `lipgloss` in panel files that use color constants from `styles.go` — the constants are package-level but the type isn't auto-imported
- Don't commit compiled binaries — add to .gitignore immediately
- `viewport` needs explicit width/height before first render — check `ready` bool
- Panel height = terminal height - header - tab bar - status bar (typically -4)
- `tea.WindowSizeMsg` fires on startup — use it to initialize viewports (gate with `!m.ready`)

## References
- `core-nexus/cmd/nexus-tui/` — full implementation
- `github.com/charmbracelet/bubbletea` — Elm-architecture TUI framework
- `github.com/charmbracelet/bubbles` — pre-built components (viewport, textarea, list)
- `github.com/charmbracelet/lipgloss` — terminal styling (colors, borders, padding)
- Pattern: main.go → app.go (tabs) → panel_*.go (one per view) → styles.go (shared palette)
