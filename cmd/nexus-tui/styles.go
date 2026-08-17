package main

import "github.com/charmbracelet/lipgloss"

// Color palette
var (
	colorPrimary   = lipgloss.Color("#04B575")
	colorSecondary = lipgloss.Color("#3C3C3C")
	colorText      = lipgloss.Color("#E2E1ED")
	colorCritical  = lipgloss.Color("#FF4444")
	colorHigh      = lipgloss.Color("#FF8800")
	colorMedium    = lipgloss.Color("#FFCC00")
	colorLow       = lipgloss.Color("#44AAFF")
	colorInfo      = lipgloss.Color("#888888")
	colorApproved  = lipgloss.Color("#04B575")
	colorRejected  = lipgloss.Color("#FF4444")
	colorPending   = lipgloss.Color("#FFCC00")
)

// Layout styles
var (
	headerStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FFF")).
			Background(colorPrimary).
			Padding(0, 1).
			Bold(true)

	tabStyle = lipgloss.NewStyle().
			Padding(0, 2)

	activeTabStyle = lipgloss.NewStyle().
			Padding(0, 2).
			Foreground(colorPrimary).
			Bold(true).
			Underline(true)

	inactiveTabStyle = lipgloss.NewStyle().
				Padding(0, 2).
				Foreground(colorInfo)

	statusBarStyle = lipgloss.NewStyle().
			Foreground(colorText).
			Background(colorSecondary).
			Padding(0, 1)

	panelStyle = lipgloss.NewStyle().
			Padding(1, 2)

	borderStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colorSecondary).
			Padding(0, 1)
)

// Text styles
var (
	titleStyle = lipgloss.NewStyle().
			Foreground(colorPrimary).
			Bold(true)

	subtitleStyle = lipgloss.NewStyle().
			Foreground(colorInfo).
			Italic(true)

	agentNameStyle = lipgloss.NewStyle().
			Foreground(colorPrimary).
			Bold(true)

	phaseObserveStyle = lipgloss.NewStyle().
				Foreground(lipgloss.Color("#44AAFF")).
				Bold(true)

	phasePlanStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#AA44FF")).
			Bold(true)

	phaseActStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FF8800")).
			Bold(true)

	phaseReflectStyle = lipgloss.NewStyle().
				Foreground(lipgloss.Color("#04B575")).
				Bold(true)
)

// Severity styling helper
func severityStyle(severity string) lipgloss.Style {
	switch severity {
	case "critical":
		return lipgloss.NewStyle().Foreground(colorCritical).Bold(true)
	case "high":
		return lipgloss.NewStyle().Foreground(colorHigh).Bold(true)
	case "medium":
		return lipgloss.NewStyle().Foreground(colorMedium)
	case "low":
		return lipgloss.NewStyle().Foreground(colorLow)
	default:
		return lipgloss.NewStyle().Foreground(colorInfo)
	}
}
