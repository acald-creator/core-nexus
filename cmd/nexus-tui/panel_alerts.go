package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
)

// Alert represents a SOC alert from Wazuh or Suricata.
type Alert struct {
	Timestamp string `json:"timestamp"`
	Source    string `json:"source"`   // wazuh, suricata
	Severity  string `json:"severity"` // critical, high, medium, low, info
	RuleID    string `json:"rule_id"`
	Title     string `json:"title"`
	SrcIP     string `json:"src_ip,omitempty"`
	DstIP     string `json:"dst_ip,omitempty"`
	Agent     string `json:"agent,omitempty"`
	Labels    map[string]string `json:"labels,omitempty"` // traffic labels from Athena
}

// AlertsModel manages the alert triage panel.
type AlertsModel struct {
	viewport   viewport.Model
	alerts     []Alert
	alertsFile string
	cursor     int
	width      int
	height     int
	ready      bool
}

// NewAlertsModel creates a new alerts panel.
func NewAlertsModel(alertsFile string) AlertsModel {
	return AlertsModel{
		alertsFile: alertsFile,
		alerts:     []Alert{},
	}
}

func (m AlertsModel) Init() tea.Cmd {
	if m.alertsFile != "" {
		return loadAlerts(m.alertsFile)
	}
	return nil
}

func (m AlertsModel) Count() int {
	return len(m.alerts)
}

type alertsLoaded struct {
	alerts []Alert
	err    error
}

func loadAlerts(path string) tea.Cmd {
	return func() tea.Msg {
		data, err := os.ReadFile(path)
		if err != nil {
			return alertsLoaded{err: err}
		}

		var alerts []Alert
		// Try JSON array first
		if err := json.Unmarshal(data, &alerts); err != nil {
			// Fall back to JSONL
			for _, line := range strings.Split(string(data), "\n") {
				line = strings.TrimSpace(line)
				if line == "" {
					continue
				}
				var a Alert
				if err := json.Unmarshal([]byte(line), &a); err == nil {
					alerts = append(alerts, a)
				}
			}
		}
		return alertsLoaded{alerts: alerts}
	}
}

func (m AlertsModel) Update(msg tea.Msg) (AlertsModel, tea.Cmd) {
	switch msg := msg.(type) {
	case alertsLoaded:
		if msg.err == nil {
			m.alerts = msg.alerts
			m.viewport.SetContent(m.renderAlerts())
		}
	case tea.KeyMsg:
		switch msg.String() {
		case "r":
			if m.alertsFile != "" {
				return m, loadAlerts(m.alertsFile)
			}
		case "j", "down":
			if m.cursor < len(m.alerts)-1 {
				m.cursor++
				m.viewport.SetContent(m.renderAlerts())
			}
		case "k", "up":
			if m.cursor > 0 {
				m.cursor--
				m.viewport.SetContent(m.renderAlerts())
			}
		}
	}

	var cmd tea.Cmd
	m.viewport, cmd = m.viewport.Update(msg)
	return m, cmd
}

func (m AlertsModel) View() string {
	if !m.ready {
		return panelStyle.Render("Alerts: loading...")
	}

	if len(m.alerts) == 0 {
		help := subtitleStyle.Render("No alerts loaded.\n\n") +
			"Set NEXUS_ALERTS_FILE to a JSON/JSONL file with alert objects.\n\n" +
			"Expected format:\n" +
			`  {"timestamp":"...","source":"suricata","severity":"high","rule_id":"2024001","title":"..."}` + "\n\n" +
			subtitleStyle.Render("Keys: j/k or ↑/↓ to navigate, r to reload")
		return panelStyle.Render(help)
	}

	return m.viewport.View()
}

func (m AlertsModel) SetSize(width, height int) AlertsModel {
	m.width = width
	m.height = height
	if !m.ready {
		m.viewport = viewport.New(width-4, height-2)
		m.ready = true
	} else {
		m.viewport.Width = width - 4
		m.viewport.Height = height - 2
	}
	if len(m.alerts) > 0 {
		m.viewport.SetContent(m.renderAlerts())
	}
	return m
}

func (m AlertsModel) renderAlerts() string {
	var b strings.Builder

	header := fmt.Sprintf("%-8s %-10s %-10s %-10s %s\n",
		"TIME", "SOURCE", "SEVERITY", "RULE", "TITLE")
	b.WriteString(titleStyle.Render(header))
	b.WriteString(strings.Repeat("─", m.width-6) + "\n")

	for i, a := range m.alerts {
		ts := a.Timestamp
		if t, err := time.Parse(time.RFC3339, ts); err == nil {
			ts = t.Format("15:04:05")
		}

		sev := severityStyle(a.Severity).Render(fmt.Sprintf("%-10s", a.Severity))

		cursor := "  "
		if i == m.cursor {
			cursor = "▶ "
		}

		// Check if this is Athena-generated traffic
		athenaLabel := ""
		if a.Labels != nil {
			if scenario, ok := a.Labels["athena_scenario"]; ok {
				athenaLabel = subtitleStyle.Render(fmt.Sprintf(" [athena:%s]", scenario))
			}
		}

		line := fmt.Sprintf("%s%-8s %-10s %s %-10s %s%s\n",
			cursor, ts, a.Source, sev, a.RuleID, a.Title, athenaLabel)
		b.WriteString(line)
	}

	return b.String()
}
