package main

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Tab identifiers
const (
	tabAgentFeed = iota
	tabAlerts
	tabApprovals
	tabSkills
	tabCount
)

var tabNames = [tabCount]string{
	"Agent Feed",
	"Alerts",
	"Approvals",
	"Skills",
}

// App is the root model that manages tabs and delegates to panel models.
type App struct {
	config    Config
	activeTab int
	width     int
	height    int
	ready     bool

	// Panel models
	agentFeed AgentFeedModel
	alerts    AlertsModel
	approvals ApprovalsModel
	skills    SkillsModel
}

// NewApp creates the root application model.
func NewApp(cfg Config) App {
	return App{
		config:    cfg,
		activeTab: tabAgentFeed,
		agentFeed: NewAgentFeedModel(cfg.AgentLogFile),
		alerts:    NewAlertsModel(cfg.AlertsFile),
		approvals: NewApprovalsModel(cfg.ApprovalFile),
		skills:    NewSkillsModel(cfg.SkillsDir),
	}
}

func (a App) Init() tea.Cmd {
	return tea.Batch(
		a.agentFeed.Init(),
		a.alerts.Init(),
		a.approvals.Init(),
		a.skills.Init(),
	)
}

func (a App) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd

	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			return a, tea.Quit
		case "tab", "right":
			a.activeTab = (a.activeTab + 1) % tabCount
			return a, nil
		case "shift+tab", "left":
			a.activeTab = (a.activeTab - 1 + tabCount) % tabCount
			return a, nil
		case "1":
			a.activeTab = tabAgentFeed
			return a, nil
		case "2":
			a.activeTab = tabAlerts
			return a, nil
		case "3":
			a.activeTab = tabApprovals
			return a, nil
		case "4":
			a.activeTab = tabSkills
			return a, nil
		}

	case tea.WindowSizeMsg:
		a.width = msg.Width
		a.height = msg.Height
		a.ready = true

		// Propagate size to panels (subtract header + tabs + status bar)
		panelHeight := a.height - 4
		panelWidth := a.width

		a.agentFeed = a.agentFeed.SetSize(panelWidth, panelHeight)
		a.alerts = a.alerts.SetSize(panelWidth, panelHeight)
		a.approvals = a.approvals.SetSize(panelWidth, panelHeight)
		a.skills = a.skills.SetSize(panelWidth, panelHeight)
	}

	// Delegate update to the active panel
	switch a.activeTab {
	case tabAgentFeed:
		updated, cmd := a.agentFeed.Update(msg)
		a.agentFeed = updated
		cmds = append(cmds, cmd)
	case tabAlerts:
		updated, cmd := a.alerts.Update(msg)
		a.alerts = updated
		cmds = append(cmds, cmd)
	case tabApprovals:
		updated, cmd := a.approvals.Update(msg)
		a.approvals = updated
		cmds = append(cmds, cmd)
	case tabSkills:
		updated, cmd := a.skills.Update(msg)
		a.skills = updated
		cmds = append(cmds, cmd)
	}

	return a, tea.Batch(cmds...)
}

func (a App) View() string {
	if !a.ready {
		return "\n  Initializing Nexus TUI..."
	}

	// Header
	header := headerStyle.Width(a.width).Render("⚡ Nexus Triage Console")

	// Tab bar
	var tabs []string
	for i, name := range tabNames {
		label := fmt.Sprintf("[%d] %s", i+1, name)
		if i == a.activeTab {
			tabs = append(tabs, activeTabStyle.Render(label))
		} else {
			tabs = append(tabs, inactiveTabStyle.Render(label))
		}
	}
	tabBar := lipgloss.JoinHorizontal(lipgloss.Top, tabs...)

	// Active panel content
	var content string
	switch a.activeTab {
	case tabAgentFeed:
		content = a.agentFeed.View()
	case tabAlerts:
		content = a.alerts.View()
	case tabApprovals:
		content = a.approvals.View()
	case tabSkills:
		content = a.skills.View()
	}

	// Status bar
	statusLeft := fmt.Sprintf(" Tab/←→: switch panels | q: quit | Alerts: %d | Pending: %d",
		a.alerts.Count(), a.approvals.PendingCount())
	statusRight := " Nexus SOC "
	gap := a.width - lipgloss.Width(statusLeft) - lipgloss.Width(statusRight)
	if gap < 0 {
		gap = 0
	}
	statusBar := statusBarStyle.Width(a.width).Render(
		statusLeft + strings.Repeat(" ", gap) + statusRight,
	)

	return lipgloss.JoinVertical(lipgloss.Left,
		header,
		tabBar,
		content,
		statusBar,
	)
}
